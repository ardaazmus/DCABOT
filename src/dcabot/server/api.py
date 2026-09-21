"""Small local-only HTTP API that delegates preview calculations to the core."""

import json
import os
import re
import time
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
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
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
from dcabot.application.paper_feed_binding import (
    apply_observations,
    new_market_state,
)
from dcabot.application.paper_orders import (
    cancel_paper_order,
    fill_paper_order,
    place_paper_order,
)
from dcabot.application.paper_trading_gate import PaperSession, activate_paper_session
from dcabot.application.futures_grid_levels import (
    FuturesGridProfile,
    project_futures_grid_levels,
)
from dcabot.application.linear_futures_math import LinearFuturesPosition, project_funding
from dcabot.application.trailing_ratchet import (
    TrailingLongPercentageState,
    TrailingLongState,
    TrailingShortPercentageState,
    TrailingShortState,
    arm_long_percentage_trailing,
    arm_long_trailing,
    arm_short_percentage_trailing,
    arm_short_trailing,
    observe_long_percentage_trailing,
    observe_long_trailing,
    observe_short_percentage_trailing,
    observe_short_trailing,
)
from dcabot.application.trailing_exit_binding import bind_trailing_exit_candidate
from dcabot.application.futures_dca_plan import project_futures_dca_plan
from dcabot.application.futures_dca_fill_projection import (
    FuturesDcaFill,
    project_futures_dca_fills,
)
from dcabot.application.futures_dca_breakeven_contract import (
    FuturesDcaFeeAwareProfile,
    assess_futures_dca_breakeven,
)
from dcabot.application.rebalance_execution import (
    bind_execution_orders,
    disclose_execution,
)
from dcabot.application.rebalance_projection import build_rebalance_projection
from dcabot.application.rebalance_triggers import (
    evaluate_threshold_trigger,
    evaluate_time_trigger,
)
from dcabot.application.rebalance_valuation import RebalancePlan, build_rebalance_plan, value_holdings
from dcabot.application.hedge_two_leg_contract import (
    HedgePositionIdentity,
    new_hedge_position_identity,
)
from dcabot.application.two_leg_fill_projection import (
    LegFill,
    TwoLegFillProjection,
)
from dcabot.persistence.two_leg_journal import TwoLegJournal
from dcabot.application.bot_registry import BotProfile, BotRegistry, new_bot_profile
from dcabot.application.dashboard import build_dashboard
from dcabot.application.settlement_profile import (
    SUPPORTED_SETTLEMENT_ASSETS,
    require_settlement_asset,
)
from dcabot.application.recurring_schedule import project_recurring_schedule
from dcabot.application.draft_level import validate_draft_level
from dcabot.application.event_log import EventLog
from dcabot.application.risk_explanation import explain_risk
from dcabot.application.single_worker import SingleWorkerGuard
from dcabot.application.run_export import export_run_csv, export_run_json
from dcabot.application.store_backup import (
    StoreBackupError,
    backup_sqlite_file,
    list_backup_manifests,
    verify_backup,
)
from dcabot.application.config_revision import new_config_revision
from dcabot.application.deal_lifecycle import DealLifecycle, new_deal_lifecycle
from dcabot.application.lifecycle_event_transition import apply_lifecycle_event
from dcabot.application.lifecycle_event_contract import LifecycleEvent, new_lifecycle_event
from dcabot.persistence.lifecycle_store import LifecycleStore, LifecycleStoreError
from dcabot.application.signal_candidate_binding import bind_signal_candidate
from dcabot.application.signal_event_contract import new_signal_event
from dcabot.application.signal_intake import hash_signal_payload
from dcabot.application.signal_readiness import assess_signal_readiness
from dcabot.application.strategy_template import new_strategy_template
from dcabot.application.template_materialization import (
    TemplateFileStore,
    diff_templates,
    materialize_binding,
)
from dcabot.application.template_profile_binding import bind_template_to_profile
from dcabot.data_adapters.binance_public import BinanceTimeUnit
from dcabot.data_adapters.binance_public_transport import (
    BinancePublicTransportError,
    fetch_binance_public_trades,
)
from dcabot.data_adapters.public_feed import ObservationOutcome, PublicObservation
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
REBALANCE_VALUATION_FIELDS = {"valuation_asset", "holdings", "prices"}
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
    "/api/rebalance/valuation": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/paper/sessions": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/paper/sessions/{session_id}/orders": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/paper/sessions/{session_id}/fills": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/paper/sessions/{session_id}/market-refresh": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/templates/import": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/templates/{template_id}/bind": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/templates/diff": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/rebalance/plan": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/rebalance/disclose": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/signals/hash": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/signals/assess": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/signals/candidates": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/futures/grid/levels": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/futures/position/pnl": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/futures/trailing/arm": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/futures/trailing/observe": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/futures/funding": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/two-leg/sessions": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/two-leg/sessions/{session_id}/fills": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/two-leg/sessions/{session_id}/recovery": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/two-leg/sessions/{session_id}/timeout": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/two-leg/sessions/{session_id}/replay": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/bots": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/bots/{bot_id}/lists": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/bots/{bot_id}/sessions": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/bots/{bot_id}/check": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/deals": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/deals/bulk": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/deals/{deal_id}/events": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/deals/{deal_id}/replay": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/exits/trailing": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/exits/trailing/percent-arm": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/exits/trailing/percent-observe": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/exits/breakeven": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/admin/backup": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/admin/backup/verify": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/recurring/schedule": SMALL_JSON_BODY_LIMIT_BYTES,
    "/api/risk/explain": SMALL_JSON_BODY_LIMIT_BYTES,
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


ROUTE_BODY_LIMITS = {
    **SMALL_JSON_BODY_LIMITS,
    # Upload route: own 20 MB budget enforced before the handler reads;
    # a lying or missing Content-Length must not cause an unbounded read.
    "/api/data-quality": MAX_INPUT_BYTES,
}


class BoundedAPIRoute(APIRoute):
    """Attach native Starlette body limits to the explicitly bounded JSON routes."""

    def __init__(self, path: str, endpoint: Any, **kwargs: Any) -> None:
        super().__init__(path, endpoint, **kwargs)
        max_body_size = ROUTE_BODY_LIMITS.get(path)
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


class DraftLevelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)

    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    draft_price: str


class DraftLevelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    verdict: Literal["ACCEPTED", "REJECTED"]
    draft_price: str
    reason: str
    dataset_id: str
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


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


class HistoricalRunExportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    format: Literal["json", "csv"]
    filename: str
    content: str
    note: str


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


def _validate_rebalance_valuation_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    if not isinstance(payload, dict):
        return None, {"body": "JSON gövdesi nesne olmalıdır."}
    unknown = set(payload) - REBALANCE_VALUATION_FIELDS
    missing = REBALANCE_VALUATION_FIELDS - set(payload)
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
    if "valuation_asset" in payload and not isinstance(payload["valuation_asset"], str):
        fields["valuation_asset"] = "Valuation asset string olmalıdır."
    for name, lo, hi in (("holdings", 1, 64), ("prices", 0, 64)):
        if name not in payload:
            continue
        rows = payload[name]
        if not isinstance(rows, list) or not lo <= len(rows) <= hi:
            fields[name] = f"{name} {lo} ile {hi} arasında satır listesi olmalıdır."
            continue
        for row in rows:
            if not isinstance(row, list) or len(row) != 2 or not all(isinstance(v, str) for v in row):
                fields[name] = f"{name} satırları iki string listesi olmalıdır."
                break
    if fields:
        return None, fields
    return payload, {}


def _calculate_rebalance_valuation(payload: dict[str, object]) -> dict[str, object]:
    result = value_holdings(
        valuation_asset=payload["valuation_asset"],  # type: ignore[arg-type]
        holdings=tuple((row[0], row[1]) for row in payload["holdings"]),  # type: ignore[union-attr]
        prices=tuple((row[0], row[1]) for row in payload["prices"]),  # type: ignore[union-attr]
    )
    return {
        "valuation_asset": result.valuation_asset,
        "total_equity": result.total_equity,
        "positions": [
            {"asset": p.asset, "qty": p.qty, "price": p.price, "value": p.value}
            for p in result.positions
        ],
    }


PAPER_ACTIVATION_FIELDS = {"confirmed", "symbols", "max_staleness_us", "starting_cash"}
PAPER_ORDER_FIELDS = {"symbol", "side", "order_type", "qty", "limit_price", "client_order_id"}
PAPER_FILL_FIELDS = {"client_order_id", "event_id", "fill_qty"}
PAPER_FILL_REQUIRED = {"client_order_id", "event_id"}
MAX_PAPER_SESSIONS = 16
MAX_CACHED_PRINTS_PER_SYMBOL = 50
PAPER_REFRESH_LIMIT = 5


def _new_paper_store() -> dict[str, object]:
    return {"sessions": {}, "binding": new_market_state(), "prints": {}}


PAPER_STORE = _new_paper_store()
PAPER_LOCK = Lock()
TEMPLATE_IMPORT_FIELDS = {"template_id", "schema_version", "payload", "declared_capabilities"}
TEMPLATE_BIND_FIELDS = {"profile_id", "allowed_capabilities", "approval"}
TEMPLATE_DIFF_FIELDS = {"first_id", "second_id"}
TEMPLATE_STORE = TemplateFileStore(ROOT / "data" / "templates")
TEMPLATE_LOCK = Lock()
TWO_LEG_LOCK = Lock()
BOT_REGISTRY = BotRegistry()
BOT_LOCK = Lock()
DEALS_DIR = ROOT / "data" / "deals"
BACKUPS_DIR = ROOT / "data" / "backups"
BACKUP_LOCK = Lock()
EVENT_LOG = EventLog()
EVENT_LOCK = Lock()
DEAL_LOCK = Lock()
_DEAL_EVENTS = frozenset({"START", "PAUSE", "RESUME", "COMPLETE", "ABORT", "FAIL"})
_TWO_LEG_SESSION_RE = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)
_TWO_LEG_JOURNAL: TwoLegJournal | None = None


def _get_two_leg_journal() -> TwoLegJournal:
    global _TWO_LEG_JOURNAL
    if _TWO_LEG_JOURNAL is None:
        _TWO_LEG_JOURNAL = TwoLegJournal(ROOT / "data" / "two_leg_journal.db")
    return _TWO_LEG_JOURNAL


def _validate_paper_activation_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    if not isinstance(payload, dict):
        return None, {"body": "JSON gövdesi nesne olmalıdır."}
    unknown = set(payload) - PAPER_ACTIVATION_FIELDS
    missing = PAPER_ACTIVATION_FIELDS - set(payload)
    fields: dict[str, str] = {}
    if unknown:
        fields["body"] = "Bilinmeyen alanlar: " + ", ".join(sorted(unknown))
    if missing:
        fields["body"] = (fields.get("body", "") + (" " if fields.get("body") else "")
                           + "Eksik alanlar: " + ", ".join(sorted(missing)))
    if "confirmed" in payload and (type(payload["confirmed"]) is not bool or not payload["confirmed"]):
        fields["confirmed"] = "Paper session açık onay gerektirir."
    if "symbols" in payload and (
        not isinstance(payload["symbols"], list)
        or not 1 <= len(payload["symbols"]) <= 16
        or not all(isinstance(s, str) for s in payload["symbols"])
    ):
        fields["symbols"] = "Symbols 1 ile 16 arasında string listesi olmalıdır."
    if "max_staleness_us" in payload and (
        type(payload["max_staleness_us"]) is not int or payload["max_staleness_us"] < 0
    ):
        fields["max_staleness_us"] = "Staleness negatif olmayan tam sayı olmalıdır."
    if "starting_cash" in payload and not isinstance(payload["starting_cash"], str):
        fields["starting_cash"] = "Başlangıç nakdi string olmalıdır."
    if fields:
        return None, fields
    return payload, {}


def _validate_paper_order_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    if not isinstance(payload, dict):
        return None, {"body": "JSON gövdesi nesne olmalıdır."}
    unknown = set(payload) - PAPER_ORDER_FIELDS
    missing = PAPER_ORDER_FIELDS - set(payload)
    fields: dict[str, str] = {}
    if unknown:
        fields["body"] = "Bilinmeyen alanlar: " + ", ".join(sorted(unknown))
    if missing:
        fields["body"] = (fields.get("body", "") + (" " if fields.get("body") else "")
                           + "Eksik alanlar: " + ", ".join(sorted(missing)))
    for name in ("symbol", "side", "order_type", "qty", "client_order_id"):
        if name in payload and not isinstance(payload[name], str):
            fields[name] = f"{name} string olmalıdır."
    if "limit_price" in payload and payload["limit_price"] is not None and not isinstance(payload["limit_price"], str):
        fields["limit_price"] = "limit_price string veya null olmalıdır."
    if fields:
        return None, fields
    return payload, {}


