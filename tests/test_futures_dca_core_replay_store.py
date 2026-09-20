from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from dcabot.persistence.futures_dca_core_replay_store import (
    FuturesDcaCoreReplayStorePreflight,
    append_futures_dca_core_replay_receipt,
    load_futures_dca_core_replay_receipts,
    preflight_futures_dca_core_replay_store,
)
from dcabot.application.futures_dca_core_mapping import FuturesDcaCoreReplayReceipt
from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaEconomicPosting,
    FuturesDcaEventEnvelope,
    FuturesDcaProfileRevision,
    FuturesDcaReservationProjection,
    SCHEMA_VERSION,
    append_journal_event,
    append_profile_revision,
    append_reservation_projection,
    create_futures_dca_journal_schema,
)
from dcabot.persistence.futures_dca_release_store import append_futures_dca_fill_release_and_posting_atomic
from dcabot.persistence.futures_dca_release_transition import FuturesDcaReleaseTransition


class FuturesDcaCoreReplayStoreTests(unittest.TestCase):
    def test_current_v4_journal_exposes_receipt_schema_read_only(self):
        with TemporaryDirectory() as directory:
            path = create_futures_dca_journal_schema(Path(directory) / "journal.sqlite")
            before = path.read_bytes()
            self.assertEqual(
                preflight_futures_dca_core_replay_store(path),
                FuturesDcaCoreReplayStorePreflight(
                    "READY", (), "FUTURES_DCA_CORE_REPLAY_RECEIPT_SCHEMA_READY", SCHEMA_VERSION
                ),
            )
            self.assertEqual(path.read_bytes(), before)

    def test_receipt_schema_contract_is_read_only_and_requires_both_unique_scopes(self):
        with TemporaryDirectory() as directory:
            path = create_futures_dca_journal_schema(Path(directory) / "journal.sqlite")
            before = path.read_bytes()
            self.assertEqual(
                preflight_futures_dca_core_replay_store(path),
                FuturesDcaCoreReplayStorePreflight(
                    "READY", (), "FUTURES_DCA_CORE_REPLAY_RECEIPT_SCHEMA_READY", SCHEMA_VERSION
                ),
            )
            self.assertEqual(path.read_bytes(), before)

    def test_malformed_receipt_schema_is_blocked_with_missing_columns(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "journal.sqlite"
            db = sqlite3.connect(path)
            try:
                db.execute("PRAGMA application_id=0x4446444A")
                db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
                db.execute("CREATE TABLE core_replay_receipts(mapping_id TEXT PRIMARY KEY)")
            finally:
                db.close()
            result = preflight_futures_dca_core_replay_store(path)
            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.reason_code, "FUTURES_DCA_CORE_REPLAY_RECEIPT_SCHEMA_INVALID")
            self.assertIn("core_replay_receipts.fingerprint", result.missing_authority)

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
        append_futures_dca_fill_release_and_posting_atomic(path, event, transition, posting)
        return directory, path, FuturesDcaCoreReplayReceipt(
            "mapping-1", "event-2", "posting-1", "event-2", "release-1", 1, "a" * 64
        )

    def test_receipt_append_is_exactly_idempotent_and_loads_after_reopen(self):
        directory, path, receipt = self.prepare()
        try:
            self.assertEqual(append_futures_dca_core_replay_receipt(path, receipt), "ACCEPTED")
            self.assertEqual(append_futures_dca_core_replay_receipt(path, receipt), "DUPLICATE")
            self.assertEqual(load_futures_dca_core_replay_receipts(path), (receipt,))
        finally:
            directory.cleanup()

    def test_receipt_scope_conflict_is_rejected_without_overwrite(self):
        directory, path, receipt = self.prepare()
        try:
            append_futures_dca_core_replay_receipt(path, receipt)
            conflict = FuturesDcaCoreReplayReceipt(
                receipt.mapping_id, receipt.event_id, receipt.posting_id, receipt.transition_event_id,
                receipt.release_identity, receipt.release_cursor, "b" * 64,
            )
            with self.assertRaisesRegex(ValueError, "FUTURES_DCA_CORE_REPLAY_RECEIPT_CONFLICT"):
                append_futures_dca_core_replay_receipt(path, conflict)
            self.assertEqual(load_futures_dca_core_replay_receipts(path), (receipt,))
        finally:
            directory.cleanup()

    def test_receipt_requires_existing_posting_and_release_links(self):
        with TemporaryDirectory() as directory:
            path = create_futures_dca_journal_schema(Path(directory) / "journal.sqlite")
            receipt = FuturesDcaCoreReplayReceipt(
                "mapping-1", "event-1", "posting-1", "event-1", "release-1", 1, "a" * 64
            )
            with self.assertRaisesRegex(ValueError, "FUTURES_DCA_CORE_REPLAY_RECEIPT_EVENT_INVALID"):
                append_futures_dca_core_replay_receipt(path, receipt)


if __name__ == "__main__":
    unittest.main()
