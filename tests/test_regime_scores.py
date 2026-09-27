"""Faz 17 F.1: Bollinger Band Width (stdev needs sqrt -> analytics/, float64,
stdlib-only) + the one allowlisted bridge into application/regime_detection."""
import unittest

from dcabot.analytics.regime_scores import bollinger_band_width_series


class BollingerBandWidthTests(unittest.TestCase):
    def test_warmup_prefix_is_none(self):
        closes = [10.0, 10.1, 10.2, 9.9, 10.05]
        result = bollinger_band_width_series(closes, window=3, num_std=2.0)
        self.assertEqual(len(result), len(closes))
        self.assertIsNone(result[0])
        self.assertIsNone(result[1])

    def test_flat_series_has_zero_width(self):
        closes = [10.0] * 6
        result = bollinger_band_width_series(closes, window=3, num_std=2.0)
        self.assertEqual(result[-1], 0.0)

    def test_volatile_series_has_positive_width(self):
        closes = [10.0, 12.0, 8.0, 13.0, 7.0, 14.0]
        result = bollinger_band_width_series(closes, window=3, num_std=2.0)
        self.assertGreater(result[-1], 0.0)

    def test_rejects_empty_series(self):
        with self.assertRaises(ValueError):
            bollinger_band_width_series([], window=3, num_std=2.0)

    def test_rejects_nonpositive_window(self):
        with self.assertRaises(ValueError):
            bollinger_band_width_series([1.0, 2.0], window=0, num_std=2.0)


class AnalyticsBridgeTests(unittest.TestCase):
    def test_regime_detection_can_compute_bb_width_from_exact_closes(self):
        from dcabot.application.regime_detection import bb_width_series

        closes = ("10.0", "10.1", "10.2", "9.9", "10.05")
        result = bb_width_series(closes, window=3, num_std="2")
        self.assertEqual(len(result), 5)
        self.assertIsNone(result[0])
        self.assertIsInstance(result[-1], str)


if __name__ == "__main__":
    unittest.main()
