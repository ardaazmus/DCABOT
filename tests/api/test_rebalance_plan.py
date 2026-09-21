import unittest

from dcabot.server.api import (
    _rebalance_disclose,
    _rebalance_plan,
    _validate_rebalance_disclose_payload,
    _validate_rebalance_plan_payload,
)


def _plan_body():
    return {
        "trigger": {
            "policy": "threshold",
            "current_weight": "0.5",
            "target_weight": "0.6",
            "threshold": "0.05",
        },
        "projection": {
            "valuation_asset": "USDT",
            "total_equity": "1000",
            "allocations": [["BTC", "0.6", "500"], ["ETH", "0.4", "500"]],
        },
    }


class RebalancePlanApiTests(unittest.TestCase):
    def test_valid_plan_returns_identity_and_gross(self):
        validated, fields = _validate_rebalance_plan_payload(_plan_body())
        self.assertEqual(fields, {})
        result = _rebalance_plan(validated, 1700000000000000)
        self.assertEqual(result["status"], "DRAFT")
        self.assertEqual(result["gross_buy"], "100")
        self.assertEqual(result["gross_sell"], "100")
        self.assertRegex(result["plan_id"], r"\A[0-9a-f]{64}\Z")

    def test_untriggered_plan_is_value_error(self):
        body = _plan_body()
        body["trigger"]["current_weight"] = "0.59"
        validated, fields = _validate_rebalance_plan_payload(body)
        self.assertEqual(fields, {})
        with self.assertRaises(ValueError) as ctx:
            _rebalance_plan(validated, 1700000000000000)
        self.assertIn("REBALANCE_PLAN_TRIGGER_NOT_TRIGGERED", str(ctx.exception))

    def test_unknown_trigger_policy_is_field_error(self):
        body = _plan_body()
        body["trigger"]["policy"] = "vibes"
        validated, fields = _validate_rebalance_plan_payload(body)
        self.assertIsNone(validated)
        self.assertIn("trigger", fields)

    def test_time_trigger_plan(self):
        body = _plan_body()
        body["trigger"] = {
            "policy": "time",
            "last_rebalance_us": 1699999990000000,
            "now_us": 1700000000000000,
            "interval_us": 1000000,
        }
        validated, fields = _validate_rebalance_plan_payload(body)
        self.assertEqual(fields, {})
        result = _rebalance_plan(validated, 1700000000000000)
        self.assertEqual(result["trigger_policy"], "TIME_INTERVAL")


class RebalanceDiscloseApiTests(unittest.TestCase):
    def _disclose_body(self):
        plan_validated, _ = _validate_rebalance_plan_payload(_plan_body())
        plan = _rebalance_plan(plan_validated, 1700000000000000)
        return {
            "plan": plan,
            "projection": _plan_body()["projection"],
            "prices": [["BTC", "50000"], ["ETH", "1600"]],
            "fee_rate": "0.001",
            "qty_step": "0.001",
            "min_notional": "10",
            "cash_reserve": "1000",
        }

    def test_disclose_returns_lines_and_candidates(self):
        validated, fields = _validate_rebalance_disclose_payload(self._disclose_body())
        self.assertEqual(fields, {})
        result = _rebalance_disclose(validated, 1700000001000000)
        self.assertEqual(result["disclosure"]["status"], "READY")
        self.assertEqual(len(result["disclosure"]["lines"]), 2)
        self.assertEqual(len(result["candidates"]), 2)
        self.assertEqual(result["candidates"][0]["status"], "CANDIDATE")

    def test_blocked_plan_returns_no_candidates(self):
        body = self._disclose_body()
        body["cash_reserve"] = "50"
        validated, fields = _validate_rebalance_disclose_payload(body)
        self.assertEqual(fields, {})
        result = _rebalance_disclose(validated, 1700000001000000)
        self.assertEqual(result["disclosure"]["status"], "BLOCKED_INSUFFICIENT_RESERVE")
        self.assertEqual(result["candidates"], [])


if __name__ == "__main__":
    unittest.main()
