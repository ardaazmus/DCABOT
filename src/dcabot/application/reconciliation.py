"""Offline reconciliation state machine for restart and stream recovery."""

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import re
from typing import Iterable, Protocol

from dcabot.application.order_attempt import AttemptState, OrderAttempt, OrderAttemptError
from dcabot.application.order_list_contract import (
    OrderListStatus,
    UserDataOrderListEvent,
    UserDataOrderListResyncAnchor,
)
from dcabot.persistence.attempt_store import AttemptStore


class ConnectionState(StrEnum):
    """Connection and synchronization states exposed to the application layer."""

    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    AUTHENTICATING = "AUTHENTICATING"
    SUBSCRIBING = "SUBSCRIBING"
    CONNECTED_READ_ONLY = "CONNECTED_READ_ONLY"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    SYNCED = "SYNCED"
    STALE = "STALE"
    GAP = "GAP"
    UNKNOWN = "UNKNOWN"
    FAILED = "FAILED"


class EventDecision(StrEnum):
    """Admission result for one user-data event without assuming global ordering."""

    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    CONFLICT = "CONFLICT"
    QUARANTINED = "QUARANTINED"


class LookupKind(StrEnum):
    """Result classes returned by the fake or future authoritative REST query."""

    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    UNAVAILABLE = "UNAVAILABLE"
    CONFLICT = "CONFLICT"


class ReconciliationError(OrderAttemptError):
    """Raised when synchronization would violate a fail-closed invariant."""


@dataclass(frozen=True, slots=True)
class OrderLookup:
    """Redacted REST lookup result; it carries no raw response or credentials."""

    kind: LookupKind
    venue_order_id: int | None = None

    def __post_init__(self) -> None:
        try:
            kind = LookupKind(self.kind)
        except (TypeError, ValueError) as exc:
            raise ReconciliationError("LOOKUP_KIND_INVALID", "REST lookup sonucu geçersiz.") from exc
        object.__setattr__(self, "kind", kind)
        if self.venue_order_id is not None and (
            type(self.venue_order_id) is not int or self.venue_order_id < 0
        ):
            raise ReconciliationError("LOOKUP_ORDER_ID_INVALID", "Venue order ID negatif olamaz.")
        if kind is LookupKind.FOUND and self.venue_order_id is None:
            raise ReconciliationError("LOOKUP_ORDER_ID_REQUIRED", "FOUND sonucu order ID taşımalıdır.")
        if kind is not LookupKind.FOUND and self.venue_order_id is not None:
            raise ReconciliationError("LOOKUP_ORDER_ID_UNEXPECTED", "FOUND olmayan sonuç order ID taşıyamaz.")

    @classmethod
    def found(cls, venue_order_id: int) -> "OrderLookup":
        return cls(LookupKind.FOUND, venue_order_id)

    @classmethod
    def not_found(cls) -> "OrderLookup":
        return cls(LookupKind.NOT_FOUND)


class OrderQuery(Protocol):
    """Authoritative query boundary implemented by a fake or signed adapter."""

    def find_order(self, attempt: OrderAttempt) -> OrderLookup: ...


@dataclass(frozen=True, slots=True)
class UserDataEvent:
    """Minimal event identity; raw WebSocket payload is intentionally not retained."""

    event_id: str
    event_time_ms: int
    event_type: str
    venue_order_id: int
    payload_fingerprint: str

    def __post_init__(self) -> None:
        if _IDENTIFIER.fullmatch(self.event_id) is None:
            raise ReconciliationError("EVENT_ID_INVALID", "Event ID güvenli biçimde saklanamaz.")
        if type(self.event_time_ms) is not int or self.event_time_ms < 0:
            raise ReconciliationError("EVENT_TIME_INVALID", "Event zamanı negatif olmayan integer olmalıdır.")
        if _IDENTIFIER.fullmatch(self.event_type) is None:
            raise ReconciliationError("EVENT_TYPE_INVALID", "Event tipi güvenli biçimde saklanamaz.")
        if type(self.venue_order_id) is not int or self.venue_order_id < 0:
            raise ReconciliationError("EVENT_ORDER_ID_INVALID", "Event order ID negatif olamaz.")
        if _SHA256.fullmatch(self.payload_fingerprint) is None:
            raise ReconciliationError("EVENT_HASH_INVALID", "Event fingerprint geçersiz.")

    @classmethod
    def create(
        cls, event_id: str, event_time_ms: int, event_type: str, venue_order_id: int
    ) -> "UserDataEvent":
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "event_id": event_id,
                    "event_time_ms": event_time_ms,
                    "event_type": event_type,
                    "venue_order_id": venue_order_id,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return cls(event_id, event_time_ms, event_type, venue_order_id, fingerprint)


