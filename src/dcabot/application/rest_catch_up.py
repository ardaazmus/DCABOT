"""REST catch-up: resolve blocking order attempts via a real signed lookup.

After a User Data Stream gap or restart, some attempts sit UNKNOWN or
RECONCILING with no confirmed venue outcome. This module resolves each one
through a read-only signed WebSocket-API order-status query (never a mutating
request), then applies an authoritative snapshot so the connection can reach
SYNCED. It never places, amends, or cancels an order.
"""

from dataclasses import dataclass
import hashlib
import json
from typing import Callable
from uuid import uuid4

from websockets.asyncio.client import connect

from dcabot.application.credential_boundary import CredentialProvider
from dcabot.application.order_attempt import OrderAttempt
from dcabot.application.reconciliation import (
    AuthoritativeReconciliationSnapshot,
    ConnectionState,
    OrderLookup,
    ReconciliationCoordinator,
    ReconciliationError,
)
from dcabot.application.signed_request import Clock
from dcabot.data_adapters.binance_testnet_user_stream import (
    BinanceTestnetUserStreamError,
    WebSocketFactory,
    query_binance_testnet_order_status,
    query_binance_testnet_order_status_by_client_id,
)
from dcabot.persistence.attempt_store import AttemptStore


class RestCatchUpError(ReconciliationError):
    """Raised when a REST catch-up pass cannot safely reach SYNCED."""


@dataclass(frozen=True, slots=True)
class _PrefetchedOrderQuery:
    """Adapt one already-awaited OrderLookup to the synchronous OrderQuery protocol."""

    lookup: OrderLookup

    def find_order(self, attempt: OrderAttempt) -> OrderLookup:
        return self.lookup


async def lookup_attempt_via_testnet(
    attempt: OrderAttempt,
    *,
    credential_id: str,
    provider: CredentialProvider,
    clock: Clock,
    websocket_factory: WebSocketFactory = connect,
    request_id_factory: Callable[[], str] = lambda: str(uuid4()),
) -> OrderLookup:
    """Resolve one attempt's real venue outcome; never raises for a routine miss.

    Prefers the venue order ID when the attempt already has one (a normal
    fill/reject path that only lost its acknowledgement); falls back to the
    client order ID for a send that never got a response at all, since that
    is the only identity such an attempt carries. A `-2013 order does not
    exist` venue response resolves to NOT_FOUND rather than an exception —
    that is an expected reconciliation outcome, not a transport failure.
    """

    try:
        if attempt.venue_order_id is not None:
            return await query_binance_testnet_order_status(
                credential_id,
                attempt.symbol,
                attempt.venue_order_id,
                provider=provider,
                clock=clock,
                websocket_factory=websocket_factory,
                request_id_factory=request_id_factory,
            )
        if attempt.client_order_id is not None:
            return await query_binance_testnet_order_status_by_client_id(
                credential_id,
                attempt.symbol,
                attempt.client_order_id,
                provider=provider,
                clock=clock,
                websocket_factory=websocket_factory,
                request_id_factory=request_id_factory,
            )
    except BinanceTestnetUserStreamError as exc:
        raise RestCatchUpError(
            "CATCH_UP_LOOKUP_FAILED", f"Attempt {attempt.attempt_id} için REST lookup başarısız."
        ) from exc
    raise RestCatchUpError(
        "CATCH_UP_ATTEMPT_UNIDENTIFIABLE",
        f"Attempt {attempt.attempt_id} ne venue order ID ne client order ID taşıyor.",
    )


async def run_rest_catch_up(
    coordinator: ReconciliationCoordinator,
    store: AttemptStore,
    *,
    credential_id: str,
    provider: CredentialProvider,
    clock: Clock,
    now_us: int,
    websocket_factory: WebSocketFactory = connect,
    request_id_factory: Callable[[], str] = lambda: str(uuid4()),
    snapshot_id_factory: Callable[[], str] = lambda: str(uuid4()),
) -> ConnectionState:
    """Resolve every resolvable blocking attempt, then apply an authoritative
    snapshot. Read-only end to end; issues no mutating venue request.

    Any pre-existing UNRESOLVED attempt (from an earlier failed catch-up)
    keeps this from reaching SYNCED by design — `can_transition` gives
    UNRESOLVED no outgoing edge, so it is a permanent block until an operator
    investigates out of band, not something this pass retries.
    """

    if coordinator.state not in {
        ConnectionState.RECONCILIATION_REQUIRED,
        ConnectionState.GAP,
        ConnectionState.STALE,
    }:
        raise RestCatchUpError(
            "CATCH_UP_STATE_INVALID", "REST catch-up yalnız reconciliation durumunda başlatılabilir."
        )
    resolved: list[tuple[str, OrderLookup]] = []
    for attempt in store.list_resolvable_attempts():
        lookup = await lookup_attempt_via_testnet(
            attempt,
            credential_id=credential_id,
            provider=provider,
            clock=clock,
            websocket_factory=websocket_factory,
            request_id_factory=request_id_factory,
        )
        coordinator.reconcile_attempt(
            attempt.attempt_id, _PrefetchedOrderQuery(lookup), now_us=now_us
        )
        resolved.append((attempt.attempt_id, lookup))
    if store.count_blocking_attempts() > 0:
        raise RestCatchUpError(
            "CATCH_UP_UNRESOLVED_ATTEMPTS",
            "REST catch-up sonrası hâlâ blocking attempt var; SYNCED'e geçilmiyor.",
        )
    snapshot = AuthoritativeReconciliationSnapshot(
        snapshot_id=snapshot_id_factory(),
        observed_at_ms=clock.now_ms(),
        event_cursor=coordinator.last_accepted_event,
        snapshot_fingerprint=_snapshot_fingerprint(resolved, now_us=now_us),
    )
    return coordinator.apply_authoritative_snapshot(snapshot)


def _snapshot_fingerprint(resolved: list[tuple[str, OrderLookup]], *, now_us: int) -> str:
    canonical = json.dumps(
        {
            "now_us": now_us,
            "resolved": sorted(
                (attempt_id, lookup.kind.value, lookup.venue_order_id)
                for attempt_id, lookup in resolved
            ),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
