"""F6.1: durable two-leg journal — crash/replay/recovery evidence (LCR-09)."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from dcabot.application.hedge_two_leg_contract import (
    HedgeTwoLegError,
    TwoLegState,
    new_hedge_position_identity,
)
from dcabot.application.two_leg_fill_projection import LegFill
from dcabot.persistence.two_leg_journal import TwoLegJournal, TwoLegJournalError


def _identity(side):
    return new_hedge_position_identity(
        account_id="acct-1",
        venue_profile="BINANCE-SPOT",
        product_id="BTCUSDT",
        symbol="BTCUSDT",
        position_mode="HEDGE",
        hedge_side=side,
    )


def _fill(fill_id, leg, side, quantity, status, t_us):
    return LegFill(
        fill_id=fill_id,
        leg_id=leg,
        position=_identity(side),
        quantity=quantity,
        fill_status=status,
        event_time_us=t_us,
    )


class TwoLegJournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "two_leg.db"

    def tearDown(self):
        self.tmp.cleanup()

    def test_crash_after_leg_a_commit_replays_one_leg_filled(self):
        with TwoLegJournal(self.path) as journal:
            self.assertEqual(journal.start("sess-1"), "CREATED")
            fill = _fill("f-a1", "A", "LONG", "0.5", "FULL", 1000)
            self.assertEqual(journal.accept_fill("sess-1", fill), "ACCEPTED")
        # "crash": fresh instance over the same file
        with TwoLegJournal(self.path) as journal:
            projection = journal.replay("sess-1")
        self.assertEqual(projection.state, TwoLegState.ONE_LEG_FILLED)
        self.assertEqual(projection.leg_a_quantity, "0.5")
        self.assertEqual(projection.leg_a_status, "FULL")
        self.assertEqual(projection.leg_b_quantity, "0")
        self.assertEqual(projection.leg_b_status, "NONE")
        self.assertEqual(projection.fills, (fill,))
        self.assertIsNone(projection.leg_b_identity)

    def test_duplicate_fill_is_idempotent(self):
        with TwoLegJournal(self.path) as journal:
            journal.start("sess-1")
            fill = _fill("f-a1", "A", "LONG", "1", "FULL", 1000)
            self.assertEqual(journal.accept_fill("sess-1", fill), "ACCEPTED")
            self.assertEqual(journal.accept_fill("sess-1", fill), "DUPLICATE")
            self.assertEqual(journal.replay("sess-1").fills, (fill,))

    def test_conflicting_fill_id_rejected(self):
        with TwoLegJournal(self.path) as journal:
            journal.start("sess-1")
            journal.accept_fill("sess-1", _fill("f-a1", "A", "LONG", "1", "FULL", 1000))
            with self.assertRaises(TwoLegJournalError) as ctx:
                journal.accept_fill("sess-1", _fill("f-a1", "A", "LONG", "2", "FULL", 1000))
            self.assertEqual(ctx.exception.code, "TWO_LEG_JOURNAL_FILL_CONFLICT")

    def test_leg_b_before_leg_a_fails_closed(self):
        with TwoLegJournal(self.path) as journal:
            journal.start("sess-1")
            with self.assertRaises(HedgeTwoLegError):
                journal.accept_fill("sess-1", _fill("f-b1", "B", "SHORT", "1", "FULL", 1000))
            # negative expectation: no synthetic hedge without policy
            projection = journal.replay("sess-1")
            self.assertEqual(projection.state, TwoLegState.LEG_A_PENDING)
            self.assertEqual(projection.fills, ())

    def test_recovery_is_terminal_and_operator_owned(self):
        with TwoLegJournal(self.path) as journal:
            journal.start("sess-1")
            journal.accept_fill("sess-1", _fill("f-a1", "A", "LONG", "1", "FULL", 1000))
            projection = journal.mark_recovery("sess-1")
            self.assertEqual(projection.state, TwoLegState.RECOVERY_REQUIRED)
            self.assertEqual(projection.leg_a_quantity, "1")
            with self.assertRaises(HedgeTwoLegError):
                journal.accept_fill("sess-1", _fill("f-b1", "B", "SHORT", "1", "FULL", 2000))
            self.assertEqual(journal.replay("sess-1").state, TwoLegState.RECOVERY_REQUIRED)

    def test_timeout_from_pending_is_terminal(self):
        with TwoLegJournal(self.path) as journal:
            journal.start("sess-1")
            projection = journal.mark_timeout("sess-1")
            self.assertEqual(projection.state, TwoLegState.TIMEOUT)
            self.assertEqual(projection.fills, ())

    def test_timeout_on_unknown_session_rejected(self):
        with TwoLegJournal(self.path) as journal:
            with self.assertRaises(TwoLegJournalError) as ctx:
                journal.mark_timeout("nope")
            self.assertEqual(ctx.exception.code, "TWO_LEG_JOURNAL_UNKNOWN_SESSION")

    def test_both_legs_established_replay_exact(self):
        with TwoLegJournal(self.path) as journal:
            journal.start("sess-1")
            journal.accept_fill("sess-1", _fill("f-a1", "A", "LONG", "1.5", "FULL", 1000))
            journal.accept_fill("sess-1", _fill("f-b1", "B", "SHORT", "1.5", "FULL", 2000))
            projection = journal.replay("sess-1")
        self.assertEqual(projection.state, TwoLegState.BOTH_ESTABLISHED)
        self.assertEqual(projection.leg_a_quantity, "1.5")
        self.assertEqual(projection.leg_b_quantity, "1.5")

    def test_partial_leg_a_replays_partial_hedge(self):
        with TwoLegJournal(self.path) as journal:
            journal.start("sess-1")
            journal.accept_fill("sess-1", _fill("f-a1", "A", "LONG", "0.25", "PARTIAL", 1000))
            projection = journal.replay("sess-1")
        self.assertEqual(projection.state, TwoLegState.PARTIAL_HEDGE)
        self.assertEqual(projection.leg_a_quantity, "0.25")

    def test_wrong_types_fail_closed(self):
        with TwoLegJournal(self.path) as journal:
            with self.assertRaises(TwoLegJournalError):
                journal.start(123)  # type: ignore[arg-type]
            journal.start("sess-1")
            with self.assertRaises(HedgeTwoLegError):
                journal.accept_fill("sess-1", object())  # type: ignore[arg-type]

    def test_foreign_database_rejected(self):
        db = sqlite3.connect(self.path)
        db.execute("CREATE TABLE other (id INTEGER PRIMARY KEY)")
        db.execute("PRAGMA application_id=12345")
        db.commit()
        db.close()
        with self.assertRaises(TwoLegJournalError):
            TwoLegJournal(self.path)

    def test_replay_unknown_session_rejected(self):
        with TwoLegJournal(self.path) as journal:
            with self.assertRaises(TwoLegJournalError) as ctx:
                journal.replay("ghost")
            self.assertEqual(ctx.exception.code, "TWO_LEG_JOURNAL_UNKNOWN_SESSION")


if __name__ == "__main__":
    unittest.main()