def _validate_paper_fill_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    if not isinstance(payload, dict):
        return None, {"body": "JSON gövdesi nesne olmalıdır."}
    unknown = set(payload) - PAPER_FILL_FIELDS
    missing = PAPER_FILL_REQUIRED - set(payload)
    fields: dict[str, str] = {}
    if unknown:
        fields["body"] = "Bilinmeyen alanlar: " + ", ".join(sorted(unknown))
    if missing:
        fields["body"] = (fields.get("body", "") + (" " if fields.get("body") else "")
                           + "Eksik alanlar: " + ", ".join(sorted(missing)))
    for name in ("client_order_id", "event_id", "fill_qty"):
        if name in payload and not isinstance(payload[name], str):
            fields[name] = f"{name} string olmalıdır."
    if fields:
        return None, fields
    return payload, {}


def _paper_session_or_raise(store: dict[str, object], session_id: str) -> PaperSession:
    sessions = store["sessions"]
    assert isinstance(sessions, dict)
    session = sessions.get(session_id)
    if not isinstance(session, PaperSession):
        raise ValueError("PAPER_SESSION_UNKNOWN: Paper session bulunamadı.")
    return session


def _paper_snapshot(session: PaperSession, store: dict[str, object]) -> dict[str, object]:
    binding = store["binding"]
    assert hasattr(binding, "marks")
    return {
        "session_id": session.session_id,
        "status": session.status,
        "cash": session.cash,
        "positions": [{"symbol": p.symbol, "qty": p.qty} for p in session.positions],
        "orders": [
            {
                "client_order_id": o.client_order_id, "symbol": o.symbol,
                "side": o.side, "order_type": o.order_type, "qty": o.qty,
                "limit_price": o.limit_price, "filled_qty": o.filled_qty,
                "status": o.status,
            }
            for o in session.orders
        ],
        "fills": [
            {
                "fill_id": f.fill_id, "client_order_id": f.client_order_id,
                "event_id": f.event_id, "symbol": f.symbol, "side": f.side,
                "price": f.price, "qty": f.qty, "notional": f.notional,
            }
            for f in session.fills
        ],
        "marks": [
            {"symbol": m.symbol, "price": m.price, "event_id": m.event_id}
            for m in binding.marks
        ],
    }


def _paper_activate(store: dict[str, object], validated: dict[str, object], now_us: int) -> dict[str, object]:
    sessions = store["sessions"]
    assert isinstance(sessions, dict)
    if len(sessions) >= MAX_PAPER_SESSIONS:
        raise ValueError("PAPER_SESSION_CAPACITY: Paper session sınırı dolu.")
    session = activate_paper_session(
        confirmed=True,
        session_time_us=now_us,
        symbols=tuple(validated["symbols"]),  # type: ignore[arg-type]
        max_staleness_us=validated["max_staleness_us"],  # type: ignore[arg-type]
        starting_cash=validated["starting_cash"],  # type: ignore[arg-type]
        credential_present=False,
    )
    sessions[session.session_id] = session
    return _paper_snapshot(session, store)


def _paper_place(store: dict[str, object], session_id: str, validated: dict[str, object], now_us: int) -> dict[str, object]:
    session = _paper_session_or_raise(store, session_id)
    updated, order, outcome = place_paper_order(
        session=session,
        symbol=validated["symbol"],  # type: ignore[arg-type]
        side=validated["side"],  # type: ignore[arg-type]
        order_type=validated["order_type"],  # type: ignore[arg-type]
        qty=validated["qty"],  # type: ignore[arg-type]
        limit_price=validated["limit_price"],  # type: ignore[arg-type]
        client_order_id=validated["client_order_id"],  # type: ignore[arg-type]
        order_time_us=now_us,
    )
    sessions = store["sessions"]
    assert isinstance(sessions, dict)
    sessions[session_id] = updated
    return {"outcome": outcome, "snapshot": _paper_snapshot(updated, store)}


def _paper_fill(store: dict[str, object], session_id: str, validated: dict[str, object], now_us: int) -> dict[str, object]:
    session = _paper_session_or_raise(store, session_id)
    prints = store["prints"]
    assert isinstance(prints, dict)
    observation = None
    for cached in prints.values():
        for item in cached:
            if item.event_id == validated["event_id"]:
                observation = item
                break
        if observation is not None:
            break
    if observation is None:
        raise ValueError("PAPER_EVENT_UNKNOWN: Event server önbelleğinde yok.")
    fill_qty = validated.get("fill_qty")
    if fill_qty is None:
        target = next(
            (o for o in session.orders if o.client_order_id == validated["client_order_id"]),
            None,
        )
        if target is None:
            raise ValueError("PAPER_ORDER_UNKNOWN: Emir bu sessionda yok.")
        fill_qty = exact_text(number(target.qty) - number(target.filled_qty))
    updated, fill, outcome = fill_paper_order(
        session=session,
        client_order_id=validated["client_order_id"],  # type: ignore[arg-type]
        observation=observation,
        fill_qty=fill_qty,  # type: ignore[arg-type]
        fill_time_us=now_us,
    )
    sessions = store["sessions"]
    assert isinstance(sessions, dict)
    sessions[session_id] = updated
    return {
        "outcome": outcome,
        "fill": {"fill_id": fill.fill_id, "price": fill.price, "notional": fill.notional},
        "snapshot": _paper_snapshot(updated, store),
    }


def _paper_refresh(store: dict[str, object], session_id: str, *, fetch, now_us: int, time_unit) -> dict[str, object]:
    session = _paper_session_or_raise(store, session_id)
    prints = store["prints"]
    assert isinstance(prints, dict)
    fresh: list[PublicObservation] = []
    for symbol in session.symbols:
        for item in fetch(symbol):
            if not isinstance(item, PublicObservation) or item.symbol != symbol:
                raise ValueError("PAPER_REFRESH_OBSERVATION_INVALID: Piyasa gözlemi geçersiz.")
            fresh.append(item)
    binding, _ = apply_observations(
        store["binding"],  # type: ignore[arg-type]
        tuple(fresh),
        now_times_us=tuple(now_us for _ in fresh),
        max_staleness_us=session.max_staleness_us,
    )
    store["binding"] = binding
    for item in fresh:
        cached = list(prints.get(item.symbol, ()))
        if all(p.event_id != item.event_id for p in cached):
            cached.append(item)
        prints[item.symbol] = tuple(cached[-MAX_CACHED_PRINTS_PER_SYMBOL:])
    return {
        "prints": [
            {
                "event_id": item.event_id, "symbol": item.symbol,
                "price": item.price, "qty": item.quantity,
                "event_time_us": item.event_time_us,
            }
            for item in fresh
        ],
        "snapshot": _paper_snapshot(session, store),
    }


def _template_field_errors(payload: object, allowed: set[str]) -> tuple[dict[str, object] | None, dict[str, str]]:
    if not isinstance(payload, dict):
        return None, {"body": "JSON gövdesi nesne olmalıdır."}
    unknown = set(payload) - allowed
    missing = allowed - set(payload)
    fields: dict[str, str] = {}
    if unknown:
        fields["body"] = "Bilinmeyen alanlar: " + ", ".join(sorted(unknown))
    if missing:
        fields["body"] = (fields.get("body", "") + (" " if fields.get("body") else "")
                           + "Eksik alanlar: " + ", ".join(sorted(missing)))
    return payload, fields


def _validate_template_import_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    payload, fields = _template_field_errors(payload, TEMPLATE_IMPORT_FIELDS)
    if payload is None or fields:
        return None, fields
    assert isinstance(payload, dict)
    if not isinstance(payload["template_id"], str):
        fields["template_id"] = "template_id string olmalıdır."
    if payload["schema_version"] != "strategy-template-v1":
        fields["schema_version"] = "Yalnız strategy-template-v1 kabul edilir."
    if not isinstance(payload["payload"], dict):
        fields["payload"] = "payload JSON nesnesi olmalıdır."
    if (
        not isinstance(payload["declared_capabilities"], list)
        or not all(isinstance(c, str) for c in payload["declared_capabilities"])
    ):
        fields["declared_capabilities"] = "declared_capabilities string listesi olmalıdır."
    if fields:
        return None, fields
    return payload, {}


def _validate_template_bind_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    payload, fields = _template_field_errors(payload, TEMPLATE_BIND_FIELDS)
    if payload is None or fields:
        return None, fields
    assert isinstance(payload, dict)
    if not isinstance(payload["profile_id"], str):
        fields["profile_id"] = "profile_id string olmalıdır."
    if (
        not isinstance(payload["allowed_capabilities"], list)
        or not all(isinstance(c, str) for c in payload["allowed_capabilities"])
    ):
        fields["allowed_capabilities"] = "allowed_capabilities string listesi olmalıdır."
    if not isinstance(payload["approval"], str):
        fields["approval"] = "approval string olmalıdır."
    if fields:
        return None, fields
    return payload, {}


def _validate_template_diff_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    payload, fields = _template_field_errors(payload, TEMPLATE_DIFF_FIELDS)
    if payload is None or fields:
        return None, fields
    assert isinstance(payload, dict)
    for name in ("first_id", "second_id"):
        if not isinstance(payload[name], str):
            fields[name] = f"{name} string olmalıdır."
    if fields:
        return None, fields
    return payload, {}


def _template_import(store: TemplateFileStore, validated: dict[str, object]) -> dict[str, object]:
    template = new_strategy_template(
        template_id=validated["template_id"],  # type: ignore[arg-type]
        schema_version=validated["schema_version"],  # type: ignore[arg-type]
        payload=validated["payload"],  # type: ignore[arg-type]
        declared_capabilities=tuple(validated["declared_capabilities"]),  # type: ignore[arg-type]
    )
    store.save(template)
    return {
        "template_id": template.template_id,
        "payload_sha256": template.payload_sha256,
        "declared_capabilities": list(template.declared_capabilities),
    }


def _template_bind(store: TemplateFileStore, template_id: str, validated: dict[str, object], now_us: int) -> dict[str, object]:
    template = store.load(template_id)
    binding = bind_template_to_profile(
        template=template,
        profile_id=validated["profile_id"],  # type: ignore[arg-type]
        allowed_capabilities=tuple(validated["allowed_capabilities"]),  # type: ignore[arg-type]
        approval=validated["approval"],  # type: ignore[arg-type]
        binding_time_us=now_us,
    )
    materialized = materialize_binding(binding, ROOT)
    return {
        "binding": {
            "binding_id": binding.binding_id,
            "status": binding.status,
            "template_id": binding.template_id,
            "profile_id": binding.profile_id,
            "params": [[k, v] for k, v in binding.params],
        },
        "materialized": {
            "config": materialized.config,
            "config_hash": materialized.config_hash,
        },
    }


def _template_diff(store: TemplateFileStore, validated: dict[str, object]) -> list[dict[str, object]]:
    first = store.load(validated["first_id"])  # type: ignore[arg-type]
    second = store.load(validated["second_id"])  # type: ignore[arg-type]
    return [
        {"key": key, "before": before, "after": after}
        for key, before, after in diff_templates(first, second)
    ]


def _template_meta(store: TemplateFileStore, template_id: str) -> dict[str, object]:
    template = store.load(template_id)
    return {
        "template_id": template.template_id,
        "payload_sha256": template.payload_sha256,
        "declared_capabilities": list(template.declared_capabilities),
    }


REBALANCE_PLAN_FIELDS = {"trigger", "projection"}
REBALANCE_DISCLOSE_FIELDS = {"plan", "projection", "prices", "fee_rate", "qty_step", "min_notional", "cash_reserve"}
SIGNAL_HASH_FIELDS = {"payload"}
SIGNAL_ASSESS_FIELDS = {"signal", "closed_bar_time_us", "warmup_bars_observed", "required_warmup_bars", "max_staleness_us"}
SIGNAL_CANDIDATE_FIELDS = SIGNAL_ASSESS_FIELDS | {"action", "symbol", "action_map", "qty", "ttl_us"}


def _allocation_rows(value: object) -> list[list[str]] | None:
    if not isinstance(value, list):
        return None
    rows: list[list[str]] = []
    for row in value:
        if not isinstance(row, list) or len(row) != 3 or not all(isinstance(v, str) for v in row):
            return None
        rows.append([row[0], row[1], row[2]])
    return rows


def _pair_rows(value: object) -> list[list[str]] | None:
    if not isinstance(value, list):
        return None
    rows: list[list[str]] = []
    for row in value:
        if not isinstance(row, list) or len(row) != 2 or not all(isinstance(v, str) for v in row):
            return None
        rows.append([row[0], row[1]])
    return rows


def _validate_rebalance_plan_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, REBALANCE_PLAN_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    trigger = body["trigger"]
    if not isinstance(trigger, dict) or trigger.get("policy") not in ("threshold", "time"):
        fields["trigger"] = "trigger policy threshold veya time olmalıdır."
    elif trigger["policy"] == "threshold":
        for name in ("current_weight", "target_weight", "threshold"):
            if not isinstance(trigger.get(name), str):
                fields["trigger"] = f"trigger.{name} string olmalıdır."
    else:
        for name in ("last_rebalance_us", "now_us", "interval_us"):
            if type(trigger.get(name)) is not int:
                fields["trigger"] = f"trigger.{name} integer olmalıdır."
    projection = body["projection"]
    if (
        not isinstance(projection, dict)
        or not isinstance(projection.get("valuation_asset"), str)
        or not isinstance(projection.get("total_equity"), str)
        or _allocation_rows(projection.get("allocations")) is None
    ):
        fields["projection"] = "projection valuation_asset/total_equity/allocations gerektirir."
    if fields:
        return None, fields
    return body, {}


