import importlib
import json
from fractions import Fraction as F
from pathlib import Path
import tempfile
import unittest

from dcabot.application.instrument_filters import InstrumentFilterProfile
from dcabot.application.spot_lifecycle_core_binding import CoreBindingOutcome
from dcabot.application.spot_order_lifecycle import (
    SpotSide,
    create_limit_order,
    new_lifecycle,
)
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply


class SpotBindingStoreTests(unittest.TestCase):
    def setUp(self):
        self.profile = InstrumentFilterProfile(
            profile_id="spot-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="10",
        )
        config_path = Path(__file__).resolve().parents[1] / "config/paper.json"
        self.config = Config.parse(json.loads(config_path.read_text(encoding="utf-8")))
        order = create_limit_order(
            self.profile,
            order_id="order-1",
            client_order_id="client-1",
            symbol="BTCUSDT",
            side=SpotSide.BUY,
            quantity="1",
            price="100",
        )
        self.lifecycle = new_lifecycle(order)
        self.core_state = apply(State(), {"type": "MARK", "price": "100"}, self.config)

    def _event(self, *, price="100"):
        return self.lifecycle.event(
            event_id="event-1",
            execution_id="execution-1",
            event_time_ms=100,
            status="PARTIALLY_FILLED",
            last_filled_qty="0.4",
            cumulative_filled_qty="0.4",
            last_price=price,
        )

    def _store_class(self):
        try:
            return importlib.import_module(
                "dcabot.persistence.spot_binding_store"
            ).SpotBindingStore
        except ModuleNotFoundError as exc:
            self.fail(f"SpotBindingStore implementation is missing: {exc}")

    def test_restart_replays_lifecycle_and_core_from_one_atomic_journal(self):
        store_class = self._store_class()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spot-bindings.sqlite"
            with store_class.create(
                path,
                config=self.config,
                lifecycle=self.lifecycle,
                core_state=self.core_state,
            ) as store:
                result = store.append(
                    self._event(), fee="0.04", fee_asset="USDT", core_role="BASE"
                )
                self.assertEqual(result.outcome, CoreBindingOutcome.ACCEPTED)

            with store_class.open(path, config=self.config) as reopened:
                replay = reopened.load()

            self.assertEqual(replay.lifecycle.order.filled_quantity, "0.4")
            self.assertEqual(replay.core_state.position.qty, F(2, 5))
            self.assertEqual(replay.accepted_event_count, 1)

    def test_duplicate_is_idempotent_and_conflict_does_not_change_replay(self):
        store_class = self._store_class()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spot-bindings.sqlite"
            with store_class.create(
                path,
                config=self.config,
                lifecycle=self.lifecycle,
                core_state=self.core_state,
            ) as store:
                event = self._event()
                store.append(event, fee="0.04", fee_asset="USDT", core_role="BASE")
                duplicate = store.append(
                    event, fee="0.04", fee_asset="USDT", core_role="BASE"
                )
                self.assertEqual(duplicate.outcome, CoreBindingOutcome.DUPLICATE)
                with self.assertRaisesRegex(ValueError, "SPOT_BINDING_EVENT_CONFLICT"):
                    store.append(
                        self._event(price="99.5"),
                        fee="0.04",
                        fee_asset="USDT",
                        core_role="BASE",
                    )
                self.assertEqual(store.load().accepted_event_count, 1)

    def test_rejected_binding_publishes_neither_projection(self):
        store_class = self._store_class()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spot-bindings.sqlite"
            with store_class.create(
                path,
                config=self.config,
                lifecycle=self.lifecycle,
                core_state=self.core_state,
            ) as store:
                result = store.append(
                    self._event(), fee_asset="USDT", core_role="BASE"
                )
                self.assertEqual(result.outcome, CoreBindingOutcome.CORE_BINDING_REJECTED)
                replay = store.load()

            self.assertEqual(replay.lifecycle, self.lifecycle)
            self.assertEqual(replay.core_state, self.core_state)
            self.assertEqual(replay.accepted_event_count, 0)


if __name__ == "__main__":
    unittest.main()
