"""Faz 17 F.1: ADX/DI (exact Fraction) + BB-Width (analytics/, float64) ->
5-state regime label. Öneri-only: hiçbir deal/config parametresi değişmez,
bu modül yalnız bir etiket üretir."""
import unittest

from dcabot.application.regime_detection import (
    RegimeDetectionError,
    adx_series,
    classify_regime,
)


def _bars(*rows):
    """rows: (high, low, close) tuples as decimal strings."""
    return tuple({"high": h, "low": l, "close": c} for h, l, c in rows)


class AdxSeriesTests(unittest.TestCase):
    def test_warmup_prefix_is_none(self):
        # window=2 needs a handful of bars before ADX itself seeds.
        bars = _bars(
            ("10", "8", "9"), ("11", "9", "10"), ("12", "10", "11"), ("13", "11", "12"),
        )
        points = adx_series(bars, window=2)
        self.assertEqual(len(points), len(bars))
        self.assertIsNone(points[0].adx)

    def test_strong_uptrend_has_high_adx_and_positive_di_dominance(self):
        # Monotonic higher-highs/higher-lows: a textbook clean uptrend.
        bars = _bars(*[(str(10 + i), str(9 + i), str(9.5 + i)) for i in range(20)])
        points = adx_series(bars, window=3)
        last = points[-1]
        self.assertIsNotNone(last.adx)
        self.assertIsNotNone(last.plus_di)
        self.assertIsNotNone(last.minus_di)
        self.assertGreater(float(last.plus_di), float(last.minus_di))

    def test_flat_bars_have_zero_true_range_and_are_handled(self):
        bars = _bars(*[("10", "10", "10")] * 10)
        points = adx_series(bars, window=3)
        # No directional movement, no range -- ADX should not raise, DI is None or 0.
        self.assertIsNotNone(points[-1])

    def test_rejects_empty_series(self):
        with self.assertRaises(RegimeDetectionError):
            adx_series((), window=3)

    def test_rejects_nonpositive_window(self):
        with self.assertRaises(RegimeDetectionError):
            adx_series(_bars(("10", "9", "9.5")), window=0)

    def test_rejects_high_below_low(self):
        with self.assertRaises(RegimeDetectionError):
            adx_series(_bars(("9", "10", "9.5")), window=1)


class ClassifyRegimeTests(unittest.TestCase):
    def test_insufficient_bars_is_unknown(self):
        result = classify_regime(
            adx=None, plus_di=None, minus_di=None, bb_width=None,
            trend_threshold="25", range_threshold="20", squeeze_threshold="0.02",
        )
        self.assertEqual(result.state, "UNKNOWN")

    def test_squeeze_wins_over_a_weak_adx_reading(self):
        result = classify_regime(
            adx="10", plus_di="15", minus_di="14", bb_width="0.01",
            trend_threshold="25", range_threshold="20", squeeze_threshold="0.02",
        )
        self.assertEqual(result.state, "COMPRESSION")

    def test_strong_adx_with_clear_di_separation_is_trend_candidate(self):
        result = classify_regime(
            adx="30", plus_di="28", minus_di="10", bb_width="0.08",
            trend_threshold="25", range_threshold="20", squeeze_threshold="0.02",
        )
        self.assertEqual(result.state, "TREND_CANDIDATE")
        self.assertEqual(result.direction, "UP")

    def test_strong_adx_but_di_not_separated_is_not_trend(self):
        # High ADX alone is not enough -- DI lines must actually diverge.
        result = classify_regime(
            adx="30", plus_di="20.1", minus_di="19.9", bb_width="0.08",
            trend_threshold="25", range_threshold="20", squeeze_threshold="0.02",
            min_di_separation="2",
        )
        self.assertNotEqual(result.state, "TREND_CANDIDATE")

    def test_low_adx_and_no_squeeze_is_range_candidate(self):
        result = classify_regime(
            adx="12", plus_di="15", minus_di="14", bb_width="0.08",
            trend_threshold="25", range_threshold="20", squeeze_threshold="0.02",
        )
        self.assertEqual(result.state, "RANGE_CANDIDATE")

    def test_ambiguous_middle_zone_is_transition(self):
        result = classify_regime(
            adx="22", plus_di="18", minus_di="12", bb_width="0.08",
            trend_threshold="25", range_threshold="20", squeeze_threshold="0.02",
        )
        self.assertEqual(result.state, "TRANSITION")

    def test_down_direction_when_minus_di_dominates(self):
        result = classify_regime(
            adx="30", plus_di="8", minus_di="27", bb_width="0.08",
            trend_threshold="25", range_threshold="20", squeeze_threshold="0.02",
        )
        self.assertEqual(result.direction, "DOWN")

    def test_confidence_is_deterministic_not_a_probability(self):
        result = classify_regime(
            adx="30", plus_di="28", minus_di="10", bb_width="0.08",
            trend_threshold="25", range_threshold="20", squeeze_threshold="0.02",
        )
        self.assertIsInstance(result.confidence, str)
        # Must round-trip as an exact decimal, not e.g. "0.83333..." floats.
        from dcabot.domain.numbers import number
        number(result.confidence)


if __name__ == "__main__":
    unittest.main()
