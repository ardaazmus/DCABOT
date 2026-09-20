import unittest

from dcabot.persistence.futures_dca_journal_schema import FuturesDcaReservationProjection
from dcabot.persistence.futures_dca_release_transition import (
    FuturesDcaReleaseTransition,
    FuturesDcaReleaseTransitionError,
    apply_futures_dca_release_transition,
)


class FuturesDcaReleaseTransitionTests(unittest.TestCase):
    def reservation(self, state="OPEN", consumed="0", releasable="100", version=0, cursor=0, identity=None):
        return FuturesDcaReservationProjection(
            "reservation-1", "deal-1", "USDT", "100", consumed, releasable,
            identity, state, version, "event-1", cursor,
        )

    def transition(self, kind, *, cursor=1, version=0, consumed="0", releasable="100", identity="release-1"):
        return FuturesDcaReleaseTransition(
            "reservation-1", "event-2", identity, cursor, version, kind, consumed, releasable,
        )

    def test_partial_then_cancel_conserves_amounts_and_cursor(self):
        partial, outcome = apply_futures_dca_release_transition(
            self.reservation(), self.transition("PARTIAL_FILL", consumed="40", releasable="60")
        )
        self.assertEqual(outcome, "ACCEPTED")
        self.assertEqual(partial.terminal_state, "PARTIAL")
        self.assertEqual((partial.consumed_amount, partial.releasable_amount, partial.release_cursor), ("40", "60", 1))

        canceled, outcome = apply_futures_dca_release_transition(
            partial,
            self.transition("CANCEL", cursor=2, version=1, consumed="40", releasable="60", identity="release-2"),
        )
        self.assertEqual(outcome, "ACCEPTED")
        self.assertEqual(canceled.terminal_state, "CANCELED")
        self.assertEqual((canceled.consumed_amount, canceled.releasable_amount, canceled.release_cursor), ("40", "60", 2))

    def test_full_fill_and_late_fill_quarantine_are_explicit(self):
        released, outcome = apply_futures_dca_release_transition(
            self.reservation(), self.transition("FULL_FILL", consumed="100", releasable="0")
        )
        self.assertEqual(outcome, "ACCEPTED")
        self.assertEqual(released.terminal_state, "RELEASED")

        quarantined, outcome = apply_futures_dca_release_transition(
            released,
            self.transition("LATE_FILL", cursor=2, version=1, consumed="100", releasable="0", identity="release-2"),
        )
        self.assertEqual(outcome, "ACCEPTED")
        self.assertEqual(quarantined.terminal_state, "QUARANTINED")
        self.assertEqual((quarantined.consumed_amount, quarantined.releasable_amount), ("100", "0"))

    def test_unknown_does_not_invent_economic_release_and_duplicate_is_idempotent(self):
        quarantined, outcome = apply_futures_dca_release_transition(
            self.reservation(), self.transition("UNKNOWN", identity="release-unknown")
        )
        self.assertEqual(outcome, "ACCEPTED")
        self.assertEqual((quarantined.terminal_state, quarantined.consumed_amount, quarantined.releasable_amount), ("QUARANTINED", "0", "100"))

        duplicate, outcome = apply_futures_dca_release_transition(
            quarantined, self.transition("UNKNOWN", identity="release-unknown")
        )
        self.assertEqual((duplicate, outcome), (quarantined, "DUPLICATE"))

    def test_cursor_gap_conflict_and_terminal_transition_fail_closed(self):
        partial, _ = apply_futures_dca_release_transition(
            self.reservation(), self.transition("PARTIAL_FILL", consumed="40", releasable="60")
        )
        with self.assertRaisesRegex(FuturesDcaReleaseTransitionError, "FUTURES_DCA_RELEASE_CONFLICT"):
            apply_futures_dca_release_transition(
                partial, self.transition("PARTIAL_FILL", consumed="50", releasable="50")
            )
        with self.assertRaisesRegex(FuturesDcaReleaseTransitionError, "FUTURES_DCA_RELEASE_CURSOR_INVALID"):
            apply_futures_dca_release_transition(
                self.reservation(), self.transition("CANCEL", cursor=2, identity="release-2")
            )
        with self.assertRaisesRegex(FuturesDcaReleaseTransitionError, "FUTURES_DCA_RELEASE_CONSERVATION"):
            apply_futures_dca_release_transition(
                self.reservation(), self.transition("PARTIAL_FILL", consumed="10", releasable="80")
            )
        with self.assertRaisesRegex(FuturesDcaReleaseTransitionError, "FUTURES_DCA_RELEASE_TRANSITION_INVALID"):
            apply_futures_dca_release_transition(
                self.reservation(state="CANCELED", consumed="40", releasable="60", version=1, cursor=1, identity="release-1"),
                self.transition("PARTIAL_FILL", cursor=2, version=1, consumed="50", releasable="50", identity="release-2"),
            )


if __name__ == "__main__":
    unittest.main()
