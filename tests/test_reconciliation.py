import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dcabot.application.order_attempt import AttemptOperation, AttemptState, OrderAttempt, request_fingerprint
from dcabot.application.reconciliation import (
    ConnectionState,
    EventDecision,
    OrderLookup,
    ReconciliationCoordinator,
    ReconciliationError,
    UserDataEvent,
)
from dcabot.persistence.attempt_store import AttemptStore


def attempt() -> OrderAttempt:
    return OrderAttempt(
        attempt_id="attempt-1",
        run_id="run-1",
        venue="BINANCE_SPOT_TESTNET",
        operation=AttemptOperation.PLACE_ORDER,
        symbol="BTCUSDT",
        client_order_id="client-1",
        request_fingerprint_sha256=request_fingerprint({"symbol": "BTCUSDT"}),
        capability_snapshot_hash="a" * 64,
        filter_snapshot_hash="b" * 64,
        state=AttemptState.PREPARED,
        created_at_us=1_700_000_000_000_000,
        last_transition_at_us=1_700_000_000_000_000,
    )


class FakeRest:
    def __init__(self, lookup: OrderLookup):
        self.lookup = lookup

    def find_order(self, _attempt: OrderAttempt) -> OrderLookup:
        return self.lookup


class ReconciliationTests(unittest.TestCase):
    def test_restart_quarantines_send_and_blocks_sync_until_rest_reconciliation(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                store.prepare(attempt())
                store.persist("attempt-1", now_us=1_700_000_000_000_001)
                store.mark_sending("attempt-1", now_us=1_700_000_000_000_002)
                coordinator = ReconciliationCoordinator(store)

                recovered = coordinator.startup(now_us=1_700_000_000_000_003)

                self.assertEqual(coordinator.state, ConnectionState.RECONCILIATION_REQUIRED)
                self.assertEqual(recovered[0].state, AttemptState.UNKNOWN)
                with self.assertRaisesRegex(ReconciliationError, "UNRESOLVED_ATTEMPTS"):
                    coordinator.mark_synced(authoritative_snapshot=True)

    def test_found_order_resolves_unknown_without_claiming_fill(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                store.prepare(attempt())
                store.persist("attempt-1", now_us=1_700_000_000_000_001)
                store.mark_sending("attempt-1", now_us=1_700_000_000_000_002)
                coordinator = ReconciliationCoordinator(store)
                coordinator.startup(now_us=1_700_000_000_000_003)

                resolved = coordinator.reconcile_attempt(
                    "attempt-1",
                    FakeRest(OrderLookup.found(777)),
                    now_us=1_700_000_000_000_004,
                )

                self.assertEqual(resolved.state, AttemptState.ACKNOWLEDGED)
                self.assertEqual(resolved.venue_order_id, 777)
                self.assertIsNone(resolved.venue_event_time_ms)
                self.assertEqual(coordinator.mark_synced(authoritative_snapshot=True), ConnectionState.SYNCED)

    def test_missing_order_remains_unresolved_and_never_becomes_rejected(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                store.prepare(attempt())
                store.persist("attempt-1", now_us=1_700_000_000_000_001)
                store.mark_sending("attempt-1", now_us=1_700_000_000_000_002)
                coordinator = ReconciliationCoordinator(store)
                coordinator.startup(now_us=1_700_000_000_000_003)

                unresolved = coordinator.reconcile_attempt(
                    "attempt-1",
                    FakeRest(OrderLookup.not_found()),
                    now_us=1_700_000_000_000_004,
                )

                self.assertEqual(unresolved.state, AttemptState.UNRESOLVED)
                with self.assertRaisesRegex(ReconciliationError, "UNRESOLVED_ATTEMPTS"):
                    coordinator.mark_synced(authoritative_snapshot=True)

    def test_reconnect_requires_reconciliation_and_does_not_imply_synced(self):
        coordinator = ReconciliationCoordinator()

        coordinator.begin_connect()
        coordinator.public_snapshot_ready()
        self.assertEqual(coordinator.state, ConnectionState.CONNECTED_READ_ONLY)
        coordinator.on_disconnect()
        self.assertEqual(coordinator.state, ConnectionState.STALE)
        coordinator.reconnect()

        self.assertEqual(coordinator.state, ConnectionState.RECONCILIATION_REQUIRED)
        with self.assertRaisesRegex(ReconciliationError, "AUTHORITATIVE_SNAPSHOT_REQUIRED"):
            coordinator.mark_synced(authoritative_snapshot=False)

    def test_duplicate_is_idempotent_but_out_of_order_event_opens_gap(self):
        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()
        first = UserDataEvent.create("event-1", 100, "executionReport", 1)
        duplicate = UserDataEvent.create("event-1", 100, "executionReport", 1)
        older = UserDataEvent.create("event-2", 99, "executionReport", 1)

        self.assertEqual(coordinator.accept_event(first), EventDecision.ACCEPTED)
        self.assertEqual(coordinator.accept_event(duplicate), EventDecision.DUPLICATE)
        self.assertEqual(coordinator.accept_event(older), EventDecision.OUT_OF_ORDER)
        self.assertEqual(coordinator.state, ConnectionState.GAP)

    def test_same_event_id_with_different_payload_is_quarantined(self):
        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()
        first = UserDataEvent.create("event-1", 100, "executionReport", 1)
        conflict = UserDataEvent(
            event_id="event-1",
            event_time_ms=100,
            event_type="executionReport",
            venue_order_id=2,
            payload_fingerprint=hashlib.sha256(b"different").hexdigest(),
        )

        coordinator.accept_event(first)
        self.assertEqual(coordinator.accept_event(conflict), EventDecision.CONFLICT)
        self.assertEqual(coordinator.state, ConnectionState.GAP)

    def test_rest_and_stream_disagreement_opens_gap(self):
        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()
        event = UserDataEvent.create("event-1", 100, "executionReport", 777)
        coordinator.accept_event(event)

        self.assertEqual(
            coordinator.compare_event_with_lookup(event, OrderLookup.found(888)),
            EventDecision.CONFLICT,
        )
        self.assertEqual(coordinator.state, ConnectionState.GAP)

    def test_snapshot_at_freshness_boundary_becomes_stale(self):
        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()

        self.assertEqual(
            coordinator.apply_freshness(observed_at_ms=1_000, now_ms=1_100, max_age_ms=100),
            ConnectionState.STALE,
        )

    def test_reset_requires_new_authoritative_snapshot_before_sync(self):
        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()
        coordinator.accept_event(UserDataEvent.create("event-1", 100, "executionReport", 777))
        coordinator.testnet_reset_detected()

        with self.assertRaisesRegex(ReconciliationError, "RESET_REVALIDATION_REQUIRED"):
            coordinator.mark_synced(authoritative_snapshot=True)
        coordinator.revalidate_after_reset(authoritative_snapshot=True)
        self.assertEqual(coordinator.mark_synced(authoritative_snapshot=True), ConnectionState.SYNCED)

    def test_gap_quarantines_following_events_until_reconnect_reconciliation(self):
        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()
        coordinator.accept_event(UserDataEvent.create("event-1", 100, "executionReport", 777))
        coordinator.accept_event(UserDataEvent.create("event-2", 99, "executionReport", 777))

        self.assertEqual(
            coordinator.accept_event(UserDataEvent.create("event-3", 101, "executionReport", 777)),
            EventDecision.QUARANTINED,
        )


if __name__ == "__main__":
    unittest.main()
