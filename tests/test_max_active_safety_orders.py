"""Faz 17 G.3: Config.max_active_safety_orders (None -> effective=safety_count,
davranış aynı; geriye uyumlu -- eski config'ler/hash'ler değişmez)."""
import json
import unittest
from pathlib import Path

from dcabot.domain.config import Config

ROOT = Path(__file__).resolve().parents[1]


def _raw() -> dict:
    return json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))


class MaxActiveSafetyOrdersTests(unittest.TestCase):
    def test_field_present_explicitly_as_null_in_paper_json(self):
        raw = _raw()
        self.assertIn("max_active_safety_orders", raw)
        self.assertIsNone(raw["max_active_safety_orders"])

    def test_none_defaults_effective_to_safety_count(self):
        config = Config.parse(_raw())
        self.assertIsNone(config.max_active_safety_orders)
        self.assertEqual(config.effective_max_active_safety_orders, config.safety_count)

    def test_missing_field_also_defaults_like_none(self):
        raw = _raw()
        del raw["max_active_safety_orders"]
        config = Config.parse(raw)
        self.assertIsNone(config.max_active_safety_orders)
        self.assertEqual(config.effective_max_active_safety_orders, config.safety_count)

    def test_explicit_value_within_range_is_accepted(self):
        raw = _raw()
        raw["max_active_safety_orders"] = 1
        config = Config.parse(raw)
        self.assertEqual(config.effective_max_active_safety_orders, 1)

    def test_value_above_safety_count_is_rejected_not_clamped(self):
        raw = _raw()  # safety_count=2
        raw["max_active_safety_orders"] = 3
        with self.assertRaises(ValueError):
            Config.parse(raw)

    def test_zero_value_is_rejected_when_safety_count_positive(self):
        raw = _raw()
        raw["max_active_safety_orders"] = 0
        with self.assertRaises(ValueError):
            Config.parse(raw)

    def test_zero_safety_count_requires_none_or_zero(self):
        raw = _raw()
        raw["safety_count"] = 0
        raw["max_active_safety_orders"] = 1
        with self.assertRaises(ValueError):
            Config.parse(raw)

    def test_zero_safety_count_with_none_is_effective_zero(self):
        raw = _raw()
        raw["safety_count"] = 0
        raw["max_active_safety_orders"] = None
        config = Config.parse(raw)
        self.assertEqual(config.effective_max_active_safety_orders, 0)

    def test_zero_safety_count_with_explicit_zero_is_accepted(self):
        raw = _raw()
        raw["safety_count"] = 0
        raw["max_active_safety_orders"] = 0
        config = Config.parse(raw)
        self.assertEqual(config.effective_max_active_safety_orders, 0)

    def test_non_integer_value_is_rejected(self):
        raw = _raw()
        raw["max_active_safety_orders"] = "2"
        with self.assertRaises(ValueError):
            Config.parse(raw)

    def test_negative_value_is_rejected(self):
        raw = _raw()
        raw["max_active_safety_orders"] = -1
        with self.assertRaises(ValueError):
            Config.parse(raw)

    def test_parse_does_not_mutate_callers_dict(self):
        raw = _raw()
        before = dict(raw)
        Config.parse(raw)
        self.assertEqual(raw, before)


if __name__ == "__main__":
    unittest.main()
