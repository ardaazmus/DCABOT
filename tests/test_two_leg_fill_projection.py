import unittest

from dcabot.application.hedge_two_leg_contract import (
    HedgePositionIdentity,
    TwoLegState,
)
from dcabot.application.two_leg_fill_projection import (
    LegFill,
    TwoLegFillProjection,
    accept_two_leg_fill,
    new_two_leg_projection,
    start_two_leg_projection,
)


def identity(side):
    return HedgePositionIdentity(
        account_id="account",
        venue_profile="venue-v1",
        product_id="BTCUSDT",
        symbol="BTCUSDT",
        position_mode="HEDGE",
        hedge_side=side,
    )


class TwoLegFillProjectionTests(unittest.TestCase):
    def test_accepted_partial_legs_remain_visible_until_both_are_complete(self):
        projection = start_two_leg_projection(new_two_leg_projection())
        projection, outcome = accept_two_leg_fill(
            projection,
            LegFill("fill-a-1", "A", identity("LONG"), "0.4", "PARTIAL", 1_000),
        )
        self.assertEqual(outcome, "ACCEPTED")
        self.assertEqual(projection.state, TwoLegState.PARTIAL_HEDGE)
        self.assertEqual(projection.leg_a_quantity, "0.4")

        projection, _ = accept_two_leg_fill(
            projection,
            LegFill("fill-b-1", "B", identity("SHORT"), "1", "FULL", 2_000),
        )
        self.assertEqual(projection.state, TwoLegState.PARTIAL_HEDGE)
        self.assertEqual(projection.leg_b_quantity, "1")

        projection, _ = accept_two_leg_fill(
            projection,
            LegFill("fill-a-2", "A", identity("LONG"), "0.6", "FULL", 3_000),
        )
        self.assertEqual(projection.state, TwoLegState.BOTH_ESTABLISHED)
        self.assertEqual(projection.leg_a_quantity, "1")

    def test_duplicate_is_idempotent_and_conflicting_fill_fails_closed(self):
        projection = start_two_leg_projection(new_two_leg_projection())
        fill = LegFill("fill-a-1", "A", identity("LONG"), "1", "FULL", 1_000)
        projection, outcome = accept_two_leg_fill(projection, fill)
        duplicate, duplicate_outcome = accept_two_leg_fill(projection, fill)
        self.assertEqual(duplicate, projection)
        self.assertEqual(duplicate_outcome, "DUPLICATE")

        with self.assertRaisesRegex(ValueError, "TWO_LEG_FILL_CONFLICT"):
            accept_two_leg_fill(
                projection,
                LegFill("fill-a-1", "A", identity("LONG"), "2", "FULL", 1_000),
            )

    def test_cross_scope_or_same_side_fill_is_rejected(self):
        projection = start_two_leg_projection(new_two_leg_projection())
        projection, _ = accept_two_leg_fill(
            projection,
            LegFill("fill-a-1", "A", identity("LONG"), "1", "FULL", 1_000),
        )
        with self.assertRaisesRegex(ValueError, "TWO_LEG_SIDE_CONFLICT"):
            accept_two_leg_fill(
                projection,
                LegFill("fill-b-1", "B", identity("LONG"), "1", "FULL", 2_000),
            )

    def test_invalid_order_and_fill_inputs_do_not_create_economic_state(self):
        with self.assertRaisesRegex(ValueError, "TWO_LEG_TRANSITION_INVALID"):
            accept_two_leg_fill(
                new_two_leg_projection(),
                LegFill("fill-a-1", "A", identity("LONG"), "1", "FULL", 1_000),
            )
        projection = start_two_leg_projection(new_two_leg_projection())
        with self.assertRaisesRegex(ValueError, "TWO_LEG_EVENT_TIME_ORDER"):
            projection, _ = accept_two_leg_fill(
                projection,
                LegFill("fill-a-1", "A", identity("LONG"), "1", "FULL", 2_000),
            )
            accept_two_leg_fill(
                projection,
                LegFill("fill-b-1", "B", identity("SHORT"), "1", "FULL", 1_000),
            )

    def test_public_projection_constructor_rejects_inconsistent_state(self):
        with self.assertRaisesRegex(ValueError, "TWO_LEG_STATE_INCONSISTENT"):
            TwoLegFillProjection(state=TwoLegState.BOTH_ESTABLISHED)

    def test_wrong_type_whitelists_fail_closed(self):
        class EqualsTo:
            __hash__ = None

            def __init__(self, value):
                self.value = value

            def __eq__(self, other):
                return other == self.value

        with self.assertRaisesRegex(ValueError, "TWO_LEG_STATE_INVALID"):
            TwoLegFillProjection(state=EqualsTo(TwoLegState.NONE))
        with self.assertRaisesRegex(ValueError, "TWO_LEG_LEG_ID_INVALID"):
            LegFill(
                "fill-a-1",
                EqualsTo("A"),
                identity("LONG"),
                "1",
                "FULL",
                1_000,
            )
        with self.assertRaisesRegex(ValueError, "TWO_LEG_FILL_STATUS_INVALID"):
            LegFill(
                "fill-a-1",
                "A",
                identity("LONG"),
                "1",
                EqualsTo("FULL"),
                1_000,
            )

    def test_public_projection_rejects_identity_and_aggregate_mismatch(self):
        with self.assertRaisesRegex(ValueError, "TWO_LEG_POSITION_MODE_INVALID"):
            TwoLegFillProjection(
                state=TwoLegState.LEG_A_PENDING,
                leg_a_identity=HedgePositionIdentity(
                    account_id="account",
                    venue_profile="venue-v1",
                    product_id="BTCUSDT",
                    symbol="BTCUSDT",
                    position_mode="ONE_WAY",
                    hedge_side=None,
                ),
            )
        with self.assertRaisesRegex(ValueError, "TWO_LEG_SIDE_CONFLICT"):
            TwoLegFillProjection(
                state=TwoLegState.LEG_A_PENDING,
                leg_a_identity=identity("LONG"),
                leg_b_identity=identity("LONG"),
            )
        with self.assertRaisesRegex(ValueError, "TWO_LEG_SCOPE_CONFLICT"):
            TwoLegFillProjection(
                state=TwoLegState.LEG_A_PENDING,
                leg_a_identity=identity("LONG"),
                leg_b_identity=HedgePositionIdentity(
                    account_id="other-account",
                    venue_profile="venue-v1",
                    product_id="BTCUSDT",
                    symbol="BTCUSDT",
                    position_mode="HEDGE",
                    hedge_side="SHORT",
                ),
            )
        fill = LegFill("fill-a-1", "A", identity("LONG"), "1", "FULL", 1_000)
        with self.assertRaisesRegex(ValueError, "TWO_LEG_AGGREGATE_INCONSISTENT"):
            TwoLegFillProjection(
                state=TwoLegState.ONE_LEG_FILLED,
                leg_a_identity=identity("LONG"),
                leg_a_quantity="0",
                leg_a_status="FULL",
                fills=(fill,),
            )
        complete_b = LegFill("fill-b-1", "B", identity("SHORT"), "1", "FULL", 2_000)
        with self.assertRaisesRegex(ValueError, "TWO_LEG_STATE_INCONSISTENT"):
            TwoLegFillProjection(
                state=TwoLegState.RECOVERY_REQUIRED,
                leg_a_identity=identity("LONG"),
                leg_b_identity=identity("SHORT"),
                leg_a_quantity="1",
                leg_b_quantity="1",
                leg_a_status="FULL",
                leg_b_status="FULL",
                fills=(fill, complete_b),
            )


if __name__ == "__main__":
    unittest.main()
