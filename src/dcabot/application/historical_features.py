"""Bounded, exact feature and future-label pipeline for closed historical bars."""

from dataclasses import dataclass
import hashlib
import json
import re

from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput
from dcabot.domain.numbers import number


MAX_FEATURE_RUN_BARS = 1_000
MAX_LOOKBACK_BARS = 500
MAX_LABEL_HORIZON_BARS = 500
_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)
_HASH = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_FEATURE_IDS = frozenset(("CLOSE_SMA", "CLOSE_RETURN"))
_LABEL_IDS = frozenset(("FUTURE_CLOSE_RETURN",))


class HistoricalFeatureError(ValueError):
    """Raised when a feature/label binding cannot be proven from closed bars."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FeatureDefinition:
    """One exact feature whose input ends at the feature row's bar."""

    feature_id: str
    lookback_bars: int

    def __post_init__(self) -> None:
        if type(self.feature_id) is not str or self.feature_id not in _FEATURE_IDS:
            raise HistoricalFeatureError("FEATURE_ID_INVALID", "Feature kimliği desteklenmiyor.")
        if type(self.lookback_bars) is not int or not 1 <= self.lookback_bars <= MAX_LOOKBACK_BARS:
            raise HistoricalFeatureError("FEATURE_LOOKBACK_INVALID", "Feature lookback sınırı geçersiz.")


@dataclass(frozen=True, slots=True)
class LabelDefinition:
    """One forward label; its value is never read before its future bar exists."""

    label_id: str
    horizon_bars: int

    def __post_init__(self) -> None:
        if type(self.label_id) is not str or self.label_id not in _LABEL_IDS:
            raise HistoricalFeatureError("LABEL_ID_INVALID", "Label kimliği desteklenmiyor.")
        if type(self.horizon_bars) is not int or not 1 <= self.horizon_bars <= MAX_LABEL_HORIZON_BARS:
            raise HistoricalFeatureError("LABEL_HORIZON_INVALID", "Label future horizon sınırı geçersiz.")


@dataclass(frozen=True, slots=True)
class HistoricalFeaturePipeline:
    """Immutable feature set used only for read-only historical evaluation."""

    pipeline_id: str
    features: tuple[FeatureDefinition, ...]
    label: LabelDefinition

    def __post_init__(self) -> None:
        if type(self.pipeline_id) is not str or _IDENTIFIER.fullmatch(self.pipeline_id) is None:
            raise HistoricalFeatureError("FEATURE_PIPELINE_ID_INVALID", "Feature pipeline kimliği geçersiz.")
        if type(self.features) is not tuple or not self.features:
            raise HistoricalFeatureError("FEATURE_PIPELINE_EMPTY", "En az bir feature tanımlanmalıdır.")
        if not all(type(feature) is FeatureDefinition for feature in self.features):
            raise HistoricalFeatureError("FEATURE_DEFINITION_INVALID", "Feature tanımı geçersiz.")
        if type(self.label) is not LabelDefinition:
            raise HistoricalFeatureError("LABEL_DEFINITION_INVALID", "Label tanımı geçersiz.")
        ids = tuple(feature.feature_id for feature in self.features)
        if len(set(ids)) != len(ids):
            raise HistoricalFeatureError("FEATURE_DUPLICATE", "Feature kimliği tekrar edemez.")

    @property
    def required_lookback_bars(self) -> int:
        return max(feature.lookback_bars for feature in self.features)


@dataclass(frozen=True, slots=True)
class HistoricalFeatureRow:
    """One eligible row with exact features and a strictly future label."""

    bar_index: int
    open_time_us: int
    features: tuple[tuple[str, str], ...]
    label_id: str
    label_value: str


@dataclass(frozen=True, slots=True)
class HistoricalFeatureRunBinding:
    """Dataset/config identity and computed rows bound to a historical runner."""

    dataset_id: str
    artifact_sha256: str
    config_hash: str
    pipeline_id: str
    features: tuple[FeatureDefinition, ...]
    label: LabelDefinition
    required_lookback_bars: int
    warmup_bar_count: int
    label_horizon_bars: int
    first_eligible_bar_index: int
    last_eligible_bar_index: int
    rows: tuple[HistoricalFeatureRow, ...]
    binding_sha256: str


