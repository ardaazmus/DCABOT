import unittest

from dcabot.application.rebalance_triggers import (
    RebalanceTriggerError,
    ThresholdTriggerDecision,
    TimeTriggerDecision,
    evaluate_threshold_trigger,
    evaluate_time_trigger,
)


class RebalanceTriggerTests(unittest.TestCase):
    def test_threshold_trigger_uses_inclusive_exact_deviation(self):
        result = evaluate_threshold_trigger(
            current_weight="0.55",
            target_weight="0.60",
            threshold="0.05",
        )

        self.assertEqual(
            result,
            ThresholdTriggerDecision(
                policy="THRESHOLD",
                status="TRIGGERED",
                deviation="0.05",
                threshold="0.05",
            ),
        )

    def test_threshold_below_boundary_is_not_triggered(self):
        result = evaluate_threshold_trigger(
            current_weight="0.551",
            target_weight="0.60",
            threshold="0.05",
        )

        self.assertEqual(result.status, "NOT_TRIGGERED")
        self.assertEqual(result.deviation, "0.049")

    def test_time_trigger_uses_inclusive_elapsed_interval(self):
        result = evaluate_time_trigger(
            last_rebalance_time_us=1_000,
            observation_time_us=2_000,
            interval_us=1_000,
        )

        self.assertEqual(
            result,
            TimeTriggerDecision(
                policy="TIME_INTERVAL",
                status="TRIGGERED",
                elapsed_us=1_000,
                interval_us=1_000,
            ),
        )

    def test_time_before_boundary_is_not_triggered(self):
        result = evaluate_time_trigger(
            last_rebalance_time_us=1_000,
            observation_time_us=1_999,
            interval_us=1_000,
        )

        self.assertEqual(result.status, "NOT_TRIGGERED")
        self.assertEqual(result.elapsed_us, 999)

    def test_invalid_weight_or_time_inputs_fail_closed(self):
        with self.assertRaisesRegex(
            RebalanceTriggerError, "REBALANCE_WEIGHT_INVALID"
        ):
            evaluate_threshold_trigger(
                current_weight="1.1", target_weight="0.5", threshold="0.1"
            )
        with self.assertRaisesRegex(
            RebalanceTriggerError, "REBALANCE_TIME_ORDER_INVALID"
        ):
            evaluate_time_trigger(
                last_rebalance_time_us=2,
                observation_time_us=1,
                interval_us=1,
            )
        with self.assertRaisesRegex(
            RebalanceTriggerError, "REBALANCE_INTERVAL_INVALID"
        ):
            evaluate_time_trigger(
                last_rebalance_time_us=1,
                observation_time_us=2,
                interval_us=0,
            )
        for field in (
            "last_rebalance_time_us",
            "observation_time_us",
            "interval_us",
        ):
            with self.subTest(field=field), self.assertRaises(
                RebalanceTriggerError
            ):
                values = {
                    "last_rebalance_time_us": 1,
                    "observation_time_us": 2,
                    "interval_us": 1,
                }
                values[field] = True
                evaluate_time_trigger(**values)
        for threshold in ("NaN", "Infinity", "1e-2"):
            with self.subTest(threshold=threshold), self.assertRaisesRegex(
                RebalanceTriggerError, "REBALANCE_THRESHOLD_INVALID"
            ):
                evaluate_threshold_trigger(
                    current_weight="0.5",
                    target_weight="0.6",
                    threshold=threshold,
                )

    def test_threshold_zero_and_signed_zero_are_exact(self):
        result = evaluate_threshold_trigger(
            current_weight="-0.0", target_weight="0.0", threshold="0"
        )

        self.assertEqual(
            result,
            ThresholdTriggerDecision(
                policy="THRESHOLD",
                status="TRIGGERED",
                deviation="0",
                threshold="0",
            ),
        )

    def test_same_time_without_elapsed_interval_is_not_triggered(self):
        result = evaluate_time_trigger(
            last_rebalance_time_us=1_000,
            observation_time_us=1_000,
            interval_us=1,
        )

        self.assertEqual(
            result,
            TimeTriggerDecision(
                policy="TIME_INTERVAL",
                status="NOT_TRIGGERED",
                elapsed_us=0,
                interval_us=1,
            ),
        )

    def test_trigger_decisions_have_no_order_or_fill_authority(self):
        threshold = evaluate_threshold_trigger(
            current_weight="0.5", target_weight="0.6", threshold="0.1"
        )
        time = evaluate_time_trigger(
            last_rebalance_time_us=1, observation_time_us=2, interval_us=1
        )

        self.assertFalse(hasattr(threshold, "orders"))
        self.assertFalse(hasattr(time, "fills"))
