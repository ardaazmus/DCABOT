from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dcabot.application.futures_dca_core_mapping import FuturesDcaCoreReplayReceipt
from dcabot.application.futures_dca_recovery_capability import (
    FuturesDcaProfileRecoveryCapability,
    assess_futures_dca_profile_recovery,
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


class FuturesDcaRecoveryCapabilityTests(unittest.TestCase):
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

    def test_profile_recovery_is_ready_but_core_admission_stays_blocked(self):
        directory, path = self.prepare(with_receipt=True)
        try:
            before = path.read_bytes()
            self.assertEqual(
                assess_futures_dca_profile_recovery(path, "profile-1"),
                FuturesDcaProfileRecoveryCapability(
                    "profile-1", "READY", "BLOCKED",
                    ("core_order_intent", "limit_price", "role", "side"),
                    "FUTURES_DCA_PROFILE_RECOVERY_READY_CORE_ADMISSION_BLOCKED", 2, 1, 1,
                ),
            )
            self.assertEqual(path.read_bytes(), before)
        finally:
            directory.cleanup()

    def test_missing_receipt_blocks_profile_recovery(self):
        directory, path = self.prepare(with_receipt=False)
        try:
            result = assess_futures_dca_profile_recovery(path, "profile-1")
            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.reason_code, "FUTURES_DCA_PROFILE_RECOVERY_RECEIPT_MISSING")
            self.assertEqual(result.receipt_count, 0)
        finally:
            directory.cleanup()

    def test_unknown_profile_is_blocked_without_journal_write(self):
        directory, path = self.prepare(with_receipt=True)
        try:
            before = path.read_bytes()
            result = assess_futures_dca_profile_recovery(path, "profile-unknown")
            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.reason_code, "FUTURES_DCA_PROFILE_RECOVERY_PROFILE_MISSING")
            self.assertEqual(path.read_bytes(), before)
        finally:
            directory.cleanup()

    def test_corrupt_profile_is_fail_closed(self):
        directory, path = self.prepare(with_receipt=True)
        try:
            import sqlite3

            db = sqlite3.connect(path)
            try:
                db.execute("UPDATE profile_revisions SET profile_hash=?", ("0" * 64,))
                db.commit()
            finally:
                db.close()
            result = assess_futures_dca_profile_recovery(path, "profile-1")
            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.reason_code, "FUTURES_DCA_PROFILE_RECOVERY_DURABLE_INVALID")
        finally:
            directory.cleanup()


if __name__ == "__main__":
    unittest.main()
