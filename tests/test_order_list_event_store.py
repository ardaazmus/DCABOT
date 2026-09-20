import hashlib
import json
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from dcabot.application.order_list_contract import (
    OrderListLegIdentity,
    OrderListLegRole,
    UserDataOrderListEvent,
    UserDataOrderListLeg,
    UserDataOrderListResyncAnchor,
    create_oco_identity,
)
from dcabot.application.order_list_reconciliation import (
    CancelReplaceDisposition,
    CancelReplaceIdentity,
    OrderListVenueEvent,
)
from dcabot.persistence.order_list_event_store import (
    OrderListEventStore,
    OrderListEventStoreError,
    OrderListJournalRecordOutcome,
)
from dcabot.application.reconciliation import (
    AuthoritativeReconciliationSnapshot,
    ConnectionState,
    EventDecision,
    ReconciliationError,
    ReconciliationCoordinator,
)


class OrderListEventStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "oco-events.sqlite3"
        self.identity = create_oco_identity(
            order_list_id=42,
            list_client_order_id="list-42",
            symbol="BTCUSDT",
            working=OrderListLegIdentity(
                "working", 101, "working-101", OrderListLegRole.WORKING, "LIMIT"
            ),
            pending=OrderListLegIdentity(
                "pending", 102, "pending-102", OrderListLegRole.PENDING, "STOP_LOSS_LIMIT"
            ),
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def event(self, *, event_id="event-1", at=100, status="EXECUTING"):
        return OrderListVenueEvent(
            event_id,
            at,
            42,
            "list-42",
            101,
            "working-101",
            status,
            status,
            "NEW",
        )

    def replacement(self, *, operation_id="replace-1", at=101, cancel="SUCCESS", new="FAILURE"):
        return CancelReplaceIdentity(
            operation_id,
            101,
            "working-101",
            cancel,
            new,
            103 if new == "SUCCESS" else None,
            "working-103" if new == "SUCCESS" else None,
            at,
        )

    def user_data_event(self, *, event_id="list:42:120:123", at=120):
        return UserDataOrderListEvent(
            event_id,
            123,
            at,
            "BTCUSDT",
            42,
            "OCO",
            "EXEC_STARTED",
            "EXECUTING",
            "list-42",
            (
                UserDataOrderListLeg("BTCUSDT", 101, "working-101"),
                UserDataOrderListLeg("BTCUSDT", 102, "pending-102"),
            ),
        )

    def test_restart_replays_ordered_events_and_cancel_replace_without_identity_migration(self):
        with OrderListEventStore.create(self.path, self.identity) as store:
            self.assertEqual(store.append_event(self.event()), OrderListJournalRecordOutcome.ACCEPTED)
            replacement = self.replacement()
            self.assertEqual(
                store.append_cancel_replace(replacement),
                OrderListJournalRecordOutcome.ACCEPTED,
            )
            expected = store.load()
            self.assertEqual(expected.identity, self.identity)
            self.assertEqual(expected.observations, (self.event(), replacement))
            self.assertEqual(replacement.disposition, CancelReplaceDisposition.CANCEL_CONFIRMED_NEW_REJECTED)
        with OrderListEventStore.open(self.path) as reopened:
            self.assertEqual(reopened.load(), expected)

    def test_exact_duplicate_is_idempotent_and_conflicting_payload_is_rejected(self):
        with OrderListEventStore.create(self.path, self.identity) as store:
            first = self.event()
            self.assertEqual(store.append_event(first), OrderListJournalRecordOutcome.ACCEPTED)
            self.assertEqual(store.append_event(first), OrderListJournalRecordOutcome.DUPLICATE)
            with self.assertRaisesRegex(OrderListEventStoreError, "ORDER_LIST_EVENT_CONFLICT"):
                store.append_event(self.event(at=101))
            self.assertEqual(store.load().observations, (first,))

    def test_identity_conflict_is_rejected_without_journal_write(self):
        with OrderListEventStore.create(self.path, self.identity) as store:
            conflicting = self.event()
            conflicting = OrderListVenueEvent(
                conflicting.event_id,
                conflicting.event_time_ms,
                43,
                conflicting.list_client_order_id,
                conflicting.order_id,
                conflicting.client_order_id,
                conflicting.list_status,
                conflicting.list_order_status,
                conflicting.leg_status,
            )
            with self.assertRaisesRegex(OrderListEventStoreError, "ORDER_LIST_EVENT_CONFLICT"):
                store.append_event(conflicting)
            self.assertEqual(store.load().observations, ())

    def test_cross_type_out_of_order_and_terminal_observations_fail_closed(self):
        with OrderListEventStore.create(self.path, self.identity) as store:
            store.append_event(self.event(at=100))
            with self.assertRaisesRegex(OrderListEventStoreError, "ORDER_LIST_EVENT_OUT_OF_ORDER"):
                store.append_cancel_replace(self.replacement(at=99))
            terminal = self.event(event_id="event-2", at=101, status="ALL_DONE")
            terminal = OrderListVenueEvent(
                terminal.event_id,
                terminal.event_time_ms,
                terminal.order_list_id,
                terminal.list_client_order_id,
                terminal.order_id,
                terminal.client_order_id,
                "ALL_DONE",
                "ALL_DONE",
                "CANCELED",
            )
            store.append_event(terminal)
            with self.assertRaisesRegex(OrderListEventStoreError, "ORDER_LIST_TERMINAL_EVENT"):
                store.append_cancel_replace(self.replacement(operation_id="replace-2", at=102))

    def test_tampered_observation_checksum_fails_closed_on_reopen(self):
        with OrderListEventStore.create(self.path, self.identity) as store:
            store.append_event(self.event())
        db = sqlite3.connect(self.path)
        try:
            db.execute(
                "UPDATE order_list_event_observations SET observation_payload=?",
                ("{}",),
            )
            db.commit()
        finally:
            db.close()
        with self.assertRaisesRegex(OrderListEventStoreError, "ORDER_LIST_EVENT_RECORD_CORRUPT"):
            OrderListEventStore.open(self.path)

    def test_user_data_list_status_is_durable_without_inventing_leg_status(self):
        event = self.user_data_event()
        with OrderListEventStore.create(self.path, self.identity) as store:
            self.assertEqual(store.append_user_data_event(event), OrderListJournalRecordOutcome.ACCEPTED)
            self.assertEqual(store.append_user_data_event(event), OrderListJournalRecordOutcome.DUPLICATE)
            self.assertEqual(store.load().observations, (event,))
        with OrderListEventStore.open(self.path) as reopened:
            self.assertEqual(reopened.load().observations, (event,))

    def test_journal_duplicate_and_conflict_match_coordinator_decisions(self):
        event = self.user_data_event()
        conflict = UserDataOrderListEvent(
            event.event_id,
            event.transaction_time_ms,
            event.event_time_ms,
            event.symbol,
            event.order_list_id,
            event.contingency_type,
            "REJECT",
            "REJECT",
            event.list_client_order_id,
            event.orders,
        )
        with OrderListEventStore.create(self.path, self.identity) as store:
            self.assertEqual(store.append_user_data_event(event), OrderListJournalRecordOutcome.ACCEPTED)
            self.assertEqual(store.append_user_data_event(event), OrderListJournalRecordOutcome.DUPLICATE)
            with self.assertRaisesRegex(OrderListEventStoreError, "ORDER_LIST_EVENT_CONFLICT"):
                store.append_user_data_event(conflict)

        coordinator = ReconciliationCoordinator()
        coordinator.public_snapshot_ready()
        self.assertEqual(coordinator.accept_order_list_event(event), EventDecision.ACCEPTED)
        self.assertEqual(coordinator.accept_order_list_event(event), EventDecision.DUPLICATE)
        self.assertEqual(coordinator.accept_order_list_event(conflict), EventDecision.CONFLICT)
        self.assertEqual(coordinator.state, ConnectionState.GAP)

    def test_reopen_replays_same_cursor_identity_and_fingerprint_parity(self):
        base = replace(
            self.user_data_event(event_id="same-cursor-base", at=300),
            event_time_ms=200,
            transaction_time_ms=300,
        )
        same_cursor_identity = replace(base, event_id="same-cursor-second")
        same_identity_conflict = replace(
            base,
            list_status="REJECT",
            list_order_status="REJECT",
        )
        with OrderListEventStore.create(self.path, self.identity) as store:
            self.assertEqual(store.append_user_data_event(base), OrderListJournalRecordOutcome.ACCEPTED)
            self.assertEqual(
                store.append_user_data_event(same_cursor_identity),
                OrderListJournalRecordOutcome.ACCEPTED,
            )
            self.assertEqual(store.append_user_data_event(base), OrderListJournalRecordOutcome.DUPLICATE)
            with self.assertRaisesRegex(OrderListEventStoreError, "ORDER_LIST_EVENT_CONFLICT"):
                store.append_user_data_event(same_identity_conflict)
        with OrderListEventStore.open(self.path) as reopened:
            list_events = reopened.load_user_data_events()
            self.assertEqual(list_events, (base, same_cursor_identity))

        coordinator = ReconciliationCoordinator()
        self.assertEqual(
            coordinator.hydrate_order_list_continuity(list_events),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(
                UserDataOrderListResyncAnchor("same-cursor-anchor", 350, same_cursor_identity)
            ),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(
                AuthoritativeReconciliationSnapshot("same-cursor-snapshot", 350, None, "a" * 64)
            ),
            ConnectionState.SYNCED,
        )
        self.assertEqual(coordinator.accept_order_list_event(base), EventDecision.ACCEPTED)
        self.assertEqual(
            coordinator.accept_order_list_event(same_cursor_identity),
            EventDecision.DUPLICATE,
        )
        self.assertEqual(
            coordinator.accept_order_list_event(same_identity_conflict),
            EventDecision.CONFLICT,
        )
        self.assertEqual(coordinator.state, ConnectionState.GAP)

    def test_user_data_list_status_identity_conflict_and_gap_fail_closed(self):
        with OrderListEventStore.create(self.path, self.identity) as store:
            first = self.user_data_event()
            store.append_user_data_event(first)
            conflicting = self.user_data_event(event_id="list:43:220:223")
            conflicting = UserDataOrderListEvent(
                conflicting.event_id,
                conflicting.event_time_ms,
                223,
                "ETHUSDT",
                conflicting.order_list_id,
                conflicting.contingency_type,
                conflicting.list_status,
                conflicting.list_order_status,
                conflicting.list_client_order_id,
                tuple(
                    UserDataOrderListLeg("ETHUSDT", order.order_id, order.client_order_id)
                    for order in conflicting.orders
                ),
            )
            with self.assertRaisesRegex(OrderListEventStoreError, "USER_STREAM_ORDER_LIST_IDENTITY_CONFLICT"):
                store.append_user_data_event(conflicting)
            with self.assertRaisesRegex(OrderListEventStoreError, "ORDER_LIST_EVENT_OUT_OF_ORDER"):
                store.append_user_data_event(self.user_data_event(event_id="list:42:119:122", at=119))
            self.assertEqual(store.load().observations, (first,))

    def test_reopened_journal_hydrates_order_list_cursor_without_sync_authority(self):
        first = self.user_data_event()
        second = self.user_data_event(event_id="list:42:130:133", at=130)
        with OrderListEventStore.create(self.path, self.identity) as store:
            store.append_user_data_event(first)
            store.append_user_data_event(second)
        with OrderListEventStore.open(self.path) as reopened:
            snapshot = reopened.load()

        coordinator = ReconciliationCoordinator()
        list_events = tuple(
            observation
            for observation in snapshot.observations
            if isinstance(observation, UserDataOrderListEvent)
        )
        self.assertEqual(
            coordinator.hydrate_order_list_continuity(list_events),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.accept_order_list_event(
                self.user_data_event(event_id="list:42:140:143", at=140)
            ),
            EventDecision.QUARANTINED,
        )
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(
                UserDataOrderListResyncAnchor("restart-anchor", 150, second)
            ),
            ConnectionState.RECONCILIATION_REQUIRED,
        )

    def test_sqlite_reopen_hydrates_anchor_and_authoritative_snapshot_offline(self):
        first = self.user_data_event()
        second = self.user_data_event(event_id="list:42:130:133", at=130)
        with OrderListEventStore.create(self.path, self.identity) as store:
            store.append_user_data_event(first)
            store.append_user_data_event(second)
        with OrderListEventStore.open(self.path) as reopened:
            snapshot = reopened.load()

        coordinator = ReconciliationCoordinator()
        list_events = tuple(
            observation
            for observation in snapshot.observations
            if isinstance(observation, UserDataOrderListEvent)
        )
        self.assertEqual(
            coordinator.hydrate_order_list_continuity(list_events),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(
                UserDataOrderListResyncAnchor("e2e-anchor", 150, second)
            ),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(
                AuthoritativeReconciliationSnapshot("e2e-snapshot", 150, None, "a" * 64)
            ),
            ConnectionState.SYNCED,
        )
        self.assertEqual(
            coordinator.accept_order_list_event(
                self.user_data_event(event_id="list:42:160:163", at=160)
            ),
            EventDecision.ACCEPTED,
        )

    def test_reopened_store_exposes_only_list_status_for_coordinator_hydration(self):
        list_event = self.user_data_event()
        venue_event = self.event(event_id="event-2", at=121)
        with OrderListEventStore.create(self.path, self.identity) as store:
            store.append_user_data_event(list_event)
            store.append_event(venue_event)
            store.append_cancel_replace(self.replacement(at=122))
        with OrderListEventStore.open(self.path) as reopened:
            self.assertEqual(reopened.load_user_data_events(), (list_event,))
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )

    def test_empty_journal_hydration_requires_authoritative_snapshot(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            self.assertEqual(reopened.load().observations, ())
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(coordinator.public_snapshot_ready(), ConnectionState.RECONCILIATION_REQUIRED)
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("empty-journal-snapshot", 0, None, "a" * 64)
                ),
                ConnectionState.SYNCED,
            )

    def test_empty_reopen_and_resync_anchor_keep_cursor_freshness_parity(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            self.assertEqual(reopened.load_user_data_events(), ())

            empty = ReconciliationCoordinator()
            self.assertEqual(
                empty.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(empty.public_snapshot_ready(), ConnectionState.RECONCILIATION_REQUIRED)
            self.assertEqual(
                empty.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("empty-reopen-snapshot", 0, None, "a" * 64)
                ),
                ConnectionState.SYNCED,
            )

            anchored = ReconciliationCoordinator()
            self.assertEqual(
                anchored.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            cursor = self.user_data_event()
            self.assertEqual(
                anchored.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("empty-reopen-anchor", 123, cursor)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                anchored.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("empty-reopen-stale", 122, None, "a" * 64)
                )
            self.assertEqual(
                anchored.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("empty-reopen-fresh", 123, None, "b" * 64)
                ),
                ConnectionState.SYNCED,
            )

    def test_empty_reopen_same_cursor_conflict_requires_replacement_anchor(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            self.assertEqual(reopened.load_user_data_events(), ())
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            cursor = self.user_data_event()
            conflict = replace(cursor, list_status="REJECT", list_order_status="REJECT")
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("empty-conflict-anchor", 123, cursor)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("empty-conflict-snapshot", 123, None, "a" * 64)
                ),
                ConnectionState.SYNCED,
            )
            self.assertEqual(coordinator.accept_order_list_event(cursor), EventDecision.DUPLICATE)
            self.assertEqual(coordinator.accept_order_list_event(conflict), EventDecision.CONFLICT)
            self.assertEqual(coordinator.state, ConnectionState.GAP)
            with self.assertRaisesRegex(ReconciliationError, "SYNC_STATE_INVALID"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("empty-conflict-invalid", 123, None, "b" * 64)
                )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("empty-conflict-replacement", 123, conflict)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("empty-conflict-replacement-snapshot", 123, None, "c" * 64)
                ),
                ConnectionState.SYNCED,
            )
            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_replacement_anchor_keeps_terminal_late_events_quarantined(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            terminal = replace(
                self.user_data_event(),
                list_status="REJECT",
                list_order_status="REJECT",
            )
            late = replace(
                terminal,
                event_id="empty-terminal-late",
                event_time_ms=122,
                transaction_time_ms=123,
            )
            after_terminal = replace(
                terminal,
                event_id="empty-terminal-after",
                event_time_ms=124,
                transaction_time_ms=124,
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("empty-terminal-anchor", 123, terminal)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("empty-terminal-snapshot", 123, None, "a" * 64)
                ),
                ConnectionState.SYNCED,
            )
            self.assertEqual(coordinator.accept_order_list_event(terminal), EventDecision.DUPLICATE)
            self.assertEqual(coordinator.accept_order_list_event(late), EventDecision.QUARANTINED)
            self.assertEqual(coordinator.accept_order_list_event(after_terminal), EventDecision.QUARANTINED)
            self.assertEqual(coordinator.state, ConnectionState.SYNCED)
            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_terminal_anchor_snapshot_freshness_uses_both_cursor_components(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            transaction_coordinator = ReconciliationCoordinator()
            self.assertEqual(
                transaction_coordinator.hydrate_order_list_continuity(
                    reopened.load_user_data_events()
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            transaction_terminal = replace(
                self.user_data_event(event_id="terminal-transaction", at=210),
                event_time_ms=200,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                transaction_coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor(
                        "terminal-transaction-anchor", 210, transaction_terminal
                    )
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                transaction_coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot(
                        "terminal-transaction-stale", 209, None, "a" * 64
                    )
                )
            self.assertEqual(
                transaction_coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot(
                        "terminal-transaction-fresh", 210, None, "b" * 64
                    )
                ),
                ConnectionState.SYNCED,
            )

            event_coordinator = ReconciliationCoordinator()
            self.assertEqual(
                event_coordinator.hydrate_order_list_continuity(
                    reopened.load_user_data_events()
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            event_terminal = replace(
                self.user_data_event(event_id="terminal-event", at=200),
                event_time_ms=210,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                event_coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("terminal-event-anchor", 210, event_terminal)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                event_coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("terminal-event-stale", 209, None, "c" * 64)
                )
            self.assertEqual(
                event_coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("terminal-event-fresh", 210, None, "d" * 64)
                ),
                ConnectionState.SYNCED,
            )
            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_stale_resync_anchor_cannot_bypass_snapshot_reentry(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            terminal = replace(
                self.user_data_event(event_id="terminal-base", at=210),
                event_time_ms=210,
                transaction_time_ms=210,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("terminal-base-anchor", 210, terminal)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("terminal-base-snapshot", 210, None, "a" * 64)
                ),
                ConnectionState.SYNCED,
            )

            conflict = replace(
                terminal,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(coordinator.accept_order_list_event(conflict), EventDecision.CONFLICT)
            self.assertEqual(coordinator.state, ConnectionState.GAP)

            stale_anchor = replace(
                conflict,
                event_id="stale-anchor",
                event_time_ms=209,
                transaction_time_ms=209,
            )
            with self.assertRaisesRegex(ReconciliationError, "RESYNC_ANCHOR_STALE"):
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("stale-anchor-cursor", 209, stale_anchor)
                )
            with self.assertRaisesRegex(ReconciliationError, "SYNC_STATE_INVALID"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("stale-anchor-snapshot", 211, None, "b" * 64)
                )

            replacement = replace(
                conflict,
                event_id="fresh-replacement",
                event_time_ms=211,
                transaction_time_ms=211,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("fresh-replacement-anchor", 211, replacement)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("fresh-replacement-snapshot", 211, None, "c" * 64)
                ),
                ConnectionState.SYNCED,
            )
            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_equal_cursor_resync_identity_requires_fresh_snapshot(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            terminal = replace(
                self.user_data_event(event_id="terminal-base", at=210),
                event_time_ms=210,
                transaction_time_ms=210,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("terminal-base-anchor", 210, terminal)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("terminal-base-snapshot", 210, None, "a" * 64)
                ),
                ConnectionState.SYNCED,
            )
            conflict = replace(
                terminal,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(coordinator.accept_order_list_event(conflict), EventDecision.CONFLICT)
            self.assertEqual(coordinator.state, ConnectionState.GAP)

            equal_cursor_replacement = replace(
                conflict,
                event_id="equal-cursor-replacement",
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor(
                        "equal-cursor-replacement-anchor", 210, equal_cursor_replacement
                    )
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "AUTHORITATIVE_SNAPSHOT_REQUIRED"):
                coordinator.mark_synced(authoritative_snapshot=True)
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-cursor-fresh", 210, None, "c" * 64)
                ),
                ConnectionState.SYNCED,
            )
            self.assertEqual(coordinator.accept_order_list_event(equal_cursor_replacement), EventDecision.DUPLICATE)
            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_equal_cursor_terminal_replacement_quarantines_late_and_forward_events(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            terminal = replace(
                self.user_data_event(event_id="terminal-base", at=210),
                event_time_ms=210,
                transaction_time_ms=210,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("terminal-base-anchor", 210, terminal)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("terminal-base-snapshot", 210, None, "a" * 64)
                ),
                ConnectionState.SYNCED,
            )
            conflict = replace(
                terminal,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(coordinator.accept_order_list_event(conflict), EventDecision.CONFLICT)
            self.assertEqual(coordinator.state, ConnectionState.GAP)
            equal_cursor_replacement = replace(
                conflict,
                event_id="equal-cursor-replacement",
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor(
                        "equal-cursor-replacement-anchor", 210, equal_cursor_replacement
                    )
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-cursor-snapshot", 210, None, "b" * 64)
                ),
                ConnectionState.SYNCED,
            )

            late_event = replace(
                equal_cursor_replacement,
                event_id="late-event",
                event_time_ms=209,
                transaction_time_ms=209,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            forward_event = replace(
                equal_cursor_replacement,
                event_id="forward-event",
                event_time_ms=211,
                transaction_time_ms=211,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(equal_cursor_replacement), EventDecision.DUPLICATE
            )
            self.assertEqual(coordinator.accept_order_list_event(late_event), EventDecision.QUARANTINED)
            self.assertEqual(coordinator.accept_order_list_event(forward_event), EventDecision.QUARANTINED)
            self.assertEqual(coordinator.state, ConnectionState.SYNCED)
            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_equal_cursor_replacement_fingerprint_conflict_requires_snapshot_reentry(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            replacement = replace(
                self.user_data_event(event_id="equal-cursor-replacement", at=210),
                event_time_ms=210,
                transaction_time_ms=210,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-cursor-anchor", 210, replacement)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-cursor-snapshot", 210, None, "a" * 64)
                ),
                ConnectionState.SYNCED,
            )

            fingerprint_conflict = replace(
                replacement,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(fingerprint_conflict), EventDecision.CONFLICT
            )
            self.assertEqual(coordinator.state, ConnectionState.GAP)
            with self.assertRaisesRegex(ReconciliationError, "SYNC_STATE_INVALID"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("conflict-snapshot", 210, None, "b" * 64)
                )

            recovery_replacement = replace(
                fingerprint_conflict,
                event_id="equal-cursor-recovery",
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-cursor-recovery-anchor", 210, recovery_replacement)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-cursor-recovery-snapshot", 210, None, "c" * 64)
                ),
                ConnectionState.SYNCED,
            )
            self.assertEqual(coordinator.accept_order_list_event(recovery_replacement), EventDecision.DUPLICATE)
            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_recovery_anchor_snapshot_freshness_preserves_terminal_quarantine(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            replacement = replace(
                self.user_data_event(event_id="equal-cursor-replacement", at=210),
                event_time_ms=210,
                transaction_time_ms=210,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-cursor-anchor", 210, replacement)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-cursor-snapshot", 210, None, "a" * 64)
                ),
                ConnectionState.SYNCED,
            )
            fingerprint_conflict = replace(
                replacement,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(fingerprint_conflict), EventDecision.CONFLICT
            )
            recovery_replacement = replace(
                fingerprint_conflict,
                event_id="equal-cursor-recovery",
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-cursor-recovery-anchor", 210, recovery_replacement)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-cursor-recovery-stale", 209, None, "b" * 64)
                )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-cursor-recovery-fresh", 210, None, "c" * 64)
                ),
                ConnectionState.SYNCED,
            )

            late_event = replace(
                recovery_replacement,
                event_id="recovery-late-event",
                event_time_ms=209,
                transaction_time_ms=209,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            forward_event = replace(
                recovery_replacement,
                event_id="recovery-forward-event",
                event_time_ms=211,
                transaction_time_ms=211,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(coordinator.accept_order_list_event(recovery_replacement), EventDecision.DUPLICATE)
            self.assertEqual(coordinator.accept_order_list_event(late_event), EventDecision.QUARANTINED)
            self.assertEqual(coordinator.accept_order_list_event(forward_event), EventDecision.QUARANTINED)
            self.assertEqual(coordinator.state, ConnectionState.SYNCED)
            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_recovery_anchor_transaction_and_event_cursor_components_match(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            for component_name, recovery_cursor in (
                ("transaction", (210, 200)),
                ("event", (200, 210)),
            ):
                coordinator = ReconciliationCoordinator()
                self.assertEqual(
                    coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                base = replace(
                    self.user_data_event(event_id=f"{component_name}-base", at=200),
                    event_time_ms=200,
                    transaction_time_ms=200,
                    list_status="REJECT",
                    list_order_status="REJECT",
                )
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(f"{component_name}-base-anchor", 200, base)
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"{component_name}-base-snapshot", 200, None, "a" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )

                conflict = replace(
                    base,
                    list_status="EXECUTING",
                    list_order_status="EXECUTING",
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(conflict), EventDecision.CONFLICT
                )
                self.assertEqual(coordinator.state, ConnectionState.GAP)

                recovery = replace(
                    conflict,
                    event_id=f"{component_name}-recovery",
                    event_time_ms=recovery_cursor[1],
                    transaction_time_ms=recovery_cursor[0],
                    list_status="REJECT",
                    list_order_status="REJECT",
                )
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"{component_name}-recovery-anchor", 210, recovery
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"{component_name}-stale-snapshot", 209, None, "b" * 64
                        )
                    )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"{component_name}-fresh-snapshot", 210, None, "c" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )

            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_recovery_anchor_mixed_component_equal_boundary_quarantines_late_events(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            for component_name, recovery_cursor, late_cursor, forward_cursor in (
                ("transaction", (210, 200), (210, 199), (211, 200)),
                ("event", (200, 210), (199, 210), (200, 211)),
            ):
                coordinator = ReconciliationCoordinator()
                self.assertEqual(
                    coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                terminal = replace(
                    self.user_data_event(event_id=f"{component_name}-terminal", at=200),
                    event_time_ms=recovery_cursor[1],
                    transaction_time_ms=recovery_cursor[0],
                    list_status="REJECT",
                    list_order_status="REJECT",
                )
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"{component_name}-terminal-anchor", 210, terminal
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"{component_name}-equal-boundary", 210, None, "a" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )
                self.assertEqual(coordinator.accept_order_list_event(terminal), EventDecision.DUPLICATE)
                late_event = replace(
                    terminal,
                    event_id=f"{component_name}-late",
                    event_time_ms=late_cursor[1],
                    transaction_time_ms=late_cursor[0],
                    list_status="EXECUTING",
                    list_order_status="EXECUTING",
                )
                forward_event = replace(
                    terminal,
                    event_id=f"{component_name}-forward",
                    event_time_ms=forward_cursor[1],
                    transaction_time_ms=forward_cursor[0],
                    list_status="EXECUTING",
                    list_order_status="EXECUTING",
                )
                self.assertEqual(coordinator.accept_order_list_event(late_event), EventDecision.QUARANTINED)
                self.assertEqual(
                    coordinator.accept_order_list_event(forward_event), EventDecision.QUARANTINED
                )
                self.assertEqual(coordinator.state, ConnectionState.SYNCED)

            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_recovery_anchor_paired_component_ordering_quarantines_after_regression(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            cases = (
                ("tx-primary-regressed", (210, 200), (209, 201), (211, 200)),
                ("tx-secondary-regressed", (210, 200), (210, 199), (211, 200)),
                ("event-secondary-regressed", (200, 210), (200, 209), (200, 211)),
                ("event-primary-regressed", (200, 210), (199, 211), (200, 211)),
            )
            for case_name, recovery_cursor, late_cursor, forward_cursor in cases:
                coordinator = ReconciliationCoordinator()
                self.assertEqual(
                    coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                anchor_event = replace(
                    self.user_data_event(event_id=f"{case_name}-anchor", at=200),
                    event_time_ms=recovery_cursor[1],
                    transaction_time_ms=recovery_cursor[0],
                )
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"{case_name}-resync", 210, anchor_event
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"{case_name}-snapshot", 210, None, "a" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )
                late_event = replace(
                    anchor_event,
                    event_id=f"{case_name}-late",
                    event_time_ms=late_cursor[1],
                    transaction_time_ms=late_cursor[0],
                )
                forward_event = replace(
                    anchor_event,
                    event_id=f"{case_name}-forward",
                    event_time_ms=forward_cursor[1],
                    transaction_time_ms=forward_cursor[0],
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(late_event), EventDecision.OUT_OF_ORDER
                )
                self.assertEqual(coordinator.state, ConnectionState.GAP)
                self.assertEqual(
                    coordinator.accept_order_list_event(forward_event), EventDecision.QUARANTINED
                )
                self.assertEqual(coordinator.state, ConnectionState.GAP)

            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_recovery_anchor_post_gap_reentry_requires_paired_fresh_snapshot(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            cases = (
                ("tx-reentry", (210, 200), (199, 201)),
                ("event-reentry", (200, 210), (199, 201)),
            )
            for case_name, recovery_cursor, late_cursor in cases:
                coordinator = ReconciliationCoordinator()
                self.assertEqual(
                    coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                initial = replace(
                    self.user_data_event(event_id=f"{case_name}-initial", at=200),
                    event_time_ms=200,
                    transaction_time_ms=200,
                )
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"{case_name}-initial-anchor", 200, initial
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"{case_name}-initial-snapshot", 200, None, "a" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )
                late_event = replace(
                    initial,
                    event_id=f"{case_name}-late",
                    event_time_ms=late_cursor[1],
                    transaction_time_ms=late_cursor[0],
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(late_event), EventDecision.OUT_OF_ORDER
                )
                self.assertEqual(coordinator.state, ConnectionState.GAP)
                with self.assertRaisesRegex(ReconciliationError, "SYNC_STATE_INVALID"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"{case_name}-blocked-snapshot", 210, None, "b" * 64
                        )
                    )

                recovery = replace(
                    initial,
                    event_id=f"{case_name}-recovery",
                    event_time_ms=recovery_cursor[1],
                    transaction_time_ms=recovery_cursor[0],
                )
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"{case_name}-recovery-anchor", 210, recovery
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"{case_name}-stale-snapshot", 209, None, "c" * 64
                        )
                    )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"{case_name}-fresh-snapshot", 210, None, "d" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )
                self.assertEqual(coordinator.accept_order_list_event(recovery), EventDecision.DUPLICATE)

            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_post_gap_replacement_conflict_reentry_quarantines_old_and_forward_events(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            cases = (
                ("tx-conflict", (210, 200)),
                ("event-conflict", (200, 210)),
            )
            for case_name, recovery_cursor in cases:
                coordinator = ReconciliationCoordinator()
                self.assertEqual(
                    coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                base = self.user_data_event(event_id=f"{case_name}-base", at=200)
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(f"{case_name}-base-anchor", 200, base)
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"{case_name}-base-snapshot", 200, None, "a" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )
                replacement_conflict = replace(
                    base,
                    list_status="REJECT",
                    list_order_status="REJECT",
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(replacement_conflict), EventDecision.CONFLICT
                )
                self.assertEqual(coordinator.state, ConnectionState.GAP)
                with self.assertRaisesRegex(ReconciliationError, "SYNC_STATE_INVALID"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"{case_name}-blocked-snapshot", 210, None, "b" * 64
                        )
                    )

                recovery = replace(
                    replacement_conflict,
                    event_id=f"{case_name}-recovery",
                    event_time_ms=recovery_cursor[1],
                    transaction_time_ms=recovery_cursor[0],
                )
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(f"{case_name}-recovery-anchor", 210, recovery)
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"{case_name}-stale-snapshot", 209, None, "c" * 64
                        )
                    )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"{case_name}-fresh-snapshot", 210, None, "d" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )
                self.assertEqual(coordinator.accept_order_list_event(recovery), EventDecision.DUPLICATE)
                self.assertEqual(
                    coordinator.accept_order_list_event(replacement_conflict), EventDecision.QUARANTINED
                )
                forward_event = replace(
                    recovery,
                    event_id=f"{case_name}-forward",
                    event_time_ms=recovery_cursor[1] + 1,
                    transaction_time_ms=recovery_cursor[0] + 1,
                    list_status="EXECUTING",
                    list_order_status="EXECUTING",
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(forward_event), EventDecision.QUARANTINED
                )
                self.assertEqual(coordinator.state, ConnectionState.SYNCED)

            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_post_gap_repeated_conflict_requires_monotonic_terminal_reentry(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            base = self.user_data_event(event_id="repeated-conflict-base", at=200)
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("repeated-conflict-base-anchor", 200, base)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("repeated-conflict-base-snapshot", 200, None, "a" * 64)
                ),
                ConnectionState.SYNCED,
            )

            first_conflict = replace(base, list_status="REJECT", list_order_status="REJECT")
            self.assertEqual(
                coordinator.accept_order_list_event(first_conflict), EventDecision.CONFLICT
            )
            self.assertEqual(coordinator.state, ConnectionState.GAP)
            first_recovery = replace(
                first_conflict,
                event_id="repeated-conflict-first-recovery",
                event_time_ms=210,
                transaction_time_ms=210,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("repeated-conflict-first-anchor", 210, first_recovery)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("repeated-conflict-first-snapshot", 210, None, "b" * 64)
                ),
                ConnectionState.SYNCED,
            )

            second_conflict = replace(
                first_recovery,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(second_conflict), EventDecision.CONFLICT
            )
            self.assertEqual(coordinator.state, ConnectionState.GAP)
            stale_recovery = replace(
                second_conflict,
                event_id="repeated-conflict-stale-recovery",
                event_time_ms=209,
                transaction_time_ms=209,
            )
            with self.assertRaisesRegex(ReconciliationError, "RESYNC_ANCHOR_STALE"):
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("repeated-conflict-stale-anchor", 209, stale_recovery)
                )
            self.assertEqual(coordinator.state, ConnectionState.GAP)

            second_recovery = replace(
                second_conflict,
                event_id="repeated-conflict-second-recovery",
                event_time_ms=211,
                transaction_time_ms=211,
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("repeated-conflict-second-anchor", 211, second_recovery)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("repeated-conflict-stale-snapshot", 210, None, "c" * 64)
                )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("repeated-conflict-second-snapshot", 211, None, "d" * 64)
                ),
                ConnectionState.SYNCED,
            )
            self.assertEqual(
                coordinator.accept_order_list_event(second_recovery), EventDecision.DUPLICATE
            )
            self.assertEqual(
                coordinator.accept_order_list_event(first_recovery), EventDecision.QUARANTINED
            )
            forward_event = replace(
                second_recovery,
                event_id="repeated-conflict-forward",
                event_time_ms=212,
                transaction_time_ms=212,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(forward_event), EventDecision.QUARANTINED
            )
            self.assertEqual(coordinator.state, ConnectionState.SYNCED)
            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_post_gap_repeated_equal_boundary_anchor_preserves_quarantine(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            base = self.user_data_event(event_id="equal-boundary-base", at=200)
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-boundary-base-anchor", 200, base)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-boundary-base-snapshot", 200, None, "a" * 64)
                ),
                ConnectionState.SYNCED,
            )

            first_conflict = replace(base, list_status="REJECT", list_order_status="REJECT")
            self.assertEqual(
                coordinator.accept_order_list_event(first_conflict), EventDecision.CONFLICT
            )
            first_recovery = replace(
                first_conflict,
                event_id="equal-boundary-first-recovery",
                event_time_ms=200,
                transaction_time_ms=210,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-boundary-first-anchor", 210, first_recovery)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-boundary-first-snapshot", 210, None, "b" * 64)
                ),
                ConnectionState.SYNCED,
            )

            second_conflict = replace(
                first_recovery,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(second_conflict), EventDecision.CONFLICT
            )
            equal_recovery = replace(
                second_conflict,
                event_id="equal-boundary-terminal-recovery",
                event_time_ms=200,
                transaction_time_ms=210,
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-boundary-terminal-anchor", 210, equal_recovery)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-boundary-stale-snapshot", 209, None, "c" * 64)
                )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-boundary-fresh-snapshot", 210, None, "d" * 64)
                ),
                ConnectionState.SYNCED,
            )
            self.assertEqual(coordinator.accept_order_list_event(equal_recovery), EventDecision.DUPLICATE)
            self.assertEqual(coordinator.accept_order_list_event(first_recovery), EventDecision.QUARANTINED)
            forward_event = replace(
                equal_recovery,
                event_id="equal-boundary-forward",
                event_time_ms=201,
                transaction_time_ms=211,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(forward_event), EventDecision.QUARANTINED
            )
            self.assertEqual(coordinator.state, ConnectionState.SYNCED)
            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_post_gap_equal_boundary_repeated_recovery_conflict_requires_reentry(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            base = self.user_data_event(event_id="equal-reentry-base", at=200)
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-reentry-base-anchor", 200, base)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-reentry-base-snapshot", 200, None, "a" * 64)
                ),
                ConnectionState.SYNCED,
            )

            first_conflict = replace(base, list_status="REJECT", list_order_status="REJECT")
            self.assertEqual(
                coordinator.accept_order_list_event(first_conflict), EventDecision.CONFLICT
            )
            first_recovery = replace(
                first_conflict,
                event_id="equal-reentry-first-recovery",
                event_time_ms=200,
                transaction_time_ms=210,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-reentry-first-anchor", 210, first_recovery)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-reentry-first-snapshot", 210, None, "b" * 64)
                ),
                ConnectionState.SYNCED,
            )

            second_conflict = replace(
                first_recovery,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(second_conflict), EventDecision.CONFLICT
            )
            equal_recovery = replace(
                second_conflict,
                event_id="equal-reentry-terminal-recovery",
                event_time_ms=200,
                transaction_time_ms=210,
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-reentry-terminal-anchor", 210, equal_recovery)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-reentry-terminal-snapshot", 210, None, "c" * 64)
                ),
                ConnectionState.SYNCED,
            )

            reentry_conflict = replace(
                equal_recovery,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(reentry_conflict), EventDecision.CONFLICT
            )
            self.assertEqual(coordinator.state, ConnectionState.GAP)
            with self.assertRaisesRegex(ReconciliationError, "SYNC_STATE_INVALID"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-reentry-blocked-snapshot", 210, None, "d" * 64)
                )

            final_recovery = replace(
                reentry_conflict,
                event_id="equal-reentry-final-recovery",
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-reentry-final-anchor", 210, final_recovery)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-reentry-stale-snapshot", 209, None, "e" * 64)
                )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("equal-reentry-final-snapshot", 210, None, "f" * 64)
                ),
                ConnectionState.SYNCED,
            )
            self.assertEqual(coordinator.accept_order_list_event(final_recovery), EventDecision.DUPLICATE)
            self.assertEqual(coordinator.accept_order_list_event(equal_recovery), EventDecision.QUARANTINED)
            forward_event = replace(
                final_recovery,
                event_id="equal-reentry-forward",
                event_time_ms=201,
                transaction_time_ms=211,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(forward_event), EventDecision.QUARANTINED
            )
            self.assertEqual(coordinator.state, ConnectionState.SYNCED)
            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_post_gap_multi_cycle_recovery_cursor_freshness_preserves_terminal_quarantine(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            base = self.user_data_event(event_id="multi-cycle-base", at=200)
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("multi-cycle-base-anchor", 200, base)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("multi-cycle-base-snapshot", 200, None, "a" * 64)
                ),
                ConnectionState.SYNCED,
            )

            first_conflict = replace(base, list_status="REJECT", list_order_status="REJECT")
            self.assertEqual(
                coordinator.accept_order_list_event(first_conflict), EventDecision.CONFLICT
            )
            first_recovery = replace(
                first_conflict,
                event_id="multi-cycle-first-recovery",
                event_time_ms=200,
                transaction_time_ms=210,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("multi-cycle-first-anchor", 210, first_recovery)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("multi-cycle-first-stale-snapshot", 209, None, "b" * 64)
                )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("multi-cycle-first-fresh-snapshot", 210, None, "c" * 64)
                ),
                ConnectionState.SYNCED,
            )

            second_conflict = replace(
                first_recovery,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(second_conflict), EventDecision.CONFLICT
            )
            second_recovery = replace(
                second_conflict,
                event_id="multi-cycle-second-recovery",
                event_time_ms=211,
                transaction_time_ms=210,
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("multi-cycle-second-anchor", 211, second_recovery)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("multi-cycle-second-stale-snapshot", 210, None, "d" * 64)
                )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("multi-cycle-second-fresh-snapshot", 211, None, "e" * 64)
                ),
                ConnectionState.SYNCED,
            )
            self.assertEqual(coordinator.accept_order_list_event(second_recovery), EventDecision.DUPLICATE)
            self.assertEqual(coordinator.accept_order_list_event(first_recovery), EventDecision.QUARANTINED)
            forward_event = replace(
                second_recovery,
                event_id="multi-cycle-forward",
                event_time_ms=212,
                transaction_time_ms=211,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(forward_event), EventDecision.QUARANTINED
            )
            self.assertEqual(coordinator.state, ConnectionState.SYNCED)
            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_post_gap_mixed_cursor_equal_boundary_reentry_preserves_terminal_quarantine(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            base = self.user_data_event(event_id="mixed-reentry-base", at=200)
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("mixed-reentry-base-anchor", 200, base)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("mixed-reentry-base-snapshot", 200, None, "a" * 64)
                ),
                ConnectionState.SYNCED,
            )

            first_conflict = replace(base, list_status="REJECT", list_order_status="REJECT")
            self.assertEqual(
                coordinator.accept_order_list_event(first_conflict), EventDecision.CONFLICT
            )
            first_recovery = replace(
                first_conflict,
                event_id="mixed-reentry-first-recovery",
                event_time_ms=200,
                transaction_time_ms=210,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("mixed-reentry-first-anchor", 210, first_recovery)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("mixed-reentry-first-snapshot", 210, None, "b" * 64)
                ),
                ConnectionState.SYNCED,
            )

            second_conflict = replace(
                first_recovery,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(second_conflict), EventDecision.CONFLICT
            )
            terminal_recovery = replace(
                second_conflict,
                event_id="mixed-reentry-terminal-recovery",
                event_time_ms=200,
                transaction_time_ms=211,
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("mixed-reentry-terminal-anchor", 211, terminal_recovery)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("mixed-reentry-stale-snapshot", 210, None, "c" * 64)
                )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("mixed-reentry-terminal-snapshot", 211, None, "d" * 64)
                ),
                ConnectionState.SYNCED,
            )

            reentry_conflict = replace(
                terminal_recovery,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(reentry_conflict), EventDecision.CONFLICT
            )
            self.assertEqual(coordinator.state, ConnectionState.GAP)
            final_recovery = replace(
                reentry_conflict,
                event_id="mixed-reentry-final-recovery",
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("mixed-reentry-final-anchor", 211, final_recovery)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("mixed-reentry-final-stale-snapshot", 210, None, "e" * 64)
                )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot("mixed-reentry-final-snapshot", 211, None, "f" * 64)
                ),
                ConnectionState.SYNCED,
            )
            self.assertEqual(coordinator.accept_order_list_event(final_recovery), EventDecision.DUPLICATE)
            self.assertEqual(coordinator.accept_order_list_event(terminal_recovery), EventDecision.QUARANTINED)
            self.assertEqual(coordinator.accept_order_list_event(reentry_conflict), EventDecision.QUARANTINED)
            forward_event = replace(
                final_recovery,
                event_id="mixed-reentry-forward",
                event_time_ms=201,
                transaction_time_ms=212,
                list_status="EXECUTING",
                list_order_status="EXECUTING",
            )
            self.assertEqual(
                coordinator.accept_order_list_event(forward_event), EventDecision.QUARANTINED
            )
            self.assertEqual(coordinator.state, ConnectionState.SYNCED)
            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_post_gap_mixed_cursor_replacement_conflict_terminal_boundary_parity(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            for case_name, terminal_cursor in (
                ("transaction", (211, 200)),
                ("event", (210, 211)),
            ):
                coordinator = ReconciliationCoordinator()
                self.assertEqual(
                    coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                base = self.user_data_event(event_id=f"mixed-replacement-{case_name}-base", at=200)
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"mixed-replacement-{case_name}-base-anchor", 200, base
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"mixed-replacement-{case_name}-base-snapshot", 200, None, "a" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )

                replacement_conflict = replace(
                    base,
                    list_status="REJECT",
                    list_order_status="REJECT",
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(replacement_conflict), EventDecision.CONFLICT
                )
                terminal_recovery = replace(
                    replacement_conflict,
                    event_id=f"mixed-replacement-{case_name}-terminal-recovery",
                    event_time_ms=terminal_cursor[1],
                    transaction_time_ms=terminal_cursor[0],
                )
                boundary = max(terminal_cursor)
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"mixed-replacement-{case_name}-terminal-anchor", boundary, terminal_recovery
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"mixed-replacement-{case_name}-terminal-stale", boundary - 1, None, "b" * 64
                        )
                    )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"mixed-replacement-{case_name}-terminal-fresh", boundary, None, "c" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )

                replacement_retry = replace(
                    terminal_recovery,
                    list_status="EXECUTING",
                    list_order_status="EXECUTING",
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(replacement_retry), EventDecision.CONFLICT
                )
                self.assertEqual(coordinator.state, ConnectionState.GAP)
                final_recovery = replace(
                    replacement_retry,
                    event_id=f"mixed-replacement-{case_name}-final-recovery",
                    list_status="REJECT",
                    list_order_status="REJECT",
                )
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"mixed-replacement-{case_name}-final-anchor", boundary, final_recovery
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"mixed-replacement-{case_name}-final-stale", boundary - 1, None, "d" * 64
                        )
                    )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"mixed-replacement-{case_name}-final-fresh", boundary, None, "e" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )
                self.assertEqual(coordinator.accept_order_list_event(final_recovery), EventDecision.DUPLICATE)
                self.assertEqual(coordinator.accept_order_list_event(terminal_recovery), EventDecision.QUARANTINED)
                self.assertEqual(coordinator.accept_order_list_event(replacement_retry), EventDecision.QUARANTINED)
                forward_event = replace(
                    final_recovery,
                    event_id=f"mixed-replacement-{case_name}-forward",
                    event_time_ms=terminal_cursor[1] + 1,
                    transaction_time_ms=terminal_cursor[0] + 1,
                    list_status="EXECUTING",
                    list_order_status="EXECUTING",
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(forward_event), EventDecision.QUARANTINED
                )
                self.assertEqual(coordinator.state, ConnectionState.SYNCED)

            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_post_gap_mixed_cursor_replacement_anchor_monotonicity(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            for case_name, recovery_cursor in (
                ("transaction", (211, 199)),
                ("event", (209, 211)),
            ):
                coordinator = ReconciliationCoordinator()
                self.assertEqual(
                    coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                base = self.user_data_event(event_id=f"mixed-anchor-{case_name}-base", at=200)
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(f"mixed-anchor-{case_name}-base", 200, base)
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"mixed-anchor-{case_name}-base-snapshot", 200, None, "a" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )
                replacement_conflict = replace(base, list_status="REJECT", list_order_status="REJECT")
                self.assertEqual(
                    coordinator.accept_order_list_event(replacement_conflict), EventDecision.CONFLICT
                )
                recovery = replace(
                    replacement_conflict,
                    event_id=f"mixed-anchor-{case_name}-recovery",
                    event_time_ms=recovery_cursor[1],
                    transaction_time_ms=recovery_cursor[0],
                )
                boundary = max(recovery_cursor)
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(f"mixed-anchor-{case_name}-recovery", boundary, recovery)
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"mixed-anchor-{case_name}-stale", boundary - 1, None, "b" * 64
                        )
                    )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"mixed-anchor-{case_name}-fresh", boundary, None, "c" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )

                reentry_conflict = replace(
                    recovery,
                    list_status="EXECUTING",
                    list_order_status="EXECUTING",
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(reentry_conflict), EventDecision.CONFLICT
                )
                older_cursor = (recovery_cursor[0] - 1, recovery_cursor[1] - 1)
                older_anchor = replace(
                    reentry_conflict,
                    event_id=f"mixed-anchor-{case_name}-older",
                    event_time_ms=older_cursor[1],
                    transaction_time_ms=older_cursor[0],
                )
                with self.assertRaisesRegex(ReconciliationError, "RESYNC_ANCHOR_STALE"):
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"mixed-anchor-{case_name}-older-anchor", max(older_cursor), older_anchor
                        )
                    )
                final_recovery = replace(
                    reentry_conflict,
                    event_id=f"mixed-anchor-{case_name}-final",
                    list_status="REJECT",
                    list_order_status="REJECT",
                )
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"mixed-anchor-{case_name}-final-anchor", boundary, final_recovery
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"mixed-anchor-{case_name}-final-stale", boundary - 1, None, "d" * 64
                        )
                    )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"mixed-anchor-{case_name}-final-fresh", boundary, None, "e" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )
                self.assertEqual(coordinator.accept_order_list_event(final_recovery), EventDecision.DUPLICATE)
                self.assertEqual(coordinator.accept_order_list_event(recovery), EventDecision.QUARANTINED)
                self.assertEqual(coordinator.accept_order_list_event(reentry_conflict), EventDecision.QUARANTINED)
                forward_event = replace(
                    final_recovery,
                    event_id=f"mixed-anchor-{case_name}-forward",
                    event_time_ms=recovery_cursor[1] + 1,
                    transaction_time_ms=recovery_cursor[0] + 1,
                    list_status="EXECUTING",
                    list_order_status="EXECUTING",
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(forward_event), EventDecision.QUARANTINED
                )
                self.assertEqual(coordinator.state, ConnectionState.SYNCED)

            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_post_gap_mixed_cursor_equal_reentry_terminal_snapshot_parity(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            coordinator = ReconciliationCoordinator()
            self.assertEqual(
                coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            base = self.user_data_event(event_id="equal-reentry-parity-base", at=200)
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-reentry-parity-base-anchor", 200, base)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot(
                        "equal-reentry-parity-base-snapshot", 200, None, "a" * 64
                    )
                ),
                ConnectionState.SYNCED,
            )

            terminal = replace(
                base,
                event_time_ms=199,
                transaction_time_ms=211,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(coordinator.accept_order_list_event(terminal), EventDecision.CONFLICT)
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-reentry-parity-terminal-anchor", 211, terminal)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot(
                        "equal-reentry-parity-terminal-stale", 210, None, "b" * 64
                    )
                )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot(
                        "equal-reentry-parity-terminal-fresh", 211, None, "c" * 64
                    )
                ),
                ConnectionState.SYNCED,
            )

            reentry = replace(terminal, list_status="EXECUTING", list_order_status="EXECUTING")
            self.assertEqual(coordinator.accept_order_list_event(reentry), EventDecision.CONFLICT)
            final = replace(
                reentry,
                event_id="equal-reentry-parity-final",
                list_status="REJECT",
                list_order_status="REJECT",
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-reentry-parity-final-anchor", 211, final)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot(
                        "equal-reentry-parity-final-stale", 210, None, "d" * 64
                    )
                )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot(
                        "equal-reentry-parity-final-fresh", 211, None, "e" * 64
                    )
                ),
                ConnectionState.SYNCED,
            )
            self.assertEqual(coordinator.accept_order_list_event(final), EventDecision.DUPLICATE)

            second_reentry = replace(final, list_status="EXECUTING", list_order_status="EXECUTING")
            self.assertEqual(
                coordinator.accept_order_list_event(second_reentry), EventDecision.CONFLICT
            )
            cross_component = replace(
                second_reentry,
                event_id="equal-reentry-parity-cross-component",
                event_time_ms=211,
                transaction_time_ms=209,
                list_status="REJECT",
                list_order_status="REJECT",
            )
            with self.assertRaisesRegex(ReconciliationError, "RESYNC_ANCHOR_STALE"):
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-reentry-parity-cross-anchor", 211, cross_component)
                )

            forward = replace(
                cross_component,
                event_id="equal-reentry-parity-forward",
                transaction_time_ms=212,
            )
            self.assertEqual(
                coordinator.apply_order_list_resync_anchor(
                    UserDataOrderListResyncAnchor("equal-reentry-parity-forward-anchor", 212, forward)
                ),
                ConnectionState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot(
                        "equal-reentry-parity-forward-stale", 211, None, "f" * 64
                    )
                )
            self.assertEqual(
                coordinator.apply_authoritative_snapshot(
                    AuthoritativeReconciliationSnapshot(
                        "equal-reentry-parity-forward-fresh", 212, None, "1" * 64
                    )
                ),
                ConnectionState.SYNCED,
            )
            self.assertEqual(coordinator.accept_order_list_event(forward), EventDecision.DUPLICATE)
            self.assertEqual(coordinator.accept_order_list_event(final), EventDecision.QUARANTINED)
            self.assertEqual(coordinator.accept_order_list_event(second_reentry), EventDecision.QUARANTINED)
            self.assertEqual(coordinator.state, ConnectionState.SYNCED)
            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_post_gap_mixed_cursor_forward_terminal_duplicate_quarantine_parity(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            for case_name, recovery_cursor, forward_cursor in (
                ("transaction-forward", (211, 199), (212, 211)),
                ("event-forward", (209, 211), (211, 212)),
            ):
                coordinator = ReconciliationCoordinator()
                self.assertEqual(
                    coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                base = self.user_data_event(
                    event_id=f"forward-terminal-{case_name}-base", at=200
                )
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"forward-terminal-{case_name}-base-anchor", 200, base
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"forward-terminal-{case_name}-base-snapshot", 200, None, "a" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )

                replacement_conflict = replace(
                    base, list_status="REJECT", list_order_status="REJECT"
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(replacement_conflict), EventDecision.CONFLICT
                )
                recovery = replace(
                    replacement_conflict,
                    event_id=f"forward-terminal-{case_name}-recovery",
                    event_time_ms=recovery_cursor[1],
                    transaction_time_ms=recovery_cursor[0],
                )
                recovery_boundary = max(recovery_cursor)
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"forward-terminal-{case_name}-recovery-anchor",
                            recovery_boundary,
                            recovery,
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"forward-terminal-{case_name}-recovery-stale",
                            recovery_boundary - 1,
                            None,
                            "b" * 64,
                        )
                    )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"forward-terminal-{case_name}-recovery-fresh",
                            recovery_boundary,
                            None,
                            "c" * 64,
                        )
                    ),
                    ConnectionState.SYNCED,
                )

                reentry = replace(
                    recovery, list_status="EXECUTING", list_order_status="EXECUTING"
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(reentry), EventDecision.CONFLICT
                )
                forward_terminal = replace(
                    reentry,
                    event_id=f"forward-terminal-{case_name}-forward",
                    event_time_ms=forward_cursor[1],
                    transaction_time_ms=forward_cursor[0],
                    list_status="REJECT",
                    list_order_status="REJECT",
                )
                forward_boundary = max(forward_cursor)
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"forward-terminal-{case_name}-forward-anchor",
                            forward_boundary,
                            forward_terminal,
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"forward-terminal-{case_name}-forward-stale",
                            forward_boundary - 1,
                            None,
                            "d" * 64,
                        )
                    )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"forward-terminal-{case_name}-forward-fresh",
                            forward_boundary,
                            None,
                            "e" * 64,
                        )
                    ),
                    ConnectionState.SYNCED,
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(forward_terminal), EventDecision.DUPLICATE
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(recovery), EventDecision.QUARANTINED
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(reentry), EventDecision.QUARANTINED
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(replacement_conflict), EventDecision.QUARANTINED
                )
                self.assertEqual(coordinator.state, ConnectionState.SYNCED)

            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_post_gap_mixed_cursor_forward_terminal_equal_reentry_snapshot_parity(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            for case_name, recovery_cursor, forward_cursor in (
                ("transaction-forward", (211, 199), (212, 211)),
                ("event-forward", (209, 211), (211, 212)),
            ):
                coordinator = ReconciliationCoordinator()
                self.assertEqual(
                    coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                base = self.user_data_event(
                    event_id=f"forward-reentry-{case_name}-base", at=200
                )
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"forward-reentry-{case_name}-base-anchor", 200, base
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"forward-reentry-{case_name}-base-snapshot", 200, None, "a" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )

                replacement_conflict = replace(
                    base, list_status="REJECT", list_order_status="REJECT"
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(replacement_conflict), EventDecision.CONFLICT
                )
                recovery = replace(
                    replacement_conflict,
                    event_id=f"forward-reentry-{case_name}-recovery",
                    event_time_ms=recovery_cursor[1],
                    transaction_time_ms=recovery_cursor[0],
                )
                recovery_boundary = max(recovery_cursor)
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"forward-reentry-{case_name}-recovery-anchor",
                            recovery_boundary,
                            recovery,
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"forward-reentry-{case_name}-recovery-snapshot",
                            recovery_boundary,
                            None,
                            "b" * 64,
                        )
                    ),
                    ConnectionState.SYNCED,
                )

                reentry = replace(
                    recovery,
                    list_status="EXECUTING",
                    list_order_status="EXECUTING",
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(reentry), EventDecision.CONFLICT
                )
                forward_terminal = replace(
                    reentry,
                    event_id=f"forward-reentry-{case_name}-terminal",
                    event_time_ms=forward_cursor[1],
                    transaction_time_ms=forward_cursor[0],
                    list_status="REJECT",
                    list_order_status="REJECT",
                )
                forward_boundary = max(forward_cursor)
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"forward-reentry-{case_name}-terminal-anchor",
                            forward_boundary,
                            forward_terminal,
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"forward-reentry-{case_name}-terminal-stale",
                            forward_boundary - 1,
                            None,
                            "c" * 64,
                        )
                    )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"forward-reentry-{case_name}-terminal-fresh",
                            forward_boundary,
                            None,
                            "d" * 64,
                        )
                    ),
                    ConnectionState.SYNCED,
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(forward_terminal), EventDecision.DUPLICATE
                )

                equal_reentry = replace(
                    forward_terminal,
                    list_status="EXECUTING",
                    list_order_status="EXECUTING",
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(equal_reentry), EventDecision.CONFLICT
                )
                equal_terminal = replace(
                    equal_reentry,
                    event_id=f"forward-reentry-{case_name}-equal-terminal",
                    list_status="REJECT",
                    list_order_status="REJECT",
                )
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"forward-reentry-{case_name}-equal-anchor",
                            forward_boundary,
                            equal_terminal,
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"forward-reentry-{case_name}-equal-stale",
                            forward_boundary - 1,
                            None,
                            "e" * 64,
                        )
                    )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"forward-reentry-{case_name}-equal-fresh",
                            forward_boundary,
                            None,
                            "f" * 64,
                        )
                    ),
                    ConnectionState.SYNCED,
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(equal_terminal), EventDecision.DUPLICATE
                )
                repeated_conflict = replace(
                    equal_terminal,
                    list_status="EXECUTING",
                    list_order_status="EXECUTING",
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(repeated_conflict), EventDecision.CONFLICT
                )
                self.assertEqual(coordinator.state, ConnectionState.GAP)
                repeated_terminal = replace(
                    repeated_conflict,
                    event_id=f"forward-reentry-{case_name}-repeated-terminal",
                    list_status="REJECT",
                    list_order_status="REJECT",
                )
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"forward-reentry-{case_name}-repeated-anchor",
                            forward_boundary,
                            repeated_terminal,
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"forward-reentry-{case_name}-repeated-stale",
                            forward_boundary - 1,
                            None,
                            "2" * 64,
                        )
                    )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"forward-reentry-{case_name}-repeated-fresh",
                            forward_boundary,
                            None,
                            "3" * 64,
                        )
                    ),
                    ConnectionState.SYNCED,
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(repeated_terminal), EventDecision.DUPLICATE
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(equal_reentry), EventDecision.QUARANTINED
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(repeated_conflict), EventDecision.QUARANTINED
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(equal_terminal), EventDecision.QUARANTINED
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(reentry), EventDecision.QUARANTINED
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(forward_terminal), EventDecision.QUARANTINED
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(replacement_conflict), EventDecision.QUARANTINED
                )
                self.assertEqual(coordinator.state, ConnectionState.SYNCED)

            self.assertEqual(reopened.load_user_data_events(), ())

    def test_empty_reopen_post_gap_mixed_cursor_repeated_conflict_old_anchor_stays_stale_before_final_replay(self):
        with OrderListEventStore.create(self.path, self.identity):
            pass
        with OrderListEventStore.open(self.path) as reopened:
            for case_name, recovery_cursor, old_cursor in (
                ("transaction-forward", (211, 199), (210, 212)),
                ("event-forward", (209, 211), (208, 212)),
            ):
                coordinator = ReconciliationCoordinator()
                self.assertEqual(
                    coordinator.hydrate_order_list_continuity(reopened.load_user_data_events()),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                base = self.user_data_event(event_id=f"repeated-mixed-{case_name}-base", at=200)
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(f"repeated-mixed-{case_name}-base-anchor", 200, base)
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"repeated-mixed-{case_name}-base-snapshot", 200, None, "a" * 64
                        )
                    ),
                    ConnectionState.SYNCED,
                )

                first_conflict = replace(base, list_status="REJECT", list_order_status="REJECT")
                self.assertEqual(
                    coordinator.accept_order_list_event(first_conflict), EventDecision.CONFLICT
                )
                recovery = replace(
                    first_conflict,
                    event_id=f"repeated-mixed-{case_name}-recovery",
                    event_time_ms=recovery_cursor[1],
                    transaction_time_ms=recovery_cursor[0],
                    list_status="EXECUTING",
                    list_order_status="EXECUTING",
                )
                recovery_boundary = max(recovery_cursor)
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"repeated-mixed-{case_name}-recovery-anchor",
                            recovery_boundary,
                            recovery,
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"repeated-mixed-{case_name}-recovery-snapshot",
                            recovery_boundary,
                            None,
                            "b" * 64,
                        )
                    ),
                    ConnectionState.SYNCED,
                )

                repeated_conflict = replace(
                    recovery,
                    list_status="REJECT",
                    list_order_status="REJECT",
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(repeated_conflict), EventDecision.CONFLICT
                )
                self.assertEqual(coordinator.state, ConnectionState.GAP)
                old_anchor_event = replace(
                    repeated_conflict,
                    event_id=f"repeated-mixed-{case_name}-old-anchor",
                    event_time_ms=old_cursor[1],
                    transaction_time_ms=old_cursor[0],
                )
                with self.assertRaisesRegex(ReconciliationError, "RESYNC_ANCHOR_STALE"):
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"repeated-mixed-{case_name}-old-anchor",
                            max(old_cursor),
                            old_anchor_event,
                        )
                    )
                self.assertEqual(coordinator.state, ConnectionState.GAP)

                final_recovery = replace(
                    repeated_conflict,
                    event_id=f"repeated-mixed-{case_name}-final-recovery",
                )
                self.assertEqual(
                    coordinator.apply_order_list_resync_anchor(
                        UserDataOrderListResyncAnchor(
                            f"repeated-mixed-{case_name}-final-anchor",
                            recovery_boundary,
                            final_recovery,
                        )
                    ),
                    ConnectionState.RECONCILIATION_REQUIRED,
                )
                with self.assertRaisesRegex(ReconciliationError, "SNAPSHOT_STALE"):
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"repeated-mixed-{case_name}-final-stale",
                            recovery_boundary - 1,
                            None,
                            "c" * 64,
                        )
                    )
                self.assertEqual(
                    coordinator.apply_authoritative_snapshot(
                        AuthoritativeReconciliationSnapshot(
                            f"repeated-mixed-{case_name}-final-fresh",
                            recovery_boundary,
                            None,
                            "d" * 64,
                        )
                    ),
                    ConnectionState.SYNCED,
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(final_recovery), EventDecision.DUPLICATE
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(old_anchor_event), EventDecision.QUARANTINED
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(repeated_conflict), EventDecision.QUARANTINED
                )
                self.assertEqual(
                    coordinator.accept_order_list_event(recovery), EventDecision.QUARANTINED
                )
                self.assertEqual(coordinator.state, ConnectionState.SYNCED)

            self.assertEqual(reopened.load_user_data_events(), ())

    def test_reopen_preserves_equal_transaction_cursor_order(self):
        first = replace(
            self.user_data_event(event_id="list:42:120:123", at=120),
            event_time_ms=120,
            transaction_time_ms=123,
        )
        second = replace(
            self.user_data_event(event_id="list:42:130:133", at=130),
            event_time_ms=130,
            transaction_time_ms=123,
        )
        same_transaction_late = replace(
            self.user_data_event(event_id="list:42:125:128", at=125),
            event_time_ms=125,
            transaction_time_ms=123,
        )
        forward = replace(
            self.user_data_event(event_id="list:42:140:143", at=140),
            event_time_ms=140,
            transaction_time_ms=123,
        )
        with OrderListEventStore.create(self.path, self.identity) as store:
            store.append_user_data_event(first)
            store.append_user_data_event(second)
        with OrderListEventStore.open(self.path) as reopened:
            list_events = reopened.load_user_data_events()

        coordinator = ReconciliationCoordinator()
        self.assertEqual(
            coordinator.hydrate_order_list_continuity(list_events),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(
                UserDataOrderListResyncAnchor("equal-tx-anchor", 150, second)
            ),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(
                AuthoritativeReconciliationSnapshot("equal-tx-snapshot", 150, None, "a" * 64)
            ),
            ConnectionState.SYNCED,
        )
        self.assertEqual(
            coordinator.accept_order_list_event(same_transaction_late),
            EventDecision.OUT_OF_ORDER,
        )
        self.assertEqual(coordinator.state, ConnectionState.GAP)
        self.assertEqual(
            coordinator.accept_order_list_event(forward),
            EventDecision.QUARANTINED,
        )

    def test_reopen_prioritizes_transaction_time_over_regressed_event_time(self):
        first = replace(
            self.user_data_event(event_id="mixed:123:140", at=140),
            event_time_ms=140,
            transaction_time_ms=123,
        )
        second = replace(
            self.user_data_event(event_id="mixed:124:100", at=100),
            event_time_ms=100,
            transaction_time_ms=124,
        )
        same_transaction_late = replace(
            self.user_data_event(event_id="mixed:124:090", at=90),
            event_time_ms=90,
            transaction_time_ms=124,
        )
        forward = replace(
            self.user_data_event(event_id="mixed:125:010", at=10),
            event_time_ms=10,
            transaction_time_ms=125,
        )
        with OrderListEventStore.create(self.path, self.identity) as store:
            store.append_user_data_event(first)
            store.append_user_data_event(second)
        with OrderListEventStore.open(self.path) as reopened:
            list_events = reopened.load_user_data_events()

        coordinator = ReconciliationCoordinator()
        self.assertEqual(
            coordinator.hydrate_order_list_continuity(list_events),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(
                UserDataOrderListResyncAnchor("mixed-tx-anchor", 150, second)
            ),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(
                AuthoritativeReconciliationSnapshot("mixed-tx-snapshot", 150, None, "a" * 64)
            ),
            ConnectionState.SYNCED,
        )
        self.assertEqual(
            coordinator.accept_order_list_event(same_transaction_late),
            EventDecision.OUT_OF_ORDER,
        )
        self.assertEqual(coordinator.state, ConnectionState.GAP)
        self.assertEqual(
            coordinator.accept_order_list_event(forward),
            EventDecision.QUARANTINED,
        )

    def test_repeated_sqlite_hydration_is_deterministic_and_quarantines_duplicates(self):
        first = self.user_data_event()
        second = self.user_data_event(event_id="list:42:130:133", at=130)
        with OrderListEventStore.create(self.path, self.identity) as store:
            store.append_user_data_event(first)
            store.append_user_data_event(second)
        with OrderListEventStore.open(self.path) as reopened:
            list_events = reopened.load_user_data_events()

        coordinator = ReconciliationCoordinator()
        self.assertEqual(
            coordinator.hydrate_order_list_continuity(list_events),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.hydrate_order_list_continuity(list_events),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(coordinator.accept_order_list_event(second), EventDecision.QUARANTINED)
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(
                UserDataOrderListResyncAnchor("repeat-anchor", 150, second)
            ),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(
                AuthoritativeReconciliationSnapshot("repeat-snapshot", 150, None, "a" * 64)
            ),
            ConnectionState.SYNCED,
        )
        self.assertEqual(coordinator.accept_order_list_event(second), EventDecision.DUPLICATE)
        self.assertEqual(
            coordinator.accept_order_list_event(
                self.user_data_event(event_id="list:42:160:163", at=160)
            ),
            EventDecision.ACCEPTED,
        )

    def test_hydrated_cursor_is_quarantined_after_disconnect_and_reconnect_until_resync(self):
        first = self.user_data_event()
        second = self.user_data_event(event_id="list:42:130:133", at=130)
        with OrderListEventStore.create(self.path, self.identity) as store:
            store.append_user_data_event(first)
            store.append_user_data_event(second)
        with OrderListEventStore.open(self.path) as reopened:
            list_events = reopened.load_user_data_events()

        coordinator = ReconciliationCoordinator()
        self.assertEqual(
            coordinator.hydrate_order_list_continuity(list_events),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(
                UserDataOrderListResyncAnchor("disconnect-anchor", 150, second)
            ),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(
                AuthoritativeReconciliationSnapshot("disconnect-snapshot", 150, None, "a" * 64)
            ),
            ConnectionState.SYNCED,
        )
        self.assertEqual(coordinator.on_disconnect(), ConnectionState.STALE)
        self.assertEqual(coordinator.reconnect(), ConnectionState.RECONCILIATION_REQUIRED)
        self.assertEqual(coordinator.accept_order_list_event(second), EventDecision.QUARANTINED)
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(
                UserDataOrderListResyncAnchor("reconnect-anchor", 160, second)
            ),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(
                AuthoritativeReconciliationSnapshot("reconnect-snapshot", 160, None, "b" * 64)
            ),
            ConnectionState.SYNCED,
        )
        self.assertEqual(coordinator.accept_order_list_event(second), EventDecision.DUPLICATE)
        self.assertEqual(
            coordinator.accept_order_list_event(
                self.user_data_event(event_id="list:42:170:173", at=170)
            ),
            EventDecision.ACCEPTED,
        )

    def test_recovery_distinguishes_duplicate_from_late_event_and_quarantines_forward(self):
        first = self.user_data_event()
        second = self.user_data_event(event_id="list:42:130:133", at=130)
        late = self.user_data_event(event_id="list:42:110:113", at=110)
        forward = self.user_data_event(event_id="list:42:140:143", at=140)
        with OrderListEventStore.create(self.path, self.identity) as store:
            store.append_user_data_event(first)
            store.append_user_data_event(second)
        with OrderListEventStore.open(self.path) as reopened:
            replay = reopened.load_user_data_events()

        coordinator = ReconciliationCoordinator()
        self.assertEqual(
            coordinator.hydrate_order_list_continuity(replay),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(
                UserDataOrderListResyncAnchor("normal-recovery-anchor", 150, second)
            ),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(
                AuthoritativeReconciliationSnapshot("normal-recovery-snapshot", 150, None, "a" * 64)
            ),
            ConnectionState.SYNCED,
        )
        self.assertEqual(coordinator.accept_order_list_event(second), EventDecision.DUPLICATE)
        self.assertEqual(coordinator.accept_order_list_event(late), EventDecision.OUT_OF_ORDER)
        self.assertEqual(coordinator.state, ConnectionState.GAP)
        self.assertEqual(coordinator.accept_order_list_event(forward), EventDecision.QUARANTINED)

    def test_user_data_hydration_rejects_late_record_after_terminal_replay(self):
        first = self.user_data_event()
        terminal = UserDataOrderListEvent(
            "list:42:121:124",
            124,
            121,
            "BTCUSDT",
            42,
            "OCO",
            "ALL_DONE",
            "ALL_DONE",
            "list-42",
            first.orders,
        )
        with OrderListEventStore.create(self.path, self.identity) as store:
            store.append_user_data_event(first)
            store.append_user_data_event(terminal)
        with OrderListEventStore.open(self.path) as reopened:
            self.assertEqual(reopened.load_user_data_events(), (first, terminal))

        late = UserDataOrderListEvent(
            "list:42:130:133",
            133,
            130,
            "BTCUSDT",
            42,
            "OCO",
            "ALL_DONE",
            "ALL_DONE",
            "list-42",
            first.orders,
        )
        payload = json.dumps(
            {
                "contingency_type": late.contingency_type,
                "event_id": late.event_id,
                "event_time_ms": late.event_time_ms,
                "list_client_order_id": late.list_client_order_id,
                "list_order_status": late.list_order_status.value,
                "list_status": late.list_status.value,
                "order_list_id": late.order_list_id,
                "orders": [
                    {
                        "client_order_id": order.client_order_id,
                        "order_id": order.order_id,
                        "symbol": order.symbol,
                    }
                    for order in late.orders
                ],
                "symbol": late.symbol,
                "transaction_time_ms": late.transaction_time_ms,
                "observation_type": "USER_STREAM_LIST_STATUS",
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        db = sqlite3.connect(self.path)
        try:
            db.execute(
                "INSERT INTO order_list_event_observations("
                "sequence, observation_id, observation_type, observed_at_ms, "
                "observation_payload, observation_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (3, late.event_id, "USER_STREAM_LIST_STATUS", late.transaction_time_ms, payload, payload_hash),
            )
            db.commit()
        finally:
            db.close()

        with self.assertRaisesRegex(OrderListEventStoreError, "ORDER_LIST_TERMINAL_EVENT"):
            OrderListEventStore.open(self.path)

    def test_reopen_terminal_duplicate_is_idempotent_and_new_event_is_rejected(self):
        first = self.user_data_event()
        terminal = replace(
            first,
            event_id="terminal-reopen",
            event_time_ms=124,
            transaction_time_ms=121,
            list_status="ALL_DONE",
            list_order_status="ALL_DONE",
        )
        following = replace(
            terminal,
            event_id="terminal-following",
            event_time_ms=125,
            transaction_time_ms=122,
        )
        with OrderListEventStore.create(self.path, self.identity) as store:
            store.append_user_data_event(first)
            store.append_user_data_event(terminal)
        with OrderListEventStore.open(self.path) as reopened:
            self.assertEqual(
                reopened.append_user_data_event(terminal),
                OrderListJournalRecordOutcome.DUPLICATE,
            )
            with self.assertRaisesRegex(OrderListEventStoreError, "ORDER_LIST_TERMINAL_EVENT"):
                reopened.append_user_data_event(following)
            self.assertEqual(reopened.load_user_data_events(), (first, terminal))

    def test_terminal_conflict_and_restart_snapshot_remain_parity(self):
        first = self.user_data_event()
        terminal = replace(
            first,
            event_id="terminal-parity",
            event_time_ms=124,
            transaction_time_ms=121,
            list_status="ALL_DONE",
            list_order_status="ALL_DONE",
        )
        conflict = replace(
            terminal,
            list_status="EXEC_STARTED",
            list_order_status="EXECUTING",
        )
        with OrderListEventStore.create(self.path, self.identity) as store:
            store.append_user_data_event(first)
            store.append_user_data_event(terminal)
        with OrderListEventStore.open(self.path) as reopened:
            self.assertEqual(reopened.append_user_data_event(terminal), OrderListJournalRecordOutcome.DUPLICATE)
            with self.assertRaisesRegex(OrderListEventStoreError, "ORDER_LIST_EVENT_CONFLICT"):
                reopened.append_user_data_event(conflict)
            expected = (first, terminal)
            self.assertEqual(reopened.load_user_data_events(), expected)
        with OrderListEventStore.open(self.path) as restarted:
            self.assertEqual(restarted.load_user_data_events(), expected)

        coordinator = ReconciliationCoordinator()
        self.assertEqual(
            coordinator.hydrate_order_list_continuity(expected),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(
                UserDataOrderListResyncAnchor("terminal-parity-anchor", 150, terminal)
            ),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(
                AuthoritativeReconciliationSnapshot("terminal-parity-snapshot", 150, None, "a" * 64)
            ),
            ConnectionState.SYNCED,
        )
        self.assertEqual(coordinator.accept_order_list_event(terminal), EventDecision.DUPLICATE)
        self.assertEqual(coordinator.accept_order_list_event(conflict), EventDecision.CONFLICT)
        self.assertEqual(coordinator.state, ConnectionState.GAP)

    def test_terminal_replay_stays_terminal_across_reconnect_and_resync(self):
        first = self.user_data_event()
        terminal = UserDataOrderListEvent(
            "list:42:121:124",
            124,
            121,
            "BTCUSDT",
            42,
            "OCO",
            "ALL_DONE",
            "ALL_DONE",
            "list-42",
            first.orders,
        )
        late = UserDataOrderListEvent(
            "list:42:130:133",
            133,
            130,
            "BTCUSDT",
            42,
            "OCO",
            "ALL_DONE",
            "ALL_DONE",
            "list-42",
            first.orders,
        )
        terminal_conflict = UserDataOrderListEvent(
            "list:42:121:124",
            124,
            121,
            "BTCUSDT",
            42,
            "OCO",
            "EXEC_STARTED",
            "EXECUTING",
            "list-42",
            first.orders,
        )
        with OrderListEventStore.create(self.path, self.identity) as store:
            store.append_user_data_event(first)
            store.append_user_data_event(terminal)
        with OrderListEventStore.open(self.path) as reopened:
            replay = reopened.load_user_data_events()

        coordinator = ReconciliationCoordinator()
        self.assertEqual(
            coordinator.hydrate_order_list_continuity(replay),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(
                UserDataOrderListResyncAnchor("terminal-anchor", 150, terminal)
            ),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(
                AuthoritativeReconciliationSnapshot("terminal-snapshot", 150, None, "a" * 64)
            ),
            ConnectionState.SYNCED,
        )
        self.assertEqual(coordinator.on_disconnect(), ConnectionState.STALE)
        self.assertEqual(coordinator.reconnect(), ConnectionState.RECONCILIATION_REQUIRED)
        self.assertEqual(coordinator.accept_order_list_event(late), EventDecision.QUARANTINED)
        self.assertEqual(
            coordinator.apply_order_list_resync_anchor(
                UserDataOrderListResyncAnchor("terminal-reconnect-anchor", 160, terminal)
            ),
            ConnectionState.RECONCILIATION_REQUIRED,
        )
        self.assertEqual(
            coordinator.apply_authoritative_snapshot(
                AuthoritativeReconciliationSnapshot("terminal-reconnect-snapshot", 160, None, "b" * 64)
            ),
            ConnectionState.SYNCED,
        )
        self.assertEqual(coordinator.accept_order_list_event(terminal), EventDecision.DUPLICATE)
        self.assertEqual(coordinator.accept_order_list_event(terminal_conflict), EventDecision.CONFLICT)
        self.assertEqual(coordinator.state, ConnectionState.GAP)
        self.assertEqual(coordinator.accept_order_list_event(late), EventDecision.QUARANTINED)


if __name__ == "__main__":
    unittest.main()
