"""Faz 17 E.1: Lab rate bütçesi — paylaşılan tavan, kayan 60sn penceresi,
venue gözlemi (X-MBX-USED-WEIGHT-1M) ile fail-closed yukarı yuvarlama."""

import unittest

from dcabot.application.lab_rate_budget import (
    LabRateBudget,
    LabRateBudgetError,
)


class LabRateBudgetTests(unittest.TestCase):
    def test_fresh_budget_allows_within_ceiling(self):
        budget = LabRateBudget(ceiling_weight_1m=10)
        self.assertTrue(budget.allow("whale", 7, now_us=0))
        self.assertEqual(budget.usage_1m(now_us=0), 7)

    def test_exceeding_ceiling_is_denied_without_consuming(self):
        budget = LabRateBudget(ceiling_weight_1m=10)
        self.assertTrue(budget.allow("whale", 7, now_us=0))
        self.assertFalse(budget.allow("whale", 4, now_us=1_000))
        self.assertTrue(budget.allow("whale", 3, now_us=2_000))
        self.assertEqual(budget.usage_1m(now_us=2_000), 10)

    def test_window_expiry_frees_budget(self):
        budget = LabRateBudget(ceiling_weight_1m=10)
        self.assertTrue(budget.allow("whale", 10, now_us=0))
        self.assertFalse(budget.allow("whale", 1, now_us=59_999_999))
        self.assertTrue(budget.allow("whale", 10, now_us=60_000_000))

    def test_ceiling_is_shared_across_features(self):
        budget = LabRateBudget(ceiling_weight_1m=10)
        self.assertTrue(budget.allow("whale", 6, now_us=0))
        self.assertFalse(budget.allow("other", 5, now_us=1_000))

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(LabRateBudgetError):
            LabRateBudget(ceiling_weight_1m=0)
        budget = LabRateBudget(ceiling_weight_1m=10)
        with self.assertRaises(LabRateBudgetError):
            budget.allow("", 1, now_us=0)
        with self.assertRaises(LabRateBudgetError):
            budget.allow("whale", 0, now_us=0)
        with self.assertRaises(LabRateBudgetError):
            budget.allow("whale", 1, now_us=-1)
        with self.assertRaises(LabRateBudgetError):
            budget.observe_used_weight_1m(-1, now_us=0)

    def test_regressed_clock_fails_closed(self):
        budget = LabRateBudget(ceiling_weight_1m=10)
        self.assertTrue(budget.allow("whale", 1, now_us=100))
        with self.assertRaises(LabRateBudgetError):
            budget.allow("whale", 1, now_us=99)
        with self.assertRaises(LabRateBudgetError):
            budget.usage_1m(now_us=99)

    def test_venue_observation_raises_effective_usage(self):
        budget = LabRateBudget(ceiling_weight_1m=600)
        self.assertTrue(budget.allow("whale", 100, now_us=0))
        budget.observe_used_weight_1m(500, now_us=1_000)
        self.assertEqual(budget.usage_1m(now_us=1_000), 500)
        self.assertFalse(budget.allow("whale", 101, now_us=2_000))
        self.assertTrue(budget.allow("whale", 100, now_us=2_000))

    def test_venue_observation_below_tracked_keeps_tracked(self):
        budget = LabRateBudget(ceiling_weight_1m=600)
        self.assertTrue(budget.allow("whale", 500, now_us=0))
        budget.observe_used_weight_1m(100, now_us=1_000)
        self.assertEqual(budget.usage_1m(now_us=1_000), 500)

    def test_stale_venue_observation_is_ignored(self):
        budget = LabRateBudget(ceiling_weight_1m=600)
        budget.observe_used_weight_1m(500, now_us=0)
        self.assertEqual(budget.usage_1m(now_us=0), 500)
        self.assertEqual(budget.usage_1m(now_us=60_000_001), 0)


if __name__ == "__main__":
    unittest.main()
