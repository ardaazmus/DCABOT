import unittest

from dcabot.application.conditional_execution import (
    ConditionalExecutionError,
    ConditionalExecutionOutcome,
    ConditionalStatus,
    create_conditional_execution,
)


class ConditionalExecutionContractTests(unittest.TestCase):
    def _armed(self):
        return create_conditional_execution(
            conditional_order_id="conditional-1",
            symbol="BTCUSDT",
            side="SELL",
            trigger_kind="STOP_PRICE",
            trigger_price="95",
        )

    def test_trigger_observation_does_not_create_execution_or_fill(self):
        result = self._armed().observe_trigger(
            trigger_event_id="trigger-event-1",
            observed_at_ms=100,
            observed_price="94.5",
        )

        self.assertEqual(result.outcome, ConditionalExecutionOutcome.ACCEPTED)
        self.assertEqual(result.execution.status, ConditionalStatus.TRIGGERED)
        self.assertEqual(result.execution.trigger_event_id, "trigger-event-1")
        self.assertIsNone(result.execution.execution_order_id)
        self.assertFalse(hasattr(result.execution, "fills"))

    def test_trigger_is_idempotent_but_a_different_trigger_conflicts(self):
        triggered = self._armed().observe_trigger(
            trigger_event_id="trigger-event-1",
            observed_at_ms=100,
            observed_price="94.5",
        ).execution

        duplicate = triggered.observe_trigger(
            trigger_event_id="trigger-event-1",
            observed_at_ms=100,
            observed_price="94.50",
        )

        self.assertEqual(duplicate.outcome, ConditionalExecutionOutcome.DUPLICATE)
        with self.assertRaisesRegex(ConditionalExecutionError, "CONDITIONAL_TRIGGER_CONFLICT"):
            triggered.observe_trigger(
                trigger_event_id="trigger-event-2",
                observed_at_ms=101,
                observed_price="94",
            )

    def test_execution_identity_requires_trigger_and_is_explicit(self):
        with self.assertRaisesRegex(ConditionalExecutionError, "CONDITIONAL_EXECUTION_REQUIRES_TRIGGER"):
            self._armed().bind_execution(
                execution_order_id="execution-order-1",
                execution_order_type="MARKET",
                execution_event_id="execution-event-1",
                observed_at_ms=101,
            )

        triggered = self._armed().observe_trigger(
            trigger_event_id="trigger-event-1",
            observed_at_ms=100,
            observed_price="94.5",
        ).execution
        result = triggered.bind_execution(
            execution_order_id="execution-order-1",
            execution_order_type="MARKET",
            execution_event_id="execution-event-1",
            observed_at_ms=101,
        )

        self.assertEqual(result.outcome, ConditionalExecutionOutcome.ACCEPTED)
        self.assertEqual(result.execution.status, ConditionalStatus.EXECUTION_IDENTIFIED)
        self.assertEqual(result.execution.execution_order_id, "execution-order-1")
        self.assertEqual(result.execution.execution_order_type, "MARKET")
        self.assertEqual(result.execution.execution_event_id, "execution-event-1")

        duplicate = result.execution.bind_execution(
            execution_order_id="execution-order-1",
            execution_order_type="MARKET",
            execution_event_id="execution-event-1",
            observed_at_ms=101,
        )
        self.assertEqual(duplicate.outcome, ConditionalExecutionOutcome.DUPLICATE)

    def test_execution_before_trigger_or_out_of_order_is_rejected(self):
        triggered = self._armed().observe_trigger(
            trigger_event_id="trigger-event-1",
            observed_at_ms=100,
            observed_price="94.5",
        ).execution

        with self.assertRaisesRegex(ConditionalExecutionError, "CONDITIONAL_EXECUTION_OUT_OF_ORDER"):
            triggered.bind_execution(
                execution_order_id="execution-order-1",
                execution_order_type="LIMIT",
                execution_event_id="execution-event-1",
                observed_at_ms=99,
            )

    def test_gap_or_stale_quarantines_without_erasing_trigger_identity(self):
        triggered = self._armed().observe_trigger(
            trigger_event_id="trigger-event-1",
            observed_at_ms=100,
            observed_price="94.5",
        ).execution
        quarantined = triggered.quarantine(
            evidence_event_id="gap-event-1",
            observed_at_ms=101,
            reason="GAP",
        )

        self.assertEqual(quarantined.outcome, ConditionalExecutionOutcome.ACCEPTED)
        self.assertEqual(quarantined.execution.status, ConditionalStatus.QUARANTINED)
        self.assertEqual(quarantined.execution.trigger_event_id, "trigger-event-1")
        self.assertEqual(quarantined.execution.quarantine_reason, "GAP")
        with self.assertRaisesRegex(ConditionalExecutionError, "CONDITIONAL_QUARANTINED"):
            quarantined.execution.bind_execution(
                execution_order_id="execution-order-1",
                execution_order_type="MARKET",
                execution_event_id="execution-event-1",
                observed_at_ms=102,
            )

    def test_cancel_confirmation_is_explicit_and_execution_cancel_race_fails_closed(self):
        triggered = self._armed().observe_trigger(
            trigger_event_id="trigger-event-1",
            observed_at_ms=100,
            observed_price="94.5",
        ).execution
        canceled = triggered.confirm_cancel(
            cancel_event_id="cancel-event-1",
            observed_at_ms=101,
        )

        self.assertEqual(canceled.execution.status, ConditionalStatus.CANCELED)
        with self.assertRaisesRegex(ConditionalExecutionError, "CONDITIONAL_CANCEL_RACE"):
            canceled.execution.bind_execution(
                execution_order_id="execution-order-1",
                execution_order_type="MARKET",
                execution_event_id="execution-event-1",
                observed_at_ms=102,
            )

        bound = triggered.bind_execution(
            execution_order_id="execution-order-1",
            execution_order_type="MARKET",
            execution_event_id="execution-event-1",
            observed_at_ms=101,
        ).execution
        with self.assertRaisesRegex(ConditionalExecutionError, "CONDITIONAL_CANCEL_RACE"):
            bound.confirm_cancel(cancel_event_id="cancel-event-2", observed_at_ms=102)
        with self.assertRaisesRegex(ConditionalExecutionError, "CONDITIONAL_EXECUTION_CONFLICT"):
            bound.quarantine(
                evidence_event_id="conflict-event-1",
                observed_at_ms=102,
                reason="CONFLICT",
            )


if __name__ == "__main__":
    unittest.main()
