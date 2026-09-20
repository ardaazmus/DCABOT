import sqlite3
import tempfile
import unittest
from pathlib import Path

from dcabot.application.order_list_contract import (
    OrderListError,
    OrderListLegIdentity,
    OrderListLegRole,
    OrderListLegStatus,
    OrderListObservation,
    OrderListObservationOutcome,
    create_oco_identity,
)
from dcabot.persistence.order_list_store import OrderListStore, OrderListStoreError


class OrderListStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "oco.sqlite3"
        self.identity = create_oco_identity(
            order_list_id=7,
            list_client_order_id="list-7",
            symbol="BTCUSDT",
            working=OrderListLegIdentity("working-7", 70, "working-client-7", OrderListLegRole.WORKING, "LIMIT_MAKER"),
            pending=OrderListLegIdentity("pending-7", 71, "pending-client-7", OrderListLegRole.PENDING, "STOP_LOSS_LIMIT"),
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def observation(self, *, event_id="event-1", status="EXEC_STARTED", at=100, legs=None):
        return OrderListObservation(
            event_id=event_id,
            order_list_id=7,
            list_client_order_id="list-7",
            list_status=status,
            list_order_status="EXECUTING" if status != "ALL_DONE" else "ALL_DONE",
            leg_statuses=legs or ("NEW", "PENDING_NEW"),
            observed_at_ms=at,
        )

    def test_create_restart_replays_exact_projection_and_duplicate_is_idempotent(self):
        first = self.observation()
        with OrderListStore.create(self.path, self.identity, first) as store:
            self.assertEqual(store.append(self.observation(event_id="event-2", status="EXECUTING", at=101)), OrderListObservationOutcome.ACCEPTED)
            self.assertEqual(store.append(self.observation(event_id="event-2", status="EXECUTING", at=101)), OrderListObservationOutcome.DUPLICATE)
            expected = store.load()
        with OrderListStore.open(self.path) as reopened:
            self.assertEqual(reopened.load(), expected)

    def test_atomic_insert_failure_leaves_no_partial_observation(self):
        with OrderListStore.create(self.path, self.identity, self.observation()) as store:
            store.db.execute(
                "CREATE TRIGGER reject_order_list_observation BEFORE INSERT ON order_list_observations "
                "WHEN NEW.sequence=2 BEGIN SELECT RAISE(ABORT, 'injected observation failure'); END"
            )
            with self.assertRaisesRegex(sqlite3.IntegrityError, "injected observation failure"):
                store.append(self.observation(event_id="event-2", status="EXECUTING", at=101))
            self.assertEqual(len(store.load().observations), 1)

    def test_conflict_and_out_of_order_do_not_change_durable_replay(self):
        with OrderListStore.create(self.path, self.identity, self.observation()) as store:
            with self.assertRaisesRegex(OrderListStoreError, "ORDER_LIST_EVENT_CONFLICT"):
                store.append(self.observation(event_id="event-1", at=101))
            with self.assertRaisesRegex(OrderListError, "ORDER_LIST_EVENT_OUT_OF_ORDER"):
                store.append(self.observation(event_id="event-0", at=99))
            self.assertEqual(len(store.load().observations), 1)

    def test_checksum_corruption_fails_closed_on_restart(self):
        with OrderListStore.create(self.path, self.identity, self.observation()):
            db = sqlite3.connect(self.path)
            db.execute("UPDATE order_list_observations SET observation_payload='{}'")
            db.commit()
            db.close()
        with self.assertRaisesRegex(OrderListStoreError, "ORDER_LIST_RECORD_CORRUPT"):
            OrderListStore.open(self.path)


if __name__ == "__main__":
    unittest.main()
