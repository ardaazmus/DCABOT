"""Real bug found + fixed 2026-09-23 (docs/KARARLAR.md), while investigating
futures/leveraged paper support: `place_next_action`/`paper_fill_next_action`
hardcoded `side = "SELL" if role in ("EXIT","STOP") else "BUY"` -- wrong for
BOTH a SHORT-direction config (the whole ladder inverted: opening a SHORT
sells, closing buys back) AND a LONG config with a take-profit LADDER
configured (`role="EXIT:1"` is not in `("EXIT","STOP")`, so it silently fell
through to the OPENING side -- a real order-direction bug, not just a paper
one). `order_side()` now mirrors engine.py's own INTENT-time side derivation
(engine.py:228-232) exactly, so a FILL's side can never mismatch the order's
own `o.side`."""
import json
from pathlib import Path
import unittest

from dcabot.application.testnet_dca_session import (
    new_session,
    order_side,
    paper_fill_next_action,
    propose_next_action,
)
from dcabot.domain.config import Config
from dcabot.application.testnet_dca_session import apply_mark

ROOT = Path(__file__).resolve().parents[1]


def raw_config(**updates) -> dict:
    raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
    raw.update(updates)
    return raw


class OrderSideTests(unittest.TestCase):
    def test_long_base_and_safety_open_with_buy(self):
        self.assertEqual(order_side("BASE", "LONG"), "BUY")
        self.assertEqual(order_side("SAFETY:1", "LONG"), "BUY")

    def test_long_exit_and_stop_close_with_sell(self):
        self.assertEqual(order_side("EXIT", "LONG"), "SELL")
        self.assertEqual(order_side("STOP", "LONG"), "SELL")

    def test_long_ladder_exit_also_closes_with_sell(self):
        """The exact bug: EXIT:N was never in ("EXIT","STOP")."""
        self.assertEqual(order_side("EXIT:1", "LONG"), "SELL")
        self.assertEqual(order_side("EXIT:12", "LONG"), "SELL")

    def test_short_base_and_safety_open_with_sell(self):
        self.assertEqual(order_side("BASE", "SHORT"), "SELL")
        self.assertEqual(order_side("SAFETY:1", "SHORT"), "SELL")

    def test_short_exit_and_ladder_close_with_buy(self):
        self.assertEqual(order_side("EXIT", "SHORT"), "BUY")
        self.assertEqual(order_side("STOP", "SHORT"), "BUY")
        self.assertEqual(order_side("EXIT:1", "SHORT"), "BUY")

    def test_short_direction_paper_fill_no_longer_crashes(self):
        config = Config.parse(raw_config(direction="SHORT", leverage="10"))
        session = new_session(config, "BTCUSDT")
        session = apply_mark(session, "100")
        role, qty = propose_next_action(session)
        self.assertEqual(role, "BASE")

        filled = paper_fill_next_action(session, role=role, qty=qty, attempt_id="t1")

        self.assertEqual(filled.state.position.qty, qty)


if __name__ == "__main__":
    unittest.main()
