from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaEventEnvelope,
    FuturesDcaProfileRevision,
    FuturesDcaReservationProjection,
    append_journal_event,
    append_profile_revision,
    append_reservation_projection,
    create_futures_dca_journal_schema,
    load_reservation_projections,
)
from dcabot.persistence.futures_dca_release_store import (
    append_futures_dca_release_transition,
    load_futures_dca_release_transitions,
)
from dcabot.persistence.futures_dca_release_transition import FuturesDcaReleaseTransition


class FuturesDcaReleaseStoreTests(unittest.TestCase):
    def event(self, event_id, sequence_no, execution_id):
        return FuturesDcaEventEnvelope(
            event_id, sequence_no, execution_id, "order-1", "FILL", "profile-1", 100, 101,
            "1", "100", "100", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}',
        )

    def prepare(self):
        directory = TemporaryDirectory()
        path = create_futures_dca_journal_schema(Path(directory.name) / "journal.sqlite")
        append_profile_revision(path, FuturesDcaProfileRevision(
            "profile-1", "BINANCE", "USD_M_PERPETUAL", "BTCUSDT", "USDT", "ISOLATED", "ONE_WAY", 100,
            "0.001", "fee-1", "slippage-1", "rounding-1",
        ))
        append_journal_event(path, self.event("event-1", 1, "execution-1"))
        append_reservation_projection(path, FuturesDcaReservationProjection(
            "reservation-1", "deal-1", "USDT", "100", "0", "100", None, "OPEN", 0, "event-1",
        ))
        return directory, path

    def transition(self, kind, event_id, cursor, version, consumed, releasable, identity):
        return FuturesDcaReleaseTransition(
            "reservation-1", event_id, identity, cursor, version, kind, consumed, releasable,
        )

    def test_release_update_and_replay_are_atomic_and_idempotent(self):
        directory, path = self.prepare()
        try:
            append_journal_event(path, self.event("event-2", 2, "execution-2"))
            partial = self.transition("PARTIAL_FILL", "event-2", 1, 0, "40", "60", "release-1")
            self.assertEqual(append_futures_dca_release_transition(path, partial), "ACCEPTED")
            self.assertEqual(append_futures_dca_release_transition(path, partial), "DUPLICATE")

            append_journal_event(path, self.event("event-3", 3, "execution-3"))
            canceled = self.transition("CANCEL", "event-3", 2, 1, "40", "60", "release-2")
            self.assertEqual(append_futures_dca_release_transition(path, canceled), "ACCEPTED")
            self.assertEqual(
                load_reservation_projections(path),
                (FuturesDcaReservationProjection(
                    "reservation-1", "deal-1", "USDT", "100", "40", "60", "release-2", "CANCELED", 2, "event-1", 2,
                ),),
            )
            records = load_futures_dca_release_transitions(path)
            self.assertEqual(tuple(record.transition for record in records), (partial, canceled))
            self.assertEqual(tuple(record.target_state for record in records), ("PARTIAL", "CANCELED"))
        finally:
            directory.cleanup()

    def test_release_failure_rolls_back_projection_and_history(self):
        directory, path = self.prepare()
        try:
            append_journal_event(path, self.event("event-2", 2, "execution-2"))
            db = sqlite3.connect(path)
            try:
                db.execute(
                    "CREATE TRIGGER reject_release BEFORE INSERT ON reservation_releases "
                    "BEGIN SELECT RAISE(ABORT, 'injected release failure'); END"
                )
            finally:
                db.close()

            with self.assertRaisesRegex(sqlite3.IntegrityError, "injected release failure"):
                append_futures_dca_release_transition(
                    path, self.transition("PARTIAL_FILL", "event-2", 1, 0, "40", "60", "release-1")
                )
            self.assertEqual(load_reservation_projections(path)[0].terminal_state, "OPEN")
            self.assertEqual(load_futures_dca_release_transitions(path), ())
        finally:
            directory.cleanup()

    def test_cursor_gap_is_rejected_before_durable_update(self):
        directory, path = self.prepare()
        try:
            append_journal_event(path, self.event("event-2", 2, "execution-2"))
            with self.assertRaisesRegex(ValueError, "FUTURES_DCA_RELEASE_CURSOR_INVALID"):
                append_futures_dca_release_transition(
                    path, self.transition("CANCEL", "event-2", 2, 0, "0", "100", "release-2")
                )
            self.assertEqual(load_reservation_projections(path)[0].release_cursor, 0)
            self.assertEqual(load_futures_dca_release_transitions(path), ())
        finally:
            directory.cleanup()


if __name__ == "__main__":
    unittest.main()
