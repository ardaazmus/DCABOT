import unittest

from dcabot.application.account_reservation import (
    AccountCapacity,
    AccountReservation,
    AccountReservationError,
    ReservationProjection,
    project_reservation,
)
from dcabot.application.shared_account_identity import new_shared_account_identity


def capacity(version=3):
    return AccountCapacity(
        account_id="account-1", asset="USDT", amount="100", version=version
    )


def reservation(reservation_id, amount):
    return AccountReservation(
        reservation_id=reservation_id,
        owner=new_shared_account_identity(
            "account-1", "BTCUSDT", "SPOT", reservation_id, None
        ),
        asset="USDT",
        amount=amount,
    )


class AccountReservationTests(unittest.TestCase):
    def test_projection_sums_active_reservations_and_advances_version(self):
        result = project_reservation(
            capacity=capacity(),
            active_reservations=(reservation("deal-1", "20"),),
            reservation_id="deal-2",
            amount="30",
            expected_version=3,
        )

        self.assertEqual(
            result,
            ReservationProjection(
                account_id="account-1",
                asset="USDT",
                version_before=3,
                version_after=4,
                active_reserved="20",
                requested="30",
                available_after="50",
            ),
        )

    def test_capacity_conflict_fails_closed_without_mutation(self):
        with self.assertRaisesRegex(
            AccountReservationError, "ACCOUNT_CAPACITY_CONFLICT"
        ):
            project_reservation(
                capacity=capacity(),
                active_reservations=(reservation("deal-1", "80"),),
                reservation_id="deal-2",
                amount="21",
                expected_version=3,
            )

    def test_stale_version_fails_closed_before_new_reservation(self):
        with self.assertRaisesRegex(AccountReservationError, "ACCOUNT_VERSION_CONFLICT"):
            project_reservation(
                capacity=capacity(version=4),
                active_reservations=(),
                reservation_id="deal-2",
                amount="10",
                expected_version=3,
            )

    def test_cross_account_or_asset_reservation_fails_closed(self):
        foreign = AccountReservation(
            reservation_id="deal-1",
            owner=new_shared_account_identity(
                "account-2", "BTCUSDT", "SPOT", "deal-1", None
            ),
            asset="USDT",
            amount="20",
        )
        with self.assertRaisesRegex(
            AccountReservationError, "ACCOUNT_RESERVATION_SCOPE_CONFLICT"
        ):
            project_reservation(
                capacity=capacity(),
                active_reservations=(foreign,),
                reservation_id="deal-2",
                amount="10",
                expected_version=3,
            )

    def test_duplicate_or_malformed_reservation_fails_closed(self):
        with self.assertRaisesRegex(
            AccountReservationError, "ACCOUNT_RESERVATION_DUPLICATE"
        ):
            project_reservation(
                capacity=capacity(),
                active_reservations=(reservation("deal-1", "20"),),
                reservation_id="deal-1",
                amount="10",
                expected_version=3,
            )


if __name__ == "__main__":
    unittest.main()
