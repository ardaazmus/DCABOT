import unittest

from dcabot.application.futures_grid_levels import FuturesGridProfile
from dcabot.application.futures_grid_margin import (
    FuturesGridMarginReserveError,
    project_futures_grid_margin_reserve,
)
from dcabot.application.futures_grid_position import (
    FuturesGridFill,
    FuturesGridFillSide,
    apply_accepted_futures_grid_fill,
    new_futures_grid_position,
)


def opened_state(direction="LONG", price="100", quantity="2"):
    state = new_futures_grid_position(
        profile=FuturesGridProfile(leverage="2"), direction=direction
    )
    side = FuturesGridFillSide.BUY if direction == "LONG" else FuturesGridFillSide.SELL
    return apply_accepted_futures_grid_fill(
        state,
        FuturesGridFill("open-1", side, price, quantity, 1),
    )


class FuturesGridMarginTests(unittest.TestCase):
    def test_projects_explicit_initial_margin_without_balance_claim(self):
        result = project_futures_grid_margin_reserve(
            opened_state(), reference_price="100", contract_size="1"
        )

        self.assertEqual(
            (
                result.notional,
                result.required_initial_margin,
                result.reserve_asset,
                result.capacity_status,
            ),
            ("200", "100", "USDT", "UNVERIFIED"),
        )

    def test_explicit_contract_size_and_available_margin_are_used(self):
        result = project_futures_grid_margin_reserve(
            opened_state("SHORT", quantity="3"),
            reference_price="100",
            contract_size="2",
            available_margin="300",
        )

        self.assertEqual(
            (result.notional, result.required_initial_margin, result.capacity_status),
            ("600", "300", "ELIGIBLE"),
        )

    def test_insufficient_available_margin_is_a_projection_status(self):
        result = project_futures_grid_margin_reserve(
            opened_state(), reference_price="100", contract_size="1", available_margin="99"
        )

        self.assertEqual(result.capacity_status, "INSUFFICIENT_AVAILABLE_MARGIN")

    def test_flat_position_and_unsupported_policy_fail_closed(self):
        flat = new_futures_grid_position(profile=FuturesGridProfile(), direction="LONG")
        with self.assertRaisesRegex(FuturesGridMarginReserveError, "FUTURES_GRID_MARGIN_FLAT_POSITION"):
            project_futures_grid_margin_reserve(flat, reference_price="100", contract_size="1")
        with self.assertRaisesRegex(FuturesGridMarginReserveError, "FUTURES_GRID_RESERVE_POLICY_UNSUPPORTED"):
            project_futures_grid_margin_reserve(
                opened_state(), reference_price="100", contract_size="1", reserve_policy="MAINTENANCE"
            )

    def test_missing_contract_size_or_invalid_available_margin_fail_closed(self):
        with self.assertRaisesRegex(FuturesGridMarginReserveError, "FUTURES_GRID_MARGIN_NUMERIC_INVALID"):
            project_futures_grid_margin_reserve(opened_state(), reference_price="100", contract_size="0")
        with self.assertRaisesRegex(FuturesGridMarginReserveError, "FUTURES_GRID_AVAILABLE_MARGIN_INVALID"):
            project_futures_grid_margin_reserve(
                opened_state(), reference_price="100", contract_size="1", available_margin="-1"
            )

    def test_non_terminating_initial_margin_is_not_rounded(self):
        state = new_futures_grid_position(
            profile=FuturesGridProfile(leverage="3"), direction="LONG"
        )
        state = apply_accepted_futures_grid_fill(
            state,
            FuturesGridFill("open-1", FuturesGridFillSide.BUY, "10", "1", 1),
        )
        with self.assertRaisesRegex(FuturesGridMarginReserveError, "FUTURES_GRID_MARGIN_NOT_EXACT"):
            project_futures_grid_margin_reserve(state, reference_price="10", contract_size="1")


if __name__ == "__main__":
    unittest.main()
