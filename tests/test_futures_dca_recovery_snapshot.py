from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from dcabot.application.futures_dca_core_mapping import FuturesDcaCoreReplayReceipt
from dcabot.application.futures_dca_recovery_snapshot import (
    FuturesDcaProfileRecoverySnapshot,
    project_futures_dca_profile_recovery_snapshot,
)
from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaEconomicPosting,
    FuturesDcaEventEnvelope,
    FuturesDcaProfileRevision,
    FuturesDcaReservationProjection,
    append_journal_event,
    append_profile_revision,
    append_reservation_projection,
    create_futures_dca_journal_schema,
)
from dcabot.persistence.futures_dca_release_store import (
    append_futures_dca_core_replay_receipt_atomic,
    append_futures_dca_fill_release_and_posting_atomic,
)
from dcabot.persistence.futures_dca_release_transition import FuturesDcaReleaseTransition


class FuturesDcaRecoverySnapshotTests(unittest.TestCase):
    def prepare(self, *, with_receipt: bool):
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
        if with_receipt:
            append_futures_dca_core_replay_receipt_atomic(
                path,
                event,
                transition,
                posting,
                FuturesDcaCoreReplayReceipt(
                    "mapping-1", "event-2", "posting-1", "event-2", "release-1", 1, "a" * 64,
                ),
            )
        else:
            append_futures_dca_fill_release_and_posting_atomic(path, event, transition, posting)
        return directory, path

    def test_snapshot_projects_deterministic_profile_lineage_read_only(self):
        directory, path = self.prepare(with_receipt=True)
        try:
            before = path.read_bytes()
            self.assertEqual(
                project_futures_dca_profile_recovery_snapshot(path, "profile-1", "profile-1"),
                FuturesDcaProfileRecoverySnapshot(
                    "profile-1", "READY", "BLOCKED",
                    "FUTURES_DCA_RECOVERY_SNAPSHOT_READY_CORE_ADMISSION_BLOCKED",
                    ("core_order_intent", "limit_price", "role", "side"),
                    ("event-1", "event-2"), ("posting-1",), ("release-1",), ("a" * 64,),
                ),
            )
            self.assertEqual(path.read_bytes(), before)
        finally:
            directory.cleanup()

    def test_stale_profile_is_quarantined_without_projecting_lineage(self):
        directory, path = self.prepare(with_receipt=True)
        try:
            append_profile_revision(path, FuturesDcaProfileRevision(
                "profile-2", "BINANCE", "USD_M_PERPETUAL", "BTCUSDT", "USDT", "ISOLATED", "ONE_WAY", 200,
                "0.001", "fee-2", "slippage-2", "rounding-2",
            ))
            result = project_futures_dca_profile_recovery_snapshot(path, "profile-1", "profile-2")
            self.assertEqual(result.status, "QUARANTINED")
            self.assertEqual(result.reason_code, "FUTURES_DCA_RECOVERY_SNAPSHOT_PROFILE_STALE")
            self.assertEqual(result.event_ids, ())
        finally:
            directory.cleanup()

    def test_missing_receipt_blocks_snapshot_projection(self):
        directory, path = self.prepare(with_receipt=False)
        try:
            result = project_futures_dca_profile_recovery_snapshot(path, "profile-1", "profile-1")
            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.reason_code, "FUTURES_DCA_PROFILE_RECOVERY_RECEIPT_MISSING")
            self.assertEqual(result.event_ids, ())
        finally:
            directory.cleanup()

    def test_corrupt_profile_is_quarantined_as_durable_invalid(self):
        directory, path = self.prepare(with_receipt=True)
        try:
            db = sqlite3.connect(path)
            try:
                db.execute("UPDATE profile_revisions SET profile_hash=?", ("0" * 64,))
                db.commit()
            finally:
                db.close()
            result = project_futures_dca_profile_recovery_snapshot(path, "profile-1", "profile-1")
            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.reason_code, "FUTURES_DCA_RECOVERY_SNAPSHOT_DURABLE_INVALID")
        finally:
            directory.cleanup()


if __name__ == "__main__":
    unittest.main()
