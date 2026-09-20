import unittest

from dcabot.application.market_base_quantity import create_market_base_execution
from dcabot.application.reconciliation import (
    ConnectionState,
    EventDecision,
    OrderLookup,
    UserDataEvent,
)
from dcabot.application.spot_order_lifecycle import SpotOrderEvent
from dcabot.application.venue_event_binding import evaluate_venue_event_lookup
from dcabot.application.venue_spot_event_mapping import build_spot_event_mapping_candidate


class MarketExecutionReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.execution = create_market_base_execution(
            order_id="order-1",
            symbol="BTCUSDT",
            side="BUY",
            requested_quantity="1",
            reference_price="100",
            max_slippage_bps=200,
        )
        result = self.execution.apply_fill(
            execution_id="execution-1",
            base_quantity="0.5",
            quote_quantity="50",
            fee="0.05",
            fee_asset="USDT",
        )
        self.execution = result.execution
        self.event = UserDataEvent.create("stream-1", 100, "executionReport", 777)
        self.lookup = OrderLookup.found(777)
        self.observation = (
            self.event,
            EventDecision.ACCEPTED,
            ConnectionState.CONNECTED_READ_ONLY,
        )
        self.spot_event = SpotOrderEvent(
            order_id="order-1",
            event_id="spot-event-1",
            execution_id="execution-1",
            event_time_ms=100,
            status="PARTIALLY_FILLED",
            last_filled_qty="0.5",
            cumulative_filled_qty="0.5",
            last_price="100",
        )
        self.candidate = build_spot_event_mapping_candidate(
            evaluate_venue_event_lookup(self.event, self.lookup), self.spot_event
        )

    def test_matched_identity_binds_exact_market_fill_without_core_promotion(self):
        from dcabot.application.market_execution_reconciliation import (
            bind_market_fill_to_reconciliation,
        )

        binding = bind_market_fill_to_reconciliation(
            self.candidate,
            self.observation,
            self.lookup,
            self.execution,
            self.execution.fills[0],
        )

        self.assertEqual(binding.venue_event_id, "stream-1")
        self.assertEqual(binding.venue_order_id, 777)
        self.assertEqual(binding.spot_event_id, "spot-event-1")
        self.assertEqual(binding.market_order_id, "order-1")
        self.assertEqual(binding.fill.execution_id, "execution-1")
        self.assertEqual(binding.fill.quote_quantity, "50")
        self.assertFalse(hasattr(binding, "core_events"))

    def test_unmatched_or_unaccepted_evidence_cannot_bind_market_fill(self):
        from dcabot.application.market_execution_reconciliation import (
            bind_market_fill_to_reconciliation,
        )

        with self.assertRaisesRegex(ValueError, "MARKET_RECONCILIATION_LOOKUP_INVALID"):
            bind_market_fill_to_reconciliation(
                self.candidate,
                self.observation,
                OrderLookup.not_found(),
                self.execution,
                self.execution.fills[0],
            )
        with self.assertRaisesRegex(ValueError, "MARKET_RECONCILIATION_DECISION_INVALID"):
            bind_market_fill_to_reconciliation(
                self.candidate,
                (self.event, EventDecision.CONFLICT, ConnectionState.GAP),
                self.lookup,
                self.execution,
                self.execution.fills[0],
            )

    def test_execution_or_order_identity_mismatch_fails_closed(self):
        from dcabot.application.market_execution_reconciliation import (
            bind_market_fill_to_reconciliation,
        )

        with self.assertRaisesRegex(ValueError, "MARKET_RECONCILIATION_EXECUTION_INVALID"):
            bind_market_fill_to_reconciliation(
                self.candidate,
                self.observation,
                self.lookup,
                self.execution,
                type(self.execution.fills[0])(
                    "execution-2", "0.5", "50", "100", "0.05", "USDT"
                ),
            )


if __name__ == "__main__":
    unittest.main()
