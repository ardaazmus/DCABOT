import sqlite3
from dataclasses import replace
from tempfile import TemporaryDirectory
import unittest
from pathlib import Path

from dcabot.application.conditional_execution import (
    ConditionalExecutionOutcome,
    create_conditional_execution,
)
from dcabot.persistence.conditional_execution_store import (
    ConditionalExecutionStore,
    ConditionalExecutionStoreError,
)


class ConditionalExecutionStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "conditional.sqlite3"
        self.armed = create_conditional_execution(
            conditional_order_id="conditional-1",
            symbol="BTCUSDT",
            side="SELL",
            trigger_kind="STOP_PRICE",
            trigger_price="95",
        )
        self.triggered = self.armed.observe_trigger(
            trigger_event_id="trigger-event-1",
            observed_at_ms=100,
            observed_price="94.5",
        ).execution
        self.execution = self.triggered.bind_execution(
            execution_order_id="execution-order-1",
            execution_order_type="MARKET",
            execution_event_id="execution-event-1",
            observed_at_ms=101,
        ).execution

    def tearDown(self):
        self.tempdir.cleanup()

    def test_restart_replays_exact_conditional_identity_without_core_or_fill(self):
        with ConditionalExecutionStore.create(self.path, self.armed) as store:
            self.assertEqual(store.save(self.triggered), ConditionalExecutionOutcome.ACCEPTED)
            self.assertEqual(store.save(self.execution), ConditionalExecutionOutcome.ACCEPTED)
            replay = store.load()

        with ConditionalExecutionStore.open(self.path) as store:
            reopened = store.load()

        self.assertEqual(reopened, replay)
        self.assertEqual(reopened, self.execution)
        self.assertFalse(hasattr(reopened, "core_state"))
        self.assertFalse(hasattr(reopened, "fills"))

    def test_exact_retry_is_duplicate_and_state_conflict_is_rejected(self):
        with ConditionalExecutionStore.create(self.path, self.armed) as store:
            self.assertEqual(store.save(self.triggered), ConditionalExecutionOutcome.ACCEPTED)
            self.assertEqual(store.save(self.execution), ConditionalExecutionOutcome.ACCEPTED)
            self.assertEqual(store.save(self.execution), ConditionalExecutionOutcome.DUPLICATE)

            different = replace(self.execution, symbol="ETHUSDT")
            with self.assertRaisesRegex(ConditionalExecutionStoreError, "CONDITIONAL_STORE_STATE_CONFLICT"):
                store.save(different)
            self.assertEqual(store.load(), self.execution)

    def test_tampered_state_checksum_fails_closed(self):
        with ConditionalExecutionStore.create(self.path, self.armed):
            pass
        db = sqlite3.connect(self.path)
        db.execute("UPDATE conditional_execution_state SET state_payload=?", ("{}",))
        db.commit()
        db.close()

        with self.assertRaisesRegex(ConditionalExecutionStoreError, "CONDITIONAL_STORE_RECORD_CORRUPT"):
            ConditionalExecutionStore.open(self.path)


if __name__ == "__main__":
    unittest.main()
