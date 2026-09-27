"""Faz 17 I.1-motor (RG-12): base-asset profit retention. Only the
cost-recovery portion is actually sold at take-profit; the remainder is
withdrawn (not sold) via WITHDRAW_PROFIT. STOP (loss-cutting) always fully
liquidates to quote regardless of profit_asset -- there is no "profit" to
choose a currency for on a loss. Default (quote profit) stays byte-for-byte
unchanged.
"""
import json
from fractions import Fraction as F
from pathlib import Path
import unittest

from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply, decision
from dcabot.domain.numbers import text

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
    side = state.orders["base"].side
    state = apply(
        state,
        {"type": "FILL", "execution_id": "base-fill", "order_id": "base", "side": side,
         "qty": "1", "price": price, "fee": "0", "fee_asset": "USDT"},
        config,
    )
    state = apply(
        state,
        {"type": "ORDER_FINAL", "order_id": "base", "status": "FILLED", "filled_qty": "1", "coverage_complete": True},
        config,
    )
    return state


class DefaultQuoteProfitRegressionTests(unittest.TestCase):
    def test_exit_still_proposes_full_quantity_by_default(self):
        config = Config.parse(raw_config())
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "102"}, config)
        self.assertEqual(decision(state, config), ("EXIT", F(1)))


class BaseProfitFullCycleTests(unittest.TestCase):
    def test_cost_recovery_then_withdraw(self):
        config = Config.parse(raw_config(profit_asset="BTC"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "102"}, config)

        role, qty = decision(state, config)
        self.assertEqual(role, "EXIT")
        # cost=100, price=102 -> raw 100/102, rounded UP to qty_step=0.001.
        expected = F(100, 102)
        from dcabot.domain.numbers import align

        expected_aligned = align(expected, F("0.001"), up=True)
        self.assertEqual(qty, expected_aligned)
        self.assertLess(qty, F(1))  # strictly less than the full position

        state = apply(
            state,
            {"type": "INTENT", "order_id": "tp", "role": "EXIT", "qty": text(qty), "limit_price": "102"},
            config,
        )
        side = state.orders["tp"].side
        self.assertEqual(side, "SELL")
        state = apply(
            state,
            {"type": "FILL", "execution_id": "tp-fill", "order_id": "tp", "side": side,
             "qty": text(qty), "price": "102", "fee": "0", "fee_asset": "USDT"},
            config,
        )
        state = apply(
            state,
            {"type": "ORDER_FINAL", "order_id": "tp", "status": "FILLED", "filled_qty": text(qty), "coverage_complete": True},
            config,
        )
        self.assertTrue(state.profit_cost_recovered)
        remaining = state.position.qty
        self.assertGreater(remaining, F(0))
        # Cost was fully recovered (rounding UP means proceeds >= cost).
        self.assertGreaterEqual(qty * F(102), F(100))

        self.assertEqual(decision(state, config), ("WITHDRAW_PROFIT", remaining))
        state = apply(state, {"type": "WITHDRAW_PROFIT", "qty": text(remaining)}, config)
        self.assertEqual(state.position.qty, F(0))
        self.assertEqual(state.retained_profit_base, remaining)
        self.assertIsNone(decision(state, config))  # deal complete, nothing left to propose


class RejectionTests(unittest.TestCase):
    def test_exit_with_wrong_quantity_is_rejected_in_base_profit_mode(self):
        config = Config.parse(raw_config(profit_asset="BTC"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "102"}, config)
        with self.assertRaises(ValueError):
            apply(
                state,
                {"type": "INTENT", "order_id": "tp", "role": "EXIT", "qty": "1", "limit_price": "102"},
                config,
            )

    def test_withdraw_profit_rejected_before_cost_recovery(self):
        config = Config.parse(raw_config(profit_asset="BTC"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        with self.assertRaises(ValueError):
            apply(state, {"type": "WITHDRAW_PROFIT", "qty": "1"}, config)

    def test_withdraw_profit_rejected_when_not_base_profit_mode(self):
        config = Config.parse(raw_config())
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        with self.assertRaises(ValueError):
            apply(state, {"type": "WITHDRAW_PROFIT", "qty": "1"}, config)

    def test_withdraw_profit_must_be_the_full_remainder(self):
        config = Config.parse(raw_config(profit_asset="BTC"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "102"}, config)
        role, qty = decision(state, config)
        state = apply(
            state,
            {"type": "INTENT", "order_id": "tp", "role": "EXIT", "qty": text(qty), "limit_price": "102"},
            config,
        )
        state = apply(
            state,
            {"type": "FILL", "execution_id": "tp-fill", "order_id": "tp", "side": "SELL",
             "qty": text(qty), "price": "102", "fee": "0", "fee_asset": "USDT"},
            config,
        )
        state = apply(
            state,
            {"type": "ORDER_FINAL", "order_id": "tp", "status": "FILLED", "filled_qty": text(qty), "coverage_complete": True},
            config,
        )
        remaining = state.position.qty
        partial = text(remaining / 2)
        with self.assertRaises(ValueError):
            apply(state, {"type": "WITHDRAW_PROFIT", "qty": partial}, config)


class StopIsUnaffectedByProfitAssetTests(unittest.TestCase):
    def test_stop_always_fully_liquidates_regardless_of_profit_asset(self):
        # A small initial_equity relative to position size makes a halt
        # (minimum_equity breach) reachable from a plain price drop.
        config = Config.parse(raw_config(profit_asset="BTC", initial_equity="150", minimum_equity="100"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "10"}, config)
        self.assertTrue(state.halted)
        self.assertEqual(decision(state, config), ("STOP", F(1)))


if __name__ == "__main__":
    unittest.main()
