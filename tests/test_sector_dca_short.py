"""Faz G1: SHORT sector DCA -- parse, derive, summarize ters yonde calisir.

Elde hesaplanmis degerler (referans 100, sapma %10, adim 1, TP %5):
kademeler 110/120 (yukarida, artan), TP 95 (asagida), kapsam %20.
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
    summarize_deal_plan,
)
from dcabot.domain.config import Config
from dcabot.domain.numbers import exact_text

ROOT = Path(__file__).resolve().parents[1]
RULES = SymbolRules("BTCUSDT", "TRADING", "BTC", "USDT", "0.01", "0.001", "0.001", "5")
TEMPLATE = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))


def _raw(**overrides):
    body = dict(
        symbol="BTCUSDT", base_order="100", safety_order="100", max_safety_orders=2,
        max_active_safety_orders=None, price_deviation="10", safety_order_volume_scale="1",
        safety_order_step_scale="1", take_profit="5", stop_loss=None, direction="SHORT",
    )
    body.update(overrides)
    return body


class SectorShortParseTests(unittest.TestCase):
    def test_parse_accepts_short(self):
        self.assertEqual(parse_sector_dca(_raw()).direction, "SHORT")

    def test_parse_accepts_long(self):
        self.assertEqual(parse_sector_dca(_raw(direction="LONG")).direction, "LONG")

    def test_parse_rejects_bad_direction(self):
        with self.assertRaises(SectorDcaError):
            parse_sector_dca(_raw(direction="LONGG"))

    def test_legacy_ten_field_payload_defaults_to_long(self):
        """Pre-G1 stored strategies lack direction; they stay LONG, everything
        else about the strict field set is unchanged."""
        body = _raw()
        del body["direction"]
        self.assertEqual(parse_sector_dca(body).direction, "LONG")
        body["direction"] = "SHORT"
        body["extra"] = "1"
        with self.assertRaises(SectorDcaError):
            parse_sector_dca(body)


class SectorShortDeriveTests(unittest.TestCase):
    def test_derive_short_inverts_ladder(self):
        raw = derive_deal_config(
            parse_sector_dca(_raw()), rules=RULES, reference_price=Q(100),
            budget=Q(1000), template=TEMPLATE,
        )
        self.assertEqual(raw["direction"], "SHORT")
        config = Config.parse(raw)
        plan = config.plan(Q(100))
        self.assertEqual([exact_text(level.price) for level in plan], ["110", "120"])
        self.assertEqual([exact_text(level.qty) for level in plan], ["0.909", "0.833"])

    def test_summarize_short_exact(self):
        raw = derive_deal_config(
            parse_sector_dca(_raw()), rules=RULES, reference_price=Q(100),
            budget=Q(1000), template=TEMPLATE,
        )
        summary = summarize_deal_plan(raw, Q(100))
        self.assertEqual(summary["base_price"], "100")
        self.assertEqual([row["price"] for row in summary["safety_orders"]], ["110", "120"])
        self.assertEqual(
            [row["deviation_percent"] for row in summary["safety_orders"]], ["10", "20"]
        )
        self.assertEqual(summary["take_profit_price"], "95")
        self.assertEqual(summary["price_coverage_percent"], "20")
        # Emirler 100 + 99.99 + 99.96; ucretler 0.1 + 0.09999 + 0.09996.
        self.assertEqual(summary["orders_total"], "299.95")
        self.assertEqual(summary["estimated_fees"], "0.29995")
        self.assertEqual(summary["required_funds"], "300.24995")
        self.assertIsNone(summary["stop_loss_price_initial"])

    def test_summarize_short_stop_loss_above(self):
        raw = derive_deal_config(
            parse_sector_dca(_raw(stop_loss="10")), rules=RULES, reference_price=Q(100),
            budget=Q(1000), template=TEMPLATE,
        )
        summary = summarize_deal_plan(raw, Q(100))
        self.assertEqual(summary["stop_loss_price_initial"], "110")


if __name__ == "__main__":
    unittest.main()
