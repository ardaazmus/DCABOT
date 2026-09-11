import unittest

from dcabot.application.lifecycle_event_contract import (
    LifecycleEventContractError,
    accept_lifecycle_event,
    new_lifecycle_event,
)


class LifecycleEventContractTests(unittest.TestCase):
    def test_new_events_are_scoped_and_sequential(self):
        first = new_lifecycle_event(
            "event-1", "deal-1", "config-revision-1", "START", 1
        )
        second = new_lifecycle_event(
            "event-2", "deal-1", "config-revision-1", "PAUSE", 2
        )

        history, first_outcome = accept_lifecycle_event((), first)
        history, second_outcome = accept_lifecycle_event(history, second)

        self.assertEqual(history, (first, second))
        self.assertEqual(first_outcome, "ACCEPTED")
        self.assertEqual(second_outcome, "ACCEPTED")

    def test_exact_duplicate_is_idempotent_and_conflicting_duplicate_is_rejected(self):
        event = new_lifecycle_event(
            "event-1", "deal-1", "config-revision-1", "START", 1
        )
        history, _ = accept_lifecycle_event((), event)

        duplicate_history, duplicate_outcome = accept_lifecycle_event(history, event)
        self.assertEqual(duplicate_history, history)
        self.assertEqual(duplicate_outcome, "DUPLICATE")

        conflicting = new_lifecycle_event(
            "event-1", "deal-1", "config-revision-1", "FAIL", 1
        )
        with self.assertRaisesRegex(
            LifecycleEventContractError, "LIFECYCLE_EVENT_CONFLICT"
        ):
            accept_lifecycle_event(history, conflicting)
        self.assertEqual(history, (event,))

    def test_scope_and_sequence_violations_are_rejected(self):
        first = new_lifecycle_event(
            "event-1", "deal-1", "config-revision-1", "START", 1
        )
        history, _ = accept_lifecycle_event((), first)

        wrong_scope = new_lifecycle_event(
            "event-2", "deal-2", "config-revision-1", "PAUSE", 2
        )
        with self.assertRaisesRegex(
            LifecycleEventContractError, "LIFECYCLE_EVENT_SCOPE_CONFLICT"
        ):
            accept_lifecycle_event(history, wrong_scope)

        sequence_gap = new_lifecycle_event(
            "event-2", "deal-1", "config-revision-1", "PAUSE", 4
        )
        with self.assertRaisesRegex(
            LifecycleEventContractError, "LIFECYCLE_EVENT_SEQUENCE_INVALID"
        ):
            accept_lifecycle_event(history, sequence_gap)


if __name__ == "__main__":
    unittest.main()
