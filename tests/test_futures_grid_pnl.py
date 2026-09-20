import unittest

from dcabot.application.futures_grid_levels import FuturesGridProfile
from dcabot.application.futures_grid_pnl import (
    FuturesGridFundingEvent,
    FuturesGridPnlError,
    project_futures_grid_pnl,
)
from dcabot.application.futures_grid_position import (
    FuturesGridFill,
    FuturesGridFillSide,
    apply_accepted_futures_grid_fill,
    new_futures_grid_position,
)


def grid_state(direction="LONG"):
    state = new_futures_grid_position(profile=FuturesGridProfile(), direction=direction)
    open_side = FuturesGridFillSide.BUY if direction == "LONG" else FuturesGridFillSide.SELL
    state = apply_accepted_futures_grid_fill(
        state, FuturesGridFill("open-1", open_side, "100", "2", 1)
    )
    close_side = FuturesGridFillSide.SELL if direction == "LONG" else FuturesGridFillSide.BUY
    return apply_accepted_futures_grid_fill(
        state, FuturesGridFill("close-1", close_side, "110" if direction == "LONG" else "90", "1", 3)
    )


class FuturesGridPnlTests(unittest.TestCase):
    def test_long_splits_matched_cycle_from_open_inventory_and_funding(self):
        result = project_futures_grid_pnl(
            grid_state(),
            contract_size="1",
            mark_price="120",
            as_of_time_us=4,
            funding_events=(FuturesGridFundingEvent("fund-1", 2, "USDT", "-2"),),
        )

        self.assertEqual(
            (
                result.realized_gross_pnl,
                result.unrealized_pnl,
                result.funding_cashflow,
                result.matched_cycle_profit,
                result.total_pnl,
            ),
            ("10", "20", "-2", "8", "28"),
        )

    def test_short_uses_opposite_price_movement(self):
        result = project_futures_grid_pnl(
            grid_state("SHORT"),
            contract_size="2",
            mark_price="80",
            as_of_time_us=4,
        )

        self.assertEqual(
            (result.realized_gross_pnl, result.unrealized_pnl, result.total_pnl),
            ("20", "40", "60"),
        )

    def test_flat_position_has_no_unrealized_pnl_but_keeps_cycle_result(self):
        state = grid_state()
        state = apply_accepted_futures_grid_fill(
            state, FuturesGridFill("close-2", FuturesGridFillSide.SELL, "120", "1", 4)
        )
        result = project_futures_grid_pnl(
            state, contract_size="1", mark_price="999", as_of_time_us=4
        )

        self.assertEqual(
            (result.realized_gross_pnl, result.unrealized_pnl, result.total_pnl),
            ("30", "0", "30"),
        )
        self.assertFalse(hasattr(result, "total_equity"))

    def test_funding_identity_asset_order_and_snapshot_are_fail_closed(self):
        state = grid_state()
        with self.assertRaisesRegex(FuturesGridPnlError, "FUTURES_GRID_FUNDING_ASSET_MISMATCH"):
            project_futures_grid_pnl(
                state,
                contract_size="1",
                mark_price="120",
                as_of_time_us=4,
                funding_events=(FuturesGridFundingEvent("fund-1", 2, "BTC", "1"),),
            )
        with self.assertRaisesRegex(FuturesGridPnlError, "FUTURES_GRID_PNL_FILL_AFTER_SNAPSHOT"):
            project_futures_grid_pnl(state, contract_size="1", mark_price="120", as_of_time_us=2)
        with self.assertRaisesRegex(FuturesGridPnlError, "FUTURES_GRID_FUNDING_CONFLICT"):
            project_futures_grid_pnl(
                state,
                contract_size="1",
                mark_price="120",
                as_of_time_us=4,
                funding_events=(
                    FuturesGridFundingEvent("fund-1", 2, "USDT", "1"),
                    FuturesGridFundingEvent("fund-1", 2, "USDT", "2"),
                ),
            )

    def test_funding_after_snapshot_and_non_positive_inputs_fail_closed(self):
        state = grid_state()
        with self.assertRaisesRegex(FuturesGridPnlError, "FUTURES_GRID_FUNDING_AFTER_SNAPSHOT"):
            project_futures_grid_pnl(
                state,
                contract_size="1",
                mark_price="120",
                as_of_time_us=4,
                funding_events=(FuturesGridFundingEvent("fund-1", 5, "USDT", "1"),),
            )
        with self.assertRaisesRegex(FuturesGridPnlError, "FUTURES_GRID_PNL_NUMERIC_INVALID"):
            project_futures_grid_pnl(state, contract_size="0", mark_price="120", as_of_time_us=4)


if __name__ == "__main__":
    unittest.main()
