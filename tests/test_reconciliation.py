import hashlib
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dcabot.application.order_attempt import AttemptOperation, AttemptState, OrderAttempt, request_fingerprint
from dcabot.application.order_list_contract import (
    OrderListError,
    UserDataOrderListEvent,
    UserDataOrderListLeg,
    UserDataOrderListResyncAnchor,
)
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


def order_list_event(**overrides) -> UserDataOrderListEvent:
    values = {
        "event_id": "list-event-1",
        "event_time_ms": 100,
        "transaction_time_ms": 100,
        "symbol": "BTCUSDT",
        "order_list_id": 42,
        "contingency_type": "OCO",
        "list_status": "EXECUTING",
        "list_order_status": "EXECUTING",
        "list_client_order_id": "list-42",
        "orders": (
            UserDataOrderListLeg("BTCUSDT", 101, "working-101"),
            UserDataOrderListLeg("BTCUSDT", 102, "pending-102"),
        ),
    }
    values.update(overrides)
    return UserDataOrderListEvent(**values)


class FakeRest:
    def __init__(self, lookup: OrderLookup):
        self.lookup = lookup

    def find_order(self, _attempt: OrderAttempt) -> OrderLookup:
        return self.lookup


class RecordingRest:
    def __init__(self, lookups: dict[str, OrderLookup]):
        self.lookups = lookups
        self.attempt_ids: list[str] = []

    def find_order(self, attempt: OrderAttempt) -> OrderLookup:
        self.attempt_ids.append(attempt.attempt_id)
        return self.lookups[attempt.attempt_id]


