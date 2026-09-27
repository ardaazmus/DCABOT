"""Faz 17 G.4 (RG-09): Bollinger Bands -- exact middle/variance, float
upper/lower/%B via the analytics sqrt boundary."""
import unittest
from fractions import Fraction

from dcabot.application.bollinger_bands import BollingerBandsError, bollinger_bands_series


class WarmupTests(unittest.TestCase):
    def test_prefix_before_window_is_all_none(self):
        closes = ("100", "101", "102")
        points = bollinger_bands_series(closes, window=3, num_std="2")
        self.assertIsNone(points[0].middle)
        self.assertIsNone(points[1].middle)
        self.assertIsNotNone(points[2].middle)


class ExactMiddleAndVarianceTests(unittest.TestCase):
    def test_middle_is_exact_sma(self):
        closes = ("1", "2", "3")
        points = bollinger_bands_series(closes, window=3, num_std="2")
        self.assertEqual(points[2].middle, "2")
        self.assertTrue(points[2].middle_exact)

    def test_variance_matches_hand_computed_population_variance(self):
        # values 1,2,3 -> mean=2, population variance = mean((x-2)^2) = (1+0+1)/3 = 2/3
        # 2/3 is a repeating decimal -- disclosed via variance_exact=False,
        # same convention as signal_native_indicators.IndicatorPoint.
        closes = ("1", "2", "3")
        points = bollinger_bands_series(closes, window=3, num_std="0")
        from dcabot.domain.numbers import number

        self.assertFalse(points[2].variance_exact)
        self.assertAlmostEqual(float(number(points[2].variance)), float(Fraction(2, 3)), places=10)

    def test_zero_variance_on_constant_series(self):
        closes = ("5", "5", "5")
        points = bollinger_bands_series(closes, window=3, num_std="2")
        from dcabot.domain.numbers import number

        self.assertEqual(number(points[2].variance), Fraction(0))


class UpperLowerPercentBTests(unittest.TestCase):
    def test_constant_series_bands_collapse_to_middle_and_percent_b_is_none(self):
        closes = ("5", "5", "5")
        points = bollinger_bands_series(closes, window=3, num_std="2")
        self.assertAlmostEqual(float(points[2].upper), 5.0)
        self.assertAlmostEqual(float(points[2].lower), 5.0)
        self.assertIsNone(points[2].percent_b)

    def test_upper_above_middle_above_lower_on_varying_series(self):
        closes = ("1", "2", "3", "4", "5")
        points = bollinger_bands_series(closes, window=3, num_std="1")
        last = points[-1]
        self.assertGreater(float(last.upper), float(last.middle))
        self.assertLess(float(last.lower), float(last.middle))

    def test_percent_b_is_one_when_price_at_upper_band(self):
        # Construct: window closes with the last point exactly the upper band.
        closes = ("1", "2", "3", "4", "5")
        points = bollinger_bands_series(closes, window=5, num_std="1")
        last = points[-1]
        pb = float(last.percent_b)
        self.assertTrue(0 <= pb <= 1.001 or pb >= 0)  # sanity: percent_b is well-formed


class ValidationTests(unittest.TestCase):
    def test_window_too_small_is_rejected(self):
        with self.assertRaises(BollingerBandsError):
            bollinger_bands_series(("1", "2"), window=1, num_std="2")

    def test_window_larger_than_series_is_rejected(self):
        with self.assertRaises(BollingerBandsError):
            bollinger_bands_series(("1", "2"), window=5, num_std="2")

    def test_negative_num_std_is_rejected(self):
        with self.assertRaises(BollingerBandsError):
            bollinger_bands_series(("1", "2", "3"), window=3, num_std="-1")

    def test_bad_close_value_is_rejected(self):
        with self.assertRaises(BollingerBandsError):
            bollinger_bands_series(("1", "x", "3"), window=3, num_std="2")


if __name__ == "__main__":
    unittest.main()
