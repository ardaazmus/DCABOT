import importlib
import unittest

from dcabot.application.reconciliation import OrderLookup, UserDataEvent


class VenueEventBindingTests(unittest.TestCase):
    def _evaluate(self):
        try:
            module = importlib.import_module("dcabot.application.venue_event_binding")
        except ModuleNotFoundError:
            self.fail("Venue event evidence contract implementation is missing")
        evaluate = getattr(module, "evaluate_venue_event_lookup", None)
        if evaluate is None:
            self.fail("Venue event evidence contract implementation is missing")
        return evaluate

    def test_exact_lookup_match_produces_redacted_match_evidence(self):
        evaluate = self._evaluate()
        event = UserDataEvent.create("stream-1", 100, "executionReport", 777)

        evidence = evaluate(event, OrderLookup.found(777))

        self.assertEqual(evidence.event_id, "stream-1")
        self.assertEqual(evidence.event_venue_order_id, 777)
        self.assertEqual(evidence.lookup_venue_order_id, 777)
        self.assertEqual(evidence.outcome.value, "MATCHED")
        self.assertFalse(hasattr(evidence, "raw_payload"))

    def test_mismatch_is_conflict_and_missing_lookup_is_unresolved(self):
        evaluate = self._evaluate()
        event = UserDataEvent.create("stream-1", 100, "executionReport", 777)

        conflict = evaluate(event, OrderLookup.found(778))
        unresolved = evaluate(event, OrderLookup.not_found())

        self.assertEqual(conflict.outcome.value, "CONFLICT")
        self.assertEqual(unresolved.outcome.value, "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
