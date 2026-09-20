import unittest

from dcabot.application.hedge_two_leg_contract import (
    HedgePositionIdentity,
    TwoLegState,
    advance_two_leg_state,
    new_hedge_position_identity,
)


class HedgeTwoLegContractTests(unittest.TestCase):
    def test_position_identity_keeps_one_way_and_hedge_scopes_distinct(self):
        one_way = new_hedge_position_identity(
            account_id="account",
            venue_profile="venue-v1",
            product_id="BTCUSDT",
            symbol="BTCUSDT",
            position_mode="ONE_WAY",
            hedge_side=None,
        )
        hedge_long = new_hedge_position_identity(
            account_id="account",
            venue_profile="venue-v1",
            product_id="BTCUSDT",
            symbol="BTCUSDT",
            position_mode="HEDGE",
            hedge_side="LONG",
        )
        hedge_short = new_hedge_position_identity(
            account_id="account",
            venue_profile="venue-v1",
            product_id="BTCUSDT",
            symbol="BTCUSDT",
            position_mode="HEDGE",
            hedge_side="SHORT",
        )

        self.assertEqual(
            one_way,
            HedgePositionIdentity(
                "account", "venue-v1", "BTCUSDT", "BTCUSDT", "ONE_WAY", None
            ),
        )
        self.assertNotEqual(hedge_long, hedge_short)
        self.assertNotEqual(one_way, hedge_long)

    def test_two_leg_path_preserves_partial_hedge_as_first_class_state(self):
        state = TwoLegState.NONE
        state = advance_two_leg_state(state, "LEG_A_SENT")
        state = advance_two_leg_state(state, "LEG_A_PARTIAL_FILL")
        self.assertEqual(state, TwoLegState.PARTIAL_HEDGE)
        self.assertEqual(
            advance_two_leg_state(state, "BOTH_LEGS_ACCEPTED"),
            TwoLegState.BOTH_ESTABLISHED,
        )

    def test_one_leg_fill_can_enter_recovery_without_rollback(self):
        state = advance_two_leg_state(TwoLegState.NONE, "LEG_A_SENT")
        state = advance_two_leg_state(state, "LEG_A_ACCEPTED_FILL")
        self.assertEqual(state, TwoLegState.ONE_LEG_FILLED)
        self.assertEqual(
            advance_two_leg_state(state, "RECOVERY_REQUIRED"),
            TwoLegState.RECOVERY_REQUIRED,
        )

    def test_invalid_identity_and_transition_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "HEDGE_SIDE_REQUIRED"):
            new_hedge_position_identity(
                account_id="account",
                venue_profile="venue-v1",
                product_id="BTCUSDT",
                symbol="BTCUSDT",
                position_mode="HEDGE",
                hedge_side=None,
            )
        with self.assertRaisesRegex(ValueError, "ONE_WAY_HEDGE_SIDE"):
            new_hedge_position_identity(
                account_id="account",
                venue_profile="venue-v1",
                product_id="BTCUSDT",
                symbol="BTCUSDT",
                position_mode="ONE_WAY",
                hedge_side="LONG",
            )
        with self.assertRaisesRegex(ValueError, "TWO_LEG_TRANSITION_INVALID"):
            advance_two_leg_state(TwoLegState.NONE, "BOTH_LEGS_ACCEPTED")
        with self.assertRaisesRegex(ValueError, "TWO_LEG_STATE_INVALID"):
            class UnhashableMatchingState:
                __hash__ = None

                def __eq__(self, other):
                    return other == TwoLegState.NONE

            advance_two_leg_state(UnhashableMatchingState(), "LEG_A_SENT")


if __name__ == "__main__":
    unittest.main()
