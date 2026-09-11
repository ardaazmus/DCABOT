import json
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path
import unittest

from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply, decision
from dcabot.domain.math import Position


ROOT = Path(__file__).resolve().parents[1]


def stop_state():
    config = Config.parse(
        json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
    )
    state = State(position=Position(F(1), F(100)), mark=F(100))
    return config, replace(state, halted=True)


class StopTriggerContractTests(unittest.TestCase):
    def test_stop_trigger_is_observation_only(self):
        config, state = stop_state()
        before = (state.position, state.realized, state.fees, state.orders.copy())

        self.assertEqual(decision(state, config), ("STOP", F(1)))
        self.assertEqual(
            (state.position, state.realized, state.fees, state.orders),
            before,
        )

    def test_stop_intent_does_not_manufacture_a_fill(self):
        config, state = stop_state()

        state = apply(
            state,
            {
                "type": "INTENT",
                "order_id": "stop",
                "role": "STOP",
                "qty": "1",
                "limit_price": "100",
            },
            config,
        )

        self.assertEqual(state.position.qty, F(1))
        self.assertEqual(state.realized, F(0))
        self.assertEqual(state.orders["stop"].filled, F(0))

    def test_stop_fill_is_the_economic_transition(self):
        config, state = stop_state()
        state = apply(
            state,
            {
                "type": "INTENT",
                "order_id": "stop",
                "role": "STOP",
                "qty": "1",
                "limit_price": "100",
            },
            config,
        )
        state = apply(
            state,
            {
                "type": "FILL",
                "execution_id": "stop-fill",
                "order_id": "stop",
                "side": "SELL",
                "qty": "1",
                "price": "100",
                "fee": "0.1",
                "fee_asset": "USDT",
            },
            config,
        )

        self.assertEqual(state.position.qty, F(0))
        self.assertEqual(state.realized, F(0))
        self.assertEqual(state.fees, F(1, 10))


if __name__ == "__main__":
    unittest.main()
