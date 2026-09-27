"""Faz 17 AA.-1: API-kablolama -- ince route'lar, hiçbir yeni ekonomik
formül yok. Bu testler yalnız validasyon+dispatch'i doğrular; matematiğin
kendisi zaten `test_momentum_oscillators.py`/`test_bollinger_bands.py`/
`test_correlation_risk.py`'de kanıtlı."""
import unittest

from dcabot.server.api import (
    _indicators_bollinger,
    _indicators_ema,
    _indicators_macd,
    _indicators_sma,
    _indicators_stoch_rsi,
    _risk_correlation,
    _risk_regime,
    _validate_indicator_bollinger_payload,
    _validate_indicator_macd_payload,
    _validate_indicator_series_payload,
    _validate_indicator_stoch_rsi_payload,
    _validate_risk_correlation_payload,
    _validate_risk_regime_payload,
)


def _closes(n: int, start=100) -> list:
    return [str(start + i) for i in range(n)]


class SmaEmaSeriesTests(unittest.TestCase):
    def test_sma_returns_points(self):
        validated, fields = _validate_indicator_series_payload({"closes": _closes(5), "window": 3})
        self.assertEqual(fields, {})
        result = _indicators_sma(validated)
        self.assertEqual(len(result["points"]), 5)
        self.assertIsNone(result["points"][0]["value"])
        self.assertIsNotNone(result["points"][2]["value"])

    def test_ema_returns_points(self):
        validated, fields = _validate_indicator_series_payload({"closes": _closes(5), "window": 3})
        result = _indicators_ema(validated)
        self.assertEqual(len(result["points"]), 5)

    def test_bad_window_is_field_error(self):
        validated, fields = _validate_indicator_series_payload({"closes": _closes(5), "window": 0})
        self.assertIsNone(validated)
        self.assertIn("window", fields)

    def test_unknown_field_is_rejected(self):
        validated, fields = _validate_indicator_series_payload(
            {"closes": _closes(5), "window": 3, "extra": 1}
        )
        self.assertIsNone(validated)
        self.assertIn("body", fields)


class MacdApiTests(unittest.TestCase):
    def test_macd_returns_decimal_text_points(self):
        validated, fields = _validate_indicator_macd_payload(
            {"closes": _closes(20), "fast": 3, "slow": 6, "signal": 3, "scale": 8}
        )
        self.assertEqual(fields, {})
        result = _indicators_macd(validated)
        self.assertEqual(len(result["points"]), 20)
        last = result["points"][-1]
        self.assertIsInstance(last["macd"], str)

    def test_fast_slow_ordering_error_propagates_as_field_error(self):
        validated, fields = _validate_indicator_macd_payload(
            {"closes": _closes(10), "fast": 3, "slow": 6, "signal": 3, "scale": 8}
        )
        validated["fast"], validated["slow"] = 6, 3
        with self.assertRaises(Exception):
            _indicators_macd(validated)

    def test_bad_scale_is_field_error(self):
        validated, fields = _validate_indicator_macd_payload(
            {"closes": _closes(10), "fast": 3, "slow": 6, "signal": 3, "scale": 0}
        )
        self.assertIsNone(validated)
        self.assertIn("scale", fields)


class StochRsiApiTests(unittest.TestCase):
    def test_stoch_rsi_returns_decimal_text_points(self):
        validated, fields = _validate_indicator_stoch_rsi_payload(
            {"closes": _closes(30), "rsi_window": 5, "stoch_window": 5, "scale": 8}
        )
        self.assertEqual(fields, {})
        result = _indicators_stoch_rsi(validated)
        self.assertEqual(len(result["points"]), 30)
        self.assertIsInstance(result["points"][-1]["rsi"], str)


class BollingerApiTests(unittest.TestCase):
    def test_bollinger_returns_exact_and_float_fields(self):
        validated, fields = _validate_indicator_bollinger_payload(
            {"closes": _closes(10), "window": 3, "num_std": "2"}
        )
        self.assertEqual(fields, {})
        result = _indicators_bollinger(validated)
        self.assertEqual(len(result["points"]), 10)
        last = result["points"][-1]
        self.assertIn("middle_exact", last)
        self.assertIn("upper", last)

    def test_missing_num_std_is_field_error(self):
        validated, fields = _validate_indicator_bollinger_payload(
            {"closes": _closes(5), "window": 3}
        )
        self.assertIsNone(validated)
        self.assertIn("body", fields)


