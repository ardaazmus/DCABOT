"""Safe, deterministic capture contract for a future local historical run store."""

from dataclasses import dataclass
import hashlib
import json
import re

from dcabot import __version__
from dcabot.application.historical_simulation import HistoricalSimulationResult
from dcabot.application.historical_features import (
    HistoricalFeatureError,
    HistoricalFeatureRunBinding,
    validate_historical_feature_binding,
)
from dcabot.application.historical_profiles import get_historical_profile
from dcabot.data_adapters.historical import HistoricalDatasetInput
from dcabot.domain.config import Config
from dcabot.domain.numbers import number


RUN_RECORD_SCHEMA_VERSION = 1
INPUT_SNAPSHOT_SCHEMA_VERSION = 1
IDENTITY_SCHEMA_VERSION = 1
MODEL_ID = "historical_ohlcv_v1"
MODEL_VERSION = "1"
SIMULATOR_VERSION = __version__
KERNEL_VERSION = "offline-core-1"
ASSUMPTION_CONTRACT_VERSION = "historical_ohlcv_v1-assumptions-1"
SEED_POLICY = "NOT_APPLICABLE"
MAX_SNAPSHOT_BARS = 1_000
MAX_SNAPSHOT_ACTIONS = 1_000
MAX_ACTION_ROLE_LENGTH = 64
MAX_ACTION_REFERENCE_LENGTH = 50

_CONFIG_FIELDS = frozenset((*Config.__dataclass_fields__, "mode", "schema_version"))
_RISK_FIELDS = (
    "symbol",
    "base_asset",
    "quote_asset",
    "tick",
    "qty_step",
    "min_qty",
    "min_notional",
    "initial_equity",
    "max_entry_notional",
    "leverage",
    "max_drawdown",
    "minimum_equity",
)
_ACTION_ROLE = re.compile(r"(?:BASE|EXIT|SAFETY:[1-9][0-9]*)\Z", re.ASCII)


