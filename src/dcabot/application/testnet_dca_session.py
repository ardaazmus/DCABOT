"""Faz 3.7: drive one real DCA deal on Binance Spot Testnet.

Reuses the core reducer (`domain.engine.State/apply/decision`) exactly as
Faz 2's historical simulation does -- no new economic logic. Reuses the
Faz 3.4/3.5 mutation gate for every real order and Faz 3.2's exact-fill
source (`fetch_binance_testnet_my_trades`, the only place fee/price/qty
come from) for every FILL event fed back into the reducer.

This module is a thin, in-memory orchestration layer only. It does not
persist `State`/`bindings` durably -- a process crash mid-deal loses the
in-memory DCA session (not the underlying venue orders, which Faz 3.6's
recover_stuck_attempts still protects at the attempt level). A durable
live-deal store is a real limitation, deliberately deferred rather than
invented in this first slice (docs/KARARLAR.md, 2026-09-21).
"""

from dataclasses import dataclass, field, replace

from dcabot.application.credential_boundary import CredentialProvider
from dcabot.application.instrument_filters import InstrumentFilterProfile
from dcabot.application.signed_request import Clock
from dcabot.application.testnet_order_execution import (
    GatedOrderResult,
    TestnetOrderExecutionError,
    place_gated_testnet_limit_order,
)
from dcabot.data_adapters.binance_testnet_account import fetch_binance_testnet_my_trades
from dcabot.data_adapters.binance_testnet_order_execution import WebSocketFactory
from dcabot.data_adapters.binance_testnet_user_stream import query_binance_testnet_order_status
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply, decision
from dcabot.domain.numbers import Q, exact_text, number
from dcabot.persistence.attempt_store import AttemptStore


class TestnetDcaSessionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def build_live_config(
    profile: InstrumentFilterProfile,
    *,
    symbol: str,
    base_asset: str,
    base_qty: str,
    safety_qty: str,
    safety_count: int,
    deviation: str,
    take_profit: str,
    target_quote: str,
    initial_equity: str,
    max_entry_notional: str,
    minimum_equity: str,
    fee_rate: str = "0.001",
    fee_quantum: str = "0.00000001",
) -> Config:
    """Build a real Config from real instrument filters, not a canned file.

    `mode: "offline"` here is only `Config.parse`'s schema-shape label, not
    a claim about this deal -- `Config` itself carries no live/offline flag,
    every field is a risk-limit number Config.parse validates identically
    either way.
    """

    raw = {
        "schema_version": 1,
        "mode": "offline",
        "symbol": symbol,
        "base_asset": base_asset,
        "quote_asset": "USDT",
        "base_qty": base_qty,
        "safety_qty": safety_qty,
        "safety_count": safety_count,
        "deviation": deviation,
        "step_multiplier": "1",
        "volume_multiplier": "1",
        "tick": profile.price_tick,
        "qty_step": profile.qty_step,
        "min_qty": profile.min_qty,
        "min_notional": profile.min_notional,
        "initial_equity": initial_equity,
        "max_entry_notional": max_entry_notional,
        "leverage": "1",
        "max_drawdown": "0.9",
        "minimum_equity": minimum_equity,
        "take_profit": take_profit,
        "target_mode": "GROSS_PRICE_RETURN",
        "target_quote": target_quote,
        "fee_rate": fee_rate,
        "fee_quantum": fee_quantum,
        "slippage": "0",
    }
    try:
        return Config.parse(raw)
    except ValueError as exc:
        raise TestnetDcaSessionError("DCA_CONFIG_INVALID", str(exc)) from exc


@dataclass(frozen=True, slots=True)
class OrderBinding:
    """Ties one local engine order_id to its real venue identity."""

    local_order_id: str
    role: str
    attempt_id: str
    venue_order_id: int


@dataclass(frozen=True, slots=True)
class DcaSession:
    state: State
    config: Config
    symbol: str
    bindings: tuple[OrderBinding, ...] = ()
    applied_trade_ids: frozenset[int] = field(default_factory=frozenset)

    def binding_for(self, role: str) -> OrderBinding | None:
        return next((b for b in self.bindings if b.role == role), None)