def _rebalance_plan(validated: dict[str, object], now_us: int) -> dict[str, object]:
    trigger = validated["trigger"]
    assert isinstance(trigger, dict)
    if trigger["policy"] == "threshold":
        decision = evaluate_threshold_trigger(
            current_weight=trigger["current_weight"],  # type: ignore[arg-type]
            target_weight=trigger["target_weight"],  # type: ignore[arg-type]
            threshold=trigger["threshold"],  # type: ignore[arg-type]
        )
    else:
        decision = evaluate_time_trigger(
            last_rebalance_time_us=trigger["last_rebalance_us"],  # type: ignore[arg-type]
            observation_time_us=trigger["now_us"],  # type: ignore[arg-type]
            interval_us=trigger["interval_us"],  # type: ignore[arg-type]
        )
    projection_body = validated["projection"]
    assert isinstance(projection_body, dict)
    projection = build_rebalance_projection(
        valuation_asset=projection_body["valuation_asset"],  # type: ignore[arg-type]
        total_equity=projection_body["total_equity"],  # type: ignore[arg-type]
        allocations=tuple((r[0], r[1], r[2]) for r in projection_body["allocations"]),  # type: ignore[union-attr]
    )
    plan = build_rebalance_plan(trigger=decision, projection=projection, plan_time_us=now_us)
    return {
        "plan_id": plan.plan_id,
        "status": plan.status,
        "plan_time_us": plan.plan_time_us,
        "valuation_asset": plan.valuation_asset,
        "total_equity": plan.total_equity,
        "gross_buy": plan.gross_buy,
        "gross_sell": plan.gross_sell,
        "trigger_policy": plan.trigger_policy,
    }


def _validate_rebalance_disclose_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, REBALANCE_DISCLOSE_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    plan = body["plan"]
    if (
        not isinstance(plan, dict)
        or not isinstance(plan.get("plan_id"), str)
        or plan.get("status") != "DRAFT"
        or type(plan.get("plan_time_us")) is not int
        or not isinstance(plan.get("valuation_asset"), str)
        or not isinstance(plan.get("total_equity"), str)
        or not isinstance(plan.get("gross_buy"), str)
        or not isinstance(plan.get("gross_sell"), str)
        or not isinstance(plan.get("trigger_policy"), str)
    ):
        fields["plan"] = "plan kaydı eksik veya geçersiz."
    projection = body["projection"]
    if (
        not isinstance(projection, dict)
        or not isinstance(projection.get("valuation_asset"), str)
        or not isinstance(projection.get("total_equity"), str)
        or _allocation_rows(projection.get("allocations")) is None
    ):
        fields["projection"] = "projection valuation_asset/total_equity/allocations gerektirir."
    if _pair_rows(body.get("prices")) is None:
        fields["prices"] = "prices ikili string listesi olmalıdır."
    for name in ("fee_rate", "qty_step", "min_notional", "cash_reserve"):
        if not isinstance(body.get(name), str):
            fields[name] = f"{name} string olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _rebalance_disclose(validated: dict[str, object], now_us: int) -> dict[str, object]:
    plan_body = validated["plan"]
    assert isinstance(plan_body, dict)
    plan = RebalancePlan(
        plan_id=plan_body["plan_id"],  # type: ignore[arg-type]
        schema_version="rebalance-plan-v1",
        status="DRAFT",
        plan_time_us=plan_body["plan_time_us"],  # type: ignore[arg-type]
        valuation_asset=plan_body["valuation_asset"],  # type: ignore[arg-type]
        total_equity=plan_body["total_equity"],  # type: ignore[arg-type]
        gross_buy=plan_body["gross_buy"],  # type: ignore[arg-type]
        gross_sell=plan_body["gross_sell"],  # type: ignore[arg-type]
        trigger_policy=plan_body["trigger_policy"],  # type: ignore[arg-type]
    )
    projection_body = validated["projection"]
    assert isinstance(projection_body, dict)
    projection = build_rebalance_projection(
        valuation_asset=projection_body["valuation_asset"],  # type: ignore[arg-type]
        total_equity=projection_body["total_equity"],  # type: ignore[arg-type]
        allocations=tuple((r[0], r[1], r[2]) for r in projection_body["allocations"]),  # type: ignore[union-attr]
    )
    disclosure = disclose_execution(
        plan=plan,
        projection=projection,
        prices=tuple((r[0], r[1]) for r in validated["prices"]),  # type: ignore[union-attr]
        fee_rate=validated["fee_rate"],  # type: ignore[arg-type]
        qty_step=validated["qty_step"],  # type: ignore[arg-type]
        min_notional=validated["min_notional"],  # type: ignore[arg-type]
        cash_reserve=validated["cash_reserve"],  # type: ignore[arg-type]
    )
    candidates = (
        bind_execution_orders(disclosure, order_time_us=now_us)
        if disclosure.status == "READY"
        else ()
    )
    return {
        "disclosure": {
            "plan_id": disclosure.plan_id,
            "status": disclosure.status,
            "total_buy_gross": disclosure.total_buy_gross,
            "total_fee": disclosure.total_fee,
            "lines": [
                {
                    "asset": line.asset, "side": line.side,
                    "gross_delta": line.gross_delta, "fee": line.fee,
                    "net_delta": line.net_delta, "qty": line.qty,
                    "quantized_qty": line.quantized_qty,
                    "remainder_qty": line.remainder_qty,
                    "notional": line.notional, "status": line.status,
                }
                for line in disclosure.lines
            ],
        },
        "candidates": [
            {
                "candidate_id": c.candidate_id, "plan_id": c.plan_id,
                "asset": c.asset, "side": c.side, "qty": c.qty,
                "status": c.status,
            }
            for c in candidates
        ],
    }


def _signal_event_or_errors(body: dict[str, object], fields: dict[str, str]):
    signal = body.get("signal")
    if (
        not isinstance(signal, dict)
        or not isinstance(signal.get("signal_id"), str)
        or not isinstance(signal.get("source"), str)
        or type(signal.get("event_time_us")) is not int
        or not isinstance(signal.get("schema_version"), str)
        or not isinstance(signal.get("payload_hash"), str)
    ):
        fields["signal"] = "signal kimlik/zaman/hash alanları gerektirir."
        return None
    return signal


def _validate_signal_hash_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, SIGNAL_HASH_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    if not isinstance(body["payload"], dict):
        return None, {"payload": "payload JSON nesnesi olmalıdır."}
    return body, {}


def _signal_hash(validated: dict[str, object]) -> dict[str, object]:
    return {"payload_hash": hash_signal_payload(validated["payload"])}  # type: ignore[arg-type]


def _validate_signal_assess_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, SIGNAL_ASSESS_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    _signal_event_or_errors(body, fields)
    for name in ("closed_bar_time_us", "warmup_bars_observed", "required_warmup_bars", "max_staleness_us"):
        if type(body.get(name)) is not int:
            fields[name] = f"{name} integer olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _signal_assess(validated: dict[str, object]) -> dict[str, object]:
    signal = new_signal_event(
        signal_id=validated["signal"]["signal_id"],  # type: ignore[index]
        source=validated["signal"]["source"],  # type: ignore[index]
        event_time_us=validated["signal"]["event_time_us"],  # type: ignore[index]
        schema_version=validated["signal"]["schema_version"],  # type: ignore[index]
        payload_hash=validated["signal"]["payload_hash"],  # type: ignore[index]
    )
    result = assess_signal_readiness(
        signal,
        closed_bar_time_us=validated["closed_bar_time_us"],  # type: ignore[arg-type]
        warmup_bars_observed=validated["warmup_bars_observed"],  # type: ignore[arg-type]
        required_warmup_bars=validated["required_warmup_bars"],  # type: ignore[arg-type]
        max_staleness_us=validated["max_staleness_us"],  # type: ignore[arg-type]
    )
    return {
        "signal_id": result.signal_id,
        "status": result.status,
        "event_time_us": result.event_time_us,
        "closed_bar_time_us": result.closed_bar_time_us,
    }


def _validate_signal_candidate_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, SIGNAL_CANDIDATE_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    _signal_event_or_errors(body, fields)
    for name in ("closed_bar_time_us", "warmup_bars_observed", "required_warmup_bars", "max_staleness_us", "ttl_us"):
        if type(body.get(name)) is not int:
            fields[name] = f"{name} integer olmalıdır."
    for name in ("action", "symbol", "qty"):
        if not isinstance(body.get(name), str):
            fields[name] = f"{name} string olmalıdır."
    if _pair_rows(body.get("action_map")) is None:
        fields["action_map"] = "action_map ikili string listesi olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _signal_bind_candidate(validated: dict[str, object], now_us: int) -> dict[str, object]:
    signal = new_signal_event(
        signal_id=validated["signal"]["signal_id"],  # type: ignore[index]
        source=validated["signal"]["source"],  # type: ignore[index]
        event_time_us=validated["signal"]["event_time_us"],  # type: ignore[index]
        schema_version=validated["signal"]["schema_version"],  # type: ignore[index]
        payload_hash=validated["signal"]["payload_hash"],  # type: ignore[index]
    )
    readiness = assess_signal_readiness(
        signal,
        closed_bar_time_us=validated["closed_bar_time_us"],  # type: ignore[arg-type]
        warmup_bars_observed=validated["warmup_bars_observed"],  # type: ignore[arg-type]
        required_warmup_bars=validated["required_warmup_bars"],  # type: ignore[arg-type]
        max_staleness_us=validated["max_staleness_us"],  # type: ignore[arg-type]
    )
    candidate = bind_signal_candidate(
        signal=signal,
        readiness=readiness,
        action=validated["action"],  # type: ignore[arg-type]
        symbol=validated["symbol"],  # type: ignore[arg-type]
        action_map=tuple((r[0], r[1]) for r in validated["action_map"]),  # type: ignore[union-attr]
        qty=validated["qty"],  # type: ignore[arg-type]
        ttl_us=validated["ttl_us"],  # type: ignore[arg-type]
        binding_time_us=now_us,
    )
    return {
        "candidate_id": candidate.candidate_id,
        "status": candidate.status,
        "signal_id": candidate.signal_id,
        "symbol": candidate.symbol,
        "side": candidate.side,
        "qty": candidate.qty,
        "expires_us": candidate.expires_us,
    }


FUTURES_GRID_LEVELS_FIELDS = {"direction", "level_mode", "lower_price", "upper_price", "interval_count", "price_tick", "tick_origin"}
FUTURES_POSITION_PNL_FIELDS = {"side", "quantity", "contract_size", "entry_price", "mark_price", "settlement_asset"}


def _validate_futures_grid_levels_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, FUTURES_GRID_LEVELS_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    if body["direction"] not in ("LONG", "SHORT", "NEUTRAL"):
        fields["direction"] = "direction LONG, SHORT veya NEUTRAL olmalıdır."
    if body["level_mode"] not in ("ARITHMETIC", "GEOMETRIC"):
        fields["level_mode"] = "level_mode ARITHMETIC veya GEOMETRIC olmalıdır."
    for name in ("lower_price", "upper_price", "price_tick", "tick_origin"):
        if not isinstance(body.get(name), str):
            fields[name] = f"{name} string olmalıdır."
    if type(body.get("interval_count")) is not int:
        fields["interval_count"] = "interval_count integer olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _futures_grid_levels(validated: dict[str, object]) -> dict[str, object]:
    profile = FuturesGridProfile()
    result = project_futures_grid_levels(
        profile=profile,
        direction=validated["direction"],  # type: ignore[arg-type]
        initial_position_policy="FLAT",
        level_mode=validated["level_mode"],  # type: ignore[arg-type]
        lower_price=validated["lower_price"],  # type: ignore[arg-type]
        upper_price=validated["upper_price"],  # type: ignore[arg-type]
        interval_count=validated["interval_count"],  # type: ignore[arg-type]
        price_tick=validated["price_tick"],  # type: ignore[arg-type]
        tick_origin=validated["tick_origin"],  # type: ignore[arg-type]
    )
    return {
        "direction": result.direction,
        "level_mode": result.level_mode,
        "lower_price": result.lower_price,
        "upper_price": result.upper_price,
        "interval_count": result.interval_count,
        "levels": list(result.levels),
        "arithmetic_step": result.arithmetic_step,
        "ratio_numerator": result.ratio_numerator,
        "ratio_denominator": result.ratio_denominator,
        "profile": {
            "venue": profile.venue,
            "product_family": profile.product_family,
            "settlement_asset": profile.settlement_asset,
            "contract_type": profile.contract_type,
            "position_mode": profile.position_mode,
            "margin_mode": profile.margin_mode,
            "leverage": profile.leverage,
        },
    }


