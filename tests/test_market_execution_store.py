import sqlite3
from tempfile import TemporaryDirectory
import unittest
from pathlib import Path

from dcabot.application.market_base_quantity import (
    MarketExecutionOutcome,
    MarketExecutionStatus,
    create_market_base_execution,
)
from dcabot.application.market_execution_reconciliation import (
    MarketExecutionReconciliationBinding,
)
from dcabot.persistence.market_execution_store import (
    MarketExecutionStore,
    MarketExecutionStoreError,
)


class MarketExecutionStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "market.sqlite3"
        self.execution = create_market_base_execution(
            order_id="order-1",
            symbol="BTCUSDT",
            side="BUY",
            requested_quantity="1",
            reference_price="100",
            max_slippage_bps=200,
        )
        accepted = self.execution.apply_fill(
            execution_id="execution-1",
            base_quantity="0.5",
            quote_quantity="50",
            fee="0.05",
            fee_asset="USDT",
        )
        self.filled_execution = accepted.execution
        self.binding = MarketExecutionReconciliationBinding(
            venue_event_id="stream-1",
            venue_order_id=777,
            spot_event_id="spot-event-1",
            spot_order_id="order-1",
            market_order_id="order-1",
            execution_id="execution-1",
            fill=self.filled_execution.fills[0],
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def test_replays_exact_market_state_and_redacted_binding_without_core(self):
        with MarketExecutionStore.create(self.path, self.execution) as store:
            self.assertEqual(store.save(self.filled_execution, self.binding), MarketExecutionOutcome.ACCEPTED)
            replay = store.load()

        with MarketExecutionStore.open(self.path) as store:
            reopened = store.load()

        self.assertEqual(reopened, replay)
        self.assertEqual(reopened.execution, self.filled_execution)
        self.assertEqual(reopened.bindings, (self.binding,))
        self.assertFalse(hasattr(reopened, "core_state"))

    def test_duplicate_is_idempotent_and_conflict_does_not_change_state(self):
        with MarketExecutionStore.create(self.path, self.execution) as store:
            self.assertEqual(store.save(self.filled_execution, self.binding), MarketExecutionOutcome.ACCEPTED)
            self.assertEqual(store.save(self.filled_execution, self.binding), MarketExecutionOutcome.DUPLICATE)

            conflict = MarketExecutionReconciliationBinding(
                "stream-1", 778, "spot-event-2", "order-1", "order-1", "execution-1", self.binding.fill
            )
            with self.assertRaisesRegex(MarketExecutionStoreError, "MARKET_STORE_BINDING_CONFLICT"):
                store.save(self.filled_execution, conflict)

            self.assertEqual(store.load().bindings, (self.binding,))

    def test_failed_binding_rolls_back_execution_state(self):
        with MarketExecutionStore.create(self.path, self.execution) as store:
            invalid = MarketExecutionReconciliationBinding(
                "stream-1", 777, "spot-event-1", "different-order", "order-1", "execution-1", self.binding.fill
            )
            with self.assertRaisesRegex(MarketExecutionStoreError, "MARKET_STORE_BINDING_INVALID"):
                store.save(self.filled_execution, invalid)

            replay = store.load()
            self.assertEqual(replay.execution, self.execution)
            self.assertEqual(replay.bindings, ())

    def test_terminal_state_is_durable(self):
        canceled = self.filled_execution.close(MarketExecutionStatus.CANCELED)
        with MarketExecutionStore.create(self.path, self.execution) as store:
            self.assertEqual(store.save(self.filled_execution, self.binding), MarketExecutionOutcome.ACCEPTED)
            self.assertEqual(store.save(canceled), MarketExecutionOutcome.ACCEPTED)
            self.assertEqual(store.load().execution, canceled)

    def test_tampered_state_checksum_fails_closed(self):
        with MarketExecutionStore.create(self.path, self.execution):
            pass
        db = sqlite3.connect(self.path)
        db.execute("UPDATE market_execution_state SET state_payload=?", ("{}",))
        db.commit()
        db.close()

        with self.assertRaisesRegex(MarketExecutionStoreError, "MARKET_STORE_RECORD_CORRUPT"):
            MarketExecutionStore.open(self.path)


if __name__ == "__main__":
    unittest.main()
