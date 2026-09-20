import importlib
import unittest

from dcabot.application.reconciliation import OrderLookup, UserDataEvent
from dcabot.application.spot_order_lifecycle import SpotOrderEvent


class VenueSpotEventMappingTests(unittest.TestCase):
    def _builder(self):
        try:
            module = importlib.import_module("dcabot.application.venue_spot_event_mapping")
        except ModuleNotFoundError:
            self.fail("Venue-to-Spot event mapping contract implementation is missing")
        builder = getattr(module, "build_spot_event_mapping_candidate", None)
        if builder is None:
            self.fail("Venue-to-Spot event mapping contract implementation is missing")
        return builder

    def _evidence(self, lookup):
        from dcabot.application.venue_event_binding import evaluate_venue_event_lookup

        return evaluate_venue_event_lookup(
            UserDataEvent.create("stream-1", 100, "executionReport", 777), lookup
        )

    def _spot_event(self):
        return SpotOrderEvent(
            order_id="order-1",
            event_id="spot-event-1",
            execution_id="execution-1",
            event_time_ms=100,
            status="PARTIALLY_FILLED",
            last_filled_qty="0.4",
            cumulative_filled_qty="0.4",
            last_price="100",
        )

    def test_matched_evidence_creates_explicit_candidate_without_economic_fields(self):
        candidate = self._builder()(self._evidence(OrderLookup.found(777)), self._spot_event())

        self.assertEqual(candidate.venue_event_id, "stream-1")
        self.assertEqual(candidate.venue_order_id, 777)
        self.assertEqual(candidate.spot_event_id, "spot-event-1")
        self.assertEqual(candidate.spot_order_id, "order-1")
        self.assertEqual(candidate.execution_id, "execution-1")
        self.assertEqual(candidate.status.value, "CANDIDATE")
        self.assertFalse(hasattr(candidate, "qty"))
        self.assertFalse(hasattr(candidate, "price"))
        self.assertFalse(hasattr(candidate, "fee"))

    def test_unresolved_or_conflicting_evidence_cannot_create_mapping_candidate(self):
        builder = self._builder()

        with self.assertRaisesRegex(ValueError, "VENUE_SPOT_MAPPING_REQUIRES_MATCH"):
            builder(self._evidence(OrderLookup.not_found()), self._spot_event())
        with self.assertRaisesRegex(ValueError, "VENUE_SPOT_MAPPING_REQUIRES_MATCH"):
            builder(self._evidence(OrderLookup.found(778)), self._spot_event())


if __name__ == "__main__":
    unittest.main()