def _validate_futures_position_pnl_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, FUTURES_POSITION_PNL_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    if body["side"] not in ("LONG", "SHORT"):
        fields["side"] = "side LONG veya SHORT olmalıdır."
    for name in ("quantity", "contract_size", "entry_price", "mark_price", "settlement_asset"):
        if not isinstance(body.get(name), str):
            fields[name] = f"{name} string olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _futures_position_pnl(validated: dict[str, object]) -> dict[str, object]:
    require_settlement_asset(validated["settlement_asset"])
    position = LinearFuturesPosition(
        side=validated["side"],  # type: ignore[arg-type]
        quantity=validated["quantity"],  # type: ignore[arg-type]
        contract_size=validated["contract_size"],  # type: ignore[arg-type]
        entry_price=validated["entry_price"],  # type: ignore[arg-type]
        mark_price=validated["mark_price"],  # type: ignore[arg-type]
        settlement_asset=validated["settlement_asset"],  # type: ignore[arg-type]
    )
    return {
        "side": position.side,
        "effective_quantity": position.effective_quantity,
        "position_value": position.position_value,
        "unrealized_pnl": position.unrealized_pnl,
        "settlement_asset": position.settlement_asset,
    }


FUTURES_TRAILING_ARM_FIELDS = {"side", "activation_price", "distance"}
FUTURES_TRAILING_OBSERVE_FIELDS = {"side", "state", "price"}
FUTURES_FUNDING_FIELDS = {"position", "funding_rate", "effective_time_us"}


def _validate_futures_trailing_arm_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, FUTURES_TRAILING_ARM_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    if body["side"] not in ("LONG", "SHORT"):
        fields["side"] = "side LONG veya SHORT olmalıdır."
    for name in ("activation_price", "distance"):
        if not isinstance(body.get(name), str):
            fields[name] = f"{name} string olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _futures_trailing_arm(validated: dict[str, object]) -> dict[str, object]:
    if validated["side"] == "LONG":
        state = arm_long_trailing(
            activation_price=validated["activation_price"],  # type: ignore[arg-type]
            distance=validated["distance"],  # type: ignore[arg-type]
        )
        return {
            "status": state.status, "activation_price": state.activation_price,
            "distance": state.distance, "high_water": state.high_water,
            "stop_price": state.stop_price,
        }
    state = arm_short_trailing(
        activation_price=validated["activation_price"],  # type: ignore[arg-type]
        distance=validated["distance"],  # type: ignore[arg-type]
    )
    return {
        "status": state.status, "activation_price": state.activation_price,
        "distance": state.distance, "low_water": state.low_water,
        "stop_price": state.stop_price,
    }


def _validate_futures_trailing_observe_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, FUTURES_TRAILING_OBSERVE_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    if body["side"] not in ("LONG", "SHORT"):
        fields["side"] = "side LONG veya SHORT olmalıdır."
    state = body.get("state")
    water = "high_water" if body.get("side") == "LONG" else "low_water"
    if (
        not isinstance(state, dict)
        or state.get("status") not in ("INACTIVE", "ACTIVE", "TRIGGERED")
        or not isinstance(state.get("activation_price"), str)
        or not isinstance(state.get("distance"), str)
        or (state.get(water) is not None and not isinstance(state.get(water), str))
        or (state.get("stop_price") is not None and not isinstance(state.get("stop_price"), str))
    ):
        fields["state"] = "trailing state eksik veya geçersiz."
    if not isinstance(body.get("price"), str):
        fields["price"] = "price string olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _futures_trailing_observe(validated: dict[str, object]) -> dict[str, object]:
    state_body = validated["state"]
    assert isinstance(state_body, dict)
    if validated["side"] == "LONG":
        state = TrailingLongState(
            status=state_body["status"],  # type: ignore[arg-type]
            activation_price=state_body["activation_price"],  # type: ignore[arg-type]
            distance=state_body["distance"],  # type: ignore[arg-type]
            high_water=state_body.get("high_water"),  # type: ignore[arg-type]
            stop_price=state_body.get("stop_price"),  # type: ignore[arg-type]
        )
        result = observe_long_trailing(state, price=validated["price"])  # type: ignore[arg-type]
        return {
            "status": result.status, "activation_price": result.activation_price,
            "distance": result.distance, "high_water": result.high_water,
            "stop_price": result.stop_price,
        }
    state = TrailingShortState(
        status=state_body["status"],  # type: ignore[arg-type]
        activation_price=state_body["activation_price"],  # type: ignore[arg-type]
        distance=state_body["distance"],  # type: ignore[arg-type]
        low_water=state_body.get("low_water"),  # type: ignore[arg-type]
        stop_price=state_body.get("stop_price"),  # type: ignore[arg-type]
    )
    result = observe_short_trailing(state, price=validated["price"])  # type: ignore[arg-type]
    return {
        "status": result.status, "activation_price": result.activation_price,
        "distance": result.distance, "low_water": result.low_water,
        "stop_price": result.stop_price,
    }


def _validate_futures_funding_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, FUTURES_FUNDING_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    position = body.get("position")
    if (
        not isinstance(position, dict)
        or position.get("side") not in ("LONG", "SHORT")
        or not all(isinstance(position.get(n), str) for n in ("quantity", "contract_size", "entry_price", "mark_price", "settlement_asset"))
    ):
        fields["position"] = "position kaydı eksik veya geçersiz."
    if not isinstance(body.get("funding_rate"), str):
        fields["funding_rate"] = "funding_rate string olmalıdır."
    if type(body.get("effective_time_us")) is not int:
        fields["effective_time_us"] = "effective_time_us integer olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _futures_funding(validated: dict[str, object]) -> dict[str, object]:
    position_body = validated["position"]
    assert isinstance(position_body, dict)
    require_settlement_asset(position_body["settlement_asset"])
    position = LinearFuturesPosition(
        side=position_body["side"],  # type: ignore[arg-type]
        quantity=position_body["quantity"],  # type: ignore[arg-type]
        contract_size=position_body["contract_size"],  # type: ignore[arg-type]
        entry_price=position_body["entry_price"],  # type: ignore[arg-type]
        mark_price=position_body["mark_price"],  # type: ignore[arg-type]
        settlement_asset=position_body["settlement_asset"],  # type: ignore[arg-type]
    )
    result = project_funding(
        position,
        validated["funding_rate"],  # type: ignore[arg-type]
        effective_time_us=validated["effective_time_us"],  # type: ignore[arg-type]
    )
    return {
        "amount": result.amount,
        "core_expense": result.core_expense,
        "settlement_asset": result.settlement_asset,
        "effective_time_us": result.effective_time_us,
    }


TWO_LEG_SESSION_FIELDS = {"session_id"}
TWO_LEG_FILL_FIELDS = {
    "fill_id", "leg_id", "account_id", "venue_profile", "product_id",
    "symbol", "hedge_side", "quantity", "fill_status", "event_time_us",
}


def _validate_two_leg_session_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, TWO_LEG_SESSION_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    session_id = body.get("session_id")
    if type(session_id) is not str or _TWO_LEG_SESSION_RE.fullmatch(session_id) is None:
        fields["session_id"] = "session_id geçersiz kimlik olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _validate_two_leg_fill_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, TWO_LEG_FILL_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    for name in ("fill_id", "account_id", "venue_profile", "product_id", "symbol"):
        value = body.get(name)
        if type(value) is not str or _TWO_LEG_SESSION_RE.fullmatch(value) is None:
            fields[name] = f"{name} geçersiz kimlik olmalıdır."
    if body.get("leg_id") not in ("A", "B"):
        fields["leg_id"] = "leg_id A veya B olmalıdır."
    if body.get("hedge_side") not in ("LONG", "SHORT"):
        fields["hedge_side"] = "hedge_side LONG veya SHORT olmalıdır."
    if not isinstance(body.get("quantity"), str):
        fields["quantity"] = "quantity string olmalıdır."
    if body.get("fill_status") not in ("PARTIAL", "FULL"):
        fields["fill_status"] = "fill_status PARTIAL veya FULL olmalıdır."
    if type(body.get("event_time_us")) is not int:
        fields["event_time_us"] = "event_time_us integer olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _two_leg_projection_data(projection: TwoLegFillProjection) -> dict[str, object]:
    return {
        "state": projection.state,
        "leg_a_identity": _two_leg_identity_data(projection.leg_a_identity),
        "leg_b_identity": _two_leg_identity_data(projection.leg_b_identity),
        "leg_a_quantity": projection.leg_a_quantity,
        "leg_b_quantity": projection.leg_b_quantity,
        "leg_a_status": projection.leg_a_status,
        "leg_b_status": projection.leg_b_status,
        "fills": [
            {
                "fill_id": fill.fill_id,
                "leg_id": fill.leg_id,
                "quantity": fill.quantity,
                "fill_status": fill.fill_status,
                "event_time_us": fill.event_time_us,
            }
            for fill in projection.fills
        ],
    }


def _two_leg_identity_data(identity: HedgePositionIdentity | None) -> dict[str, object] | None:
    if identity is None:
        return None
    return {
        "account_id": identity.account_id,
        "venue_profile": identity.venue_profile,
        "product_id": identity.product_id,
        "symbol": identity.symbol,
        "position_mode": identity.position_mode,
        "hedge_side": identity.hedge_side,
    }


def _two_leg_start(journal: TwoLegJournal, validated: dict[str, object]) -> dict[str, object]:
    session_id = validated["session_id"]
    assert isinstance(session_id, str)
    result = journal.start(session_id)
    return {
        "session_id": session_id,
        "result": result,
        "projection": _two_leg_projection_data(journal.replay(session_id)),
    }


def _two_leg_accept_fill(
    journal: TwoLegJournal, session_id: str, validated: dict[str, object]
) -> dict[str, object]:
    fill = LegFill(
        fill_id=validated["fill_id"],  # type: ignore[arg-type]
        leg_id=validated["leg_id"],  # type: ignore[arg-type]
        position=new_hedge_position_identity(
            account_id=validated["account_id"],  # type: ignore[arg-type]
            venue_profile=validated["venue_profile"],  # type: ignore[arg-type]
            product_id=validated["product_id"],  # type: ignore[arg-type]
            symbol=validated["symbol"],  # type: ignore[arg-type]
            position_mode="HEDGE",
            hedge_side=validated["hedge_side"],  # type: ignore[arg-type]
        ),
        quantity=validated["quantity"],  # type: ignore[arg-type]
        fill_status=validated["fill_status"],  # type: ignore[arg-type]
        event_time_us=validated["event_time_us"],  # type: ignore[arg-type]
    )
    result = journal.accept_fill(session_id, fill)
    return {
        "session_id": session_id,
        "result": result,
        "projection": _two_leg_projection_data(journal.replay(session_id)),
    }


def _two_leg_mark(
    journal: TwoLegJournal, session_id: str, terminal: str
) -> dict[str, object]:
    if terminal == "RECOVERY_REQUIRED":
        projection = journal.mark_recovery(session_id)
    elif terminal == "TIMEOUT":
        projection = journal.mark_timeout(session_id)
    else:
        raise ValueError(f"Bilinmeyen terminal işareti: {terminal}")
    return {
        "session_id": session_id,
        "result": "MARKED",
        "projection": _two_leg_projection_data(projection),
    }


def _two_leg_replay(journal: TwoLegJournal, session_id: str) -> dict[str, object]:
    return {
        "session_id": session_id,
        "projection": _two_leg_projection_data(journal.replay(session_id)),
    }


BOT_REGISTER_REQUIRED = {"bot_id", "name", "pairs"}
BOT_REGISTER_OPTIONAL = {"blacklist", "favorites", "virtual_quote_budget"}
BOT_LISTS_FIELDS = {"blacklist", "favorites"}
BOT_BIND_FIELDS = {"session_id", "symbol"}
BOT_CHECK_FIELDS = {"symbol"}


def _validate_bot_register_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    if not isinstance(payload, dict):
        return None, {"body": "JSON gövdesi nesne olmalıdır."}
    allowed = BOT_REGISTER_REQUIRED | BOT_REGISTER_OPTIONAL
    unknown = set(payload) - allowed
    missing = BOT_REGISTER_REQUIRED - set(payload)
    fields: dict[str, str] = {}
    if unknown:
        fields["body"] = "Bilinmeyen alanlar: " + ", ".join(sorted(unknown))
    if missing:
        fields["body"] = (fields.get("body", "") + (" " if fields.get("body") else "")
                           + "Eksik alanlar: " + ", ".join(sorted(missing)))
    for name in ("bot_id", "name"):
        if name in payload and not isinstance(payload[name], str):
            fields[name] = f"{name} string olmalıdır."
    if "pairs" in payload and (
        not isinstance(payload["pairs"], list)
        or not all(isinstance(s, str) for s in payload["pairs"])
    ):
        fields["pairs"] = "pairs string listesi olmalıdır."
    for name in ("blacklist", "favorites"):
        if name in payload and (
            not isinstance(payload[name], list)
            or not all(isinstance(s, str) for s in payload[name])
        ):
            fields[name] = f"{name} string listesi olmalıdır."
    if "virtual_quote_budget" in payload and not isinstance(payload["virtual_quote_budget"], str):
        fields["virtual_quote_budget"] = "virtual_quote_budget string olmalıdır."
    if fields:
        return None, fields
    return payload, {}


