import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from dcabot.application.account_reservation import AccountCapacity
from dcabot.application.account_reservation_ledger import ReservationLedger
from dcabot.application.futures_dca_event_contract import new_futures_dca_fill_event
from dcabot.application.futures_dca_fill_projection import FuturesDcaFill
from dcabot.persistence.futures_dca_event_store import FuturesDcaEventStore


class FuturesDcaAtomicityGateTests(unittest.TestCase):
    def test_failure_after_event_commit_exposes_cross_store_gap(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            event_path = root / "events.sqlite"
            account_path = root / "account.sqlite"
            event = new_futures_dca_fill_event(
                "event-1",
                "deal-1",
                "config-1",
                1,
                FuturesDcaFill("execution-1", 0, "0.1", "100"),
            )
            event_store = FuturesDcaEventStore.create(event_path, "deal-1", "config-1")
            ledger = ReservationLedger(account_path)
            ledger.initialize_capacity(AccountCapacity("account-1", "USDT", "100", 0))
            try:
                self.assertEqual(event_store.append(event), "ACCEPTED")
                with self.assertRaisesRegex(RuntimeError, "injected failure"):
                    raise RuntimeError("injected failure before reservation commit")
            finally:
                event_store.close()
                ledger.close()

            with FuturesDcaEventStore.open(event_path) as reopened_events:
                self.assertEqual(reopened_events.load(), (event,))
            with ReservationLedger(account_path) as reopened_ledger:
                self.assertEqual(
                    reopened_ledger.get_capacity("account-1", "USDT"),
                    AccountCapacity("account-1", "USDT", "100", 0),
                )
                self.assertEqual(reopened_ledger.list_active("account-1", "USDT"), ())


if __name__ == "__main__":
    unittest.main()
