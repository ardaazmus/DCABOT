import unittest

from dcabot.application.deal_lifecycle import (
    DealLifecycleError,
    copy_deal_lifecycle,
    new_deal_lifecycle,
    transition_deal_lifecycle,
)


class DealLifecycleTests(unittest.TestCase):
    def test_declarative_lifecycle_transition_table_preserves_config_revision(self):
        cases = (
            ("DRAFT", "START", "RUNNING"),
            ("RUNNING", "PAUSE", "PAUSED"),
            ("PAUSED", "RESUME", "RUNNING"),
            ("RUNNING", "COMPLETE", "COMPLETED"),
            ("DRAFT", "ABORT", "ABORTED"),
            ("DRAFT", "FAIL", "FAILED"),
            ("RUNNING", "ABORT", "ABORTED"),
            ("RUNNING", "FAIL", "FAILED"),
            ("PAUSED", "ABORT", "ABORTED"),
            ("PAUSED", "FAIL", "FAILED"),
        )

        for initial_status, event, expected_status in cases:
            with self.subTest(initial_status=initial_status, event=event):
                lifecycle = new_deal_lifecycle("deal-1", "config-revision-1")
                if initial_status != "DRAFT":
                    lifecycle = transition_deal_lifecycle(lifecycle, "START")
                if initial_status == "PAUSED":
                    lifecycle = transition_deal_lifecycle(lifecycle, "PAUSE")

                result = transition_deal_lifecycle(lifecycle, event)

                self.assertEqual(result.status, expected_status)
                self.assertEqual(result.deal_id, "deal-1")
                self.assertEqual(result.config_revision_id, "config-revision-1")
                self.assertEqual(result.event_sequence, lifecycle.event_sequence + 1)

    def test_invalid_transition_is_rejected_without_mutating_lifecycle(self):
        lifecycle = new_deal_lifecycle("deal-1", "config-revision-1")

        with self.assertRaisesRegex(DealLifecycleError, "LIFECYCLE_TRANSITION_INVALID"):
            transition_deal_lifecycle(lifecycle, "RESUME")

        self.assertEqual(lifecycle.status, "DRAFT")
        self.assertEqual(lifecycle.event_sequence, 0)

    def test_copy_creates_a_new_draft_without_mutating_source_lifecycle(self):
        source = transition_deal_lifecycle(
            new_deal_lifecycle("deal-1", "config-revision-1"), "START"
        )

        copied = copy_deal_lifecycle(
            source,
            new_deal_id="deal-2",
            new_config_revision_id="config-revision-2",
        )

        self.assertEqual(source.status, "RUNNING")
        self.assertEqual(source.deal_id, "deal-1")
        self.assertEqual(source.config_revision_id, "config-revision-1")
        self.assertEqual(source.event_sequence, 1)
        self.assertEqual(copied.deal_id, "deal-2")
        self.assertEqual(copied.config_revision_id, "config-revision-2")
        self.assertEqual(copied.status, "DRAFT")
        self.assertEqual(copied.event_sequence, 0)

    def test_copy_rejects_source_deal_or_config_revision_identity_reuse(self):
        source = new_deal_lifecycle("deal-1", "config-revision-1")

        with self.assertRaisesRegex(DealLifecycleError, "COPY_DEAL_ID_REUSED"):
            copy_deal_lifecycle(
                source,
                new_deal_id="deal-1",
                new_config_revision_id="config-revision-2",
            )
        with self.assertRaisesRegex(DealLifecycleError, "COPY_CONFIG_REVISION_ID_REUSED"):
            copy_deal_lifecycle(
                source,
                new_deal_id="deal-2",
                new_config_revision_id="config-revision-1",
            )


if __name__ == "__main__":
    unittest.main()