def _validate_bot_lists_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, BOT_LISTS_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    for name in ("blacklist", "favorites"):
        if not isinstance(body.get(name), list) or not all(
            isinstance(s, str) for s in body[name]  # type: ignore[union-attr]
        ):
            fields[name] = f"{name} string listesi olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _validate_bot_bind_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, BOT_BIND_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    for name in ("session_id", "symbol"):
        if not isinstance(body.get(name), str):
            fields[name] = f"{name} string olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _validate_bot_check_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, BOT_CHECK_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    if not isinstance(body.get("symbol"), str):
        fields["symbol"] = "symbol string olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _bot_profile_data(profile: BotProfile) -> dict[str, object]:
    return {
        "bot_id": profile.bot_id,
        "name": profile.name,
        "pairs": list(profile.pairs),
        "blacklist": list(profile.blacklist),
        "favorites": list(profile.favorites),
        "virtual_quote_budget": profile.virtual_quote_budget,
    }


def _bot_register(registry: BotRegistry, validated: dict[str, object]) -> dict[str, object]:
    profile = new_bot_profile(
        bot_id=validated["bot_id"],  # type: ignore[arg-type]
        name=validated["name"],  # type: ignore[arg-type]
        pairs=validated["pairs"],  # type: ignore[arg-type]
        blacklist=validated.get("blacklist", ()),  # type: ignore[arg-type]
        favorites=validated.get("favorites", ()),  # type: ignore[arg-type]
        virtual_quote_budget=validated.get("virtual_quote_budget", "0"),  # type: ignore[arg-type]
    )
    result = registry.register(profile)
    return {"bot_id": profile.bot_id, "result": result, "profile": _bot_profile_data(profile)}


def _bot_list(registry: BotRegistry) -> dict[str, object]:
    return {"bot_ids": list(registry.list_ids())}


def _bot_get(registry: BotRegistry, bot_id: str) -> dict[str, object]:
    return {
        "bot_id": bot_id,
        "profile": _bot_profile_data(registry.get(bot_id)),
        "sessions": registry.sessions_of(bot_id),
    }


def _bot_update_lists(
    registry: BotRegistry, bot_id: str, validated: dict[str, object]
) -> dict[str, object]:
    updated = registry.update_lists(
        bot_id,
        blacklist=validated["blacklist"],  # type: ignore[arg-type]
        favorites=validated["favorites"],  # type: ignore[arg-type]
    )
    return {"bot_id": bot_id, "result": "UPDATED", "profile": _bot_profile_data(updated)}


def _bot_bind_session(
    registry: BotRegistry, bot_id: str, validated: dict[str, object]
) -> dict[str, object]:
    session_id = validated["session_id"]
    symbol = validated["symbol"]
    assert isinstance(session_id, str) and isinstance(symbol, str)
    result = registry.bind_session(bot_id, session_id, symbol)
    return {"bot_id": bot_id, "session_id": session_id, "result": result, "owner": bot_id}


def _bot_check_pair(
    registry: BotRegistry, bot_id: str, validated: dict[str, object]
) -> dict[str, object]:
    symbol = validated["symbol"]
    assert isinstance(symbol, str)
    verdict, reason = registry.check_pair(bot_id, symbol)
    return {"bot_id": bot_id, "symbol": symbol, "verdict": verdict, "reason": reason}


DEAL_CREATE_REQUIRED = {"deal_id", "config_revision_id"}
DEAL_CREATE_OPTIONAL = {"config_snapshot"}
DEAL_EVENT_REQUIRED = {"event_id", "config_revision_id", "event", "event_sequence"}
DEAL_EVENT_OPTIONAL = {"config_snapshot"}
DEAL_BULK_ACTION_REQUIRED = DEAL_EVENT_REQUIRED | {"deal_id"}
DEAL_BULK_ACTION_OPTIONAL = DEAL_EVENT_OPTIONAL


def _validate_deal_create_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    if not isinstance(payload, dict):
        return None, {"body": "JSON gövdesi nesne olmalıdır."}
    allowed = DEAL_CREATE_REQUIRED | DEAL_CREATE_OPTIONAL
    unknown = set(payload) - allowed
    missing = DEAL_CREATE_REQUIRED - set(payload)
    fields: dict[str, str] = {}
    if unknown:
        fields["body"] = "Bilinmeyen alanlar: " + ", ".join(sorted(unknown))
    if missing:
        fields["body"] = (fields.get("body", "") + (" " if fields.get("body") else "")
                           + "Eksik alanlar: " + ", ".join(sorted(missing)))
    for name in ("deal_id", "config_revision_id"):
        if name in payload and not isinstance(payload[name], str):
            fields[name] = f"{name} string olmalıdır."
    if "config_snapshot" in payload and not isinstance(payload["config_snapshot"], dict):
        fields["config_snapshot"] = "config_snapshot nesne olmalıdır."
    if fields:
        return None, fields
    return payload, {}


def _validate_deal_event_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    if not isinstance(payload, dict):
        return None, {"body": "JSON gövdesi nesne olmalıdır."}
    allowed = DEAL_EVENT_REQUIRED | DEAL_EVENT_OPTIONAL
    unknown = set(payload) - allowed
    missing = DEAL_EVENT_REQUIRED - set(payload)
    fields: dict[str, str] = {}
    if unknown:
        fields["body"] = "Bilinmeyen alanlar: " + ", ".join(sorted(unknown))
    if missing:
        fields["body"] = (fields.get("body", "") + (" " if fields.get("body") else "")
                           + "Eksik alanlar: " + ", ".join(sorted(missing)))
    _check_deal_event_fields(payload, fields)
    if fields:
        return None, fields
    return payload, {}


def _validate_deal_bulk_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    if not isinstance(payload, dict) or set(payload) != {"actions"}:
        return None, {"body": "Gövde yalnız actions listesi taşımalıdır."}
    actions = payload["actions"]
    if not isinstance(actions, list) or not 1 <= len(actions) <= 32:
        return None, {"actions": "actions 1-32 arası liste olmalıdır."}
    allowed = DEAL_BULK_ACTION_REQUIRED | DEAL_BULK_ACTION_OPTIONAL
    fields: dict[str, str] = {}
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            fields[f"actions[{index}]"] = "Aksiyon nesne olmalıdır."
            continue
        unknown = set(action) - allowed
        missing = DEAL_BULK_ACTION_REQUIRED - set(action)
        if unknown or missing:
            fields[f"actions[{index}]"] = "Aksiyon alanları eksik veya fazla."
            continue
        if not isinstance(action.get("deal_id"), str):
            fields[f"actions[{index}].deal_id"] = "deal_id string olmalıdır."
        sub: dict[str, str] = {}
        _check_deal_event_fields(action, sub)
        for key, message in sub.items():
            fields[f"actions[{index}].{key}"] = message
    if fields:
        return None, fields
    return payload, {}


def _check_deal_event_fields(body: dict[str, object], fields: dict[str, str]) -> None:
    for name in ("event_id", "config_revision_id"):
        if name in body and not isinstance(body[name], str):
            fields[name] = f"{name} string olmalıdır."
    if "config_snapshot" in body and not isinstance(body["config_snapshot"], dict):
        fields["config_snapshot"] = "config_snapshot nesne olmalıdır."
    if "event" in body and body["event"] not in _DEAL_EVENTS:
        fields["event"] = "event geçersiz lifecycle olayı."
    if "event_sequence" in body and type(body["event_sequence"]) is not int:
        fields["event_sequence"] = "event_sequence integer olmalıdır."


def _deal_snapshot(validated: dict[str, object]) -> dict[str, object]:
    snapshot = validated.get("config_snapshot")
    if snapshot is None:
        return _load_config()
    assert isinstance(snapshot, dict)
    return snapshot


def _deal_path(deals_dir: Path, deal_id: str) -> Path:
    if _TWO_LEG_SESSION_RE.fullmatch(deal_id) is None or ":" in deal_id:
        raise LifecycleStoreError("DEAL_ID_INVALID", "Deal kimliği dosya-güvenli değil.")
    return deals_dir / f"{deal_id}.sqlite3"


def _deal_lifecycle_data(lifecycle: DealLifecycle | None) -> dict[str, object] | None:
    if lifecycle is None:
        return None
    return {
        "deal_id": lifecycle.deal_id,
        "config_revision_id": lifecycle.config_revision_id,
        "status": lifecycle.status,
        "event_sequence": lifecycle.event_sequence,
    }


def _deal_event_data(event: LifecycleEvent) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "deal_id": event.deal_id,
        "config_revision_id": event.config_revision_id,
        "event": event.event,
        "event_sequence": event.event_sequence,
    }


def _deal_create(deals_dir: Path, validated: dict[str, object]) -> dict[str, object]:
    deal_id = validated["deal_id"]
    revision_id = validated["config_revision_id"]
    assert isinstance(deal_id, str) and isinstance(revision_id, str)
    new_config_revision(revision_id, _deal_snapshot(validated))
    path = _deal_path(deals_dir, deal_id)
    if path.exists():
        return {"deal_id": deal_id, "result": "DUPLICATE"}
    deals_dir.mkdir(parents=True, exist_ok=True)
    with LifecycleStore.create(path):
        pass
    return {"deal_id": deal_id, "result": "CREATED"}


def _deal_append_event(
    deals_dir: Path, deal_id: str, validated: dict[str, object]
) -> dict[str, object]:
    path = _deal_path(deals_dir, deal_id)
    if not path.exists():
        raise LifecycleStoreError("DEAL_UNKNOWN", "Deal kayıtlı değil.")
    revision_id = validated["config_revision_id"]
    assert isinstance(revision_id, str)
    revision = new_config_revision(revision_id, _deal_snapshot(validated))
    event = new_lifecycle_event(
        validated["event_id"],  # type: ignore[arg-type]
        deal_id,
        revision_id,
        validated["event"],  # type: ignore[arg-type]
        validated["event_sequence"],  # type: ignore[arg-type]
    )
    with LifecycleStore.open(path) as store:
        result = store.append(event, config_revision=revision)
        replay = store.load()
    return {
        "deal_id": deal_id,
        "result": result,
        "lifecycle": _deal_lifecycle_data(replay.lifecycle),
    }


def _deal_replay(deals_dir: Path, deal_id: str) -> dict[str, object]:
    path = _deal_path(deals_dir, deal_id)
    if not path.exists():
        raise LifecycleStoreError("DEAL_UNKNOWN", "Deal kayıtlı değil.")
    with LifecycleStore.open(path) as store:
        replay = store.load()
    return {
        "deal_id": deal_id,
        "lifecycle": _deal_lifecycle_data(replay.lifecycle),
        "history": [_deal_event_data(event) for event in replay.history],
    }


def _deal_bulk(deals_dir: Path, validated: dict[str, object]) -> dict[str, object]:
    actions = validated["actions"]
    assert isinstance(actions, list)
    results: list[dict[str, object]] = []
    for action in actions:
        assert isinstance(action, dict)
        deal_id = action["deal_id"]
        assert isinstance(deal_id, str)
        try:
            outcome = _deal_append_event(deals_dir, deal_id, action)
            results.append({
                "deal_id": deal_id,
                "event_id": action["event_id"],
                "result": outcome["result"],
            })
        except ValueError as exc:
            results.append({
                "deal_id": deal_id,
                "event_id": action["event_id"],
                "error": str(exc),
            })
    return {"results": results}


EXITS_BIND_FIELDS = {
    "side", "kind", "state", "open_qty", "accepted_exit_fills",
    "committed_exit_qty", "requested_qty",
}
EXITS_PERCENT_ARM_FIELDS = {"side", "activation_price", "rate"}
EXITS_PERCENT_OBSERVE_FIELDS = {"side", "state", "price"}
EXITS_BREAKEVEN_REQUIRED = {"plan", "fills"}
EXITS_BREAKEVEN_OPTIONAL = {"fee_profile"}
EXITS_PLAN_FIELDS = {
    "side", "anchor_price", "base_amount", "base_sizing", "safety_amount",
    "safety_sizing", "safety_count", "deviation", "step_multiplier",
    "volume_multiplier", "price_tick", "quantity_step",
}
EXITS_FILL_FIELDS = {"execution_id", "level_index", "quantity", "price"}
EXITS_FEE_FIELDS = {
    "settlement_asset", "fee_asset", "entry_fee_rate", "exit_fee_rate",
    "funding_cashflow", "profile_revision",
}


def _validate_exits_trailing_bind_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, EXITS_BIND_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    if body.get("side") not in ("LONG", "SHORT"):
        fields["side"] = "side LONG veya SHORT olmalıdır."
    if body.get("kind") not in ("FIXED", "PERCENT"):
        fields["kind"] = "kind FIXED veya PERCENT olmalıdır."
    _check_exits_state(body.get("side"), body.get("kind"), body.get("state"), fields)
    for name in ("open_qty", "requested_qty"):
        if not isinstance(body.get(name), str):
            fields[name] = f"{name} string olmalıdır."
    for name in ("accepted_exit_fills", "committed_exit_qty"):
        if not isinstance(body.get(name), list) or not all(
            isinstance(s, str) for s in body[name]  # type: ignore[union-attr]
        ):
            fields[name] = f"{name} string listesi olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _check_exits_state(side: object, kind: object, state: object, fields: dict[str, str]) -> None:
    water = "high_water" if side == "LONG" else "low_water"
    offset = "distance" if kind == "FIXED" else "rate"
    if (
        not isinstance(state, dict)
        or state.get("status") not in ("INACTIVE", "ACTIVE", "TRIGGERED")
        or not isinstance(state.get("activation_price"), str)
        or not isinstance(state.get(offset), str)
        or (state.get(water) is not None and not isinstance(state.get(water), str))
        or (state.get("stop_price") is not None and not isinstance(state.get("stop_price"), str))
    ):
        fields["state"] = "trailing state eksik veya geçersiz."


