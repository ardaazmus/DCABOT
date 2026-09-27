"""Faz 17 H.2-motor (RG-11): bar-count-confirmed stop-loss. A single bad
bar-close never triggers a STOP by itself; only `stop_loss_confirmation_bars`
CONSECUTIVE closed bars beyond the trigger do -- and any bar that recovers
resets the streak to zero."""
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


def _bar(state, config, close):
    return apply(state, {"type": "BAR_CLOSE", "close": close}, config)


class ConfirmationStreakTests(unittest.TestCase):
    def test_single_breach_does_not_trigger_stop(self):
        # trigger = 100*(1-0.05) = 95
        config = Config.parse(raw_config(stop_loss_rate="0.05", stop_loss_confirmation_bars=2))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = apply(state, {"type": "MARK", "price": "94"}, config)
        state = _bar(state, config, "94")
        self.assertEqual(state.sl_breach_streak, 1)
        self.assertIsNone(decision(state, config))

    def test_confirmed_streak_triggers_stop(self):
        config = Config.parse(raw_config(stop_loss_rate="0.05", stop_loss_confirmation_bars=2))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = _bar(state, config, "94")
        state = _bar(state, config, "93")
        self.assertEqual(state.sl_breach_streak, 2)
        state = apply(state, {"type": "MARK", "price": "93"}, config)
        self.assertEqual(decision(state, config), ("STOP", F(1)))

    def test_recovery_bar_resets_the_streak(self):
        config = Config.parse(raw_config(stop_loss_rate="0.05", stop_loss_confirmation_bars=2))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = _bar(state, config, "94")
        self.assertEqual(state.sl_breach_streak, 1)
        state = _bar(state, config, "96")  # recovers above trigger (95)
        self.assertEqual(state.sl_breach_streak, 0)
        state = _bar(state, config, "94")
        self.assertEqual(state.sl_breach_streak, 1)
        state = apply(state, {"type": "MARK", "price": "94"}, config)
        self.assertIsNone(decision(state, config))

    def test_exact_trigger_price_counts_as_breach_inclusive(self):
        config = Config.parse(raw_config(stop_loss_rate="0.05", stop_loss_confirmation_bars=1))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = _bar(state, config, "95")  # exactly the trigger
        self.assertEqual(state.sl_breach_streak, 1)

    def test_full_confirmed_stop_can_be_executed(self):
        config = Config.parse(raw_config(stop_loss_rate="0.05", stop_loss_confirmation_bars=1))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = _bar(state, config, "94")
        state = apply(state, {"type": "MARK", "price": "94"}, config)
        role, qty = decision(state, config)
        self.assertEqual((role, qty), ("STOP", F(1)))
        state = apply(
            state,
            {"type": "INTENT", "order_id": "stop", "role": "STOP", "qty": "1", "limit_price": "94"},
            config,
        )
        self.assertEqual(state.orders["stop"].side, "SELL")


class FeatureOffRegressionTests(unittest.TestCase):
    def test_bar_close_events_are_harmless_when_stop_loss_not_configured(self):
        config = Config.parse(raw_config())
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_fill(state, config)
        state = _bar(state, config, "50")  # would be a massive breach if configured
        self.assertEqual(state.sl_breach_streak, 0)
        state = apply(state, {"type": "MARK", "price": "50"}, config)
        # Halted by drawdown is a separate mechanism; this only asserts SL confirmation itself did nothing.
        self.assertIsNone(config.stop_loss_rate)


if __name__ == "__main__":
    unittest.main()
