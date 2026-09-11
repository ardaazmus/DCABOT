from decimal import Decimal
import unittest

from dcabot.application.historical_fixed_limit import (
    FIXED_LIMIT_MODEL,
    FixedLimitOrder,
    simulate_fixed_limit_order,
)
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.domain.config import Config


def _dataset(*ohlc: tuple[str, str, str, str]) -> HistoricalDatasetInput:
    bars = tuple(
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
        for index, (open_price, high, low, close) in enumerate(ohlc, start=1)
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
        bars=bars,
    )


def _config() -> Config:
    return Config.parse(
        {
            "schema_version": 1,
            "mode": "offline",
            "symbol": "BTCUSDT",
            "base_asset": "BTC",
            "quote_asset": "USDT",
            "base_qty": "1",
            "safety_qty": "1",
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
    )


def _reference_kind(side: str, high: str, low: str, limit: str) -> str:
    """Independent table oracle; it intentionally does not call production code."""

    if side == "BUY":
        observed = Decimal(low) - Decimal(limit)
    else:
        observed = Decimal(high) - Decimal(limit)
    if observed == 0:
        return "EQUALITY_TOUCH"
    if (side == "BUY" and observed < 0) or (side == "SELL" and observed > 0):
        return "STRICT_PENETRATION"
    return "NONE"


class HistoricalFixedLimitTests(unittest.TestCase):
    def test_placement_bar_is_not_eligible_and_next_bar_strictly_fills_at_limit(self):
        result = simulate_fixed_limit_order(
            _dataset(
                ("105", "107", "99", "104"),
                ("105", "106", "99", "103"),
            ),
            _config(),
            FixedLimitOrder("order-1", "BUY", "100", "0.004", 1, 3_600_000_000),
            slice_qty="0.003",
        )

        self.assertEqual(result.model, FIXED_LIMIT_MODEL)
        self.assertEqual(result.status, "OPEN_AT_END")
        self.assertEqual(result.observations[0].kind, "STRICT_PENETRATION")
        self.assertEqual(result.actions[0].bar_index, 2)
        self.assertEqual(result.actions[0].fill_price, "100")
        self.assertEqual(result.actions[0].quantity, "0.003")
        self.assertEqual(result.leaves_qty, "0.001")

    def test_equality_is_observed_without_fill_and_eof_remains_open(self):
        result = simulate_fixed_limit_order(
            _dataset(("105", "106", "100", "102")),
            _config(),
            FixedLimitOrder("order-1", "BUY", "100", "0.001", 0, 0),
            slice_qty="0.001",
        )

        self.assertEqual(result.status, "OPEN_AT_END")
        self.assertEqual(result.last_observation_kind, "EQUALITY_TOUCH")
        self.assertEqual(result.actions, ())
        self.assertEqual(result.leaves_qty, "0.001")

    def test_advantageous_open_does_not_replace_exact_limit_fill_price(self):
        result = simulate_fixed_limit_order(
            _dataset(("98", "102", "97", "101")),
            _config(),
            FixedLimitOrder("order-1", "BUY", "100", "0.001", 0, 0),
            slice_qty="0.001",
        )

        self.assertEqual(result.status, "FILLED")
        self.assertEqual(result.actions[0].fill_price, "100")
        self.assertEqual(result.actions[0].observation_kind, "STRICT_PENETRATION")

    def test_sell_touch_and_strict_penetration_are_mirrored(self):
        touch = simulate_fixed_limit_order(
            _dataset(("95", "100", "94", "99")),
            _config(),
            FixedLimitOrder("order-1", "SELL", "100", "0.001", 0, 0),
            slice_qty="0.001",
        )
        fill = simulate_fixed_limit_order(
            _dataset(("95", "101", "94", "99")),
            _config(),
            FixedLimitOrder("order-1", "SELL", "100", "0.001", 0, 0),
            slice_qty="0.001",
        )

        self.assertEqual(touch.last_observation_kind, "EQUALITY_TOUCH")
        self.assertEqual(touch.actions, ())
        self.assertEqual(fill.status, "FILLED")
        self.assertEqual(fill.actions[0].fill_price, "100")

    def test_exact_remainder_has_one_fill_per_bar(self):
        result = simulate_fixed_limit_order(
            _dataset(
                ("105", "107", "101", "104"),
                ("105", "107", "99", "104"),
                ("103", "106", "98", "102"),
            ),
            _config(),
            FixedLimitOrder("order-1", "BUY", "100", "0.005", 0, 0),
            slice_qty="0.003",
        )

        self.assertEqual(result.status, "FILLED")
        self.assertEqual([action.quantity for action in result.actions], ["0.003", "0.002"])
        self.assertEqual([action.bar_index for action in result.actions], [2, 3])
        self.assertEqual(result.leaves_qty, "0")

    def test_competing_event_is_fail_closed_before_limit_fill(self):
        result = simulate_fixed_limit_order(
            _dataset(("105", "107", "99", "104")),
            _config(),
            FixedLimitOrder("order-1", "BUY", "100", "0.001", 0, 0),
            slice_qty="0.001",
            ambiguous_bar_indices={1},
        )

        self.assertEqual(result.status, "INDETERMINATE")
        self.assertEqual(result.application_code, "AMBIGUOUS_OHLC_PATH")
        self.assertEqual(result.actions, ())
        self.assertEqual(result.leaves_qty, "0.001")

    def test_independent_decimal_table_oracle_matches_trigger_and_fill_policy(self):
        cases = (
            ("BUY", "107", "99", "FILLED", "STRICT_PENETRATION"),
            ("BUY", "106", "100", "OPEN_AT_END", "EQUALITY_TOUCH"),
            ("SELL", "101", "94", "FILLED", "STRICT_PENETRATION"),
            ("SELL", "99", "94", "OPEN_AT_END", "NONE"),
        )
        for side, high, low, expected_status, expected_kind in cases:
            with self.subTest(side=side, high=high, low=low):
                result = simulate_fixed_limit_order(
                    _dataset(("100", high, low, "100")),
                    _config(),
                    FixedLimitOrder("order-1", side, "100", "0.001", 0, 0),
                    slice_qty="0.001",
                )
                self.assertEqual(_reference_kind(side, high, low, "100"), expected_kind)
                self.assertEqual(result.status, expected_status)
                self.assertEqual(result.last_observation_kind, expected_kind)


if __name__ == "__main__":
    unittest.main()
