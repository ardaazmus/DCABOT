"""Faz 17 G.2-motor (RG-07): per-role order_type (MARKET/LIMIT) + a single
live `max_adverse_slippage_bps` bound + `slippage_reference` (MARK-only for
now). Absence defaults to today's implicit behavior (every role LIMIT, no
adverse-slippage bound) so existing config/hashes are unaffected -- same
setdefault pattern as `direction`/`max_active_safety_orders`.
"""
import json
import unittest
from pathlib import Path

from dcabot.domain.config import Config

ROOT = Path(__file__).resolve().parents[1]


def _raw(**updates) -> dict:
    raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
    raw.update(updates)
    return raw


class DefaultBackwardCompatibilityTests(unittest.TestCase):
    def test_paper_json_has_no_explicit_order_type_fields(self):
        raw = _raw()
        for field in (
            "base_order_type", "safety_order_type", "exit_order_type",
            "stop_order_type", "max_adverse_slippage_bps", "slippage_reference",
        ):
            self.assertNotIn(field, raw)

    def test_absence_defaults_to_limit_everywhere_and_no_adverse_bound(self):
        config = Config.parse(_raw())
        self.assertEqual(config.base_order_type, "LIMIT")
        self.assertEqual(config.safety_order_type, "LIMIT")
        self.assertEqual(config.exit_order_type, "LIMIT")
        self.assertEqual(config.stop_order_type, "LIMIT")
        self.assertIsNone(config.max_adverse_slippage_bps)
        self.assertEqual(config.slippage_reference, "MARK")

    def test_role_lookup_helper_matches_fields(self):
        config = Config.parse(_raw())
        self.assertEqual(config.order_type_for_role("BASE"), "LIMIT")
        self.assertEqual(config.order_type_for_role("EXIT"), "LIMIT")
        self.assertEqual(config.order_type_for_role("STOP"), "LIMIT")
        self.assertEqual(config.order_type_for_role("SAFETY:1"), "LIMIT")


class OrderTypeValidationTests(unittest.TestCase):
    def test_invalid_order_type_value_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(base_order_type="STOP_LIMIT"))

    def test_market_requires_max_adverse_slippage_bps(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(stop_order_type="MARKET"))

    def test_market_with_valid_bound_is_accepted(self):
        config = Config.parse(_raw(stop_order_type="MARKET", max_adverse_slippage_bps="50"))
        self.assertEqual(config.stop_order_type, "MARKET")
        self.assertEqual(config.order_type_for_role("STOP"), "MARKET")
        from fractions import Fraction as F
        self.assertEqual(config.max_adverse_slippage_bps, F(50))

    def test_adverse_bound_rejected_when_nothing_is_market(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(max_adverse_slippage_bps="50"))

    def test_adverse_bound_out_of_range_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(stop_order_type="MARKET", max_adverse_slippage_bps="0"))
        with self.assertRaises(ValueError):
            Config.parse(_raw(stop_order_type="MARKET", max_adverse_slippage_bps="10000"))

    def test_slippage_reference_only_supports_mark(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(slippage_reference="LAST"))
        with self.assertRaises(ValueError):
            Config.parse(_raw(slippage_reference="MID"))


if __name__ == "__main__":
    unittest.main()