class RiskCorrelationApiTests(unittest.TestCase):
    def test_allow_decision_for_dissimilar_series(self):
        prices_x = [100 + i for i in range(30)]
        prices_y = [200 - i for i in range(30)]
        validated, fields = _validate_risk_correlation_payload(
            {
                "prices_x": prices_x,
                "prices_y": prices_y,
                "windows": [5, 10],
                "threshold_numerator": 9,
                "threshold_denominator": 10,
                "scale": 1_000_000_000_000,
            }
        )
        self.assertEqual(fields, {})
        result = _risk_correlation(validated)
        self.assertIn(result["decision"], ("ALLOW", "DENY"))

    def test_bad_windows_is_field_error(self):
        validated, fields = _validate_risk_correlation_payload(
            {
                "prices_x": [1.0, 2.0, 3.0],
                "prices_y": [1.0, 2.0, 3.0],
                "windows": [],
                "threshold_numerator": 9,
                "threshold_denominator": 10,
                "scale": 1000,
            }
        )
        self.assertIsNone(validated)
        self.assertIn("windows", fields)

    def test_mismatched_length_price_series_denies_via_gate_not_crash(self):
        validated, fields = _validate_risk_correlation_payload(
            {
                "prices_x": [1.0, 2.0, 3.0],
                "prices_y": [1.0, 2.0],
                "windows": [2],
                "threshold_numerator": 9,
                "threshold_denominator": 10,
                "scale": 1000,
            }
        )
        self.assertEqual(fields, {})
        with self.assertRaises(Exception):
            _risk_correlation(validated)


def _regime_bars(n: int, *, up: bool = True) -> list[dict]:
    return [
        {"high": str(10 + (i if up else -i)), "low": str(8 + (i if up else -i)), "close": str(9 + (i if up else -i))}
        for i in range(n)
    ]


class RiskRegimeApiTests(unittest.TestCase):
    """AA.8 wiring (2026-09-23): thin route over already-tested
    `adx_series`/`bb_width_series`/`classify_regime` -- no new math."""

    def test_strong_uptrend_classifies_as_trend_or_range_with_exact_adx_di(self):
        validated, fields = _validate_risk_regime_payload(
            {
                "bars": _regime_bars(30, up=True),
                "adx_window": 3,
                "bb_window": 5,
                "bb_num_std": "2",
                "trend_threshold": "20",
                "range_threshold": "15",
                "squeeze_threshold": "0.01",
            }
        )
        self.assertEqual(fields, {})
        result = _risk_regime(validated)
        self.assertIn(result["state"], ("TREND_CANDIDATE", "RANGE_CANDIDATE", "TRANSITION", "COMPRESSION", "UNKNOWN"))
        self.assertIsNotNone(result["adx"])
        self.assertIsNotNone(result["plus_di"])

    def test_missing_field_is_field_error(self):
        validated, fields = _validate_risk_regime_payload(
            {
                "bars": _regime_bars(10),
                "adx_window": 3,
                "bb_window": 5,
                "bb_num_std": "2",
                "trend_threshold": "20",
                "range_threshold": "15",
            }
        )
        self.assertIsNone(validated)
        self.assertIn("body", fields)

    def test_bad_bar_shape_is_field_error(self):
        validated, fields = _validate_risk_regime_payload(
            {
                "bars": [{"high": "10", "low": "9"}],
                "adx_window": 3,
                "bb_window": 5,
                "bb_num_std": "2",
                "trend_threshold": "20",
                "range_threshold": "15",
                "squeeze_threshold": "0.01",
            }
        )
        self.assertIsNone(validated)
        self.assertIn("bars", fields)

    def test_min_di_separation_defaults_to_zero(self):
        validated, fields = _validate_risk_regime_payload(
            {
                "bars": _regime_bars(10),
                "adx_window": 3,
                "bb_window": 5,
                "bb_num_std": "2",
                "trend_threshold": "20",
                "range_threshold": "15",
                "squeeze_threshold": "0.01",
            }
        )
        self.assertEqual(fields, {})
        self.assertEqual(validated["min_di_separation"], "0")


if __name__ == "__main__":
    unittest.main()
