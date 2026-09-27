"""Faz 17 C.3: engine.py yön-farkındalığı (Config.direction -> Order side,
safety/take-profit tetikleyicileri, realized PnL işareti). LONG davranışı
regresyon-sıfır olmalı; SHORT yeni, ayrı test edilen bir yoldur.
"""
import json
from fractions import Fraction as F
from pathlib import Path
import unittest

from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply, decision, target

ROOT = Path(__file__).resolve().parents[1]


def raw_config(**updates):
    raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
    raw.update(updates)
    return raw


def _base_fill(state, config, *, price="100"):
    state = apply(
        state,
        {"type": "INTENT", "order_id": "base", "role": "BASE", "qty": "1", "limit_price": price},
        config,
    )
    order_side = state.orders["base"].side
    state = apply(
        state,
        {
            "type": "FILL",
            "execution_id": "base-fill",
            "order_id": "base",
            "side": order_side,
            "qty": "1",
            "price": price,
            "fee": "0",
            "fee_asset": "USDT",
        },
        config,
    )
    state = apply(
        state,
        {"type": "ORDER_FINAL", "order_id": "base", "status": "FILLED", "filled_qty": "1", "coverage_complete": True},
        config,
    )
    return state, order_side


class LongDirectionRegressionTests(unittest.TestCase):
    """Pin the pre-existing LONG behavior byte-for-byte."""

    def test_base_and_exit_sides_are_buy_and_sell(self):
        config = Config.parse(raw_config())
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state, base_side = _base_fill(state, config)
        self.assertEqual(base_side, "BUY")
        self.assertEqual(config.direction, "LONG")

        # Take-profit at average*(1+0.02) = 102
        state = apply(state, {"type": "MARK", "price": "102"}, config)
        self.assertEqual(decision(state, config), ("EXIT", F(1)))
        state = apply(
            state,
            {"type": "INTENT", "order_id": "exit", "role": "EXIT", "qty": "1", "limit_price": "102"},
            config,
        )
        self.assertEqual(state.orders["exit"].side, "SELL")
        state = apply(
            state,
            {
                "type": "FILL",
                "execution_id": "exit-fill",
                "order_id": "exit",
                "side": "SELL",
                "qty": "1",
                "price": "102",
                "fee": "0",
                "fee_asset": "USDT",
            },
            config,
        )
        self.assertEqual(state.realized, F(2))  # (102-100)*1, profit on price rise

    def test_safety_triggers_on_price_fall(self):
        config = Config.parse(raw_config())
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state, _ = _base_fill(state, config)
        # deviation=0.1 -> first safety at 90
        state = apply(state, {"type": "MARK", "price": "91"}, config)
        self.assertIsNone(decision(state, config))
        state = apply(state, {"type": "MARK", "price": "90"}, config)
        self.assertEqual(decision(state, config), ("SAFETY:1", F(1)))


class ShortDirectionTests(unittest.TestCase):
    def test_base_side_is_sell_for_short(self):
        config = Config.parse(raw_config(direction="SHORT"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state, base_side = _base_fill(state, config)
        self.assertEqual(base_side, "SELL")

    def test_safety_triggers_on_price_rise_for_short(self):
        config = Config.parse(raw_config(direction="SHORT"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state, _ = _base_fill(state, config)
        # deviation=0.1 -> first SHORT safety at 110 (above anchor)
        state = apply(state, {"type": "MARK", "price": "109"}, config)
        self.assertIsNone(decision(state, config))
        state = apply(state, {"type": "MARK", "price": "110"}, config)
        self.assertEqual(decision(state, config), ("SAFETY:1", F(1)))

    def test_take_profit_triggers_on_price_fall_for_short(self):
        config = Config.parse(raw_config(direction="SHORT"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state, _ = _base_fill(state, config)
        # take_profit=0.02 -> SHORT target = average*(1-0.02) = 98
        state = apply(state, {"type": "MARK", "price": "99"}, config)
        self.assertIsNone(decision(state, config))
        state = apply(state, {"type": "MARK", "price": "98"}, config)
        self.assertEqual(decision(state, config), ("EXIT", F(1)))

    def test_exit_side_is_buy_and_realized_pnl_is_positive_on_price_fall(self):
        config = Config.parse(raw_config(direction="SHORT"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state, _ = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "98"}, config)
        state = apply(
            state,
            {"type": "INTENT", "order_id": "exit", "role": "EXIT", "qty": "1", "limit_price": "98"},
            config,
        )
        self.assertEqual(state.orders["exit"].side, "BUY")
        state = apply(
            state,
            {
                "type": "FILL",
                "execution_id": "exit-fill",
                "order_id": "exit",
                "side": "BUY",
                "qty": "1",
                "price": "98",
                "fee": "0",
                "fee_asset": "USDT",
            },
            config,
        )
        # Sold to open at 100, bought back to close at 98 -> profit 2 per unit.
        self.assertEqual(state.realized, F(2))
        self.assertEqual(state.position.qty, F(0))

    def test_realized_pnl_is_negative_when_short_covered_at_a_loss(self):
        config = Config.parse(raw_config(direction="SHORT"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state, _ = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "105"}, config)
        state = apply(
            state,
            {"type": "INTENT", "order_id": "stop", "role": "STOP", "qty": "1", "limit_price": "105"},
            config,
        )
        self.assertEqual(state.orders["stop"].side, "BUY")
        state = apply(
            state,
            {
                "type": "FILL",
                "execution_id": "stop-fill",
                "order_id": "stop",
                "side": "BUY",
                "qty": "1",
                "price": "105",
                "fee": "0",
                "fee_asset": "USDT",
            },
            config,
        )
        self.assertEqual(state.realized, F(-5))


if __name__ == "__main__":
    unittest.main()