def _exits_state_from_body(side: str, kind: str, state_body: dict[str, object]):
    water_key = "high_water" if side == "LONG" else "low_water"
    if kind == "FIXED":
        cls = TrailingLongState if side == "LONG" else TrailingShortState
        return cls(
            status=state_body["status"],  # type: ignore[arg-type]
            activation_price=state_body["activation_price"],  # type: ignore[arg-type]
            distance=state_body["distance"],  # type: ignore[arg-type]
            **{water_key: state_body.get(water_key)},  # type: ignore[arg-type]
            stop_price=state_body.get("stop_price"),  # type: ignore[arg-type]
        )
    cls = TrailingLongPercentageState if side == "LONG" else TrailingShortPercentageState
    return cls(
        status=state_body["status"],  # type: ignore[arg-type]
        activation_price=state_body["activation_price"],  # type: ignore[arg-type]
        rate=state_body["rate"],  # type: ignore[arg-type]
        **{water_key: state_body.get(water_key)},  # type: ignore[arg-type]
        stop_price=state_body.get("stop_price"),  # type: ignore[arg-type]
    )


def _exits_state_data(side: str, kind: str, state) -> dict[str, object]:
    water_key = "high_water" if side == "LONG" else "low_water"
    data: dict[str, object] = {
        "status": state.status,
        "activation_price": state.activation_price,
        water_key: getattr(state, water_key),
        "stop_price": state.stop_price,
    }
    data["distance" if kind == "FIXED" else "rate"] = (
        state.distance if kind == "FIXED" else state.rate
    )
    return data


def _exits_trailing_bind(validated: dict[str, object]) -> dict[str, object]:
    side = validated["side"]
    kind = validated["kind"]
    state_body = validated["state"]
    assert isinstance(side, str) and isinstance(kind, str)
    assert isinstance(state_body, dict)
    trailing = _exits_state_from_body(side, kind, state_body)
    accepted = validated["accepted_exit_fills"]
    committed = validated["committed_exit_qty"]
    assert isinstance(accepted, list) and isinstance(committed, list)
    binding = bind_trailing_exit_candidate(
        trailing=trailing,
        open_qty=validated["open_qty"],  # type: ignore[arg-type]
        accepted_exit_fills=tuple(accepted),
        committed_exit_qty=tuple(committed),
        requested_qty=validated["requested_qty"],  # type: ignore[arg-type]
    )
    return {
        "trigger_price": binding.trigger_price,
        "requested_qty": binding.requested_qty,
        "remaining_capacity": binding.remaining_capacity,
        "order_authority": binding.order_authority,
    }


def _validate_exits_percent_arm_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, EXITS_PERCENT_ARM_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    if body.get("side") not in ("LONG", "SHORT"):
        fields["side"] = "side LONG veya SHORT olmalıdır."
    for name in ("activation_price", "rate"):
        if not isinstance(body.get(name), str):
            fields[name] = f"{name} string olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _exits_percent_arm(validated: dict[str, object]) -> dict[str, object]:
    side = validated["side"]
    assert isinstance(side, str)
    if side == "LONG":
        state = arm_long_percentage_trailing(
            activation_price=validated["activation_price"],  # type: ignore[arg-type]
            rate=validated["rate"],  # type: ignore[arg-type]
        )
    else:
        state = arm_short_percentage_trailing(
            activation_price=validated["activation_price"],  # type: ignore[arg-type]
            rate=validated["rate"],  # type: ignore[arg-type]
        )
    return _exits_state_data(side, "PERCENT", state)


def _validate_exits_percent_observe_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, EXITS_PERCENT_OBSERVE_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    if body.get("side") not in ("LONG", "SHORT"):
        fields["side"] = "side LONG veya SHORT olmalıdır."
    _check_exits_state(body.get("side"), "PERCENT", body.get("state"), fields)
    if not isinstance(body.get("price"), str):
        fields["price"] = "price string olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _exits_percent_observe(validated: dict[str, object]) -> dict[str, object]:
    side = validated["side"]
    state_body = validated["state"]
    assert isinstance(side, str) and isinstance(state_body, dict)
    state = _exits_state_from_body(side, "PERCENT", state_body)
    if side == "LONG":
        result = observe_long_percentage_trailing(state, price=validated["price"])  # type: ignore[arg-type]
    else:
        result = observe_short_percentage_trailing(state, price=validated["price"])  # type: ignore[arg-type]
    return _exits_state_data(side, "PERCENT", result)


def _validate_exits_breakeven_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    if not isinstance(payload, dict):
        return None, {"body": "JSON gövdesi nesne olmalıdır."}
    allowed = EXITS_BREAKEVEN_REQUIRED | EXITS_BREAKEVEN_OPTIONAL
    unknown = set(payload) - allowed
    missing = EXITS_BREAKEVEN_REQUIRED - set(payload)
    fields: dict[str, str] = {}
    if unknown or missing:
        fields["body"] = "Gövde plan+fills (+fee_profile) taşımalıdır."
        return None, fields
    plan = payload["plan"]
    if not isinstance(plan, dict) or set(plan) != EXITS_PLAN_FIELDS:
        fields["plan"] = "plan alanları eksik veya fazla."
    elif type(plan.get("safety_count")) is not int or not all(
        isinstance(plan.get(name), str) for name in EXITS_PLAN_FIELDS - {"side", "safety_count"}
    ) or plan.get("side") not in ("LONG", "SHORT"):
        fields["plan"] = "plan alan türleri geçersiz."
    fills = payload["fills"]
    if not isinstance(fills, list) or not fills:
        fields["fills"] = "fills boş olmayan liste olmalıdır."
    else:
        for index, fill in enumerate(fills):
            if not isinstance(fill, dict) or set(fill) != EXITS_FILL_FIELDS:
                fields[f"fills[{index}]"] = "fill alanları eksik veya fazla."
            elif (
                not isinstance(fill.get("execution_id"), str)
                or type(fill.get("level_index")) is not int
                or not isinstance(fill.get("quantity"), str)
                or not isinstance(fill.get("price"), str)
            ):
                fields[f"fills[{index}]"] = "fill alan türleri geçersiz."
    profile = payload.get("fee_profile")
    if profile is not None and (
        not isinstance(profile, dict)
        or set(profile) != EXITS_FEE_FIELDS
        or not all(isinstance(profile.get(name), str) for name in EXITS_FEE_FIELDS)
    ):
        fields["fee_profile"] = "fee_profile alanları eksik veya geçersiz."
    if fields:
        return None, fields
    return payload, {}


def _exits_breakeven(validated: dict[str, object]) -> dict[str, object]:
    plan_body = validated["plan"]
    fills_body = validated["fills"]
    assert isinstance(plan_body, dict) and isinstance(fills_body, list)
    plan = project_futures_dca_plan(
        side=plan_body["side"],  # type: ignore[arg-type]
        anchor_price=plan_body["anchor_price"],  # type: ignore[arg-type]
        base_amount=plan_body["base_amount"],  # type: ignore[arg-type]
        base_sizing=plan_body["base_sizing"],  # type: ignore[arg-type]
        safety_amount=plan_body["safety_amount"],  # type: ignore[arg-type]
        safety_sizing=plan_body["safety_sizing"],  # type: ignore[arg-type]
        safety_count=plan_body["safety_count"],  # type: ignore[arg-type]
        deviation=plan_body["deviation"],  # type: ignore[arg-type]
        step_multiplier=plan_body["step_multiplier"],  # type: ignore[arg-type]
        volume_multiplier=plan_body["volume_multiplier"],  # type: ignore[arg-type]
        price_tick=plan_body["price_tick"],  # type: ignore[arg-type]
        quantity_step=plan_body["quantity_step"],  # type: ignore[arg-type]
    )
    fills = tuple(
        FuturesDcaFill(
            fill["execution_id"],  # type: ignore[arg-type]
            fill["level_index"],  # type: ignore[arg-type]
            fill["quantity"],  # type: ignore[arg-type]
            fill["price"],  # type: ignore[arg-type]
        )
        for fill in fills_body
    )
    projection = project_futures_dca_fills(plan, fills)
    profile_body = validated.get("fee_profile")
    profile = None
    if profile_body is not None:
        assert isinstance(profile_body, dict)
        require_settlement_asset(profile_body["settlement_asset"])
        profile = FuturesDcaFeeAwareProfile(
            settlement_asset=profile_body["settlement_asset"],  # type: ignore[arg-type]
            fee_asset=profile_body["fee_asset"],  # type: ignore[arg-type]
            entry_fee_rate=profile_body["entry_fee_rate"],  # type: ignore[arg-type]
            exit_fee_rate=profile_body["exit_fee_rate"],  # type: ignore[arg-type]
            funding_cashflow=profile_body["funding_cashflow"],  # type: ignore[arg-type]
            profile_revision=profile_body["profile_revision"],  # type: ignore[arg-type]
        )
    result = assess_futures_dca_breakeven(projection, fee_profile=profile)
    return {
        "status": str(result.status),
        "gross_breakeven_price": result.gross_breakeven_price,
        "fee_aware_breakeven_price": result.fee_aware_breakeven_price,
        "reason": result.reason,
        "profile_revision": result.profile_revision,
        "order_authority": result.order_authority,
    }


app = FastAPI(title="DCABOT Offline API", version="0.1.0")
app.router.route_class = BoundedAPIRoute

WORKER_LOCK_PATH = ROOT / "data" / ".api-single-worker.lock"
_worker_guard: SingleWorkerGuard | None = None


def enforce_single_worker(lock_path: Path = WORKER_LOCK_PATH) -> SingleWorkerGuard:
    return SingleWorkerGuard(lock_path).acquire()


@app.on_event("startup")
def _acquire_worker_lock() -> None:
    global _worker_guard
    _worker_guard = enforce_single_worker()


