"""Faz 17 C.1: Config.direction alanı (varsayılan LONG, geriye uyumlu)."""
import json
import unittest
from pathlib import Path

from dcabot.domain.config import Config

ROOT = Path(__file__).resolve().parents[1]


def _raw() -> dict:
    return json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))


class ConfigDirectionTests(unittest.TestCase):
    def test_direction_defaults_to_long_when_absent(self):
        raw = _raw()
        self.assertNotIn("direction", raw)
        config = Config.parse(raw)
        self.assertEqual(config.direction, "LONG")

    def test_explicit_short_direction_accepted(self):
        raw = _raw()
        raw["direction"] = "SHORT"
        config = Config.parse(raw)
        self.assertEqual(config.direction, "SHORT")

    def test_explicit_long_direction_accepted(self):
        raw = _raw()
        raw["direction"] = "LONG"
        config = Config.parse(raw)
        self.assertEqual(config.direction, "LONG")

    def test_invalid_direction_value_rejected(self):
        raw = _raw()
        raw["direction"] = "SIDEWAYS"
        with self.assertRaises(ValueError):
            Config.parse(raw)

    def test_unknown_extra_field_still_rejected(self):
        raw = _raw()
        raw["bogus_field"] = "x"
        with self.assertRaises(ValueError):
            Config.parse(raw)

    def test_parse_does_not_mutate_callers_dict(self):
        raw = _raw()
        before = dict(raw)
        Config.parse(raw)
        self.assertEqual(raw, before)
        self.assertNotIn("direction", raw)

    def test_short_config_plan_ascends_above_anchor(self):
        from fractions import Fraction as F

        raw = _raw()
        raw["direction"] = "SHORT"
        config = Config.parse(raw)
        anchor = F(100)
        plan = config.plan(anchor)
        prices = [level.price for level in plan]
        self.assertEqual(prices, sorted(prices))
        self.assertTrue(all(price > anchor for price in prices))

    def test_long_config_plan_unchanged_by_default(self):
        from fractions import Fraction as F

        raw = _raw()
        config = Config.parse(raw)
        anchor = F(100)
        plan = config.plan(anchor)
        prices = [level.price for level in plan]
        self.assertEqual(prices, sorted(prices, reverse=True))
        self.assertTrue(all(price < anchor for price in prices))


if __name__ == "__main__":
    unittest.main()
