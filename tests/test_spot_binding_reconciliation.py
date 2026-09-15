import json
from pathlib import Path
import tempfile
import unittest

from dcabot.application.reconciliation import (
    ConnectionState,
    EventDecision,
    ReconciliationCoordinator,
    UserDataEvent,
)
from dcabot.application.instrument_filters import InstrumentFilterProfile
from dcabot.application.spot_order_lifecycle import (
    SpotSide,
    create_limit_order,
    new_lifecycle,
)
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply
from dcabot.persistence.spot_binding_store import SpotBindingStore


class SpotBindingReconciliationTests(unittest.TestCase):
    def setUp(self):
        profile = InstrumentFilterProfile(
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

    def _spot_event(self):
        return self.lifecycle.event(
            event_id="event-1",
            execution_id="execution-1",
            event_time_ms=100,
            status="PARTIALLY_FILLED",
            last_filled_qty="0.4",
            cumulative_filled_qty="0.4",
            last_price="100",
        )

    def _observation(self, *, binding_event_id="event-1", event_id="stream-1"):
        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()
        event = UserDataEvent.create(event_id, 100, "executionReport", 1)
        decision = coordinator.accept_event(event)
        self.assertEqual(decision, EventDecision.ACCEPTED)
        return self._observation_type(event, decision, coordinator.state, binding_event_id)

    @staticmethod
    def _observation_type(event, decision, state, binding_event_id):
        module = __import__(
            "dcabot.persistence.spot_binding_store",
            fromlist=["DurableReconciliationObservation"],
        )
        observation_type = getattr(module, "DurableReconciliationObservation", None)
        if observation_type is None:
            raise AssertionError("DurableReconciliationObservation implementation is missing")
        return observation_type(event, decision, state, binding_event_id)

    def test_atomic_binding_and_reconciliation_survive_restart_without_raw_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spot-bindings.sqlite"
            observation = self._observation()
            with SpotBindingStore.create(
                path,
                config=self.config,
                lifecycle=self.lifecycle,
                core_state=self.core_state,
            ) as store:
                result = store.append(
                    self._spot_event(),
                    fee="0.04",
                    fee_asset="USDT",
                    core_role="BASE",
                    reconciliation=observation,
                )
                self.assertEqual(result.outcome.value, "ACCEPTED")

            with SpotBindingStore.open(path, config=self.config) as reopened:
                self.assertEqual(reopened.load_reconciliation(), (observation,))
                raw_columns = {
                    row[1]
                    for row in reopened.db.execute("PRAGMA table_info(reconciliation_events)")
                }
                self.assertNotIn("raw_payload", raw_columns)

    def test_reconciliation_duplicate_and_conflict_leave_journal_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spot-bindings.sqlite"
            with SpotBindingStore.create(
                path,
                config=self.config,
                lifecycle=self.lifecycle,
                core_state=self.core_state,
            ) as store:
                observation = self._observation()
                self.assertEqual(store.record_reconciliation(observation).value, "ACCEPTED")
                self.assertEqual(store.record_reconciliation(observation).value, "DUPLICATE")
                conflict = type(observation)(
                    type(observation.event)(
                        observation.event.event_id,
                        observation.event.event_time_ms,
                        observation.event.event_type,
                        2,
                        "0" * 64,
                    ),
                    observation.decision,
                    observation.state,
                    observation.binding_event_id,
                )
                with self.assertRaisesRegex(ValueError, "SPOT_RECONCILIATION_EVENT_CONFLICT"):
                    store.record_reconciliation(conflict)
                self.assertEqual(store.load_reconciliation(), (observation,))

    def test_non_synced_observation_is_replayed_as_observed_without_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spot-bindings.sqlite"
            with SpotBindingStore.create(
                path,
                config=self.config,
                lifecycle=self.lifecycle,
                core_state=self.core_state,
            ) as store:
                observation = self._observation()
                observation = type(observation)(
                    observation.event,
                    EventDecision.QUARANTINED,
                    ConnectionState.GAP,
                    observation.binding_event_id,
                )
                store.record_reconciliation(observation)
                self.assertEqual(store.load_reconciliation(), (observation,))
            with SpotBindingStore.open(path, config=self.config) as reopened:
                self.assertEqual(reopened.load_reconciliation()[0].state, ConnectionState.GAP)

    def test_reconciliation_conflict_rolls_back_the_core_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spot-bindings.sqlite"
            with SpotBindingStore.create(
                path,
                config=self.config,
                lifecycle=self.lifecycle,
                core_state=self.core_state,
            ) as store:
                prior = self._observation(binding_event_id=None)
                store.record_reconciliation(prior)
                linked = self._observation()
                with self.assertRaisesRegex(ValueError, "SPOT_RECONCILIATION_EVENT_CONFLICT"):
                    store.append(
                        self._spot_event(),
                        fee="0.04",
                        fee_asset="USDT",
                        core_role="BASE",
                        reconciliation=linked,
                    )
                self.assertEqual(store.load().accepted_event_count, 0)
                self.assertEqual(store.load_reconciliation(), (prior,))


if __name__ == "__main__":
    unittest.main()
