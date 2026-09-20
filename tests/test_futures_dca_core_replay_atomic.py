from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from dcabot.application.futures_dca_core_mapping import FuturesDcaCoreReplayReceipt
from dcabot.persistence.futures_dca_core_replay_store import load_futures_dca_core_replay_receipts
from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaEconomicPosting,
    FuturesDcaEventEnvelope,
    FuturesDcaProfileRevision,
    FuturesDcaReservationProjection,
    append_journal_event,
    append_profile_revision,
    append_reservation_projection,
    create_futures_dca_journal_schema,
    load_journal_events,
    load_economic_postings,
    load_reservation_projections,
)
from dcabot.persistence.futures_dca_release_store import (
    append_futures_dca_core_replay_receipt_atomic,
    load_futures_dca_release_transitions,
)
from dcabot.persistence.futures_dca_release_transition import FuturesDcaReleaseTransition


class FuturesDcaCoreReplayAtomicTests(unittest.TestCase):
    def prepare(self):
        directory = TemporaryDirectory()
        path = create_futures_dca_journal_schema(Path(directory.name) / "journal.sqlite")
        append_profile_revision(path, FuturesDcaProfileRevision(
            "profile-1", "BINANCE", "USD_M_PERPETUAL", "BTCUSDT", "USDT", "ISOLATED", "ONE_WAY", 100,
            "0.001", "fee-1", "slippage-1", "rounding-1",
        ))
        append_journal_event(path, FuturesDcaEventEnvelope(
            "event-1", 1, "execution-1", "order-1", "FILL", "profile-1", 100, 101,
            "1", "100", "100", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}',
        ))
        append_reservation_projection(path, FuturesDcaReservationProjection(
            "reservation-1", "deal-1", "USDT", "100", "0", "100", None, "OPEN", 0, "event-1",
        ))
        event = FuturesDcaEventEnvelope(
            "event-2", 2, "execution-2", "order-1", "FILL", "profile-1", 100, 101,
            "0.4", "100", "40", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}',
        )
        transition = FuturesDcaReleaseTransition(
            "reservation-1", "event-2", "release-1", 1, 0, "PARTIAL_FILL", "40", "60",
        )
        posting = FuturesDcaEconomicPosting("posting-1", "event-2", 1, "40", "0", "0", "PROJECTED")
        receipt = FuturesDcaCoreReplayReceipt(
            "mapping-1", "event-2", "posting-1", "event-2", "release-1", 1, "a" * 64
        )
        return directory, path, event, transition, posting, receipt

    def test_event_release_posting_and_receipt_are_one_idempotent_transaction(self):
        directory, path, event, transition, posting, receipt = self.prepare()
        try:
            self.assertEqual(
                append_futures_dca_core_replay_receipt_atomic(
                    path, event, transition, posting, receipt
                ),
                "ACCEPTED",
            )
            self.assertEqual(
                append_futures_dca_core_replay_receipt_atomic(
                    path, event, transition, posting, receipt
                ),
                "DUPLICATE",
            )
            self.assertEqual(load_futures_dca_core_replay_receipts(path), (receipt,))
        finally:
            directory.cleanup()

    def test_receipt_failure_rolls_back_event_release_posting_and_reservation(self):
        directory, path, event, transition, posting, receipt = self.prepare()
        try:
            db = sqlite3.connect(path)
            try:
                db.execute(
                    "CREATE TRIGGER reject_receipt BEFORE INSERT ON core_replay_receipts "
                    "BEGIN SELECT RAISE(ABORT, 'injected receipt failure'); END"
                )
            finally:
                db.close()

            with self.assertRaisesRegex(sqlite3.IntegrityError, "injected receipt failure"):
                append_futures_dca_core_replay_receipt_atomic(
                    path, event, transition, posting, receipt
                )
            self.assertEqual(len(load_journal_events(path)), 1)
            self.assertEqual(load_futures_dca_release_transitions(path), ())
            self.assertEqual(load_economic_postings(path), ())
            self.assertEqual(load_reservation_projections(path)[0].terminal_state, "OPEN")
            self.assertEqual(load_futures_dca_core_replay_receipts(path), ())
        finally:
            directory.cleanup()

    def test_receipt_scope_mismatch_is_rejected_before_any_write(self):
        directory, path, event, transition, posting, receipt = self.prepare()
        try:
            conflict = FuturesDcaCoreReplayReceipt(
                receipt.mapping_id, receipt.event_id, "other-posting", receipt.transition_event_id,
                receipt.release_identity, receipt.release_cursor, "b" * 64,
            )
            with self.assertRaisesRegex(ValueError, "FUTURES_DCA_CORE_REPLAY_RECEIPT_SCOPE_CONFLICT"):
                append_futures_dca_core_replay_receipt_atomic(
                    path, event, transition, posting, conflict
                )
            self.assertEqual(len(load_journal_events(path)), 1)
            self.assertEqual(load_futures_dca_release_transitions(path), ())
            self.assertEqual(load_economic_postings(path), ())
            self.assertEqual(load_futures_dca_core_replay_receipts(path), ())
        finally:
            directory.cleanup()


if __name__ == "__main__":
    unittest.main()
