"""Small local-only HTTP API that delegates preview calculations to the core."""

import json
import os
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, model_validator
from starlette.middleware.body_limit import RequestBodyLimitMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from dcabot.application.historical import (
    HistoricalRunPlanError,
    HistoricalRunValidationError,
    build_historical_run_plan,
    load_verified_dataset,
    validate_historical_run_request,
)
from dcabot.application.historical_profiles import (
    HistoricalProfile,
    HistoricalProfileError,
    get_historical_profile,
    list_historical_profiles,
    load_historical_profile_config,
)
from dcabot.application.chart_data import HistoricalChartDataError, build_historical_chart_data
from dcabot.application.read_only_explanations import explain_historical_result
from dcabot.application.historical_simulation import (
    MAX_HISTORICAL_SIMULATION_BARS,
    HistoricalSimulationError,
    HistoricalSimulationResult,
    simulate_historical_ohlcv,
    simulate_historical_fixed_slice,
)
from dcabot.application.historical_fixed_slice import HistoricalFixedSliceResult
from dcabot.application.historical_fixed_limit import FixedLimitOrder, HistoricalFixedLimitError
from dcabot.application.historical_base_limit_binding import (
    HistoricalBaseLimitBindingError,
    base_limit_binding_identity_sha256,
    simulate_base_fixed_limit_binding,
)
from dcabot.application.historical_run_contract import (
    HistoricalRunCapture,
    HistoricalRunContractError,
    build_historical_run_capture,
)
from dcabot.application.service import preview
from dcabot.data_adapters.catalog import (
    BINANCE_BTCUSDT_1H_2025_01_01_DATASET,
    CatalogError,
    PublicDatasetCatalog,
    PublicDatasetCatalogEntry,
)
from dcabot.data_adapters.binance_testnet_public import (
    BinanceTestnetExchangeInfoSnapshot,
    BinanceTestnetPublicError,
    fetch_binance_testnet_exchange_info,
)
from dcabot.data_adapters.binance_testnet_account import (
    BinanceTestnetAccountError,
    fetch_binance_testnet_account,
    fetch_binance_testnet_open_orders,
)
from dcabot.application.signed_request import SignedRequestError
from dcabot.application.windows_credential_provider import WindowsCredentialManagerProvider
from dcabot.data_adapters.download_jobs import (
    DownloadJobConflict,
    DownloadJobManager,
    DownloadJobNotFound,
    DownloadJobSnapshot,
)
from dcabot.data_adapters.quality import DataQualityError, MAX_INPUT_BYTES, quality_from_bytes
from dcabot.data_adapters.historical import MAX_BARS, HistoricalDatasetInput, HistoricalInputError
from dcabot.domain.config import Config
from dcabot.domain.numbers import exact_text, number, positive
from dcabot.persistence.historical_runs import (
    DEFAULT_RUN_LIST_LIMIT,
    MAX_RUN_LIST_LIMIT,
    HistoricalRunStore,
    HistoricalRunStoreError,
)


ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "paper.json"
_PAPER_CONFIG_CACHE: tuple[int, dict[str, Any]] | None = None
DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)

def _cors_origins() -> list[str]:
    raw_origins = os.getenv("DCABOT_CORS_ORIGINS")
    if raw_origins is None:
        return list(DEFAULT_CORS_ORIGINS)
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    if not origins or "*" in origins:
        return list(DEFAULT_CORS_ORIGINS)
    return origins
PREVIEW_FIELDS = {"anchor", "safety_qty", "safety_count", "deviation", "revision"}
SMALL_JSON_BODY_LIMIT_BYTES = 4 * 1024
SMALL_JSON_BODY_LIMITS = {
    "/api/dataset-selection": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/historical-runs/simulate": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/historical-runs/simulate-base-limit": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/historical-runs/validate": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/historical-runs": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/dataset-downloads": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/dataset-downloads/{job_id}/cancel": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/preview": SMALL_JSON_BODY_LIMIT_BYTES,
}
FIELD_LABELS = {
    "anchor": "Anchor fiyatı",
    "safety_qty": "Safety miktarı",
    "deviation": "Sapma",
}
DATASET_CACHE_DIR = ROOT / "data" / "public_cache"
DATASET_CATALOG = PublicDatasetCatalog(DATASET_CACHE_DIR, [BINANCE_BTCUSDT_1H_2025_01_01_DATASET])
DOWNLOAD_JOBS = DownloadJobManager()
HISTORICAL_EXECUTION_LOCK = Lock()
HISTORICAL_EXECUTIONS_LOCK = Lock()
HISTORICAL_RUNS_PATH = ROOT / "data" / "historical_runs.sqlite3"
HISTORICAL_EXECUTIONS: dict[str, HistoricalRunCapture] = {}
MAX_EPHEMERAL_HISTORICAL_EXECUTIONS = 16
MAX_HISTORICAL_RUN_DETAIL_RESPONSE_BYTES = 256 * 1024
MAX_HISTORICAL_BASE_LIMIT_RESPONSE_BYTES = 256 * 1024

DatasetStatus = Literal["MISSING", "CORRUPT", "VERIFIED"]
DatasetId = Annotated[
    str,
    Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$",
    ),
]
ProfileId = Annotated[
    str,
    Field(
        min_length=1,
        max_length=128,
        pattern=r"^[a-z0-9](?:[a-z0-9_-]{0,126}[a-z0-9])?$",
    ),
]
ExecutionId = Annotated[
    str,
    Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9:_-]{1,128}$"),
]
BinanceTestnetSymbol = Annotated[
    str,
    Field(min_length=1, max_length=32, pattern=r"^[^\x00-\x20\x7f]{1,32}$"),
]


class BoundedAPIRoute(APIRoute):
    """Attach native Starlette body limits to the explicitly bounded JSON routes."""

    def __init__(self, path: str, endpoint: Any, **kwargs: Any) -> None:
        super().__init__(path, endpoint, **kwargs)
        max_body_size = SMALL_JSON_BODY_LIMITS.get(path)
        if max_body_size is not None:
            self.app = ProblemDetailsBodyLimitMiddleware(self.app, max_body_size=max_body_size)


class ProblemDetailsBodyLimitMiddleware:
    """Adapt native body-limit 413 responses to the local Problem Details contract."""

    def __init__(self, app: ASGIApp, *, max_body_size: int) -> None:
        self.app = RequestBodyLimitMiddleware(app, max_body_size=max_body_size)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        replaced = False

        async def send_with_problem(message: Message) -> None:
            nonlocal replaced
            if replaced:
                return
            if message["type"] == "http.response.start" and message["status"] == 413:
                replaced = True
                await _problem(
                    413,
                    "REQUEST_TOO_LARGE",
                    "İstek gövdesi çok büyük",
                    "İstek gövdesi byte sınırını aşıyor.",
                )(scope, receive, send)
                return
            await send(message)

        await self.app(scope, receive, send_with_problem)


class DatasetSelectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)

    dataset_id: DatasetId


class ArtifactSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(ge=0)


class DatasetSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    dataset_id: str
    dataset_type: Literal["kline_csv_zip"]
    instrument: str
    interval: str
    period_start: date
    period_end: date
    status: DatasetStatus
    artifact: ArtifactSummary | None

    @model_validator(mode="after")
    def validate_artifact_state(self):
        if (self.status == "VERIFIED") != (self.artifact is not None):
            raise ValueError("VERIFIED dataset artifact özeti gerektirir.")
        return self


class DatasetListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    datasets: list[DatasetSummary]
    count: int = Field(ge=0)


class BinanceTestnetExchangeInfoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    environment: Literal["BINANCE_SPOT_TESTNET"]
    symbol: str
    status: str
    base_asset: str
    quote_asset: str
    permissions: list[str]
    permission_sets: list[list[str]]
    order_types: list[str]
    filters: list[dict[str, str]]
    exchange_filters: list[dict[str, str]]
    rate_limits: list[dict[str, str]]
    response_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    observed_at_us: int = Field(ge=0)
    read_only: Literal[True]
    credential_required: Literal[False]


class BinanceTestnetBalanceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    asset: str
    free: str
    locked: str


class BinanceTestnetAccountResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    environment: Literal["BINANCE_SPOT_TESTNET"]
    account_type: str
    can_trade: bool
    can_withdraw: bool
    can_deposit: bool
    permissions: list[str]
    update_time_ms: int = Field(ge=0)
    balances_count: int = Field(ge=0)
    balances: list[BinanceTestnetBalanceResponse]
    response_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    observed_at_us: int = Field(ge=0)
    read_only: Literal[True]
    credential_required: Literal[True]


class BinanceTestnetOpenOrderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    symbol: str
    order_id: int = Field(ge=0)
    client_order_id: str
    side: str
    type: str
    status: str
    price: str
    orig_qty: str
    executed_qty: str
    time_ms: int = Field(ge=0)
    update_time_ms: int = Field(ge=0)


class BinanceTestnetOpenOrdersResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    environment: Literal["BINANCE_SPOT_TESTNET"]
    orders: list[BinanceTestnetOpenOrderResponse]
    count: int = Field(ge=0)
    read_only: Literal[True]
    credential_required: Literal[True]


class DatasetSelectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    selected: DatasetSummary


class DatasetPreflightResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    dataset_id: str
    artifact_status: Literal["VERIFIED"]
    preflight_status: Literal["READY"]
    instrument: str
    interval: str
    period_start: date
    period_end: date
    bar_count: int = Field(ge=1)
    timestamp_unit: Literal["microseconds"]
    timezone: Literal["UTC"]
    data_quality_status: Literal["UNKNOWN"]
    data_quality_message: str
    artifact: ArtifactSummary
    read_only: bool


class HistoricalChartBarResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    bar_index: int = Field(ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    open_time_us: int = Field(ge=0)
    close_time_us: int = Field(ge=0)
    open: str
    high: str
    low: str
    close: str


class HistoricalChartDataResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    dataset_id: str
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_id: Literal["historical_ohlcv_v1"]
    period_start: date
    period_end: date
    processed_bar_count: int = Field(ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    bars: list[HistoricalChartBarResponse]

    @model_validator(mode="after")
    def validate_bar_count(self):
        if len(self.bars) != self.processed_bar_count:
            raise ValueError("Chart bar sayısı işlenen bar sayısıyla eşleşmelidir.")
        return self


class DatasetRunPlanConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    mode: Literal["offline"]
    symbol: str
    base_asset: str
    quote_asset: Literal["USDT"]
    base_qty: str
    safety_qty: str
    safety_count: int = Field(ge=0, le=50)
    deviation: str
    target_mode: Literal["GROSS_PRICE_RETURN", "NET_QUOTE"]
    fee_rate: str
    slippage: str


class HistoricalFixedSlicePlanConfigResponse(DatasetRunPlanConfigResponse):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    simulation_model: Literal["historical_ohlcv_partial_fixed_v1"]
    slice_qty: str


class HistoricalProfileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    profile_id: str
    profile_version: str
    label: str
    expected_dataset_id: str | None
    venue_filter_provenance: Literal["historical_verified", "current_observation", "project_fixture", "unknown"]
    historical_filter_claim: bool
    anchor_source: Literal["explicit", "dataset_first_bar_open"]


class HistoricalFixedSliceProfileResponse(HistoricalProfileResponse):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    simulation_model: Literal["historical_ohlcv_partial_fixed_v1"]
    slice_qty: str


class DatasetRunPlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    dataset: DatasetPreflightResponse
    config: DatasetRunPlanConfigResponse | HistoricalFixedSlicePlanConfigResponse
    profile: HistoricalProfileResponse | HistoricalFixedSliceProfileResponse
    execution_mode: Literal["SIMULATED"]
    run_status: Literal["NOT_STARTED"]
    read_only: bool


class HistoricalRunValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)

    dataset_id: DatasetId
    profile_id: ProfileId
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_mode: Literal["SIMULATED"]
    simulation_model: Literal["historical_ohlcv_v1", "historical_ohlcv_partial_fixed_v1"] = "historical_ohlcv_v1"


class HistoricalRunValidationDatasetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    dataset_id: str
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal["VERIFIED"]
    instrument: str
    interval: str
    period_start: date
    period_end: date
    bar_count: int = Field(ge=1, le=MAX_BARS)


class HistoricalRunValidationConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class HistoricalFixedSliceValidationConfigResponse(HistoricalRunValidationConfigResponse):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    simulation_model: Literal["historical_ohlcv_partial_fixed_v1"]
    slice_qty: str


class HistoricalRunValidationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    validation_status: Literal["READY"]
    run_status: Literal["NOT_STARTED"]
    read_only: bool
    offline: bool
    execution_mode: Literal["SIMULATED"]
    dataset: HistoricalRunValidationDatasetResponse
    config: HistoricalRunValidationConfigResponse | HistoricalFixedSliceValidationConfigResponse
    profile: HistoricalProfileResponse | HistoricalFixedSliceProfileResponse


class HistoricalSimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)

    dataset_id: DatasetId
    profile_id: ProfileId
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_mode: Literal["historical_ohlcv_v1", "historical_ohlcv_partial_fixed_v1"]
    action_authority: Literal["NONE", "COMMITTED_PREFIX"] = "NONE"


class HistoricalSimulationDatasetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    dataset_id: str
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    period_start: date
    period_end: date
    processed_bar_count: int = Field(ge=1, le=MAX_BARS)


class HistoricalSimulationConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class HistoricalSimulationAssumptionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    model: Literal["historical_ohlcv_v1"]
    bar_visibility: Literal["CLOSED_ONLY"]
    intrabar_path: Literal["NOT_INFERRED"]
    max_actions_per_bar: Literal[1]
    fee_model: str
    slippage_model: str
    funding: Literal["NOT_MODELED"]
    exchange_mark: Literal["NOT_AVAILABLE"]
    force_close_at_end: bool


class HistoricalSimulationActionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    bar_index: int = Field(ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    open_time_us: int = Field(ge=0)
    role: str
    raw_reference: str
    fill_price: str
    quantity: str
    fee: str


class HistoricalSimulationSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    symbol: str
    qty: str
    cost: str
    realized_gross: str
    fees: str
    funding: str
    realized_net_after_all_costs: str
    unrealized: str | None
    equity: str
    anchor: str | None
    take_profit_price: str | None
    entry_notional: str
    peak_equity: str
    max_drawdown: str
    current_drawdown: str | None
    action_count: int
    average_entry_price: str | None
    time_in_position_us: int
    deal_count: int
    completed_deal_count: int
    position_status: Literal["CLOSED", "OPEN_AT_END"]
    funding_status: Literal["NOT_MODELED"]
    mark_status: Literal["NOT_AVAILABLE"]


class HistoricalFixedSliceSummaryResponse(BaseModel):
    """Fixed-slice final summary: no deal/action-count metrics, that model has no deal concept."""

    model_config = ConfigDict(extra="forbid", strict=True)

    symbol: str
    qty: str
    cost: str
    realized_gross: str
    fees: str
    funding: str
    realized_net_after_all_costs: str
    unrealized: str | None
    equity: str
    anchor: str | None
    take_profit_price: str | None
    entry_notional: str
    position_status: Literal["CLOSED", "OPEN_AT_END"]
    funding_status: Literal["NOT_MODELED"]
    mark_status: Literal["NOT_AVAILABLE"]


class HistoricalSimulationAmbiguityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    bar_index: int = Field(ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    code: Literal["AMBIGUOUS_OHLC_PATH"]


class ReadOnlyExplanationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    code: str = Field(min_length=1, max_length=64, pattern=r"^[A-Z0-9_]+$")
    severity: Literal["INFO", "WARNING", "ERROR"]
    title: str = Field(min_length=1, max_length=160)
    message: str = Field(min_length=1, max_length=500)
    source: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_\[\]]+$")
    context: dict[str, int | str]


class HistoricalFixedSliceAmbiguityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    bar_index: int = Field(ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    open_time_us: int = Field(ge=0)
    code: Literal["AMBIGUOUS_OHLC_PATH"]


class HistoricalSimulationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    execution_id: ExecutionId
    execution_status: Literal["COMPLETED", "INDETERMINATE"]
    application_code: Literal["AMBIGUOUS_OHLC_PATH"] | None
    persisted: Literal[False]
    dataset: HistoricalSimulationDatasetResponse
    config: HistoricalSimulationConfigResponse
    profile: HistoricalProfileResponse | HistoricalFixedSliceProfileResponse
    assumptions: HistoricalSimulationAssumptionsResponse
    actions: list[HistoricalSimulationActionResponse]
    summary: HistoricalSimulationSummaryResponse
    ambiguity: HistoricalSimulationAmbiguityResponse | None
    explanations: list[ReadOnlyExplanationResponse]


class HistoricalFixedSliceConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    schema_version: Literal[1]
    config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    slice_qty: str
    quantity_unit: Literal["BASE_ASSET"]


class HistoricalFixedSliceAssumptionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    model: Literal["historical_ohlcv_partial_fixed_v1"]
    bar_visibility: Literal["CLOSED_ONLY"]
    intrabar_path: Literal["NOT_INFERRED"]
    max_actions_per_bar: Literal[1]
    fill_policy: Literal["FIXED_SLICE_ON_OHLC_TOUCH"]
    fee_model: str
    slippage_model: str
    funding: Literal["NOT_MODELED"]
    exchange_mark: Literal["NOT_AVAILABLE"]
    synthetic_cancel_at_eof: Literal[False]
    persistence: Literal["NOT_SUPPORTED_IN_THIS_PHASE"]


class HistoricalFixedSliceActionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    event_sequence: int = Field(ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    bar_index: int = Field(ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    open_time_us: int = Field(ge=0)
    action_type: Literal["PARTIAL_FILL", "FULL_FILL"]
    role: str = Field(min_length=1, max_length=64)
    order_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9:_-]+$")
    execution_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9:_-]+$")
    raw_reference: str
    fill_price: str
    quantity: str
    fee: str
    fee_asset: Literal["USDT"]
    order_status_after: Literal["PARTIALLY_FILLED", "FILLED"]
    original_qty: str
    cumulative_filled_qty: str
    leaves_qty: str
    canceled_qty: str
    fill_provenance: Literal["OHLC_TOUCH_FIXED_SLICE_ASSUMPTION"]


class HistoricalFixedSliceActionAuthorityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    mode: Literal["FULL_RUN", "COMMITTED_PREFIX", "NONE"]
    economic_state_commit_scope: Literal["FULL_RUN", "PREFIX_ONLY", "NONE"]
    committed_through_bar_index: int | None = Field(default=None, ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    committed_through_open_time_us: int | None = Field(default=None, ge=0)
    ambiguity_bar_index: int | None = Field(default=None, ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    contains_ambiguity_bar_actions: Literal[False]
    contains_post_ambiguity_actions: Literal[False]
    complete_history: bool
    economic_state_committed: bool
    committed_through_event_sequence: int | None = Field(default=None, ge=1)
    action_count: int = Field(ge=0, le=MAX_HISTORICAL_SIMULATION_BARS)


class HistoricalFixedSliceSimulationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    execution_id: Literal[None] = None
    complete_execution: bool
    execution_status: Literal["COMPLETED", "INDETERMINATE"]
    application_code: Literal["AMBIGUOUS_OHLC_PATH"] | None
    persisted: Literal[False]
    dataset: HistoricalSimulationDatasetResponse
    config: HistoricalFixedSliceConfigResponse
    profile: HistoricalProfileResponse
    assumptions: HistoricalFixedSliceAssumptionsResponse
    action_authority: HistoricalFixedSliceActionAuthorityResponse
    marker_authority: Literal["FULL", "PREFIX_BOUNDARY_ONLY", "NONE"]
    marker_kind: Literal["TRADE_EXECUTION", "INCOMPLETE_BOUNDARY", "NONE"]
    actions: list[HistoricalFixedSliceActionResponse]
    final_economic_summary: HistoricalFixedSliceSummaryResponse | None
    ambiguity: HistoricalFixedSliceAmbiguityResponse | None
    explanations: list[ReadOnlyExplanationResponse]


class HistoricalBaseLimitSimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)

    dataset_id: DatasetId
    profile_id: ProfileId
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_mode: Literal["SIMULATED"]
    simulation_model: Literal["historical_ohlcv_base_fixed_limit_binding_v1"]
    order_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")
    limit_price: str = Field(min_length=1, max_length=64)
    slice_qty: str = Field(min_length=1, max_length=64)
    placement_bar_index: int = Field(ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    placement_open_time_us: int = Field(ge=0)


class HistoricalBaseLimitProvenanceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    execution_kind: Literal["SYNTHETIC_OHLCV_FILL"]
    venue_replay: Literal[False]
    role: Literal["BASE"]
    placement_policy: Literal["ACTIVE_NEXT_BAR"]
    equality_policy: Literal["OBSERVE_ONLY"]
    price_policy: Literal["DECLARED_LIMIT_ONLY"]
    liquidity_policy: Literal["FIXED_SLICE_NO_MARKET_VOLUME"]
    ambiguity_policy: Literal["FAIL_CLOSED"]


class HistoricalBaseLimitReserveResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    model: Literal["NONE"]
    amount: Literal["NOT_MODELED"]
    asset: Literal["NOT_APPLICABLE"]


class HistoricalBaseLimitOrderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    order_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")
    role: Literal["BASE"]
    side: Literal["BUY"]
    limit_price: str
    original_qty: str
    slice_qty: str
    placement_bar_index: int = Field(ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    placement_open_time_us: int = Field(ge=0)


class HistoricalBaseLimitObservationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    bar_index: int = Field(ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    open_time_us: int = Field(ge=0)
    kind: Literal["NONE", "EQUALITY_TOUCH", "STRICT_PENETRATION"]
    trigger_observed: bool
    fill_committed: bool


class HistoricalBaseLimitActionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    event_sequence: int = Field(ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    bar_index: int = Field(ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    open_time_us: int = Field(ge=0)
    action_type: Literal["PARTIAL_FILL", "FULL_FILL"]
    role: Literal["BASE"]
    order_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")
    fill_price: str
    quantity: str
    cumulative_filled_qty: str
    leaves_qty: str
    fill_provenance: Literal["SYNTHETIC_OHLCV_FIXED_LIMIT"]


class HistoricalBaseLimitStateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    order_status: Literal["OPEN", "PARTIALLY_FILLED", "FILLED", "INDETERMINATE"]
    original_qty: str
    filled_qty: str
    leaves_qty: str
    position_status: Literal["NO_POSITION", "OPEN"]
    position_qty: str
    anchor: str | None


class HistoricalBaseLimitSimulationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    execution_id: Literal[None] = None
    execution_status: Literal["FILLED", "OPEN_AT_END", "INDETERMINATE"]
    application_code: Literal["AMBIGUOUS_OHLC_PATH"] | None
    model: Literal["historical_ohlcv_base_fixed_limit_binding_v1"]
    policy: Literal["BASE_ONLY_CORE_REDUCER_V1"]
    production_ready: Literal[False]
    persisted: Literal[False]
    dataset: HistoricalSimulationDatasetResponse
    config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    binding_identity_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    profile: HistoricalProfileResponse
    provenance: HistoricalBaseLimitProvenanceResponse
    reserve: HistoricalBaseLimitReserveResponse
    order: HistoricalBaseLimitOrderResponse
    state: HistoricalBaseLimitStateResponse
    observations: list[HistoricalBaseLimitObservationResponse]
    actions: list[HistoricalBaseLimitActionResponse]
    ambiguity: HistoricalFixedSliceAmbiguityResponse | None


class HistoricalRunSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)

    execution_id: ExecutionId


class HistoricalRunSaveResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: str = Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
    created: bool
    record_health: Literal["OK"]
    execution_status: Literal["COMPLETED", "INDETERMINATE"]
    created_at: str
    dataset_id: str
    symbol: str
    interval: str
    period_start: date
    period_end: date
    processed_bar_count: int = Field(ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    position_status: Literal["CLOSED", "OPEN_AT_END"]


class HistoricalRunListItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: str = Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
    created_at: str
    execution_status: Literal["COMPLETED", "INDETERMINATE"]
    record_health: Literal["OK", "CORRUPT"]
    symbol: str
    interval: str
    period_start: date
    period_end: date
    processed_bar_count: int = Field(ge=1, le=MAX_HISTORICAL_SIMULATION_BARS)
    position_status: Literal["CLOSED", "OPEN_AT_END"]


class HistoricalRunListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    runs: list[HistoricalRunListItemResponse]
    count: int = Field(ge=0, le=MAX_RUN_LIST_LIMIT)


class HistoricalRunReproduceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: str = Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
    reproduced: bool
    result_sha256_match: bool
    canonical_input_sha256_match: bool
    execution_identity_sha256_match: bool
    stored_result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    new_result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class HistoricalRunDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: str = Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
    created_at: str
    storage_state: Literal["STORED"]
    execution_status: Literal["COMPLETED", "INDETERMINATE"]
    dataset: dict[str, object]
    input_snapshot: dict[str, object]
    config: dict[str, object]
    instrument_risk: dict[str, object]
    execution: dict[str, object]
    result_snapshot: dict[str, object]
    result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    record_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evaluation_lineage: dict[str, object] | None = None


DownloadJobWireStatus = Literal["QUEUED", "RUNNING", "RETRYING", "SUCCEEDED", "FAILED", "CANCELLED"]


class DatasetDownloadJobResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    job_id: str
    dataset_id: str
    status: DownloadJobWireStatus
    attempt: int = Field(ge=0)
    max_attempts: int = Field(ge=1)
    bytes_downloaded: int = Field(ge=0)
    total_bytes: int | None = Field(default=None, ge=0)
    cache_hit: bool | None
    error_code: str | None
    error_message: str | None


class DatasetDownloadStartResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    job: DatasetDownloadJobResponse


def _dataset_summary(entry: PublicDatasetCatalogEntry) -> DatasetSummary:
    artifact = None
    if entry.quality_status == "VERIFIED":
        if entry.byte_count is None:
            raise CatalogError("Verified dataset byte bilgisi eksik.")
        artifact = ArtifactSummary(sha256=entry.sha256, byte_size=entry.byte_count)
    return DatasetSummary(
        dataset_id=entry.dataset_id,
        dataset_type="kline_csv_zip",
        instrument=entry.symbol,
        interval=entry.interval,
        period_start=date.fromisoformat(entry.period_start),
        period_end=date.fromisoformat(entry.period_end),
        status=entry.quality_status,
        artifact=artifact,
    )


def _download_job_response(snapshot: DownloadJobSnapshot) -> DatasetDownloadJobResponse:
    return DatasetDownloadJobResponse(
        job_id=snapshot.job_id,
        dataset_id=snapshot.dataset_id,
        status=snapshot.status.value,
        attempt=snapshot.attempt,
        max_attempts=snapshot.max_attempts,
        bytes_downloaded=snapshot.bytes_downloaded,
        total_bytes=snapshot.total_bytes,
        cache_hit=snapshot.cache_hit,
        error_code=snapshot.error_code,
        error_message=snapshot.error_message,
    )


def _problem(status: int, code: str, title: str, detail: str, *, errors: list[dict[str, str]] | None = None):
    content: dict[str, object] = {
        "type": f"urn:local-api:problem:{code.replace('_', '-')}",
        "title": title,
        "status": status,
        "detail": detail,
        "code": code,
    }
    if errors:
        content["errors"] = errors
    return JSONResponse(
        status_code=status,
        content=content,
        media_type="application/problem+json",
        headers={"Cache-Control": "no-store"},
    )


def _error(message: str, *, fields: dict[str, str] | None = None, revision: int = 0):
    return {
        "error": {
            "code": "validation_error",
            "message": message,
            "fields": fields or {},
            "revision": revision,
        }
    }


MAX_QUALITY_RESPONSE_BYTES = 256 * 1024


def _quality_response(report: dict[str, object]):
    status_code = 422 if report["status"] == "REJECTED" else 200
    content: dict[str, object] = {"data": report}
    if status_code == 422:
        content.update(_error("Veri kalite kontrolü başarısız.", fields={"file": "Veri kalite raporunda hata var."}))
    response = JSONResponse(
        status_code=status_code,
        content=content,
        headers={"Cache-Control": "no-store"},
    )
    if len(response.body) > MAX_QUALITY_RESPONSE_BYTES:
        return _problem(
            422,
            "QUALITY_RESPONSE_TOO_LARGE",
            "Veri kalite raporu çok büyük",
            "Veri kalite raporu izin verilen response byte sınırını aşıyor.",
        )
    return response


def _load_config(profile_id: str = "paper") -> dict[str, Any]:
    global _PAPER_CONFIG_CACHE
    if profile_id == "paper":
        mtime_ns = CONFIG_PATH.stat().st_mtime_ns
        if _PAPER_CONFIG_CACHE is None or _PAPER_CONFIG_CACHE[0] != mtime_ns:
            with CONFIG_PATH.open(encoding="utf-8") as handle:
                _PAPER_CONFIG_CACHE = (mtime_ns, json.load(handle))
        return deepcopy(_PAPER_CONFIG_CACHE[1])
    _profile, raw_config = load_historical_profile_config(ROOT, profile_id)
    return raw_config


def _profile_response(profile_id: str) -> HistoricalProfileResponse:
    profile = get_historical_profile(profile_id)
    return HistoricalProfileResponse(
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        label=profile.label,
        expected_dataset_id=profile.expected_dataset_id,
        venue_filter_provenance=profile.venue_filter_provenance,
        historical_filter_claim=profile.historical_filter_claim,
        anchor_source=profile.anchor_source,
    )


def _fixed_slice_profile_response(profile_id: str) -> HistoricalFixedSliceProfileResponse:
    profile = get_historical_profile(profile_id)
    return HistoricalFixedSliceProfileResponse(
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        label=profile.label,
        expected_dataset_id=profile.expected_dataset_id,
        venue_filter_provenance=profile.venue_filter_provenance,
        historical_filter_claim=profile.historical_filter_claim,
        anchor_source=profile.anchor_source,
        simulation_model="historical_ohlcv_partial_fixed_v1",
        slice_qty=profile.slice_qty,
    )


def _profile_catalog_response(profile: HistoricalProfile) -> HistoricalProfileResponse | HistoricalFixedSliceProfileResponse:
    if profile.simulation_model == "historical_ohlcv_partial_fixed_v1":
        return _fixed_slice_profile_response(profile.profile_id)
    return HistoricalProfileResponse(
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        label=profile.label,
        expected_dataset_id=profile.expected_dataset_id,
        venue_filter_provenance=profile.venue_filter_provenance,
        historical_filter_claim=profile.historical_filter_claim,
        anchor_source=profile.anchor_source,
    )


def _localized_numeric_error(name: str, exc: ValueError) -> str:
    if "Financial values" in str(exc):
        return "Noktasız ondalık sayı girin."
    if "Expected positive value" in str(exc):
        return f"{FIELD_LABELS[name]} pozitif olmalıdır."
    return str(exc)


def _validate_preview_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    if not isinstance(payload, dict):
        return None, {"body": "JSON gövdesi nesne olmalıdır."}
    unknown = set(payload) - PREVIEW_FIELDS
    missing = PREVIEW_FIELDS - set(payload)
    fields: dict[str, str] = {}
    if unknown:
        fields["body"] = "Bilinmeyen alanlar: " + ", ".join(sorted(unknown))
    if missing:
        fields["body"] = (
            fields.get("body", "")
            + (" " if fields.get("body") else "")
            + "Eksik alanlar: "
            + ", ".join(sorted(missing))
        )
    for name in ("anchor", "safety_qty", "deviation"):
        if name in payload and not isinstance(payload[name], str):
            fields[name] = "Finansal değer noktasız ondalık JSON string olmalıdır."
        elif name in payload and isinstance(payload[name], str):
            try:
                positive(payload[name])
            except ValueError as exc:
                fields[name] = _localized_numeric_error(name, exc)
    if "safety_count" in payload and type(payload["safety_count"]) is not int:
        fields["safety_count"] = "Safety sayısı tam sayı olmalıdır."
    elif "safety_count" in payload and not 0 <= payload["safety_count"] <= 50:
        fields["safety_count"] = "Safety sayısı 0 ile 50 arasında olmalıdır."
    if "revision" in payload and type(payload["revision"]) is not int:
        fields["revision"] = "Revision tam sayı olmalıdır."
    if fields:
        return None, fields
    return payload, {}


def _calculate_preview(payload: dict[str, object]) -> dict[str, object]:
    config = _load_config()
    config.update(
        {
            "safety_qty": payload["safety_qty"],
            "safety_count": payload["safety_count"],
            "deviation": payload["deviation"],
        }
    )
    result = preview(config, payload["anchor"])
    result["revision"] = payload["revision"]
    return result


app = FastAPI(title="DCABOT Offline API", version="0.1.0")
app.router.route_class = BoundedAPIRoute


@app.get("/api/historical-profiles", response_model=list[HistoricalProfileResponse | HistoricalFixedSliceProfileResponse])
def list_profiles(response: Response):
    response.headers["Cache-Control"] = "no-store"
    return [_profile_catalog_response(profile) for profile in list_historical_profiles()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type", "X-Filename"],
)


@app.exception_handler(RequestValidationError)
async def request_validation_error(_request: Request, exc: RequestValidationError):
    if _request.url.path in {
        "/api/dataset-selection",
        "/api/dataset-downloads",
        "/api/historical-runs/validate",
        "/api/historical-runs/simulate",
        "/api/historical-runs/simulate-base-limit",
        "/api/historical-runs",
    }:
        errors = [
            {
                "field": ".".join(str(part) for part in error["loc"] if part != "body"),
                "code": "INVALID_REQUEST",
            }
            for error in exc.errors()
        ]
        malformed_json = any(error["type"] == "json_invalid" for error in exc.errors())
        return _problem(
            400 if malformed_json else 422,
            "MALFORMED_JSON" if malformed_json else "REQUEST_VALIDATION_FAILED",
            "İstek gövdesi geçersiz" if malformed_json else "İstek doğrulanamadı",
            "JSON gövdesi okunamadı." if malformed_json else "Bir veya daha fazla alan geçersiz.",
            errors=errors,
        )
    fields = {
        ".".join(str(part) for part in error["loc"] if part != "body"): error["msg"]
        for error in exc.errors()
    }
    return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"status": "ok", "mode": "offline", "trading_enabled": False}


@app.get("/api/capabilities")
def capabilities() -> dict[str, object]:
    return {
        "mode": "offline",
        "data_mode": "HISTORY_LOCAL",
        "execution_mode": "SIMULATED",
        "trading_enabled": False,
        "features": {"preview": True, "historical_import": False, "testnet": False},
    }


@app.get(
    "/api/venue-snapshots/binance-spot-testnet",
    response_model=BinanceTestnetExchangeInfoResponse,
)
def get_binance_testnet_exchange_info(
    symbol: BinanceTestnetSymbol,
    response: Response,
) -> BinanceTestnetExchangeInfoResponse | JSONResponse:
    """Return one credential-free public Binance Spot Testnet symbol snapshot."""

    response.headers["Cache-Control"] = "no-store"
    try:
        snapshot = fetch_binance_testnet_exchange_info(symbol)
    except BinanceTestnetPublicError as exc:
        if exc.code == "TESTNET_SYMBOL_NOT_FOUND":
            return _problem(
                404,
                exc.code,
                "Testnet symbol bulunamadı",
                "İstenen symbol public exchangeInfo snapshot içinde yok.",
            )
        if exc.code.startswith("TESTNET_RESPONSE") or exc.code == "TESTNET_ENCODING_INVALID":
            return _problem(
                502,
                exc.code,
                "Testnet public snapshot geçersiz",
                "Binance public snapshot güvenli sözleşmeye uymuyor.",
            )
        return _problem(
            503,
            exc.code,
            "Binance Testnet public verisine ulaşılamadı",
            "Public Testnet snapshot şu anda alınamadı.",
        )
    return BinanceTestnetExchangeInfoResponse(
        environment=snapshot.environment,
        symbol=snapshot.symbol,
        status=snapshot.status,
        base_asset=snapshot.base_asset,
        quote_asset=snapshot.quote_asset,
        permissions=[*snapshot.permissions],
        permission_sets=[[*permission_set] for permission_set in snapshot.permission_sets],
        order_types=[*snapshot.order_types],
        filters=[dict(item) for item in snapshot.filters],
        exchange_filters=[dict(item) for item in snapshot.exchange_filters],
        rate_limits=[dict(item) for item in snapshot.rate_limits],
        response_sha256=snapshot.response_sha256,
        observed_at_us=snapshot.observed_at_us,
        read_only=True,
        credential_required=False,
    )


def _testnet_credential_id() -> str | None:
    raw = os.getenv("DCABOT_TESTNET_CREDENTIAL_ID")
    return raw.strip() if raw and raw.strip() else None


def _testnet_not_configured() -> JSONResponse:
    return _problem(
        409,
        "TESTNET_CREDENTIAL_NOT_CONFIGURED",
        "Testnet credential yapılandırılmadı",
        "DCABOT_TESTNET_CREDENTIAL_ID ayarlanmadı veya tools/configure_testnet_credential.py hiç çalıştırılmadı.",
    )


@app.get("/api/testnet/account", response_model=BinanceTestnetAccountResponse)
def get_binance_testnet_account(response: Response) -> BinanceTestnetAccountResponse | JSONResponse:
    """Return one signed, read-only Testnet account snapshot. No mutation endpoint is reachable."""

    response.headers["Cache-Control"] = "no-store"
    credential_id = _testnet_credential_id()
    if credential_id is None:
        return _testnet_not_configured()
    try:
        snapshot = fetch_binance_testnet_account(
            credential_id, provider=WindowsCredentialManagerProvider()
        )
    except (BinanceTestnetAccountError, SignedRequestError) as exc:
        return _testnet_account_problem(exc.code)
    return BinanceTestnetAccountResponse(
        environment="BINANCE_SPOT_TESTNET",
        account_type=snapshot.account_type,
        can_trade=snapshot.can_trade,
        can_withdraw=snapshot.can_withdraw,
        can_deposit=snapshot.can_deposit,
        permissions=[*snapshot.permissions],
        update_time_ms=snapshot.update_time_ms,
        balances_count=snapshot.balances_count,
        balances=[
            BinanceTestnetBalanceResponse(asset=item.asset, free=item.free, locked=item.locked)
            for item in snapshot.balances
        ],
        response_sha256=snapshot.response_sha256,
        observed_at_us=snapshot.observed_at_us,
        read_only=True,
        credential_required=True,
    )


@app.get("/api/testnet/open-orders", response_model=BinanceTestnetOpenOrdersResponse)
def get_binance_testnet_open_orders(
    response: Response, symbol: str | None = None
) -> BinanceTestnetOpenOrdersResponse | JSONResponse:
    """Return the account's current open orders. No order/cancel endpoint is reachable."""

    response.headers["Cache-Control"] = "no-store"
    credential_id = _testnet_credential_id()
    if credential_id is None:
        return _testnet_not_configured()
    try:
        orders = fetch_binance_testnet_open_orders(
            credential_id, provider=WindowsCredentialManagerProvider(), symbol=symbol
        )
    except (BinanceTestnetAccountError, SignedRequestError) as exc:
        return _testnet_account_problem(exc.code)
    return BinanceTestnetOpenOrdersResponse(
        environment="BINANCE_SPOT_TESTNET",
        orders=[
            BinanceTestnetOpenOrderResponse(
                symbol=item.symbol,
                order_id=item.order_id,
                client_order_id=item.client_order_id,
                side=item.side,
                type=item.type,
                status=item.status,
                price=item.price,
                orig_qty=item.orig_qty,
                executed_qty=item.executed_qty,
                time_ms=item.time_ms,
                update_time_ms=item.update_time_ms,
            )
            for item in orders
        ],
        count=len(orders),
        read_only=True,
        credential_required=True,
    )


def _testnet_account_problem(code: str) -> JSONResponse:
    if code in ("TESTNET_ACCOUNT_RESPONSE_INVALID", "TESTNET_OPEN_ORDERS_RESPONSE_INVALID"):
        return _problem(
            502,
            code,
            "Testnet hesap yanıtı geçersiz",
            "Binance Testnet yanıtı güvenli sözleşmeye uymuyor.",
        )
    if code in ("TESTNET_ACCOUNT_HTTP_ERROR", "TESTNET_OPEN_ORDERS_HTTP_ERROR"):
        return _problem(
            502,
            code,
            "Testnet hesap isteği reddedildi",
            "Binance Testnet imzalı istek başarısız oldu.",
        )
    if code == "WINDOWS_CREDENTIALS_UNSUPPORTED":
        return _problem(
            409,
            code,
            "Credential deposu kullanılamıyor",
            "Windows Credential Manager yalnız Windows'ta kullanılabilir.",
        )
    return _problem(
        503,
        code,
        "Binance Testnet hesap verisine ulaşılamadı",
        "İmzalı Testnet hesap/açık emir isteği şu anda tamamlanamadı.",
    )


@app.get("/api/datasets", response_model=DatasetListResponse)
def list_datasets(response: Response) -> DatasetListResponse:
    response.headers["Cache-Control"] = "no-store"
    entries = DATASET_CATALOG.list_entries()
    return DatasetListResponse(
        datasets=[_dataset_summary(entry) for entry in entries],
        count=len(entries),
    )


def _dataset_preflight(dataset_id: str) -> tuple[HistoricalDatasetInput, DatasetPreflightResponse] | JSONResponse:
    entries = {entry.dataset_id: entry for entry in DATASET_CATALOG.list_entries()}
    entry = entries.get(dataset_id)
    if entry is None:
        return _problem(
            404,
            "DATASET_NOT_FOUND",
            "Dataset bulunamadı",
            "İstenen dataset tanımı katalogda yok.",
        )
    if entry.quality_status == "MISSING":
        return _problem(
            409,
            "DATASET_CACHE_MISSING",
            "Dataset cache’i eksik",
            "Dataset tanımlı fakat doğrulanmış yerel cache artifact’ı yok.",
        )
    if entry.quality_status == "CORRUPT":
        return _problem(
            409,
            "DATASET_CACHE_CORRUPT",
            "Dataset cache’i bozuk",
            "Dataset yerel bütünlük doğrulamasından geçemedi.",
        )
    try:
        loaded = load_verified_dataset(DATASET_CATALOG.select(dataset_id))
    except (CatalogError, HistoricalInputError):
        return _problem(
            409,
            "DATASET_PREFLIGHT_UNAVAILABLE",
            "Ön kontrol gösterilemedi",
            "Dataset seçimi korunuyor. Özet bilgileri şu anda alınamadı.",
        )
    if entry.byte_count is None:
        return _problem(
            409,
            "DATASET_PREFLIGHT_UNAVAILABLE",
            "Ön kontrol gösterilemedi",
            "Dataset seçimi korunuyor. Özet bilgileri şu anda alınamadı.",
        )
    return loaded, DatasetPreflightResponse(
        dataset_id=loaded.metadata.dataset_id,
        artifact_status="VERIFIED",
        preflight_status="READY",
        instrument=loaded.metadata.symbol,
        interval=loaded.metadata.interval,
        period_start=date.fromisoformat(loaded.metadata.period_start),
        period_end=date.fromisoformat(loaded.metadata.period_end),
        bar_count=len(loaded.bars),
        timestamp_unit="microseconds",
        timezone="UTC",
        data_quality_status="UNKNOWN",
        data_quality_message="Bu fazda analitik veri kalite uyarısı üretilmiyor.",
        artifact=ArtifactSummary(sha256=loaded.metadata.artifact_sha256, byte_size=entry.byte_count),
        read_only=True,
    )


@app.put("/api/dataset-selection", response_model=DatasetSelectionResponse)
def select_dataset(payload: DatasetSelectionRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    entries = {entry.dataset_id: entry for entry in DATASET_CATALOG.list_entries()}
    entry = entries.get(payload.dataset_id)
    if entry is None:
        return _problem(
            404,
            "DATASET_NOT_FOUND",
            "Dataset bulunamadı",
            "İstenen dataset tanımı katalogda yok.",
        )
    if entry.quality_status == "MISSING":
        return _problem(
            409,
            "DATASET_CACHE_MISSING",
            "Dataset cache’i eksik",
            "Dataset tanımlı fakat doğrulanmış yerel cache artifact’ı yok.",
        )
    if entry.quality_status == "CORRUPT":
        return _problem(
            409,
            "DATASET_CACHE_CORRUPT",
            "Dataset cache’i bozuk",
            "Dataset yerel bütünlük doğrulamasından geçemedi.",
        )
    try:
        selection = DATASET_CATALOG.select(payload.dataset_id)
    except CatalogError:
        return _problem(
            409,
            "DATASET_CACHE_CHANGED",
            "Dataset cache’i değişti",
            "Doğrulama sırasında dataset cache’i değişti ve seçilmedi.",
        )
    return DatasetSelectionResponse(selected=_dataset_summary(selection.entry))


@app.get("/api/datasets/{dataset_id}/preflight", response_model=DatasetPreflightResponse)
def get_dataset_preflight(dataset_id: str, response: Response):
    response.headers["Cache-Control"] = "no-store"
    result = _dataset_preflight(dataset_id)
    return result if isinstance(result, JSONResponse) else result[1]


@app.get("/api/datasets/{dataset_id}/chart-data", response_model=HistoricalChartDataResponse)
def get_dataset_chart_data(dataset_id: str, response: Response):
    response.headers["Cache-Control"] = "no-store"
    result = _dataset_preflight(dataset_id)
    if isinstance(result, JSONResponse):
        return result
    loaded, _preflight = result
    try:
        bars = build_historical_chart_data(loaded)
    except HistoricalChartDataError:
        return _problem(
            409,
            "CHART_SCOPE_NOT_ADMISSIBLE",
            "Chart verisi hazırlanamadı",
            "Dataset chart için izin verilen bar kapsamını aşıyor.",
        )
    return HistoricalChartDataResponse(
        dataset_id=loaded.metadata.dataset_id,
        artifact_sha256=loaded.metadata.artifact_sha256,
        model_id="historical_ohlcv_v1",
        period_start=date.fromisoformat(loaded.metadata.period_start),
        period_end=date.fromisoformat(loaded.metadata.period_end),
        processed_bar_count=len(bars),
        bars=[
            HistoricalChartBarResponse(
                bar_index=bar.bar_index,
                open_time_us=bar.open_time_us,
                close_time_us=bar.close_time_us,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
            )
            for bar in bars
        ],
    )


@app.get("/api/datasets/{dataset_id}/run-plan", response_model=DatasetRunPlanResponse)
def get_dataset_run_plan(dataset_id: str, response: Response, profile_id: ProfileId = "paper"):
    response.headers["Cache-Control"] = "no-store"
    result = _dataset_preflight(dataset_id)
    if isinstance(result, JSONResponse):
        return result
    loaded, preflight = result
    try:
        profile = get_historical_profile(profile_id)
        if profile.expected_dataset_id is not None and profile.expected_dataset_id != loaded.metadata.dataset_id:
            raise HistoricalProfileError("PROFILE_DATASET_CONFLICT", "Historical profile bu dataset ile eşleşmiyor.")
        plan = build_historical_run_plan(
            loaded,
            _load_config(profile_id),
            simulation_model=profile.simulation_model,
            slice_qty=profile.slice_qty,
        )
    except (HistoricalRunPlanError, HistoricalProfileError) as exc:
        return _problem(
            409,
            getattr(exc, "code", "DATASET_RUN_PLAN_UNAVAILABLE"),
            "Koşu planı hazırlanamadı",
            "Dataset seçimi korunuyor. Aktif offline config bu dataset’e bağlanamadı.",
        )
    config = plan.config
    if profile.simulation_model == "historical_ohlcv_partial_fixed_v1":
        plan_config = HistoricalFixedSlicePlanConfigResponse(
            schema_version=config.schema_version,
            config_hash=config.config_hash,
            mode=config.mode,
            symbol=config.symbol,
            base_asset=config.base_asset,
            quote_asset=config.quote_asset,
            base_qty=config.base_qty,
            safety_qty=config.safety_qty,
            safety_count=config.safety_count,
            deviation=config.deviation,
            target_mode=config.target_mode,
            fee_rate=config.fee_rate,
            slippage=config.slippage,
            simulation_model=config.simulation_model,
            slice_qty=config.slice_qty,
        )
        plan_profile = _fixed_slice_profile_response(profile.profile_id)
    else:
        plan_config = DatasetRunPlanConfigResponse(
            schema_version=config.schema_version,
            config_hash=config.config_hash,
            mode=config.mode,
            symbol=config.symbol,
            base_asset=config.base_asset,
            quote_asset=config.quote_asset,
            base_qty=config.base_qty,
            safety_qty=config.safety_qty,
            safety_count=config.safety_count,
            deviation=config.deviation,
            target_mode=config.target_mode,
            fee_rate=config.fee_rate,
            slippage=config.slippage,
        )
        plan_profile = _profile_response(profile.profile_id)
    return DatasetRunPlanResponse(
        dataset=preflight,
        config=plan_config,
        profile=plan_profile,
        execution_mode=plan.execution_mode,
        run_status=plan.run_status,
        read_only=plan.read_only,
    )


@app.post("/api/historical-runs/validate", response_model=HistoricalRunValidationResponse)
def validate_historical_run(payload: HistoricalRunValidationRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    result = _dataset_preflight(payload.dataset_id)
    if isinstance(result, JSONResponse):
        return result
    loaded, _preflight = result
    try:
        profile = get_historical_profile(payload.profile_id)
        if profile.expected_dataset_id is not None and profile.expected_dataset_id != loaded.metadata.dataset_id:
            raise HistoricalProfileError("PROFILE_DATASET_CONFLICT", "Historical profile bu dataset ile eşleşmiyor.")
        plan = build_historical_run_plan(
            loaded,
            _load_config(payload.profile_id),
            simulation_model=profile.simulation_model,
            slice_qty=profile.slice_qty,
        )
    except (HistoricalRunPlanError, HistoricalProfileError) as exc:
        return _problem(
            409,
            getattr(exc, "code", "CONFIG_CONTEXT_UNAVAILABLE"),
            "Koşu doğrulaması hazır değil",
            "Dataset ve aktif offline config doğrulama bağlamı eşleşmiyor.",
        )
    try:
        validate_historical_run_request(
            loaded,
            plan,
            dataset_id=payload.dataset_id,
            artifact_sha256=payload.artifact_sha256,
            config_hash=payload.config_hash,
            execution_mode=payload.execution_mode,
            simulation_model=payload.simulation_model,
        )
    except HistoricalRunValidationError as exc:
        return _problem(409, exc.code, "Koşu doğrulaması reddedildi", str(exc))
    return HistoricalRunValidationResponse(
        validation_status="READY",
        run_status="NOT_STARTED",
        read_only=True,
        offline=True,
        execution_mode="SIMULATED",
        dataset=HistoricalRunValidationDatasetResponse(
            dataset_id=loaded.metadata.dataset_id,
            artifact_sha256=loaded.metadata.artifact_sha256,
            status="VERIFIED",
            instrument=loaded.metadata.symbol,
            interval=loaded.metadata.interval,
            period_start=date.fromisoformat(loaded.metadata.period_start),
            period_end=date.fromisoformat(loaded.metadata.period_end),
            bar_count=len(loaded.bars),
        ),
        config=(
            HistoricalFixedSliceValidationConfigResponse(
                schema_version=plan.config.schema_version,
                config_hash=plan.config.config_hash,
                simulation_model=plan.config.simulation_model,
                slice_qty=plan.config.slice_qty,
            )
            if profile.simulation_model == "historical_ohlcv_partial_fixed_v1"
            else HistoricalRunValidationConfigResponse(
                schema_version=plan.config.schema_version,
                config_hash=plan.config.config_hash,
            )
        ),
        profile=(
            _fixed_slice_profile_response(profile.profile_id)
            if profile.simulation_model == "historical_ohlcv_partial_fixed_v1"
            else _profile_response(profile.profile_id)
        ),
    )


def _historical_simulation_response(
    dataset: HistoricalDatasetInput,
    plan,
    result: HistoricalSimulationResult,
    execution_id: str,
    profile,
) -> HistoricalSimulationResponse:
    summary = result.summary
    ambiguity = None
    if result.first_ambiguous_bar_index is not None:
        ambiguity = HistoricalSimulationAmbiguityResponse(
            bar_index=result.first_ambiguous_bar_index,
            code="AMBIGUOUS_OHLC_PATH",
        )
    deal_count = max((action.deal_sequence for action in result.actions), default=0)
    completed_deal_count = max(deal_count - (1 if result.position_status == "OPEN_AT_END" else 0), 0)
    return HistoricalSimulationResponse(
        execution_id=execution_id,
        execution_status=result.execution_status,
        application_code=result.application_code,
        persisted=False,
        dataset=HistoricalSimulationDatasetResponse(
            dataset_id=dataset.metadata.dataset_id,
            artifact_sha256=dataset.metadata.artifact_sha256,
            period_start=date.fromisoformat(dataset.metadata.period_start),
            period_end=date.fromisoformat(dataset.metadata.period_end),
            processed_bar_count=result.processed_bar_count,
        ),
        config=HistoricalSimulationConfigResponse(
            schema_version=plan.config.schema_version,
            config_hash=plan.config.config_hash,
        ),
        profile=_profile_response(profile.profile_id),
        assumptions=HistoricalSimulationAssumptionsResponse(
            model="historical_ohlcv_v1",
            bar_visibility="CLOSED_ONLY",
            intrabar_path="NOT_INFERRED",
            max_actions_per_bar=1,
            fee_model="CONFIGURED_RATE_ON_EACH_FILL",
            slippage_model="CONFIGURED_DETERMINISTIC_ON_EACH_FILL",
            funding="NOT_MODELED",
            exchange_mark="NOT_AVAILABLE",
            force_close_at_end=False,
        ),
        actions=[
            HistoricalSimulationActionResponse(
                bar_index=action.bar_index,
                open_time_us=action.open_time_us,
                role=action.role,
                raw_reference=action.raw_reference,
                fill_price=action.fill_price,
                quantity=action.quantity,
                fee=action.fee,
            )
            for action in result.actions
        ],
        summary=HistoricalSimulationSummaryResponse(
            symbol=summary["symbol"],
            qty=summary["qty"],
            cost=summary["cost"],
            realized_gross=summary["realized_gross"],
            fees=summary["fees"],
            funding=summary["funding"],
            realized_net_after_all_costs=summary["realized_net_after_all_costs"],
            unrealized=summary["unrealized"],
            equity=summary["equity"],
            anchor=summary["anchor"],
            take_profit_price=summary["take_profit_price"],
            entry_notional=summary["entry_notional"],
            peak_equity=summary["peak_equity"],
            max_drawdown=summary["max_drawdown"],
            current_drawdown=summary.get("current_drawdown"),
            action_count=summary["action_count"],
            average_entry_price=summary.get("average_entry_price"),
            time_in_position_us=summary["time_in_position_us"],
            deal_count=deal_count,
            completed_deal_count=completed_deal_count,
            position_status=result.position_status,
            funding_status=result.funding_status,
            mark_status=result.mark_status,
        ),
        ambiguity=ambiguity,
        explanations=_read_only_explanation_responses(result),
    )


def _historical_fixed_slice_response(
    dataset: HistoricalDatasetInput,
    plan,
    result: HistoricalFixedSliceResult,
    profile,
    *,
    expose_committed_prefix: bool,
) -> HistoricalFixedSliceSimulationResponse:
    summary = result.summary
    ambiguity = None
    if result.first_ambiguous_bar_index is not None:
        ambiguity = HistoricalFixedSliceAmbiguityResponse(
            bar_index=result.first_ambiguous_bar_index,
            open_time_us=dataset.bars[result.first_ambiguous_bar_index - 1].open_time_us,
            code="AMBIGUOUS_OHLC_PATH",
        )
    complete_execution = result.execution_status == "COMPLETED"
    committed_prefix = result.execution_status == "INDETERMINATE" and expose_committed_prefix and bool(result.actions)
    public_actions = result.actions if complete_execution or committed_prefix else ()
    last_processed_bar = dataset.bars[result.processed_bar_count - 1]
    authority_mode = "FULL_RUN" if complete_execution else "COMMITTED_PREFIX" if committed_prefix else "NONE"
    action_authority = HistoricalFixedSliceActionAuthorityResponse(
        mode=authority_mode,
        economic_state_commit_scope=("FULL_RUN" if complete_execution else "PREFIX_ONLY" if committed_prefix else "NONE"),
        committed_through_bar_index=result.processed_bar_count if complete_execution or committed_prefix else None,
        committed_through_open_time_us=last_processed_bar.open_time_us if complete_execution or committed_prefix else None,
        ambiguity_bar_index=result.first_ambiguous_bar_index,
        contains_ambiguity_bar_actions=False,
        contains_post_ambiguity_actions=False,
        complete_history=complete_execution,
        economic_state_committed=complete_execution or committed_prefix,
        committed_through_event_sequence=public_actions[-1].event_sequence if public_actions else None,
        action_count=len(public_actions),
    )
    return HistoricalFixedSliceSimulationResponse(
        complete_execution=complete_execution,
        execution_status=result.execution_status,
        application_code=result.application_code,
        persisted=False,
        dataset=HistoricalSimulationDatasetResponse(
            dataset_id=dataset.metadata.dataset_id,
            artifact_sha256=dataset.metadata.artifact_sha256,
            period_start=date.fromisoformat(dataset.metadata.period_start),
            period_end=date.fromisoformat(dataset.metadata.period_end),
            processed_bar_count=result.processed_bar_count,
        ),
        config=HistoricalFixedSliceConfigResponse(
            schema_version=plan.config.schema_version,
            config_hash=plan.config.config_hash,
            slice_qty=plan.config.slice_qty,
            quantity_unit="BASE_ASSET",
        ),
        profile=_fixed_slice_profile_response(profile.profile_id),
        assumptions=HistoricalFixedSliceAssumptionsResponse(
            model="historical_ohlcv_partial_fixed_v1",
            bar_visibility="CLOSED_ONLY",
            intrabar_path="NOT_INFERRED",
            max_actions_per_bar=1,
            fill_policy="FIXED_SLICE_ON_OHLC_TOUCH",
            fee_model="CONFIGURED_RATE_ON_EACH_FILL",
            slippage_model="CONFIGURED_DETERMINISTIC_ON_EACH_FILL",
            funding="NOT_MODELED",
            exchange_mark="NOT_AVAILABLE",
            synthetic_cancel_at_eof=False,
            persistence="NOT_SUPPORTED_IN_THIS_PHASE",
        ),
        action_authority=action_authority,
        marker_authority="FULL" if complete_execution else "PREFIX_BOUNDARY_ONLY" if committed_prefix else "NONE",
        marker_kind="TRADE_EXECUTION" if complete_execution else "INCOMPLETE_BOUNDARY" if committed_prefix else "NONE",
        actions=[
            HistoricalFixedSliceActionResponse(
                event_sequence=action.event_sequence,
                bar_index=action.bar_index,
                open_time_us=action.open_time_us,
                action_type=action.action_type,
                role=action.role,
                order_id=action.order_id,
                execution_id=action.execution_id,
                raw_reference=action.raw_reference,
                fill_price=action.fill_price,
                quantity=action.quantity,
                fee=action.fee,
                fee_asset=action.fee_asset,
                order_status_after=action.order_status_after,
                original_qty=action.original_qty,
                cumulative_filled_qty=action.cumulative_filled_qty,
                leaves_qty=action.leaves_qty,
                canceled_qty=action.canceled_qty,
                fill_provenance=action.fill_provenance,
            )
            for action in public_actions
        ],
        final_economic_summary=HistoricalFixedSliceSummaryResponse(
            symbol=summary["symbol"],
            qty=summary["qty"],
            cost=summary["cost"],
            realized_gross=summary["realized_gross"],
            fees=summary["fees"],
            funding=summary["funding"],
            realized_net_after_all_costs=summary["realized_net_after_all_costs"],
            unrealized=summary["unrealized"],
            equity=summary["equity"],
            anchor=summary["anchor"],
            take_profit_price=summary["take_profit_price"],
            entry_notional=summary["entry_notional"],
            position_status=result.position_status,
            funding_status=summary.get("funding_status", "NOT_MODELED"),
            mark_status=summary.get("mark_status", "NOT_AVAILABLE"),
        ) if complete_execution else None,
        ambiguity=ambiguity,
        explanations=_read_only_explanation_responses(result),
    )


def _read_only_explanation_responses(
    result: HistoricalSimulationResult | HistoricalFixedSliceResult,
) -> list[ReadOnlyExplanationResponse]:
    return [
        ReadOnlyExplanationResponse(
            code=explanation.code,
            severity=explanation.severity,
            title=explanation.title,
            message=explanation.message,
            source=explanation.source,
            context=dict(explanation.context),
        )
        for explanation in explain_historical_result(result)
    ]


def _historical_base_limit_response(
    dataset: HistoricalDatasetInput,
    plan,
    result,
    order: FixedLimitOrder,
    profile,
    slice_qty: str,
) -> HistoricalBaseLimitSimulationResponse:
    core_order = result.state.orders[order.order_id]
    order_status = "OPEN"
    if result.status == "INDETERMINATE":
        order_status = "INDETERMINATE"
    elif core_order.complete:
        order_status = "FILLED"
    elif core_order.filled > 0:
        order_status = "PARTIALLY_FILLED"
    ambiguity = None
    if result.status == "INDETERMINATE":
        ambiguity_bar_index = result.processed_bar_count + 1
        ambiguity = HistoricalFixedSliceAmbiguityResponse(
            bar_index=ambiguity_bar_index,
            open_time_us=dataset.bars[ambiguity_bar_index - 1].open_time_us,
            code="AMBIGUOUS_OHLC_PATH",
        )
    return HistoricalBaseLimitSimulationResponse(
        execution_id=None,
        execution_status=result.status,
        application_code=result.application_code,
        model=result.model,
        policy=result.policy,
        production_ready=False,
        persisted=False,
        dataset=HistoricalSimulationDatasetResponse(
            dataset_id=dataset.metadata.dataset_id,
            artifact_sha256=dataset.metadata.artifact_sha256,
            period_start=date.fromisoformat(dataset.metadata.period_start),
            period_end=date.fromisoformat(dataset.metadata.period_end),
            processed_bar_count=result.processed_bar_count,
        ),
        config_hash=plan.config.config_hash,
        binding_identity_sha256=base_limit_binding_identity_sha256(
            dataset_id=dataset.metadata.dataset_id,
            artifact_sha256=dataset.metadata.artifact_sha256,
            profile_id=profile.profile_id,
            profile_version=profile.profile_version,
            config_hash=plan.config.config_hash,
            order=order,
            slice_qty=slice_qty,
        ),
        profile=_profile_response(profile.profile_id),
        provenance=HistoricalBaseLimitProvenanceResponse(
            execution_kind="SYNTHETIC_OHLCV_FILL",
            venue_replay=False,
            role="BASE",
            placement_policy="ACTIVE_NEXT_BAR",
            equality_policy="OBSERVE_ONLY",
            price_policy="DECLARED_LIMIT_ONLY",
            liquidity_policy="FIXED_SLICE_NO_MARKET_VOLUME",
            ambiguity_policy="FAIL_CLOSED",
        ),
        reserve=HistoricalBaseLimitReserveResponse(
            model=result.reserve_model,
            amount=result.reserve_amount,
            asset=result.reserve_asset,
        ),
        order=HistoricalBaseLimitOrderResponse(
            order_id=order.order_id,
            role="BASE",
            side="BUY",
            limit_price=order.limit_price,
            original_qty=order.original_qty,
            slice_qty=slice_qty,
            placement_bar_index=order.placement_bar_index,
            placement_open_time_us=order.placement_open_time_us,
        ),
        state=HistoricalBaseLimitStateResponse(
            order_status=order_status,
            original_qty=exact_text(core_order.qty),
            filled_qty=exact_text(core_order.filled),
            leaves_qty=exact_text(core_order.leaves),
            position_status="OPEN" if result.state.position.qty > 0 else "NO_POSITION",
            position_qty=exact_text(result.state.position.qty),
            anchor=exact_text(result.state.anchor) if result.state.anchor is not None else None,
        ),
        observations=[
            HistoricalBaseLimitObservationResponse(
                bar_index=observation.bar_index,
                open_time_us=observation.open_time_us,
                kind=observation.kind,
                trigger_observed=observation.trigger_observed,
                fill_committed=observation.fill_committed,
            )
            for observation in result.observations
        ],
        actions=[
            HistoricalBaseLimitActionResponse(
                event_sequence=action.event_sequence,
                bar_index=action.bar_index,
                open_time_us=action.open_time_us,
                action_type="FULL_FILL" if action.leaves_qty == "0" else "PARTIAL_FILL",
                role="BASE",
                order_id=action.order_id,
                fill_price=action.fill_price,
                quantity=action.quantity,
                cumulative_filled_qty=action.cumulative_filled_qty,
                leaves_qty=action.leaves_qty,
                fill_provenance="SYNTHETIC_OHLCV_FIXED_LIMIT",
            )
            for action in result.actions
            if result.status != "INDETERMINATE"
        ],
        ambiguity=ambiguity,
    )


@app.post(
    "/api/historical-runs/simulate-base-limit",
    response_model=HistoricalBaseLimitSimulationResponse,
)
def simulate_base_limit_historical_run(
    payload: HistoricalBaseLimitSimulationRequest,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    if payload.profile_id != "historical_demo_btcusdt_1h_v1":
        return _problem(
            409,
            "BASE_LIMIT_PROFILE_REQUIRED",
            "BASE limit profili desteklenmiyor",
            "Bu contract yalnız açık historical demo profile ile kullanılabilir.",
        )
    if not HISTORICAL_EXECUTION_LOCK.acquire(blocking=False):
        return _problem(
            409,
            "EXECUTION_BUSY",
            "Simülasyon meşgul",
            "Başka bir tarihsel simülasyon çalışıyor.",
        )
    try:
        preflight = _dataset_preflight(payload.dataset_id)
        if isinstance(preflight, JSONResponse):
            return preflight
        loaded, _preflight = preflight
        try:
            profile = get_historical_profile(payload.profile_id)
            if profile.expected_dataset_id != loaded.metadata.dataset_id:
                raise HistoricalProfileError("PROFILE_DATASET_CONFLICT", "Historical profile bu dataset ile eşleşmiyor.")
            raw_config = _load_config(payload.profile_id)
            plan = build_historical_run_plan(loaded, raw_config)
            validate_historical_run_request(
                loaded,
                plan,
                dataset_id=payload.dataset_id,
                artifact_sha256=payload.artifact_sha256,
                config_hash=payload.config_hash,
                execution_mode=payload.execution_mode,
                simulation_model="historical_ohlcv_v1",
            )
            config = Config.parse(raw_config)
        except (HistoricalProfileError, HistoricalRunPlanError, HistoricalRunValidationError) as exc:
            return _problem(
                409,
                getattr(exc, "code", "BASE_LIMIT_CONTEXT_UNAVAILABLE"),
                "BASE limit doğrulaması hazır değil",
                "Dataset, profile ve offline config bağlamı eşleşmiyor.",
            )
        try:
            limit_price = exact_text(number(payload.limit_price))
            slice_qty = exact_text(number(payload.slice_qty))
        except ValueError:
            return _problem(
                422,
                "INVALID_EXACT_DECIMAL",
                "BASE limit sayısal alanı geçersiz",
                "Limit price ve slice quantity noktasız exact decimal string olmalıdır.",
            )
        order = FixedLimitOrder(
            order_id=payload.order_id,
            side="BUY",
            limit_price=limit_price,
            original_qty=exact_text(config.base_qty),
            placement_bar_index=payload.placement_bar_index,
            placement_open_time_us=payload.placement_open_time_us,
        )
        try:
            result = simulate_base_fixed_limit_binding(
                loaded,
                config,
                order,
                slice_qty=slice_qty,
                config_hash=plan.config.config_hash,
            )
        except (HistoricalBaseLimitBindingError, HistoricalFixedLimitError) as exc:
            return _problem(
                422,
                exc.code,
                "BASE limit policy reddedildi",
                "İstek mevcut BASE/core binding sınırları içinde güvenli biçimde çalıştırılamadı.",
            )
        public_result = _historical_base_limit_response(loaded, plan, result, order, profile, slice_qty)
        serialized_size = len(json.dumps(public_result.model_dump(mode="json"), separators=(",", ":")).encode("utf-8"))
        if serialized_size > MAX_HISTORICAL_BASE_LIMIT_RESPONSE_BYTES:
            return _problem(
                422,
                "BASE_LIMIT_RESPONSE_TOO_LARGE",
                "BASE limit sonucu çok büyük",
                "Sonuç response byte sınırını aşıyor.",
            )
        return public_result
    finally:
        HISTORICAL_EXECUTION_LOCK.release()


@app.post(
    "/api/historical-runs/simulate",
    response_model=HistoricalSimulationResponse | HistoricalFixedSliceSimulationResponse,
)
def simulate_historical_run(payload: HistoricalSimulationRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    if payload.action_authority == "COMMITTED_PREFIX" and payload.execution_mode != "historical_ohlcv_partial_fixed_v1":
        return _problem(
            422,
            "UNSUPPORTED_ACTION_AUTHORITY",
            "Aksiyon yetkisi desteklenmiyor",
            "COMMITTED_PREFIX yalnızca historical_ohlcv_partial_fixed_v1 için açıkça desteklenir.",
        )
    if not HISTORICAL_EXECUTION_LOCK.acquire(blocking=False):
        return _problem(
            409,
            "EXECUTION_BUSY",
            "Simülasyon meşgul",
            "Başka bir tarihsel simülasyon çalışıyor.",
        )
    try:
        preflight = _dataset_preflight(payload.dataset_id)
        if isinstance(preflight, JSONResponse):
            return preflight
        loaded, _preflight = preflight
        try:
            profile = get_historical_profile(payload.profile_id)
            if profile.expected_dataset_id is not None and profile.expected_dataset_id != loaded.metadata.dataset_id:
                raise HistoricalProfileError("PROFILE_DATASET_CONFLICT", "Historical profile bu dataset ile eşleşmiyor.")
            raw_config = _load_config(payload.profile_id)
        except HistoricalProfileError as exc:
            return _problem(
                409,
                exc.code,
                "Simülasyon profili kullanılamadı",
                "Seçilen historical profile bu dataset için güvenli biçimde yüklenemedi.",
            )
        try:
            plan = build_historical_run_plan(
                loaded,
                raw_config,
                simulation_model=profile.simulation_model,
                slice_qty=profile.slice_qty,
            )
        except HistoricalRunPlanError as exc:
            code = "SYMBOL_MISMATCH" if exc.code == "DATASET_CONFIG_CONFLICT" else exc.code
            status = 422 if code == "SYMBOL_MISMATCH" else 409
            return _problem(
                status,
                code,
                "Simülasyon doğrulaması hazır değil",
                "Dataset ve aktif offline config uyumlu değil.",
            )
        try:
            validate_historical_run_request(
                loaded,
                plan,
                dataset_id=payload.dataset_id,
                artifact_sha256=payload.artifact_sha256,
                config_hash=payload.config_hash,
                execution_mode=payload.execution_mode,
                simulation_model=payload.execution_mode,
            )
        except HistoricalRunValidationError as exc:
            status = 422 if exc.code == "UNSUPPORTED_EXECUTION_MODE" else 409
            return _problem(status, exc.code, "Simülasyon doğrulaması reddedildi", str(exc))
        try:
            config = Config.parse(raw_config)
            if payload.execution_mode == "historical_ohlcv_partial_fixed_v1":
                result = simulate_historical_fixed_slice(
                    loaded,
                    config,
                    slice_qty=plan.config.slice_qty,
                    config_hash=plan.config.config_hash,
                )
            else:
                result = simulate_historical_ohlcv(
                    loaded,
                    config,
                    config_hash=plan.config.config_hash,
                )
        except HistoricalSimulationError as exc:
            status = 503 if exc.code == "EXECUTION_BUDGET_EXCEEDED" else 422
            return _problem(status, exc.code, "Simülasyon çalıştırılamadı", str(exc))
        if payload.execution_mode == "historical_ohlcv_partial_fixed_v1":
            return _historical_fixed_slice_response(
                loaded,
                plan,
                result,
                profile,
                expose_committed_prefix=payload.action_authority == "COMMITTED_PREFIX",
            )
        try:
            capture = build_historical_run_capture(
                loaded,
                raw_config,
                result,
                config_hash=plan.config.config_hash,
                profile_id=profile.profile_id,
            )
        except HistoricalRunContractError:
            return _problem(
                422,
                "RUN_CAPTURE_INVALID",
                "Simülasyon sonucu kaydedilemedi",
                "Simülasyon sonucu güvenli tarihsel koşu snapshot sözleşmesine uymuyor.",
            )
        execution_id = str(uuid4())
        with HISTORICAL_EXECUTIONS_LOCK:
            HISTORICAL_EXECUTIONS[execution_id] = capture
            while len(HISTORICAL_EXECUTIONS) > MAX_EPHEMERAL_HISTORICAL_EXECUTIONS:
                oldest_execution_id = next(iter(HISTORICAL_EXECUTIONS))
                del HISTORICAL_EXECUTIONS[oldest_execution_id]
        return _historical_simulation_response(loaded, plan, result, execution_id, profile)
    finally:
        HISTORICAL_EXECUTION_LOCK.release()


def _historical_run_created_at() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@app.post("/api/historical-runs", response_model=HistoricalRunSaveResponse)
def save_historical_run(payload: HistoricalRunSaveRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    with HISTORICAL_EXECUTIONS_LOCK:
        capture = HISTORICAL_EXECUTIONS.get(payload.execution_id)
    if capture is None:
        return _problem(
            404,
            "EXECUTION_NOT_FOUND",
            "Simülasyon sonucu bulunamadı",
            "Kaydetme isteği yalnızca mevcut yerel execution kimliğiyle yapılabilir.",
        )
    try:
        with HistoricalRunStore(HISTORICAL_RUNS_PATH) as store:
            saved = store.save(
                capture,
                source_execution_id=payload.execution_id,
                created_at=_historical_run_created_at(),
            )
    except HistoricalRunStoreError as exc:
        if exc.code == "SOURCE_EXECUTION_CONFLICT":
            return _problem(
                409,
                exc.code,
                "Execution kaydı çakıştı",
                "Aynı execution kimliği farklı bir snapshot ile yeniden kullanılamaz.",
            )
        if exc.code in {"RUN_RECORD_TOO_LARGE", "RUN_CAPTURE_INVALID"}:
            return _problem(
                422,
                exc.code,
                "Historical run kaydedilemedi",
                "Tarihsel koşu snapshot’ı güvenli kayıt sınırlarına uymuyor.",
            )
        return _problem(
            503,
            "RUN_STORE_UNAVAILABLE",
            "Historical run store kullanılamıyor",
            "Yerel tarihsel koşu kaydı şu anda tamamlanamadı.",
        )
    input_snapshot = json.loads(saved.capture.input_snapshot_json)
    response.status_code = 201 if saved.created else 200
    item = saved.list_item
    return HistoricalRunSaveResponse(
        run_id=item.run_id,
        created=saved.created,
        record_health=item.record_health,
        execution_status=item.execution_status,
        created_at=item.created_at,
        dataset_id=input_snapshot["dataset_id"],
        symbol=item.symbol,
        interval=item.interval,
        period_start=date.fromisoformat(item.period_start),
        period_end=date.fromisoformat(item.period_end),
        processed_bar_count=item.processed_bar_count,
        position_status=item.position_status,
    )


def _historical_run_store_read_problem(exc: HistoricalRunStoreError):
    if exc.code == "RUN_NOT_FOUND":
        return _problem(
            404,
            exc.code,
            "Historical run bulunamadı",
            "İstenen historical run local store içinde yok.",
        )
    if exc.code == "RUN_ID_INVALID":
        return _problem(
            422,
            exc.code,
            "Historical run kimliği geçersiz",
            "Run kimliği desteklenen UUID biçiminde değil.",
        )
    if exc.code == "RUN_CORRUPT":
        return _problem(
            409,
            exc.code,
            "Historical run doğrulanamadı",
            "Historical run bütünlük kontrolünden geçemedi.",
        )
    return _problem(
        503,
        "RUN_STORE_UNAVAILABLE",
        "Historical run store kullanılamıyor",
        "Yerel tarihsel koşu kayıtları şu anda okunamadı.",
    )


def _contains_forbidden_run_key(value: object) -> bool:
    forbidden = {"api_key", "credential", "password", "path", "private_key", "secret", "token", "url"}
    if isinstance(value, dict):
        return any(str(key).lower() in forbidden or _contains_forbidden_run_key(nested) for key, nested in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_run_key(nested) for nested in value)
    return False


@app.get("/api/historical-runs", response_model=HistoricalRunListResponse)
def list_historical_runs(
    response: Response,
    limit: int = Query(DEFAULT_RUN_LIST_LIMIT, ge=1, le=MAX_RUN_LIST_LIMIT),
):
    response.headers["Cache-Control"] = "no-store"
    if not HISTORICAL_RUNS_PATH.exists():
        return HistoricalRunListResponse(runs=[], count=0)
    try:
        with HistoricalRunStore(HISTORICAL_RUNS_PATH) as store:
            items = store.list_runs(limit)
    except HistoricalRunStoreError as exc:
        return _historical_run_store_read_problem(exc)
    return HistoricalRunListResponse(
        runs=[
            HistoricalRunListItemResponse(
                run_id=item.run_id,
                created_at=item.created_at,
                execution_status=item.execution_status,
                record_health=item.record_health,
                symbol=item.symbol,
                interval=item.interval,
                period_start=date.fromisoformat(item.period_start),
                period_end=date.fromisoformat(item.period_end),
                processed_bar_count=item.processed_bar_count,
                position_status=item.position_status,
            )
            for item in items
        ],
        count=len(items),
    )


@app.get("/api/historical-runs/{run_id}", response_model=HistoricalRunDetailResponse)
def get_historical_run(run_id: str, response: Response):
    response.headers["Cache-Control"] = "no-store"
    try:
        parsed_run_id = UUID(run_id)
    except (AttributeError, ValueError):
        return _problem(
            422,
            "RUN_ID_INVALID",
            "Historical run kimliği geçersiz",
            "Run kimliği desteklenen UUID biçiminde değil.",
        )
    if str(parsed_run_id) != run_id:
        return _problem(
            422,
            "RUN_ID_INVALID",
            "Historical run kimliği geçersiz",
            "Run kimliği canonical UUID biçiminde değil.",
        )
    if not HISTORICAL_RUNS_PATH.exists():
        return _problem(
            404,
            "RUN_NOT_FOUND",
            "Historical run bulunamadı",
            "İstenen historical run local store içinde yok.",
        )
    try:
        with HistoricalRunStore(HISTORICAL_RUNS_PATH) as store:
            detail = store.get(run_id)
    except HistoricalRunStoreError as exc:
        return _historical_run_store_read_problem(exc)
    if any(
        _contains_forbidden_run_key(value)
        for value in (
            detail.dataset,
            detail.input_snapshot,
            detail.config,
            detail.instrument_risk,
            detail.execution,
            detail.result_snapshot,
            detail.evaluation_lineage,
        )
    ):
        return _problem(
            409,
            "RUN_DETAIL_UNSAFE",
            "Historical run güvenli değil",
            "Historical run detail allowlist dışı alan içeriyor.",
        )
    result = HistoricalRunDetailResponse(
        run_id=detail.run_id,
        created_at=detail.created_at,
        storage_state=detail.storage_state,
        execution_status=detail.execution_status,
        dataset=detail.dataset,
        input_snapshot=detail.input_snapshot,
        config=detail.config,
        instrument_risk=detail.instrument_risk,
        execution=detail.execution,
        result_snapshot=detail.result_snapshot,
        result_sha256=detail.result_sha256,
        record_sha256=detail.record_sha256,
        evaluation_lineage=detail.evaluation_lineage,
    )
    serialized = json.dumps(result.model_dump(mode="json"), ensure_ascii=True, separators=(",", ":"))
    if len(serialized.encode("utf-8")) > MAX_HISTORICAL_RUN_DETAIL_RESPONSE_BYTES:
        return _problem(
            422,
            "RUN_DETAIL_RESPONSE_TOO_LARGE",
            "Historical run detail çok büyük",
            "Historical run detail izin verilen response byte sınırını aşıyor.",
        )
    return result


@app.post("/api/historical-runs/{run_id}/reproduce", response_model=HistoricalRunReproduceResponse)
def reproduce_historical_run(run_id: str, response: Response):
    """Re-run a stored historical simulation from its exact recorded config/dataset and compare hashes."""

    response.headers["Cache-Control"] = "no-store"
    try:
        parsed_run_id = UUID(run_id)
    except (AttributeError, ValueError):
        return _problem(
            422,
            "RUN_ID_INVALID",
            "Historical run kimliği geçersiz",
            "Run kimliği desteklenen UUID biçiminde değil.",
        )
    if str(parsed_run_id) != run_id:
        return _problem(
            422,
            "RUN_ID_INVALID",
            "Historical run kimliği geçersiz",
            "Run kimliği canonical UUID biçiminde değil.",
        )
    if not HISTORICAL_RUNS_PATH.exists():
        return _problem(
            404,
            "RUN_NOT_FOUND",
            "Historical run bulunamadı",
            "İstenen historical run local store içinde yok.",
        )
    try:
        with HistoricalRunStore(HISTORICAL_RUNS_PATH) as store:
            stored = store.get(run_id)
    except HistoricalRunStoreError as exc:
        return _historical_run_store_read_problem(exc)
    if stored.execution.get("model_id") != "historical_ohlcv_v1":
        return _problem(
            422,
            "REPRODUCE_MODEL_UNSUPPORTED",
            "Reproduce desteklenmiyor",
            "Bu run kayıtlı model için reproduce henüz desteklenmiyor.",
        )
    if not HISTORICAL_EXECUTION_LOCK.acquire(blocking=False):
        return _problem(
            409,
            "EXECUTION_BUSY",
            "Simülasyon meşgul",
            "Başka bir tarihsel simülasyon çalışıyor.",
        )
    try:
        preflight = _dataset_preflight(stored.dataset["dataset_id"])
        if isinstance(preflight, JSONResponse):
            return preflight
        loaded, _preflight = preflight
        if loaded.metadata.artifact_sha256 != stored.dataset["artifact_sha256"]:
            return _problem(
                409,
                "REPRODUCE_ARTIFACT_CHANGED",
                "Dataset değişti",
                "Kayıtlı run'ın dataset artifact'ı yerel cache'teki güncel artifact ile eşleşmiyor; reproduce güvenli değil.",
            )
        raw_config = stored.config["snapshot"]
        config_hash = stored.config["config_hash"]
        try:
            config = Config.parse(raw_config)
            result = simulate_historical_ohlcv(loaded, config, config_hash=config_hash)
        except HistoricalSimulationError as exc:
            status = 503 if exc.code == "EXECUTION_BUDGET_EXCEEDED" else 422
            return _problem(status, exc.code, "Reproduce simülasyonu çalıştırılamadı", str(exc))
        try:
            new_capture = build_historical_run_capture(
                loaded,
                raw_config,
                result,
                config_hash=config_hash,
                profile_id=stored.execution.get("profile_id", "paper"),
            )
        except HistoricalRunContractError:
            return _problem(
                422,
                "RUN_CAPTURE_INVALID",
                "Reproduce sonucu doğrulanamadı",
                "Yeniden üretilen sonuç güvenli tarihsel koşu snapshot sözleşmesine uymuyor.",
            )
        result_sha256_match = new_capture.result_sha256 == stored.result_sha256
        canonical_input_sha256_match = new_capture.canonical_input_sha256 == stored.dataset["canonical_input_sha256"]
        execution_identity_sha256_match = (
            new_capture.execution.identity_sha256 == stored.execution["execution_identity_sha256"]
        )
        return HistoricalRunReproduceResponse(
            run_id=run_id,
            reproduced=result_sha256_match and canonical_input_sha256_match and execution_identity_sha256_match,
            result_sha256_match=result_sha256_match,
            canonical_input_sha256_match=canonical_input_sha256_match,
            execution_identity_sha256_match=execution_identity_sha256_match,
            stored_result_sha256=stored.result_sha256,
            new_result_sha256=new_capture.result_sha256,
        )
    finally:
        HISTORICAL_EXECUTION_LOCK.release()


@app.post(
    "/api/dataset-downloads",
    response_model=DatasetDownloadStartResponse,
    status_code=202,
)
def start_dataset_download(payload: DatasetSelectionRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    try:
        plan = DATASET_CATALOG.plan_for(payload.dataset_id)
    except CatalogError:
        return _problem(
            404,
            "DATASET_NOT_FOUND",
            "Dataset bulunamadı",
            "İstenen dataset tanımı katalogda yok.",
        )
    try:
        job_id = DOWNLOAD_JOBS.start(payload.dataset_id, plan, DATASET_CACHE_DIR)
    except DownloadJobConflict:
        return _problem(
            409,
            "DATASET_DOWNLOAD_ACTIVE",
            "Dataset download zaten çalışıyor",
            "Aynı dataset için tamamlanmamış bir download job var.",
        )
    return DatasetDownloadStartResponse(job=_download_job_response(DOWNLOAD_JOBS.get(job_id)))


@app.get("/api/dataset-downloads/{job_id}", response_model=DatasetDownloadJobResponse)
def get_dataset_download(job_id: str, response: Response):
    response.headers["Cache-Control"] = "no-store"
    try:
        snapshot = DOWNLOAD_JOBS.get(job_id)
    except DownloadJobNotFound:
        return _problem(
            404,
            "DOWNLOAD_JOB_NOT_FOUND",
            "Download job bulunamadı",
            "İstenen local job bellekte yok.",
        )
    return _download_job_response(snapshot)


@app.post("/api/dataset-downloads/{job_id}/cancel", response_model=DatasetDownloadJobResponse)
def cancel_dataset_download(job_id: str, response: Response):
    response.headers["Cache-Control"] = "no-store"
    try:
        snapshot = DOWNLOAD_JOBS.cancel(job_id)
    except DownloadJobNotFound:
        return _problem(
            404,
            "DOWNLOAD_JOB_NOT_FOUND",
            "Download job bulunamadı",
            "İstenen local job bellekte yok.",
        )
    return _download_job_response(snapshot)


@app.post("/api/preview")
async def create_preview(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_preview_payload(payload)
    revision = payload.get("revision", 0) if isinstance(payload, dict) else 0
    if type(revision) is not int:
        revision = 0
    if fields:
        return JSONResponse(
            status_code=422,
            content=_error("İstek doğrulanamadı.", fields=fields, revision=revision),
        )
    try:
        return {"data": _calculate_preview(validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(
            status_code=422,
            content=_error(str(exc), fields={"config": str(exc)}, revision=revision),
        )


@app.post("/api/data-quality")
async def create_data_quality(request: Request):
    filename = request.headers.get("x-filename", "")
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except ValueError:
            return JSONResponse(status_code=400, content=_error("Content-Length geçersiz."))
        if declared_size < 0:
            return JSONResponse(status_code=400, content=_error("Content-Length geçersiz."))
        if declared_size > MAX_INPUT_BYTES:
            return JSONResponse(
                status_code=422,
                content=_error(f"Dosya {MAX_INPUT_BYTES} byte sınırını aşıyor.", fields={"file": "Dosya çok büyük."}),
            )
    try:
        content = await request.body()
        report = quality_from_bytes(filename, content)
    except DataQualityError as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"file": str(exc)}))
    return _quality_response(report)
