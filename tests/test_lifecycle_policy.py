import unittest

from dcabot.application.deal_lifecycle import DealLifecycleError, new_deal_lifecycle
from dcabot.application.lifecycle_event_contract import new_lifecycle_event
from dcabot.application.lifecycle_event_transition import apply_lifecycle_event
from dcabot.application.lifecycle_policy import (
    LifecyclePolicyError,
    cooldown_allows_new_deal,
)


class LifecyclePolicyTests(unittest.TestCase):
    def test_terminal_lifecycle_rejects_later_event_without_mutation(self):
        terminal_cases = (
            ("COMPLETE", "COMPLETED"),
            ("ABORT", "ABORTED"),
            ("FAIL", "FAILED"),
        )

        for terminal_event, expected_status in terminal_cases:
            with self.subTest(terminal_event=terminal_event):
                lifecycle = new_deal_lifecycle("deal-1", "config-revision-1")
                start = new_lifecycle_event(
                    "event-1", "deal-1", "config-revision-1", "START", 1
                )
                lifecycle, history, _ = apply_lifecycle_event(
                    lifecycle, (), start
                )
                terminal = new_lifecycle_event(
                    "event-2", "deal-1", "config-revision-1", terminal_event, 2
                )
                lifecycle, history, _ = apply_lifecycle_event(
                    lifecycle, history, terminal
                )
                later = new_lifecycle_event(
                    "event-3", "deal-1", "config-revision-1", "PAUSE", 3
                )

                with self.assertRaisesRegex(
                    DealLifecycleError, "LIFECYCLE_TRANSITION_INVALID"
                ):
                    apply_lifecycle_event(lifecycle, history, later)

                self.assertEqual(lifecycle.status, expected_status)
                self.assertEqual(lifecycle.event_sequence, 2)
                self.assertEqual(history, (start, terminal))

    def test_cooldown_uses_effective_time_and_inclusive_boundary(self):
        self.assertFalse(cooldown_allows_new_deal(1_000, 1_099, 100))
        self.assertTrue(cooldown_allows_new_deal(1_000, 1_100, 100))
        self.assertTrue(cooldown_allows_new_deal(1_000, 1_000, 0))

    def test_cooldown_rejects_invalid_duration_and_time_order(self):
        with self.assertRaisesRegex(LifecyclePolicyError, "COOLDOWN_INVALID"):
            cooldown_allows_new_deal(1_000, 1_100, -1)

        with self.assertRaisesRegex(
            LifecyclePolicyError, "COOLDOWN_TIME_ORDER_INVALID"
        ):
            cooldown_allows_new_deal(1_000, 999, 0)


if __name__ == "__main__":
    unittest.main()
