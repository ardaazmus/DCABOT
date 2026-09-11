import json
import unittest
from fractions import Fraction as F
from pathlib import Path

from dcabot.application.historical_fixed_limit import FixedLimitOrder
from dcabot.data_adapters.historical import (
    CanonicalBar,
    HistoricalDatasetInput,
    HistoricalDatasetMetadata,
)
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply


def _config() -> Config:
    raw = json.loads(Path("config/paper.json").read_text(encoding="utf-8"))
    return Config.parse(raw)


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


def _base_order(*, placement_bar_index: int = 1) -> FixedLimitOrder:
    return FixedLimitOrder(
        order_id="base-limit-1",
        side="BUY",
        limit_price="100",
        original_qty="1",
        placement_bar_index=placement_bar_index,
        placement_open_time_us=placement_bar_index * 3_600_000_000,
    )


class HistoricalBaseLimitBindingTests(unittest.TestCase):
    def test_base_strict_candidates_post_through_core_with_exact_remainder(self):
        from dcabot.application.historical_base_limit_binding import (
            simulate_base_fixed_limit_binding,
        )

        result = simulate_base_fixed_limit_binding(
            _dataset(
                ("105", "107", "101", "104"),
                ("105", "106", "99", "103"),
                ("103", "106", "98", "102"),
                ("101", "104", "97", "100"),
            ),
            _config(),
            _base_order(),
            slice_qty="0.4",
            config_hash="b" * 64,
        )

        self.assertEqual(result.status, "FILLED")
        self.assertEqual([action.quantity for action in result.actions], ["0.4", "0.4", "0.2"])
        self.assertEqual(result.state.position.qty, 1)
        self.assertEqual(result.state.orders["base-limit-1"].leaves, 0)
        self.assertEqual(result.state.anchor, 100)
        self.assertEqual(result.state.fees, F(1, 10))
        self.assertEqual(result.reserve_model, "NONE")

    def test_none_reserve_is_not_modeled_and_not_numeric_zero(self):
        from dcabot.application.historical_base_limit_binding import (
            simulate_base_fixed_limit_binding,
        )

        result = simulate_base_fixed_limit_binding(
            _dataset(
                ("105", "107", "101", "104"),
                ("105", "106", "100", "100"),
            ),
            _config(),
            _base_order(),
            slice_qty="0.4",
            config_hash="b" * 64,
        )

        self.assertEqual(
            (result.reserve_model, result.reserve_amount, result.reserve_asset),
            ("NONE", "NOT_MODELED", "NOT_APPLICABLE"),
        )
        self.assertNotEqual(result.reserve_amount, "0")

    def test_equality_observation_does_not_post_economic_fill(self):
        from dcabot.application.historical_base_limit_binding import (
            simulate_base_fixed_limit_binding,
        )

        result = simulate_base_fixed_limit_binding(
            _dataset(
                ("105", "107", "101", "104"),
                ("105", "106", "100", "100"),
            ),
            _config(),
            _base_order(),
            slice_qty="0.4",
            config_hash="b" * 64,
        )

        self.assertEqual(result.status, "OPEN_AT_END")
        self.assertEqual(result.actions, ())
        self.assertEqual(result.state.position.qty, 0)
        self.assertEqual(result.state.orders["base-limit-1"].leaves, 1)
        self.assertIsNone(result.state.anchor)

    def test_placement_bar_is_not_eligible_even_when_it_penetrates(self):
        from dcabot.application.historical_base_limit_binding import (
            simulate_base_fixed_limit_binding,
        )

        result = simulate_base_fixed_limit_binding(
            _dataset(
                ("105", "107", "99", "104"),
                ("105", "106", "101", "103"),
            ),
            _config(),
            _base_order(),
            slice_qty="0.4",
            config_hash="b" * 64,
        )

        self.assertEqual(result.status, "OPEN_AT_END")
        self.assertEqual(result.actions, ())
        self.assertEqual(result.state.position.qty, 0)

    def test_ambiguous_bar_preserves_core_prefix_without_new_fill(self):
        from dcabot.application.historical_base_limit_binding import (
            simulate_base_fixed_limit_binding,
        )

        result = simulate_base_fixed_limit_binding(
            _dataset(
                ("105", "107", "101", "104"),
                ("105", "106", "99", "103"),
                ("103", "106", "98", "102"),
            ),
            _config(),
            _base_order(),
            slice_qty="0.4",
            config_hash="b" * 64,
            ambiguous_bar_indices={3},
        )

        self.assertEqual((result.status, result.application_code), ("INDETERMINATE", "AMBIGUOUS_OHLC_PATH"))
        self.assertEqual([action.bar_index for action in result.actions], [2])
        self.assertEqual(result.state.position.qty, F(2, 5))
        self.assertEqual(result.state.orders["base-limit-1"].leaves, F(3, 5))

    def test_base_only_binding_rejects_non_buy_order(self):
        from dcabot.application.historical_base_limit_binding import (
            HistoricalBaseLimitBindingError,
            simulate_base_fixed_limit_binding,
        )

        with self.assertRaises(HistoricalBaseLimitBindingError) as context:
            simulate_base_fixed_limit_binding(
                _dataset(("105", "107", "101", "104")),
                _config(),
                FixedLimitOrder("exit-limit-1", "SELL", "100", "1", 1, 3_600_000_000),
                slice_qty="0.4",
                config_hash="b" * 64,
            )

        self.assertEqual(context.exception.code, "BASE_SIDE_REQUIRED")

    def test_pending_base_blocks_a_second_core_intent(self):
        from dcabot.application.historical_base_limit_binding import (
            simulate_base_fixed_limit_binding,
        )

        result = simulate_base_fixed_limit_binding(
            _dataset(
                ("105", "107", "101", "104"),
                ("105", "106", "100", "100"),
            ),
            _config(),
            _base_order(),
            slice_qty="0.4",
            config_hash="b" * 64,
        )

        with self.assertRaises(ValueError):
            apply(
                result.state,
                {
                    "type": "INTENT",
                    "order_id": "second-base",
                    "role": "BASE",
                    "qty": "1",
                    "limit_price": "99",
                },
                _config(),
            )

    def test_pending_base_blocks_safety_before_final_coverage(self):
        from dcabot.application.historical_base_limit_binding import (
            simulate_base_fixed_limit_binding,
        )

        result = simulate_base_fixed_limit_binding(
            _dataset(
                ("105", "107", "101", "104"),
                ("105", "106", "99", "103"),
            ),
            _config(),
            _base_order(),
            slice_qty="0.4",
            config_hash="b" * 64,
        )

        self.assertEqual(result.state.orders["base-limit-1"].leaves, F(3, 5))
        with self.assertRaises(ValueError):
            apply(
                result.state,
                {
                    "type": "INTENT",
                    "order_id": "safety-1",
                    "role": "SAFETY:1",
                    "qty": "1",
                    "limit_price": "90",
                },
                _config(),
            )

    def test_full_fill_without_final_coverage_has_no_anchor(self):
        config = _config()
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = apply(
            state,
            {
                "type": "INTENT",
                "order_id": "base-limit-1",
                "role": "BASE",
                "qty": "1",
                "limit_price": "100",
            },
            config,
        )
        state = apply(
            state,
            {
                "type": "FILL",
                "execution_id": "direct-fill-1",
                "order_id": "base-limit-1",
                "side": "BUY",
                "qty": "1",
                "price": "100",
                "fee": "0.1",
                "fee_asset": "USDT",
            },
            config,
        )

        order = state.orders["base-limit-1"]
        self.assertEqual((order.filled, order.leaves, order.complete, state.anchor), (1, 0, False, None))


if __name__ == "__main__":
    unittest.main()
