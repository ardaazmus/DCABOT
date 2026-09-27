"""Faz 17 G.4 (RG-09): indicator registry is a thin lookup layer -- it must
route to the SAME underlying functions, not reimplement or reinterpret
anything."""
import unittest

from dcabot.application.indicator_registry import (
    IndicatorRegistryError,
    available_indicators,
    compute_indicator,
)
from dcabot.application.momentum_oscillators import macd_series
from dcabot.application.signal_native_indicators import sma_series


def _closes(n: int, start=100) -> tuple[str, ...]:
    return tuple(str(start + i) for i in range(n))


class RegistryLookupTests(unittest.TestCase):
    def test_available_indicators_lists_all_registered_names(self):
        names = available_indicators()
        for expected in ("SMA", "EMA", "MACD", "STOCH_RSI", "BOLLINGER"):
            self.assertIn(expected, names)

    def test_unknown_indicator_is_rejected(self):
        with self.assertRaises(IndicatorRegistryError):
            compute_indicator("NOT_A_REAL_INDICATOR", _closes(10))

    def test_sma_routes_to_the_same_function_and_result(self):
        closes = _closes(10)
        via_registry = compute_indicator("SMA", closes, window=3)
        direct = sma_series(closes, window=3)
        self.assertEqual(via_registry, direct)

    def test_macd_routes_to_the_same_function_and_result(self):
        closes = _closes(20)
        via_registry = compute_indicator("MACD", closes, fast=3, slow=6, signal=3)
        direct = macd_series(closes, fast=3, slow=6, signal=3)
        self.assertEqual(via_registry, direct)


if __name__ == "__main__":
    unittest.main()