@dataclass(frozen=True, slots=True)
class AuthoritativeReconciliationSnapshot:
    """Redacted snapshot proof required before hydrated state can become synced."""

    snapshot_id: str
    observed_at_ms: int
    event_cursor: UserDataEvent | None
    snapshot_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot_id, str) or _IDENTIFIER.fullmatch(self.snapshot_id) is None:
            raise ReconciliationError(
                "SNAPSHOT_ID_INVALID", "Snapshot ID güvenli biçimde saklanamaz."
            )
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise ReconciliationError(
                "SNAPSHOT_TIME_INVALID", "Snapshot zamanı negatif olmayan integer olmalıdır."
            )
        if self.event_cursor is not None and not isinstance(self.event_cursor, UserDataEvent):
            raise ReconciliationError(
                "SNAPSHOT_CURSOR_INVALID", "Snapshot event cursor güvenli tipte değil."
            )
        if not isinstance(self.snapshot_fingerprint, str) or _SHA256.fullmatch(
            self.snapshot_fingerprint
        ) is None:
            raise ReconciliationError(
                "SNAPSHOT_HASH_INVALID", "Snapshot fingerprint geçersiz."
            )


class ReconciliationCoordinator:
    """Keep venue connectivity, event continuity, and economic synchronization separate."""

    def __init__(self, store: AttemptStore | None = None):
        self.store = store
        self.state = ConnectionState.DISCONNECTED
        self._seen_events: dict[str, str] = {}
        self._last_event_time_ms: int | None = None
        self._last_event_id: str | None = None
        self._last_event: UserDataEvent | None = None
        self._seen_order_list_events: dict[str, str] = {}
        self._last_order_list_cursor: tuple[int, int] | None = None
        self._order_list_terminal = False
        self._order_list_resync_required = False
        self._reset_pending = False
        self._snapshot_required = False

    @property
    def last_accepted_event(self) -> "UserDataEvent | None":
        """The full last ACCEPTED event, for building a real snapshot cursor.

        Read-only; callers must not mutate the coordinator through this.
        """

        return self._last_event

    def begin_connect(self) -> ConnectionState:
        self.state = ConnectionState.CONNECTING
        return self.state

    def public_snapshot_ready(self) -> ConnectionState:
        if self._snapshot_required or self._order_list_resync_required:
            return self.state
        self.state = ConnectionState.CONNECTED_READ_ONLY
        return self.state

    def startup(self, *, now_us: int) -> tuple[OrderAttempt, ...]:
        if self.store is None:
            raise ReconciliationError("ATTEMPT_STORE_REQUIRED", "Restart recovery için durable store gerekir.")
        self.begin_connect()
        recovered = self.store.recover_after_restart(now_us=now_us)
        self.state = ConnectionState.RECONCILIATION_REQUIRED
        return recovered

    def startup_with_durable_recovery(
        self,
        *,
        now_us: int,
        continuity_observations: Iterable[tuple[UserDataEvent, EventDecision, ConnectionState]],
    ) -> tuple[OrderAttempt, ...]:
        """Validate durable event continuity before quarantining in-flight attempts."""

        if self.store is None:
            raise ReconciliationError("ATTEMPT_STORE_REQUIRED", "Restart recovery için durable store gerekir.")
        restored_state = self.hydrate_event_continuity(continuity_observations)
        recovered = self.store.recover_after_restart(now_us=now_us)
        self.state = restored_state
        return recovered

    def reconcile_recovered_attempts(
        self,
        recovered_attempts: Iterable[OrderAttempt],
        query: OrderQuery,
        *,
        now_us: int,
    ) -> tuple[OrderAttempt, ...]:
        """Hand recovered UNKNOWN attempts to the explicit lookup boundary."""

        if self.store is None:
            raise ReconciliationError("ATTEMPT_STORE_REQUIRED", "Reconciliation için durable store gerekir.")
        if self.state not in {
            ConnectionState.RECONCILIATION_REQUIRED,
            ConnectionState.GAP,
            ConnectionState.STALE,
        }:
            raise ReconciliationError(
                "RECONCILIATION_STATE_INVALID", "Attempt yalnız reconciliation durumunda sorgulanabilir."
            )
        if not callable(getattr(query, "find_order", None)):
            raise ReconciliationError("RECONCILIATION_QUERY_INVALID", "Lookup query callable olmalıdır.")
        try:
            items = tuple(recovered_attempts)
        except TypeError as exc:
            raise ReconciliationError(
                "RECOVERY_HANDOFF_INVALID", "Recovered attempt listesi iterable olmalıdır."
            ) from exc
        if len(items) > 1_000:
            raise ReconciliationError(
                "RECOVERY_HANDOFF_LIMIT", "Recovered attempt sınırı aşılamaz."
            )
        attempt_ids: set[str] = set()
        for item in items:
            if not isinstance(item, OrderAttempt):
                raise ReconciliationError(
                    "RECOVERY_HANDOFF_ATTEMPT_INVALID", "Recovered kayıt güvenli attempt tipinde değil."
                )
            if item.state is not AttemptState.UNKNOWN:
                raise ReconciliationError(
                    "RECOVERY_HANDOFF_STATE_INVALID", "Recovery handoff yalnız UNKNOWN attempt kabul eder."
                )
            if item.attempt_id in attempt_ids:
                raise ReconciliationError(
                    "RECOVERY_HANDOFF_DUPLICATE", "Aynı recovered attempt iki kez verilemez."
                )
            attempt_ids.add(item.attempt_id)
        return tuple(
            self.reconcile_attempt(item.attempt_id, query, now_us=now_us)
            for item in items
        )

    def hydrate_event_continuity(
        self,
        observations: Iterable[tuple[UserDataEvent, EventDecision, ConnectionState]],
    ) -> ConnectionState:
        """Restore a validated event cursor without restoring economic sync."""

        seen_events: dict[str, str] = {}
        last_event_time_ms: int | None = None
        last_event_id: str | None = None
        last_event: UserDataEvent | None = None
        restored_state = ConnectionState.RECONCILIATION_REQUIRED
        state_priority = {
            ConnectionState.RECONCILIATION_REQUIRED: 0,
            ConnectionState.STALE: 1,
            ConnectionState.GAP: 2,
            ConnectionState.UNKNOWN: 3,
            ConnectionState.FAILED: 4,
        }
        try:
            iterator = iter(observations)
        except TypeError as exc:
            raise ReconciliationError(
                "HYDRATION_OBSERVATIONS_INVALID", "Hydration gözlemleri iterable olmalıdır."
            ) from exc
        for count, item in enumerate(iterator, start=1):
            if count > 1_000:
                raise ReconciliationError(
                    "HYDRATION_EVENT_LIMIT", "Hydration gözlem sınırı aşılamaz."
                )
            if not isinstance(item, tuple) or len(item) != 3:
                raise ReconciliationError(
                    "HYDRATION_OBSERVATION_INVALID", "Hydration gözlemi üçlü tuple olmalıdır."
                )
            event, decision, state = item
            if not isinstance(event, UserDataEvent):
                raise ReconciliationError(
                    "HYDRATION_EVENT_INVALID", "Hydration event güvenli tipte değil."
                )
            try:
                decision = EventDecision(decision)
                state = ConnectionState(state)
            except (TypeError, ValueError) as exc:
                raise ReconciliationError(
                    "HYDRATION_STATE_INVALID", "Hydration karar/state değeri geçersiz."
                ) from exc
            if decision is EventDecision.ACCEPTED:
                prior_fingerprint = seen_events.get(event.event_id)
                if prior_fingerprint is not None and prior_fingerprint != event.payload_fingerprint:
                    raise ReconciliationError(
                        "HYDRATION_EVENT_CONFLICT", "Hydration aynı event için farklı fingerprint buldu."
                    )
                if last_event_time_ms is not None and event.event_time_ms < last_event_time_ms:
                    raise ReconciliationError(
                        "HYDRATION_EVENT_ORDER", "Hydration event zamanı geriye gidemez."
                    )
                seen_events[event.event_id] = event.payload_fingerprint
                last_event_time_ms = event.event_time_ms
                last_event_id = event.event_id
                last_event = event
            elif decision is EventDecision.DUPLICATE:
                if seen_events.get(event.event_id) != event.payload_fingerprint:
                    raise ReconciliationError(
                        "HYDRATION_DUPLICATE_INVALID", "Hydration duplicate kabul edilmiş event ile eşleşmiyor."
                    )
            elif decision in {EventDecision.CONFLICT, EventDecision.OUT_OF_ORDER}:
                state = ConnectionState.GAP
            if state in state_priority and state_priority[state] > state_priority[restored_state]:
                restored_state = state
        self._seen_events = seen_events
        self._last_event_time_ms = last_event_time_ms
        self._last_event_id = last_event_id
        self._last_event = last_event
        self.state = restored_state
        self._snapshot_required = True
        return self.state

    def hydrate_order_list_continuity(
        self,
        observations: Iterable[UserDataOrderListEvent],
    ) -> ConnectionState:
        """Restore a durable list cursor without restoring authoritative sync."""

        seen_events: dict[str, str] = {}
        last_cursor: tuple[int, int] | None = None
        terminal = False
        try:
            iterator = iter(observations)
        except TypeError as exc:
            raise ReconciliationError(
                "ORDER_LIST_HYDRATION_INVALID", "ListStatus hydration gözlemleri iterable olmalıdır."
            ) from exc
        for count, event in enumerate(iterator, start=1):
            if count > 1_000:
                raise ReconciliationError(
                    "ORDER_LIST_HYDRATION_LIMIT", "ListStatus hydration gözlem sınırı aşılamaz."
                )
            if not isinstance(event, UserDataOrderListEvent):
                raise ReconciliationError(
                    "ORDER_LIST_HYDRATION_EVENT_INVALID",
                    "ListStatus hydration yalnız güvenli event tiplerini kabul eder.",
                )
            if terminal:
                raise ReconciliationError(
                    "ORDER_LIST_HYDRATION_TERMINAL",
                    "Terminal listStatus event sonrasında yeni event hydrate edilemez.",
                )
            fingerprint = self._order_list_event_fingerprint(event)
            if event.event_id in seen_events:
                raise ReconciliationError(
                    "ORDER_LIST_HYDRATION_CONFLICT",
                    "ListStatus hydration event kimlikleri tekil olmalıdır.",
                )
            cursor = (event.transaction_time_ms, event.event_time_ms)
            if last_cursor is not None and cursor < last_cursor:
                raise ReconciliationError(
                    "ORDER_LIST_HYDRATION_ORDER",
                    "ListStatus hydration cursor zamanı geriye gidemez.",
                )
            seen_events[event.event_id] = fingerprint
            last_cursor = cursor
            terminal = event.list_status in {OrderListStatus.ALL_DONE, OrderListStatus.REJECT}
        self._seen_order_list_events = seen_events
        self._last_order_list_cursor = last_cursor
        self._order_list_terminal = terminal
        self._order_list_resync_required = last_cursor is not None
        self._snapshot_required = True
        self.state = ConnectionState.RECONCILIATION_REQUIRED
        return self.state

    def on_disconnect(self) -> ConnectionState:
        self._order_list_resync_required = self._last_order_list_cursor is not None
        self.state = ConnectionState.STALE
        return self.state

    def reconnect(self) -> ConnectionState:
        self.begin_connect()
        self._order_list_resync_required = self._last_order_list_cursor is not None
        self.state = ConnectionState.RECONCILIATION_REQUIRED
        return self.state

    def accept_event(self, event: UserDataEvent) -> EventDecision:
        if self.state not in {
            ConnectionState.CONNECTED_READ_ONLY,
            ConnectionState.RECONCILIATION_REQUIRED,
            ConnectionState.SYNCED,
        }:
            return EventDecision.QUARANTINED
        prior_fingerprint = self._seen_events.get(event.event_id)
        if prior_fingerprint is not None:
            if prior_fingerprint == event.payload_fingerprint:
                return EventDecision.DUPLICATE
            self.state = ConnectionState.GAP
            return EventDecision.CONFLICT
        if self._last_event_time_ms is not None and event.event_time_ms < self._last_event_time_ms:
            self.state = ConnectionState.GAP
            return EventDecision.OUT_OF_ORDER
        self._seen_events[event.event_id] = event.payload_fingerprint
        self._last_event_time_ms = event.event_time_ms
        self._last_event_id = event.event_id
        self._last_event = event
        return EventDecision.ACCEPTED

    def accept_order_list_event(self, event: UserDataOrderListEvent) -> EventDecision:
        """Admit redacted listStatus identity without inventing venue sequence."""

        if not isinstance(event, UserDataOrderListEvent):
            raise ReconciliationError(
                "ORDER_LIST_EVENT_INVALID", "User Data Stream order-list olayı güvenli tipte değil."
            )
        if self.state not in {ConnectionState.CONNECTED_READ_ONLY, ConnectionState.SYNCED}:
            return EventDecision.QUARANTINED
        fingerprint = self._order_list_event_fingerprint(event)
        prior_fingerprint = self._seen_order_list_events.get(event.event_id)
        if prior_fingerprint is not None:
            if prior_fingerprint == fingerprint:
                return EventDecision.DUPLICATE
            self._order_list_resync_required = True
            self.state = ConnectionState.GAP
            return EventDecision.CONFLICT
        if self._order_list_terminal:
            return EventDecision.QUARANTINED
        cursor = (event.transaction_time_ms, event.event_time_ms)
        if self._last_order_list_cursor is not None and cursor < self._last_order_list_cursor:
            self._order_list_resync_required = True
            self.state = ConnectionState.GAP
            return EventDecision.OUT_OF_ORDER
        self._seen_order_list_events[event.event_id] = fingerprint
        self._last_order_list_cursor = cursor
        self._order_list_terminal = event.list_status in {OrderListStatus.ALL_DONE, OrderListStatus.REJECT}
        return EventDecision.ACCEPTED

    @staticmethod
    def _order_list_event_fingerprint(event: UserDataOrderListEvent) -> str:
        return hashlib.sha256(
            json.dumps(
                {
                    "event_id": event.event_id,
                    "event_time_ms": event.event_time_ms,
                    "transaction_time_ms": event.transaction_time_ms,
                    "symbol": event.symbol,
                    "order_list_id": event.order_list_id,
                    "contingency_type": event.contingency_type,
                    "list_status": event.list_status.value,
                    "list_order_status": event.list_order_status.value,
                    "list_client_order_id": event.list_client_order_id,
                    "orders": [
                        {
                            "symbol": order.symbol,
                            "order_id": order.order_id,
                            "client_order_id": order.client_order_id,
                        }
                        for order in event.orders
                    ],
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

    def apply_order_list_resync_anchor(
        self, anchor: UserDataOrderListResyncAnchor
    ) -> ConnectionState:
        """Record an offline list cursor; an authoritative snapshot is still required."""

        if not isinstance(anchor, UserDataOrderListResyncAnchor):
            raise ReconciliationError(
                "ORDER_LIST_RESYNC_ANCHOR_REQUIRED", "Geçerli listStatus resync anchor gerekir."
            )
        if self.state not in {
            ConnectionState.RECONCILIATION_REQUIRED,
            ConnectionState.STALE,
            ConnectionState.GAP,
        }:
            raise ReconciliationError(
                "ORDER_LIST_RESYNC_STATE_INVALID",
                "Resync anchor yalnız reconciliation, stale veya gap durumunda uygulanabilir.",
            )
        if self.state is ConnectionState.GAP and not self._order_list_resync_required:
            raise ReconciliationError(
                "ORDER_LIST_RESYNC_STATE_INVALID",
                "Genel event GAP yalnız listStatus anchor ile temizlenemez.",
            )
        if self._reset_pending:
            raise ReconciliationError(
                "RESET_REVALIDATION_REQUIRED", "Testnet reset sonrası yeni snapshot doğrulanmalıdır."
            )
        cursor = (anchor.event.transaction_time_ms, anchor.event.event_time_ms)
        if self._last_order_list_cursor is not None and cursor < self._last_order_list_cursor:
            raise ReconciliationError(
                "RESYNC_ANCHOR_STALE", "Resync anchor mevcut listStatus cursor’dan eski."
            )
        self._seen_order_list_events = {
            anchor.event.event_id: self._order_list_event_fingerprint(anchor.event)
        }
        self._last_order_list_cursor = cursor
        self._order_list_terminal = anchor.event.list_status in {
            OrderListStatus.ALL_DONE,
            OrderListStatus.REJECT,
        }
        self._order_list_resync_required = False
        self._snapshot_required = True
        self.state = ConnectionState.RECONCILIATION_REQUIRED
        return self.state

    def compare_event_with_lookup(
        self, event: UserDataEvent, lookup: OrderLookup
    ) -> EventDecision:
        """Quarantine a stream/REST identity disagreement instead of choosing one."""

        from dcabot.application.venue_event_binding import (
            VenueEventEvidenceOutcome,
            evaluate_venue_event_lookup,
        )

        evidence = evaluate_venue_event_lookup(event, lookup)
        if evidence.outcome is VenueEventEvidenceOutcome.MATCHED:
            return EventDecision.ACCEPTED
        self.state = ConnectionState.GAP
        return EventDecision.CONFLICT

    def apply_freshness(
        self, *, observed_at_ms: int, now_ms: int, max_age_ms: int
    ) -> ConnectionState:
        """Mark a snapshot stale at the inclusive age boundary; never freshen implicitly."""

        for value, code in (
            (observed_at_ms, "OBSERVED_TIME_INVALID"),
            (now_ms, "CURRENT_TIME_INVALID"),
            (max_age_ms, "MAX_AGE_INVALID"),
        ):
            if type(value) is not int or value < 0:
                raise ReconciliationError(code, "Freshness zamanı negatif olmayan integer olmalıdır.")
        if max_age_ms == 0:
            raise ReconciliationError("MAX_AGE_INVALID", "Freshness süresi pozitif olmalıdır.")
        if now_ms < observed_at_ms:
            self.state = ConnectionState.UNKNOWN
            return self.state
        if now_ms - observed_at_ms >= max_age_ms:
            self.state = ConnectionState.STALE
        return self.state

    def reconcile_attempt(
        self, attempt_id: str, query: OrderQuery, *, now_us: int
    ) -> OrderAttempt:
        if self.store is None:
            raise ReconciliationError("ATTEMPT_STORE_REQUIRED", "Reconciliation için durable store gerekir.")
        if self.state not in {
            ConnectionState.RECONCILIATION_REQUIRED,
            ConnectionState.GAP,
            ConnectionState.STALE,
        }:
            raise ReconciliationError(
                "RECONCILIATION_STATE_INVALID", "Attempt yalnız reconciliation durumunda sorgulanabilir."
            )
        current = self.store.get(attempt_id)
        if current.state is AttemptState.UNKNOWN:
            current = self.store.begin_reconciliation(attempt_id, now_us=now_us)
        elif current.state is not AttemptState.RECONCILING:
            raise ReconciliationError(
                "RECONCILIATION_ATTEMPT_STATE", "Attempt UNKNOWN veya RECONCILING olmalıdır."
            )
        lookup = query.find_order(current)
        if not isinstance(lookup, OrderLookup):
            raise ReconciliationError("LOOKUP_RESULT_INVALID", "REST lookup sonucu güvenli tipte değil.")
        if lookup.kind is LookupKind.FOUND:
            return self.store.mark_reconciled_acknowledged(
                attempt_id, now_us=now_us, venue_order_id=lookup.venue_order_id
            )
        return self.store.mark_reconciliation_unresolved(
            attempt_id,
            now_us=now_us,
            reason=f"REST_{lookup.kind.value}",
        )

    def apply_authoritative_snapshot(
        self, snapshot: AuthoritativeReconciliationSnapshot
    ) -> ConnectionState:
        """Validate a redacted snapshot against the hydrated cursor before syncing."""

        if not isinstance(snapshot, AuthoritativeReconciliationSnapshot):
            raise ReconciliationError(
                "AUTHORITATIVE_SNAPSHOT_REQUIRED", "Geçerli authoritative snapshot gerekir."
            )
        if self.state is not ConnectionState.RECONCILIATION_REQUIRED:
            raise ReconciliationError(
                "SYNC_STATE_INVALID", "Snapshot yalnız reconciliation sonrasında uygulanabilir."
            )
        if self._reset_pending:
            raise ReconciliationError(
                "RESET_REVALIDATION_REQUIRED", "Testnet reset sonrası yeni snapshot doğrulanmalıdır."
            )
        if self._order_list_resync_required:
            raise ReconciliationError(
                "ORDER_LIST_RESYNC_ANCHOR_REQUIRED",
                "ListStatus snapshot öncesi explicit resync anchor gerekir.",
            )
        if self._last_event_id is None:
            if snapshot.event_cursor is not None:
                raise ReconciliationError(
                    "SNAPSHOT_CURSOR_MISMATCH", "Snapshot cursor boş hydrated cursor ile eşleşmiyor."
                )
        else:
            cursor = snapshot.event_cursor
            if (
                cursor is None
                or cursor.event_id != self._last_event_id
                or cursor.event_time_ms != self._last_event_time_ms
                or self._seen_events.get(cursor.event_id) != cursor.payload_fingerprint
            ):
                raise ReconciliationError(
                    "SNAPSHOT_CURSOR_MISMATCH", "Authoritative snapshot hydrated cursor ile eşleşmiyor."
                )
        if (
            self._last_event_time_ms is not None
            and snapshot.observed_at_ms < self._last_event_time_ms
        ):
            raise ReconciliationError(
                "SNAPSHOT_STALE", "Authoritative snapshot hydrated event cursor’dan eski."
            )
        if (
            self._last_order_list_cursor is not None
            and snapshot.observed_at_ms < max(self._last_order_list_cursor)
        ):
            raise ReconciliationError(
                "SNAPSHOT_STALE", "Authoritative snapshot order-list cursor’dan eski."
            )
        if self.store is not None and self.store.count_blocking_attempts() > 0:
            raise ReconciliationError(
                "UNRESOLVED_ATTEMPTS", "Çözülmemiş attempt varken ekonomik state SYNCED olamaz."
            )
        self._snapshot_required = False
        self._order_list_resync_required = False
        self.state = ConnectionState.SYNCED
        return self.state

    def mark_synced(self, *, authoritative_snapshot: bool) -> ConnectionState:
        if self.state is not ConnectionState.RECONCILIATION_REQUIRED:
            raise ReconciliationError("SYNC_STATE_INVALID", "SYNCED yalnız reconciliation sonrasında verilebilir.")
        if self._snapshot_required:
            raise ReconciliationError(
                "AUTHORITATIVE_SNAPSHOT_REQUIRED", "Hydration sonrası snapshot nesnesi gerekir."
            )
        if authoritative_snapshot is not True:
            raise ReconciliationError(
                "AUTHORITATIVE_SNAPSHOT_REQUIRED", "SYNCED için authoritative REST snapshot gerekir."
            )
        if self._reset_pending:
            raise ReconciliationError(
                "RESET_REVALIDATION_REQUIRED", "Testnet reset sonrası yeni snapshot doğrulanmalıdır."
            )
        if self._order_list_resync_required:
            raise ReconciliationError(
                "ORDER_LIST_RESYNC_ANCHOR_REQUIRED",
                "SYNCED öncesi explicit listStatus resync anchor gerekir.",
            )
        if self.store is not None and self.store.count_blocking_attempts() > 0:
            raise ReconciliationError(
                "UNRESOLVED_ATTEMPTS", "Çözülmemiş attempt varken ekonomik state SYNCED olamaz."
            )
        self.state = ConnectionState.SYNCED
        return self.state

    def stream_terminated(self) -> ConnectionState:
        self._order_list_resync_required = self._last_order_list_cursor is not None
        self.state = ConnectionState.STALE
        return self.state

    def testnet_reset_detected(self) -> ConnectionState:
        self._seen_events.clear()
        self._last_event_time_ms = None
        self._last_event_id = None
        self._last_event = None
        self._seen_order_list_events.clear()
        self._last_order_list_cursor = None
        self._order_list_terminal = False
        self._order_list_resync_required = False
        self._reset_pending = True
        self.state = ConnectionState.RECONCILIATION_REQUIRED
        return self.state

    def revalidate_after_reset(self, *, authoritative_snapshot: bool) -> ConnectionState:
        """Clear reset quarantine only after a fresh authoritative snapshot is supplied."""

        if self.state is not ConnectionState.RECONCILIATION_REQUIRED:
            raise ReconciliationError(
                "RESET_STATE_INVALID", "Reset revalidation reconciliation durumunda yapılmalıdır."
            )
        if authoritative_snapshot is not True:
            raise ReconciliationError(
                "AUTHORITATIVE_SNAPSHOT_REQUIRED", "Reset sonrası authoritative snapshot gerekir."
            )
        self._reset_pending = False
        return self.state


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,128}\Z", re.ASCII)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
