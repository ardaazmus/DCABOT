"""G4-a COMBO-lite: combined take-profit — sector field, null engine TP,
exact combined trigger, close_at_market reason.

Elde hesap (trigger): A qty 1 @100, mark 102 -> +2; B qty 2 @50
(cost 100), mark 51 -> +2. Toplam +4/200 = %2 -> hedef 2 tetikler,
2.0001 tetiklemez. SHORT Ayna: qty 1 @100, mark 98 -> +2.
"""
import json
import unittest
from fractions import Fraction as Q
from pathlib import Path

from dcabot.application.deal_actions import DealActionError, close_at_market
from dcabot.application.paper_bot_runner import ComboPosition, combo_close_triggered
from dcabot.application.sector_dca import (
    SectorDcaError,
    SymbolRules,
    derive_deal_config,
    parse_sector_dca,
)
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply, decision, target
from dcabot.domain.numbers import number
from dcabot.persistence.bot_store import BotDeal

ROOT = Path(__file__).resolve().parents[1]
RULES = SymbolRules("BTCUSDT", "TRADING", "BTC", "USDT", "0.01", "0.001", "0.001", "5")
TEMPLATE = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))


def _raw(**overrides):
    body = dict(
        symbol="BTCUSDT", base_order="100", safety_order="100", max_safety_orders=2,
        max_active_safety_orders=None, price_deviation="10", safety_order_volume_scale="1",
        safety_order_step_scale="1", take_profit="5", stop_loss=None, direction="LONG",
        cooldown_seconds=0, min_price=None, max_price=None,
    )
    body.update(overrides)
    return body


def _raw_config(**updates):
    raw = dict(TEMPLATE)
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


class ComboSectorParseTests(unittest.TestCase):
    def test_default_is_none(self):
        self.assertIsNone(parse_sector_dca(_raw()).combined_take_profit)

    def test_value_accepted(self):
        params = parse_sector_dca(_raw(combined_take_profit="1.5"))
        self.assertEqual(params.combined_take_profit, Q("1.5"))

    def test_out_of_range_rejected(self):
        for bad in ("0", "100", "-1", "101", "x", ""):
            with self.assertRaises(SectorDcaError, msg=bad):
                parse_sector_dca(_raw(combined_take_profit=bad))

    def test_per_deal_take_profit_still_required(self):
        body = _raw(combined_take_profit="2")
        del body["take_profit"]
        with self.assertRaises(SectorDcaError):
            parse_sector_dca(body)


class ComboDeriveTests(unittest.TestCase):
    def _derive(self, **overrides):
        params = parse_sector_dca(_raw(**overrides))
        return derive_deal_config(
            params, rules=RULES, reference_price=Q(100), budget=Q(1000), template=TEMPLATE
        )

    def test_combo_suppresses_engine_take_profit(self):
        raw = self._derive(combined_take_profit="2")
        self.assertIsNone(raw["take_profit"])
        config = Config.parse(raw)
        self.assertIsNone(config.take_profit)

    def test_plain_bot_keeps_take_profit(self):
        raw = self._derive()
        self.assertEqual(raw["take_profit"], "0.05")
        config = Config.parse(raw)
        self.assertEqual(config.take_profit, Q("0.05"))


