"""Faz 13.5: native indikatör kesişim endpoint'i."""
import unittest

from dcabot.server.api import (
    _signal_indicator_cross,
    _validate_indicator_cross_payload,
)


class IndicatorCrossApiTests(unittest.TestCase):
    def test_cross_returns_series_and_events(self):
        validated, fields = _validate_indicator_cross_payload(
            {"closes": ["1", "2", "3", "2", "1"], "fast_window": 2, "slow_window": 3}
        )
        self.assertEqual(fields, {})
        assert validated is not None
        result = _signal_indicator_cross(validated)
        self.assertEqual(result["events"], [{"index": 4, "direction": "DEATH"}])
        self.assertEqual(len(result["fast"]), 5)
        self.assertEqual(result["fast"][1], {"index": 1, "value": "1.5", "exact": True})

    def test_kind_defaults_to_sma_and_ema_is_accepted(self):
        validated, fields = _validate_indicator_cross_payload(
            {"closes": ["1", "2", "3", "2", "1"], "fast_window": 2, "slow_window": 3}
        )
        self.assertEqual(fields, {})
        assert validated is not None
        self.assertEqual(validated.get("kind"), "sma")
        validated, fields = _validate_indicator_cross_payload(
            {"closes": ["1", "2", "3", "2", "1"], "fast_window": 2, "slow_window": 3, "kind": "ema"}
        )
        self.assertEqual(fields, {})
        assert validated is not None
        result = _signal_indicator_cross(validated)
        self.assertTrue(all(set(point) == {"index", "value", "exact"} for point in result["fast"]))

    def test_unknown_kind_is_field_error(self):
        validated, fields = _validate_indicator_cross_payload(
            {"closes": ["1", "2", "3"], "fast_window": 2, "slow_window": 2, "kind": "rsi"}
        )
        self.assertIsNone(validated)
        self.assertIn("kind", fields)

    def test_bad_payload_is_field_error(self):
        validated, fields = _validate_indicator_cross_payload(
            {"closes": ["1"], "fast_window": 2, "slow_window": 3}
        )
        self.assertIsNone(validated)
        self.assertIn("closes", fields)
        validated, fields = _validate_indicator_cross_payload(
            {"closes": ["1", "2"], "fast_window": 0, "slow_window": 3}
        )
        self.assertIsNone(validated)
        self.assertIn("fast_window", fields)
