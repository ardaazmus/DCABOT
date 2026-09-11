"""Offline reconciliation state machine for restart and stream recovery."""

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import re
from typing import Protocol

from dcabot.application.order_attempt import AttemptState, OrderAttempt, OrderAttemptError
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


class ReconciliationCoordinator:
    """Keep venue connectivity, event continuity, and economic synchronization separate."""

    def __init__(self, store: AttemptStore | None = None):
        self.store = store
        self.state = ConnectionState.DISCONNECTED
        self._seen_events: dict[str, str] = {}
        self._last_event_time_ms: int | None = None
        self._reset_pending = False

    def begin_connect(self) -> ConnectionState:
        self.state = ConnectionState.CONNECTING
        return self.state

    def public_snapshot_ready(self) -> ConnectionState:
        self.state = ConnectionState.CONNECTED_READ_ONLY
        return self.state

    def startup(self, *, now_us: int) -> tuple[OrderAttempt, ...]:
        if self.store is None:
            raise ReconciliationError("ATTEMPT_STORE_REQUIRED", "Restart recovery için durable store gerekir.")
        self.begin_connect()
        recovered = self.store.recover_after_restart(now_us=now_us)
        self.state = ConnectionState.RECONCILIATION_REQUIRED
        return recovered

    def on_disconnect(self) -> ConnectionState:
        self.state = ConnectionState.STALE
        return self.state

    def reconnect(self) -> ConnectionState:
        self.begin_connect()
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
        return EventDecision.ACCEPTED

    def compare_event_with_lookup(
        self, event: UserDataEvent, lookup: OrderLookup
    ) -> EventDecision:
        """Quarantine a stream/REST identity disagreement instead of choosing one."""

        if not isinstance(lookup, OrderLookup):
            raise ReconciliationError("LOOKUP_RESULT_INVALID", "REST lookup sonucu güvenli tipte değil.")
        if lookup.kind is LookupKind.FOUND and lookup.venue_order_id == event.venue_order_id:
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

    def mark_synced(self, *, authoritative_snapshot: bool) -> ConnectionState:
        if self.state is not ConnectionState.RECONCILIATION_REQUIRED:
            raise ReconciliationError("SYNC_STATE_INVALID", "SYNCED yalnız reconciliation sonrasında verilebilir.")
        if authoritative_snapshot is not True:
            raise ReconciliationError(
                "AUTHORITATIVE_SNAPSHOT_REQUIRED", "SYNCED için authoritative REST snapshot gerekir."
            )
        if self._reset_pending:
            raise ReconciliationError(
                "RESET_REVALIDATION_REQUIRED", "Testnet reset sonrası yeni snapshot doğrulanmalıdır."
            )
        if self.store is not None and self.store.count_blocking_attempts() > 0:
            raise ReconciliationError(
                "UNRESOLVED_ATTEMPTS", "Çözülmemiş attempt varken ekonomik state SYNCED olamaz."
            )
        self.state = ConnectionState.SYNCED
        return self.state

    def stream_terminated(self) -> ConnectionState:
        self.state = ConnectionState.STALE
        return self.state

    def testnet_reset_detected(self) -> ConnectionState:
        self._seen_events.clear()
        self._last_event_time_ms = None
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
