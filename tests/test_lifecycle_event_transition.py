import unittest

from dcabot.application.deal_lifecycle import (
    DealLifecycleError,
    new_deal_lifecycle,
)
from dcabot.application.lifecycle_event_contract import new_lifecycle_event
from dcabot.application.lifecycle_event_transition import apply_lifecycle_event


class LifecycleEventTransitionTests(unittest.TestCase):
    def test_accepted_event_advances_projection_and_history_once(self):
        lifecycle = new_deal_lifecycle("deal-1", "config-revision-1")
        start = new_lifecycle_event(
            "event-1", "deal-1", "config-revision-1", "START", 1
        )
        pause = new_lifecycle_event(
            "event-2", "deal-1", "config-revision-1", "PAUSE", 2
        )

        lifecycle, history, first_outcome = apply_lifecycle_event(
            lifecycle, (), start
        )
        lifecycle, history, second_outcome = apply_lifecycle_event(
            lifecycle, history, pause
        )

        self.assertEqual(lifecycle.status, "PAUSED")
        self.assertEqual(lifecycle.event_sequence, 2)
        self.assertEqual(history, (start, pause))
        self.assertEqual(first_outcome, "ACCEPTED")
        self.assertEqual(second_outcome, "ACCEPTED")

    def test_exact_duplicate_does_not_advance_projection_or_history(self):
        lifecycle = new_deal_lifecycle("deal-1", "config-revision-1")
        start = new_lifecycle_event(
            "event-1", "deal-1", "config-revision-1", "START", 1
        )

        lifecycle, history, _ = apply_lifecycle_event(lifecycle, (), start)
        duplicate_lifecycle, duplicate_history, outcome = apply_lifecycle_event(
            lifecycle, history, start
        )

        self.assertEqual(duplicate_lifecycle, lifecycle)
        self.assertEqual(duplicate_history, history)
        self.assertEqual(outcome, "DUPLICATE")

    def test_invalid_transition_does_not_append_event(self):
        lifecycle = new_deal_lifecycle("deal-1", "config-revision-1")
        resume = new_lifecycle_event(
            "event-1", "deal-1", "config-revision-1", "RESUME", 1
        )

        with self.assertRaisesRegex(DealLifecycleError, "LIFECYCLE_TRANSITION_INVALID"):
            apply_lifecycle_event(lifecycle, (), resume)

        self.assertEqual(lifecycle.status, "DRAFT")
        self.assertEqual(lifecycle.event_sequence, 0)


if __name__ == "__main__":
    unittest.main()
