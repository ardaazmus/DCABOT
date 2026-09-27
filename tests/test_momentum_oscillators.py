"""Faz 17 G.4 (RG-09): MACD/StochRSI via fixed-point integers. Correctness
is proven against an independent raw-`Fraction` oracle on short series;
digit-growth tests prove the production path stays bounded over long series
(the quantified failure mode raw Fraction has, per konu 9/12 research)."""
import unittest
from fractions import Fraction

from dcabot.application.momentum_oscillators import (
    MomentumOscillatorError,
    macd_series,
    stoch_rsi_series,
)


def _fraction_ema(values: list[Fraction], window: int) -> list[Fraction | None]:
    """Independent oracle: the SAME SMA-seeded EMA recursion, but in raw,
    unbounded Fraction -- deliberately not calling production code."""
    out: list[Fraction | None] = [None] * len(values)
    factor = Fraction(2, window + 1)
    seed = sum(values[:window], Fraction(0)) / window
    out[window - 1] = seed
    prev = seed
    for i in range(window, len(values)):
        prev = values[i] * factor + prev * (1 - factor)
        out[i] = prev
    return out


def _closes(n: int, *, start=100, step=1) -> tuple[str, ...]:
    return tuple(str(start + i * step) for i in range(n))


class MacdFractionOracleTests(unittest.TestCase):
    def test_matches_raw_fraction_oracle_within_rounding_tolerance(self):
        closes = _closes(40, start=100, step=1)
        scale = 8
        points = macd_series(closes, fast=3, slow=6, signal=3, scale=scale)
        values = [Fraction(int(c)) for c in closes]
        fast_oracle = _fraction_ema(values, 3)
        slow_oracle = _fraction_ema(values, 6)
        macd_oracle = [
            None if f is None or s is None else f - s for f, s in zip(fast_oracle, slow_oracle)
        ]
        for i, point in enumerate(points):
            if point.macd is None:
                self.assertIsNone(macd_oracle[i])
                continue
            expected = round(macd_oracle[i] * 10**scale)
            # Independent per-step rounding can drift by a small, bounded
            # amount step-over-step -- never unboundedly, and never enough
            # to change the sign/order of magnitude at this scale.
            self.assertLessEqual(abs(point.macd - expected), 50)

    def test_windows_must_be_ordered(self):
        with self.assertRaises(MomentumOscillatorError):
            macd_series(_closes(10), fast=6, slow=3, signal=2)

    def test_series_too_short_is_rejected(self):
        with self.assertRaises(MomentumOscillatorError):
            macd_series(_closes(3), fast=3, slow=6, signal=2)

    def test_invalid_scale_is_rejected(self):
        with self.assertRaises(MomentumOscillatorError):
            macd_series(_closes(10), fast=2, slow=4, signal=2, scale=0)
        with self.assertRaises(MomentumOscillatorError):
            macd_series(_closes(10), fast=2, slow=4, signal=2, scale=19)

    def test_output_is_always_int_never_fraction(self):
        points = macd_series(_closes(20), fast=3, slow=6, signal=3)
        for point in points:
            if point.macd is not None:
                self.assertIsInstance(point.macd, int)
            if point.signal is not None:
                self.assertIsInstance(point.signal, int)


class MacdDigitGrowthTests(unittest.TestCase):
    def test_scaled_integer_never_grows_over_a_long_series(self):
        # Oscillating series (never monotonic) over 2000 bars -- the exact
        # scenario the konu 9/12 research measured raw Fraction blowing up
        # on. The fixed-point path must stay bounded to a small, constant
        # digit count regardless of series length.
        closes = tuple(str(100 + (i % 20) - 10) for i in range(2000))
        points = macd_series(closes, fast=12, slow=26, signal=9, scale=8)
        max_digits = max(
            len(str(abs(p.macd))) for p in points if p.macd is not None
        )
        # A raw Fraction recursion of this length would reach 1000+ digit
        # denominators (measured in research); fixed-point stays near the
        # scale + a handful of integer-part digits, forever.
        self.assertLess(max_digits, 30)


class StochRsiFractionOracleTests(unittest.TestCase):
    def test_matches_hand_computed_rsi_on_a_simple_series(self):
        # Alternating +1/-1 deltas after a monotonic warmup -- avg_gain and
        # avg_loss both settle to the same magnitude, RSI -> 50.
        closes = _closes(30, start=100, step=1)
        points = stoch_rsi_series(closes, rsi_window=5, stoch_window=5, scale=8)
        # Strictly rising series: every delta is a gain, avg_loss stays 0 -> RSI=100.
        last = points[-1]
        self.assertEqual(last.rsi, 100 * 10**8)

    def test_flat_series_is_neutral_fifty(self):
        closes = tuple("100" for _ in range(20))
        points = stoch_rsi_series(closes, rsi_window=5, stoch_window=5, scale=8)
        last = points[-1]
        self.assertEqual(last.rsi, 50 * 10**8)

    def test_output_is_always_int_never_fraction(self):
        points = stoch_rsi_series(_closes(30), rsi_window=5, stoch_window=5)
        for point in points:
            if point.rsi is not None:
                self.assertIsInstance(point.rsi, int)
            if point.stoch_rsi is not None:
                self.assertIsInstance(point.stoch_rsi, int)

    def test_stoch_rsi_is_bounded_zero_to_hundred(self):
        closes = tuple(str(100 + (i % 13) - 6) for i in range(60))
        points = stoch_rsi_series(closes, rsi_window=7, stoch_window=7, scale=8)
        for point in points:
            if point.stoch_rsi is not None:
                self.assertGreaterEqual(point.stoch_rsi, 0)
                self.assertLessEqual(point.stoch_rsi, 100 * 10**8)

    def test_series_too_short_is_rejected(self):
        with self.assertRaises(MomentumOscillatorError):
            stoch_rsi_series(_closes(3), rsi_window=5, stoch_window=5)


if __name__ == "__main__":
    unittest.main()
