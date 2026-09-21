"""Faz 15.7: sampler + sweep tek çağrıda (Optimize)."""
import unittest
from fractions import Fraction

from dcabot.application.sweep_optimize import (
    SweepOptimizeError,
    optimize_parameters,
)
from dcabot.application.sweep_orchestrator import SweepError
from dcabot.application.trial_sampler import TrialSamplerError
from dcabot.data_adapters.historical import (
    CanonicalBar,
    HistoricalDatasetInput,
    HistoricalDatasetMetadata,
)


def _dataset() -> HistoricalDatasetInput:
    metadata = HistoricalDatasetMetadata(
        dataset_id="optimize-fixture",
        source_id="fixture",
        symbol="BTCUSDT",
        interval="1h",
        period_start="2024-01-01",
        period_end="2024-01-02",
        artifact_sha256="f" * 64,
        artifact_bytes=64,
        timestamp_unit="microseconds",
        timezone="UTC",
    )
    bars = tuple(
        CanonicalBar(
            open_time_us=i * 3_600_000_000,
            close_time_us=(i + 1) * 3_600_000_000 - 1,
            open="100.00",
            high="101.00",
            low="99.00",
            close="100.50",
            base_volume="1",
            is_closed=True,
        )
        for i in range(4)
    )
    return HistoricalDatasetInput(metadata=metadata, bars=bars)


def _base_config() -> dict:
    return {
        "schema_version": 1,
        "mode": "offline",
        "symbol": "BTCUSDT",
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "base_qty": "0.001",
        "safety_qty": "0.002",
        "safety_count": 2,
        "deviation": "0.1",
        "step_multiplier": "1",
        "volume_multiplier": "1",
        "tick": "0.01",
        "qty_step": "0.001",
        "min_qty": "0.001",
        "min_notional": "0.01",
        "initial_equity": "1000",
        "max_entry_notional": "1000",
        "leverage": "1",
        "max_drawdown": "0.25",
        "minimum_equity": "100",
        "take_profit": "0.02",
        "target_mode": "GROSS_PRICE_RETURN",
        "target_quote": "5",
        "fee_rate": "0.001",
        "fee_quantum": "0.00000001",
        "slippage": "0",
    }


SPACE = {
    "take_profit": {"kind": "categorical", "choices": ["0.01", "0.05"]},
    "deviation": {"kind": "categorical", "choices": ["0.05", "0.2"]},
}


class OptimizeTests(unittest.TestCase):
    def test_best_is_max_net_and_overrides_echoed(self):
        result = optimize_parameters(
            _dataset(), _base_config(), space=SPACE, max_trials=4, seed=0, sampler="grid"
        )
        self.assertEqual(result["trial_count"], 4)
        self.assertEqual(result["skipped_count"], 0)
        metrics = [Fraction(t["realized_net_after_all_costs"]) for t in result["trials"]]
        self.assertEqual(Fraction(result["best_metric"]), max(metrics))
        best = next(t for t in result["trials"] if t["recipe_id"] == result["best_recipe_id"])
        self.assertEqual(result["best_overrides"], best["overrides"])
        self.assertEqual(set(best["overrides"]), {"take_profit", "deviation"})

    def test_mixed_space_runs_valid_and_skips_invalid(self):
        space = {"deviation": {"kind": "categorical", "choices": ["0.1", "1.5"]}}
        result = optimize_parameters(
            _dataset(), _base_config(), space=space, max_trials=2, seed=0, sampler="grid"
        )
        self.assertEqual(result["trial_count"], 1)
        self.assertEqual(result["skipped_count"], 1)
        self.assertEqual(result["skipped"][0]["overrides"], {"deviation": "1.5"})
        self.assertEqual(result["skipped"][0]["code"], "SWEEP_TASK_FAILED")
        self.assertIn("best_recipe_id", result)

    def test_duplicate_suggestions_run_once(self):
        single = {"take_profit": {"kind": "categorical", "choices": ["0.02"]}}
        result = optimize_parameters(
            _dataset(), _base_config(), space=single, max_trials=3, seed=0, sampler="grid"
        )
        self.assertEqual(result["suggested_count"], 3)
        self.assertEqual(result["trial_count"], 1)

    def test_float_values_become_repr_exact_text(self):
        space = {"deviation": {"kind": "float", "low": 0.01, "high": 0.05}}
        result = optimize_parameters(
            _dataset(), _base_config(), space=space, max_trials=2, seed=0, sampler="random"
        )
        for trial in result["trials"]:
            self.assertIsInstance(trial["overrides"]["deviation"], str)
            self.assertEqual(Fraction(trial["overrides"]["deviation"]), Fraction(trial["overrides"]["deviation"]))

    def test_bad_sampler_and_bounds_raise(self):
        with self.assertRaises(TrialSamplerError):
            optimize_parameters(_dataset(), _base_config(), space=SPACE, max_trials=2, seed=0, sampler="optuna-x")
        with self.assertRaises(SweepOptimizeError):
            optimize_parameters(_dataset(), _base_config(), space=SPACE, max_trials=0, seed=0, sampler="grid")
        with self.assertRaises(SweepOptimizeError):
            optimize_parameters(_dataset(), _base_config(), space=SPACE, max_trials=33, seed=0, sampler="grid")
        with self.assertRaises(SweepOptimizeError):
            optimize_parameters(_dataset(), _base_config(), space=SPACE, max_trials=2, seed=True, sampler="grid")

    def test_non_sweepable_param_raises(self):
        with self.assertRaises(SweepError):
            optimize_parameters(
                _dataset(), _base_config(),
                space={"tick": {"kind": "categorical", "choices": ["0.01"]}},
                max_trials=1, seed=0, sampler="grid",
            )


if __name__ == "__main__":
    unittest.main()
