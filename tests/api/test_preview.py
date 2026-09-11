import json
import unittest
from pathlib import Path

from dcabot.server.api import _calculate_preview, _validate_preview_payload


ROOT = Path(__file__).resolve().parents[2]


class PreviewApiContractTests(unittest.TestCase):
    def test_valid_payload_delegates_to_core_preview(self):
        payload = {
            "anchor": "100",
            "safety_qty": "1",
            "safety_count": 2,
            "deviation": "0.1",
            "revision": 7,
        }
        validated, fields = _validate_preview_payload(payload)
        self.assertEqual(fields, {})
        self.assertEqual(
            _calculate_preview(validated),
            {
                "symbol": "BTCUSDT",
                "base_asset": "BTC",
                "quote_asset": "USDT",
                "anchor": "100",
                "base_notional": "100",
                "planned_gross_notional": "270",
                "estimated_initial_margin": "270",
                "policy_required_collateral": None,
                "within_gross_entry_cap": True,
                "levels": [
                    {"index": 1, "price": "90", "qty": "1", "notional": "90"},
                    {"index": 2, "price": "80", "qty": "1", "notional": "80"},
                ],
                "assumption": "Theoretical full fills at plan prices; no venue collateral guarantee",
                "revision": 7,
            },
        )

    def test_financial_inputs_must_be_strings_and_fields_are_reported(self):
        payload = {
            "anchor": 100,
            "safety_qty": "1",
            "safety_count": 2,
            "deviation": "0.1",
            "revision": 1,
        }
        validated, fields = _validate_preview_payload(payload)
        self.assertIsNone(validated)
        self.assertEqual(
            fields,
            {"anchor": "Finansal değer noktasız ondalık JSON string olmalıdır."},
        )

    def test_malformed_financial_string_is_assigned_to_its_field(self):
        payload = {
            "anchor": "abc",
            "safety_qty": "1",
            "safety_count": 2,
            "deviation": "0.1",
            "revision": 1,
        }
        validated, fields = _validate_preview_payload(payload)
        self.assertIsNone(validated)
        self.assertEqual(fields, {"anchor": "Noktasız ondalık sayı girin."})

    def test_config_path_is_the_active_paper_config(self):
        config = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
        self.assertEqual(config["mode"], "offline")
