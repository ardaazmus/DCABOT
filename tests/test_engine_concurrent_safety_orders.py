"""Faz 17 G.3-motor: concurrent (eşzamanlı açık) safety order desteği.

Araştırma (KARARLAR.md, 2026-09-22 "Faz 17 konu 8/12" girdisi) 3Commas/Bitsgap'te
bu davranışın gerçek, sektörde doğrulanmış bir özellik olduğunu teyit etti:
`effective_max_active_safety_orders` kadar SO aynı anda açık (unsettled)
kalabilir. Öncesi (tek seferde tek açık emir) davranışı, cap=1 verildiğinde
veya her emir tamamlanana kadar bir sonraki tetiklenmediğinde regresyon-sıfır
olarak korunmalıdır.
"""
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


def _open_safety(state, config, order_id, role, price, qty="1"):
    return apply(
        state,
        {"type": "INTENT", "order_id": order_id, "role": role, "qty": qty, "limit_price": price},
        config,
    )


def _fill_and_finalize(state, config, order_id, side, price, qty="1"):
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


class ConcurrentSafetyOrderTests(unittest.TestCase):
    """cap == safety_count (2): both SO1 and SO2 may be open at once."""

    def test_second_safety_level_is_proposed_while_first_is_still_open(self):
        config = Config.parse(raw_config(max_active_safety_orders=2))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "90"}, config)
        self.assertEqual(decision(state, config), ("SAFETY:1", F(1)))
        state = _open_safety(state, config, "so1", "SAFETY:1", "90")
        # SO1 is unsettled (open, not filled) -- old code would block here.
        self.assertEqual(len(state.unsettled), 1)
        state = apply(state, {"type": "MARK", "price": "80"}, config)
        self.assertEqual(decision(state, config), ("SAFETY:2", F(1)))
        state = _open_safety(state, config, "so2", "SAFETY:2", "80")
        self.assertEqual(len(state.unsettled), 2)

    def test_cap_reached_blocks_further_proposal_and_acceptance(self):
        config = Config.parse(raw_config(max_active_safety_orders=2))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "80"}, config)
        state = _open_safety(state, config, "so1", "SAFETY:1", "90")
        state = _open_safety(state, config, "so2", "SAFETY:2", "80")
        # Both slots full; safety_count is exhausted too, so no more levels exist,
        # but the cap check itself must also hold when safety_count > cap
        # (covered by the next test). Here just confirm no further proposal.
        self.assertIsNone(decision(state, config))

    def test_cap_smaller_than_safety_count_blocks_second_concurrent_order(self):
        config = Config.parse(raw_config(max_active_safety_orders=1, safety_count=3))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "90"}, config)
        self.assertEqual(decision(state, config), ("SAFETY:1", F(1)))
        state = _open_safety(state, config, "so1", "SAFETY:1", "90")
        state = apply(state, {"type": "MARK", "price": "80"}, config)
        # SAFETY:2 would trigger by price, but cap=1 and SO1 is still open.
        self.assertIsNone(decision(state, config))
        with self.assertRaises(ValueError):
            _open_safety(state, config, "so2", "SAFETY:2", "80")

    def test_slot_frees_only_on_full_fill_not_partial(self):
        config = Config.parse(raw_config(max_active_safety_orders=1, safety_count=3, safety_qty="2"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "90"}, config)
        state = _open_safety(state, config, "so1", "SAFETY:1", "90", qty="2")
        side = state.orders["so1"].side
        # Partial fill: 1 of 2 requested, not finalized as complete.
        state = apply(
            state,
            {
                "type": "FILL",
                "execution_id": "so1-partial",
                "order_id": "so1",
                "side": side,
                "qty": "1",
                "price": "90",
                "fee": "0",
                "fee_asset": "USDT",
            },
            config,
        )
        self.assertFalse(state.orders["so1"].complete)
        state = apply(state, {"type": "MARK", "price": "80"}, config)
        # Slot not freed by a partial fill; cap=1 still blocks SAFETY:2.
        self.assertIsNone(decision(state, config))
        # Now finalize SO1 as fully filled -> slot frees.
        state = apply(
            state,
            {
                "type": "FILL",
                "execution_id": "so1-rest",
                "order_id": "so1",
                "side": side,
                "qty": "1",
                "price": "90",
                "fee": "0",
                "fee_asset": "USDT",
            },
            config,
        )
        state = apply(
            state,
            {"type": "ORDER_FINAL", "order_id": "so1", "status": "FILLED", "filled_qty": "2", "coverage_complete": True},
            config,
        )
        self.assertEqual(decision(state, config), ("SAFETY:2", F(2)))

    def test_next_index_skips_already_open_unsettled_index(self):
        config = Config.parse(raw_config(max_active_safety_orders=2))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "90"}, config)
        state = _open_safety(state, config, "so1", "SAFETY:1", "90")
        state = apply(state, {"type": "MARK", "price": "80"}, config)
        # Must propose SAFETY:2, not re-propose SAFETY:1.
        self.assertEqual(decision(state, config), ("SAFETY:2", F(1)))

    def test_exit_and_stop_still_require_all_orders_settled(self):
        config = Config.parse(raw_config(max_active_safety_orders=2))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "90"}, config)
        state = _open_safety(state, config, "so1", "SAFETY:1", "90")
        # Take-profit trigger price for LONG: average*(1+0.02) = 102.
        state = apply(state, {"type": "MARK", "price": "102"}, config)
        # SO1 is still unsettled -> EXIT must not be proposed yet.
        self.assertIsNone(decision(state, config))
        with self.assertRaises(ValueError):
            apply(
                state,
                {"type": "INTENT", "order_id": "exit", "role": "EXIT", "qty": "1", "limit_price": "102"},
                config,
            )


class BackwardCompatibleSequentialRegressionTests(unittest.TestCase):
    """Default (max_active_safety_orders=None, effective=safety_count) must
    keep behaving exactly like the pre-G.3 code when each order is completed
    before the next is triggered -- regression-zero pin."""

    def test_sequential_completion_matches_prior_single_open_flow(self):
        config = Config.parse(raw_config())
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "90"}, config)
        self.assertEqual(decision(state, config), ("SAFETY:1", F(1)))
        state = _open_safety(state, config, "so1", "SAFETY:1", "90")
        side = state.orders["so1"].side
        state = _fill_and_finalize(state, config, "so1", side, "90")
        state = apply(state, {"type": "MARK", "price": "80"}, config)
        self.assertEqual(decision(state, config), ("SAFETY:2", F(1)))


if __name__ == "__main__":
    unittest.main()
