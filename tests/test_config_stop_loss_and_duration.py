"""Faz 17 H.2-motor (RG-11): `Config.stop_loss_rate`/`stop_loss_confirmation_bars`
(bar-count confirmation only -- no seconds-based mode, per the data-resolution
warning) and `max_deal_duration_seconds`/`max_deal_duration_action`
(explicit action enum required, no universal sector default). Both pairs
default to null/null -- OFF, byte-for-byte backward compatible."""
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
    def test_paper_json_has_neither_field(self):
        raw = _raw()
        for field in (
            "stop_loss_rate", "stop_loss_confirmation_bars",
            "max_deal_duration_seconds", "max_deal_duration_action",
        ):
            self.assertNotIn(field, raw)

    def test_absence_defaults_to_all_null(self):
        config = Config.parse(_raw())
        self.assertIsNone(config.stop_loss_rate)
        self.assertIsNone(config.stop_loss_confirmation_bars)
        self.assertIsNone(config.max_deal_duration_seconds)
        self.assertIsNone(config.max_deal_duration_action)


class StopLossValidationTests(unittest.TestCase):
    def test_valid_pair_is_accepted(self):
        config = Config.parse(_raw(stop_loss_rate="0.05", stop_loss_confirmation_bars=3))
        self.assertEqual(config.stop_loss_confirmation_bars, 3)

    def test_rate_without_bars_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(stop_loss_rate="0.05"))

    def test_bars_without_rate_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(stop_loss_confirmation_bars=3))

    def test_rate_out_of_range_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(stop_loss_rate="0", stop_loss_confirmation_bars=1))
        with self.assertRaises(ValueError):
            Config.parse(_raw(stop_loss_rate="1", stop_loss_confirmation_bars=1))

    def test_non_positive_bars_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(stop_loss_rate="0.05", stop_loss_confirmation_bars=0))
        with self.assertRaises(ValueError):
            Config.parse(_raw(stop_loss_rate="0.05", stop_loss_confirmation_bars=-1))


class MaxDealDurationValidationTests(unittest.TestCase):
    def test_valid_pair_is_accepted_for_each_action(self):
        for action in ("FORCE_CLOSE", "STOP_NEW_SAFETY_ORDERS", "WARN_ONLY", "FREEZE"):
            config = Config.parse(_raw(max_deal_duration_seconds=3600, max_deal_duration_action=action))
            self.assertEqual(config.max_deal_duration_action, action)

    def test_seconds_without_action_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(max_deal_duration_seconds=3600))

    def test_action_without_seconds_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(max_deal_duration_action="FORCE_CLOSE"))

    def test_invalid_action_value_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(max_deal_duration_seconds=3600, max_deal_duration_action="CANCEL_EVERYTHING"))

    def test_non_positive_seconds_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(max_deal_duration_seconds=0, max_deal_duration_action="WARN_ONLY"))


if __name__ == "__main__":
    unittest.main()
