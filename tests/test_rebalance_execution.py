import unittest

from dcabot.application.rebalance_execution import (
    RebalanceExecutionError,
    bind_execution_orders,
    disclose_execution,
)
from dcabot.application.rebalance_projection import build_rebalance_projection
from dcabot.application.rebalance_triggers import evaluate_threshold_trigger
from dcabot.application.rebalance_valuation import build_rebalance_plan


def _plan():
    projection = build_rebalance_projection(
        valuation_asset="USDT",
        total_equity="1000",
        allocations=(("BTC", "0.6", "500"), ("ETH", "0.4", "500")),
    )
    trigger = evaluate_threshold_trigger(
        current_weight="0.5", target_weight="0.6", threshold="0.05"
    )
    return build_rebalance_plan(
        trigger=trigger, projection=projection, plan_time_us=1700000000000000
    ), projection


def _disclose(plan, projection, **overrides):
    params = {
        "plan": plan,
        "projection": projection,
        "prices": (("BTC", "50000"), ("ETH", "1600")),
        "fee_rate": "0.001",
        "qty_step": "0.001",
        "min_notional": "10",
        "cash_reserve": "1000",
    }
    params.update(overrides)
    return disclose_execution(**params)


class DiscloseExecutionTests(unittest.TestCase):
    def test_ready_lines_carry_exact_fee_and_quantization(self):
        plan, projection = _plan()
        result = _disclose(plan, projection)
        self.assertEqual(result.status, "READY")
        self.assertEqual(result.plan_id, plan.plan_id)
        by_asset = {line.asset: line for line in result.lines}
        btc = by_asset["BTC"]
        self.assertEqual(
            (btc.side, btc.qty, btc.fee, btc.quantized_qty, btc.remainder_qty, btc.status),
            ("BUY", "0.002", "0.1", "0.002", "0", "READY"),
        )
        eth = by_asset["ETH"]
        self.assertEqual(
            (eth.side, eth.qty, eth.fee, eth.quantized_qty, eth.remainder_qty, eth.status),
            ("SELL", "0.0625", "0.1", "0.062", "0.0005", "READY"),
        )
        self.assertEqual(result.total_fee, "0.2")

    def test_unrepresentable_line_is_skipped_explicitly(self):
        plan, projection = _plan()
        result = _disclose(plan, projection, prices=(("BTC", "50000"), ("ETH", "1000000")))
        by_asset = {line.asset: line for line in result.lines}
        self.assertEqual(by_asset["ETH"].status, "SKIPPED_UNREPRESENTABLE")
        self.assertEqual(by_asset["BTC"].status, "READY")
        self.assertEqual(result.status, "READY")

    def test_below_min_notional_is_skipped_explicitly(self):
        plan, projection = _plan()
        result = _disclose(plan, projection, min_notional="150")
        by_asset = {line.asset: line for line in result.lines}
        self.assertEqual(by_asset["BTC"].status, "SKIPPED_BELOW_MIN")
        self.assertEqual(by_asset["ETH"].status, "SKIPPED_BELOW_MIN")

    def test_insufficient_reserve_blocks_the_plan(self):
        plan, projection = _plan()
        result = _disclose(plan, projection, cash_reserve="50")
        self.assertEqual(result.status, "BLOCKED_INSUFFICIENT_RESERVE")

    def test_plan_projection_mismatch_rejected(self):
        plan, _ = _plan()
        other = build_rebalance_projection(
            valuation_asset="USDT",
            total_equity="2000",
            allocations=(("BTC", "0.6", "1000"), ("ETH", "0.4", "1000")),
        )
        with self.assertRaises(RebalanceExecutionError) as ctx:
            _disclose(plan, other)
        self.assertEqual(ctx.exception.code, "REBALANCE_EXEC_PLAN_MISMATCH")

    def test_missing_price_rejected(self):
        plan, projection = _plan()
        with self.assertRaises(RebalanceExecutionError) as ctx:
            _disclose(plan, projection, prices=(("BTC", "50000"),))
        self.assertEqual(ctx.exception.code, "REBALANCE_EXEC_PRICE_MISSING")

    def test_fee_rate_bounds_rejected(self):
        plan, projection = _plan()
        for bad in ("-0.001", "1", "abc"):
            with self.assertRaises(RebalanceExecutionError) as ctx:
                _disclose(plan, projection, fee_rate=bad)
            self.assertEqual(ctx.exception.code, "REBALANCE_EXEC_FEE_INVALID")


class BindExecutionOrdersTests(unittest.TestCase):
    def test_ready_disclosure_binds_deterministic_candidates(self):
        plan, projection = _plan()
        disclosure = _disclose(plan, projection)
        first = bind_execution_orders(disclosure, order_time_us=1700000001000000)
        second = bind_execution_orders(disclosure, order_time_us=1700000001000000)
        self.assertEqual(len(first), 2)
        self.assertEqual(first, second)
        btc = next(c for c in first if c.asset == "BTC")
        self.assertEqual((btc.side, btc.qty, btc.status), ("BUY", "0.002", "CANDIDATE"))
        self.assertRegex(btc.candidate_id, r"\A[0-9a-f]{64}\Z")

    def test_empty_disclosure_binds_empty_tuple(self):
        plan, projection = _plan()
        disclosure = _disclose(plan, projection, min_notional="150")
        self.assertEqual(disclosure.status, "EMPTY_NO_TRADABLE_LINE")
        self.assertEqual(
            bind_execution_orders(disclosure, order_time_us=1700000001000000), ()
        )

    def test_blocked_disclosure_binds_nothing(self):
        plan, projection = _plan()
        disclosure = _disclose(plan, projection, cash_reserve="50")
        with self.assertRaises(RebalanceExecutionError) as ctx:
            bind_execution_orders(disclosure, order_time_us=1700000001000000)
        self.assertEqual(ctx.exception.code, "REBALANCE_EXEC_BLOCKED")


if __name__ == "__main__":
    unittest.main()
