import json
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dcabot.application.futures_dca_core_mapping import (
    assess_futures_dca_core_fill_admission,
    assess_futures_dca_core_fill_replay,
    build_futures_dca_core_mapping_candidate,
    build_futures_dca_core_replay_receipt,
)
from dcabot.application.futures_dca_core_replay_oracle import (
    assess_futures_dca_core_replay_restart_oracle,
)
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply
from dcabot.persistence.futures_dca_core_replay_store import (
    load_futures_dca_core_replay_receipts,
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


class FuturesDcaCoreReplayOracleTests(unittest.TestCase):
    def setUp(self):
        config_path = Path(__file__).resolve().parents[1] / "config/paper.json"
        self.config = Config.parse(json.loads(config_path.read_text()))

    def prepare(self):
        directory = TemporaryDirectory()
        path = create_futures_dca_journal_schema(Path(directory.name) / "journal.sqlite")
        append_profile_revision(path, FuturesDcaProfileRevision(
            "profile-1", "BINANCE", "USD_M_PERPETUAL", "BTCUSDT", "USDT", "ISOLATED", "ONE_WAY", 100,
            "0.001", "fee-1", "slippage-1", "rounding-1",
        ))
        append_journal_event(path, FuturesDcaEventEnvelope(
            "event-1", 1, "execution-1", "order-1", "FILL", "profile-1", 100, 101,
            "1", "100", "40", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}',
        ))
        append_reservation_projection(path, FuturesDcaReservationProjection(
            "reservation-1", "deal-1", "USDT", "40", "0", "40", None, "OPEN", 0, "event-1",
        ))
        event = FuturesDcaEventEnvelope(
            "event-2", 2, "execution-2", "venue-order-1", "FILL", "profile-1", 100, 101,
            "0.4", "100", "40", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}',
        )
        posting = FuturesDcaEconomicPosting("posting-1", "event-2", 1, "40", "0", "0", "PROJECTED")
        transition = FuturesDcaReleaseTransition(
            "reservation-1", "event-2", "release-1", 1, 0, "FULL_FILL", "40", "0",
        )
        mapping = build_futures_dca_core_mapping_candidate(
            event,
            posting,
            mapping_id="mapping-1",
            profile_revision_id="profile-1",
            core_order_id="core-order-1",
            core_order_intent_id="core-intent-1",
            role="BASE",
            side="BUY",
            limit_price="100",
        )
        state = apply(State(), {"type": "MARK", "price": "100"}, self.config)
        state = apply(
            state,
            {
                "type": "INTENT",
                "order_id": "core-order-1",
                "intent_id": "core-intent-1",
                "role": "BASE",
                "qty": "1",
                "limit_price": "100",
            },
            self.config,
        )
        reservation = FuturesDcaReservationProjection(
            "reservation-1", "deal-1", "USDT", "40", "0", "40", None, "OPEN", 0, "event-1",
        )
        admission = assess_futures_dca_core_fill_admission(
            event, posting, mapping, state, self.config
        )
        pure_decision = assess_futures_dca_core_fill_replay(
            event, posting, transition, reservation, mapping, admission, state, self.config
        )
        receipt = build_futures_dca_core_replay_receipt(
            event, posting, transition, mapping, pure_decision
        )
        return (
            directory, path, event, posting, transition, reservation, mapping,
            state, admission, pure_decision, receipt,
        )

    def test_restart_oracle_matches_pure_projection_and_is_read_only(self):
        (
            directory, path, event, posting, transition, reservation, mapping,
            state, admission, pure_decision, receipt,
        ) = self.prepare()
        try:
            append_futures_dca_core_replay_receipt_atomic(
                path, event, transition, posting, receipt
            )
            before = path.read_bytes()
            result = assess_futures_dca_core_replay_restart_oracle(
                path, event, posting, transition, reservation, mapping, admission, state, self.config
            )
            self.assertEqual(result.status, "READY")
            self.assertEqual(result.reason_code, "FUTURES_DCA_CORE_REPLAY_ORACLE_READY")
            self.assertEqual(result.receipt, receipt)
            self.assertEqual(result.decision.status, "ACCEPTED")
            self.assertEqual(result.decision, pure_decision)
            self.assertEqual(path.read_bytes(), before)
        finally:
            directory.cleanup()

    def test_restart_oracle_blocks_when_receipt_is_missing(self):
        (
            directory, path, event, posting, transition, reservation, mapping,
            state, admission, _, _,
        ) = self.prepare()
        try:
            append_futures_dca_fill_release_and_posting_atomic(
                path, event, transition, posting
            )
            before = path.read_bytes()
            result = assess_futures_dca_core_replay_restart_oracle(
                path, event, posting, transition, reservation, mapping, admission, state, self.config
            )
            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.reason_code, "FUTURES_DCA_CORE_REPLAY_ORACLE_RECEIPT_MISSING")
            self.assertEqual(result.decision, None)
            self.assertEqual(result.receipt, None)
            self.assertEqual(load_futures_dca_core_replay_receipts(path), ())
            self.assertEqual(path.read_bytes(), before)
        finally:
            directory.cleanup()

    def test_restart_oracle_blocks_when_core_admission_is_stale(self):
        (
            directory, path, event, posting, transition, reservation, mapping,
            state, admission, _, receipt,
        ) = self.prepare()
        try:
            append_futures_dca_core_replay_receipt_atomic(
                path, event, transition, posting, receipt
            )
            result = assess_futures_dca_core_replay_restart_oracle(
                path, event, posting, transition, reservation, mapping, admission,
                State(), self.config
            )
            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.reason_code, "FUTURES_DCA_CORE_REPLAY_ADMISSION_STALE")
            self.assertIsNone(result.decision)
            self.assertIsNone(result.receipt)
        finally:
            directory.cleanup()

    def test_restart_oracle_blocks_when_posting_checksum_is_corrupt(self):
        (
            directory, path, event, posting, transition, reservation, mapping,
            state, admission, _, receipt,
        ) = self.prepare()
        try:
            append_futures_dca_core_replay_receipt_atomic(
                path, event, transition, posting, receipt
            )
            db = sqlite3.connect(path)
            try:
                db.execute(
                    "UPDATE economic_postings SET checksum=? WHERE posting_id=?",
                    ("0" * 64, posting.posting_id),
                )
                db.commit()
            finally:
                db.close()
            result = assess_futures_dca_core_replay_restart_oracle(
                path, event, posting, transition, reservation, mapping, admission, state, self.config
            )
            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(
                result.reason_code,
                "FUTURES_DCA_CORE_REPLAY_ORACLE_DURABLE_CORRUPT",
            )
        finally:
            directory.cleanup()

    def test_restart_oracle_blocks_when_reservation_projection_is_corrupt(self):
        (
            directory, path, event, posting, transition, reservation, mapping,
            state, admission, _, receipt,
        ) = self.prepare()
        try:
            append_futures_dca_core_replay_receipt_atomic(
                path, event, transition, posting, receipt
            )
            db = sqlite3.connect(path)
            try:
                db.execute(
                    "UPDATE reservations SET releasable_amount=? WHERE reservation_id=?",
                    ("1", reservation.reservation_id),
                )
                db.commit()
            finally:
                db.close()
            result = assess_futures_dca_core_replay_restart_oracle(
                path, event, posting, transition, reservation, mapping, admission, state, self.config
            )
            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(
                result.reason_code,
                "FUTURES_DCA_CORE_REPLAY_ORACLE_DURABLE_CORRUPT",
            )
        finally:
            directory.cleanup()

    def test_restart_oracle_blocks_when_receipt_fingerprint_conflicts(self):
        (
            directory, path, event, posting, transition, reservation, mapping,
            state, admission, _, receipt,
        ) = self.prepare()
        try:
            append_futures_dca_core_replay_receipt_atomic(
                path, event, transition, posting, receipt
            )
            db = sqlite3.connect(path)
            try:
                db.execute(
                    "UPDATE core_replay_receipts SET fingerprint=? WHERE fingerprint=?",
                    ("0" * 64, receipt.fingerprint),
                )
                db.commit()
            finally:
                db.close()
            result = assess_futures_dca_core_replay_restart_oracle(
                path, event, posting, transition, reservation, mapping, admission, state, self.config
            )
            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(
                result.reason_code,
                "FUTURES_DCA_CORE_REPLAY_ORACLE_RECEIPT_CONFLICT",
            )
        finally:
            directory.cleanup()


if __name__ == "__main__":
    unittest.main()
