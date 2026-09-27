"""Faz W: quote-denominated safety-order sizing (3Commas/Bitsgap/Pionex convention)."""
import json
import random
import unittest
from fractions import Fraction as Q
from pathlib import Path

from dcabot.domain.config import Config
from dcabot.domain.math import Direction, build_plan
from dcabot.domain.numbers import align
from dcabot.persistence.spot_binding_store import _config_payload

ROOT = Path(__file__).resolve().parents[1]


def _paper(**overrides) -> dict:
    raw = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
    raw.update(overrides)
    return raw


class BuildPlanQuoteSizingTests(unittest.TestCase):
    def test_quote_levels_divide_the_scaled_amount_by_their_own_price(self):
        plan = build_plan(
            Q(100), Q(50), 3, Q(1, 10), Q(1), Q(2), Q(1, 100), Q(1, 1000), sizing="QUOTE"
        )
        # amounts 50, 100, 200 at prices 90, 80, 70, floored to 0.001
        self.assertEqual([level.price for level in plan], [Q(90), Q(80), Q(70)])
        self.assertEqual([level.qty for level in plan], [Q(555, 1000), Q(1250, 1000), Q(2857, 1000)])

    def test_base_sizing_is_the_unchanged_default(self):
        args = (Q(100), Q(1), 4, Q(1, 20), Q(3, 2), Q(3, 2), Q(1, 100), Q(1, 1000))
        self.assertEqual(build_plan(*args), build_plan(*args, sizing="BASE"))

    def test_unknown_sizing_is_rejected(self):
        with self.assertRaises(ValueError):
            build_plan(Q(100), Q(1), 1, Q(1, 10), Q(1), Q(1), Q(1, 100), Q(1, 1000), sizing="USD")

    def test_amount_too_small_for_the_grid_fails_closed(self):
        with self.assertRaises(ValueError):
            build_plan(Q(100000), Q(1, 100), 1, Q(1, 10), Q(1), Q(1), Q(1, 100), Q(1, 1000), sizing="QUOTE")

    def test_property_quote_levels_floor_the_amount_and_keep_base_prices(self):
        rng = random.Random(20260924)
        checked = 0
        for _ in range(400):
            anchor = Q(rng.randint(1_000, 10_000_000), 100)
            amount = Q(rng.randint(10, 100_000))
            count = rng.randint(1, 8)
            deviation = Q(rng.randint(1, 40), 1000)
            step = Q(rng.randint(100, 150), 100)
            volume = Q(rng.randint(100, 200), 100)
            tick = Q(1, 100)
            qty_step = Q(1, 10 ** rng.randint(3, 6))
            direction = rng.choice([Direction.LONG, Direction.SHORT])
            try:
                quote_plan = build_plan(anchor, amount, count, deviation, step, volume, tick, qty_step, direction=direction, sizing="QUOTE")
                base_plan = build_plan(anchor, Q(1), count, deviation, step, volume, tick, qty_step, direction=direction)
            except ValueError:
                continue
            checked += 1
            self.assertEqual([lv.price for lv in quote_plan], [lv.price for lv in base_plan])
            scaled = amount
            for level in quote_plan:
                self.assertEqual(align(level.qty, qty_step, up=False), level.qty)
                self.assertLessEqual(level.qty * level.price, scaled)
                self.assertLess(scaled - level.qty * level.price, qty_step * level.price)
                scaled = scaled * volume
        self.assertGreater(checked, 300)


class ConfigSafetySizingTests(unittest.TestCase):
    def test_absent_field_defaults_to_base(self):
        self.assertEqual(Config.parse(_paper()).safety_sizing, "BASE")

    def test_quote_sizing_changes_only_quantities(self):
        base = Config.parse(_paper(safety_qty="1", deviation="0.1"))
        quote = Config.parse(_paper(safety_qty="45", deviation="0.1", safety_sizing="QUOTE"))
        base_plan, quote_plan = base.plan(Q(100)), quote.plan(Q(100))
        self.assertEqual([lv.price for lv in base_plan], [lv.price for lv in quote_plan])
        self.assertEqual([lv.qty for lv in quote_plan], [Q(500, 1000), Q(562, 1000)])

    def test_invalid_value_is_rejected(self):
        with self.assertRaises(ValueError):
            Config.parse(_paper(safety_sizing="quote"))