def new_session(config: Config, symbol: str) -> DcaSession:
    return DcaSession(state=State(), config=config, symbol=symbol)


def apply_mark(session: DcaSession, price: str) -> DcaSession:
    next_state = apply(session.state, {"type": "MARK", "price": price}, session.config)
    return replace(session, state=next_state)


def propose_next_action(session: DcaSession) -> tuple[str, Q] | None:
    """Read-only: what the core reducer says should happen next, if anything."""

    return decision(session.state, session.config)


async def place_next_action(
    session: DcaSession,
    *,
    role: str,
    qty: Q,
    store: AttemptStore,
    attempt_id: str,
    credential_id: str,
    provider: CredentialProvider,
    clock: Clock,
    now_us: int,
    max_entry_notional: Q,
    capability_snapshot_hash: str,
    websocket_factory: WebSocketFactory | None = None,
    request_id_factory=None,
) -> tuple[DcaSession, GatedOrderResult]:
    """Record the local INTENT, then place the real gated order.

    INTENT is applied locally FIRST (as `historical_simulation.py` and the
    live offline bot both do) so the reducer's own INTENT-time checks (one
    base order per deal, safety plan order, entry-notional cap) run before
    any signed request exists -- the same fail-closed order engine.py's
    other callers already rely on.
    """

    side = "SELL" if role in ("EXIT", "STOP") else "BUY"
    price = _role_price(session, role)
    intent_state = apply(
        session.state,
        {
            "type": "INTENT",
            "order_id": attempt_id,
            "role": role,
            "qty": exact_text(qty),
            "limit_price": exact_text(price),
        },
        session.config,
    )
    try:
        result = await place_gated_testnet_limit_order(
            store=store,
            run_id=f"dca-{session.symbol.lower()}",
            attempt_id=attempt_id,
            client_order_id=attempt_id,
            symbol=session.symbol,
            side=side,
            quantity=exact_text(qty),
            price=exact_text(price),
            filter_profile=InstrumentFilterProfile(
                profile_id=f"{session.symbol.lower()}-dca",
                qty_step=exact_text(session.config.qty_step),
                price_tick=exact_text(session.config.tick),
                min_qty=exact_text(session.config.min_qty),
                min_notional=exact_text(session.config.min_notional),
            ),
            max_entry_notional=max_entry_notional,
            capability_snapshot_hash=capability_snapshot_hash,
            confirmed=True,
            credential_id=credential_id,
            provider=provider,
            clock=clock,
            now_us=now_us,
            websocket_factory=websocket_factory,
            request_id_factory=request_id_factory,
        )
    except TestnetOrderExecutionError:
        # The local INTENT is not committed to the session on a failed send;
        # the caller sees the original session and may retry with a fresh id.
        raise
    binding = OrderBinding(attempt_id, role, attempt_id, result.placed.order_id)
    next_session = replace(
        session, state=intent_state, bindings=(*session.bindings, binding)
    )
    return next_session, result


