"""Faz 17 H.2-motor (RG-11): Max Deal Duration -- deal start is the first
economic exposure (position.qty 0 -> nonzero), never order-submission time.
Four actions with distinct, deliberately-chosen semantics: FORCE_CLOSE
(auto-STOP once unsettled clears), STOP_NEW_SAFETY_ORDERS (blocks new
risk only, EXIT/TP still work), WARN_ONLY (flag only, nothing blocked),
FREEZE (blocks everything, the most conservative interpretation)."""
import json
from fractions import Fraction as F
from pathlib import Path
import unittest

from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply, decision

ROOT = Path(__file__).resolve().parents[1]
HOUR_US = 3600 * 1_000_000


def raw_config(**updates):
    raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
    raw.update(updates)
    return raw


def _base_fill_with_clock(state, config, *, price="100", now_us=0):
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
    state = apply(state, {"type": "CLOCK", "now_us": now_us}, config)
    return state


class ClockEventTests(unittest.TestCase):
    def test_deal_start_captured_on_first_clock_after_exposure(self):
        config = Config.parse(raw_config())
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        self.assertIsNone(state.deal_started_at_us)
        state = _base_fill_with_clock(state, config, now_us=1000)
        self.assertEqual(state.deal_started_at_us, 1000)

    def test_clock_before_any_exposure_does_not_set_deal_start(self):
        config = Config.parse(raw_config())
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = apply(state, {"type": "CLOCK", "now_us": 500}, config)
        self.assertIsNone(state.deal_started_at_us)

    def test_clock_cannot_move_backward(self):
        config = Config.parse(raw_config())
        state = apply(State(), {"type": "CLOCK", "now_us": 1000}, config)
        with self.assertRaises(ValueError):
            apply(state, {"type": "CLOCK", "now_us": 999}, config)

    def test_negative_or_non_integer_now_is_rejected(self):
        config = Config.parse(raw_config())
        with self.assertRaises(ValueError):
            apply(State(), {"type": "CLOCK", "now_us": -1}, config)
        with self.assertRaises(ValueError):
            apply(State(), {"type": "CLOCK", "now_us": "1000"}, config)


class ForceCloseTests(unittest.TestCase):
    def test_expires_and_proposes_stop_once_unsettled_clears(self):
        config = Config.parse(raw_config(max_deal_duration_seconds=3600, max_deal_duration_action="FORCE_CLOSE"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill_with_clock(state, config, now_us=0)
        state = apply(state, {"type": "CLOCK", "now_us": HOUR_US - 1}, config)
        self.assertFalse(state.deal_duration_expired)
        state = apply(state, {"type": "CLOCK", "now_us": HOUR_US}, config)
        self.assertTrue(state.deal_duration_expired)
        state = apply(state, {"type": "MARK", "price": "100"}, config)
        self.assertEqual(decision(state, config), ("STOP", F(1)))

    def test_new_safety_order_is_blocked_after_expiry_even_though_force_close_proposes_stop(self):
        config = Config.parse(raw_config(max_deal_duration_seconds=3600, max_deal_duration_action="FORCE_CLOSE"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill_with_clock(state, config, now_us=0)
        state = apply(state, {"type": "CLOCK", "now_us": HOUR_US}, config)
        state = apply(state, {"type": "MARK", "price": "90"}, config)
        # FORCE_CLOSE proposes STOP unconditionally once expired (regardless
        # of price) -- confirms decision() prioritizes closing over a would-be
        # SAFETY trigger. A direct attempt to submit new risk is separately
        # blocked at apply() by the MAX_DEAL_DURATION_EXPIRED blocker.
        self.assertEqual(decision(state, config), ("STOP", F(1)))
        with self.assertRaises(ValueError):
            apply(
                state,
                {"type": "INTENT", "order_id": "so1", "role": "SAFETY:1", "qty": "1", "limit_price": "90"},
                config,
            )


class StopNewSafetyOrdersTests(unittest.TestCase):
    def test_new_safety_blocked_but_normal_exit_still_works(self):
        config = Config.parse(
            raw_config(max_deal_duration_seconds=3600, max_deal_duration_action="STOP_NEW_SAFETY_ORDERS")
        )
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill_with_clock(state, config, now_us=0)
        state = apply(state, {"type": "CLOCK", "now_us": HOUR_US}, config)
        # New SO blocked.
        state = apply(state, {"type": "MARK", "price": "90"}, config)
        self.assertIsNone(decision(state, config))
        # But a normal take-profit EXIT still works.
        state = apply(state, {"type": "MARK", "price": "102"}, config)
        self.assertEqual(decision(state, config), ("EXIT", F(1)))


class WarnOnlyTests(unittest.TestCase):
    def test_nothing_is_blocked_only_the_flag_is_set(self):
        config = Config.parse(raw_config(max_deal_duration_seconds=3600, max_deal_duration_action="WARN_ONLY"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill_with_clock(state, config, now_us=0)
        state = apply(state, {"type": "CLOCK", "now_us": HOUR_US}, config)
        self.assertTrue(state.deal_duration_expired)
        self.assertEqual(state.blockers, [])
        state = apply(state, {"type": "MARK", "price": "90"}, config)
        self.assertEqual(decision(state, config), ("SAFETY:1", F(1)))


class FreezeTests(unittest.TestCase):
    def test_freeze_blocks_take_profit_proposal_too(self):
        config = Config.parse(raw_config(max_deal_duration_seconds=3600, max_deal_duration_action="FREEZE"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill_with_clock(state, config, now_us=0)
        state = apply(state, {"type": "CLOCK", "now_us": HOUR_US}, config)
        state = apply(state, {"type": "MARK", "price": "102"}, config)  # would trigger EXIT otherwise
        self.assertIsNone(decision(state, config))

    def test_freeze_rejects_direct_intent_submission(self):
        config = Config.parse(raw_config(max_deal_duration_seconds=3600, max_deal_duration_action="FREEZE"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill_with_clock(state, config, now_us=0)
        state = apply(state, {"type": "CLOCK", "now_us": HOUR_US}, config)
        state = apply(state, {"type": "MARK", "price": "102"}, config)
        with self.assertRaises(ValueError):
            apply(
                state,
                {"type": "INTENT", "order_id": "exit", "role": "EXIT", "qty": "1", "limit_price": "102"},
                config,
            )


class FeatureOffRegressionTests(unittest.TestCase):
    def test_clock_events_are_harmless_when_duration_not_configured(self):
        config = Config.parse(raw_config())
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill_with_clock(state, config, now_us=0)
        state = apply(state, {"type": "CLOCK", "now_us": HOUR_US * 1000}, config)
        self.assertFalse(state.deal_duration_expired)
        state = apply(state, {"type": "MARK", "price": "102"}, config)
        self.assertEqual(decision(state, config), ("EXIT", F(1)))


if __name__ == "__main__":
    unittest.main()
