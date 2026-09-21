"""Faz 14.5: bar-cache'li parametre sweep orkestratörü (reducer korunur)."""
import tempfile
import unittest
from pathlib import Path

from dcabot.application.sweep_orchestrator import (
    SweepError,
    run_parameter_sweep,
    write_sweep_cache,
)
from dcabot.data_adapters.historical import (
    CanonicalBar,
    HistoricalDatasetInput,
    HistoricalDatasetMetadata,
)


def _dataset() -> HistoricalDatasetInput:
    metadata = HistoricalDatasetMetadata(
        dataset_id="sweep-fixture",
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


def _recipes():
    return (
        {"recipe_id": "r1", "overrides": {"take_profit": "0.02"}},
        {"recipe_id": "r2", "overrides": {"take_profit": "0.05"}},
    )


class SweepOrchestratorTests(unittest.TestCase):
    def test_sequential_sweep_runs_reducer_per_recipe(self):
        results = run_parameter_sweep(
            _recipes(), base_config=_base_config(), dataset=_dataset(), max_workers=1
        )
        self.assertEqual([r["recipe_id"] for r in results], ["r1", "r2"])
        for result in results:
            self.assertEqual(result["execution_status"], "COMPLETED")
            self.assertEqual(result["processed_bar_count"], 4)
            self.assertEqual(len(result["config_hash"]), 64)
        self.assertNotEqual(results[0]["config_hash"], results[1]["config_hash"])

    def test_parallel_matches_sequential(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "bars.cache"
            write_sweep_cache(_dataset(), cache)
            parallel = run_parameter_sweep(
                _recipes(), base_config=_base_config(), cache_path=cache, max_workers=2
            )
        sequential = run_parameter_sweep(
            _recipes(), base_config=_base_config(), dataset=_dataset(), max_workers=1
        )
        self.assertEqual(parallel, sequential)

    def test_empty_recipes_return_empty(self):
        self.assertEqual(
            run_parameter_sweep((), base_config=_base_config(), dataset=_dataset(), max_workers=1),
            (),
        )

    def test_bad_recipe_fails_closed_with_identity(self):
        with self.assertRaises(SweepError) as ctx:
            run_parameter_sweep(
                ({"recipe_id": "bad", "overrides": {"take_profit": "zzz"}},),
                base_config=_base_config(),
                dataset=_dataset(),
                max_workers=1,
            )
        self.assertIn("bad", str(ctx.exception))

    def test_parallel_without_cache_path_raises(self):
        with self.assertRaises(SweepError):
            run_parameter_sweep(
                _recipes(), base_config=_base_config(), dataset=_dataset(), max_workers=2
            )

    def test_unknown_override_field_raises(self):
        with self.assertRaises(SweepError):
            run_parameter_sweep(
                ({"recipe_id": "r1", "overrides": {"mode": "live"}},),
                base_config=_base_config(),
                dataset=_dataset(),
                max_workers=1,
            )
