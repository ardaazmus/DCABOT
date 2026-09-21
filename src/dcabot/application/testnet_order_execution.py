"""Faz 3.4's mutation gate, wired to the one real order-placement transport.

Every rule from docs/KARARLAR.md (2026-09-21, "Faz 3.4 Mutation gate kararı")
is enforced here, in order, before a signed request is ever built:

1. Kill-switch (checked here AND independently inside the transport layer).
2. `max_entry_notional` cap (the same cap `engine.py` already enforces for
   simulated entries) checked again at the mutation boundary.
3. Execution-time confirmation is the CALLER's job (the CLI tool) — this
   module never sends without a `confirmed=True` the caller only sets after
   showing the operator the exact order and getting an explicit yes.
4. Idempotent identity + durable-before-send: every attempt goes through
   `AttemptStore.prepare() -> persist() -> mark_sending()` before signing.
5. Single in-flight/unresolved mutation: refuses to prepare a new attempt
   while any attempt is still between PREPARED and a venue answer, OR while
   any attempt is UNKNOWN/RECONCILING (`_require_no_blocking_attempts`) — a
   transport failure that leaves an attempt's real outcome undetermined must
   block further mutation exactly like an in-flight one, not just fail to
   count as "in-flight" (closed 2026-09-21 after independent review, finding
   F2: it previously only checked PREPARED/PERSISTED/SENDING). UNRESOLVED
   does not block further mutation -- REST catch-up already ran and could
   not confirm placement; see `_require_no_blocking_attempts` docstring.
6. Cancellation goes through the identical discipline: its own durable
   `AttemptStore` identity (`prepare()`/`persist()`/`mark_sending()`), not
   just the kill-switch + confirmation checks (closed 2026-09-21 after
   independent review, finding F1: cancel previously bypassed the store
   entirely).
7. The transport layer's base URL stays hard-coded to Testnet.
"""

from dataclasses import dataclass

from dcabot.application.credential_boundary import CredentialProvider
from dcabot.application.instrument_filters import InstrumentFilterError, InstrumentFilterProfile, validate_order_candidate
from dcabot.application.order_attempt import AttemptOperation, AttemptState, OrderAttempt, request_fingerprint
from dcabot.application.reconciliation import OrderLookup, ReconciliationCoordinator
from dcabot.application.rest_catch_up import lookup_attempt_via_testnet
from dcabot.application.signed_request import Clock
from dcabot.data_adapters.binance_testnet_order_execution import (
    BinanceTestnetOrderExecutionError,
    CancelledTestnetOrder,
    OrderRejectedByVenue,
    PlacedTestnetOrder,
    WebSocketFactory,
    cancel_binance_testnet_order,
    place_binance_testnet_limit_order,
    trading_kill_switch_enabled,
)
from dcabot.domain.numbers import Q, number
from dcabot.persistence.attempt_store import AttemptStore


@dataclass(frozen=True, slots=True)
class _PrefetchedOrderQuery:
    """Adapt one already-awaited OrderLookup to the synchronous OrderQuery protocol."""

    lookup: OrderLookup

    def find_order(self, attempt: OrderAttempt) -> OrderLookup:
        return self.lookup