class ReconciliationTests(unittest.TestCase):
    @staticmethod
    def _hydrate(coordinator, observations):
        hydrate = getattr(coordinator, "hydrate_event_continuity", None)
        if hydrate is None:
            raise AssertionError("hydrate_event_continuity implementation is missing")
        return hydrate(observations)

    @staticmethod
    def _snapshot(snapshot_id, observed_at_ms, event_cursor):
        module = __import__(
            "dcabot.application.reconciliation",
            fromlist=["AuthoritativeReconciliationSnapshot"],
        )
        snapshot_type = getattr(module, "AuthoritativeReconciliationSnapshot", None)
        if snapshot_type is None:
            raise AssertionError("AuthoritativeReconciliationSnapshot implementation is missing")
        return snapshot_type(snapshot_id, observed_at_ms, event_cursor, "a" * 64)

    @staticmethod
    def _apply_snapshot(coordinator, snapshot):
        apply_snapshot = getattr(coordinator, "apply_authoritative_snapshot", None)
        if apply_snapshot is None:
            raise AssertionError("apply_authoritative_snapshot implementation is missing")
        return apply_snapshot(snapshot)

    @staticmethod
    def _durable_start(coordinator, *, now_us, observations):
        start = getattr(coordinator, "startup_with_durable_recovery", None)
        if start is None:
            raise AssertionError("startup_with_durable_recovery implementation is missing")
        return start(now_us=now_us, continuity_observations=observations)

    @staticmethod
    def _reconcile_recovered(coordinator, recovered, query, *, now_us):
        reconcile = getattr(coordinator, "reconcile_recovered_attempts", None)
        if reconcile is None:
            raise AssertionError("reconcile_recovered_attempts implementation is missing")
        return reconcile(recovered, query, now_us=now_us)

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

    def test_list_status_duplicate_and_transaction_order_are_quarantined_without_source_sequence(self):
        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()
        first = order_list_event()
        duplicate = order_list_event()
        older = order_list_event(
            event_id="list-event-2",
            event_time_ms=101,
            transaction_time_ms=99,
        )

        self.assertEqual(coordinator.accept_order_list_event(first), EventDecision.ACCEPTED)
        self.assertEqual(coordinator.accept_order_list_event(duplicate), EventDecision.DUPLICATE)
        self.assertEqual(coordinator.accept_order_list_event(older), EventDecision.OUT_OF_ORDER)
        self.assertEqual(coordinator.state, ConnectionState.GAP)

    def test_list_status_reconnect_requires_explicit_reconciliation_before_acceptance(self):
        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()
        coordinator.accept_order_list_event(order_list_event())
        coordinator.on_disconnect()
        coordinator.reconnect()

        self.assertEqual(
            coordinator.accept_order_list_event(
                order_list_event(event_id="list-event-2", event_time_ms=101, transaction_time_ms=101)
            ),
            EventDecision.QUARANTINED,
        )

    def test_public_snapshot_does_not_bypass_list_status_reconciliation(self):
        coordinator = ReconciliationCoordinator()
        hydrated = order_list_event()
        forward = order_list_event(event_id="list-event-2", event_time_ms=101, transaction_time_ms=101)

        self.assertEqual(
            coordinator.hydrate_order_list_continuity((hydrated,)),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.public_snapshot_ready(),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(coordinator.accept_order_list_event(forward), EventDecision.QUARANTINED)

        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()
        self.assertEqual(coordinator.accept_order_list_event(hydrated), EventDecision.ACCEPTED)
        self.assertEqual(coordinator.reconnect(), ConnectionState.RECONCILIATION_REQUIRED)
        self.assertEqual(
            coordinator.public_snapshot_ready(),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(coordinator.accept_order_list_event(forward), EventDecision.QUARANTINED)

    def test_list_status_anchor_stays_quarantined_until_fresh_snapshot_after_public_callback(self):
        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()
        self.assertEqual(coordinator.accept_order_list_event(order_list_event()), EventDecision.ACCEPTED)
        coordinator.on_disconnect()
        self.assertEqual(coordinator.reconnect(), ConnectionState.RECONCILIATION_REQUIRED)
        self.assertEqual(
            coordinator.public_snapshot_ready(),
            ConnectionState.RECONCILIATION_REQUIRED,
        )

        anchor = UserDataOrderListResyncAnchor(
            anchor_id="resync-public-1",
            observed_at_ms=120,
            event=order_list_event(
                event_id="list-anchor-public-1",
                event_time_ms=120,
                transaction_time_ms=120,
            ),
        )
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(anchor),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.public_snapshot_ready(),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
            coordinator.apply_authoritative_snapshot(self._snapshot("snapshot-stale-public", 119, None))
        self.assertEqual(
            coordinator.public_snapshot_ready(),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        forward = order_list_event(
            event_id="list-event-public-2",
            event_time_ms=121,
            transaction_time_ms=121,
        )
        self.assertEqual(coordinator.accept_order_list_event(forward), EventDecision.QUARANTINED)
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(self._snapshot("snapshot-fresh-public", 120, None)),
            ConnectionState.SYNCED,
        )
        self.assertEqual(coordinator.accept_order_list_event(forward), EventDecision.ACCEPTED)

    def test_list_status_resync_anchor_stays_quarantined_until_authoritative_snapshot(self):
        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()
        coordinator.accept_order_list_event(order_list_event())
        self.assertEqual(
            coordinator.accept_order_list_event(
                order_list_event(event_id="list-event-2", event_time_ms=99, transaction_time_ms=99)
            ),
            EventDecision.OUT_OF_ORDER,
        )
        anchor = UserDataOrderListResyncAnchor(
            anchor_id="resync-1",
            observed_at_ms=120,
            event=order_list_event(event_id="list-anchor-1", event_time_ms=120, transaction_time_ms=120),
        )

        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(anchor),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.accept_order_list_event(
                order_list_event(event_id="list-event-3", event_time_ms=121, transaction_time_ms=121)
            ),
            EventDecision.QUARANTINED,
        )
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(self._snapshot("snapshot-1", 120, None)),
            ConnectionState.SYNCED,
        )
        self.assertEqual(
            coordinator.accept_order_list_event(
                order_list_event(event_id="list-event-4", event_time_ms=121, transaction_time_ms=121)
            ),
            EventDecision.ACCEPTED,
        )

    def test_list_status_reconnect_snapshot_requires_anchor_before_sync(self):
        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()
        coordinator.accept_order_list_event(order_list_event())
        coordinator.on_disconnect()
        coordinator.reconnect()

        with self.assertRaisesRegex(ReconciliationError, "ORDER_LIST_RESYNC_ANCHOR_REQUIRED"):
            coordinator.apply_authoritative_snapshot(self._snapshot("snapshot-1", 100, None))

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

    def test_restart_hydrates_durable_cursor_but_requires_authoritative_sync(self):
        coordinator = ReconciliationCoordinator()
        event = UserDataEvent.create("event-1", 100, "executionReport", 777)

        self._hydrate(
            coordinator,
            ((event, EventDecision.ACCEPTED, ConnectionState.SYNCED),)
        )

        self.assertEqual(coordinator.state, ConnectionState.RECONCILIATION_REQUIRED)
        with self.assertRaisesRegex(ReconciliationError, "AUTHORITATIVE_SNAPSHOT_REQUIRED"):
            coordinator.mark_synced(authoritative_snapshot=False)
        with self.assertRaisesRegex(ReconciliationError, "AUTHORITATIVE_SNAPSHOT_REQUIRED"):
            coordinator.mark_synced(authoritative_snapshot=True)
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(
                self._snapshot("snapshot-1", 101, event)
            ),
            ConnectionState.SYNCED,
        )
        self.assertEqual(
            coordinator.accept_event(UserDataEvent.create("event-2", 99, "executionReport", 777)),
            EventDecision.OUT_OF_ORDER,
        )

    def test_authoritative_snapshot_must_match_cursor_and_be_fresh(self):
        coordinator = ReconciliationCoordinator()
        event = UserDataEvent.create("event-1", 100, "executionReport", 777)
        self._hydrate(
            coordinator,
            ((event, EventDecision.ACCEPTED, ConnectionState.SYNCED),),
        )

        with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
            self._apply_snapshot(
                coordinator,
                self._snapshot("snapshot-stale", 99, event)
            )
        with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_CURSOR_MISMATCH"):
            self._apply_snapshot(
                coordinator,
                self._snapshot(
                    "snapshot-mismatch",
                    101,
                    UserDataEvent.create("event-2", 100, "executionReport", 777),
                )
            )
        self.assertEqual(coordinator.state, ConnectionState.RECONCILIATION_REQUIRED)

    def test_durable_start_validates_cursor_before_recovering_attempts(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                store.prepare(attempt())
                store.persist("attempt-1", now_us=1_700_000_000_000_001)
                store.mark_sending("attempt-1", now_us=1_700_000_000_000_002)
                coordinator = ReconciliationCoordinator(store)
                event = UserDataEvent.create("event-1", 100, "executionReport", 777)

                recovered = self._durable_start(
                    coordinator,
                    now_us=1_700_000_000_000_003,
                    observations=((event, EventDecision.ACCEPTED, ConnectionState.SYNCED),),
                )

                self.assertEqual(recovered[0].state, AttemptState.UNKNOWN)
                self.assertEqual(coordinator.state, ConnectionState.RECONCILIATION_REQUIRED)
                self.assertEqual(coordinator.accept_event(event), EventDecision.DUPLICATE)

    def test_invalid_durable_cursor_does_not_mutate_attempt_recovery(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                store.prepare(attempt())
                store.persist("attempt-1", now_us=1_700_000_000_000_001)
                store.mark_sending("attempt-1", now_us=1_700_000_000_000_002)
                coordinator = ReconciliationCoordinator(store)
                first = UserDataEvent.create("event-1", 100, "executionReport", 777)
                conflict = UserDataEvent(
                    event_id="event-1",
                    event_time_ms=100,
                    event_type="executionReport",
                    venue_order_id=778,
                    payload_fingerprint=hashlib.sha256(b"different").hexdigest(),
                )

                with self.assertRaisesRegex(ReconciliationError, "HYDRATION_EVENT_CONFLICT"):
                    self._durable_start(
                        coordinator,
                        now_us=1_700_000_000_000_003,
                        observations=(
                            (first, EventDecision.ACCEPTED, ConnectionState.SYNCED),
                            (conflict, EventDecision.ACCEPTED, ConnectionState.SYNCED),
                        ),
                    )

                self.assertEqual(store.get("attempt-1").state, AttemptState.SENDING)
                self.assertEqual(coordinator.state, ConnectionState.DISCONNECTED)

    def test_recovery_handoff_requires_lookup_for_each_attempt_before_snapshot(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                first = attempt()
                second = replace(
                    first,
                    attempt_id="attempt-2",
                    client_order_id="client-2",
                )
                store.prepare(first)
                store.prepare(second)
                for attempt_id, transition_time in (
                    ("attempt-1", 1_700_000_000_000_001),
                    ("attempt-2", 1_700_000_000_000_002),
                ):
                    store.persist(attempt_id, now_us=transition_time)
                    store.mark_sending(attempt_id, now_us=transition_time + 1)
                coordinator = ReconciliationCoordinator(store)
                event = UserDataEvent.create("event-1", 100, "executionReport", 777)
                recovered = self._durable_start(
                    coordinator,
                    now_us=1_700_000_000_000_004,
                    observations=((event, EventDecision.ACCEPTED, ConnectionState.SYNCED),),
                )
                query = RecordingRest(
                    {
                        "attempt-1": OrderLookup.found(777),
                        "attempt-2": OrderLookup.found(778),
                    }
                )

                resolved = self._reconcile_recovered(
                    coordinator,
                    recovered,
                    query,
                    now_us=1_700_000_000_000_005,
                )

                self.assertEqual(query.attempt_ids, ["attempt-1", "attempt-2"])
                self.assertEqual(
                    tuple(item.state for item in resolved),
                    (AttemptState.ACKNOWLEDGED, AttemptState.ACKNOWLEDGED),
                )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        self._snapshot("snapshot-1", 101, event)
                    ),
                    ConnectionState.SYNCED,
                )

    def test_recovery_handoff_validates_all_inputs_before_mutating_any_attempt(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                store.prepare(attempt())
                store.persist("attempt-1", now_us=1_700_000_000_000_001)
                store.mark_sending("attempt-1", now_us=1_700_000_000_000_002)
                coordinator = ReconciliationCoordinator(store)
                event = UserDataEvent.create("event-1", 100, "executionReport", 777)
                recovered = self._durable_start(
                    coordinator,
                    now_us=1_700_000_000_000_003,
                    observations=((event, EventDecision.ACCEPTED, ConnectionState.SYNCED),),
                )
                query = RecordingRest({"attempt-1": OrderLookup.found(777)})

                with self.assertRaisesRegex(ReconciliationError, "RECOVERY_HANDOFF_DUPLICATE"):
                    self._reconcile_recovered(
                        coordinator,
                        (recovered[0], recovered[0]),
                        query,
                        now_us=1_700_000_000_000_004,
                    )

                self.assertEqual(query.attempt_ids, [])
                self.assertEqual(store.get("attempt-1").state, AttemptState.UNKNOWN)

    def test_hydrated_gap_remains_blocking_and_does_not_promote_to_synced(self):
        coordinator = ReconciliationCoordinator()
        event = UserDataEvent.create("event-1", 100, "executionReport", 777)

        self._hydrate(
            coordinator,
            ((event, EventDecision.CONFLICT, ConnectionState.GAP),)
        )

        self.assertEqual(coordinator.state, ConnectionState.GAP)
        self.assertEqual(coordinator.accept_event(event), EventDecision.QUARANTINED)
        with self.assertRaisesRegex(ReconciliationError, "SYNC_STATE_INVALID"):
            coordinator.mark_synced(authoritative_snapshot=True)

    def test_hydration_keeps_failed_state_over_less_severe_observations(self):
        coordinator = ReconciliationCoordinator()
        first = UserDataEvent.create("event-1", 100, "executionReport", 777)
        failed = UserDataEvent.create("event-2", 101, "executionReport", 777)
        later = UserDataEvent.create("event-3", 102, "executionReport", 777)

        self._hydrate(
            coordinator,
            (
                (first, EventDecision.ACCEPTED, ConnectionState.SYNCED),
                (failed, EventDecision.ACCEPTED, ConnectionState.FAILED),
                (later, EventDecision.ACCEPTED, ConnectionState.GAP),
            ),
        )

        self.assertEqual(coordinator.state, ConnectionState.FAILED)

    def test_hydration_rejects_conflicting_accepted_cursor_without_partial_restore(self):
        coordinator = ReconciliationCoordinator()
        first = UserDataEvent.create("event-1", 100, "executionReport", 777)
        conflict = UserDataEvent(
            event_id="event-1",
            event_time_ms=100,
            event_type="executionReport",
            venue_order_id=778,
            payload_fingerprint=hashlib.sha256(b"different").hexdigest(),
        )

        with self.assertRaisesRegex(ReconciliationError, "HYDRATION_EVENT_CONFLICT"):
            self._hydrate(
                coordinator,
                (
                    (first, EventDecision.ACCEPTED, ConnectionState.SYNCED),
                    (conflict, EventDecision.ACCEPTED, ConnectionState.SYNCED),
                )
            )
        self.assertEqual(coordinator.state, ConnectionState.DISCONNECTED)

    def test_order_list_hydration_rejects_mixed_replay_without_partial_restore(self):
        coordinator = ReconciliationCoordinator()
        first = order_list_event()

        with self.assertRaisesRegex(ReconciliationError, "ORDER_LIST_HYDRATION_EVENT_INVALID"):
            coordinator.hydrate_order_list_continuity((first, object()))

        self.assertEqual(coordinator.state, ConnectionState.DISCONNECTED)
        coordinator.public_snapshot_ready()
        self.assertEqual(coordinator.accept_order_list_event(first), EventDecision.ACCEPTED)

    def test_order_list_hydration_rejects_older_cursor_without_partial_restore(self):
        coordinator = ReconciliationCoordinator()
        first = order_list_event()
        older = order_list_event(
            event_id="list-event-2",
            event_time_ms=99,
            transaction_time_ms=99,
        )

        with self.assertRaisesRegex(ReconciliationError, "ORDER_LIST_HYDRATION_ORDER"):
            coordinator.hydrate_order_list_continuity((first, older))

        self.assertEqual(coordinator.state, ConnectionState.DISCONNECTED)
        coordinator.public_snapshot_ready()
        self.assertEqual(coordinator.accept_order_list_event(first), EventDecision.ACCEPTED)

    def test_empty_order_list_hydration_requires_snapshot_but_not_resync_anchor(self):
        coordinator = ReconciliationCoordinator()

        self.assertEqual(
            coordinator.hydrate_order_list_continuity(()),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(self._snapshot("empty-list", 0, None)),
            ConnectionState.SYNCED,
        )

    def test_duplicate_order_list_hydration_is_rejected_without_partial_restore(self):
        coordinator = ReconciliationCoordinator()
        first = order_list_event()

        with self.assertRaisesRegex(ReconciliationError, "ORDER_LIST_HYDRATION_CONFLICT"):
            coordinator.hydrate_order_list_continuity((first, first))

        self.assertEqual(coordinator.state, ConnectionState.DISCONNECTED)

    def test_order_list_hydration_limit_is_bounded_without_partial_restore(self):
        coordinator = ReconciliationCoordinator()
        observations = tuple(
            replace(
                order_list_event(),
                event_id=f"list-event-{index}",
                event_time_ms=index,
                transaction_time_ms=index,
            )
            for index in range(1_001)
        )

        with self.assertRaisesRegex(ReconciliationError, "ORDER_LIST_HYDRATION_LIMIT"):
            coordinator.hydrate_order_list_continuity(observations)

        self.assertEqual(coordinator.state, ConnectionState.DISCONNECTED)

    def test_hydrated_order_list_cursor_requires_anchor_then_fresh_snapshot(self):
        coordinator = ReconciliationCoordinator()
        hydrated = order_list_event()

        self.assertEqual(
            coordinator.hydrate_order_list_continuity((hydrated,)),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        with self.assertRaisesRegex(ReconciliationError, "ORDER_LIST_RESYNC_ANCHOR_REQUIRED"):
            coordinator.apply_authoritative_snapshot(self._snapshot("before-anchor", 100, None))

        anchor = UserDataOrderListResyncAnchor("hydrated-anchor", 110, hydrated)
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(anchor),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
            coordinator.apply_authoritative_snapshot(self._snapshot("stale", 99, None))
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(self._snapshot("fresh", 110, None)),
            ConnectionState.SYNCED,
        )
        self.assertEqual(
            coordinator.accept_order_list_event(
                order_list_event(event_id="list-event-2", event_time_ms=111, transaction_time_ms=111)
            ),
            EventDecision.ACCEPTED,
        )

    def test_restart_terminal_cursor_requires_snapshot_after_event_time(self):
        terminal = order_list_event(
            event_id="terminal-freshness",
            event_time_ms=124,
            transaction_time_ms=121,
            list_status="ALL_DONE",
            list_order_status="ALL_DONE",
        )
        with self.assertRaisesRegex(OrderListError, "USER_STREAM_ORDER_LIST_ANCHOR_STALE"):
            UserDataOrderListResyncAnchor("stale-terminal-anchor", 123, terminal)

        coordinator = ReconciliationCoordinator()
        self.assertEqual(
            coordinator.hydrate_order_list_continuity((terminal,)),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(
                UserDataOrderListResyncAnchor("fresh-terminal-anchor", 124, terminal)
            ),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
            coordinator.apply_authoritative_snapshot(self._snapshot("stale-terminal-snapshot", 123, None))
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(self._snapshot("fresh-terminal-snapshot", 124, None)),
            ConnectionState.SYNCED,
        )

    def test_duplicate_and_older_resync_anchor_cannot_open_snapshot_gate(self):
        coordinator = ReconciliationCoordinator()
        hydrated = order_list_event()
        newer = order_list_event(
            event_id="list-anchor-110",
            event_time_ms=110,
            transaction_time_ms=110,
        )
        anchor = UserDataOrderListResyncAnchor("anchor-110", 110, newer)

        self.assertEqual(
            coordinator.hydrate_order_list_continuity((hydrated,)),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(anchor),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(anchor),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        older = UserDataOrderListResyncAnchor(
            "anchor-109",
            109,
            order_list_event(
                event_id="list-anchor-109",
                event_time_ms=109,
                transaction_time_ms=109,
            ),
        )
        with self.assertRaisesRegex(ReconciliationError, "RESYNC_ANCHOR_STALE"):
            coordinator.apply_order_list_resync_anchor(older)
        self.assertEqual(coordinator.public_snapshot_ready(), ConnectionState.RECONCILIATION_REQUIRED)
        with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
            coordinator.apply_authoritative_snapshot(self._snapshot("snapshot-109", 109, None))
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(self._snapshot("snapshot-110", 110, None)),
            ConnectionState.SYNCED,
        )
        self.assertEqual(
            coordinator.accept_order_list_event(
                order_list_event(event_id="list-event-111", event_time_ms=111, transaction_time_ms=111)
            ),
            EventDecision.ACCEPTED,
        )

    def test_resync_anchor_fingerprint_conflict_requires_new_anchor_and_snapshot(self):
        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()
        self.assertEqual(coordinator.accept_order_list_event(order_list_event()), EventDecision.ACCEPTED)
        coordinator.on_disconnect()
        coordinator.reconnect()
        anchor_event = order_list_event(
            event_id="list-anchor-fingerprint",
            event_time_ms=110,
            transaction_time_ms=110,
        )
        anchor = UserDataOrderListResyncAnchor("fingerprint-anchor", 110, anchor_event)
        conflict = order_list_event(
            event_id="list-anchor-fingerprint",
            event_time_ms=111,
            transaction_time_ms=111,
        )

        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(anchor),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(coordinator.accept_order_list_event(conflict), EventDecision.QUARANTINED)
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(self._snapshot("fingerprint-snapshot", 110, None)),
            ConnectionState.SYNCED,
        )
        self.assertEqual(coordinator.accept_order_list_event(conflict), EventDecision.CONFLICT)
        with self.assertRaisesRegex(ReconciliationError, "SYNC_STATE_INVALID"):
            coordinator.apply_authoritative_snapshot(self._snapshot("conflict-snapshot", 111, None))

        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(
                UserDataOrderListResyncAnchor("fingerprint-recovery", 111, conflict)
            ),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(self._snapshot("fingerprint-recovery-snapshot", 111, None)),
            ConnectionState.SYNCED,
        )
        self.assertEqual(coordinator.accept_order_list_event(order_list_event()), EventDecision.OUT_OF_ORDER)
        self.assertEqual(coordinator.state, ConnectionState.GAP)
        self.assertEqual(
            coordinator.accept_order_list_event(
                order_list_event(event_id="list-event-fingerprint-forward", event_time_ms=112, transaction_time_ms=112)
            ),
            EventDecision.QUARANTINED,
        )


if __name__ == "__main__":
    unittest.main()
