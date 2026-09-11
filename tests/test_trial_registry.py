import unittest

from dcabot.application.trial_registry import (
    TrialRecord,
    TrialStatus,
    new_trial_study,
    register_trial,
)


class TrialRegistryTests(unittest.TestCase):
    def test_trial_count_includes_success_failed_and_invalid_trials(self):
        study = new_trial_study(
            "study-1",
            parameter_space_id="space-1",
            objective_id="objective-1",
            selection_rule_id="rule-1",
        )
        for index, status in enumerate(
            (TrialStatus.SUCCEEDED, TrialStatus.FAILED, TrialStatus.INVALID), start=1
        ):
            study, outcome = register_trial(
                study,
                TrialRecord(f"trial-{index}", status),
            )
            self.assertEqual(outcome, "ACCEPTED")

        self.assertEqual(study.trial_count, 3)
        self.assertEqual(
            tuple(trial.status for trial in study.trials),
            (TrialStatus.SUCCEEDED, TrialStatus.FAILED, TrialStatus.INVALID),
        )

    def test_exact_duplicate_is_idempotent_and_conflict_is_rejected(self):
        study = new_trial_study(
            "study-1",
            parameter_space_id="space-1",
            objective_id="objective-1",
            selection_rule_id="rule-1",
        )
        trial = TrialRecord("trial-1", TrialStatus.FAILED)
        study, _ = register_trial(study, trial)

        duplicate, outcome = register_trial(study, trial)
        self.assertEqual((duplicate, outcome), (study, "DUPLICATE"))
        with self.assertRaisesRegex(ValueError, "TRIAL_ID_CONFLICT"):
            register_trial(study, TrialRecord("trial-1", TrialStatus.INVALID))

    def test_registry_is_bounded_and_does_not_select_a_winner(self):
        study = new_trial_study(
            "study-1",
            parameter_space_id="space-1",
            objective_id="objective-1",
            selection_rule_id="rule-1",
            max_trials=2,
        )
        study, _ = register_trial(study, TrialRecord("trial-1", TrialStatus.SUCCEEDED))
        study, _ = register_trial(study, TrialRecord("trial-2", TrialStatus.FAILED))

        with self.assertRaisesRegex(ValueError, "TRIAL_LIMIT_EXCEEDED"):
            register_trial(study, TrialRecord("trial-3", TrialStatus.INVALID))
        self.assertEqual(study.trial_count, 2)
        self.assertFalse(hasattr(study, "winner"))

    def test_invalid_metadata_and_status_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "TRIAL_STATUS_INVALID"):
            TrialRecord("trial-1", "UNKNOWN")
        with self.assertRaisesRegex(ValueError, "TRIAL_STUDY_ID_INVALID"):
            new_trial_study(
                "",
                parameter_space_id="space-1",
                objective_id="objective-1",
                selection_rule_id="rule-1",
            )


if __name__ == "__main__":
    unittest.main()
