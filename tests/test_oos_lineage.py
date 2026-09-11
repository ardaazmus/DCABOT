import unittest

from dcabot.application.oos_lineage import (
    OosStatus,
    inspect_oos,
    new_evaluation_lineage,
    request_tuning,
)


class OosLineageTests(unittest.TestCase):
    def test_inspecting_oos_freezes_that_lineage(self):
        lineage = new_evaluation_lineage("experiment-1")
        inspected = inspect_oos(lineage)

        self.assertEqual(inspected.status, OosStatus.OOS_INSPECTED)
        self.assertEqual(lineage.status, OosStatus.OOS_UNTOUCHED)

    def test_tuning_before_oos_inspection_is_allowed_without_touching_oos(self):
        lineage = new_evaluation_lineage("experiment-1")

        decision = request_tuning(lineage)

        self.assertEqual(decision.lineage, lineage)
        self.assertEqual(decision.outcome, "TUNING_ALLOWED")

    def test_tuning_after_oos_inspection_marks_old_lineage_touched(self):
        inspected = inspect_oos(new_evaluation_lineage("experiment-1"))

        decision = request_tuning(inspected)

        self.assertEqual(decision.lineage.status, OosStatus.TOUCHED)
        self.assertEqual(decision.outcome, "NEW_EXPERIMENT_REQUIRED")
        self.assertEqual(decision.lineage.experiment_id, "experiment-1")

    def test_touched_lineage_cannot_be_presented_as_untouched_again(self):
        touched = request_tuning(
            inspect_oos(new_evaluation_lineage("experiment-1"))
        ).lineage

        with self.assertRaisesRegex(ValueError, "OOS_LINEAGE_TRANSITION_INVALID"):
            inspect_oos(touched)


if __name__ == "__main__":
    unittest.main()