@app.on_event("shutdown")
def _release_worker_lock() -> None:
    global _worker_guard
    if _worker_guard is not None:
        _worker_guard.release()
        _worker_guard = None


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
    if code == "TESTNET_OPEN_ORDERS_SYMBOL_INVALID":
        return _problem(
            400,
            code,
            "Symbol parametresi geçersiz",
            "Açık emir sorgusundaki symbol değeri geçersiz.",
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


def _draft_level_data(loaded, artifact_sha256: str, draft_price: str) -> dict[str, object]:
    if artifact_sha256 != loaded.metadata.artifact_sha256:
        raise ValueError(
            "DRAFT_ARTIFACT_MISMATCH: Taslak, yüklü dataset revisionına ait değil."
        )
    lows = [number(bar.low) for bar in loaded.bars]
    highs = [number(bar.high) for bar in loaded.bars]
    if not lows:
        raise ValueError("DRAFT_RANGE_INVALID: Dataset bar içermiyor.")
    verdict = validate_draft_level(
        low=exact_text(min(lows)),
        high=exact_text(max(highs)),
        draft_price=draft_price,
    )
    return {
        **verdict,
        "dataset_id": loaded.metadata.dataset_id,
        "artifact_sha256": loaded.metadata.artifact_sha256,
    }


@app.post("/api/datasets/{dataset_id}/draft-level", response_model=DraftLevelResponse)
async def create_draft_level(dataset_id: str, request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return _problem(
            400,
            "DRAFT_BODY_INVALID",
            "Taslak gövdesi okunamadı",
            "JSON gövdesi ayrıştırılamadı.",
        )
    try:
        body = DraftLevelRequest(**payload)
    except ValidationError:
        return _problem(
            422,
            "DRAFT_BODY_INVALID",
            "Taslak gövdesi geçersiz",
            "artifact_sha256 ve draft_price gerekli.",
        )
    result = _dataset_preflight(dataset_id)
    if isinstance(result, JSONResponse):
        return result
    loaded, _preflight = result
    try:
        data = _draft_level_data(loaded, body.artifact_sha256, body.draft_price)
    except ValueError as exc:
        return _problem(
            422,
            "DRAFT_LEVEL_INVALID",
            "Taslak seviye geçersiz",
            str(exc),
        )
    return DraftLevelResponse(**data)


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


def _historical_run_export_data(detail: dict[str, object], format: str) -> dict[str, object]:
    if format == "json":
        content = export_run_json(detail)
        note = "Tam kayıt; canonical JSON."
    elif format == "csv":
        content = export_run_csv(detail)
        note = "Özet satır; tam kayıt JSON formatındadır."
    else:
        raise ValueError(f"Desteklenmeyen export formatı: {format}")
    run_id = detail["run_id"]
    assert isinstance(run_id, str)
    return {
        "format": format,
        "filename": f"historical-run-{run_id}.{format}",
        "content": content,
        "note": note,
    }


@app.get("/api/historical-runs/{run_id}/export", response_model=HistoricalRunExportResponse)
def export_historical_run(run_id: str, response: Response, format: str = "json"):
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
    if format not in ("json", "csv"):
        return _problem(
            422,
            "EXPORT_FORMAT_INVALID",
            "Export formatı geçersiz",
            "Desteklenen formatlar: json, csv.",
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
    data = _historical_run_export_data(
        {
            "run_id": detail.run_id,
            "created_at": detail.created_at,
            "storage_state": detail.storage_state,
            "execution_status": detail.execution_status,
            "dataset": detail.dataset,
            "input_snapshot": detail.input_snapshot,
            "config": detail.config,
            "instrument_risk": detail.instrument_risk,
            "execution": detail.execution,
            "result_snapshot": detail.result_snapshot,
            "result_sha256": detail.result_sha256,
            "record_sha256": detail.record_sha256,
            "evaluation_lineage": detail.evaluation_lineage,
        },
        format,
    )
    if len(data["content"].encode("utf-8")) > MAX_HISTORICAL_RUN_DETAIL_RESPONSE_BYTES:  # type: ignore[union-attr]
        return _problem(
            422,
            "RUN_EXPORT_TOO_LARGE",
            "Export çok büyük",
            "Export içeriği izin verilen response byte sınırını aşıyor.",
        )
    return HistoricalRunExportResponse(**data)


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


@app.post("/api/rebalance/valuation")
async def create_rebalance_valuation(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_rebalance_valuation_payload(payload)
    if fields:
        return JSONResponse(
            status_code=422,
            content=_error("İstek doğrulanamadı.", fields=fields),
        )
    try:
        return {"data": _calculate_rebalance_valuation(validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(
            status_code=422,
            content=_error(str(exc), fields={"valuation": str(exc)}),
        )


@app.post("/api/paper/sessions")
async def create_paper_session(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_paper_activation_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with PAPER_LOCK:
            data = _paper_activate(PAPER_STORE, validated, time.time_ns() // 1000)
            with EVENT_LOCK:
                _record_event(
                    EVENT_LOG, "PAPER_ACTIVATED", str(data["session_id"]),
                    f"Paper session açıldı (nakit {data['cash']}).",
                    time.time_ns() // 1000,
                )
            return {"data": data}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"session": str(exc)}))


@app.post("/api/paper/sessions/{session_id}/orders")
async def place_paper_session_order(session_id: str, request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_paper_order_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with PAPER_LOCK:
            return {"data": _paper_place(PAPER_STORE, session_id, validated, time.time_ns() // 1000)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"order": str(exc)}))


@app.post("/api/paper/sessions/{session_id}/fills")
async def fill_paper_session_order(session_id: str, request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_paper_fill_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with PAPER_LOCK:
            data = _paper_fill(PAPER_STORE, session_id, validated, time.time_ns() // 1000)
            with EVENT_LOCK:
                _record_event(
                    EVENT_LOG, "PAPER_FILLED", session_id,
                    f"Paper fill işlendi ({validated['event_id']}).",
                    time.time_ns() // 1000,
                )
            return {"data": data}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"fill": str(exc)}))


@app.post("/api/paper/sessions/{session_id}/market-refresh")
async def refresh_paper_session_market(session_id: str, request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    if payload != {}:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields={"body": "Gövde boş nesne olmalıdır."}))

    def _fetch(symbol: str):
        now_us = time.time_ns() // 1000
        return fetch_binance_public_trades(
            symbol,
            limit=PAPER_REFRESH_LIMIT,
            allowed_symbols=frozenset({symbol}),
            receive_time_us=now_us,
            processing_time_us=now_us,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )

    try:
        with PAPER_LOCK:
            return {"data": _paper_refresh(PAPER_STORE, session_id, fetch=_fetch, now_us=time.time_ns() // 1000, time_unit=BinanceTimeUnit.MILLISECONDS)}
    except BinancePublicTransportError as exc:
        return JSONResponse(status_code=502, content=_error(str(exc), fields={"market": str(exc)}))
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"market": str(exc)}))


@app.post("/api/templates/import")
async def import_template(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_template_import_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with TEMPLATE_LOCK:
            return {"data": _template_import(TEMPLATE_STORE, validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"template": str(exc)}))


@app.get("/api/templates")
async def list_templates():
    try:
        with TEMPLATE_LOCK:
            items = [_template_meta(TEMPLATE_STORE, tid) for tid in TEMPLATE_STORE.list_ids()]
        return {"data": items}
    except (OSError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"template": str(exc)}))


@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    try:
        with TEMPLATE_LOCK:
            template = TEMPLATE_STORE.load(template_id)
        return {"data": {
            "template_id": template.template_id,
            "payload_sha256": template.payload_sha256,
            "declared_capabilities": list(template.declared_capabilities),
            "payload": json.loads(template.payload_json),
        }}
    except (OSError, ValueError) as exc:
        status = 404 if "TEMPLATE_NOT_FOUND" in str(exc) else 422
        return JSONResponse(status_code=status, content=_error(str(exc), fields={"template": str(exc)}))


@app.get("/api/templates/{template_id}/export")
async def export_template(template_id: str):
    try:
        with TEMPLATE_LOCK:
            raw = TEMPLATE_STORE.export_bytes(template_id)
        return {"data": json.loads(raw.decode("utf-8"))}
    except (OSError, ValueError) as exc:
        status = 404 if "TEMPLATE_NOT_FOUND" in str(exc) else 422
        return JSONResponse(status_code=status, content=_error(str(exc), fields={"template": str(exc)}))


@app.post("/api/templates/{template_id}/bind")
async def bind_template(template_id: str, request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_template_bind_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with TEMPLATE_LOCK:
            return {"data": _template_bind(TEMPLATE_STORE, template_id, validated, time.time_ns() // 1000)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"binding": str(exc)}))


@app.post("/api/templates/diff")
async def diff_template_pair(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_template_diff_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with TEMPLATE_LOCK:
            return {"data": _template_diff(TEMPLATE_STORE, validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"diff": str(exc)}))


@app.post("/api/rebalance/plan")
async def create_rebalance_plan(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_rebalance_plan_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _rebalance_plan(validated, time.time_ns() // 1000)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"plan": str(exc)}))


@app.post("/api/rebalance/disclose")
async def disclose_rebalance_plan(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_rebalance_disclose_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _rebalance_disclose(validated, time.time_ns() // 1000)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"disclosure": str(exc)}))


@app.post("/api/signals/hash")
async def hash_signal(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_signal_hash_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _signal_hash(validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"hash": str(exc)}))


@app.post("/api/signals/assess")
async def assess_signal(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_signal_assess_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _signal_assess(validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"readiness": str(exc)}))


@app.post("/api/signals/candidates")
async def bind_signal(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_signal_candidate_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _signal_bind_candidate(validated, time.time_ns() // 1000)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"candidate": str(exc)}))


@app.post("/api/futures/grid/levels")
async def project_grid_levels(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_futures_grid_levels_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _futures_grid_levels(validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"grid": str(exc)}))


@app.post("/api/futures/position/pnl")
async def project_position_pnl(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_futures_position_pnl_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _futures_position_pnl(validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"pnl": str(exc)}))


@app.post("/api/futures/trailing/arm")
async def arm_trailing(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_futures_trailing_arm_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _futures_trailing_arm(validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"trailing": str(exc)}))


@app.post("/api/futures/trailing/observe")
async def observe_trailing(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_futures_trailing_observe_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _futures_trailing_observe(validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"trailing": str(exc)}))


@app.post("/api/futures/funding")
async def project_funding_event(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_futures_funding_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _futures_funding(validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"funding": str(exc)}))


@app.post("/api/two-leg/sessions")
async def start_two_leg_session(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_two_leg_session_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with TWO_LEG_LOCK:
            return {"data": _two_leg_start(_get_two_leg_journal(), validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"session": str(exc)}))


@app.post("/api/two-leg/sessions/{session_id}/fills")
async def accept_two_leg_session_fill(session_id: str, request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_two_leg_fill_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with TWO_LEG_LOCK:
            return {"data": _two_leg_accept_fill(_get_two_leg_journal(), session_id, validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"fill": str(exc)}))


@app.post("/api/two-leg/sessions/{session_id}/recovery")
async def mark_two_leg_session_recovery(session_id: str, request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    if payload != {}:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields={"body": "Gövde boş nesne olmalıdır."}))
    try:
        with TWO_LEG_LOCK:
            return {"data": _two_leg_mark(_get_two_leg_journal(), session_id, "RECOVERY_REQUIRED")}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"recovery": str(exc)}))


@app.post("/api/two-leg/sessions/{session_id}/timeout")
async def mark_two_leg_session_timeout(session_id: str, request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    if payload != {}:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields={"body": "Gövde boş nesne olmalıdır."}))
    try:
        with TWO_LEG_LOCK:
            return {"data": _two_leg_mark(_get_two_leg_journal(), session_id, "TIMEOUT")}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"timeout": str(exc)}))


@app.post("/api/two-leg/sessions/{session_id}/replay")
async def replay_two_leg_session(session_id: str, request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    if payload != {}:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields={"body": "Gövde boş nesne olmalıdır."}))
    try:
        with TWO_LEG_LOCK:
            return {"data": _two_leg_replay(_get_two_leg_journal(), session_id)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"replay": str(exc)}))


@app.post("/api/bots")
async def register_bot(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_bot_register_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with BOT_LOCK:
            data = _bot_register(BOT_REGISTRY, validated)
            with EVENT_LOCK:
                _record_event(
                    EVENT_LOG, "BOT_REGISTERED", str(data["bot_id"]),
                    f"Bot kaydedildi ({data['result']}).",
                    time.time_ns() // 1000,
                )
            return {"data": data}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"bot": str(exc)}))


@app.get("/api/bots")
async def list_bots():
    with BOT_LOCK:
        return {"data": _bot_list(BOT_REGISTRY)}


@app.get("/api/bots/{bot_id}")
async def get_bot(bot_id: str):
    try:
        with BOT_LOCK:
            return {"data": _bot_get(BOT_REGISTRY, bot_id)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"bot": str(exc)}))


@app.post("/api/bots/{bot_id}/lists")
async def update_bot_lists(bot_id: str, request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_bot_lists_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with BOT_LOCK:
            return {"data": _bot_update_lists(BOT_REGISTRY, bot_id, validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"lists": str(exc)}))


@app.post("/api/bots/{bot_id}/sessions")
async def bind_bot_session(bot_id: str, request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_bot_bind_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with BOT_LOCK:
            data = _bot_bind_session(BOT_REGISTRY, bot_id, validated)
            with EVENT_LOCK:
                _record_event(
                    EVENT_LOG, "BOT_BOUND", str(data["session_id"]),
                    f"Session {data['bot_id']} botuna bağlandı ({data['result']}).",
                    time.time_ns() // 1000,
                )
            return {"data": data}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"session": str(exc)}))


@app.post("/api/bots/{bot_id}/check")
async def check_bot_pair(bot_id: str, request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_bot_check_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with BOT_LOCK:
            return {"data": _bot_check_pair(BOT_REGISTRY, bot_id, validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"check": str(exc)}))


@app.post("/api/deals")
async def create_deal(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_deal_create_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with DEAL_LOCK:
            data = _deal_create(DEALS_DIR, validated)
            with EVENT_LOCK:
                _record_event(
                    EVENT_LOG, "DEAL_CREATED", str(data["deal_id"]),
                    f"Deal açıldı ({data['result']}).",
                    time.time_ns() // 1000,
                )
            return {"data": data}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"deal": str(exc)}))


@app.post("/api/deals/bulk")
async def bulk_deal_events(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_deal_bulk_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with DEAL_LOCK:
            return {"data": _deal_bulk(DEALS_DIR, validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"bulk": str(exc)}))


@app.post("/api/deals/{deal_id}/events")
async def append_deal_event(deal_id: str, request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_deal_event_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with DEAL_LOCK:
            data = _deal_append_event(DEALS_DIR, deal_id, validated)
            with EVENT_LOCK:
                _record_event(
                    EVENT_LOG, "DEAL_EVENT", deal_id,
                    f"Deal olayı {validated['event']} ({data['result']}).",
                    time.time_ns() // 1000,
                )
            return {"data": data}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"event": str(exc)}))


@app.post("/api/deals/{deal_id}/replay")
async def replay_deal(deal_id: str, request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    if payload != {}:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields={"body": "Gövde boş nesne olmalıdır."}))
    try:
        with DEAL_LOCK:
            return {"data": _deal_replay(DEALS_DIR, deal_id)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"replay": str(exc)}))


@app.post("/api/exits/trailing")
async def bind_trailing_exit(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_exits_trailing_bind_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _exits_trailing_bind(validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"exit": str(exc)}))


@app.post("/api/exits/trailing/percent-arm")
async def arm_percent_trailing(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_exits_percent_arm_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _exits_percent_arm(validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"trailing": str(exc)}))


@app.post("/api/exits/trailing/percent-observe")
async def observe_percent_trailing(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_exits_percent_observe_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _exits_percent_observe(validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"trailing": str(exc)}))


@app.post("/api/exits/breakeven")
async def assess_breakeven(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_exits_breakeven_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _exits_breakeven(validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"breakeven": str(exc)}))