class PersistedPayloadCompatibilityTests(unittest.TestCase):
    def test_base_sizing_payload_is_byte_identical_to_pre_faz_w(self):
        payload = _config_payload(Config.parse(_paper()))
        self.assertNotIn("safety_sizing", payload)

    def test_quote_sizing_is_persisted(self):
        payload = _config_payload(Config.parse(_paper(safety_sizing="QUOTE", safety_qty="45")))
        self.assertEqual(payload["safety_sizing"], "QUOTE")
        self.assertEqual(Config.parse(payload).safety_sizing, "QUOTE")



class BaseQuoteSizingTests(unittest.TestCase):
    def test_base_order_qty_is_the_quote_amount_at_the_orders_own_price(self):
        config = Config.parse(_paper(base_qty="25", base_sizing="QUOTE", qty_step="0.001", min_qty="0.001"))
        self.assertEqual(config.base_order_qty(Q(100)), Q(250, 1000))
        self.assertEqual(config.base_order_qty(Q(300)), Q(83, 1000))
        self.assertEqual(Config.parse(_paper()).base_order_qty(Q(123)), Config.parse(_paper()).base_qty)

    def test_engine_rejects_a_base_intent_not_sized_at_its_limit_price(self):
        from dcabot.domain.engine import State, apply

        config = Config.parse(_paper(base_qty="25", base_sizing="QUOTE", safety_count=1))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        with self.assertRaises(ValueError):
            apply(state, {"type": "INTENT", "order_id": "o1", "role": "BASE", "qty": "0.3", "limit_price": "100"}, config)
        accepted = apply(state, {"type": "INTENT", "order_id": "o1", "role": "BASE", "qty": "0.25", "limit_price": "100"}, config)
        self.assertEqual(len(accepted.orders), 1)

    def test_simulator_resizes_each_deals_base_order_at_that_deals_price(self):
        from dcabot.application.historical_simulation import simulate_historical_ohlcv
        from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata

        hour = 3_600_000_000
        rows = [("100", "100.5", "99.5", "100"), ("100", "102.5", "100", "102"), ("200", "200.5", "199.9", "200"), ("200", "200.4", "199.8", "200")]
        bars = tuple(CanonicalBar(i * hour, (i + 1) * hour - 1, o, h, low, c, "1", True) for i, (o, h, low, c) in enumerate(rows))
        dataset = HistoricalDatasetInput(
            HistoricalDatasetMetadata("t", "s", "BTCUSDT", "1h", "a", "b", "0" * 64, 0, "MICROSECOND", "UTC"), bars
        )
        config = Config.parse(_paper(base_qty="25", base_sizing="QUOTE", safety_count=1, safety_qty="25", safety_sizing="QUOTE", deviation="0.015", take_profit="0.02"))
        result = simulate_historical_ohlcv(dataset, config, config_hash="0" * 64)
        base_quantities = [action.quantity for action in result.actions if action.role == "BASE"]
        self.assertEqual(base_quantities, ["0.25", "0.125"])

    def test_fixed_slice_model_refuses_quote_base_sizing(self):
        from dcabot.application.historical_simulation import HistoricalSimulationError, simulate_historical_fixed_slice
        from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata

        bars = (CanonicalBar(0, 3_599_999_999, "100", "101", "99", "100", "1", True),)
        dataset = HistoricalDatasetInput(HistoricalDatasetMetadata("t", "s", "BTCUSDT", "1h", "a", "b", "0" * 64, 0, "MICROSECOND", "UTC"), bars)
        with self.assertRaises(HistoricalSimulationError):
            simulate_historical_fixed_slice(dataset, Config.parse(_paper(base_qty="25", base_sizing="QUOTE")), slice_qty="1", config_hash="0" * 64)

    def test_base_sizing_is_persisted_only_when_non_default(self):
        self.assertNotIn("base_sizing", _config_payload(Config.parse(_paper())))
        payload = _config_payload(Config.parse(_paper(base_qty="25", base_sizing="QUOTE")))
        self.assertEqual(payload["base_sizing"], "QUOTE")
        self.assertEqual(Config.parse(payload).base_sizing, "QUOTE")


if __name__ == "__main__":
    unittest.main()
