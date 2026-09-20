import unittest

from dcabot.application.futures_grid_levels import FuturesGridProfile
from dcabot.application.futures_grid_position import (
    FuturesGridFill,
    FuturesGridFillSide,
    FuturesGridPositionError,
    apply_accepted_futures_grid_fill,
    new_futures_grid_position,
)


def fill(fill_id, side, price, quantity, effective_time_us):
    return FuturesGridFill(
        fill_id=fill_id,
        side=side,
        price=price,
        quantity=quantity,
        effective_time_us=effective_time_us,
    )


class FuturesGridPositionTests(unittest.TestCase):
    def test_flat_long_buy_opens_exact_position(self):
        state = new_futures_grid_position(
            profile=FuturesGridProfile(), direction="LONG"
        )
        result = apply_accepted_futures_grid_fill(
            state, fill("long-buy-1", FuturesGridFillSide.BUY, "100", "2", 1)
        )

        self.assertEqual((result.position_side, result.quantity, result.average_entry), ("LONG", "2", "100"))

    def test_long_same_direction_fill_updates_weighted_average_exactly(self):
        state = new_futures_grid_position(
            profile=FuturesGridProfile(), direction="LONG"
        )
        state = apply_accepted_futures_grid_fill(
            state, fill("long-buy-1", FuturesGridFillSide.BUY, "100", "2", 1)
        )
        result = apply_accepted_futures_grid_fill(
            state, fill("long-buy-2", FuturesGridFillSide.BUY, "110", "2", 2)
        )

        self.assertEqual((result.position_side, result.quantity, result.average_entry), ("LONG", "4", "105"))

    def test_long_sell_reduces_and_full_close_returns_flat_without_pnl(self):
        state = new_futures_grid_position(
            profile=FuturesGridProfile(), direction="LONG"
        )
        state = apply_accepted_futures_grid_fill(
            state, fill("long-buy-1", FuturesGridFillSide.BUY, "100", "2", 1)
        )
        partial = apply_accepted_futures_grid_fill(
            state, fill("long-sell-1", FuturesGridFillSide.SELL, "120", "1", 2)
        )
        closed = apply_accepted_futures_grid_fill(
            partial, fill("long-sell-2", FuturesGridFillSide.SELL, "121", "1", 3)
        )

        self.assertEqual((partial.position_side, partial.quantity, partial.average_entry), ("LONG", "1", "100"))
        self.assertEqual((closed.position_side, closed.quantity, closed.average_entry), ("FLAT", "0", None))
        self.assertFalse(hasattr(closed, "realized_pnl"))

    def test_short_sell_opens_and_buy_reduces_exact_position(self):
        state = new_futures_grid_position(
            profile=FuturesGridProfile(), direction="SHORT"
        )
        state = apply_accepted_futures_grid_fill(
            state, fill("short-sell-1", FuturesGridFillSide.SELL, "100", "3", 1)
        )
        result = apply_accepted_futures_grid_fill(
            state, fill("short-buy-1", FuturesGridFillSide.BUY, "90", "1", 2)
        )

        self.assertEqual((result.position_side, result.quantity, result.average_entry), ("SHORT", "2", "100"))

    def test_flat_reverse_and_overclose_are_fail_closed(self):
        state = new_futures_grid_position(
            profile=FuturesGridProfile(), direction="LONG"
        )
        with self.assertRaisesRegex(FuturesGridPositionError, "FUTURES_GRID_DIRECTION_CONFLICT"):
            apply_accepted_futures_grid_fill(
                state, fill("wrong-open", FuturesGridFillSide.SELL, "100", "1", 1)
            )
        state = apply_accepted_futures_grid_fill(
            state, fill("long-buy-1", FuturesGridFillSide.BUY, "100", "1", 1)
        )
        with self.assertRaisesRegex(FuturesGridPositionError, "FUTURES_GRID_POSITION_OVERFLOW"):
            apply_accepted_futures_grid_fill(
                state, fill("overclose", FuturesGridFillSide.SELL, "90", "2", 2)
            )

    def test_duplicate_is_idempotent_and_conflict_is_rejected(self):
        state = new_futures_grid_position(
            profile=FuturesGridProfile(), direction="LONG"
        )
        first = fill("long-buy-1", FuturesGridFillSide.BUY, "100", "1", 1)
        state = apply_accepted_futures_grid_fill(state, first)
        self.assertEqual(apply_accepted_futures_grid_fill(state, first), state)
        with self.assertRaisesRegex(FuturesGridPositionError, "FUTURES_GRID_FILL_CONFLICT"):
            apply_accepted_futures_grid_fill(
                state, fill("long-buy-1", FuturesGridFillSide.BUY, "101", "1", 1)
            )

    def test_event_time_neutral_and_initial_policy_are_fail_closed(self):
        with self.assertRaisesRegex(FuturesGridPositionError, "FUTURES_GRID_POSITION_DIRECTION_UNSUPPORTED"):
            new_futures_grid_position(profile=FuturesGridProfile(), direction="NEUTRAL")
        with self.assertRaisesRegex(FuturesGridPositionError, "FUTURES_GRID_INITIAL_POSITION_UNSUPPORTED"):
            new_futures_grid_position(
                profile=FuturesGridProfile(), direction="LONG", initial_position_policy="LONG"
            )
        state = new_futures_grid_position(
            profile=FuturesGridProfile(), direction="LONG"
        )
        state = apply_accepted_futures_grid_fill(
            state, fill("long-buy-1", FuturesGridFillSide.BUY, "100", "1", 2)
        )
        with self.assertRaisesRegex(FuturesGridPositionError, "FUTURES_GRID_FILL_TIME_ORDER"):
            apply_accepted_futures_grid_fill(
                state, fill("late-fill", FuturesGridFillSide.BUY, "99", "1", 1)
            )

    def test_non_exact_average_fails_without_rounding(self):
        state = new_futures_grid_position(
            profile=FuturesGridProfile(), direction="LONG"
        )
        state = apply_accepted_futures_grid_fill(
            state, fill("long-buy-1", FuturesGridFillSide.BUY, "1", "1", 1)
        )
        with self.assertRaisesRegex(FuturesGridPositionError, "FUTURES_GRID_AVERAGE_NOT_EXACT"):
            apply_accepted_futures_grid_fill(
                state, fill("long-buy-2", FuturesGridFillSide.BUY, "2", "2", 2)
            )

    def test_position_projection_has_no_order_margin_funding_or_persistence_authority(self):
        result = new_futures_grid_position(
            profile=FuturesGridProfile(), direction="LONG"
        )

        for field in ("orders", "margin", "funding", "liquidation", "realized_pnl", "store"):
            self.assertFalse(hasattr(result, field))


if __name__ == "__main__":
    unittest.main()
