"""Faz 17 AA.7c (WF/MC): overfitting assessment across a parameter sweep --
PBO (Bailey et al. CSCV) + per-trial DSR, wiring three already-tested
modules (sweep_optimize's recipe suggestion, equity_curve_scores' bar
returns, overfitting_probability's PBO/DSR) together. No new statistics."""
import unittest

from dcabot.application.sweep_overfitting import SweepOverfittingError, assess_sweep_overfitting
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata


def _dataset(n: int = 61) -> HistoricalDatasetInput:
    metadata = HistoricalDatasetMetadata(
        dataset_id="overfit-fixture",
        source_id="fixture",
        symbol="BTCUSDT",
        interval="1h",
        period_start="2024-01-01",
        period_end="2024-01-05",
        artifact_sha256="f" * 64,
        artifact_bytes=64,
        timestamp_unit="microseconds",
        timezone="UTC",
    )
    bars = tuple(
        CanonicalBar(
            open_time_us=i * 3_600_000_000,
            close_time_us=(i + 1) * 3_600_000_000 - 1,
            open="100.50",
            high="101.00",
            low="100.00",
            close="100.50",
            base_volume="1",
            is_closed=True,
        )
        for i in range(n)
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
        "margin_mode": "ISOLATED",
    }


SPACE = {
    "take_profit": {"kind": "categorical", "choices": ["0.01", "0.03", "0.05"]},
    "deviation": {"kind": "categorical", "choices": ["0.05", "0.1", "0.2"]},
}


class AssessSweepOverfittingTests(unittest.TestCase):
    def test_succeeded_trials_get_a_pbo_and_a_dsr_each(self):
        result = assess_sweep_overfitting(
            _dataset(), _base_config(), space=SPACE, max_trials=6, seed=0, sampler="grid", block_count=4,
        )
        self.assertGreaterEqual(result["succeeded_count"], 2)
        self.assertIsNotNone(result["pbo"])
        self.assertEqual(len(result["dsr_by_trial"]), result["succeeded_count"])
        for value in result["dsr_by_trial"].values():
            if value is not None:
                float(value)  # plain float-quality text
        self.assertIsNotNone(result["pbo"])
        float(result["pbo"])
        self.assertGreaterEqual(float(result["pbo"]), 0.0)
        self.assertLessEqual(float(result["pbo"]), 1.0)

    def test_odd_block_count_that_does_not_divide_t_is_a_null_pbo_not_a_crash(self):
        result = assess_sweep_overfitting(
            _dataset(59), _base_config(), space=SPACE, max_trials=4, seed=0, sampler="grid", block_count=4,
        )
        # 58 bar returns is not divisible by 4 -> PBO undefined, not fabricated.
        self.assertIsNone(result["pbo"])

    def test_fewer_than_two_succeeded_trials_yields_null_pbo(self):
        space = {"take_profit": {"kind": "categorical", "choices": ["0.01"]}}
        result = assess_sweep_overfitting(
            _dataset(), _base_config(), space=space, max_trials=1, seed=0, sampler="grid", block_count=2,
        )
        self.assertLessEqual(result["succeeded_count"], 1)
        self.assertIsNone(result["pbo"])

    def test_empty_space_raises(self):
        with self.assertRaises(SweepOverfittingError):
            assess_sweep_overfitting(
                _dataset(), _base_config(), space={}, max_trials=4, seed=0, sampler="grid", block_count=2,
            )


if __name__ == "__main__":
    unittest.main()
