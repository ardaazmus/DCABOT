"""Faz 17 G.1-motor (RG-06): `Config.margin_mode` is MANDATORY (ISOLATED |
CROSS) -- unlike every other Faz 17 Config addition, there is no default and
no silent fall-through to the venue's own default. Absence is a config
error, not an implicit choice.
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


class MarginModeMandatoryTests(unittest.TestCase):
    def test_paper_json_declares_margin_mode_explicitly(self):
        raw = _raw()
        self.assertIn("margin_mode", raw)
        self.assertIn(raw["margin_mode"], ("ISOLATED", "CROSS"))

    def test_missing_field_is_rejected_not_defaulted(self):
        raw = _raw()
        del raw["margin_mode"]
        with self.assertRaises(ValueError):
            Config.parse(raw)

    def test_invalid_value_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(margin_mode="SPOT"))
        with self.assertRaises(ValueError):
            Config.parse(_raw(margin_mode="isolated"))

    def test_isolated_and_cross_are_both_accepted(self):
        self.assertEqual(Config.parse(_raw(margin_mode="ISOLATED")).margin_mode, "ISOLATED")
        self.assertEqual(Config.parse(_raw(margin_mode="CROSS")).margin_mode, "CROSS")


if __name__ == "__main__":
    unittest.main()
