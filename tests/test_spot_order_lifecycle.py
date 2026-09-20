import unittest

from dcabot.application.instrument_filters import InstrumentFilterProfile
from dcabot.application.spot_order_lifecycle import (
    EventOutcome,
    SpotOrderLifecycle,
    SpotOrderType,
    SpotSide,
    create_market_order,
    create_limit_order,
    new_lifecycle,
    report,
)


class SpotOrderLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.profile = InstrumentFilterProfile(
            profile_id="spot-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="10",
        )

    def test_limit_order_accepts_partial_fills_and_preserves_leaves(self):
        order = create_limit_order(
            self.profile,
            order_id="order-1",
            client_order_id="client-1",
            symbol="BTCUSDT",
            side=SpotSide.BUY,
            quantity="1",
            price="100",
        )
        lifecycle = new_lifecycle(order)

        result = lifecycle.apply(
            lifecycle.event(
                event_id="event-1",
                execution_id="execution-1",
                event_time_ms=100,
                status="PARTIALLY_FILLED",
                last_filled_qty="0.4",
                cumulative_filled_qty="0.4",
                last_price="100",
            )
        )

        self.assertEqual(result.outcome, EventOutcome.ACCEPTED)
        self.assertEqual(report(result.lifecycle), {
            "order_id": "order-1",
            "client_order_id": "client-1",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "order_type": "LIMIT",
            "status": "PARTIALLY_FILLED",
            "requested_quantity": "1",
            "filled_quantity": "0.4",
            "leaves_quantity": "0.6",
            "quote_order_quantity": None,
            "reconciliation_required": False,
        })

    def test_duplicate_execution_is_idempotent_and_conflict_requires_reconciliation(self):
        order = create_limit_order(
            self.profile,
            order_id="order-1",
            client_order_id="client-1",
            symbol="BTCUSDT",
            side=SpotSide.BUY,
            quantity="1",
            price="100",
        )
        lifecycle = new_lifecycle(order)
        event = lifecycle.event(
            event_id="event-1",
            execution_id="execution-1",
            event_time_ms=100,
            status="PARTIALLY_FILLED",
            last_filled_qty="0.4",
            cumulative_filled_qty="0.4",
            last_price="100",
        )
        lifecycle = lifecycle.apply(event).lifecycle

        duplicate = lifecycle.apply(event)
        self.assertEqual(duplicate.outcome, EventOutcome.DUPLICATE)
        self.assertEqual(duplicate.lifecycle, lifecycle)

        conflict = lifecycle.apply(
            lifecycle.event(
                event_id="event-2",
                execution_id="execution-1",
                event_time_ms=101,
                status="PARTIALLY_FILLED",
                last_filled_qty="0.4",
                cumulative_filled_qty="0.4",
                last_price="99.5",
            )
        )
        self.assertEqual(conflict.outcome, EventOutcome.CONFLICT)
        self.assertTrue(conflict.lifecycle.reconciliation_required)

    def test_cancel_event_can_include_last_fill_and_closes_remaining_quantity(self):
        order = create_limit_order(
            self.profile,
            order_id="order-1",
            client_order_id="client-1",
            symbol="BTCUSDT",
            side=SpotSide.SELL,
            quantity="1",
            price="100",
        )
        lifecycle = new_lifecycle(order)
        result = lifecycle.apply(
            lifecycle.event(
                event_id="event-1",
                execution_id="execution-1",
                event_time_ms=100,
                status="CANCELED",
                last_filled_qty="0.4",
                cumulative_filled_qty="0.4",
                last_price="100",
            )
        )

        self.assertEqual(result.outcome, EventOutcome.ACCEPTED)
        self.assertEqual(result.lifecycle.order.status, "CANCELED")
        self.assertEqual(result.lifecycle.order.leaves_quantity, "0.6")

    def test_late_fill_after_terminal_state_is_quarantined(self):
        order = create_limit_order(
            self.profile,
            order_id="order-1",
            client_order_id="client-1",
            symbol="BTCUSDT",
            side=SpotSide.BUY,
            quantity="1",
            price="100",
        )
        lifecycle = new_lifecycle(order)
        lifecycle = lifecycle.apply(
            lifecycle.event(
                event_id="event-1",
                execution_id=None,
                event_time_ms=100,
                status="CANCELED",
                last_filled_qty="0",
                cumulative_filled_qty="0",
                last_price=None,
            )
        ).lifecycle
        result = lifecycle.apply(
            lifecycle.event(
                event_id="event-2",
                execution_id="execution-2",
                event_time_ms=101,
                status="FILLED",
                last_filled_qty="1",
                cumulative_filled_qty="1",
                last_price="100",
            )
        )

        self.assertEqual(result.outcome, EventOutcome.CONFLICT)
        self.assertEqual(result.lifecycle.order.status, "CANCELED")
        self.assertTrue(result.lifecycle.reconciliation_required)

    def test_out_of_order_event_does_not_rewrite_order(self):
        order = create_limit_order(
            self.profile,
            order_id="order-1",
            client_order_id="client-1",
            symbol="BTCUSDT",
            side=SpotSide.BUY,
            quantity="1",
            price="100",
        )
        lifecycle = new_lifecycle(order)
        lifecycle = lifecycle.apply(
            lifecycle.event(
                event_id="event-1",
                execution_id="execution-1",
                event_time_ms=100,
                status="PARTIALLY_FILLED",
                last_filled_qty="0.4",
                cumulative_filled_qty="0.4",
                last_price="100",
            )
        ).lifecycle
        result = lifecycle.apply(
            lifecycle.event(
                event_id="event-2",
                execution_id="execution-2",
                event_time_ms=99,
                status="FILLED",
                last_filled_qty="0.6",
                cumulative_filled_qty="1",
                last_price="100",
            )
        )

        self.assertEqual(result.outcome, EventOutcome.OUT_OF_ORDER)
        self.assertEqual(result.lifecycle.order.status, "PARTIALLY_FILLED")
        self.assertTrue(result.lifecycle.reconciliation_required)

    def test_event_cannot_be_applied_to_a_different_order_lifecycle(self):
        first = create_limit_order(
            self.profile,
            order_id="order-1",
            client_order_id="client-1",
            symbol="BTCUSDT",
            side=SpotSide.BUY,
            quantity="1",
            price="100",
        )
        second = create_limit_order(
            self.profile,
            order_id="order-2",
            client_order_id="client-2",
            symbol="BTCUSDT",
            side=SpotSide.BUY,
            quantity="1",
            price="100",
        )
        first_lifecycle = new_lifecycle(first)
        second_lifecycle = new_lifecycle(second)
        event = first_lifecycle.event(
            event_id="event-1",
            execution_id="execution-1",
            event_time_ms=100,
            status="PARTIALLY_FILLED",
            last_filled_qty="0.4",
            cumulative_filled_qty="0.4",
            last_price="100",
        )

        result = second_lifecycle.apply(event)

        self.assertEqual(result.outcome, EventOutcome.CONFLICT)
        self.assertEqual(result.lifecycle.order.order_id, "order-2")
        self.assertTrue(result.lifecycle.reconciliation_required)

    def test_market_quote_order_does_not_derive_base_leaves(self):
        order = create_market_order(
            self.profile,
            order_id="order-1",
            client_order_id="client-1",
            symbol="BTCUSDT",
            side=SpotSide.BUY,
            quote_order_quantity="50",
        )
        self.assertEqual(order.order_type, SpotOrderType.MARKET)
        lifecycle = new_lifecycle(order)
        result = lifecycle.apply(
            lifecycle.event(
                event_id="event-1",
                execution_id="execution-1",
                event_time_ms=100,
                status="FILLED",
                last_filled_qty="0.5",
                cumulative_filled_qty="0.5",
                last_price="100",
            )
        )

        self.assertEqual(result.outcome, EventOutcome.ACCEPTED)
        self.assertIsNone(result.lifecycle.order.leaves_quantity)
        self.assertEqual(result.lifecycle.order.quote_order_quantity, "50")

    def test_market_base_quantity_tracks_fills_without_quote_economics(self):
        order = create_market_order(
            self.profile,
            order_id="order-1",
            client_order_id="client-1",
            symbol="BTCUSDT",
            side=SpotSide.BUY,
            quantity="1",
        )
        lifecycle = new_lifecycle(order)
        partial = lifecycle.apply(
            lifecycle.event(
                event_id="event-1",
                execution_id="execution-1",
                event_time_ms=100,
                status="PARTIALLY_FILLED",
                last_filled_qty="0.4",
                cumulative_filled_qty="0.4",
                last_price="101",
            )
        )
        final = partial.lifecycle.apply(
            partial.lifecycle.event(
                event_id="event-2",
                execution_id="execution-2",
                event_time_ms=101,
                status="FILLED",
                last_filled_qty="0.6",
                cumulative_filled_qty="1",
                last_price="99",
            )
        )

        self.assertEqual(final.outcome, EventOutcome.ACCEPTED)
        self.assertEqual(
            report(final.lifecycle),
            {
                "order_id": "order-1",
                "client_order_id": "client-1",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "order_type": "MARKET",
                "status": "FILLED",
                "requested_quantity": "1",
                "filled_quantity": "1",
                "leaves_quantity": "0",
                "quote_order_quantity": None,
                "reconciliation_required": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
