import json
from pathlib import Path
from fractions import Fraction as F
import unittest

from dcabot.application.instrument_filters import InstrumentFilterProfile
from dcabot.application.spot_lifecycle_core_binding import (
    CoreBindingOutcome,
    bind_spot_event_to_core,
)
from dcabot.application.spot_order_lifecycle import (
    SpotSide,
    create_limit_order,
    create_market_order,
    new_lifecycle,
)
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply, report


class SpotLifecycleCoreBindingTests(unittest.TestCase):
    def setUp(self):
        self.profile = InstrumentFilterProfile(
            profile_id="spot-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="10",
        )
        config_path = Path(__file__).resolve().parents[1] / "config/paper.json"
        self.config = Config.parse(json.loads(config_path.read_text()))

    def _marked_state(self):
        return apply(State(), {"type": "MARK", "price": "100"}, self.config)

    def _limit_lifecycle(self, side=SpotSide.BUY):
        order = create_limit_order(
            self.profile,
            order_id="order-1",
            client_order_id="client-1",
            symbol="BTCUSDT",
            side=side,
            quantity="1",
            price="100",
        )
        return new_lifecycle(order)

    def _event(self, lifecycle, *, status="PARTIALLY_FILLED", last="0.4", cumulative="0.4"):
        return lifecycle.event(
            event_id="event-1",
            execution_id="execution-1" if last != "0" else None,
            event_time_ms=100,
            status=status,
            last_filled_qty=last,
            cumulative_filled_qty=cumulative,
            last_price="100" if last != "0" else None,
        )

    def test_partial_limit_event_posts_intent_and_one_fill(self):
        lifecycle = self._limit_lifecycle()
        result = bind_spot_event_to_core(
            self._marked_state(), self.config, lifecycle, self._event(lifecycle),
            fee="0.04", fee_asset="USDT", core_role="BASE",
        )

        self.assertEqual(result.outcome, CoreBindingOutcome.ACCEPTED)
        self.assertEqual(result.core_state.position.qty, F(2, 5))
        self.assertEqual(result.core_state.orders["order-1"].status, "PARTIALLY_FILLED")
        self.assertEqual([event["type"] for event in result.core_events], ["INTENT", "FILL"])

    def test_duplicate_event_has_no_second_core_effect(self):
        lifecycle = self._limit_lifecycle()
        event = self._event(lifecycle)
        first = bind_spot_event_to_core(
            self._marked_state(), self.config, lifecycle, event,
            fee="0.04", fee_asset="USDT", core_role="BASE",
        )
        second = bind_spot_event_to_core(
            first.core_state, self.config, first.lifecycle, event,
            fee="0.04", fee_asset="USDT", core_role="BASE",
        )

        self.assertEqual(second.outcome, CoreBindingOutcome.DUPLICATE)
        self.assertEqual(second.core_events, ())
        self.assertEqual(report(second.core_state, self.config), report(first.core_state, self.config))

    def test_conflict_does_not_post_and_requires_reconciliation(self):
        lifecycle = self._limit_lifecycle()
        first = bind_spot_event_to_core(
            self._marked_state(), self.config, lifecycle, self._event(lifecycle),
            fee="0.04", fee_asset="USDT", core_role="BASE",
        )
        conflict = first.lifecycle.event(
            event_id="event-2", execution_id="execution-1", event_time_ms=101,
            status="PARTIALLY_FILLED", last_filled_qty="0.4",
            cumulative_filled_qty="0.4", last_price="99.5",
        )
        second = bind_spot_event_to_core(
            first.core_state, self.config, first.lifecycle, conflict,
            fee="0.04", fee_asset="USDT", core_role="BASE",
        )

        self.assertEqual(second.outcome, CoreBindingOutcome.RECONCILIATION_REQUIRED)
        self.assertEqual(second.core_events, ())
        self.assertEqual(second.core_state, first.core_state)
        self.assertTrue(second.lifecycle.reconciliation_required)

    def test_market_event_is_not_mapped_to_limit_core(self):
        order = create_market_order(
            self.profile, order_id="order-1", client_order_id="client-1",
            symbol="BTCUSDT", side=SpotSide.BUY, quote_order_quantity="50",
        )
        lifecycle = new_lifecycle(order)
        result = bind_spot_event_to_core(
            State(), self.config, lifecycle, self._event(lifecycle, status="FILLED", last="0.5", cumulative="0.5"),
            fee="0.05", fee_asset="USDT",
        )

        self.assertEqual(result.outcome, CoreBindingOutcome.CORE_ORDER_TYPE_UNSUPPORTED)
        self.assertEqual(result.core_events, ())
        self.assertEqual(result.core_state, State())
        self.assertEqual(result.lifecycle, lifecycle)

    def test_base_quantity_market_event_is_not_mapped_to_limit_core(self):
        order = create_market_order(
            self.profile, order_id="order-1", client_order_id="client-1",
            symbol="BTCUSDT", side=SpotSide.BUY, quantity="1",
        )
        lifecycle = new_lifecycle(order)
        result = bind_spot_event_to_core(
            State(), self.config, lifecycle,
            self._event(lifecycle, status="PARTIALLY_FILLED", last="0.5", cumulative="0.5"),
            fee="0.05", fee_asset="USDT",
        )

        self.assertEqual(result.outcome, CoreBindingOutcome.CORE_ORDER_TYPE_UNSUPPORTED)
        self.assertEqual(result.core_events, ())
        self.assertEqual(result.core_state, State())
        self.assertEqual(result.lifecycle, lifecycle)

    def test_filled_event_posts_final_coverage(self):
        lifecycle = self._limit_lifecycle()
        result = bind_spot_event_to_core(
            self._marked_state(), self.config, lifecycle,
            self._event(lifecycle, status="FILLED", last="1", cumulative="1"),
            fee="0.1", fee_asset="USDT", core_role="BASE",
        )

        self.assertEqual(result.outcome, CoreBindingOutcome.ACCEPTED)
        self.assertEqual(
            [event["type"] for event in result.core_events],
            ["INTENT", "FILL", "ORDER_FINAL"],
        )
        self.assertTrue(result.core_state.orders["order-1"].complete)
        self.assertEqual(result.core_state.anchor, 100)

    def test_canceled_event_with_last_fill_closes_only_remaining_quantity(self):
        lifecycle = self._limit_lifecycle()
        result = bind_spot_event_to_core(
            self._marked_state(), self.config, lifecycle,
            self._event(lifecycle, status="CANCELED", last="0.4", cumulative="0.4"),
            fee="0.04", fee_asset="USDT", core_role="BASE",
        )

        order = result.core_state.orders["order-1"]
        self.assertEqual(result.outcome, CoreBindingOutcome.ACCEPTED)
        self.assertEqual([event["type"] for event in result.core_events], ["INTENT", "FILL", "ORDER_FINAL"])
        self.assertEqual((order.status, order.leaves, order.canceled), ("CANCELED", F(0), F(3, 5)))

    def test_missing_fee_does_not_advance_either_projection(self):
        lifecycle = self._limit_lifecycle()
        state = self._marked_state()
        result = bind_spot_event_to_core(
            state, self.config, lifecycle, self._event(lifecycle), fee_asset="USDT", core_role="BASE"
        )

        self.assertEqual(result.outcome, CoreBindingOutcome.CORE_BINDING_REJECTED)
        self.assertEqual(result.core_events, ())
        self.assertEqual(result.core_state, state)
        self.assertEqual(result.lifecycle, lifecycle)


if __name__ == "__main__":
    unittest.main()
