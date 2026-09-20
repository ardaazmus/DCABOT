from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dcabot.application.futures_dca_event_contract import new_futures_dca_fill_event
from dcabot.application.futures_dca_fill_projection import FuturesDcaFill
from dcabot.persistence.futures_dca_event_store import (
    FuturesDcaEventStore,
    FuturesDcaEventStoreError,
)


def event(event_id="event-1", sequence=1, execution_id="execution-1", deal_id="deal-1"):
    return new_futures_dca_fill_event(
        event_id, deal_id, "config-1", sequence, FuturesDcaFill(execution_id, 0, "0.1", "100")
    )


class FuturesDcaEventStoreTests(unittest.TestCase):
    def test_restart_replays_exact_event_history_and_duplicate_is_idempotent(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.sqlite"
            store = FuturesDcaEventStore.create(path, "deal-1", "config-1")
            first = event()
            second = event("event-2", 2, "execution-2")
            self.assertEqual((store.append(first), store.append(second), store.append(first)), ("ACCEPTED", "ACCEPTED", "DUPLICATE"))
            store.close()
            with FuturesDcaEventStore.open(path) as reopened:
                self.assertEqual(reopened.load(), (first, second))

    def test_conflict_scope_and_sequence_fail_closed(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.sqlite"
            with FuturesDcaEventStore.create(path, "deal-1", "config-1") as store:
                store.append(event())
                with self.assertRaisesRegex(FuturesDcaEventStoreError, "FUTURES_DCA_EVENT_CONFLICT"):
                    store.append(event("event-1", 2, "execution-2"))
                with self.assertRaisesRegex(FuturesDcaEventStoreError, "FUTURES_DCA_STORE_SCOPE_CONFLICT"):
                    store.append(event("event-2", 2, "execution-2", "deal-2"))
                with self.assertRaisesRegex(FuturesDcaEventStoreError, "FUTURES_DCA_EVENT_SEQUENCE_INVALID"):
                    store.append(event("event-3", 3, "execution-3"))

    def test_tampered_payload_is_rejected_on_reopen(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.sqlite"
            with FuturesDcaEventStore.create(path, "deal-1", "config-1") as store:
                store.append(event())
                store.db.execute("UPDATE futures_dca_events SET event_payload=?", ("{}",))
            with self.assertRaisesRegex(FuturesDcaEventStoreError, "FUTURES_DCA_STORE_RECORD_CORRUPT"):
                FuturesDcaEventStore.open(path)

    def test_unsupported_store_metadata_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.sqlite"
            with FuturesDcaEventStore.create(path, "deal-1", "config-1") as store:
                store.db.execute("UPDATE metadata SET value='other' WHERE key='scope'")
            with self.assertRaisesRegex(FuturesDcaEventStoreError, "FUTURES_DCA_STORE_METADATA_INVALID"):
                FuturesDcaEventStore.open(path)


if __name__ == "__main__":
    unittest.main()
