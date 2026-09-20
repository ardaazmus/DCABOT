import hashlib
import json
import sqlite3
import unittest

from dcabot.application.reconciliation import (
    ConnectionState,
    EventDecision,
    OrderLookup,
    UserDataEvent,
)
from dcabot.persistence.reconciliation_journal import (
    DurableReconciliationObservation,
    RECONCILIATION_TABLE_SQL,
    ReconciliationRecordOutcome,
    load_unlocked,
    record_unlocked,
)


class ReconciliationJournalTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript(RECONCILIATION_TABLE_SQL)
        self.event = UserDataEvent.create("stream-1", 100, "executionReport", 777)

    def tearDown(self):
        self.db.close()

    def _observation(self, lookup=None):
        return DurableReconciliationObservation(
            self.event,
            EventDecision.ACCEPTED,
            ConnectionState.CONNECTED_READ_ONLY,
            "binding-1",
            lookup,
        )

    def test_lookup_is_redacted_and_replayed_without_raw_payload(self):
        observation = self._observation(OrderLookup.found(777))

        self.assertEqual(record_unlocked(self.db, observation), ReconciliationRecordOutcome.ACCEPTED)
        row = self.db.execute(
            "SELECT observation_payload FROM reconciliation_events"
        ).fetchone()
        self.assertNotIn("raw_payload", row[0])
        self.assertEqual(load_unlocked(self.db), (observation,))

    def test_lookup_conflict_is_immutable(self):
        first = self._observation(OrderLookup.found(777))
        conflict = self._observation(OrderLookup.found(778))

        self.assertEqual(record_unlocked(self.db, first), ReconciliationRecordOutcome.ACCEPTED)
        self.assertEqual(record_unlocked(self.db, first), ReconciliationRecordOutcome.DUPLICATE)
        with self.assertRaisesRegex(ValueError, "SPOT_RECONCILIATION_EVENT_CONFLICT"):
            record_unlocked(self.db, conflict)
        self.assertEqual(load_unlocked(self.db), (first,))

    def test_legacy_observation_without_lookup_field_remains_readable(self):
        observation = self._observation()
        payload = json.dumps(
            {
                "binding_event_id": observation.binding_event_id,
                "decision": observation.decision.value,
                "event": {
                    "event_id": observation.event.event_id,
                    "event_time_ms": observation.event.event_time_ms,
                    "event_type": observation.event.event_type,
                    "payload_fingerprint": observation.event.payload_fingerprint,
                    "venue_order_id": observation.event.venue_order_id,
                },
                "state": observation.state.value,
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        self.db.execute(
            "INSERT INTO reconciliation_events VALUES (?, ?, ?, ?, ?)",
            (
                1,
                observation.event.event_id,
                observation.binding_event_id,
                payload,
                hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            ),
        )

        self.assertEqual(load_unlocked(self.db), (observation,))


if __name__ == "__main__":
    unittest.main()
