"""Faz 14: izole float64 istatistik katmanı (analytics, salt danışma skoru)."""
import math
import unittest

from dcabot.analytics.scores import (
    AnalyticsError,
    deflated_sharpe_ratio,
    expected_max_sharpe,
    kurtosis_excess,
    probabilistic_sharpe_ratio,
    sharpe_ratio,
    skewness,
    to_float_series,
)


class FloatBoundaryTests(unittest.TestCase):
    def test_converts_finite_decimal_strings(self):
        self.assertEqual(to_float_series(("0.01", "-2", "3.5")), (0.01, -2.0, 3.5))

    def test_rejects_non_finite_and_non_string(self):
        for bad in ("abc", "NaN", "nan", "inf", "-inf", "", "1,0", 1.5, None):
            with self.subTest(bad=bad):
                with self.assertRaises(AnalyticsError):
                    to_float_series((bad,))  # type: ignore[arg-type]

    def test_rejects_empty_series(self):
        with self.assertRaises(AnalyticsError):
            to_float_series(())


class MomentsTests(unittest.TestCase):
    def test_symmetric_series_has_zero_skew(self):
        self.assertAlmostEqual(skewness((1.0, 2.0, 3.0, 4.0, 5.0)), 0.0, places=12)

    def test_known_asymmetric_skew(self):
        self.assertAlmostEqual(skewness((0.0, 0.0, 1.0)), 1 / math.sqrt(2), places=7)

    def test_known_excess_kurtosis(self):
        self.assertAlmostEqual(kurtosis_excess((-1.0, 0.0, 1.0)), -1.5, places=12)

    def test_constant_series_moments_raise(self):
        with self.assertRaises(AnalyticsError):
            skewness((2.0, 2.0, 2.0))
        with self.assertRaises(AnalyticsError):
            kurtosis_excess((2.0, 2.0, 2.0))

    def test_single_observation_raises(self):
        with self.assertRaises(AnalyticsError):
            skewness((1.0,))


class SharpeTests(unittest.TestCase):
    def test_known_per_period_sharpe(self):
        self.assertAlmostEqual(sharpe_ratio((0.01, 0.02, 0.03)), 2.0, places=9)

    def test_zero_volatility_raises(self):
        with self.assertRaises(AnalyticsError):
            sharpe_ratio((0.01, 0.01, 0.01))

    def test_single_observation_raises(self):
        with self.assertRaises(AnalyticsError):
            sharpe_ratio((0.05,))


class ProbabilisticSharpeTests(unittest.TestCase):
    def test_zero_sharpe_zero_benchmark_is_one_half(self):
        self.assertAlmostEqual(
            probabilistic_sharpe_ratio(sharpe=0.0, n_obs=100, skew=0.0, kurt=3.0, benchmark=0.0),
            0.5,
            places=12,
        )

    def test_strong_normal_sharpe_is_near_one(self):
        psr = probabilistic_sharpe_ratio(sharpe=1.0, n_obs=100, skew=0.0, kurt=3.0, benchmark=0.0)
        self.assertGreater(psr, 0.9999)

    def test_higher_benchmark_lowers_psr(self):
        low = probabilistic_sharpe_ratio(sharpe=1.0, n_obs=100, skew=0.0, kurt=3.0, benchmark=0.5)
        high = probabilistic_sharpe_ratio(sharpe=1.0, n_obs=100, skew=0.0, kurt=3.0, benchmark=1.5)
        self.assertGreater(low, high)

    def test_degenerate_denominator_raises(self):
        with self.assertRaises(AnalyticsError):
            probabilistic_sharpe_ratio(sharpe=10.0, n_obs=100, skew=10.0, kurt=3.0, benchmark=0.0)


class ExpectedMaxSharpeTests(unittest.TestCase):
    def test_single_trial_is_zero(self):
        self.assertEqual(expected_max_sharpe(1), 0.0)

    def test_two_trials_matches_closed_form(self):
        self.assertAlmostEqual(expected_max_sharpe(2), 0.5197, places=3)

    def test_grows_with_trial_count(self):
        self.assertAlmostEqual(expected_max_sharpe(100), 2.531, places=2)
        self.assertGreater(expected_max_sharpe(100), expected_max_sharpe(2))

    def test_non_positive_trials_raise(self):
        with self.assertRaises(AnalyticsError):
            expected_max_sharpe(0)


class DeflatedSharpeTests(unittest.TestCase):
    def test_single_trial_equals_psr_at_zero_benchmark(self):
        dsr = deflated_sharpe_ratio(sharpe=0.8, n_obs=120, skew=0.1, kurt=3.2, n_trials=1)
        psr = probabilistic_sharpe_ratio(sharpe=0.8, n_obs=120, skew=0.1, kurt=3.2, benchmark=0.0)
        self.assertAlmostEqual(dsr, psr, places=12)

    def test_more_trials_deflate_the_ratio(self):
        few = deflated_sharpe_ratio(sharpe=1.0, n_obs=200, skew=0.0, kurt=3.0, n_trials=2)
        many = deflated_sharpe_ratio(sharpe=1.0, n_obs=200, skew=0.0, kurt=3.0, n_trials=200)
        self.assertGreater(few, many)