class EngineNullTakeProfitTests(unittest.TestCase):
    def _positioned(self, **updates):
        config = Config.parse(_raw_config(**updates))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        return config, _base_fill(state, config)

    def test_target_is_none_without_position_or_take_profit(self):
        config = Config.parse(_raw_config(take_profit=None))
        self.assertIsNone(target(State(), config))
        _, state = self._positioned(take_profit=None)
        self.assertIsNone(target(state, config))

    def test_no_exit_proposal_at_would_be_target(self):
        config, state = self._positioned(take_profit=None)
        state = apply(state, {"type": "MARK", "price": "110"}, config)
        self.assertIsNone(decision(state, config))

    def test_control_exit_proposal_with_take_profit(self):
        config, state = self._positioned(take_profit="0.05")
        state = apply(state, {"type": "MARK", "price": "110"}, config)
        action = decision(state, config)
        self.assertIsNotNone(action)
        assert action is not None
        self.assertEqual(action[0], "EXIT")

    def test_stop_loss_still_fires_without_take_profit(self):
        config, state = self._positioned(
            take_profit=None, stop_loss_rate="0.05", stop_loss_confirmation_bars=1
        )
        state = apply(state, {"type": "BAR_CLOSE", "close": "94"}, config)
        state = apply(state, {"type": "MARK", "price": "94"}, config)
        action = decision(state, config)
        self.assertIsNotNone(action)
        assert action is not None
        self.assertEqual(action[0], "STOP")

    def test_null_config_rejects_garbage_and_keeps_bounds(self):
        with self.assertRaises(ValueError):
            Config.parse(_raw_config(take_profit="x"))
        with self.assertRaises(ValueError):
            Config.parse(_raw_config(take_profit="0"))
        with self.assertRaises(ValueError):
            Config.parse(_raw_config(take_profit="1"))
        raw = _raw_config()
        del raw["take_profit"]
        with self.assertRaises(ValueError):
            Config.parse(raw)


class ComboTriggerTests(unittest.TestCase):
    def test_combined_two_percent_triggers_at_two(self):
        positions = (
            ComboPosition(Q(1), Q(100), Q(102), "LONG"),
            ComboPosition(Q(2), Q(100), Q(51), "LONG"),
        )
        self.assertTrue(combo_close_triggered(positions, Q(2)))
        self.assertFalse(combo_close_triggered(positions, Q("2.0001")))

    def test_loss_elsewhere_blocks(self):
        positions = (
            ComboPosition(Q(1), Q(100), Q(110), "LONG"),
            ComboPosition(Q(1), Q(100), Q(95), "LONG"),
        )
        self.assertFalse(combo_close_triggered(positions, Q(3)))

    def test_short_mirror_counts(self):
        positions = (ComboPosition(Q(1), Q(100), Q(98), "SHORT"),)
        self.assertTrue(combo_close_triggered(positions, Q(2)))
        self.assertFalse(combo_close_triggered(positions, Q("2.0001")))

    def test_empty_flat_or_unmarked_never_triggers(self):
        self.assertFalse(combo_close_triggered((), Q(1)))
        self.assertFalse(
            combo_close_triggered((ComboPosition(Q(0), Q(0), Q(100), "LONG"),), Q(1))
        )
        self.assertFalse(
            combo_close_triggered((ComboPosition(Q(1), Q(100), None, "LONG"),), Q(1))
        )
        self.assertFalse(
            combo_close_triggered(
                (
                    ComboPosition(Q(1), Q(100), Q(200), "LONG"),
                    ComboPosition(Q(1), Q(100), None, "LONG"),
                ),
                Q(1),
            )
        )


class ComboCloseReasonTests(unittest.TestCase):
    def _positioned(self):
        config = Config.parse(_raw_config(take_profit=None))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        return config, _base_fill(state, config)

    def test_take_profit_reason_stamped(self):
        config, state = self._positioned()
        deal = BotDeal("b", 1, 100, None, 0, None, None, 0, "BTCUSDT")
        result = close_at_market(
            config, state, deal, Q(0), price=Q(102), now_us=200, reason="TAKE_PROFIT"
        )
        self.assertEqual(result.deal.close_reason, "TAKE_PROFIT")
        self.assertEqual(result.event.detail["reason"], "TAKE_PROFIT")
        self.assertEqual(result.deal.closed_at_us, 200)
        self.assertTrue(number(result.deal.profit) > 0)

    def test_default_reason_unchanged(self):
        config, state = self._positioned()
        deal = BotDeal("b", 1, 100, None, 0, None, None, 0, "BTCUSDT")
        result = close_at_market(config, state, deal, Q(0), price=Q(102), now_us=200)
        self.assertEqual(result.deal.close_reason, "MANUAL_CLOSE")

    def test_unknown_reason_rejected(self):
        config, state = self._positioned()
        deal = BotDeal("b", 1, 100, None, 0, None, None, 0, "BTCUSDT")
        with self.assertRaises(DealActionError):
            close_at_market(config, state, deal, Q(0), price=Q(102), now_us=200, reason="X")


if __name__ == "__main__":
    unittest.main()
