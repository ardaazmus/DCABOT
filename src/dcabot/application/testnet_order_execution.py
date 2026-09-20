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
5. Single in-flight mutation: refuses to prepare a new attempt while any
   attempt is still between PREPARED and a venue answer.
6. Cancellation goes through the identical discipline (its own function
   below, not a shortcut).
7. The transport layer's base URL stays hard-coded to Testnet.
"""

from dataclasses import dataclass

from dcabot.application.credential_boundary import CredentialProvider
from dcabot.application.instrument_filters import InstrumentFilterError, InstrumentFilterProfile, validate_order_candidate
from dcabot.application.order_attempt import AttemptOperation, AttemptState, OrderAttempt, request_fingerprint
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


class TestnetOrderExecutionError(RuntimeError):
    """Raised when the gate refuses a mutation before or after the venue call."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class GatedOrderResult:
    attempt: OrderAttempt
    placed: PlacedTestnetOrder


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
    if store.count_in_flight_attempts() > 0:
        raise TestnetOrderExecutionError(
            "GATE_MUTATION_IN_FLIGHT", "Zaten devam eden bir mutation var; eşzamanlı emir gönderilmez."
        )
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
    symbol: str,
    order_id: int,
    confirmed: bool,
    credential_id: str,
    provider: CredentialProvider,
    clock: Clock,
    websocket_factory: WebSocketFactory | None = None,
    request_id_factory=None,
) -> CancelledTestnetOrder:
    """Cancel exactly one order, gated by the same confirmation + kill-switch discipline."""

    if confirmed is not True:
        raise TestnetOrderExecutionError(
            "GATE_CONFIRMATION_REQUIRED",
            "Execution-anında açık onay olmadan hiçbir cancel gönderilmez.",
        )
    if not trading_kill_switch_enabled():
        raise TestnetOrderExecutionError(
            "GATE_KILL_SWITCH_OFF", "DCABOT_TRADING_ENABLED 'true' değil."
        )
    kwargs = {} if websocket_factory is None else {"websocket_factory": websocket_factory}
    if request_id_factory is not None:
        kwargs["request_id_factory"] = request_id_factory
    try:
        return await cancel_binance_testnet_order(
            credential_id, symbol, order_id=order_id, provider=provider, clock=clock, **kwargs
        )
    except BinanceTestnetOrderExecutionError as exc:
        raise TestnetOrderExecutionError(
            "GATE_CANCEL_FAILED", "Cancel isteği tamamlanamadı."
        ) from exc
