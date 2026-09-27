"""Faz 17 F.2: getiri-bazlı (log, winsorized) kovaryans/varyans -- stdev/log
sqrt/ln içerir, analytics/ izolasyonu (float64, stdlib-only)."""
import unittest

from dcabot.analytics.correlation_scores import (
    log_returns,
    sample_covariance,
    sample_variance,
    winsorize,
)


class LogReturnsTests(unittest.TestCase):
    def test_computes_log_return_per_consecutive_pair(self):
        prices = [100.0, 110.0, 121.0]
        returns = log_returns(prices)
        self.assertEqual(len(returns), 2)
        self.assertAlmostEqual(returns[0], 0.09531017980432486, places=9)

    def test_rejects_nonpositive_price(self):
        with self.assertRaises(ValueError):
            log_returns([100.0, 0.0, 90.0])

    def test_rejects_too_short_series(self):
        with self.assertRaises(ValueError):
            log_returns([100.0])


class WinsorizeTests(unittest.TestCase):
    def test_clamps_extreme_values_to_percentile_bounds(self):
        values = [1.0, 2.0, 3.0, 4.0, 100.0]
        result = winsorize(values, lower_pct=0.0, upper_pct=0.8)
        # 80th pct (linear interpolation, pos=0.8*4=3.2) = 4 + (100-4)*0.2 = 23.2
        self.assertAlmostEqual(result[-1], 23.2, places=9)
        self.assertLess(result[-1], 100.0)

    def test_no_op_when_bounds_are_full_range(self):
        values = [1.0, 5.0, 9.0]
        self.assertEqual(winsorize(values, lower_pct=0.0, upper_pct=1.0), values)


class CovarianceVarianceTests(unittest.TestCase):
    def test_perfectly_correlated_series_have_matching_variance_and_covariance(self):
        x = [0.01, 0.02, -0.01, 0.03]
        y = x[:]
        self.assertAlmostEqual(sample_covariance(x, y), sample_variance(x), places=12)

    def test_rejects_mismatched_lengths(self):
        with self.assertRaises(ValueError):
            sample_covariance([0.1, 0.2], [0.1])

    def test_rejects_too_few_points(self):
        with self.assertRaises(ValueError):
            sample_covariance([0.1], [0.1])


if __name__ == "__main__":
    unittest.main()
