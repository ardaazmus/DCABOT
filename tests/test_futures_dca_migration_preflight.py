from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dcabot.application.account_reservation import AccountCapacity
from dcabot.application.account_reservation_ledger import ReservationLedger
from dcabot.application.futures_dca_event_contract import new_futures_dca_fill_event
from dcabot.application.futures_dca_fill_projection import FuturesDcaFill
from dcabot.application.futures_dca_migration_preflight import inspect_futures_dca_migration_sources
from dcabot.persistence.futures_dca_event_store import FuturesDcaEventStore


class FuturesDcaMigrationPreflightTests(unittest.TestCase):
    def test_current_split_stores_fail_closed_without_creating_migration_target(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            event_path = root / "events.sqlite"
            account_path = root / "account.sqlite"
            with FuturesDcaEventStore.create(event_path, "deal-1", "config-1") as events:
                events.append(
                    new_futures_dca_fill_event(
                        "event-1", "deal-1", "config-1", 1, FuturesDcaFill("execution-1", 0, "1", "100")
                    )
                )
                with ReservationLedger(account_path) as ledger:
                    ledger.initialize_capacity(AccountCapacity("account-1", "USDT", "100", 0))
                    result = inspect_futures_dca_migration_sources(events, ledger)

            self.assertEqual(result.status, "NO_GO")
            self.assertIn("profile.contract_size", result.missing_fields)
            self.assertIn("event.order_id", result.missing_fields)
            self.assertIn("execution.fee_amount", result.missing_fields)
            self.assertIn("reservation.release_identity", result.missing_fields)
            self.assertIn("reservation.version", result.missing_fields)
            self.assertIn("posting.funding_amount", result.missing_fields)
            self.assertIn("posting.posting_cursor", result.missing_fields)
            self.assertFalse((root / "futures_dca_journal_v1.sqlite").exists())


if __name__ == "__main__":
    unittest.main()
