"""Faz 17 H.1-motor (RG-10): `Config.take_profit_ladder` -- additive,
default null preserves today's all-or-nothing EXIT byte-for-byte. Weights
are fractions of the ladder-START position (not the shrinking remainder),
must sum to exactly 1, and target_percent must be strictly increasing.
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
    def test_paper_json_has_no_ladder(self):
        raw = _raw()
        self.assertNotIn("take_profit_ladder", raw)

    def test_absence_defaults_to_none(self):
        config = Config.parse(_raw())
        self.assertIsNone(config.take_profit_ladder)


class LadderValidationTests(unittest.TestCase):
    def test_valid_two_level_ladder_is_parsed(self):
        config = Config.parse(_raw(take_profit_ladder=[["0.5", "0.01"], ["0.5", "0.02"]]))
        self.assertEqual(len(config.take_profit_ladder), 2)
        self.assertEqual(config.take_profit_ladder[0].weight, config.take_profit_ladder[0].weight)

    def test_single_level_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(take_profit_ladder=[["1", "0.02"]]))

    def test_weights_not_summing_to_one_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(take_profit_ladder=[["0.4", "0.01"], ["0.5", "0.02"]]))

    def test_non_increasing_target_percent_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(take_profit_ladder=[["0.5", "0.02"], ["0.5", "0.01"]]))
        with self.assertRaises(ValueError):
            Config.parse(_raw(take_profit_ladder=[["0.5", "0.02"], ["0.5", "0.02"]]))

    def test_weight_out_of_range_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(take_profit_ladder=[["0", "0.01"], ["1", "0.02"]]))
        with self.assertRaises(ValueError):
            Config.parse(_raw(take_profit_ladder=[["1.5", "0.01"], ["-0.5", "0.02"]]))

    def test_target_percent_out_of_range_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(take_profit_ladder=[["0.5", "0"], ["0.5", "0.02"]]))
        with self.assertRaises(ValueError):
            Config.parse(_raw(take_profit_ladder=[["0.5", "0.01"], ["0.5", "1"]]))

    def test_malformed_level_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(take_profit_ladder=[["0.5"], ["0.5", "0.02"]]))
        with self.assertRaises(ValueError):
            Config.parse(_raw(take_profit_ladder="not-a-list"))

    def test_net_quote_target_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(
                _raw(
                    target_mode="NET_QUOTE",
                    take_profit_ladder=[["0.5", "0.01"], ["0.5", "0.02"]],
                )
            )


class OrderTypeForRoleLadderTests(unittest.TestCase):
    def test_ladder_exit_roles_use_exit_order_type(self):
        config = Config.parse(_raw(take_profit_ladder=[["0.5", "0.01"], ["0.5", "0.02"]]))
        self.assertEqual(config.order_type_for_role("EXIT:1"), config.exit_order_type)
        self.assertEqual(config.order_type_for_role("EXIT:2"), config.exit_order_type)


if __name__ == "__main__":
    unittest.main()
