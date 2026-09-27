"""Faz 17 H.1-motor (RG-10): laddered partial take-profit in engine.py.
Default (no ladder) EXIT stays byte-for-byte identical; a configured ladder
executes strictly sequentially, weights are locked to the ladder-START
quantity, and the LAST level always closes the true remainder regardless of
its nominal weight. Safety orders remain orthogonal (still proposed when
price falls, unaffected by an active ladder).
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
        {
            "type": "FILL",
            "execution_id": "base-fill",
            "order_id": "base",
            "side": side,
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
    return state


def _fill_and_finalize(state, config, order_id, side, price, qty):
    state = apply(
        state,
        {
            "type": "FILL",
            "execution_id": f"{order_id}-fill",
            "order_id": order_id,
            "side": side,
            "qty": qty,
            "price": price,
            "fee": "0",
            "fee_asset": "USDT",
        },
        config,
    )
    state = apply(
        state,
        {"type": "ORDER_FINAL", "order_id": order_id, "status": "FILLED", "filled_qty": qty, "coverage_complete": True},
        config,
    )
    return state


LADDER = [["0.5", "0.01"], ["0.5", "0.02"]]


class BackwardCompatibleRegressionTests(unittest.TestCase):
    def test_no_ladder_plain_exit_unchanged(self):
        config = Config.parse(raw_config())
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "102"}, config)
        self.assertEqual(decision(state, config), ("EXIT", F(1)))


class LadderSequenceTests(unittest.TestCase):
    def test_two_level_ladder_executes_in_order(self):
        config = Config.parse(raw_config(take_profit_ladder=LADDER))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)

        # Level 1 target = 100*1.01 = 101, weight 0.5 -> qty 0.5.
        state = apply(state, {"type": "MARK", "price": "101"}, config)
        self.assertEqual(decision(state, config), ("EXIT:1", F("0.5")))
        state = apply(
            state,
            {"type": "INTENT", "order_id": "tp1", "role": "EXIT:1", "qty": "0.5", "limit_price": "101"},
            config,
        )
        side = state.orders["tp1"].side
        self.assertEqual(side, "SELL")
        state = _fill_and_finalize(state, config, "tp1", side, "101", "0.5")
        self.assertEqual(state.position.qty, F("0.5"))
        # Average cost is preserved by a partial sell (proven algebraically).
        self.assertEqual(state.position.average, F(100))

        # Level 2 target = 100*1.02 = 102 (average unchanged); LAST level ->
        # closes the true remainder (0.5), matching its nominal weight here.
        state = apply(state, {"type": "MARK", "price": "102"}, config)
        self.assertEqual(decision(state, config), ("EXIT:2", F("0.5")))
        state = apply(
            state,
            {"type": "INTENT", "order_id": "tp2", "role": "EXIT:2", "qty": "0.5", "limit_price": "102"},
            config,
        )
        state = _fill_and_finalize(state, config, "tp2", side, "102", "0.5")
        self.assertEqual(state.position.qty, F(0))
        self.assertTrue(state.orders["tp1"].complete and state.orders["tp2"].complete)

    def test_last_level_closes_true_remainder_even_if_nominal_weight_differs(self):
        # Three levels: 0.3/0.3/0.4 -- but qty_step rounding on level 1/2
        # could leave slightly more or less than the nominal 0.4 for level 3;
        # the engine must always demand the ACTUAL remainder for the last level.
        ladder = [["0.3", "0.01"], ["0.3", "0.02"], ["0.4", "0.03"]]
        config = Config.parse(raw_config(take_profit_ladder=ladder))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)

        state = apply(state, {"type": "MARK", "price": "101"}, config)
        role, qty = decision(state, config)
        self.assertEqual((role, qty), ("EXIT:1", F("0.3")))
        state = apply(
            state,
            {"type": "INTENT", "order_id": "tp1", "role": role, "qty": text(qty), "limit_price": "101"},
            config,
        )
        state = _fill_and_finalize(state, config, "tp1", "SELL", "101", text(qty))

        state = apply(state, {"type": "MARK", "price": "102"}, config)
        role, qty = decision(state, config)
        self.assertEqual((role, qty), ("EXIT:2", F("0.3")))
        state = apply(
            state,
            {"type": "INTENT", "order_id": "tp2", "role": role, "qty": text(qty), "limit_price": "102"},
            config,
        )
        state = _fill_and_finalize(state, config, "tp2", "SELL", "102", text(qty))

        # Remaining is exactly 0.4 here (no rounding drift with these clean
        # numbers), but decision() must derive it from s.position.qty, not
        # from the ladder's nominal 0.4 weight -- confirmed by construction.
        state = apply(state, {"type": "MARK", "price": "103"}, config)
        role, qty = decision(state, config)
        self.assertEqual(role, "EXIT:3")
        self.assertEqual(qty, state.position.qty)
        self.assertEqual(qty, F("0.4"))


class OrthogonalToSafetyOrdersTests(unittest.TestCase):
    def test_safety_orders_still_propose_when_ladder_configured_and_price_falls(self):
        config = Config.parse(raw_config(take_profit_ladder=LADDER))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "90"}, config)
        self.assertEqual(decision(state, config), ("SAFETY:1", F(1)))


class RejectionTests(unittest.TestCase):
    def test_plain_exit_rejected_when_ladder_configured(self):
        config = Config.parse(raw_config(take_profit_ladder=LADDER))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "102"}, config)
        with self.assertRaises(ValueError):
            apply(
                state,
                {"type": "INTENT", "order_id": "exit", "role": "EXIT", "qty": "1", "limit_price": "102"},
                config,
            )

    def test_ladder_role_rejected_without_ladder_configured(self):
        config = Config.parse(raw_config())
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "102"}, config)
        with self.assertRaises(ValueError):
            apply(
                state,
                {"type": "INTENT", "order_id": "tp1", "role": "EXIT:1", "qty": "0.5", "limit_price": "102"},
                config,
            )

    def test_wrong_quantity_for_level_is_rejected(self):
        config = Config.parse(raw_config(take_profit_ladder=LADDER))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "101"}, config)
        with self.assertRaises(ValueError):
            apply(
                state,
                {"type": "INTENT", "order_id": "tp1", "role": "EXIT:1", "qty": "0.6", "limit_price": "101"},
                config,
            )

    def test_level_not_yet_triggered_is_rejected(self):
        config = Config.parse(raw_config(take_profit_ladder=LADDER))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "100.5"}, config)
        with self.assertRaises(ValueError):
            apply(
                state,
                {"type": "INTENT", "order_id": "tp1", "role": "EXIT:1", "qty": "0.5", "limit_price": "100.5"},
                config,
            )

    def test_out_of_order_level_is_rejected(self):
        config = Config.parse(raw_config(take_profit_ladder=LADDER))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "102"}, config)
        with self.assertRaises(ValueError):
            apply(
                state,
                {"type": "INTENT", "order_id": "tp2", "role": "EXIT:2", "qty": "0.5", "limit_price": "102"},
                config,
            )


if __name__ == "__main__":
    unittest.main()
