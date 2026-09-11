"""Application use cases for verified historical dataset selections."""

import hashlib
import json
from dataclasses import dataclass

from dcabot.data_adapters.catalog import PublicDatasetSelection
from dcabot.data_adapters.historical import MAX_BARS, HistoricalDatasetInput, parse_verified_dataset
from dcabot.domain.config import Config
from dcabot.domain.numbers import align, exact_text, number


class HistoricalRunPlanError(ValueError):
    """Raised when a verified dataset cannot bind to the active offline config."""

    def __init__(self, message: str, *, code: str = "DATASET_RUN_PLAN_UNAVAILABLE") -> None:
        super().__init__(message)
        self.code = code


class HistoricalRunValidationError(ValueError):
    """Raised when a client revision assertion does not match current server state."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class HistoricalRunConfig:
    """Exact, read-only config facts prepared for a future historical run."""

    schema_version: int
    config_hash: str
    mode: str
    symbol: str
    base_asset: str
    quote_asset: str
    base_qty: str
    safety_qty: str
    safety_count: int
    deviation: str
    target_mode: str
    fee_rate: str
    slippage: str
    simulation_model: str
    slice_qty: str | None


@dataclass(frozen=True, slots=True)
class HistoricalRunPlan:
    """Immutable dataset/config binding that does not execute or persist a run."""

    dataset: HistoricalDatasetInput
    config: HistoricalRunConfig
    execution_mode: str = "SIMULATED"
    run_status: str = "NOT_STARTED"
    read_only: bool = True


def load_verified_dataset(selection: PublicDatasetSelection) -> HistoricalDatasetInput:
    """Load canonical bars from the catalog-selected verified artifact."""

    return parse_verified_dataset(selection)


def build_historical_run_plan(
    dataset: HistoricalDatasetInput,
    raw_config: dict[str, object],
    *,
    simulation_model: str = "historical_ohlcv_v1",
    slice_qty: str | None = None,
) -> HistoricalRunPlan:
    """Bind one canonical dataset to the active config without running or saving it."""

    try:
        config = Config.parse(raw_config)
    except ValueError as exc:
        raise HistoricalRunPlanError("Aktif offline config doğrulanamadı.", code="CONFIG_CONTEXT_UNAVAILABLE") from exc
    if config.symbol != dataset.metadata.symbol:
        raise HistoricalRunPlanError(
            "Dataset sembolü aktif config sembolüyle eşleşmiyor.",
            code="DATASET_CONFIG_CONFLICT",
        )
    if raw_config.get("mode") != "offline" or raw_config.get("schema_version") != 1:
        raise HistoricalRunPlanError(
            "Yalnız offline config schema 1 koşu planına bağlanabilir.",
            code="OFFLINE_CONFIG_UNAVAILABLE",
        )
    if simulation_model not in ("historical_ohlcv_v1", "historical_ohlcv_partial_fixed_v1"):
        raise HistoricalRunPlanError("Tarihsel simulation modeli desteklenmiyor.", code="UNSUPPORTED_EXECUTION_MODE")
    if simulation_model == "historical_ohlcv_partial_fixed_v1":
        if slice_qty is None:
            raise HistoricalRunPlanError("Fixed slice quantity zorunludur.", code="SLICE_QTY_INVALID")
        try:
            fixed_qty = number(slice_qty)
        except ValueError as exc:
            raise HistoricalRunPlanError("Fixed slice quantity geçersiz.", code="SLICE_QTY_INVALID") from exc
        if fixed_qty <= 0 or align(fixed_qty, config.qty_step, up=False) != fixed_qty:
            raise HistoricalRunPlanError("Fixed slice quantity mevcut quantity grid’inde değil.", code="SLICE_QTY_OFF_GRID")
    elif slice_qty is not None:
        raise HistoricalRunPlanError("Legacy model fixed slice quantity kabul etmez.", code="SLICE_QTY_INVALID")
    config_hash_payload: object = raw_config
    if simulation_model == "historical_ohlcv_partial_fixed_v1":
        config_hash_payload = {
            "config": raw_config,
            "simulation_model": simulation_model,
            "slice_qty": slice_qty,
        }
    config_snapshot = HistoricalRunConfig(
        schema_version=raw_config["schema_version"],
        config_hash=hashlib.sha256(_canonical(config_hash_payload).encode("utf-8")).hexdigest(),
        mode=raw_config["mode"],
        symbol=config.symbol,
        base_asset=config.base_asset,
        quote_asset=config.quote_asset,
        base_qty=exact_text(config.base_qty),
        safety_qty=exact_text(config.safety_qty),
        safety_count=config.safety_count,
        deviation=exact_text(config.deviation),
        target_mode=config.target_mode,
        fee_rate=exact_text(config.fee_rate),
        slippage=exact_text(config.slippage),
        simulation_model=simulation_model,
        slice_qty=slice_qty,
    )
    return HistoricalRunPlan(dataset=dataset, config=config_snapshot)


def validate_historical_run_request(
    dataset: HistoricalDatasetInput,
    plan: HistoricalRunPlan,
    *,
    dataset_id: str,
    artifact_sha256: str,
    config_hash: str,
    execution_mode: str,
    simulation_model: str = "historical_ohlcv_v1",
) -> None:
    """Validate client revision assertions without executing or persisting a run."""

    if dataset_id != dataset.metadata.dataset_id:
        raise HistoricalRunValidationError("DATASET_NOT_FOUND", "Dataset doğrulama bağlamıyla eşleşmiyor.")
    if artifact_sha256 != dataset.metadata.artifact_sha256:
        raise HistoricalRunValidationError(
            "ARTIFACT_REVISION_CONFLICT",
            "Dataset artifact sürümü değişti.",
        )
    if config_hash != plan.config.config_hash:
        raise HistoricalRunValidationError(
            "CONFIG_REVISION_CONFLICT",
            "Aktif config sürümü değişti.",
        )
    if execution_mode not in ("SIMULATED", "historical_ohlcv_v1", "historical_ohlcv_partial_fixed_v1"):
        raise HistoricalRunValidationError(
            "UNSUPPORTED_EXECUTION_MODE",
            "Bu doğrulama yalnız desteklenen offline historical modlarını destekler.",
        )
    if simulation_model != plan.config.simulation_model:
        raise HistoricalRunValidationError("EXECUTION_MODE_CONFLICT", "İstenen historical model seçili profile ile eşleşmiyor.")
    if plan.execution_mode != "SIMULATED" or plan.config.mode != "offline" or not plan.read_only:
        raise HistoricalRunValidationError(
            "OFFLINE_VALIDATION_UNAVAILABLE",
            "Salt okunur offline doğrulama bağlamı hazır değil.",
        )
    if len(dataset.bars) > MAX_BARS:
        raise HistoricalRunValidationError(
            "RUN_SCOPE_NOT_ADMISSIBLE",
            "Dataset bar kapsamı server sınırını aşıyor.",
        )


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
