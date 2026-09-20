import unittest

from dcabot.application.account_reservation import AccountCapacity, AccountReservation
from dcabot.application.futures_dca_fill_projection import FuturesDcaFill, project_futures_dca_fills
from dcabot.application.futures_dca_plan import project_futures_dca_plan
from dcabot.application.futures_dca_reservation import (
    FuturesDcaReservationError,
    project_futures_dca_reservation,
)
from dcabot.application.shared_account_identity import new_shared_account_identity


def binding_inputs():
    plan = project_futures_dca_plan(
        side="LONG", anchor_price="100", base_amount="10", base_sizing="QUOTE_NOTIONAL",
        safety_amount="2", safety_sizing="QUOTE_NOTIONAL", safety_count=2,
        deviation="0.01", step_multiplier="2", volume_multiplier="2",
        price_tick="0.01", quantity_step="0.0001",
    )
    fill_projection = project_futures_dca_fills(
        plan,
        (FuturesDcaFill("base", 0, "0.1", "100"), FuturesDcaFill("s1", 1, "0.02", "97")),
    )
    owner = new_shared_account_identity("account-1", "USD_M", "ONE_WAY", "deal-1", "allocation-1")
    return fill_projection, owner


class FuturesDcaReservationTests(unittest.TestCase):
    def test_pending_quote_is_bound_to_matching_capacity_without_commit(self):
        fill_projection, owner = binding_inputs()
        result = project_futures_dca_reservation(
            fill_projection=fill_projection,
            capacity=AccountCapacity("account-1", "USDT", "10", 0),
            active_reservations=(), reservation_id="safety-pending", owner=owner, expected_version=0,
        )
        self.assertEqual(
            (result.reservation.asset, result.reservation.amount, result.projection.requested, result.projection.available_after),
            ("USDT", "0.0198", "0.0198", "9.9802"),
        )

    def test_capacity_asset_and_position_mode_mismatch_fail_closed(self):
        fill_projection, owner = binding_inputs()
        with self.assertRaisesRegex(FuturesDcaReservationError, "FUTURES_DCA_RESERVATION_ASSET_CONFLICT"):
            project_futures_dca_reservation(
                fill_projection=fill_projection,
                capacity=AccountCapacity("account-1", "BTC", "10", 0),
                active_reservations=(), reservation_id="safety-pending", owner=owner, expected_version=0,
            )
        wrong_owner = new_shared_account_identity("account-1", "USD_M", "HEDGE", "deal-1", "allocation-1")
        with self.assertRaisesRegex(FuturesDcaReservationError, "FUTURES_DCA_RESERVATION_MODE_CONFLICT"):
            project_futures_dca_reservation(
                fill_projection=fill_projection,
                capacity=AccountCapacity("account-1", "USDT", "10", 0),
                active_reservations=(), reservation_id="safety-pending", owner=wrong_owner, expected_version=0,
            )

    def test_existing_active_reservation_and_version_are_preserved_by_projection(self):
        fill_projection, owner = binding_inputs()
        active = (AccountReservation("other", owner, "USDT", "9.99"),)
        with self.assertRaisesRegex(FuturesDcaReservationError, "ACCOUNT_CAPACITY_CONFLICT"):
            project_futures_dca_reservation(
                fill_projection=fill_projection,
                capacity=AccountCapacity("account-1", "USDT", "10", 0),
                active_reservations=active, reservation_id="safety-pending", owner=owner, expected_version=0,
            )
        with self.assertRaisesRegex(FuturesDcaReservationError, "ACCOUNT_VERSION_CONFLICT"):
            project_futures_dca_reservation(
                fill_projection=fill_projection,
                capacity=AccountCapacity("account-1", "USDT", "10", 1),
                active_reservations=(), reservation_id="safety-pending", owner=owner, expected_version=0,
            )


if __name__ == "__main__":
    unittest.main()
