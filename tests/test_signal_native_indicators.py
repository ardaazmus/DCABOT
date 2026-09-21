"""Faz 13.5: DCABOT-native offline indikatörler (SMA/EMA/kesişim, exact).

Pine-parity (pynecore) DEFERRED: otomatik çeviri ücretli hosted API'ye
dayanıyor ve taşınacak indikatör ürün kararı bekliyor. Bu modül Pine
eşleniği İDDİA ETMEZ; el-hesaplı, exact, offline bir alternatiftir.
"""
import unittest

from dcabot.application.signal_native_indicators import (
    SignalIndicatorError,
    detect_crosses,
    ema_series,
    sma_series,
)


class SmaTests(unittest.TestCase):
    def test_warmup_is_none_then_exact_averages(self):
        points = sma_series(("1", "2", "3", "4"), window=2)
        self.assertEqual(
            [(p.index, p.value, p.exact) for p in points],
            [(0, None, True), (1, "1.5", True), (2, "2.5", True), (3, "3.5", True)],
        )

    def test_repeating_average_is_disclosed(self):
        points = sma_series(("1", "2", "2"), window=3)
        self.assertEqual(points[2].value, "1.666666666667")
        self.assertFalse(points[2].exact)

    def test_bad_window_and_values_raise(self):
        with self.assertRaises(SignalIndicatorError):
            sma_series(("1", "2"), window=0)
        with self.assertRaises(SignalIndicatorError):
            sma_series(("1", "2"), window=3)
        with self.assertRaises(SignalIndicatorError):
            sma_series(("1", "abc"), window=2)
        with self.assertRaises(SignalIndicatorError):
            sma_series(("1",), window=2)

    def test_window_one_is_identity(self):
        points = sma_series(("1", "2"), window=1)
        self.assertEqual([(p.index, p.value) for p in points], [(0, "1"), (1, "2")])


class EmaTests(unittest.TestCase):
    def test_seeded_with_first_window_sma(self):
        points = ema_series(("1", "2", "3", "4"), window=2)
        self.assertEqual(points[0].value, None)
        self.assertEqual(points[1].value, "1.5")
        self.assertEqual(points[2].value, "2.5")
        self.assertEqual(points[3].value, "3.5")
        self.assertTrue(points[3].exact)
        repeating = ema_series(("1", "2", "4"), window=2)
        self.assertEqual(repeating[2].value, "3.166666666667")
        self.assertFalse(repeating[2].exact)

    def test_window_one_tracks_price(self):
        points = ema_series(("1", "2"), window=1)
        self.assertEqual([p.value for p in points], ["1", "2"])


class CrossTests(unittest.TestCase):
    def test_fall_after_rise_is_death_cross(self):
        result = detect_crosses(("1", "2", "3", "2", "1"), fast_window=2, slow_window=3)
        self.assertEqual([(e.index, e.direction) for e in result.events], [(4, "DEATH")])

    def test_rise_after_fall_is_golden_cross(self):
        result = detect_crosses(("3", "2", "1", "2", "3"), fast_window=2, slow_window=3)
        self.assertEqual([(e.index, e.direction) for e in result.events], [(4, "GOLDEN")])

    def test_flat_series_has_no_cross(self):
        result = detect_crosses(("2", "2", "2", "2"), fast_window=2, slow_window=3)
        self.assertEqual(result.events, ())

    def test_series_are_returned_with_events(self):
        result = detect_crosses(("1", "2", "3", "4"), fast_window=2, slow_window=3)
        self.assertEqual(len(result.fast), 4)
        self.assertEqual(len(result.slow), 4)
        self.assertEqual(result.fast[1].value, "1.5")

    def test_ema_kind_detects_cross_on_ema_series(self):
        result = detect_crosses(("3", "2", "1", "2", "3"), fast_window=2, slow_window=3, kind="ema")
        self.assertEqual([(e.index, e.direction) for e in result.events], [(4, "GOLDEN")])
        self.assertEqual(result.fast[1].value, "2.5")

    def test_unknown_kind_raises(self):
        with self.assertRaises(SignalIndicatorError):
            detect_crosses(("1", "2", "3"), fast_window=2, slow_window=2, kind="rsi")
