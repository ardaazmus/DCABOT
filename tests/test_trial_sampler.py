"""Faz 14.6: sampler arayüzü (yerleşik random/grid + opsiyonel Optuna ask-tell).

Sampler YALNIZ öneri üretir; deneme kaydı ve sonuç her zaman
trial_registry'dedir (tek doğruluk kaynağı). Optuna kurulu değilse
adaptör açık hatayla reddeder; yerleşik sampler'lar stdlib-only'dir.
"""
import unittest

from dcabot.application.trial_registry import TrialStatus, new_trial_study, register_trial
from dcabot.application.trial_sampler import (
    GridSampler,
    RandomSampler,
    StudySpace,
    TrialSamplerError,
    suggest_trial_params,
)


def _space() -> StudySpace:
    return StudySpace(
        {
            "take_profit": {"kind": "float", "low": 0.01, "high": 0.05},
            "safety_count": {"kind": "int", "low": 1, "high": 3},
            "mode": {"kind": "categorical", "choices": ("A", "B")},
        }
    )


class StudySpaceTests(unittest.TestCase):
    def test_valid_space_reports_params(self):
        space = _space()
        self.assertEqual(space.param_names(), ("take_profit", "safety_count", "mode"))

    def test_bad_definitions_raise(self):
        with self.assertRaises(TrialSamplerError):
            StudySpace({})
        with self.assertRaises(TrialSamplerError):
            StudySpace({"x": {"kind": "float", "low": 1.0, "high": 1.0}})
        with self.assertRaises(TrialSamplerError):
            StudySpace({"x": {"kind": "categorical", "choices": ()}})
        with self.assertRaises(TrialSamplerError):
            StudySpace({"x": {"kind": "weird", "low": 0, "high": 1}})


class RandomSamplerTests(unittest.TestCase):
    def test_seed_makes_suggestions_deterministic(self):
        first = RandomSampler(seed=7).suggest(_space())
        second = RandomSampler(seed=7).suggest(_space())
        self.assertEqual(first, second)

    def test_suggestions_respect_bounds(self):
        sampler = RandomSampler(seed=1)
        for _ in range(50):
            params = sampler.suggest(_space())
            self.assertTrue(0.01 <= params["take_profit"] <= 0.05)
            self.assertIn(params["safety_count"], (1, 2, 3))
            self.assertIn(params["mode"], ("A", "B"))

    def test_observe_accepts_outcome_without_changing_contract(self):
        sampler = RandomSampler(seed=1)
        sampler.observe("t1", 0.5)
        self.assertTrue(0.01 <= sampler.suggest(_space())["take_profit"] <= 0.05)


class GridSamplerTests(unittest.TestCase):
    def test_exhausts_cartesian_product_then_repeats(self):
        space = StudySpace(
            {
                "a": {"kind": "int", "low": 1, "high": 2},
                "b": {"kind": "categorical", "choices": ("x", "y")},
            }
        )
        sampler = GridSampler()
        seen = [tuple(sorted(sampler.suggest(space).items())) for _ in range(4)]
        self.assertEqual(len(set(seen)), 4)
        fifth = tuple(sorted(sampler.suggest(space).items()))
        self.assertIn(fifth, seen)

    def test_float_grid_uses_three_points(self):
        space = StudySpace({"f": {"kind": "float", "low": 0.0, "high": 1.0}})
        sampler = GridSampler()
        values = sorted(sampler.suggest(space)["f"] for _ in range(3))
        self.assertEqual(values, [0.0, 0.5, 1.0])


class RegistryLoopTests(unittest.TestCase):
    def test_suggest_register_observe_loop_keeps_registry_truth(self):
        from dcabot.application.trial_registry import TrialRecord

        space = _space()
        sampler = RandomSampler(seed=3)
        study = new_trial_study("s", parameter_space_id="p", objective_id="o", selection_rule_id="r")
        params = suggest_trial_params(sampler, space)
        study, outcome = register_trial(study, TrialRecord(trial_id="t1", status=TrialStatus.SUCCEEDED))
        self.assertEqual(outcome, "ACCEPTED")
        sampler.observe("t1", 1.2)
        self.assertEqual(len(study.trials), 1)
        self.assertEqual(study.trials[0].trial_id, "t1")
        self.assertIn("take_profit", params)


class OptunaSamplerTests(unittest.TestCase):
    def test_missing_optuna_fails_with_clear_message(self):
        try:
            import optuna  # noqa: F401
        except ImportError:
            from dcabot.application.trial_sampler import OptunaSampler

            with self.assertRaises(TrialSamplerError) as ctx:
                OptunaSampler()
            self.assertEqual(ctx.exception.code, "SAMPLER_OPTUNA_MISSING")
        else:
            self.skipTest("optuna kurulu; eksiklik yolu bu ortamda test edilemez.")

    def test_ask_tell_roundtrip_when_available(self):
        try:
            import optuna  # noqa: F401
        except ImportError:
            self.skipTest("optuna kurulu değil.")
        from dcabot.application.trial_sampler import OptunaSampler

        sampler = OptunaSampler(seed=11)
        params = sampler.suggest(_space())
        self.assertTrue(0.01 <= params["take_profit"] <= 0.05)
        sampler.observe("t-opt", 0.7)
        params2 = sampler.suggest(_space())
        self.assertTrue(0.01 <= params2["take_profit"] <= 0.05)
