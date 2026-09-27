"""Faz W-B4 motor: MANUEL emir rolu (3Commas "Add funds" karsiligi).

Acik deal'e plan disi ek alim:fonksiyon olarak safety dolumu gibi
ortalamaya girer ama plan endeksini tuketmez ve tetiklenme sarti aramaz
(kullanici acikca tikladi). Red kurallari safety ile aynidir: acik deal
yoksa, motor durmussa (halted) veya bloklayici varsa, bakiye/grid disi
miktarda. Plan bitmis olsa bile kabul edilir -- fon eklemenin anlami bu.
"""
import json
import unittest
from fractions import Fraction as F
from pathlib import Path

from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply, decision
from dcabot.domain.numbers import exact_text

ROOT = Path(__file__).resolve().parents[1]


def config():
    raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
    return Config.parse(raw)


def _mark(state, config, price):
    return apply(state, {"type": "MARK", "price": price}, config)


def _intent(state, config, order_id, role, qty, price):
    return apply(
        state,
        {"type": "INTENT", "order_id": order_id, "role": role, "qty": qty, "limit_price": price},
        config,
    )


def _fill(state, config, order_id, price, qty, fee="0"):
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
        config,
    )
    return apply(
        state,
        {"type": "ORDER_FINAL", "order_id": order_id, "status": "FILLED", "filled_qty": qty, "coverage_complete": True},
        config,
    )


def _open_deal(config):
    state = _mark(State(), config, "100")
    state = _intent(state, config, "base", "BASE", "1", "100")
    return _fill(state, config, "base", "100", "1")


class ManualOrderTests(unittest.TestCase):
    def test_manual_buy_joins_open_deal_and_keeps_anchor(self):
        config_ = config()
        state = _open_deal(config_)
        state = _intent(state, config_, "m1", "MANUAL:1", "1", "100")
        self.assertEqual(state.orders["m1"].side, "BUY")
        state = _fill(state, config_, "m1", "100", "1")
        self.assertEqual(state.position.qty, F(2))
        self.assertEqual(state.position.cost, F(200))
        self.assertEqual(state.anchor, F(100))

    def test_manual_buy_at_lower_price_averages_down(self):
        config_ = config()
        state = _open_deal(config_)
        state = _mark(state, config_, "90")
        state = _intent(state, config_, "m1", "MANUAL:1", "1", "90")
        state = _fill(state, config_, "m1", "90", "1")
        self.assertEqual(state.position.qty, F(2))
        self.assertEqual(state.position.cost, F(190))
        self.assertEqual(state.position.average, F(95))

    def test_manual_rejected_without_open_deal(self):
        config_ = config()
        state = _mark(State(), config_, "100")
        with self.assertRaises(ValueError):
            _intent(state, config_, "m1", "MANUAL:1", "1", "100")

    def test_manual_rejected_when_halted(self):
        config_ = config()
        state = _open_deal(config_)
        state.halted = True
        with self.assertRaises(ValueError):
            _intent(state, config_, "m1", "MANUAL:1", "1", "100")

    def test_manual_accepted_after_plan_exhausted(self):
        config_ = config()
        state = _open_deal(config_)
        plan = config_.plan(F(100))
        low1, low2 = exact_text(plan[0].price), exact_text(plan[1].price)
        state = _mark(state, config_, low1)
        state = _intent(state, config_, "so1", "SAFETY:1", "1", low1)
        state = _fill(state, config_, "so1", low1, "1")
        state = _mark(state, config_, low2)
        state = _intent(state, config_, "so2", "SAFETY:2", "1", low2)
        state = _fill(state, config_, "so2", low2, "1")
        with self.assertRaises(ValueError):
            _intent(state, config_, "so3", "SAFETY:3", "1", low2)
        state = _intent(state, config_, "m1", "MANUAL:1", "1", low2)
        state = _fill(state, config_, "m1", low2, "1")
        self.assertEqual(state.position.qty, F(4))

    def test_manual_index_must_be_sequential(self):
        config_ = config()
        state = _open_deal(config_)
        with self.assertRaises(ValueError):
            _intent(state, config_, "m2", "MANUAL:2", "1", "100")
        state = _intent(state, config_, "m1", "MANUAL:1", "1", "100")
        state = _fill(state, config_, "m1", "100", "1")
        state = _intent(state, config_, "m2", "MANUAL:2", "1", "100")
        state = _fill(state, config_, "m2", "100", "1")
        self.assertEqual(state.position.qty, F(3))

    def test_manual_below_minimum_rejected(self):
        config_ = config()
        state = _open_deal(config_)
        with self.assertRaises(ValueError):
            _intent(state, config_, "m1", "MANUAL:1", "0.001", "0.01")

    def test_manual_does_not_disturb_safety_indexing(self):
        config_ = config()
        state = _open_deal(config_)
        state = _intent(state, config_, "m1", "MANUAL:1", "1", "100")
        state = _fill(state, config_, "m1", "100", "1")
        state = _mark(state, config_, "90")
        proposal = decision(state, config_)
        self.assertIsNotNone(proposal)
        assert proposal is not None
        self.assertEqual(proposal[0], "SAFETY:1")
        state = _intent(state, config_, "so1", "SAFETY:1", "1", "90")
        state = _fill(state, config_, "so1", "90", "1")
        self.assertEqual(state.position.qty, F(3))

    def test_second_manual_blocked_while_first_unsettled(self):
        config_ = config()
        state = _open_deal(config_)
        state = _intent(state, config_, "m1", "MANUAL:1", "1", "100")
        with self.assertRaises(ValueError):
            _intent(state, config_, "m2", "MANUAL:2", "1", "100")


if __name__ == "__main__":
    unittest.main()