async def sync_order_fills(
    session: DcaSession,
    role: str,
    *,
    credential_id: str,
    provider: CredentialProvider,
    clock: Clock,
    websocket_factory: WebSocketFactory | None = None,
    request_id_factory=None,
    my_trades_opener=None,
) -> DcaSession:
    """Fetch the real order status + exact fills and feed them to the reducer.

    Only ever ACCEPTED, already-seen (deduplicated by real trade id, not
    reapplied), or a real ORDER_FINAL observation once the venue reports the
    order complete. Never guesses a fill from order status alone.
    """

    binding = session.binding_for(role)
    if binding is None:
        raise TestnetDcaSessionError("DCA_NO_BINDING", f"'{role}' için henüz bir emir yok.")
    kwargs = {} if websocket_factory is None else {"websocket_factory": websocket_factory}
    if request_id_factory is not None:
        kwargs["request_id_factory"] = request_id_factory
    lookup = await query_binance_testnet_order_status(
        credential_id, session.symbol, binding.venue_order_id, provider=provider, clock=clock, **kwargs
    )
    if lookup.venue_order_id is None:
        raise TestnetDcaSessionError("DCA_ORDER_NOT_FOUND", "Venue bu emri artık tanımıyor.")
    trades = fetch_binance_testnet_my_trades(
        credential_id,
        session.symbol,
        order_id=binding.venue_order_id,
        provider=provider,
        clock=clock,
        opener=my_trades_opener,
    )
    state = session.state
    applied = set(session.applied_trade_ids)
    for trade in trades:
        if trade.trade_id in applied:
            continue
        side = "BUY" if trade.is_buyer else "SELL"
        fee_quote = _fee_in_quote_asset(trade, session.config)
        state = apply(
            state,
            {
                "type": "FILL",
                "execution_id": f"trade-{trade.trade_id}",
                "order_id": binding.local_order_id,
                "side": side,
                "qty": trade.qty,
                "price": trade.price,
                "fee": exact_text(fee_quote),
                "fee_asset": session.config.quote_asset,
            },
            session.config,
        )
        applied.add(trade.trade_id)
    order = state.orders.get(binding.local_order_id)
    if order is not None and not order.complete and order.filled == order.qty:
        # Coverage is only claimed once every real trade's quantity sums
        # exactly to the requested quantity -- never inferred from a single
        # trade or from order-status text alone (OrderLookup carries no
        # status field by design; see reconciliation.OrderLookup).
        state = apply(
            state,
            {
                "type": "ORDER_FINAL",
                "order_id": binding.local_order_id,
                "status": "FILLED",
                "filled_qty": exact_text(order.filled),
                "coverage_complete": True,
            },
            session.config,
        )
    return replace(session, state=state, applied_trade_ids=frozenset(applied))


def _fee_in_quote_asset(trade, config: Config) -> Q:
    """Convert a real fill's commission into engine.py's required quote-asset fee.

    `apply()`'s FILL handler hard-requires `fee_asset == config.quote_asset`
    (found live-equivalent: real Binance BUY fills without a BNB discount
    charge commission in the asset *received* -- the base asset -- not the
    quote asset the core model assumes). A base-asset fee is converted at
    this exact fill's own price (an exact unit conversion of the same
    trade, not an invented external rate); any other commission asset
    (e.g. BNB) is refused rather than guessed at.
    """

    commission = number(trade.commission)
    if trade.commission_asset == config.quote_asset:
        return commission
    if trade.commission_asset == config.base_asset:
        return commission * number(trade.price)
    raise TestnetDcaSessionError(
        "DCA_FEE_ASSET_UNSUPPORTED",
        f"Fee asset '{trade.commission_asset}' bu dilimde desteklenmiyor (yalnız base/quote).",
    )


def _role_price(session: DcaSession, role: str) -> Q:
    if role == "BASE":
        if session.state.mark is None:
            raise TestnetDcaSessionError("DCA_MARK_REQUIRED", "BASE için önce mark fiyatı uygulanmalı.")
        return session.state.mark
    if role in ("EXIT", "STOP"):
        from dcabot.domain.engine import target

        price = target(session.state, session.config)
        if price is None:
            raise TestnetDcaSessionError("DCA_TARGET_UNAVAILABLE", "TP fiyatı hesaplanamadı.")
        return price
    plan = session.config.plan(session.state.anchor) if session.state.anchor is not None else None
    if plan is None:
        raise TestnetDcaSessionError("DCA_PLAN_UNAVAILABLE", "Safety planı için anchor gerekli.")
    done = sum(
        o.role.startswith("SAFETY:") and o.complete and o.filled == o.qty
        for o in session.state.orders.values()
    )
    if done >= len(plan):
        raise TestnetDcaSessionError("DCA_PLAN_EXHAUSTED", "Tüm safety seviyeleri kullanıldı.")
    return plan[done].price