def build_historical_feature_binding(
    dataset: HistoricalDatasetInput,
    pipeline: HistoricalFeaturePipeline,
    *,
    config_hash: str,
) -> HistoricalFeatureRunBinding:
    """Compute a deterministic closed-bar feature/label view for one run."""

    if type(dataset) is not HistoricalDatasetInput:
        raise HistoricalFeatureError("FEATURE_DATASET_INVALID", "Historical dataset tipi geçersiz.")
    if type(pipeline) is not HistoricalFeaturePipeline:
        raise HistoricalFeatureError("FEATURE_PIPELINE_INVALID", "Feature pipeline tipi geçersiz.")
    if type(config_hash) is not str or _HASH.fullmatch(config_hash) is None:
        raise HistoricalFeatureError("FEATURE_CONFIG_HASH_INVALID", "Config hash geçersiz.")
    if not 1 <= len(dataset.bars) <= MAX_FEATURE_RUN_BARS:
        raise HistoricalFeatureError("FEATURE_SCOPE_INVALID", "Feature dataset kapsamı geçersiz.")
    _validate_bars(dataset.bars)
    first_index = pipeline.required_lookback_bars - 1
    last_index = len(dataset.bars) - pipeline.label.horizon_bars - 1
    if first_index > last_index:
        raise HistoricalFeatureError(
            "FEATURE_SCOPE_TOO_SMALL",
            "Dataset lookback ve future label horizon için yeterli bar taşımıyor.",
        )
    rows = tuple(
        _build_row(dataset.bars, pipeline, index)
        for index in range(first_index, last_index + 1)
    )
    payload = {
        "schema_version": 1,
        "dataset_id": dataset.metadata.dataset_id,
        "artifact_sha256": dataset.metadata.artifact_sha256,
        "config_hash": config_hash,
        "pipeline_id": pipeline.pipeline_id,
        "features": [
            {"feature_id": feature.feature_id, "lookback_bars": feature.lookback_bars}
            for feature in pipeline.features
        ],
        "label": {"label_id": pipeline.label.label_id, "horizon_bars": pipeline.label.horizon_bars},
        "rows": [
            {
                "bar_index": row.bar_index,
                "open_time_us": row.open_time_us,
                "features": row.features,
                "label_id": row.label_id,
                "label_value": row.label_value,
            }
            for row in rows
        ],
    }
    binding_sha256 = hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
    return HistoricalFeatureRunBinding(
        dataset_id=dataset.metadata.dataset_id,
        artifact_sha256=dataset.metadata.artifact_sha256,
        config_hash=config_hash,
        pipeline_id=pipeline.pipeline_id,
        features=pipeline.features,
        label=pipeline.label,
        required_lookback_bars=pipeline.required_lookback_bars,
        warmup_bar_count=first_index,
        label_horizon_bars=pipeline.label.horizon_bars,
        first_eligible_bar_index=first_index + 1,
        last_eligible_bar_index=last_index + 1,
        rows=rows,
        binding_sha256=binding_sha256,
    )


def validate_historical_feature_binding(
    dataset: HistoricalDatasetInput,
    binding: HistoricalFeatureRunBinding,
    *,
    config_hash: str,
) -> None:
    """Recompute the binding before a runner or snapshot treats it as authoritative."""

    if type(binding) is not HistoricalFeatureRunBinding:
        raise HistoricalFeatureError("FEATURE_BINDING_INVALID", "Feature run binding tipi geçersiz.")
    expected = build_historical_feature_binding(
        dataset,
        HistoricalFeaturePipeline(binding.pipeline_id, binding.features, binding.label),
        config_hash=config_hash,
    )
    if binding != expected:
        raise HistoricalFeatureError("FEATURE_BINDING_INVALID", "Feature run binding canonical değil.")


def _build_row(bars: tuple[CanonicalBar, ...], pipeline: HistoricalFeaturePipeline, index: int) -> HistoricalFeatureRow:
    current = number(bars[index].close)
    values: list[tuple[str, str]] = []
    for feature in pipeline.features:
        if feature.feature_id == "CLOSE_SMA":
            value = sum((number(bar.close) for bar in bars[index - feature.lookback_bars + 1 : index + 1]), number("0")) / feature.lookback_bars
        elif feature.feature_id == "CLOSE_RETURN":
            previous = number(bars[index - feature.lookback_bars].close)
            value = current / previous - 1
        else:
            raise HistoricalFeatureError("FEATURE_ID_INVALID", "Feature kimliği desteklenmiyor.")
        values.append((feature.feature_id, _ratio_text(value)))
    future = number(bars[index + pipeline.label.horizon_bars].close)
    label_value = _ratio_text(future / current - 1)
    return HistoricalFeatureRow(
        bar_index=index + 1,
        open_time_us=bars[index].open_time_us,
        features=tuple(values),
        label_id=pipeline.label.label_id,
        label_value=label_value,
    )


def _validate_bars(bars: tuple[CanonicalBar, ...]) -> None:
    previous_time: int | None = None
    for bar in bars:
        if type(bar) is not CanonicalBar or not bar.is_closed:
            raise HistoricalFeatureError("FEATURE_BAR_INVALID", "Feature pipeline yalnız kapalı canonical bar kabul eder.")
        if type(bar.open_time_us) is not int or (previous_time is not None and bar.open_time_us <= previous_time):
            raise HistoricalFeatureError("FEATURE_BAR_ORDER_INVALID", "Bar zaman sırası geçersiz.")
        try:
            positive_prices = min(number(bar.open), number(bar.high), number(bar.low), number(bar.close)) > 0
        except ValueError as exc:
            raise HistoricalFeatureError("FEATURE_BAR_INVALID", "Bar fiyatları exact decimal olmalıdır.") from exc
        if not positive_prices:
            raise HistoricalFeatureError("FEATURE_BAR_INVALID", "Bar fiyatları pozitif olmalıdır.")
        previous_time = bar.open_time_us


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _ratio_text(value) -> str:
    """Serialize feature math exactly without routing it through money decimals."""

    if value == 0:
        return "0"
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"
