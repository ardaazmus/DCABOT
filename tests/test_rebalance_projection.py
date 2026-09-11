import unittest

from dcabot.application.rebalance_projection import (
    RebalanceProjection,
    RebalanceTarget,
    RebalanceProjectionError,
    build_rebalance_projection,
)


class RebalanceProjectionTests(unittest.TestCase):
    def test_exact_target_values_and_trade_deltas_are_projected(self):
        result = build_rebalance_projection(
            valuation_asset="USDT",
            total_equity="1000",
            allocations=(
                ("BTC", "0.6", "500"),
                ("ETH", "0.4", "500"),
            ),
        )

        self.assertEqual(
            result,
            RebalanceProjection(
                valuation_asset="USDT",
                total_equity="1000",
                targets=(
                    RebalanceTarget(
                        asset="BTC",
                        target_weight="0.6",
                        target_value="600",
                        current_value="500",
                        trade_delta="100",
                    ),
                    RebalanceTarget(
                        asset="ETH",
                        target_weight="0.4",
                        target_value="400",
                        current_value="500",
                        trade_delta="-100",
                    ),
                ),
            ),
        )

    def test_asset_order_does_not_change_canonical_projection(self):
        first = build_rebalance_projection(
            valuation_asset="USDT",
            total_equity="1000",
            allocations=(("BTC", "0.6", "500"), ("ETH", "0.4", "500")),
        )
        second = build_rebalance_projection(
            valuation_asset="USDT",
            total_equity="1000",
            allocations=(("ETH", "0.4", "500"), ("BTC", "0.6", "500")),
        )

        self.assertEqual(first, second)

    def test_weights_must_sum_to_one_and_assets_must_be_unique(self):
        with self.assertRaisesRegex(
            RebalanceProjectionError, "REBALANCE_WEIGHTS_INVALID"
        ):
            build_rebalance_projection(
                valuation_asset="USDT",
                total_equity="1000",
                allocations=(("BTC", "0.6", "500"),),
            )
        with self.assertRaisesRegex(
            RebalanceProjectionError, "REBALANCE_ASSET_DUPLICATE"
        ):
            build_rebalance_projection(
                valuation_asset="USDT",
                total_equity="1000",
                allocations=(
                    ("BTC", "0.5", "500"),
                    ("BTC", "0.5", "500"),
                ),
            )

    def test_negative_current_value_and_invalid_weight_fail_closed(self):
        with self.assertRaisesRegex(
            RebalanceProjectionError, "REBALANCE_CURRENT_VALUE_INVALID"
        ):
            build_rebalance_projection(
                valuation_asset="USDT",
                total_equity="1000",
                allocations=(("BTC", "1", "-1"),),
            )
        with self.assertRaisesRegex(
            RebalanceProjectionError, "REBALANCE_WEIGHT_INVALID"
        ):
            build_rebalance_projection(
                valuation_asset="USDT",
                total_equity="1000",
                allocations=(("BTC", "1.1", "1000"),),
            )

    def test_unrepresentable_target_value_is_not_rounded_silently(self):
        with self.assertRaisesRegex(
            RebalanceProjectionError, "REBALANCE_VALUE_UNREPRESENTABLE"
        ):
            build_rebalance_projection(
                valuation_asset="USDT",
                total_equity="0.123456789012345678901234",
                allocations=(
                    ("BTC", "0.333333333333333333333333", "0"),
                    ("ETH", "0.666666666666666666666667", "0"),
                ),
            )

    def test_projection_has_no_order_or_fill_authority(self):
        result = build_rebalance_projection(
            valuation_asset="USDT",
            total_equity="1000",
            allocations=(("BTC", "1", "1000"),),
        )

        self.assertFalse(hasattr(result, "orders"))
        self.assertFalse(hasattr(result, "fills"))
