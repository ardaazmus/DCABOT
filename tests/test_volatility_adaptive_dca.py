"""Faz 17 B.1: Volatility-Adaptive DCA (ATR-based dynamic SO deviation, exact).

qwen modul 1 hedefi (RG-QWEN-HTML): "SO sapmasi ve TP, ATR/volatiliteye gore
dinamik hesaplanir" -> dev_dinamik = dev_baz * (ATR_simdi / ATR_ref).

ATR burada Wilder'in klasik tanimiyla (ilk pencere SMA-tohumlu, sonrasi
1/window agirlikli recursive smoothing) hesaplanir -- signal_native_indicators
EMA'siyla ayni "recursive + bounded() fail-closed" deseni, RG-09'un Fraction
digit-growth bulgusuna karsi ayni onlemi tasir (pencere disi buyume yok cunku
smoothing sabit agirlikla calisir, ama cok uzun seride yine de bounded()
kaynak sinirina carpabilir -- bu, EMA ile aynı, bilinen ve kabul edilen risk).
"""
import unittest

from dcabot.application.volatility_adaptive_dca import (
    VolatilityAdaptiveError,
    atr_series,
    dynamic_deviation,
    true_range_series,
)


class TrueRangeTests(unittest.TestCase):
    def test_first_bar_is_high_minus_low(self):
        tr = true_range_series(("10",), ("8",), ("9",))
        self.assertEqual(tr, ("2",))

    def test_gap_up_uses_high_minus_prev_close(self):
        # prev close 9, bar2 high=13 low=12 -> |13-9|=4 dominates (13-12=1, |12-9|=3)
        tr = true_range_series(("10", "13"), ("8", "12"), ("9", "12.5"))
        self.assertEqual(tr, ("2", "4"))

    def test_gap_down_uses_prev_close_minus_low(self):
        # prev close 9, bar2 high=6 low=4 -> |4-9|=5 dominates (6-4=2, |6-9|=3)
        tr = true_range_series(("10", "6"), ("8", "4"), ("9", "5"))
        self.assertEqual(tr, ("2", "5"))

    def test_mismatched_lengths_or_bad_values_raise(self):
        with self.assertRaises(VolatilityAdaptiveError):
            true_range_series(("10", "11"), ("8",), ("9", "10"))
        with self.assertRaises(VolatilityAdaptiveError):
            true_range_series(("10",), ("8",), ("abc",))
        with self.assertRaises(VolatilityAdaptiveError):
            true_range_series((), (), ())

    def test_high_below_low_rejected(self):
        with self.assertRaises(VolatilityAdaptiveError):
            true_range_series(("5",), ("8",), ("6",))


class AtrSeriesTests(unittest.TestCase):
    def test_warmup_then_sma_seed_then_wilder_smoothing(self):
        # TR = [2, 4, 5, 3] (from four bars); window=2
        points = atr_series(
            highs=("10", "13", "14", "12"),
            lows=("8", "12", "9", "9"),
            closes=("9", "12.5", "13.5", "11"),
            window=2,
        )
        # TR[0]=2 (10-8), TR[1]=max(13-12,|13-9|,|12-9|)=4,
        # TR[2]=max(14-9,|14-12.5|,|9-12.5|)=5, TR[3]=max(12-9,|12-13.5|,|9-13.5|)=4.5
        self.assertEqual([p.index for p in points], [0, 1, 2, 3])
        self.assertIsNone(points[0].value)
        self.assertEqual(points[1].value, "3")  # SMA seed of TR[0..1] = (2+4)/2
        # Wilder: atr[2] = (atr[1]*(w-1) + TR[2]) / w = (3*1 + 5)/2 = 4
        self.assertEqual(points[2].value, "4")
        # atr[3] = (4*1 + 4.5)/2 = 4.25
        self.assertEqual(points[3].value, "4.25")

    def test_window_larger_than_series_rejected(self):
        with self.assertRaises(VolatilityAdaptiveError):
            atr_series(highs=("10",), lows=("8",), closes=("9",), window=2)

    def test_non_positive_window_rejected(self):
        with self.assertRaises(VolatilityAdaptiveError):
            atr_series(highs=("10", "11"), lows=("8", "9"), closes=("9", "10"), window=0)


class DynamicDeviationTests(unittest.TestCase):
    def test_scales_linearly_with_atr_ratio(self):
        # dev_base=0.02, atr_now=6, atr_ref=4 -> 0.02 * 1.5 = 0.03
        self.assertEqual(dynamic_deviation("0.02", "6", "4"), "0.03")

    def test_calmer_market_shrinks_deviation(self):
        # atr_now < atr_ref -> deviation shrinks
        self.assertEqual(dynamic_deviation("0.02", "2", "4"), "0.01")

    def test_equal_atr_is_identity(self):
        self.assertEqual(dynamic_deviation("0.05", "7", "7"), "0.05")

    def test_non_positive_inputs_rejected(self):
        with self.assertRaises(VolatilityAdaptiveError):
            dynamic_deviation("0", "6", "4")
        with self.assertRaises(VolatilityAdaptiveError):
            dynamic_deviation("0.02", "0", "4")
        with self.assertRaises(VolatilityAdaptiveError):
            dynamic_deviation("0.02", "6", "0")
        with self.assertRaises(VolatilityAdaptiveError):
            dynamic_deviation("-0.02", "6", "4")

    def test_bad_decimal_text_rejected(self):
        with self.assertRaises(VolatilityAdaptiveError):
            dynamic_deviation("abc", "6", "4")


if __name__ == "__main__":
    unittest.main()
