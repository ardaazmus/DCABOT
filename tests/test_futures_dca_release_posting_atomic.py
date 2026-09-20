from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaEconomicPosting,
    FuturesDcaEventEnvelope,
    FuturesDcaProfileRevision,
    FuturesDcaReservationProjection,
    append_journal_event,
    append_profile_revision,
    append_reservation_projection,
    create_futures_dca_journal_schema,
    load_economic_postings,
    load_journal_events,
    load_reservation_projections,
)
from dcabot.persistence.futures_dca_release_store import (
    append_futures_dca_fill_release_and_posting_atomic,
    load_futures_dca_release_transitions,
)
from dcabot.persistence.futures_dca_release_transition import FuturesDcaReleaseTransition


class FuturesDcaReleasePostingAtomicTests(unittest.TestCase):
    def event(self, event_id, sequence_no, execution_id, gross_commitment="40"):
        return FuturesDcaEventEnvelope(
            event_id, sequence_no, execution_id, "order-1", "FILL", "profile-1", 100, 101,
            "0.4", "100", gross_commitment, "0", "USDT", "slippage-1", "rounding-1",
            '{"source":"offline"}',
        )

    def prepare(self):
        directory = TemporaryDirectory()
        path = create_futures_dca_journal_schema(Path(directory.name) / "journal.sqlite")
        append_profile_revision(path, FuturesDcaProfileRevision(
            "profile-1", "BINANCE", "USD_M_PERPETUAL", "BTCUSDT", "USDT", "ISOLATED", "ONE_WAY", 100,
            "0.001", "fee-1", "slippage-1", "rounding-1",
        ))
        first = FuturesDcaEventEnvelope(
            "event-1", 1, "execution-1", "order-1", "FILL", "profile-1", 100, 101,
            "1", "100", "100", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}',
        )
        append_journal_event(path, first)
        append_reservation_projection(path, FuturesDcaReservationProjection(
            "reservation-1", "deal-1", "USDT", "100", "0", "100", None, "OPEN", 0, "event-1",
        ))
        return directory, path

    def transition(self, kind="PARTIAL_FILL", consumed="40", releasable="60"):
        return FuturesDcaReleaseTransition(
            "reservation-1", "event-2", "release-1", 1, 0, kind, consumed, releasable,
        )

    def posting(self, commitment="40"):
        return FuturesDcaEconomicPosting("posting-1", "event-2", 1, commitment, "0", "0", "PROJECTED")

    def test_fill_release_and_posting_are_atomic_and_idempotent(self):
        directory, path = self.prepare()
        try:
            event = self.event("event-2", 2, "execution-2")
            self.assertEqual(
                append_futures_dca_fill_release_and_posting_atomic(path, event, self.transition(), self.posting()),
                "ACCEPTED",
            )
            self.assertEqual(
                append_futures_dca_fill_release_and_posting_atomic(path, event, self.transition(), self.posting()),
                "DUPLICATE",
            )
            self.assertEqual(load_journal_events(path), (load_journal_events(path)[0], event))
            self.assertEqual(load_reservation_projections(path)[0].terminal_state, "PARTIAL")
            self.assertEqual(load_futures_dca_release_transitions(path)[0].transition, self.transition())
            self.assertEqual(load_economic_postings(path), (self.posting(),))
        finally:
            directory.cleanup()

    def test_posting_failure_rolls_back_event_release_and_reservation(self):
        directory, path = self.prepare()
        try:
            db = sqlite3.connect(path)
            try:
                db.execute(
                    "CREATE TRIGGER reject_posting BEFORE INSERT ON economic_postings "
                    "BEGIN SELECT RAISE(ABORT, 'injected posting failure'); END"
                )
            finally:
                db.close()

            with self.assertRaisesRegex(sqlite3.IntegrityError, "injected posting failure"):
                append_futures_dca_fill_release_and_posting_atomic(
                    path, self.event("event-2", 2, "execution-2"), self.transition(), self.posting()
                )
            self.assertEqual(len(load_journal_events(path)), 1)
            self.assertEqual(load_reservation_projections(path)[0].terminal_state, "OPEN")
            self.assertEqual(load_futures_dca_release_transitions(path), ())
            self.assertEqual(load_economic_postings(path), ())
        finally:
            directory.cleanup()

    def test_fill_binding_rejects_nonfill_and_amount_mismatch_before_write(self):
        directory, path = self.prepare()
        try:
            with self.assertRaisesRegex(ValueError, "FUTURES_DCA_RELEASE_POSTING_TRANSITION_INVALID"):
                append_futures_dca_fill_release_and_posting_atomic(
                    path, self.event("event-2", 2, "execution-2"), self.transition("CANCEL", "0", "100"),
                    self.posting("40"),
                )
            with self.assertRaisesRegex(ValueError, "FUTURES_DCA_RELEASE_POSTING_AMOUNT_MISMATCH"):
                append_futures_dca_fill_release_and_posting_atomic(
                    path, self.event("event-2", 2, "execution-2", "30"), self.transition(), self.posting("30")
                )
            self.assertEqual(len(load_journal_events(path)), 1)
            self.assertEqual(load_futures_dca_release_transitions(path), ())
            self.assertEqual(load_economic_postings(path), ())
        finally:
            directory.cleanup()


if __name__ == "__main__":
    unittest.main()
