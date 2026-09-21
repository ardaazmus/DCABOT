"""F10.6: recurring schedule API (F16)."""
import unittest

from dcabot.server.api import (
    _recurring_schedule,
    _validate_recurring_schedule_payload,
)


class RecurringApiTests(unittest.TestCase):
    def test_projection_roundtrip(self):
        validated, fields = _validate_recurring_schedule_payload({
            "symbol": "BTCUSDT",
            "quote_amount": "100",
            "start_us": 1_000_000,
            "interval_us": 500_000,
            "count": 3,
        })
        self.assertEqual(fields, {})
        result = _recurring_schedule(validated)
        self.assertEqual(result["total_quote"], "300")
        self.assertEqual(len(result["slots"]), 3)
        self.assertEqual(result["order_authority"], "NONE")

    def test_bad_count_is_field_error(self):
        validated, fields = _validate_recurring_schedule_payload({
            "symbol": "BTCUSDT",
            "quote_amount": "100",
            "start_us": 0,
            "interval_us": 1,
            "count": 400,
        })
        self.assertIsNone(validated)
        self.assertIn("count", fields)

    def test_string_time_is_field_error(self):
        validated, fields = _validate_recurring_schedule_payload({
            "symbol": "BTCUSDT",
            "quote_amount": "100",
            "start_us": "0",
            "interval_us": 1,
            "count": 1,
        })
        self.assertIsNone(validated)
        self.assertIn("start_us", fields)


if __name__ == "__main__":
    unittest.main()
