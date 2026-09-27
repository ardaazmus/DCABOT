"""Faz 17 AA.-1: /api/preview/full -- avg/TP/SL/margin, reusing Config.plan()/
target()/directional_stop_loss() verbatim. LCR-12: liquidation always null."""
import json
import unittest

from dcabot.server.api import _calculate_preview_full, _validate_preview_full_payload


def _base_config(**overrides) -> dict:
    raw = {
        "schema_version": 1,
        "mode": "offline",
        "symbol": "BTCUSDT",
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "base_qty": "1",
        "safety_qty": "1",
        "safety_count": 2,
        "deviation": "0.1",
        "step_multiplier": "1",
        "volume_multiplier": "1",
        "tick": "0.01",
        "qty_step": "0.001",
        "min_qty": "0.001",
        "min_notional": "0.01",
        "initial_equity": "1000",
        "max_entry_notional": "1000",
        "leverage": "1",
        "max_drawdown": "0.25",
        "minimum_equity": "100",
        "take_profit": "0.02",
        "target_mode": "GROSS_PRICE_RETURN",
        "target_quote": "5",
        "fee_rate": "0.001",
        "fee_quantum": "0.00000001",
        "slippage": "0",
        "margin_mode": "ISOLATED",
    }
    raw.update(overrides)
    return raw


class ValidationTests(unittest.TestCase):
    def test_missing_fields_are_rejected(self):
        validated, fields = _validate_preview_full_payload({"config": {}})
        self.assertIsNone(validated)
        self.assertIn("body", fields)

    def test_non_string_anchor_is_rejected(self):
        validated, fields = _validate_preview_full_payload({"config": _base_config(), "anchor": 100})
        self.assertIsNone(validated)
        self.assertIn("anchor", fields)


class CalculationTests(unittest.TestCase):
    def test_default_config_returns_avg_tp_no_sl_no_liquidation(self):
        validated, fields = _validate_preview_full_payload(
            {"config": _base_config(), "anchor": "100"}
        )
        self.assertEqual(fields, {})
        result = _calculate_preview_full(validated)
        self.assertEqual(result["average_cost"], "100")
        # take_profit=0.02 -> 102
        self.assertEqual(result["take_profit_price"], "102")
        self.assertIsNone(result["stop_loss_price"])
        self.assertIsNone(result["liquidation_price"])
        self.assertIn("LCR-12", result["liquidation_note"])
        self.assertEqual(len(result["levels"]), 2)

    def test_response_contract_is_locked(self):
        # frontend/src/FullPreviewPanel.tsx and previewOverlay.ts parse exactly this shape.
        validated, _ = _validate_preview_full_payload({"config": _base_config(), "anchor": "100"})
        result = _calculate_preview_full(validated)
        self.assertEqual(
            set(result),
            {
                "symbol", "anchor", "average_cost", "take_profit_price", "stop_loss_price",
                "liquidation_price", "liquidation_note", "estimated_initial_margin",
                "planned_gross_notional", "within_gross_entry_cap", "levels",
            },
        )
        self.assertEqual(
            result["levels"],
            [
                {"index": 1, "price": "90", "qty": "1", "notional": "90"},
                {"index": 2, "price": "80", "qty": "1", "notional": "80"},
            ],
        )

    def test_stop_loss_configured_returns_sl_price(self):
        validated, fields = _validate_preview_full_payload(
            {
                "config": _base_config(stop_loss_rate="0.05", stop_loss_confirmation_bars=3),
                "anchor": "100",
            }
        )
        self.assertEqual(fields, {})
        result = _calculate_preview_full(validated)
        self.assertEqual(result["stop_loss_price"], "95")

    def test_short_direction_flips_take_profit_below_entry(self):
        validated, fields = _validate_preview_full_payload(
            {"config": _base_config(direction="SHORT"), "anchor": "100"}
        )
        self.assertEqual(fields, {})
        result = _calculate_preview_full(validated)
        self.assertEqual(result["take_profit_price"], "98")

    def test_liquidation_is_never_present_regardless_of_leverage(self):
        validated, fields = _validate_preview_full_payload(
            {"config": _base_config(leverage="10"), "anchor": "100"}
        )
        self.assertEqual(fields, {})
        result = _calculate_preview_full(validated)
        self.assertIsNone(result["liquidation_price"])

    def test_invalid_config_raises_value_error(self):
        validated, fields = _validate_preview_full_payload(
            {"config": _base_config(margin_mode="BAD"), "anchor": "100"}
        )
        self.assertEqual(fields, {})
        with self.assertRaises(ValueError):
            _calculate_preview_full(validated)


if __name__ == "__main__":
    unittest.main()
