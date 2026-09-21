"""Faz 14.4: PBO/CSCV + DSR skorlayıcı (registry'yi salt-okunur tüketir)."""
import unittest

from dcabot.application.overfitting_probability import (
    OverfittingProbabilityError,
    deflated_sharpe_for_returns,
    probability_of_backtest_overfitting,
)
from dcabot.application.trial_registry import (
    TrialRecord,
    TrialStatus,
    new_trial_study,
    register_trial,
)


def _study():
    study = new_trial_study(
        "study-1",
        parameter_space_id="grid-a",
        objective_id="sharpe",
        selection_rule_id="max",
    )
    study, _ = register_trial(study, TrialRecord(trial_id="cfg-a", status=TrialStatus.SUCCEEDED))
    study, _ = register_trial(study, TrialRecord(trial_id="cfg-b", status=TrialStatus.SUCCEEDED))
    study, _ = register_trial(study, TrialRecord(trial_id="cfg-c", status=TrialStatus.FAILED))
    return study


class ProbabilityOfBacktestOverfittingTests(unittest.TestCase):
    def test_persistent_winner_scores_zero(self):
        study = _study()
        returns = {
            "cfg-a": ("0.10", "0.10", "0.10", "0.10"),
            "cfg-b": ("0.0", "0.0", "0.0", "0.0"),
        }
        self.assertEqual(
            probability_of_backtest_overfitting(study, returns, block_count=2), 0.0
        )

    def test_regime_flipper_scores_one(self):
        study = _study()
        returns = {
            "cfg-a": ("0.10", "0.10", "-0.10", "-0.10"),
            "cfg-b": ("0.0", "0.0", "0.0", "0.0"),
        }
        self.assertEqual(
            probability_of_backtest_overfitting(study, returns, block_count=2), 1.0
        )

    def test_failed_trials_are_ignored_read_only(self):
        study = _study()
        before = study.trials
        returns = {
            "cfg-a": ("0.10", "0.10", "0.10", "0.10"),
            "cfg-b": ("0.0", "0.0", "0.0", "0.0"),
            "cfg-c": ("9.99", "9.99", "9.99", "9.99"),
        }
        score = probability_of_backtest_overfitting(study, returns, block_count=2)
        self.assertEqual(score, 0.0)
        self.assertEqual(study.trials, before)

    def test_single_succeeded_config_raises(self):
        study = new_trial_study(
            "study-1", parameter_space_id="g", objective_id="o", selection_rule_id="r"
        )
        study, _ = register_trial(study, TrialRecord(trial_id="only", status=TrialStatus.SUCCEEDED))
        with self.assertRaises(OverfittingProbabilityError):
            probability_of_backtest_overfitting(study, {"only": ("0.1", "0.1")}, block_count=2)

    def test_ragged_or_odd_blocks_raise(self):
        study = _study()
        with self.assertRaises(OverfittingProbabilityError):
            probability_of_backtest_overfitting(
                study,
                {"cfg-a": ("0.1", "0.1"), "cfg-b": ("0.1",)},
                block_count=2,
            )
        with self.assertRaises(OverfittingProbabilityError):
            probability_of_backtest_overfitting(
                study,
                {"cfg-a": ("0.1", "0.1", "0.1"), "cfg-b": ("0.1", "0.1", "0.1")},
                block_count=2,
            )


class DeflatedSharpeForReturnsTests(unittest.TestCase):
    def test_converts_at_boundary_and_scores(self):
        score = deflated_sharpe_for_returns(("0.01", "0.02", "0.03", "0.04"), n_trials=1)
        self.assertGreater(score, 0.5)
        self.assertLessEqual(score, 1.0)

    def test_rejects_non_finite_strings(self):
        with self.assertRaises(OverfittingProbabilityError):
            deflated_sharpe_for_returns(("0.01", "abc"), n_trials=1)
