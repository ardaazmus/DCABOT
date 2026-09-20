from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from dcabot.persistence.futures_dca_journal_schema import (
    APPLICATION_ID,
    SCHEMA_VERSION,
    FuturesDcaProfileRevision,
    FuturesDcaEventEnvelope,
    FuturesDcaReservationProjection,
    FuturesDcaJournalSchemaError,
    append_journal_event,
    append_event_and_reservation_atomic,
    append_profile_revision,
    append_reservation_projection,
    create_futures_dca_journal_schema,
    load_journal_events,
    load_profile_revisions,
    load_reservation_projections,
)


class FuturesDcaJournalSchemaTests(unittest.TestCase):
    def profile(self, contract_size="0.001"):
        return FuturesDcaProfileRevision(
            "profile-1", "BINANCE", "USD_M_PERPETUAL", "BTCUSDT", "USDT", "ISOLATED", "ONE_WAY", 100, contract_size,
            "fee-1", "slippage-1", "rounding-1",
        )

    def event(self, event_id="event-1", sequence_no=1, state="ACCEPTED", execution_id="execution-1"):
        return FuturesDcaEventEnvelope(
            event_id, sequence_no, execution_id, "order-1", "FILL", "profile-1", 100, 101,
            "1", "100", "100", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}', state,
        )

    def reservation(self, reservation_id="reservation-1", source_event_id="event-1", reserved_amount="100"):
        return FuturesDcaReservationProjection(
            reservation_id, "deal-1", "USDT", reserved_amount, "0", reserved_amount,
            None, "OPEN", 0, source_event_id,
        )

    def test_empty_v1_schema_has_all_atomic_owners_and_stays_inert(self):
        with TemporaryDirectory() as directory:
            path = create_futures_dca_journal_schema(Path(directory) / "journal.sqlite")
            db = sqlite3.connect(path)
            try:
                self.assertEqual(db.execute("PRAGMA application_id").fetchone(), (APPLICATION_ID,))
                self.assertEqual(db.execute("PRAGMA user_version").fetchone(), (SCHEMA_VERSION,))
                self.assertEqual(
                    {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")},
                    {
                        "journal_metadata",
                        "profile_revisions",
                        "journal_events",
                        "reservations",
                        "reservation_releases",
                        "economic_postings",
                        "core_replay_receipts",
                    },
                )
                self.assertEqual(db.execute("SELECT value FROM journal_metadata WHERE key='activation'").fetchone(), ("INERT_UNBOUND",))
                self.assertEqual(db.execute("SELECT COUNT(*) FROM profile_revisions").fetchone(), (0,))
                self.assertEqual(db.execute("SELECT COUNT(*) FROM journal_events").fetchone(), (0,))
            finally:
                db.close()

    def test_existing_file_is_never_overwritten(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "journal.sqlite"
            path.write_text("sentinel", encoding="utf-8")
            with self.assertRaisesRegex(FuturesDcaJournalSchemaError, "FUTURES_DCA_JOURNAL_EXISTS"):
                create_futures_dca_journal_schema(path)
            self.assertEqual(path.read_text(encoding="utf-8"), "sentinel")

    def test_profile_revision_is_exactly_idempotent_and_replayable(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "journal.sqlite"
            create_futures_dca_journal_schema(path)
            profile = self.profile()

            self.assertEqual(append_profile_revision(path, profile), "ACCEPTED")
            self.assertEqual(append_profile_revision(path, profile), "DUPLICATE")
            self.assertEqual(load_profile_revisions(path), (self.profile("0.001"),))

    def test_profile_revision_conflict_and_invalid_contract_size_fail_closed(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "journal.sqlite"
            create_futures_dca_journal_schema(path)
            append_profile_revision(path, self.profile())

            with self.assertRaisesRegex(FuturesDcaJournalSchemaError, "FUTURES_DCA_PROFILE_CONFLICT"):
                append_profile_revision(path, self.profile("1"))
            with self.assertRaisesRegex(FuturesDcaJournalSchemaError, "FUTURES_DCA_PROFILE_INVALID"):
                append_profile_revision(path, self.profile("0"))

    def test_event_envelope_is_profile_bound_idempotent_and_replayable(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "journal.sqlite"
            create_futures_dca_journal_schema(path)
            append_profile_revision(path, self.profile())
            event = self.event()

            self.assertEqual(append_journal_event(path, event), "ACCEPTED")
            self.assertEqual(append_journal_event(path, event), "DUPLICATE")
            self.assertEqual(load_journal_events(path), (event,))

    def test_event_sequence_identity_profile_and_payload_fail_closed(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "journal.sqlite"
            create_futures_dca_journal_schema(path)
            append_profile_revision(path, self.profile())
            append_journal_event(path, self.event())

            with self.assertRaisesRegex(FuturesDcaJournalSchemaError, "FUTURES_DCA_EVENT_CONFLICT"):
                append_journal_event(path, self.event(event_id="event-1", state="UNKNOWN"))
            with self.assertRaisesRegex(FuturesDcaJournalSchemaError, "FUTURES_DCA_EVENT_SEQUENCE_INVALID"):
                append_journal_event(path, self.event(event_id="event-2", sequence_no=3, execution_id="execution-2"))
            with self.assertRaisesRegex(FuturesDcaJournalSchemaError, "FUTURES_DCA_EVENT_PROFILE_MISSING"):
                append_journal_event(path, FuturesDcaEventEnvelope(
                    "event-2", 2, "execution-2", "order-1", "FILL", "missing", 100, 101,
                    "1", "100", "100", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}',
                ))

    def test_reservation_projection_is_exactly_idempotent_and_replayable(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "journal.sqlite"
            create_futures_dca_journal_schema(path)
            append_profile_revision(path, self.profile())
            append_journal_event(path, self.event())
            reservation = self.reservation()

            self.assertEqual(append_reservation_projection(path, reservation), "ACCEPTED")
            self.assertEqual(append_reservation_projection(path, reservation), "DUPLICATE")
            self.assertEqual(load_reservation_projections(path), (reservation,))

    def test_reservation_projection_conflict_negative_and_missing_event_fail_closed(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "journal.sqlite"
            create_futures_dca_journal_schema(path)
            append_profile_revision(path, self.profile())
            append_journal_event(path, self.event())
            append_reservation_projection(path, self.reservation())

            with self.assertRaisesRegex(FuturesDcaJournalSchemaError, "FUTURES_DCA_RESERVATION_CONFLICT"):
                append_reservation_projection(path, self.reservation(reserved_amount="101"))
            with self.assertRaisesRegex(FuturesDcaJournalSchemaError, "FUTURES_DCA_RESERVATION_INVALID"):
                append_reservation_projection(path, self.reservation(reserved_amount="-1"))
            with self.assertRaisesRegex(FuturesDcaJournalSchemaError, "FUTURES_DCA_RESERVATION_EVENT_MISSING"):
                append_reservation_projection(path, self.reservation(source_event_id="missing-event"))

    def test_event_and_reservation_atomic_append_is_idempotent(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "journal.sqlite"
            create_futures_dca_journal_schema(path)
            append_profile_revision(path, self.profile())
            event = self.event()
            reservation = self.reservation()

            self.assertEqual(append_event_and_reservation_atomic(path, event, reservation), "ACCEPTED")
            self.assertEqual(append_event_and_reservation_atomic(path, event, reservation), "DUPLICATE")
            self.assertEqual(load_journal_events(path), (event,))
            self.assertEqual(load_reservation_projections(path), (reservation,))

    def test_atomic_append_rolls_back_event_when_reservation_insert_fails(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "journal.sqlite"
            create_futures_dca_journal_schema(path)
            append_profile_revision(path, self.profile())
            db = sqlite3.connect(path)
            try:
                db.execute(
                    "CREATE TRIGGER reject_reservation BEFORE INSERT ON reservations "
                    "BEGIN SELECT RAISE(ABORT, 'injected reservation failure'); END"
                )
            finally:
                db.close()

            with self.assertRaisesRegex(sqlite3.IntegrityError, "injected reservation failure"):
                append_event_and_reservation_atomic(path, self.event(), self.reservation())
            self.assertEqual(load_journal_events(path), ())
            self.assertEqual(load_reservation_projections(path), ())


if __name__ == "__main__":
    unittest.main()
