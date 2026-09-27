"""Faz W-B4: deal aksiyonlari -- close at market, cancel, add funds.

3Commas/Bitsgap paritesi: acik deal kullanici mudahalesiyle o anki
piyasa fiyatindan kapatilir (ucretli, exact PnL), satis yapilmadan iptal
edilir (kâr "0", alis ucretleri batik), veya plana dokunmadan fon
eklenir (MANUAL sira, safety endeksi tuketmez). Tum tutarlar elde
hesaplanmis degerlerle kilitlenir.
"""
import json
import unittest
from fractions import Fraction as F
from pathlib import Path

from dcabot.application.deal_actions import DealActionError, add_funds, cancel_deal, close_at_market
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply
from dcabot.persistence.bot_store import BotDeal

ROOT = Path(__file__).resolve().parents[1]
BOT = "bot_test"


def config():
    raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
    return Config.parse(raw)


def _fill(state, config_, order_id, role, qty, price, fee):
    state = apply(state, {"type": "MARK", "price": price}, config_)
    state = apply(
        state,
        {"type": "INTENT", "order_id": order_id, "role": role, "qty": qty, "limit_price": price},
        config_,
    )
    side = state.orders[order_id].side
    state = apply(
        state,
        {
            "type": "FILL",
            "execution_id": f"{order_id}-fill",
            "order_id": order_id,
            "side": side,
            "qty": qty,
            "price": price,
            "fee": fee,
            "fee_asset": "USDT",
        },
        config_,
    )
    return apply(
        state,
        {"type": "ORDER_FINAL", "order_id": order_id, "status": "FILLED", "filled_qty": qty, "coverage_complete": True},
        config_,
    )


def _open_deal(config_):
    """BASE 1@100 (fee 0.1) + SO1 1@90 (fee 0.09): qty 2, cost 190."""
    state = _fill(State(), config_, "base", "BASE", "1", "100", "0.1")
    return _fill(state, config_, "so1", "SAFETY:1", "1", "90", "0.09")


def _deal(**overrides):
    body = {"bot_id": BOT, "deal_sequence": 1, "started_at_us": 1000, "closed_at_us": None,
            "safety_orders_filled": 1, "profit": None, "close_reason": None}
    body.update(overrides)
    return BotDeal(**body)


class CloseAtMarketTests(unittest.TestCase):
    def test_close_at_market_realizes_exact_pnl(self):
        config_ = config()
        result = close_at_market(config_, _open_deal(config_), _deal(), F(0), price=F(100), now_us=2000)
        # Satis 2@100 = 200, maliyet 190 -> kazanc 10; ucret 0.1+0.09+0.2.
        self.assertEqual(result.deal.profit, "9.61")
        self.assertEqual(result.deal.close_reason, "MANUAL_CLOSE")
        self.assertEqual(result.deal.closed_at_us, 2000)
        self.assertEqual(result.deal.safety_orders_filled, 1)
        self.assertEqual(result.state.position.qty, F(0))
        self.assertEqual(result.prev_net, F("9.61"))
        self.assertEqual(result.event.kind, "DEAL_CLOSED")
        self.assertEqual(result.event.detail["reason"], "MANUAL_CLOSE")
        self.assertEqual(result.event.detail["profit"], "9.61")
        self.assertEqual(result.event.detail["price"], "100")
        self.assertEqual(result.event.detail["qty"], "2")
        self.assertEqual(result.event.detail["fee"], "0.2")

    def test_close_rejects_closed_deal(self):
        config_ = config()
        deal = _deal(closed_at_us=1500, profit="1", close_reason="TAKE_PROFIT")
        with self.assertRaises(DealActionError):
            close_at_market(config_, _open_deal(config_), deal, F(0), price=F(100), now_us=2000)

    def test_close_rejects_flat_position(self):
        config_ = config()
        state = apply(State(), {"type": "MARK", "price": "100"}, config_)
        with self.assertRaises(DealActionError):
            close_at_market(config_, state, _deal(), F(0), price=F(100), now_us=2000)


class CancelDealTests(unittest.TestCase):
    def test_cancel_flattens_without_sale(self):
        config_ = config()
        result = cancel_deal(config_, _open_deal(config_), _deal(), F(0), now_us=2000)
        self.assertEqual(result.deal.profit, "0")
        self.assertEqual(result.deal.close_reason, "CANCELLED")
        self.assertEqual(result.deal.closed_at_us, 2000)
        self.assertEqual(result.state.position.qty, F(0))
        self.assertEqual(result.state.position.cost, F(0))
        self.assertIsNone(result.state.anchor)
        self.assertEqual(result.state.orders, {})
        # Alis ucretleri batik: state degismez, net ayni kalir.
        self.assertEqual(result.state.fees, F("0.19"))
        self.assertEqual(result.state.realized, F(0))
        self.assertEqual(result.prev_net, F(0))
        self.assertEqual(result.event.detail["reason"], "CANCELLED")

    def test_cancel_rejects_closed_deal(self):
        config_ = config()
        deal = _deal(closed_at_us=1500, profit="1", close_reason="TAKE_PROFIT")
        with self.assertRaises(DealActionError):
            cancel_deal(config_, _open_deal(config_), deal, F(0), now_us=2000)


class AddFundsTests(unittest.TestCase):
    def test_add_funds_buys_outside_plan(self):
        config_ = config()
        result = add_funds(config_, _open_deal(config_), _deal(), F(0), quote_amount=F(100), price=F(100), now_us=2000)
        self.assertEqual(result.state.position.qty, F(3))
        self.assertEqual(result.state.position.cost, F(290))
        self.assertEqual(result.deal.manual_orders_filled, 1)
        self.assertEqual(result.deal.safety_orders_filled, 1)
        self.assertIsNone(result.deal.closed_at_us)
        self.assertEqual(result.event.kind, "MANUAL_ORDER_FILLED")
        self.assertEqual(result.event.detail["index"], 1)
        self.assertEqual(result.event.detail["qty"], "1")
        self.assertEqual(result.event.detail["fee"], "0.1")

    def test_add_funds_index_increments(self):
        config_ = config()
        first = add_funds(config_, _open_deal(config_), _deal(), F(0), quote_amount=F(100), price=F(100), now_us=2000)
        second = add_funds(config_, first.state, first.deal, F(0), quote_amount=F(50), price=F(100), now_us=3000)
        self.assertEqual(second.deal.manual_orders_filled, 2)
        self.assertEqual(second.event.detail["index"], 2)
        self.assertEqual(second.state.position.qty, F("3.5"))

    def test_add_funds_dust_rejected(self):
        config_ = config()
        with self.assertRaises(DealActionError):
            add_funds(config_, _open_deal(config_), _deal(), F(0), quote_amount=F("0.001"), price=F(100), now_us=2000)

    def test_add_funds_rejects_closed_deal(self):
        config_ = config()
        deal = _deal(closed_at_us=1500, profit="1", close_reason="TAKE_PROFIT")
        with self.assertRaises(DealActionError):
            add_funds(config_, _open_deal(config_), deal, F(0), quote_amount=F(100), price=F(100), now_us=2000)


if __name__ == "__main__":
    unittest.main()
