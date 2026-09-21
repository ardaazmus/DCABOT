import unittest

from dcabot.application.rebalance_projection import build_rebalance_projection
from dcabot.application.rebalance_triggers import evaluate_threshold_trigger
from dcabot.application.rebalance_valuation import (
    RebalancePlan,
    RebalanceValuationError,
    build_rebalance_plan,
    value_holdings,
)


class ValueHoldingsTests(unittest.TestCase):
    def test_quantities_value_with_explicit_prices_only(self):
        result = value_holdings(
            valuation_asset="USDT",
            holdings=(("BTC", "0.01"), ("ETH", "0.25"), ("USDT", "100")),
            prices=(("BTC", "50000"), ("ETH", "1600")),
        )
        self.assertEqual(result.valuation_asset, "USDT")
        self.assertEqual(result.total_equity, "1000")
        self.assertEqual(
            [(p.asset, p.qty, p.price, p.value) for p in result.positions],
            [
                ("BTC", "0.01", "50000", "500"),
                ("ETH", "0.25", "1600", "400"),
                ("USDT", "100", "1", "100"),
            ],
        )

    def test_missing_price_is_fail_closed(self):
        with self.assertRaises(RebalanceValuationError) as ctx:
            value_holdings(
                valuation_asset="USDT",
                holdings=(("BTC", "0.01"),),
                prices=(),
            )
        self.assertEqual(ctx.exception.code, "REBALANCE_VALUATION_PRICE_MISSING")

    def test_self_price_for_valuation_asset_is_rejected(self):
        with self.assertRaises(RebalanceValuationError) as ctx:
            value_holdings(
                valuation_asset="USDT",
                holdings=(("USDT", "100"),),
                prices=(("USDT", "1"),),
            )
        self.assertEqual(ctx.exception.code, "REBALANCE_VALUATION_SELF_PRICE_FORBIDDEN")

    def test_extra_price_for_unheld_asset_is_rejected(self):
        with self.assertRaises(RebalanceValuationError) as ctx:
            value_holdings(
                valuation_asset="USDT",
                holdings=(("BTC", "0.01"),),
                prices=(("BTC", "50000"), ("ETH", "1600")),
            )
        self.assertEqual(ctx.exception.code, "REBALANCE_VALUATION_PRICE_UNEXPECTED")

    def test_negative_quantity_is_rejected(self):
        with self.assertRaises(RebalanceValuationError) as ctx:
            value_holdings(
                valuation_asset="USDT",
                holdings=(("BTC", "-0.01"),),
                prices=(("BTC", "50000"),),
            )
        self.assertEqual(ctx.exception.code, "REBALANCE_VALUATION_QTY_INVALID")

    def test_zero_price_is_rejected(self):
        with self.assertRaises(RebalanceValuationError) as ctx:
            value_holdings(
                valuation_asset="USDT",
                holdings=(("BTC", "0.01"),),
                prices=(("BTC", "0"),),
            )
        self.assertEqual(ctx.exception.code, "REBALANCE_VALUATION_PRICE_INVALID")


class BuildRebalancePlanTests(unittest.TestCase):
    def _projection(self):
        return build_rebalance_projection(
            valuation_asset="USDT",
            total_equity="1000",
            allocations=(("BTC", "0.6", "500"), ("ETH", "0.4", "500")),
        )

    def _trigger(self):
        return evaluate_threshold_trigger(
            current_weight="0.5", target_weight="0.6", threshold="0.05"
        )

    def test_triggered_plan_carries_exact_gross_and_stable_id(self):
        first = build_rebalance_plan(
            trigger=self._trigger(), projection=self._projection(), plan_time_us=1700000000000000
        )
        second = build_rebalance_plan(
            trigger=self._trigger(), projection=self._projection(), plan_time_us=1700000000000000
        )
        self.assertIsInstance(first, RebalancePlan)
        self.assertEqual(first.status, "DRAFT")
        self.assertEqual(first.gross_buy, "100")
        self.assertEqual(first.gross_sell, "100")
        self.assertEqual(first.plan_id, second.plan_id)
        self.assertRegex(first.plan_id, r"\A[0-9a-f]{64}\Z")

    def test_plan_id_changes_with_inputs(self):
        base = build_rebalance_plan(
            trigger=self._trigger(), projection=self._projection(), plan_time_us=1700000000000000
        )
        other_time = build_rebalance_plan(
            trigger=self._trigger(), projection=self._projection(), plan_time_us=1700000000000001
        )
        self.assertNotEqual(base.plan_id, other_time.plan_id)

    def test_untriggered_gate_cannot_produce_a_plan(self):
        idle = evaluate_threshold_trigger(
            current_weight="0.59", target_weight="0.6", threshold="0.05"
        )
        self.assertEqual(idle.status, "NOT_TRIGGERED")
        with self.assertRaises(RebalanceValuationError) as ctx:
            build_rebalance_plan(
                trigger=idle, projection=self._projection(), plan_time_us=1700000000000000
            )
        self.assertEqual(ctx.exception.code, "REBALANCE_PLAN_TRIGGER_NOT_TRIGGERED")

    def test_plan_rejects_non_integer_time(self):
        with self.assertRaises(RebalanceValuationError) as ctx:
            build_rebalance_plan(
                trigger=self._trigger(), projection=self._projection(), plan_time_us=True
            )
        self.assertEqual(ctx.exception.code, "REBALANCE_PLAN_TIME_INVALID")


if __name__ == "__main__":
    unittest.main()
