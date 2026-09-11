import unittest

from dcabot.application.pause_order_policy import (
    PauseOrderPolicyError,
    PausedOrderDecision,
    evaluate_paused_orders,
)


class PauseOrderPolicyTests(unittest.TestCase):
    def test_paused_policy_blocks_new_intents_for_every_pending_order_policy(self):
        expected = {
            "KEEP_OPEN": PausedOrderDecision(
                pending_order_action="KEEP_OPEN",
                new_intent_action="BLOCKED",
                cancellation_state="NOT_REQUESTED",
            ),
            "CANCEL_REQUESTED": PausedOrderDecision(
                pending_order_action="CANCEL_REQUESTED",
                new_intent_action="BLOCKED",
                cancellation_state="REQUESTED_NOT_CONFIRMED",
            ),
            "BLOCKED": PausedOrderDecision(
                pending_order_action="BLOCKED",
                new_intent_action="BLOCKED",
                cancellation_state="NOT_REQUESTED",
            ),
        }

        for policy, expected_decision in expected.items():
            with self.subTest(policy=policy):
                self.assertEqual(evaluate_paused_orders(policy), expected_decision)

    def test_paused_policy_does_not_claim_cancellation_or_fill(self):
        decision = evaluate_paused_orders("CANCEL_REQUESTED")

        self.assertEqual(decision.cancellation_state, "REQUESTED_NOT_CONFIRMED")
        self.assertEqual(decision.pending_order_action, "CANCEL_REQUESTED")
        self.assertEqual(decision.new_intent_action, "BLOCKED")

    def test_unknown_paused_policy_is_rejected(self):
        with self.assertRaisesRegex(
            PauseOrderPolicyError, "PAUSE_ORDER_POLICY_INVALID"
        ):
            evaluate_paused_orders("AUTO_CANCEL")


if __name__ == "__main__":
    unittest.main()
