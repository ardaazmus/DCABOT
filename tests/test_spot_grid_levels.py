import unittest

from dcabot.application.spot_grid_levels import (
    ArithmeticGridLevels,
    SpotGridLevelError,
    build_arithmetic_grid_levels,
)


class SpotGridLevelTests(unittest.TestCase):
    def test_arithmetic_levels_use_exact_interval_count(self):
        result = build_arithmetic_grid_levels(
            lower_price="1000", upper_price="2000", interval_count=10
        )

        self.assertEqual(
            result,
            ArithmeticGridLevels(
                lower_price="1000",
                upper_price="2000",
                interval_count=10,
                step="100",
                levels=(
                    "1000",
                    "1100",
                    "1200",
                    "1300",
                    "1400",
                    "1500",
                    "1600",
                    "1700",
                    "1800",
                    "1900",
                    "2000",
                ),
            ),
        )

    def test_invalid_bounds_or_interval_count_fail_closed(self):
        with self.assertRaisesRegex(SpotGridLevelError, "GRID_BOUNDS_INVALID"):
            build_arithmetic_grid_levels(
                lower_price="2000", upper_price="1000", interval_count=10
            )
        with self.assertRaisesRegex(SpotGridLevelError, "GRID_INTERVAL_INVALID"):
            build_arithmetic_grid_levels(
                lower_price="1000", upper_price="2000", interval_count=0
            )

    def test_non_terminating_step_is_not_rounded_silently(self):
        with self.assertRaisesRegex(
            SpotGridLevelError, "GRID_LEVEL_UNREPRESENTABLE"
        ):
            build_arithmetic_grid_levels(
                lower_price="0.1", upper_price="1", interval_count=7
            )

    def test_level_generation_does_not_claim_inventory_or_economic_state(self):
        result = build_arithmetic_grid_levels(
            lower_price="10", upper_price="12", interval_count=2
        )

        self.assertFalse(hasattr(result, "inventory"))
        self.assertFalse(hasattr(result, "fee"))
        self.assertFalse(hasattr(result, "order_id"))


if __name__ == "__main__":
    unittest.main()
