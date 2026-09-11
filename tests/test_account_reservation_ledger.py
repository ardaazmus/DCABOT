import tempfile
import unittest
from pathlib import Path
import sqlite3

from dcabot.application.account_reservation import AccountCapacity, AccountReservation
from dcabot.application.account_reservation_ledger import (
    ReservationCommit,
    ReservationLedger,
)
from dcabot.application.shared_account_identity import new_shared_account_identity


def capacity(version=0):
    return AccountCapacity(
        account_id="account-1", asset="USDT", amount="100", version=version
    )


def reservation(reservation_id="reservation-1", amount="30"):
    return AccountReservation(
        reservation_id=reservation_id,
        owner=new_shared_account_identity(
            "account-1", "BTCUSDT", "SPOT", "deal-1", None
        ),
        asset="USDT",
        amount=amount,
    )


class AccountReservationLedgerTests(unittest.TestCase):
    def test_existing_unrelated_sqlite_file_is_not_adopted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unrelated.sqlite"
            db = sqlite3.connect(path)
            try:
                db.execute("CREATE TABLE user_data(value TEXT NOT NULL)")
                db.execute("INSERT INTO user_data(value) VALUES ('keep')")
                db.commit()
            finally:
                db.close()

            with self.assertRaisesRegex(ValueError, "ACCOUNT_LEDGER_UNSUPPORTED"):
                ReservationLedger(path)

            db = sqlite3.connect(path)
            try:
                self.assertEqual(
                    db.execute("SELECT value FROM user_data").fetchone(), ("keep",)
                )
            finally:
                db.close()

    def test_reservation_commit_reopens_with_exact_active_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "account.sqlite"
            ledger = ReservationLedger(path)
            ledger.initialize_capacity(capacity())

            result = ledger.reserve(reservation(), expected_version=0)

            self.assertEqual(
                result,
                ReservationCommit(
                    reservation_id="reservation-1",
                    account_id="account-1",
                    asset="USDT",
                    amount="30",
                    version_before=0,
                    version_after=1,
                    active_reserved_after="30",
                    available_after="70",
                ),
            )
            ledger.close()

            reopened = ReservationLedger(path)
            self.assertEqual(reopened.get_capacity("account-1", "USDT"), capacity(1))
            self.assertEqual(reopened.list_active("account-1", "USDT"), (reservation(),))
            reopened.close()

    def test_exact_duplicate_is_idempotent_and_conflicting_duplicate_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = ReservationLedger(Path(directory) / "account.sqlite")
            ledger.initialize_capacity(capacity())

            first = ledger.reserve(reservation(), expected_version=0)
            duplicate = ledger.reserve(reservation(), expected_version=1)

            self.assertEqual(duplicate, first)
            self.assertEqual(ledger.get_capacity("account-1", "USDT"), capacity(1))
            with self.assertRaisesRegex(
                ValueError, "ACCOUNT_RESERVATION_DUPLICATE_CONFLICT"
            ):
                ledger.reserve(reservation(amount="31"), expected_version=1)
            ledger.close()

    def test_failed_stale_or_over_capacity_reservation_does_not_mutate_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = ReservationLedger(Path(directory) / "account.sqlite")
            ledger.initialize_capacity(capacity())
            ledger.reserve(reservation(), expected_version=0)

            with self.assertRaisesRegex(ValueError, "ACCOUNT_VERSION_CONFLICT"):
                ledger.reserve(
                    reservation("reservation-2", "20"), expected_version=0
                )
            with self.assertRaisesRegex(ValueError, "ACCOUNT_CAPACITY_CONFLICT"):
                ledger.reserve(
                    reservation("reservation-2", "71"), expected_version=1
                )

            self.assertEqual(ledger.get_capacity("account-1", "USDT"), capacity(1))
            self.assertEqual(ledger.list_active("account-1", "USDT"), (reservation(),))
            ledger.close()

    def test_second_ledger_instance_cannot_commit_a_stale_account_version(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "account.sqlite"
            first_ledger = ReservationLedger(path)
            first_ledger.initialize_capacity(capacity())
            second_ledger = ReservationLedger(path)

            first_ledger.reserve(reservation(), expected_version=0)
            with self.assertRaisesRegex(ValueError, "ACCOUNT_VERSION_CONFLICT"):
                second_ledger.reserve(
                    reservation("reservation-2", "20"), expected_version=0
                )
            second = second_ledger.reserve(
                reservation("reservation-2", "20"), expected_version=1
            )

            self.assertEqual(second.active_reserved_after, "50")
            self.assertEqual(second_ledger.get_capacity("account-1", "USDT"), capacity(2))
            first_ledger.close()
            second_ledger.close()


if __name__ == "__main__":
    unittest.main()
