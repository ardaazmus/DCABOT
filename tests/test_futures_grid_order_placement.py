import unittest

from dcabot.application.futures_grid_levels import (
    FuturesGridProfile,
    project_futures_grid_levels,
)
from dcabot.application.futures_grid_order_placement import (
    FuturesGridPlacementError,
    assess_futures_grid_order_placement,
)


def projection():
    return project_futures_grid_levels(
        profile=FuturesGridProfile(),
        direction="LONG",
        initial_position_policy="FLAT",
        level_mode="ARITHMETIC",
        lower_price="100",
        upper_price="120",
        interval_count=2,
        price_tick="1",
        tick_origin="0",
    )


class FuturesGridOrderPlacementTests(unittest.TestCase):
    def test_static_fixed_returns_inert_projected_level_candidates(self):
        result = assess_futures_grid_order_placement(
            projection(), placement_mode="STATIC"
        )

        self.assertEqual(
            (result.decision, result.candidate_levels, result.order_authority),
            ("STATIC_CANDIDATE_ONLY", ("100", "110", "120"), "NONE"),
        )
        self.assertIsNone(result.reason)
        self.assertFalse(hasattr(result, "order_id"))

    def test_dynamic_placement_is_blocked_until_current_price_contract_exists(self):
        result = assess_futures_grid_order_placement(
            projection(), placement_mode="DYNAMIC"
        )

        self.assertEqual(
            (result.decision, result.candidate_levels, result.reason),
            ("BLOCKED_CONTRACT_REQUIRED", (), "FUTURES_GRID_DYNAMIC_PLACEMENT_UNVERIFIED"),
        )

    def test_range_revision_is_separate_from_static_placement(self):
        result = assess_futures_grid_order_placement(
            projection(), placement_mode="STATIC", range_policy="RANGE_REVISION"
        )

        self.assertEqual(
            (result.decision, result.candidate_levels, result.reason),
            (
                "BLOCKED_CONTRACT_REQUIRED",
                (),
                "FUTURES_GRID_RANGE_REVISION_SEPARATE_CONTRACT_REQUIRED",
            ),
        )

    def test_invalid_modes_and_projection_fail_closed(self):
        with self.assertRaisesRegex(FuturesGridPlacementError, "FUTURES_GRID_PLACEMENT_MODE_INVALID"):
            assess_futures_grid_order_placement(projection(), placement_mode="AUTO")
        with self.assertRaisesRegex(FuturesGridPlacementError, "FUTURES_GRID_RANGE_POLICY_INVALID"):
            assess_futures_grid_order_placement(
                projection(), placement_mode="STATIC", range_policy="TRAILING"
            )
        with self.assertRaisesRegex(FuturesGridPlacementError, "FUTURES_GRID_PLACEMENT_PROJECTION_INVALID"):
            assess_futures_grid_order_placement(None, placement_mode="STATIC")


if __name__ == "__main__":
    unittest.main()