class TestnetOrderExecutionError(RuntimeError):
    """Raised when the gate refuses a mutation before or after the venue call."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class GatedOrderResult:
    attempt: OrderAttempt
    placed: PlacedTestnetOrder


@dataclass(frozen=True, slots=True)
class GatedCancelResult:
    attempt: OrderAttempt
    cancelled: CancelledTestnetOrder


def _require_no_blocking_attempts(store: AttemptStore) -> None:
    """Rule 5, read broadly: refuse a new mutation while any attempt's real
    venue outcome is still genuinely undetermined -- not just while one is
    physically in-flight (PREPARED/PERSISTED/SENDING), but also while one
    sits UNKNOWN or RECONCILING (`list_resolvable_attempts()`). An UNKNOWN
    attempt is exactly the "we don't know if it went through" case AGENTS.md
    rule 4 forbids blindly retrying past, so it must block here too, not
    just fail to count as in-flight.

    UNRESOLVED is deliberately NOT included: it only exists once a real REST
    lookup already ran and still could not confirm the order (`can_transition`
    gives it no further outgoing edge -- see `reconcile_attempt`). Blocking
    forever on it would regress the already-proven Faz 3.6 REAL_TESTNET
    evidence (a genuinely never-sent attempt resolves to UNRESOLVED and the
    next order proceeds unblocked) for no safety gain: REST catch-up already
    did everything automation can do here, and further blocking would only
    be undone by an operator anyway.
    """

    if store.count_in_flight_attempts() > 0:
        raise TestnetOrderExecutionError(
            "GATE_MUTATION_IN_FLIGHT", "Zaten devam eden bir mutation var; eşzamanlı emir gönderilmez."
        )
    if store.list_resolvable_attempts():
        raise TestnetOrderExecutionError(
            "GATE_MUTATION_UNRESOLVED",
            "Çözülmemiş (UNKNOWN/RECONCILING) bir attempt var; önce recover_stuck_attempts ile çözülmeli.",
        )


async def place_gated_testnet_limit_order(
    *,
    store: AttemptStore,
    run_id: str,
    attempt_id: str,
    client_order_id: str,
    symbol: str,
    side: str,
    quantity: str,
    price: str,
    filter_profile: InstrumentFilterProfile,
    max_entry_notional: Q,
    capability_snapshot_hash: str,
    confirmed: bool,
    credential_id: str,
    provider: CredentialProvider,
    clock: Clock,
    now_us: int,
    websocket_factory: WebSocketFactory | None = None,
    request_id_factory=None,
) -> GatedOrderResult:
    """Place exactly one gated, confirmed LIMIT order. Never called in a loop."""

    if confirmed is not True:
        raise TestnetOrderExecutionError(
            "GATE_CONFIRMATION_REQUIRED",
            "Execution-anında açık onay olmadan hiçbir emir gönderilmez.",
        )
    if not trading_kill_switch_enabled():
        raise TestnetOrderExecutionError(
            "GATE_KILL_SWITCH_OFF", "DCABOT_TRADING_ENABLED 'true' değil."
        )
    _require_no_blocking_attempts(store)
    try:
        candidate = validate_order_candidate(filter_profile, quantity=quantity, price=price)
    except InstrumentFilterError as exc:
        raise TestnetOrderExecutionError(exc.code, str(exc).split(": ", 1)[-1]) from exc
    if number(candidate.notional) > max_entry_notional:
        raise TestnetOrderExecutionError(
            "GATE_NOTIONAL_CAP_EXCEEDED", "Emir notional'i max_entry_notional sınırını aşıyor."
        )
    filter_snapshot_hash = request_fingerprint(
        {
            "profile_id": filter_profile.profile_id,
            "qty_step": filter_profile.qty_step,
            "price_tick": filter_profile.price_tick,
            "min_qty": filter_profile.min_qty,
            "min_notional": filter_profile.min_notional,
        }
    )
    attempt = OrderAttempt(
        attempt_id=attempt_id,
        run_id=run_id,
        venue="BINANCE_SPOT_TESTNET",
        operation=AttemptOperation.PLACE_ORDER,
        symbol=symbol,
        client_order_id=client_order_id,
        request_fingerprint_sha256=request_fingerprint(
            {"symbol": symbol, "side": side, "quantity": candidate.quantity, "price": candidate.price}
        ),
        capability_snapshot_hash=capability_snapshot_hash,
        filter_snapshot_hash=filter_snapshot_hash,
        state=AttemptState.PREPARED,
        created_at_us=now_us,
        last_transition_at_us=now_us,
    )
    outcome = store.prepare(attempt)
    if outcome == "DUPLICATE":
        raise TestnetOrderExecutionError(
            "GATE_ATTEMPT_ALREADY_PREPARED",
            "Bu attempt_id zaten hazırlanmış; aynı emri iki kez göndermeyin.",
        )
    store.persist(attempt_id, now_us=now_us)
    store.mark_sending(attempt_id, now_us=now_us)
    kwargs = {} if websocket_factory is None else {"websocket_factory": websocket_factory}
    if request_id_factory is not None:
        kwargs["request_id_factory"] = request_id_factory
    try:
        placed = await place_binance_testnet_limit_order(
            credential_id,
            symbol,
            side,
            candidate.quantity,
            candidate.price,
            client_order_id,
            provider=provider,
            clock=clock,
            **kwargs,
        )
    except OrderRejectedByVenue as exc:
        # A clean, synchronous "no" from the venue is not ambiguous: no
        # reconciliation/REST catch-up is needed, so this must never become
        # UNKNOWN (found live: an early manual test conflated the two).
        store.mark_rejected(
            attempt_id,
            now_us=now_us,
            reason="VENUE_REJECTED",
            venue_error_code=exc.venue_error_code,
        )
        raise TestnetOrderExecutionError(
            "GATE_ORDER_REJECTED", "Emir venue tarafından reddedildi."
        ) from exc
    except BinanceTestnetOrderExecutionError as exc:
        store.mark_unknown(attempt_id, now_us=now_us, reason="TRANSPORT_FAILED")
        raise TestnetOrderExecutionError(
            "GATE_SEND_FAILED",
            "Gönderim başarısız; attempt UNKNOWN'a düştü, REST catch-up ile çözülmeli.",
        ) from exc
    acknowledged = store.mark_acknowledged(attempt_id, now_us=now_us, venue_order_id=placed.order_id)
    return GatedOrderResult(acknowledged, placed)


async def cancel_gated_testnet_order(
    *,
    store: AttemptStore,
    run_id: str,
    attempt_id: str,
    symbol: str,
    order_id: int,
    capability_snapshot_hash: str,
    confirmed: bool,
    credential_id: str,
    provider: CredentialProvider,
    clock: Clock,
    now_us: int,
    websocket_factory: WebSocketFactory | None = None,
    request_id_factory=None,
) -> GatedCancelResult:
    """Cancel exactly one order, under the identical discipline as placement
    (rules 1-5, docs/KARARLAR.md 2026-09-21, "Faz 3.4" rule 6): a cancel is a
    mutation like any other, so it gets its own durable, idempotent
    AttemptStore identity before any signed request is built, not just the
    kill-switch and confirmation checks."""

    if confirmed is not True:
        raise TestnetOrderExecutionError(
            "GATE_CONFIRMATION_REQUIRED",
            "Execution-anında açık onay olmadan hiçbir cancel gönderilmez.",
        )
    if not trading_kill_switch_enabled():
        raise TestnetOrderExecutionError(
            "GATE_KILL_SWITCH_OFF", "DCABOT_TRADING_ENABLED 'true' değil."
        )
    _require_no_blocking_attempts(store)
    attempt = OrderAttempt(
        attempt_id=attempt_id,
        run_id=run_id,
        venue="BINANCE_SPOT_TESTNET",
        operation=AttemptOperation.CANCEL_ORDER,
        symbol=symbol,
        client_order_id=None,
        request_fingerprint_sha256=request_fingerprint({"symbol": symbol, "order_id": order_id}),
        capability_snapshot_hash=capability_snapshot_hash,
        filter_snapshot_hash=request_fingerprint({"operation": "CANCEL_ORDER"}),
        state=AttemptState.PREPARED,
        created_at_us=now_us,
        last_transition_at_us=now_us,
    )
    outcome = store.prepare(attempt)
    if outcome == "DUPLICATE":
        raise TestnetOrderExecutionError(
            "GATE_ATTEMPT_ALREADY_PREPARED",
            "Bu attempt_id zaten hazırlanmış; aynı cancel'i iki kez göndermeyin.",
        )
    store.persist(attempt_id, now_us=now_us)
    store.mark_sending(attempt_id, now_us=now_us)
    kwargs = {} if websocket_factory is None else {"websocket_factory": websocket_factory}
    if request_id_factory is not None:
        kwargs["request_id_factory"] = request_id_factory
    try:
        cancelled = await cancel_binance_testnet_order(
            credential_id, symbol, order_id=order_id, provider=provider, clock=clock, **kwargs
        )
    except OrderRejectedByVenue as exc:
        store.mark_rejected(
            attempt_id,
            now_us=now_us,
            reason="VENUE_REJECTED",
            venue_error_code=exc.venue_error_code,
        )
        raise TestnetOrderExecutionError(
            "GATE_CANCEL_REJECTED", "Cancel venue tarafından reddedildi."
        ) from exc
    except BinanceTestnetOrderExecutionError as exc:
        store.mark_unknown(attempt_id, now_us=now_us, reason="TRANSPORT_FAILED")
        raise TestnetOrderExecutionError(
            "GATE_CANCEL_SEND_FAILED",
            "Cancel gönderimi başarısız; attempt UNKNOWN'a düştü, REST catch-up ile çözülmeli.",
        ) from exc
    acknowledged = store.mark_acknowledged(attempt_id, now_us=now_us, venue_order_id=cancelled.order_id)
    return GatedCancelResult(acknowledged, cancelled)


async def recover_stuck_attempts(
    *,
    store: AttemptStore,
    credential_id: str,
    provider: CredentialProvider,
    clock: Clock,
    now_us: int,
    websocket_factory: WebSocketFactory | None = None,
    request_id_factory=None,
) -> tuple[OrderAttempt, ...]:
    """Faz 3.6/3.4-F2: resolve whatever is left non-terminal, whether from a
    prior process death or a plain transport failure in an earlier run.

    Must be called once at the start of a session, before
    `place_gated_testnet_limit_order`/`cancel_gated_testnet_order` is
    attempted — otherwise a stuck attempt (PREPARED, PERSISTED, or SENDING
    from a crash; see `AttemptStore.recover_after_restart` and the
    `can_transition` extension, docs/KARARLAR.md 2026-09-21) keeps
    `count_in_flight_attempts() > 0` forever and every future mutation is
    refused by rule 5.

    Resolves every attempt `list_resolvable_attempts()` returns — this is a
    superset of what `recover_after_restart` just quarantined: it also picks
    up an UNKNOWN attempt left over from a genuine transport failure inside
    a still-running process (mark_unknown, not a crash), which the gate
    itself now refuses to mutate past via `_require_no_blocking_attempts`
    until it is resolved here or left UNRESOLVED for an operator to look at.

    Each attempt is resolved via the same real, read-only signed lookup Faz
    3.2's REST catch-up uses: ACKNOWLEDGED if the venue actually has it (so a
    crash right after a real fill is never duplicated), or it stays
    UNRESOLVED (permanent, requires an operator to look, never silently
    retried) if the venue genuinely never saw it.
    """

    coordinator = ReconciliationCoordinator(store)
    coordinator.startup(now_us=now_us)
    resolvable = store.list_resolvable_attempts()
    resolved: list[OrderAttempt] = []
    for attempt in resolvable:
        lookup = await lookup_attempt_via_testnet(
            attempt,
            credential_id=credential_id,
            provider=provider,
            clock=clock,
            **({} if websocket_factory is None else {"websocket_factory": websocket_factory}),
            **({} if request_id_factory is None else {"request_id_factory": request_id_factory}),
        )
        resolved.append(
            coordinator.reconcile_attempt(
                attempt.attempt_id, _PrefetchedOrderQuery(lookup), now_us=now_us
            )
        )
    return tuple(resolved)
