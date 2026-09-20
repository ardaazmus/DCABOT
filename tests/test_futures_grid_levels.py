import unittest

from dcabot.application.futures_grid_levels import (
    FuturesGridLevelError,
    FuturesGridLevelProjection,
    FuturesGridProfile,
    project_futures_grid_levels,
)


class FuturesGridLevelTests(unittest.TestCase):
    def test_profile_is_explicit_and_isolated(self):
        self.assertEqual(
            FuturesGridProfile(),
            FuturesGridProfile(
                venue="BINANCE",
                product_family="USD_M",
                settlement_asset="USDT",
                margin_asset="USDT",
                contract_type="PERPETUAL",
                position_mode="ONE_WAY",
                margin_mode="ISOLATED",
                leverage="1",
            ),
        )

    def test_arithmetic_projection_keeps_direction_and_flat_policy(self):
        result = project_futures_grid_levels(
            profile=FuturesGridProfile(leverage="3"),
            direction="LONG",
            initial_position_policy="FLAT",
            level_mode="ARITHMETIC",
            lower_price="100",
            upper_price="200",
            interval_count=2,
            price_tick="1",
            tick_origin="0",
        )

        self.assertEqual(
            result,
            FuturesGridLevelProjection(
                profile=FuturesGridProfile(leverage="3"),
                direction="LONG",
                initial_position_policy="FLAT",
                level_mode="ARITHMETIC",
                lower_price="100",
                upper_price="200",
                interval_count=2,
                price_tick="1",
                tick_origin="0",
                levels=("100", "150", "200"),
                arithmetic_step="50",
                ratio_numerator=None,
                ratio_denominator=None,
            ),
        )

    def test_geometric_projection_is_separate_from_spot_result(self):
        result = project_futures_grid_levels(
            profile=FuturesGridProfile(),
            direction="NEUTRAL",
            initial_position_policy="FLAT",
            level_mode="GEOMETRIC",
            lower_price="100",
            upper_price="225",
            interval_count=2,
            price_tick="1",
            tick_origin="0",
        )

        self.assertEqual(result.levels, ("100", "150", "225"))
        self.assertEqual((result.ratio_numerator, result.ratio_denominator), ("3", "2"))
        self.assertEqual(result.level_mode, "GEOMETRIC")

    def test_non_flat_initial_position_is_fail_closed(self):
        with self.assertRaisesRegex(FuturesGridLevelError, "FUTURES_GRID_INITIAL_POSITION_UNSUPPORTED"):
            project_futures_grid_levels(
                profile=FuturesGridProfile(),
                direction="SHORT",
                initial_position_policy="LONG",
                level_mode="ARITHMETIC",
                lower_price="100",
                upper_price="200",
                interval_count=2,
                price_tick="1",
                tick_origin="0",
            )

    def test_invalid_profile_direction_or_mode_is_fail_closed(self):
        with self.assertRaisesRegex(FuturesGridLevelError, "FUTURES_GRID_PROFILE_UNSUPPORTED"):
            FuturesGridProfile(margin_mode="CROSS")
        with self.assertRaisesRegex(FuturesGridLevelError, "FUTURES_GRID_DIRECTION_INVALID"):
            project_futures_grid_levels(
                profile=FuturesGridProfile(),
                direction="BOTH",
                initial_position_policy="FLAT",
                level_mode="ARITHMETIC",
                lower_price="100",
                upper_price="200",
                interval_count=2,
                price_tick="1",
                tick_origin="0",
            )
        with self.assertRaisesRegex(FuturesGridLevelError, "FUTURES_GRID_LEVEL_MODE_INVALID"):
            project_futures_grid_levels(
                profile=FuturesGridProfile(),
                direction="SHORT",
                initial_position_policy="FLAT",
                level_mode="RANDOM",
                lower_price="100",
                upper_price="200",
                interval_count=2,
                price_tick="1",
                tick_origin="0",
            )

    def test_off_tick_or_unrepresentable_levels_do_not_round(self):
        with self.assertRaisesRegex(FuturesGridLevelError, "FUTURES_GRID_TICK_OFF_GRID"):
            project_futures_grid_levels(
                profile=FuturesGridProfile(),
                direction="SHORT",
                initial_position_policy="FLAT",
                level_mode="ARITHMETIC",
                lower_price="100",
                upper_price="225",
                interval_count=2,
                price_tick="10",
                tick_origin="0",
            )
        with self.assertRaisesRegex(FuturesGridLevelError, "FUTURES_GRID_LEVELS_INVALID"):
            project_futures_grid_levels(
                profile=FuturesGridProfile(),
                direction="NEUTRAL",
                initial_position_policy="FLAT",
                level_mode="GEOMETRIC",
                lower_price="100",
                upper_price="200",
                interval_count=2,
                price_tick="1",
                tick_origin="0",
            )

    def test_projection_has_no_position_order_margin_or_pnl_authority(self):
        result = project_futures_grid_levels(
            profile=FuturesGridProfile(),
            direction="SHORT",
            initial_position_policy="FLAT",
            level_mode="ARITHMETIC",
            lower_price="10",
            upper_price="12",
            interval_count=2,
            price_tick="1",
            tick_origin="0",
        )

        for field in ("position", "orders", "margin", "funding", "liquidation", "pnl"):
            self.assertFalse(hasattr(result, field))


if __name__ == "__main__":
    unittest.main()
