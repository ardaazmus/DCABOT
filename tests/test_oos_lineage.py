import unittest

from dcabot.application.oos_lineage import (
    EvaluationLineage,
    OosStatus,
    OosTuningDecision,
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

    def test_public_models_reject_string_subclass_equality_bypasses(self):
        class StringEqualsTo(str):
            def __eq__(self, other):
                return True

        with self.assertRaisesRegex(ValueError, "OOS_EXPERIMENT_ID_INVALID"):
            EvaluationLineage(StringEqualsTo("experiment-1"))
        with self.assertRaisesRegex(ValueError, "OOS_STATUS_INVALID"):
            EvaluationLineage("experiment-1", StringEqualsTo(OosStatus.OOS_UNTOUCHED))
        with self.assertRaisesRegex(ValueError, "OOS_OUTCOME_INVALID"):
            OosTuningDecision(
                lineage=new_evaluation_lineage("experiment-1"),
                outcome=StringEqualsTo("TUNING_ALLOWED"),
            )

        class MalformedLineage(EvaluationLineage):
            def __post_init__(self):
                pass

        malformed = MalformedLineage(
            "experiment-1", StringEqualsTo(OosStatus.OOS_UNTOUCHED)
        )
        with self.assertRaisesRegex(ValueError, "OOS_LINEAGE_INVALID"):
            inspect_oos(malformed)
        with self.assertRaisesRegex(ValueError, "OOS_LINEAGE_INVALID"):
            request_tuning(malformed)
        with self.assertRaisesRegex(ValueError, "OOS_LINEAGE_INVALID"):
            OosTuningDecision(lineage=malformed, outcome="TUNING_ALLOWED")


if __name__ == "__main__":
    unittest.main()
