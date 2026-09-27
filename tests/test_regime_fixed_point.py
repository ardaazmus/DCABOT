"""ADX double Wilder smoothing on a fixed 10^-30 grid: long series no longer
exceed the 4096-bit bound, and the displayed 12-digit values are unchanged."""
import random
import unittest
from unittest import mock

from dcabot.application import regime_detection
from dcabot.application.regime_detection import adx_series


def _bars(count: int, seed: int) -> tuple[dict[str, str], ...]:
    rng = random.Random(seed)
    price = 84000.0
    bars = []
    for _ in range(count):
        price = max(1.0, price * (1 + rng.uniform(-0.01, 0.01)))
        high = price * (1 + rng.uniform(0, 0.005))
        low = price * (1 - rng.uniform(0, 0.005))
        bars.append({"high": f"{high:.2f}", "low": f"{low:.2f}", "close": f"{price:.2f}"})
    return tuple(bars)


class AdxFixedPointTests(unittest.TestCase):
    def test_long_series_stays_within_the_exact_arithmetic_bound(self):
        points = adx_series(_bars(5000, 1), window=14)
        self.assertEqual(len(points), 5000)
        self.assertIsNotNone(points[-1].adx)

    def test_displayed_values_match_unquantized_computation(self):
        bars = _bars(45, 2)
        fixed = adx_series(bars, window=14)
        with mock.patch.object(regime_detection, "_fixed", side_effect=lambda value: value):
            exact = adx_series(bars, window=14)
        self.assertEqual(fixed, exact)
        self.assertIsNotNone(fixed[-1].adx)

    def test_quantization_is_half_even_on_the_grid(self):
        scale = regime_detection._FIXED_SCALE
        from fractions import Fraction
        self.assertEqual(regime_detection._fixed(Fraction(5, 2 * scale)), Fraction(2, scale))
        self.assertEqual(regime_detection._fixed(Fraction(7, 2 * scale)), Fraction(4, scale))


if __name__ == "__main__":
    unittest.main()
