"""Faz G1-kalan/a: Config giris kapilari -- cooldown + fiyat bandi.

cooldown_seconds yoksa 0 (kapali); min/max_entry_price yoksa None
(bant yok). Tum alanlar geriye uyumlu: eski config dosyalari ve
hash'ler bayt bayt ayni kalir.
"""
import json
import unittest
from fractions import Fraction as Q
from pathlib import Path

from dcabot.domain.config import Config

ROOT = Path(__file__).resolve().parents[1]


def _raw() -> dict:
    return json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))


class ConfigEntryGatesTests(unittest.TestCase):
    def test_gates_default_to_open_when_absent(self):
        raw = _raw()
        self.assertNotIn("cooldown_seconds", raw)
        self.assertNotIn("min_entry_price", raw)
        self.assertNotIn("max_entry_price", raw)
        config = Config.parse(raw)
        self.assertEqual(config.cooldown_seconds, 0)
        self.assertIsNone(config.min_entry_price)
        self.assertIsNone(config.max_entry_price)

    def test_explicit_gates_accepted(self):
        raw = _raw()
        raw["cooldown_seconds"] = 3600
        raw["min_entry_price"] = "90.5"
        raw["max_entry_price"] = "110"
        config = Config.parse(raw)
        self.assertEqual(config.cooldown_seconds, 3600)
        self.assertEqual(config.min_entry_price, Q("90.5"))
        self.assertEqual(config.max_entry_price, Q(110))

    def test_single_sided_band_accepted(self):
        raw = _raw()
        raw["min_entry_price"] = "90"
        self.assertEqual(Config.parse(raw).min_entry_price, Q(90))
        raw = _raw()
        raw["max_entry_price"] = "110"
        parsed = Config.parse(raw)
        self.assertIsNone(parsed.min_entry_price)
        self.assertEqual(parsed.max_entry_price, Q(110))

    def test_cooldown_must_be_an_integer_in_range(self):
        for bad in (-1, "60", 60.0, None, 31_536_001):
            with self.subTest(bad=bad):
                raw = _raw()
                raw["cooldown_seconds"] = bad
                with self.assertRaises(ValueError):
                    Config.parse(raw)

    def test_cooldown_bool_rejected(self):
        raw = _raw()
        raw["cooldown_seconds"] = True
        with self.assertRaises(ValueError):
            Config.parse(raw)

    def test_entry_prices_must_be_positive_decimals(self):
        for field in ("min_entry_price", "max_entry_price"):
            for bad in ("abc", "0", "-5", "-0.01"):
                with self.subTest(field=field, bad=bad):
                    raw = _raw()
                    raw[field] = bad
                    with self.assertRaises(ValueError):
                        Config.parse(raw)

    def test_min_above_max_rejected(self):
        raw = _raw()
        raw["min_entry_price"] = "110"
        raw["max_entry_price"] = "90"
        with self.assertRaises(ValueError):
            Config.parse(raw)

    def test_payload_round_trip_preserves_gates(self):
        from dcabot.persistence.spot_binding_store import _config_payload

        raw = _raw()
        raw["cooldown_seconds"] = 300
        raw["min_entry_price"] = "90"
        parsed = Config.parse(_config_payload(Config.parse(raw)))
        self.assertEqual(parsed.cooldown_seconds, 300)
        self.assertEqual(parsed.min_entry_price, Q(90))
        self.assertIsNone(parsed.max_entry_price)

    def test_parse_does_not_mutate_callers_dict(self):
        raw = _raw()
        raw["cooldown_seconds"] = 60
        raw["min_entry_price"] = "90"
        before = dict(raw)
        Config.parse(raw)
        self.assertEqual(raw, before)


if __name__ == "__main__":
    unittest.main()
