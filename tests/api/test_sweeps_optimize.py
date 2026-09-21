"""Faz 15.7: Optimize endpoint validasyonu + hesap (HTTP'siz)."""
import unittest

from dcabot.data_adapters.historical import (
    CanonicalBar,
    HistoricalDatasetInput,
    HistoricalDatasetMetadata,
)
from dcabot.server.api import (
    _sweep_optimize_compute,
    _validate_sweep_optimize_payload,
)


SPACE = {
    "take_profit": {"kind": "categorical", "choices": ["0.01", "0.05"]},
    "deviation": {"kind": "categorical", "choices": ["0.05", "0.2"]},
}

BASE_CONFIG = {
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


def make_dataset() -> HistoricalDatasetInput:
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


class SweepOptimizeApiTests(unittest.TestCase):
    def test_validate_ok_with_defaults(self):
        validated, fields = _validate_sweep_optimize_payload(
            {
                "dataset_id": "d1",
                "profile_id": "p1",
                "space": SPACE,
                "max_trials": 4,
            }
        )
        self.assertEqual(fields, {})
        assert validated is not None
        self.assertEqual(validated["sampler"], "grid")
        self.assertEqual(validated["seed"], 0)

    def test_validate_rejects_bad_fields(self):
        validated, fields = _validate_sweep_optimize_payload(
            {"dataset_id": "d1", "profile_id": "p1", "space": SPACE, "max_trials": 0}
        )
        self.assertIsNone(validated)
        self.assertIn("max_trials", fields)
        validated, fields = _validate_sweep_optimize_payload(
                {
                    "dataset_id": "d1",
                    "profile_id": "p1",
                    "space": SPACE,
                    "max_trials": 2,
                    "sampler": "optuna",
                }
        )
        self.assertIsNone(validated)
        self.assertIn("sampler", fields)
        validated, fields = _validate_sweep_optimize_payload(
            {"dataset_id": "d1", "profile_id": "p1", "max_trials": 2}
        )
        self.assertIsNone(validated)
        self.assertIn("body", fields)

    def test_compute_returns_ranked_trials(self):
        validated, fields = _validate_sweep_optimize_payload(
            {
                "dataset_id": "d1",
                "profile_id": "p1",
                "space": SPACE,
                "max_trials": 4,
                "sampler": "grid",
                "seed": 0,
            }
        )
        assert validated is not None
        result = _sweep_optimize_compute(validated, make_dataset(), dict(BASE_CONFIG))
        self.assertEqual(result["trial_count"], 4)
        self.assertIn("best_recipe_id", result)
        self.assertIn("best_overrides", result)
        self.assertIn("best_metric", result)
        self.assertTrue(all("config_hash" in t for t in result["trials"]))
