"""Faz G1-kalan/b: futures DCA paper -- market + kaldirac.

Spot degismez (kaldirac 1, tam teminat). Futures isolated 1..10x
(default 3): gereke fon marjindir (notional/kaldirac, para
kuantumuna YUKARI yuvarlanir -- tutucu tahmin), notional tavan
butce*kaldirac'tir. Likidasyon motoru yok (G3); -%99 halt backstop'tur.

Elde hesap (LONG, ref 100, 2 kademe): notional 299.99, ucret
0.29999; 3x marj 99.99666667, gereken 100.29665667 (kuantum 1e-8).
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


class FuturesParseTests(unittest.TestCase):
    def test_market_defaults_to_spot_with_leverage_one(self):
        params = parse_sector_dca(_raw())
        self.assertEqual((params.market_type, params.leverage), ("SPOT", 1))

    def test_futures_defaults_to_isolated_3x(self):
        params = parse_sector_dca(_raw(market_type="FUTURES"))
        self.assertEqual((params.market_type, params.leverage), ("FUTURES", 3))

    def test_explicit_leverage_within_range(self):
        self.assertEqual(parse_sector_dca(_raw(market_type="FUTURES", leverage=10)).leverage, 10)
        self.assertEqual(parse_sector_dca(_raw(market_type="FUTURES", leverage=1)).leverage, 1)
        self.assertEqual(parse_sector_dca(_raw(leverage=1)).leverage, 1)

    def test_spot_rejects_leverage_above_one(self):
        with self.assertRaises(SectorDcaError) as ctx:
            parse_sector_dca(_raw(leverage=3))
        self.assertEqual(ctx.exception.code, "SECTOR_FIELD_OUT_OF_RANGE")
        self.assertEqual(ctx.exception.field, "leverage")

    def test_futures_rejects_leverage_outside_1_to_10(self):
        for bad in (0, -1, 11, 125, "3"):
            with self.subTest(bad=bad):
                with self.assertRaises(SectorDcaError) as ctx:
                    parse_sector_dca(_raw(market_type="FUTURES", leverage=bad))
                self.assertEqual(ctx.exception.field, "leverage")

    def test_unknown_market_rejected(self):
        with self.assertRaises(SectorDcaError) as ctx:
            parse_sector_dca(_raw(market_type="MARGIN"))
        self.assertEqual(ctx.exception.code, "SECTOR_FIELD_INVALID")
        self.assertEqual(ctx.exception.field, "market_type")


class FuturesDeriveTests(unittest.TestCase):
    def test_derive_maps_leverage_and_scales_notional_cap(self):
        raw = derive_deal_config(
            parse_sector_dca(_raw(market_type="FUTURES", leverage=3)),
            rules=RULES, reference_price=Q(100), budget=Q(1000), template=TEMPLATE,
        )
        self.assertEqual(raw["leverage"], "3")
        self.assertEqual(raw["margin_mode"], "ISOLATED")
        self.assertEqual(raw["max_entry_notional"], "3000")
        self.assertEqual(raw["initial_equity"], "1000")
        self.assertEqual(Config.parse(raw).leverage, Q(3))

    def test_spot_derive_unchanged(self):
        raw = derive_deal_config(
            parse_sector_dca(_raw()), rules=RULES, reference_price=Q(100),
            budget=Q(1000), template=TEMPLATE,
        )
        self.assertEqual(raw["leverage"], "1")
        self.assertEqual(raw["max_entry_notional"], "1000")

    def test_summarize_futures_margin_rounded_up_to_money_quantum(self):
        raw = derive_deal_config(
            parse_sector_dca(_raw(market_type="FUTURES", leverage=3)),
            rules=RULES, reference_price=Q(100), budget=Q(1000), template=TEMPLATE,
        )
        summary = summarize_deal_plan(raw, Q(100))
        self.assertEqual(summary["orders_total"], "299.99")
        self.assertEqual(summary["estimated_fees"], "0.29999")
        # 299.99/3 = 99.99666... -> 99.99666667 (yukari) + 0.29999.
        self.assertEqual(summary["required_funds"], "100.29665667")
        self.assertEqual(summary["budget"], "1000")
        self.assertIs(summary["within_budget"], True)

    def test_summarize_spot_required_funds_unchanged(self):
        raw = derive_deal_config(
            parse_sector_dca(_raw()), rules=RULES, reference_price=Q(100),
            budget=Q(1000), template=TEMPLATE,
        )
        summary = summarize_deal_plan(raw, Q(100))
        self.assertEqual(summary["required_funds"], "300.28999")
        self.assertEqual(summary["budget"], "1000")

    def test_margin_rounding_is_up_not_half_even(self):
        raw = dict(TEMPLATE)
        raw.update(
            symbol="BTCUSDT", base_asset="BTC", quote_asset="USDT",
            base_qty="0.001", safety_qty="0.001", safety_count=0,
            max_active_safety_orders=None, base_sizing="BASE", safety_sizing="BASE",
            tick="0.01", qty_step="0.001", min_qty="0.001", min_notional="0.01",
            initial_equity="10000", max_entry_notional="30000", minimum_equity="0",
            leverage="3", margin_mode="ISOLATED", take_profit_ladder=None,
            stop_loss_rate=None, stop_loss_confirmation_bars=None,
        )
        summary = summarize_deal_plan(raw, Q(100))
        # 0.1/3 = 0.03333... -> 0.03333334 (yukari; half-even 0.03333333
        # verirdi) + 0.0001 ucret.
        self.assertEqual(summary["required_funds"], "0.03343334")


if __name__ == "__main__":
    unittest.main()
