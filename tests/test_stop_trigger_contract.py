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

    def test_canceled_stop_keeps_trigger_and_partial_fill_separate(self):
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
                "execution_id": "stop-partial",
                "order_id": "stop",
                "side": "SELL",
                "qty": "0.4",
                "price": "100",
                "fee": "0.04",
                "fee_asset": "USDT",
            },
            config,
        )
        state = apply(
            state,
            {
                "type": "ORDER_FINAL",
                "order_id": "stop",
                "status": "CANCELED",
                "filled_qty": "0.4",
                "coverage_complete": True,
            },
            config,
        )

        self.assertEqual(
            (
                state.position.qty,
                state.realized,
                state.orders["stop"].status,
                state.orders["stop"].leaves,
                state.orders["stop"].canceled,
                decision(state, config),
            ),
            (F(3, 5), F(0), "CANCELED", F(0), F(3, 5), ("STOP", F(3, 5))),
        )


if __name__ == "__main__":
    unittest.main()
