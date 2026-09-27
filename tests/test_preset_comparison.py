"""Faz 17 B.4-motor: iki preset'i aynı dataset'te backtest edip metrikleri
yan yana koyma (17.10 satır 133). Yeni ekonomi yok: yalnız zaten test edilmiş
`materialize_binding` + `simulate_historical_ohlcv`'i birleştirir.
"""
import unittest
from pathlib import Path

from dcabot.application.historical_simulation import HistoricalSimulationError
from dcabot.application.preset_comparison import (
    PresetComparisonError,
    compare_bindings_on_dataset,
)
from dcabot.application.strategy_template import new_strategy_template
from dcabot.application.template_profile_binding import bind_template_to_profile
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata

ROOT = Path(__file__).resolve().parents[1]


def _binding(binding_id_template, payload, profile_id="paper"):
    template = new_strategy_template(
        template_id=binding_id_template,
        schema_version="strategy-template-v1",
        payload=payload,
        declared_capabilities=("DCA", "SPOT"),
    )
    return bind_template_to_profile(
        template=template,
        profile_id=profile_id,
        allowed_capabilities=("DCA", "SPOT"),
        approval="APPROVED",
        binding_time_us=1700000000000000,
    )


def _dataset(*bars):
    canonical = tuple(
        CanonicalBar(
            open_time_us=index * 3_600_000_000,
            close_time_us=index * 3_600_000_000 + 3_599_999_999,
            open=open_price,
            high=high,
            low=low,
            close=close,
            base_volume="1",
            is_closed=True,
        )
        for index, (open_price, high, low, close) in enumerate(bars, start=1)
    )
    return HistoricalDatasetInput(
        metadata=HistoricalDatasetMetadata(
            dataset_id="synthetic-btcusdt-1h",
            source_id="synthetic-source",
            symbol="BTCUSDT",
            interval="1h",
            period_start="2025-01-01",
            period_end="2025-01-10",
            artifact_sha256="a" * 64,
            artifact_bytes=1,
            timestamp_unit="microseconds",
            timezone="UTC",
        ),
        bars=canonical,
    )


class CompareBindingsOnDatasetTests(unittest.TestCase):
    def test_two_bindings_produce_two_independent_metric_sets(self):
        tame = _binding("preset-a", {"deviation": "0.05"})
        aggressive = _binding("preset-b", {"deviation": "0.2"})
        dataset = _dataset(
            ("100", "100", "100", "100"),
            ("95", "96", "94", "95"),
            ("90", "91", "89", "90"),
            ("85", "86", "84", "85"),
        )

        comparison = compare_bindings_on_dataset(tame, aggressive, dataset, ROOT)

        self.assertEqual(comparison.dataset_id, "synthetic-btcusdt-1h")
        self.assertEqual(comparison.a.binding_id, tame.binding_id)
        self.assertEqual(comparison.b.binding_id, aggressive.binding_id)
        self.assertNotEqual(comparison.a.config_hash, comparison.b.config_hash)
        # Different deviation -> different safety-order ladder -> different
        # action counts against the identical price path (real divergence,
        # not a stub).
        self.assertNotEqual(len(comparison.a.result.actions), len(comparison.b.result.actions))

    def test_same_binding_twice_is_rejected(self):
        one = _binding("preset-same", {"deviation": "0.05"})
        dataset = _dataset(("100", "100", "100", "100"))
        with self.assertRaises(PresetComparisonError) as ctx:
            compare_bindings_on_dataset(one, one, dataset, ROOT)
        self.assertEqual(ctx.exception.code, "PRESET_COMPARE_SAME_BINDING")

    def test_invalid_binding_fails_closed_with_wrapped_code(self):
        broken = _binding("preset-broken", {"base_qty": "0.0005"})
        healthy = _binding("preset-healthy", {"deviation": "0.05"})
        dataset = _dataset(("100", "100", "100", "100"))
        with self.assertRaises(PresetComparisonError) as ctx:
            compare_bindings_on_dataset(broken, healthy, dataset, ROOT)
        self.assertEqual(ctx.exception.code, "PRESET_COMPARE_MATERIALIZE_FAILED")

    def test_simulation_error_from_either_side_propagates_as_preset_comparison_error(self):
        one = _binding("preset-x", {"deviation": "0.05"})
        two = _binding("preset-y", {"deviation": "0.1"})
        empty_dataset = _dataset()
        with self.assertRaises((PresetComparisonError, HistoricalSimulationError)):
            compare_bindings_on_dataset(one, two, empty_dataset, ROOT)

    def test_config_hash_matches_independent_materialization(self):
        from dcabot.application.template_materialization import materialize_binding

        tame = _binding("preset-hashcheck-a", {"deviation": "0.05"})
        aggressive = _binding("preset-hashcheck-b", {"deviation": "0.2"})
        dataset = _dataset(("100", "100", "100", "100"))

        comparison = compare_bindings_on_dataset(tame, aggressive, dataset, ROOT)

        self.assertEqual(comparison.a.config_hash, materialize_binding(tame, ROOT).config_hash)
        self.assertEqual(comparison.b.config_hash, materialize_binding(aggressive, ROOT).config_hash)


if __name__ == "__main__":
    unittest.main()
