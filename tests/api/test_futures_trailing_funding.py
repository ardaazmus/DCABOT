import unittest

from dcabot.server.api import (
    _futures_funding,
    _futures_trailing_arm,
    _futures_trailing_observe,
    _validate_futures_funding_payload,
    _validate_futures_trailing_arm_payload,
    _validate_futures_trailing_observe_payload,
)


def _position():
    return {
        "side": "LONG",
        "quantity": "2",
        "contract_size": "0.5",
        "entry_price": "50000",
        "mark_price": "51000",
        "settlement_asset": "USDT",
    }


class FuturesTrailingApiTests(unittest.TestCase):
    def test_arm_then_observe_triggers(self):
        validated, fields = _validate_futures_trailing_arm_payload(
            {"side": "LONG", "activation_price": "100", "distance": "5"}
        )
        self.assertEqual(fields, {})
        armed = _futures_trailing_arm(validated)
        self.assertEqual(armed["status"], "INACTIVE")
        observed, fields = _validate_futures_trailing_observe_payload(
            {"side": "LONG", "state": armed, "price": "110"}
        )
        self.assertEqual(fields, {})
        active = _futures_trailing_observe(observed)
        self.assertEqual(
            (active["status"], active["high_water"], active["stop_price"]),
            ("ACTIVE", "110", "105"),
        )
        observed, _ = _validate_futures_trailing_observe_payload(
            {"side": "LONG", "state": active, "price": "103"}
        )
        triggered = _futures_trailing_observe(observed)
        self.assertEqual(triggered["status"], "TRIGGERED")

    def test_short_arm(self):
        validated, fields = _validate_futures_trailing_arm_payload(
            {"side": "SHORT", "activation_price": "100", "distance": "5"}
        )
        self.assertEqual(fields, {})
        armed = _futures_trailing_arm(validated)
        self.assertEqual(armed["status"], "INACTIVE")
        self.assertIsNone(armed["low_water"])

    def test_bad_side_is_field_error(self):
        validated, fields = _validate_futures_trailing_arm_payload(
            {"side": "UP", "activation_price": "100", "distance": "5"}
        )
        self.assertIsNone(validated)
        self.assertIn("side", fields)


class FuturesFundingApiTests(unittest.TestCase):
    def test_long_pays_positive_rate(self):
        validated, fields = _validate_futures_funding_payload(
            {
                "position": _position(),
                "funding_rate": "0.0001",
                "effective_time_us": 1700000000000000,
            }
        )
        self.assertEqual(fields, {})
        result = _futures_funding(validated)
        self.assertEqual(result["amount"], "-5.1")
        self.assertEqual(result["core_expense"], "5.1")
        self.assertEqual(result["settlement_asset"], "USDT")

    def test_short_receives_positive_rate(self):
        position = _position()
        position["side"] = "SHORT"
        validated, fields = _validate_futures_funding_payload(
            {
                "position": position,
                "funding_rate": "0.0001",
                "effective_time_us": 1700000000000000,
            }
        )
        self.assertEqual(fields, {})
        result = _futures_funding(validated)
        self.assertEqual(result["amount"], "5.1")

    def test_bad_rate_is_value_error(self):
        validated, fields = _validate_futures_funding_payload(
            {
                "position": _position(),
                "funding_rate": "abc",
                "effective_time_us": 1700000000000000,
            }
        )
        self.assertEqual(fields, {})
        with self.assertRaises(ValueError) as ctx:
            _futures_funding(validated)
        self.assertIn("FUNDING_RATE_INVALID", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