class HistoricalRunContractError(ValueError):
    """Raised when a terminal simulation cannot become a safe run capture."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class HistoricalRunExecutionIdentity:
    """Runtime identity used to gate a future exact reproduction."""

    identity_sha256: str
    model_id: str
    profile_id: str
    profile_version: str
    venue_filter_provenance: str
    historical_filter_claim: bool
    anchor_source: str
    model_version: str
    simulator_version: str
    kernel_version: str
    instrument_risk_snapshot_sha256: str
    seed_policy: str
    seed: None
    assumption_contract_version: str
    feature_binding_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class HistoricalRunCapture:
    """Canonical immutable strings that a future persistence layer may store."""

    record_schema_version: int
    input_snapshot_json: str
    canonical_input_sha256: str
    config_json: str
    config_hash: str
    instrument_risk_json: str
    instrument_risk_snapshot_sha256: str
    result_json: str
    result_sha256: str
    execution_identity_json: str
    execution: HistoricalRunExecutionIdentity
    evaluation_binding_json: str | None = None
    evaluation_binding_sha256: str | None = None
    evaluation_binding: object | None = None


def build_historical_run_capture(
    dataset: HistoricalDatasetInput,
    raw_config: dict[str, object],
    result: HistoricalSimulationResult,
    *,
    config_hash: str,
    profile_id: str = "paper",
) -> HistoricalRunCapture:
    """Build bounded, secret-free snapshot components without writing or running code."""

    try:
        Config.parse(raw_config)
    except (TypeError, ValueError) as exc:
        raise HistoricalRunContractError("CONFIG_SNAPSHOT_INVALID", "Config snapshot geçersiz.") from exc
    if set(raw_config) != _CONFIG_FIELDS:
        raise HistoricalRunContractError("CONFIG_SNAPSHOT_INVALID", "Config snapshot allowlist ile eşleşmiyor.")
    if result.feature_binding is not None:
        try:
            validate_historical_feature_binding(dataset, result.feature_binding, config_hash=config_hash)
        except HistoricalFeatureError as exc:
            raise HistoricalRunContractError(exc.code, str(exc)) from exc

    config_json = _canonical_json(raw_config)
    calculated_config_hash = _sha256(config_json)
    if calculated_config_hash != config_hash:
        raise HistoricalRunContractError("CONFIG_HASH_MISMATCH", "Config snapshot hash ile eşleşmiyor.")
    try:
        profile = get_historical_profile(profile_id)
    except ValueError as exc:
        raise HistoricalRunContractError("PROFILE_INVALID", "Historical profile snapshot kimliği geçersiz.") from exc

    input_payload = _input_payload(dataset, raw_config)
    input_json = _canonical_json(input_payload)
    canonical_input_sha256 = _sha256(input_json)

    instrument_risk = {name: raw_config[name] for name in _RISK_FIELDS}
    instrument_risk_json = _canonical_json(instrument_risk)
    instrument_risk_sha256 = _sha256(instrument_risk_json)

    result_payload = _result_payload(dataset, raw_config, result)
    result_json = _canonical_json(result_payload)
    result_sha256 = _sha256(result_json)

    identity_payload = {
        "identity_schema_version": IDENTITY_SCHEMA_VERSION,
        "canonical_input_sha256": canonical_input_sha256,
        "artifact_sha256": dataset.metadata.artifact_sha256,
        "config_hash": config_hash,
        "model_id": MODEL_ID,
        "profile_id": profile.profile_id,
        "profile_version": profile.profile_version,
        "venue_filter_provenance": profile.venue_filter_provenance,
        "historical_filter_claim": profile.historical_filter_claim,
        "anchor_source": profile.anchor_source,
        "model_version": MODEL_VERSION,
        "simulator_version": SIMULATOR_VERSION,
        "kernel_version": KERNEL_VERSION,
        "instrument_risk_snapshot_sha256": instrument_risk_sha256,
        "seed_policy": SEED_POLICY,
        "seed": None,
        "assumption_contract_version": ASSUMPTION_CONTRACT_VERSION,
        "feature_binding_sha256": (
            result.feature_binding.binding_sha256 if result.feature_binding is not None else None
        ),
    }
    identity_json = _canonical_json(identity_payload)
    identity = HistoricalRunExecutionIdentity(
        identity_sha256=_sha256(identity_json),
        model_id=MODEL_ID,
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        venue_filter_provenance=profile.venue_filter_provenance,
        historical_filter_claim=profile.historical_filter_claim,
        anchor_source=profile.anchor_source,
        model_version=MODEL_VERSION,
        simulator_version=SIMULATOR_VERSION,
        kernel_version=KERNEL_VERSION,
        instrument_risk_snapshot_sha256=instrument_risk_sha256,
        seed_policy=SEED_POLICY,
        seed=None,
        assumption_contract_version=ASSUMPTION_CONTRACT_VERSION,
        feature_binding_sha256=(result.feature_binding.binding_sha256 if result.feature_binding is not None else None),
    )
    return HistoricalRunCapture(
        record_schema_version=RUN_RECORD_SCHEMA_VERSION,
        input_snapshot_json=input_json,
        canonical_input_sha256=canonical_input_sha256,
        config_json=config_json,
        config_hash=config_hash,
        instrument_risk_json=instrument_risk_json,
        instrument_risk_snapshot_sha256=instrument_risk_sha256,
        result_json=result_json,
        result_sha256=result_sha256,
        execution_identity_json=identity_json,
        execution=identity,
    )


def _input_payload(dataset: HistoricalDatasetInput, raw_config: dict[str, object]) -> dict[str, object]:
    metadata = dataset.metadata
    if not 1 <= len(dataset.bars) <= MAX_SNAPSHOT_BARS:
        raise HistoricalRunContractError("INPUT_SCOPE_INVALID", "Canonical input bar kapsamı geçersiz.")
    if (
        metadata.timestamp_unit != "microseconds"
        or metadata.timezone != "UTC"
        or metadata.symbol != raw_config["symbol"]
        or raw_config["quote_asset"] != "USDT"
    ):
        raise HistoricalRunContractError("INPUT_CONTEXT_INVALID", "Canonical input context geçersiz.")
    bars: list[dict[str, object]] = []
    previous_open: int | None = None
    for bar in dataset.bars:
        if previous_open is not None and bar.open_time_us <= previous_open:
            raise HistoricalRunContractError("INPUT_ORDER_INVALID", "Canonical input sırası geçersiz.")
        previous_open = bar.open_time_us
        for value in (bar.open, bar.high, bar.low, bar.close, bar.base_volume):
            _plain_decimal(value, "INPUT_VALUE_INVALID")
        if type(bar.open_time_us) is not int or type(bar.close_time_us) is not int or type(bar.is_closed) is not bool:
            raise HistoricalRunContractError("INPUT_VALUE_INVALID", "Canonical input alanı geçersiz.")
        bars.append(
            {
                "open_time_us": bar.open_time_us,
                "close_time_us": bar.close_time_us,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "base_volume": bar.base_volume,
                "is_closed": bar.is_closed,
            }
        )
    return {
        "schema_version": INPUT_SNAPSHOT_SCHEMA_VERSION,
        "model": "historical_ohlcv_input_v1",
        "dataset_id": metadata.dataset_id,
        "symbol": metadata.symbol,
        "interval": metadata.interval,
        "period_start": metadata.period_start,
        "period_end": metadata.period_end,
        "monetary_unit": raw_config["quote_asset"],
        "bars": bars,
    }


def _result_payload(
    dataset: HistoricalDatasetInput,
    raw_config: dict[str, object],
    result: HistoricalSimulationResult,
) -> dict[str, object]:
    if result.execution_status not in ("COMPLETED", "INDETERMINATE"):
        raise HistoricalRunContractError("RESULT_STATUS_INVALID", "Terminal result status geçersiz.")
    if not 1 <= result.processed_bar_count <= len(dataset.bars):
        raise HistoricalRunContractError("RESULT_SCOPE_INVALID", "Result bar kapsamı input ile eşleşmiyor.")
    if len(result.actions) > MAX_SNAPSHOT_ACTIONS:
        raise HistoricalRunContractError("ACTION_SCOPE_EXCEEDED", "Result action kapsamı sınırı aşıyor.")
    actions: list[dict[str, object]] = []
    seen_bars: set[int] = set()
    for action in result.actions:
        if action.bar_index in seen_bars or not 1 <= action.bar_index <= len(dataset.bars):
            raise HistoricalRunContractError("ACTION_JOIN_INVALID", "Action bar eşleşmesi geçersiz.")
        if dataset.bars[action.bar_index - 1].open_time_us != action.open_time_us:
            raise HistoricalRunContractError("ACTION_JOIN_INVALID", "Action timestamp eşleşmesi geçersiz.")
        seen_bars.add(action.bar_index)
        if (
            not isinstance(action.role, str)
            or len(action.role) > MAX_ACTION_ROLE_LENGTH
            or _ACTION_ROLE.fullmatch(action.role) is None
        ):
            raise HistoricalRunContractError("ACTION_ROLE_INVALID", "Action role güvenli sözleşmeyle eşleşmiyor.")
        _plain_decimal(action.raw_reference, "ACTION_REFERENCE_UNSAFE")
        for value in (action.fill_price, action.quantity, action.fee):
            _plain_decimal(value, "ACTION_VALUE_INVALID")
        actions.append(
            {
                "bar_index": action.bar_index,
                "open_time_us": action.open_time_us,
                "role": action.role,
                "raw_reference": action.raw_reference,
                "fill_price": action.fill_price,
                "quantity": action.quantity,
                "fee": action.fee,
            }
        )

    summary = result.summary
    numeric_summary_fields = (
        "qty",
        "cost",
        "realized_gross",
        "fees",
        "funding",
        "realized_net_after_all_costs",
        "equity",
        "entry_notional",
    )
    for name in numeric_summary_fields:
        _plain_decimal(summary.get(name), "RESULT_VALUE_INVALID")
    for name in ("unrealized", "anchor", "take_profit_price"):
        if summary.get(name) is not None:
            _plain_decimal(summary[name], "RESULT_VALUE_INVALID")
    if summary.get("symbol") != dataset.metadata.symbol or raw_config["quote_asset"] != "USDT":
        raise HistoricalRunContractError("RESULT_CONTEXT_INVALID", "Result para birimi veya sembol context’i geçersiz.")
    safe_summary = {name: summary[name] for name in (*numeric_summary_fields, "unrealized", "anchor", "take_profit_price")}
    safe_summary.update(
        {
            "symbol": summary["symbol"],
            "monetary_unit": raw_config["quote_asset"],
            "position_status": result.position_status,
            "funding_status": result.funding_status,
            "mark_status": result.mark_status,
        }
    )
    return {
        "schema_version": RUN_RECORD_SCHEMA_VERSION,
        "execution_status": result.execution_status,
        "application_code": result.application_code,
        "persisted": False,
        "processed_bar_count": result.processed_bar_count,
        "first_ambiguous_bar_index": result.first_ambiguous_bar_index,
        "assumptions": {
            "model": MODEL_ID,
            "bar_visibility": "CLOSED_ONLY",
            "intrabar_path": "NOT_INFERRED",
            "max_actions_per_bar": 1,
            "fee_model": "CONFIGURED_RATE_ON_EACH_FILL",
            "slippage_model": "CONFIGURED_DETERMINISTIC_ON_EACH_FILL",
            "funding": "NOT_MODELED",
            "exchange_mark": "NOT_AVAILABLE",
            "force_close_at_end": False,
        },
        "actions": actions,
        "summary": safe_summary,
        "ambiguity": (
            {"bar_index": result.first_ambiguous_bar_index, "code": result.application_code}
            if result.first_ambiguous_bar_index is not None
            else None
        ),
        "feature_binding": _feature_binding_payload(result.feature_binding),
    }


def _feature_binding_payload(binding: HistoricalFeatureRunBinding | None) -> dict[str, object] | None:
    if binding is None:
        return None
    return {
        "binding_sha256": binding.binding_sha256,
        "pipeline_id": binding.pipeline_id,
        "required_lookback_bars": binding.required_lookback_bars,
        "warmup_bar_count": binding.warmup_bar_count,
        "label_horizon_bars": binding.label_horizon_bars,
        "first_eligible_bar_index": binding.first_eligible_bar_index,
        "last_eligible_bar_index": binding.last_eligible_bar_index,
        "row_count": len(binding.rows),
    }


def _plain_decimal(value: object, code: str) -> None:
    if not isinstance(value, str) or len(value) > MAX_ACTION_REFERENCE_LENGTH:
        raise HistoricalRunContractError(code, "Persist edilen finansal alan güvenli ondalık sözleşmesinde değil.")
    try:
        number(value)
    except ValueError as exc:
        raise HistoricalRunContractError(code, "Persist edilen finansal alan güvenli ondalık sözleşmesinde değil.") from exc


def _canonical_json(value: object) -> str:
    _reject_float(value)
    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise HistoricalRunContractError("SNAPSHOT_SERIALIZATION_INVALID", "Snapshot canonical JSON üretilemedi.") from exc


def canonical_json(value: object) -> str:
    """Return the canonical JSON profile shared by capture and persistence."""

    return _canonical_json(value)


def _reject_float(value: object) -> None:
    if isinstance(value, float):
        raise HistoricalRunContractError("SNAPSHOT_FLOAT_FORBIDDEN", "Snapshot içinde float alanı bulunamaz.")
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise HistoricalRunContractError("SNAPSHOT_KEY_INVALID", "Snapshot anahtarları string olmalıdır.")
        for nested in value.values():
            _reject_float(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _reject_float(nested)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
