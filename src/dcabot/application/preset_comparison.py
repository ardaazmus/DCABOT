"""Faz 17 B.4-motor: iki preset'i aynı dataset'te çalıştırıp metrikleri
yan yana koyma (qwen 17.10 satır 133 -- "İki preset'i aynı dataset'te
backtest edip metrikleri yan yana koyma").

Yeni ekonomi/motor kodu YOK: bu modül yalnız zaten teslim edilmiş, ayrı ayrı
test edilmiş iki yapı taşını birleştirir -- ``template_materialization.
materialize_binding`` (binding+profile -> doğrulanmış, hash'li Config) ve
``historical_simulation.simulate_historical_ohlcv`` (Config+dataset ->
exact sonuç). İkisi de zaten kabul edilmiş sözleşmeler; burada değiştirilmez.

UI bağlama (template-id/dataset-id seçimi, karşılaştırma ekranı) ayrı bir
muse dilimidir -- bu modül yalnız motor tarafını sağlar.
"""

from dataclasses import dataclass
from pathlib import Path

from dcabot.application.historical_simulation import (
    HistoricalSimulationError,
    HistoricalSimulationResult,
    simulate_historical_ohlcv,
)
from dcabot.application.template_materialization import (
    TemplateMaterializationError,
    materialize_binding,
)
from dcabot.application.template_profile_binding import TemplateBinding
from dcabot.data_adapters.historical import HistoricalDatasetInput
from dcabot.domain.config import Config

DEFAULT_TIMEOUT_SECONDS_EACH = 5.0


class PresetComparisonError(ValueError):
    """Raised when two presets cannot be honestly compared on one dataset."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class PresetComparisonSide:
    """One side's materialized identity plus its exact simulation result."""

    binding_id: str
    profile_id: str
    config_hash: str
    config: Config
    result: HistoricalSimulationResult


@dataclass(frozen=True, slots=True)
class PresetComparisonResult:
    """Both sides run against the identical dataset; no ranking is implied."""

    dataset_id: str
    a: PresetComparisonSide
    b: PresetComparisonSide


def compare_bindings_on_dataset(
    binding_a: TemplateBinding,
    binding_b: TemplateBinding,
    dataset: HistoricalDatasetInput,
    root: Path,
    *,
    timeout_seconds_each: float = DEFAULT_TIMEOUT_SECONDS_EACH,
) -> PresetComparisonResult:
    """Materialize two bindings and simulate each on the same dataset."""

    if not isinstance(binding_a, TemplateBinding) or not isinstance(binding_b, TemplateBinding):
        raise PresetComparisonError(
            "PRESET_COMPARE_BINDING_INVALID", "İki geçerli binding gerekir."
        )
    if binding_a.binding_id == binding_b.binding_id:
        raise PresetComparisonError(
            "PRESET_COMPARE_SAME_BINDING", "Karşılaştırma için iki farklı binding gerekir."
        )
    side_a = _run_side(binding_a, dataset, root, timeout_seconds_each)
    side_b = _run_side(binding_b, dataset, root, timeout_seconds_each)
    return PresetComparisonResult(
        dataset_id=dataset.metadata.dataset_id, a=side_a, b=side_b
    )


def _run_side(
    binding: TemplateBinding,
    dataset: HistoricalDatasetInput,
    root: Path,
    timeout_seconds: float,
) -> PresetComparisonSide:
    try:
        materialized = materialize_binding(binding, root)
    except TemplateMaterializationError as error:
        raise PresetComparisonError(
            "PRESET_COMPARE_MATERIALIZE_FAILED",
            f"{binding.binding_id}: {error}",
        ) from error
    config = Config.parse(materialized.config)
    try:
        result = simulate_historical_ohlcv(
            dataset,
            config,
            config_hash=materialized.config_hash,
            timeout_seconds=timeout_seconds,
        )
    except HistoricalSimulationError as error:
        raise PresetComparisonError(
            "PRESET_COMPARE_SIMULATE_FAILED",
            f"{binding.binding_id}: {error}",
        ) from error
    return PresetComparisonSide(
        binding_id=binding.binding_id,
        profile_id=materialized.profile_id,
        config_hash=materialized.config_hash,
        config=config,
        result=result,
    )
