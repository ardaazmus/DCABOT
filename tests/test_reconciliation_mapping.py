import json
from pathlib import Path
import tempfile
import unittest

from dcabot.application.reconciliation import (
    ConnectionState,
    EventDecision,
    OrderLookup,
    UserDataEvent,
)
from dcabot.application.venue_event_binding import evaluate_venue_event_lookup
from dcabot.application.venue_spot_event_mapping import build_spot_event_mapping_candidate
from dcabot.application.spot_order_lifecycle import (
    SpotSide,
    create_limit_order,
    new_lifecycle,
)
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply
from dcabot.persistence.reconciliation_journal import DurableReconciliationObservation
from dcabot.persistence.spot_binding_store import SpotBindingStore


class ReconciliationMappingTests(unittest.TestCase):
    def setUp(self):
        profile = __import__(
            "dcabot.application.instrument_filters",
            fromlist=["InstrumentFilterProfile"],
        ).InstrumentFilterProfile(
            profile_id="spot-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="10",
        )
        config_path = Path(__file__).resolve().parents[1] / "config/paper.json"
        self.config = Config.parse(json.loads(config_path.read_text(encoding="utf-8")))
        order = create_limit_order(
            profile,
            order_id="order-1",
            client_order_id="client-1",
            symbol="BTCUSDT",
            side=SpotSide.BUY,
            quantity="1",
            price="100",
        )
        self.lifecycle = new_lifecycle(order)
        self.core_state = apply(State(), {"type": "MARK", "price": "100"}, self.config)

    def _candidate(self):
        evidence = evaluate_venue_event_lookup(
            UserDataEvent.create("stream-1", 100, "executionReport", 777),
            OrderLookup.found(777),
        )
        spot_event = self.lifecycle.event(
            event_id="spot-event-1",
            execution_id="execution-1",
            event_time_ms=100,
            status="PARTIALLY_FILLED",
            last_filled_qty="0.4",
            cumulative_filled_qty="0.4",
            last_price="100",
        )
        return build_spot_event_mapping_candidate(evidence, spot_event)

    def _observation(self, candidate, lookup=None, binding_event_id=None):
        return DurableReconciliationObservation(
            UserDataEvent.create(candidate.venue_event_id, 100, "executionReport", candidate.venue_order_id),
            EventDecision.ACCEPTED,
            ConnectionState.CONNECTED_READ_ONLY,
            binding_event_id,
            lookup or OrderLookup.found(candidate.venue_order_id),
        )

    def test_matched_evidence_and_mapping_replay_atomically_without_core_promotion(self):
        candidate = self._candidate()
        observation = self._observation(candidate)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spot-bindings.sqlite"
            with SpotBindingStore.create(
                path,
                config=self.config,
                lifecycle=self.lifecycle,
                core_state=self.core_state,
            ) as store:
                self.assertEqual(
                    store.record_mapping_with_evidence(candidate, observation).value,
                    "ACCEPTED",
                )
                self.assertEqual(store.load_reconciliation(), (observation,))
                self.assertEqual(store.load_mappings(), (candidate,))
                replay = store.load()
                self.assertEqual(replay.core_state, self.core_state)
                self.assertEqual(replay.accepted_event_count, 0)
            with SpotBindingStore.open(path, config=self.config) as reopened:
                self.assertEqual(reopened.load_reconciliation(), (observation,))
                self.assertEqual(reopened.load_mappings(), (candidate,))

    def test_invalid_matched_link_rolls_back_both_records(self):
        candidate = self._candidate()
        observation = self._observation(candidate, OrderLookup.found(778))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spot-bindings.sqlite"
            with SpotBindingStore.create(
                path,
                config=self.config,
                lifecycle=self.lifecycle,
                core_state=self.core_state,
            ) as store:
                with self.assertRaisesRegex(
                    ValueError, "SPOT_RECONCILIATION_MAPPING_LINK_INVALID"
                ):
                    store.record_mapping_with_evidence(candidate, observation)
                self.assertEqual(store.load_reconciliation(), ())
                self.assertEqual(store.load_mappings(), ())

    def test_verified_mapping_admits_existing_spot_event_to_core(self):
        candidate = self._candidate()
        observation = self._observation(candidate)
        spot_event = self.lifecycle.event(
            event_id=candidate.spot_event_id,
            execution_id=candidate.execution_id,
            event_time_ms=100,
            status="PARTIALLY_FILLED",
            last_filled_qty="0.4",
            cumulative_filled_qty="0.4",
            last_price="100",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spot-bindings.sqlite"
            with SpotBindingStore.create(
                path,
                config=self.config,
                lifecycle=self.lifecycle,
                core_state=self.core_state,
            ) as store:
                store.record_mapping_with_evidence(candidate, observation)
                result = store.append_verified_mapping(
                    candidate,
                    observation,
                    spot_event,
                    fee="0.04",
                    fee_asset="USDT",
                    core_role="BASE",
                )
                self.assertEqual(result.outcome.value, "ACCEPTED")
                self.assertEqual(store.load().accepted_event_count, 1)
                self.assertEqual(store.load_mappings(), (candidate,))
                self.assertEqual(store.load_reconciliation(), (observation,))

    def test_verified_mapping_requires_durable_candidate_before_core_admission(self):
        candidate = self._candidate()
        observation = self._observation(candidate)
        spot_event = self.lifecycle.event(
            event_id=candidate.spot_event_id,
            execution_id=candidate.execution_id,
            event_time_ms=100,
            status="PARTIALLY_FILLED",
            last_filled_qty="0.4",
            cumulative_filled_qty="0.4",
            last_price="100",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spot-bindings.sqlite"
            with SpotBindingStore.create(
                path,
                config=self.config,
                lifecycle=self.lifecycle,
                core_state=self.core_state,
            ) as store:
                with self.assertRaisesRegex(
                    ValueError, "SPOT_RECONCILIATION_MAPPING_NOT_DURABLE"
                ):
                    store.append_verified_mapping(candidate, observation, spot_event)
                self.assertEqual(store.load().accepted_event_count, 0)

    def test_verified_mapping_rejects_nonaccepted_stream_decision(self):
        candidate = self._candidate()
        observation = DurableReconciliationObservation(
            self._observation(candidate).event,
            EventDecision.CONFLICT,
            ConnectionState.GAP,
            None,
            OrderLookup.found(candidate.venue_order_id),
        )
        spot_event = self.lifecycle.event(
            event_id=candidate.spot_event_id,
            execution_id=candidate.execution_id,
            event_time_ms=100,
            status="PARTIALLY_FILLED",
            last_filled_qty="0.4",
            cumulative_filled_qty="0.4",
            last_price="100",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spot-bindings.sqlite"
            with SpotBindingStore.create(
                path,
                config=self.config,
                lifecycle=self.lifecycle,
                core_state=self.core_state,
            ) as store:
                store.record_mapping_with_evidence(candidate, observation)
                with self.assertRaisesRegex(
                    ValueError, "SPOT_RECONCILIATION_MAPPING_ADMISSION_INVALID"
                ):
                    store.append_verified_mapping(candidate, observation, spot_event)
                self.assertEqual(store.load().accepted_event_count, 0)

    def test_mapping_candidate_replays_without_core_promotion(self):
        candidate = self._candidate()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spot-bindings.sqlite"
            with SpotBindingStore.create(
                path,
                config=self.config,
                lifecycle=self.lifecycle,
                core_state=self.core_state,
            ) as store:
                self.assertEqual(store.record_mapping(candidate).value, "ACCEPTED")
                self.assertEqual(store.load_mappings(), (candidate,))
                replay = store.load()
                self.assertEqual(replay.core_state, self.core_state)
                self.assertEqual(replay.accepted_event_count, 0)
            with SpotBindingStore.open(path, config=self.config) as reopened:
                self.assertEqual(reopened.load_mappings(), (candidate,))

    def test_mapping_identity_conflict_is_fail_closed(self):
        candidate = self._candidate()
        conflict = type(candidate)(
            candidate.venue_event_id,
            candidate.venue_order_id,
            "spot-event-2",
            candidate.spot_order_id,
            candidate.execution_id,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spot-bindings.sqlite"
            with SpotBindingStore.create(
                path,
                config=self.config,
                lifecycle=self.lifecycle,
                core_state=self.core_state,
            ) as store:
                self.assertEqual(store.record_mapping(candidate).value, "ACCEPTED")
                self.assertEqual(store.record_mapping(candidate).value, "DUPLICATE")
                with self.assertRaisesRegex(ValueError, "SPOT_RECONCILIATION_MAPPING_CONFLICT"):
                    store.record_mapping(conflict)
                self.assertEqual(store.load_mappings(), (candidate,))


if __name__ == "__main__":
    unittest.main()