BACKUP_TAKE_FIELDS = {"store", "deal_id"}
BACKUP_VERIFY_FIELDS = {"backup_file"}
_BACKUP_FILE_RE = re.compile(r"[A-Za-z0-9_.-]{1,80}\.sqlite3\Z", re.ASCII)


def _backup_store_paths() -> dict[str, Path]:
    return {
        "historical_runs": HISTORICAL_RUNS_PATH,
        "two_leg_journal": ROOT / "data" / "two_leg_journal.db",
    }


def _validate_backup_take_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    if not isinstance(payload, dict):
        return None, {"body": "JSON gövdesi nesne olmalıdır."}
    unknown = set(payload) - BACKUP_TAKE_FIELDS
    fields: dict[str, str] = {}
    if unknown:
        fields["body"] = "Bilinmeyen alanlar: " + ", ".join(sorted(unknown))
    if "store" not in payload:
        fields["body"] = (fields.get("body", "") + " Eksik alanlar: store").strip()
    store = payload.get("store")
    if "store" in payload and (not isinstance(store, str) or not store):
        fields["store"] = "store boş olmayan ad olmalıdır."
    if payload.get("store") == "deal" and not isinstance(payload.get("deal_id"), str):
        fields["deal_id"] = "deal backup deal_id gerektirir."
    if fields:
        return None, fields
    return payload, {}


def _validate_backup_verify_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, BACKUP_VERIFY_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    name = body.get("backup_file")
    if not isinstance(name, str) or _BACKUP_FILE_RE.fullmatch(name) is None:
        fields["backup_file"] = "backup_file geçersiz dosya adı."
    if fields:
        return None, fields
    return body, {}


def _backup_take(
    stores: dict[str, Path], dest_dir: Path, validated: dict[str, object], *, now_us: int
) -> dict[str, object]:
    store = validated["store"]
    assert isinstance(store, str)
    if store == "deal":
        deal_id = validated.get("deal_id")
        assert isinstance(deal_id, str)
        source = _deal_path(DEALS_DIR, deal_id)
        label = f"deal-{deal_id}"
    else:
        try:
            source = stores[store]
        except (KeyError, TypeError) as exc:
            raise StoreBackupError("BACKUP_STORE_UNKNOWN", "Store kayıtlı değil.") from exc
        label = store
    manifest = backup_sqlite_file(source, dest_dir, store=label, now_us=now_us)
    return {"manifest": manifest}


def _backup_verify(dest_dir: Path, validated: dict[str, object]) -> dict[str, object]:
    name = validated["backup_file"]
    assert isinstance(name, str)
    manifest_path = dest_dir / (name[: -len(".sqlite3")] + ".manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StoreBackupError(
            "BACKUP_MANIFEST_MISSING", "Backup manifesti bulunamadı."
        ) from exc
    if not isinstance(manifest, dict):
        raise StoreBackupError("BACKUP_MANIFEST_MISSING", "Backup manifesti geçersiz.")
    result = verify_backup(dest_dir / name, manifest)
    return {"backup_file": name, **result}


def _backup_list(dest_dir: Path) -> dict[str, object]:
    return {"backups": list_backup_manifests(dest_dir)}


@app.post("/api/admin/backup")
async def take_backup(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_backup_take_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with BACKUP_LOCK:
            data = _backup_take(
                _backup_store_paths(), BACKUPS_DIR, validated,
                now_us=time.time_ns() // 1000,
            )
            manifest = data["manifest"]
            assert isinstance(manifest, dict)
            with EVENT_LOCK:
                _record_event(
                    EVENT_LOG, "BACKUP_TAKEN", str(manifest["backup_file"]),
                    f"Backup alındı ({manifest['store']}, {manifest['bytes']} B).",
                    time.time_ns() // 1000,
                )
            return {"data": data}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"backup": str(exc)}))


@app.post("/api/admin/backup/verify")
async def verify_backup_file(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_backup_verify_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with BACKUP_LOCK:
            data = _backup_verify(BACKUPS_DIR, validated)
            with EVENT_LOCK:
                _record_event(
                    EVENT_LOG, "BACKUP_VERIFIED", str(data["backup_file"]),
                    f"Backup doğrulandı: {data['verdict']}.",
                    time.time_ns() // 1000,
                )
            return {"data": data}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"verify": str(exc)}))


@app.get("/api/admin/backups")
async def list_backups():
    with BACKUP_LOCK:
        return {"data": _backup_list(BACKUPS_DIR)}


def _dashboard_data(
    paper_store: dict[str, object],
    bot_registry: BotRegistry,
    deals_dir: Path,
    backups_dir: Path,
) -> dict[str, object]:
    sessions = paper_store.get("sessions", {})
    assert isinstance(sessions, dict)
    paper = [
        {
            "session_id": session.session_id,
            "cash": session.cash,
            "positions": [{"symbol": p.symbol, "qty": p.qty} for p in session.positions],
            "orders": [{"status": o.status} for o in session.orders],
        }
        for session in sessions.values()
    ]
    bots = [
        {"bot_id": bot_id, "sessions": bot_registry.sessions_of(bot_id)}
        for bot_id in bot_registry.list_ids()
    ]
    deals: list[dict[str, object]] = []
    if deals_dir.is_dir():
        for path in sorted(deals_dir.glob("*.sqlite3"))[:32]:
            deal_id = path.name[: -len(".sqlite3")]
            try:
                with LifecycleStore.open(path) as store:
                    replay = store.load()
            except ValueError:
                deals.append({"deal_id": deal_id, "status": "UNREADABLE"})
                continue
            lifecycle = replay.lifecycle
            deals.append({
                "deal_id": deal_id,
                "status": lifecycle.status if lifecycle is not None else "EMPTY",
            })
    backups = [
        {"backup_file": manifest["backup_file"]}
        for manifest in list_backup_manifests(backups_dir)
    ]
    return build_dashboard(paper=paper, bots=bots, deals=deals, backups=backups)


@app.get("/api/dashboard")
async def get_dashboard():
    with PAPER_LOCK:
        with BOT_LOCK:
            with DEAL_LOCK:
                with BACKUP_LOCK:
                    return {"data": _dashboard_data(
                        PAPER_STORE, BOT_REGISTRY, DEALS_DIR, BACKUPS_DIR
                    )}


def _deal_timeline(deals_dir: Path, deal_id: str, step: int) -> dict[str, object]:
    if type(step) is not int or step < 0:
        raise LifecycleStoreError("DEAL_STEP_INVALID", "Timeline adımı negatif olamaz.")
    path = _deal_path(deals_dir, deal_id)
    if not path.exists():
        raise LifecycleStoreError("DEAL_UNKNOWN", "Deal kayıtlı değil.")
    with LifecycleStore.open(path) as store:
        replay = store.load()
    history = list(replay.history)
    if step > len(history):
        raise LifecycleStoreError(
            "DEAL_STEP_INVALID", "Timeline adımı geçmişi aşıyor."
        )
    lifecycle = new_deal_lifecycle(
        deal_id,
        history[0].config_revision_id if history else "unstarted",
    )
    prefix: tuple[LifecycleEvent, ...] = ()
    for event in history[:step]:
        lifecycle, prefix, _ = apply_lifecycle_event(lifecycle, prefix, event)
    current = history[step - 1] if step > 0 else None
    return {
        "deal_id": deal_id,
        "step": step,
        "of": len(history),
        "lifecycle": _deal_lifecycle_data(lifecycle),
        "event": _deal_event_data(current) if current is not None else None,
    }


@app.get("/api/deals/{deal_id}/timeline")
async def get_deal_timeline(deal_id: str, step: int = 0):
    try:
        with DEAL_LOCK:
            return {"data": _deal_timeline(DEALS_DIR, deal_id, step)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"timeline": str(exc)}))


RECURRING_SCHEDULE_FIELDS = {
    "symbol", "quote_amount", "start_us", "interval_us", "count",
}


def _validate_recurring_schedule_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    body, fields = _template_field_errors(payload, RECURRING_SCHEDULE_FIELDS)
    if body is None or fields:
        return None, fields
    assert isinstance(body, dict)
    if not isinstance(body.get("symbol"), str):
        fields["symbol"] = "symbol string olmalıdır."
    if not isinstance(body.get("quote_amount"), str):
        fields["quote_amount"] = "quote_amount string olmalıdır."
    for name in ("start_us", "interval_us"):
        if type(body.get(name)) is not int:
            fields[name] = f"{name} integer olmalıdır."
    count = body.get("count")
    if type(count) is not int or not 1 <= count <= 365:
        fields["count"] = "count 1-365 arası integer olmalıdır."
    if fields:
        return None, fields
    return body, {}


def _recurring_schedule(validated: dict[str, object]) -> dict[str, object]:
    return project_recurring_schedule(
        symbol=validated["symbol"],  # type: ignore[arg-type]
        quote_amount=validated["quote_amount"],  # type: ignore[arg-type]
        start_us=validated["start_us"],  # type: ignore[arg-type]
        interval_us=validated["interval_us"],  # type: ignore[arg-type]
        count=validated["count"],  # type: ignore[arg-type]
    )


@app.post("/api/recurring/schedule")
async def project_recurring(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_recurring_schedule_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        return {"data": _recurring_schedule(validated)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"schedule": str(exc)}))


def _record_event(log: EventLog, kind: str, ref: str, summary: str, time_us: int) -> None:
    log.append(kind=kind, ref=ref, summary=summary, time_us=time_us)


def _events_list(log: EventLog, limit: int) -> dict[str, object]:
    return {"events": log.list(limit=limit)}


@app.get("/api/events")
async def list_events(limit: int = 50):
    try:
        with EVENT_LOCK:
            return {"data": _events_list(EVENT_LOG, limit)}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"events": str(exc)}))


RISK_EXPLAIN_FIELDS = {"session_id", "bot_id", "symbol", "deal_id"}


def _validate_risk_explain_payload(payload: object) -> tuple[dict[str, object] | None, dict[str, str]]:
    if not isinstance(payload, dict):
        return None, {"body": "JSON gövdesi nesne olmalıdır."}
    unknown = set(payload) - RISK_EXPLAIN_FIELDS
    fields: dict[str, str] = {}
    if unknown:
        fields["body"] = "Bilinmeyen alanlar: " + ", ".join(sorted(unknown))
    for name in RISK_EXPLAIN_FIELDS:
        if name in payload and not isinstance(payload[name], str):
            fields[name] = f"{name} string olmalıdır."
    if "symbol" in payload and "bot_id" not in payload:
        fields["bot_id"] = "symbol yalnız bot_id ile değerlendirilir."
    if fields:
        return None, fields
    return payload, {}


def _risk_explain(
    paper_store: dict[str, object],
    bot_registry: BotRegistry,
    deals_dir: Path,
    validated: dict[str, object],
) -> dict[str, object]:
    pair_verdict: tuple[str, str] | None = None
    if isinstance(validated.get("bot_id"), str) and isinstance(validated.get("symbol"), str):
        try:
            verdict, reason = bot_registry.check_pair(
                validated["bot_id"], validated["symbol"]  # type: ignore[arg-type]
            )
            pair_verdict = (verdict, reason)
        except ValueError as exc:
            pair_verdict = ("UNKNOWN", str(exc))
    paper: dict[str, object] | None = None
    paper_requested = isinstance(validated.get("session_id"), str)
    if paper_requested:
        sessions = paper_store.get("sessions", {})
        assert isinstance(sessions, dict)
        session = sessions.get(validated["session_id"])
        if session is not None:
            paper = {"session_id": session.session_id, "cash": session.cash}
    deal: dict[str, object] | None = None
    deal_requested = isinstance(validated.get("deal_id"), str)
    if deal_requested:
        deal_id = validated["deal_id"]
        assert isinstance(deal_id, str)
        try:
            replayed = _deal_replay(deals_dir, deal_id)
        except ValueError:
            replayed = None
        if replayed is not None:
            lifecycle = replayed["lifecycle"]
            assert isinstance(lifecycle, dict) or lifecycle is None
            deal = {
                "deal_id": deal_id,
                "status": lifecycle["status"] if lifecycle else "EMPTY",
            }
    return explain_risk(
        pair_verdict=pair_verdict,
        paper=paper,
        paper_requested=paper_requested,
        deal=deal,
        deal_requested=deal_requested,
    )


@app.post("/api/risk/explain")
async def explain_trade_risk(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content=_error("JSON gövdesi okunamadı."))
    validated, fields = _validate_risk_explain_payload(payload)
    if fields:
        return JSONResponse(status_code=422, content=_error("İstek doğrulanamadı.", fields=fields))
    try:
        with PAPER_LOCK:
            with BOT_LOCK:
                with DEAL_LOCK:
                    return {"data": _risk_explain(
                        PAPER_STORE, BOT_REGISTRY, DEALS_DIR, validated
                    )}
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(status_code=422, content=_error(str(exc), fields={"risk": str(exc)}))


@app.get("/api/settlement")
async def get_settlement_policy():
    return {
        "data": {
            "supported": list(SUPPORTED_SETTLEMENT_ASSETS),
            "policy": "USDT_ONLY",
            "note": "Çoklu settlement zamanlı kur ve envanter modeli ister (F35 DEFERRED).",
        }
    }


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
