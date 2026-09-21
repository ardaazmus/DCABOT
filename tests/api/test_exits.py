"""F9.2: trailing exit binding + percentage ratchet + breakeven API (F09)."""
import unittest

from dcabot.server.api import (
    _exits_breakeven,
    _exits_percent_arm,
    _exits_percent_observe,
    _exits_trailing_bind,
    _validate_exits_breakeven_payload,
    _validate_exits_percent_arm_payload,
    _validate_exits_percent_observe_payload,
    _validate_exits_trailing_bind_payload,
)


def _triggered_long_state():
    return {
        "status": "TRIGGERED",
        "activation_price": "100",
        "distance": "5",
        "high_water": "110",
        "stop_price": "105",
    }


def _plan_body():
    return {
        "side": "LONG",
        "anchor_price": "100",
        "base_amount": "10",
        "base_sizing": "QUOTE_NOTIONAL",
        "safety_amount": "2",
        "safety_sizing": "QUOTE_NOTIONAL",
        "safety_count": 2,
        "deviation": "0.01",
        "step_multiplier": "2",
        "volume_multiplier": "2",
        "price_tick": "0.001",
        "quantity_step": "0.0001",
    }


def _fills_body():
    return [
        {"execution_id": "base", "level_index": 0, "quantity": "0.1", "price": "100"},
        {"execution_id": "s1", "level_index": 1, "quantity": "0.02", "price": "97"},
    ]


class ExitsApiTests(unittest.TestCase):
    def test_trailing_bind_triggered(self):
        validated, fields = _validate_exits_trailing_bind_payload({
            "side": "LONG",
            "kind": "FIXED",
            "state": _triggered_long_state(),
            "open_qty": "2",
            "accepted_exit_fills": [],
            "committed_exit_qty": [],
            "requested_qty": "1",
        })
        self.assertEqual(fields, {})
        result = _exits_trailing_bind(validated)
        self.assertEqual(result["trigger_price"], "105")
        self.assertEqual(result["requested_qty"], "1")
        self.assertEqual(result["remaining_capacity"], "1")
        self.assertEqual(result["order_authority"], "NONE")

    def test_trailing_bind_untriggered_rejected(self):
        state = dict(_triggered_long_state(), status="ACTIVE")
        validated, fields = _validate_exits_trailing_bind_payload({
            "side": "LONG",
            "kind": "FIXED",
            "state": state,
            "open_qty": "2",
            "accepted_exit_fills": [],
            "committed_exit_qty": [],
            "requested_qty": "1",
        })
        self.assertEqual(fields, {})
        with self.assertRaises(ValueError):
            _exits_trailing_bind(validated)

    def test_percent_arm_observe_roundtrip(self):
        validated, fields = _validate_exits_percent_arm_payload({
            "side": "LONG", "activation_price": "100", "rate": "0.05",
        })
        self.assertEqual(fields, {})
        armed = _exits_percent_arm(validated)
        self.assertEqual(armed["status"], "INACTIVE")
        observed, fields = _validate_exits_percent_observe_payload({
            "side": "LONG", "state": armed, "price": "110",
        })
        self.assertEqual(fields, {})
        result = _exits_percent_observe(observed)
        self.assertEqual(result["status"], "ACTIVE")
        self.assertEqual(result["high_water"], "110")
        self.assertEqual(result["stop_price"], "104.5")

    def test_breakeven_gross_only_without_profile(self):
        validated, fields = _validate_exits_breakeven_payload({
            "plan": _plan_body(), "fills": _fills_body(),
        })
        self.assertEqual(fields, {})
        result = _exits_breakeven(validated)
        self.assertEqual(result["status"], "GROSS_ONLY")
        self.assertEqual(result["gross_breakeven_price"], "99.5")
        self.assertIsNone(result["fee_aware_breakeven_price"])
        self.assertEqual(result["order_authority"], "NONE")

    def test_breakeven_fee_aware_with_profile(self):
        validated, fields = _validate_exits_breakeven_payload({
            "plan": _plan_body(),
            "fills": _fills_body(),
            "fee_profile": {
                "settlement_asset": "USDT",
                "fee_asset": "USDT",
                "entry_fee_rate": "0.01",
                "exit_fee_rate": "0",
                "funding_cashflow": "0",
                "profile_revision": "test-fees-v1",
            },
        })
        self.assertEqual(fields, {})
        result = _exits_breakeven(validated)
        self.assertEqual(result["status"], "FEE_AWARE_READY")
        self.assertEqual(result["fee_aware_breakeven_price"], "100.495")

    def test_bad_kind_is_field_error(self):
        validated, fields = _validate_exits_trailing_bind_payload({
            "side": "LONG",
            "kind": "MAGIC",
            "state": _triggered_long_state(),
            "open_qty": "2",
            "accepted_exit_fills": [],
            "committed_exit_qty": [],
            "requested_qty": "1",
        })
        self.assertIsNone(validated)
        self.assertIn("kind", fields)

    def test_bad_rate_is_field_error(self):
        validated, fields = _validate_exits_percent_arm_payload({
            "side": "LONG", "activation_price": "100", "rate": "fast",
        })
        # string passes shape validation; the core rejects non-numeric
        self.assertEqual(fields, {})
        with self.assertRaises(ValueError):
            _exits_percent_arm(validated)

    def test_missing_plan_is_field_error(self):
        validated, fields = _validate_exits_breakeven_payload({"fills": _fills_body()})
        self.assertIsNone(validated)
        self.assertIn("body", fields)

    def test_non_usdt_fee_profile_rejected(self):
        validated, fields = _validate_exits_breakeven_payload({
            "plan": _plan_body(),
            "fills": _fills_body(),
            "fee_profile": {
                "settlement_asset": "BTC",
                "fee_asset": "BTC",
                "entry_fee_rate": "0.01",
                "exit_fee_rate": "0",
                "funding_cashflow": "0",
                "profile_revision": "test-btc-v1",
            },
        })
        self.assertEqual(fields, {})
        with self.assertRaises(ValueError) as ctx:
            _exits_breakeven(validated)
        self.assertIn("SETTLEMENT_ASSET_UNSUPPORTED", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
