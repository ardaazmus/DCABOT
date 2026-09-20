import json
from dataclasses import replace
from pathlib import Path
import unittest

from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.domain.config import Config


def _config() -> Config:
    raw = json.loads(Path("config/paper.json").read_text(encoding="utf-8"))
    return Config.parse(raw)


def _dataset(*bars: tuple[str, str, str, str, str, str]) -> HistoricalDatasetInput:
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
        for index, (open_price, high, low, close, _unused_a, _unused_b) in enumerate(bars, start=1)
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


class HistoricalSimulationTests(unittest.TestCase):
    def test_fixed_slice_requires_an_explicit_positive_quantity_on_the_existing_grid(self):
        from dcabot.application.historical_simulation import (
            HistoricalSimulationError,
            simulate_historical_fixed_slice,
        )

        dataset = _dataset(("100", "100", "100", "100", "", ""))

        with self.assertRaises(HistoricalSimulationError) as zero:
            simulate_historical_fixed_slice(dataset, _config(), slice_qty="0", config_hash="b" * 64)
        self.assertEqual(zero.exception.code, "SLICE_QTY_INVALID")

        with self.assertRaises(HistoricalSimulationError) as off_grid:
            simulate_historical_fixed_slice(
                dataset,
                _config(),
                slice_qty="0.0005",
                config_hash="b" * 64,
            )
        self.assertEqual(off_grid.exception.code, "SLICE_QTY_OFF_GRID")

    def test_fixed_slice_reuses_one_order_across_bars_and_finishes_exact_remainder(self):
        from dcabot.application.historical_simulation import simulate_historical_fixed_slice

        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("99", "100", "99", "99", "", ""),
            ("98", "100", "98", "98", "", ""),
        )

        result = simulate_historical_fixed_slice(
            dataset,
            _config(),
            slice_qty="0.4",
            config_hash="b" * 64,
        )

        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertEqual(result.position_status, "OPEN_AT_END")
        self.assertEqual([action.quantity for action in result.actions], ["0.4", "0.4", "0.2"])
        self.assertEqual({action.order_id for action in result.actions}, {"historical_partial:1:order"})
        self.assertEqual([action.order_status_after for action in result.actions], [
            "PARTIALLY_FILLED",
            "PARTIALLY_FILLED",
            "FILLED",
        ])
        self.assertEqual(
            (result.actions[-1].original_qty, result.actions[-1].cumulative_filled_qty, result.actions[-1].leaves_qty),
            ("1", "1", "0"),
        )
        self.assertEqual(result.summary["qty"], "1")
        self.assertEqual(result.summary["fees"], "0.1")

    def test_fixed_slice_keeps_unfilled_order_open_at_dataset_end_without_synthetic_cancel(self):
        from dcabot.application.historical_simulation import simulate_historical_fixed_slice

        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("101", "102", "101", "101", "", ""),
        )

        result = simulate_historical_fixed_slice(
            dataset,
            _config(),
            slice_qty="0.4",
            config_hash="b" * 64,
        )

        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertEqual(result.position_status, "OPEN_AT_END")
        self.assertEqual(len(result.actions), 1)
        self.assertEqual(result.actions[0].leaves_qty, "0.6")
        self.assertFalse(result.synthetic_cancel_applied)
        self.assertEqual(result.summary["qty"], "0.4")

    def test_fixed_slice_preserves_ambiguous_ohlc_without_committing_that_bar(self):
        from dcabot.application.historical_simulation import simulate_historical_fixed_slice

        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("100", "103", "89", "100", "", ""),
        )

        result = simulate_historical_fixed_slice(
            dataset,
            _config(),
            slice_qty="1",
            config_hash="b" * 64,
        )

        self.assertEqual((result.execution_status, result.application_code), ("INDETERMINATE", "AMBIGUOUS_OHLC_PATH"))
        self.assertEqual(result.processed_bar_count, 1)
        self.assertEqual([action.bar_index for action in result.actions], [1])
        self.assertEqual(result.summary["qty"], "1")

    def test_fixed_slice_is_deterministic_for_the_same_inputs(self):
        from dcabot.application.historical_simulation import simulate_historical_fixed_slice

        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("99", "100", "99", "99", "", ""),
        )

        first = simulate_historical_fixed_slice(dataset, _config(), slice_qty="0.4", config_hash="b" * 64)
        second = simulate_historical_fixed_slice(dataset, _config(), slice_qty="0.4", config_hash="b" * 64)

        self.assertEqual(first, second)

    def test_gap_is_rejected_before_historical_state_is_started(self):
        from dcabot.application.historical_simulation import (
            HistoricalSimulationError,
            simulate_historical_ohlcv,
        )

        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("99", "100", "99", "99", "", ""),
        )
        second = dataset.bars[1]
        dataset = replace(
            dataset,
            bars=(
                dataset.bars[0],
                replace(
                    second,
                    open_time_us=second.open_time_us + 3_600_000_000,
                    close_time_us=second.close_time_us + 3_600_000_000,
                ),
            ),
        )

        with self.assertRaises(HistoricalSimulationError) as context:
            simulate_historical_ohlcv(dataset, _config(), config_hash="b" * 64)

        self.assertEqual(context.exception.code, "DATASET_NOT_CONTIGUOUS")

    def test_unknown_historical_interval_is_rejected_before_simulation(self):
        from dcabot.application.historical_simulation import (
            HistoricalSimulationError,
            simulate_historical_ohlcv,
        )

        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("99", "100", "99", "99", "", ""),
        )
        dataset = replace(dataset, metadata=replace(dataset.metadata, interval="2h"))

        with self.assertRaises(HistoricalSimulationError) as context:
            simulate_historical_ohlcv(dataset, _config(), config_hash="b" * 64)

        self.assertEqual(context.exception.code, "INTERVAL_UNKNOWN")

    def test_closed_bar_simulation_reuses_exact_core_and_closes_after_safety_then_tp(self):
        from dcabot.application.historical_simulation import simulate_historical_ohlcv

        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("95", "100", "89", "90", "", ""),
            ("97", "98", "97", "97", "", ""),
        )

        result = simulate_historical_ohlcv(dataset, _config(), config_hash="b" * 64)

        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertEqual([action.role for action in result.actions], ["BASE", "SAFETY:1", "EXIT"])
        self.assertEqual([action.deal_sequence for action in result.actions], [1, 1, 1])
        self.assertEqual(result.position_status, "CLOSED")
        self.assertEqual(result.funding_status, "NOT_MODELED")
        self.assertEqual(result.mark_status, "NOT_AVAILABLE")
        self.assertEqual(result.fee_amount, "0.384")

    def test_same_bar_safety_and_take_profit_is_indeterminate_without_committing_that_bar(self):
        from dcabot.application.historical_simulation import simulate_historical_ohlcv

        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("100", "103", "89", "100", "", ""),
        )

        result = simulate_historical_ohlcv(dataset, _config(), config_hash="b" * 64)

        self.assertEqual(result.execution_status, "INDETERMINATE")
        self.assertEqual(result.application_code, "AMBIGUOUS_OHLC_PATH")
        self.assertEqual(result.first_ambiguous_bar_index, 2)
        self.assertEqual([action.role for action in result.actions], ["BASE"])

    def test_new_take_profit_created_by_safety_is_not_evaluated_on_same_bar(self):
        from dcabot.application.historical_simulation import simulate_historical_ohlcv

        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("95", "100", "89", "90", "", ""),
        )

        result = simulate_historical_ohlcv(dataset, _config(), config_hash="b" * 64)

        self.assertEqual([action.role for action in result.actions], ["BASE", "SAFETY:1"])
        self.assertEqual(result.position_status, "OPEN_AT_END")

    def test_bot_restarts_a_new_deal_after_the_prior_deal_closes_flat(self):
        from dcabot.application.historical_simulation import simulate_historical_ohlcv

        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("95", "100", "89", "90", "", ""),
            ("97", "98", "97", "97", "", ""),
            ("110", "110", "110", "110", "", ""),
            ("113", "113", "113", "113", "", ""),
        )

        result = simulate_historical_ohlcv(dataset, _config(), config_hash="b" * 64)

        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertEqual(
            [action.role for action in result.actions],
            ["BASE", "SAFETY:1", "EXIT", "BASE", "EXIT"],
        )
        self.assertEqual([action.bar_index for action in result.actions], [1, 2, 3, 4, 5])
        self.assertEqual(
            [action.deal_sequence for action in result.actions],
            [1, 1, 1, 2, 2],
        )
        self.assertEqual(result.position_status, "CLOSED")
        self.assertEqual(result.processed_bar_count, 5)
        self.assertEqual(result.fee_amount, "0.607")
        self.assertEqual(result.summary["realized_gross"], "7")
        self.assertEqual(result.summary["action_count"], 5)
        self.assertEqual(result.summary["average_entry_price"], "100")
        self.assertEqual(result.summary["time_in_position_us"], 10_800_000_000)
        self.assertIn("max_drawdown", result.summary)

    def test_same_inputs_produce_the_same_result(self):
        from dcabot.application.historical_simulation import simulate_historical_ohlcv

        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("99", "100", "99", "99", "", ""),
        )

        first = simulate_historical_ohlcv(dataset, _config(), config_hash="b" * 64)
        second = simulate_historical_ohlcv(dataset, _config(), config_hash="b" * 64)

        self.assertEqual(first, second)
