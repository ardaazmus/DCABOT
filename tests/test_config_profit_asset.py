"""Faz 17 I.1-motor (RG-12): `Config.profit_asset` -- exactly base_asset,
quote_asset, or null (defaults to quote_asset, today's unchanged implicit
behavior). No arbitrary third coin (research: none of 3Commas/Pionex/
Bitsgap/Freqtrade offer that; it would require a live conversion trade this
engine does not execute)."""
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
    def test_paper_json_has_no_profit_asset(self):
        self.assertNotIn("profit_asset", _raw())

    def test_absence_defaults_to_quote_asset(self):
        config = Config.parse(_raw())
        self.assertIsNone(config.profit_asset)
        self.assertEqual(config.effective_profit_asset, config.quote_asset)


class ValidationTests(unittest.TestCase):
    def test_explicit_quote_asset_is_accepted(self):
        config = Config.parse(_raw(profit_asset="USDT"))
        self.assertEqual(config.effective_profit_asset, "USDT")

    def test_explicit_base_asset_is_accepted(self):
        config = Config.parse(_raw(profit_asset="BTC"))
        self.assertEqual(config.effective_profit_asset, "BTC")

    def test_arbitrary_third_asset_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw(profit_asset="ETH"))

    def test_base_profit_with_ladder_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(
                _raw(
                    profit_asset="BTC",
                    take_profit_ladder=[["0.5", "0.01"], ["0.5", "0.02"]],
                )
            )

    def test_quote_profit_with_ladder_is_still_accepted(self):
        config = Config.parse(
            _raw(
                profit_asset="USDT",
                take_profit_ladder=[["0.5", "0.01"], ["0.5", "0.02"]],
            )
        )
        self.assertIsNotNone(config.take_profit_ladder)


if __name__ == "__main__":
    unittest.main()
