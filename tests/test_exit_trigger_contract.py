import json
from fractions import Fraction as F
from pathlib import Path
import unittest

from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply, decision


ROOT = Path(__file__).resolve().parents[1]


def raw_config(**updates):
    raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
    raw.update(updates)
    return raw


def seeded_position():
    config = Config.parse(raw_config())
    state = apply(State(), {"type": "MARK", "price": "100"}, config)
    state = apply(
        state,
        {
            "type": "INTENT",
            "order_id": "base",
            "role": "BASE",
            "qty": "1",
            "limit_price": "100",
        },
        config,
    )
    state = apply(
        state,
        {
            "type": "FILL",
            "execution_id": "base-fill",
            "order_id": "base",
            "side": "BUY",
            "qty": "1",
            "price": "100",
            "fee": "0.1",
            "fee_asset": "USDT",
        },
        config,
    )
    state = apply(
        state,
        {
            "type": "ORDER_FINAL",
            "order_id": "base",
            "status": "FILLED",
            "filled_qty": "1",
            "coverage_complete": True,
        },
        config,
    )
    return config, state


class ExitTriggerContractTests(unittest.TestCase):
    def test_take_profit_trigger_is_observation_only(self):
        config, state = seeded_position()
        before = (state.position, state.realized, state.fees, state.orders.copy())

        state = apply(state, {"type": "MARK", "price": "102"}, config)

        self.assertEqual(decision(state, config), ("EXIT", F(1)))
        self.assertEqual(
            (state.position, state.realized, state.fees, state.orders),
            before,
        )

    def test_exit_intent_does_not_manufacture_a_fill(self):
        config, state = seeded_position()
        state = apply(state, {"type": "MARK", "price": "102"}, config)

        state = apply(
            state,
            {
                "type": "INTENT",
                "order_id": "exit",
                "role": "EXIT",
                "qty": "1",
                "limit_price": "102",
            },
            config,
        )

        self.assertEqual(state.position.qty, F(1))
        self.assertEqual(state.realized, F(0))
        self.assertEqual(state.orders["exit"].filled, F(0))

    def test_exit_fill_is_the_economic_transition(self):
        config, state = seeded_position()
        state = apply(state, {"type": "MARK", "price": "102"}, config)
        state = apply(
            state,
            {
                "type": "INTENT",
                "order_id": "exit",
                "role": "EXIT",
                "qty": "1",
                "limit_price": "102",
            },
            config,
        )

        state = apply(
            state,
            {
                "type": "FILL",
                "execution_id": "exit-fill",
                "order_id": "exit",
                "side": "SELL",
                "qty": "1",
                "price": "102",
                "fee": "0.102",
                "fee_asset": "USDT",
            },
            config,
        )

        self.assertEqual(state.position.qty, F(0))
        self.assertEqual(state.realized, F(2))
        self.assertEqual(state.fees, F(202, 1000))


if __name__ == "__main__":
    unittest.main()
