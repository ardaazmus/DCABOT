"""Faz G1-kalan/a: sector giris kapilari -- parse + derive.

`cooldown_seconds`/`min_price`/`max_price` opsiyoneldir: G1-oncesi
kayitlar (yonsuz) ve yon-donemi kayitlar (kapisiz) aynen calisir.
"""
import json
import unittest
from fractions import Fraction as Q
from pathlib import Path

from dcabot.application.sector_dca import (
    SectorDcaError,
    SymbolRules,
    derive_deal_config,
    parse_sector_dca,
)
from dcabot.domain.config import Config

ROOT = Path(__file__).resolve().parents[1]
RULES = SymbolRules("BTCUSDT", "TRADING", "BTC", "USDT", "0.01", "0.001", "0.001", "5")
TEMPLATE = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))


def _raw(**overrides):
    body = dict(
        symbol="BTCUSDT", base_order="100", safety_order="100", max_safety_orders=2,
        max_active_safety_orders=None, price_deviation="10", safety_order_volume_scale="1",
        safety_order_step_scale="1", take_profit="5", stop_loss=None, direction="LONG",
        cooldown_seconds=0, min_price=None, max_price=None,
    )
    body.update(overrides)
    return body


class SectorGatesParseTests(unittest.TestCase):
    def test_gates_parsed(self):
        params = parse_sector_dca(_raw(cooldown_seconds=300, min_price="90", max_price="110"))
        self.assertEqual(params.cooldown_seconds, 300)
        self.assertEqual(params.min_price, Q(90))
        self.assertEqual(params.max_price, Q(110))

    def test_gates_default_when_absent(self):
        body = _raw()
        del body["cooldown_seconds"]
        del body["min_price"]
        del body["max_price"]
        params = parse_sector_dca(body)
        self.assertEqual(params.cooldown_seconds, 0)
        self.assertIsNone(params.min_price)
        self.assertIsNone(params.max_price)

    def test_pre_g1_ten_field_payload_still_parses(self):
        body = _raw()
        for key in ("direction", "cooldown_seconds", "min_price", "max_price"):
            del body[key]
        params = parse_sector_dca(body)
        self.assertEqual(params.direction, "LONG")
        self.assertEqual(params.cooldown_seconds, 0)

    def test_unknown_extra_field_still_rejected(self):
        body = _raw()
        body["extra"] = "1"
        with self.assertRaises(SectorDcaError):
            parse_sector_dca(body)

    def test_missing_required_field_still_rejected(self):
        body = _raw()
        del body["take_profit"]
        with self.assertRaises(SectorDcaError):
            parse_sector_dca(body)

    def test_bad_cooldown_rejected_with_field(self):
        for bad in (-5, "300", 31_536_001):
            with self.subTest(bad=bad):
                with self.assertRaises(SectorDcaError) as ctx:
                    parse_sector_dca(_raw(cooldown_seconds=bad))
                self.assertEqual(ctx.exception.field, "cooldown_seconds")

    def test_bad_min_price_rejected_with_field(self):
        for bad in ("abc", "0", "-9"):
            with self.subTest(bad=bad):
                with self.assertRaises(SectorDcaError) as ctx:
                    parse_sector_dca(_raw(min_price=bad))
                self.assertEqual(ctx.exception.field, "min_price")

    def test_min_above_max_rejected(self):
        with self.assertRaises(SectorDcaError) as ctx:
            parse_sector_dca(_raw(min_price="110", max_price="90"))
        self.assertEqual(ctx.exception.field, "min_price")


class SectorGatesDeriveTests(unittest.TestCase):
    def test_derive_carries_gates_into_config(self):
        raw = derive_deal_config(
            parse_sector_dca(_raw(cooldown_seconds=300, min_price="90", max_price="110")),
            rules=RULES, reference_price=Q(100), budget=Q(1000), template=TEMPLATE,
        )
        self.assertEqual(raw["cooldown_seconds"], 300)
        self.assertEqual(raw["min_entry_price"], "90")
        self.assertEqual(raw["max_entry_price"], "110")
        config = Config.parse(raw)
        self.assertEqual(config.cooldown_seconds, 300)
        self.assertEqual(config.min_entry_price, Q(90))
        self.assertEqual(config.max_entry_price, Q(110))

    def test_derive_defaults_gates_open(self):
        body = _raw()
        del body["cooldown_seconds"]
        del body["min_price"]
        del body["max_price"]
        raw = derive_deal_config(
            parse_sector_dca(body),
            rules=RULES, reference_price=Q(100), budget=Q(1000), template=TEMPLATE,
        )
        config = Config.parse(raw)
        self.assertEqual(config.cooldown_seconds, 0)
        self.assertIsNone(config.min_entry_price)
        self.assertIsNone(config.max_entry_price)


if __name__ == "__main__":
    unittest.main()
