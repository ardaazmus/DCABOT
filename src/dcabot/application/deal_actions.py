"""Faz W-B4: user deal actions on the open deal -- close at market, cancel,
add funds (3Commas/Bitsgap parity).

Pure and exact: each action takes the bot's engine config, its current
engine state, the open deal record and the net baseline, and returns the
next state plus the deal row and event to persist. Fills mirror the
simulator's own fill rule (side-aware slippage, tick align, fee quantum);
this layer invents no economics. Manual buys use the engine's MANUAL
role, so averaging, fees and the safety-plan index stay consistent by
construction.
"""

from dataclasses import dataclass

from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply
from dcabot.domain.math import Position
from dcabot.domain.numbers import Q, align, exact_text, round_quantum
from dcabot.persistence.bot_store import BotDeal, BotEvent


class DealActionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class DealActionResult:
    state: State
    deal: BotDeal
    event: BotEvent
    prev_net: Q


def _require_open(deal: BotDeal) -> None:
    if deal.closed_at_us is not None:
        raise DealActionError("DEAL_ALREADY_CLOSED", "Deal zaten kapali.")


def _sides(direction: str) -> tuple[str, str]:
    """Opening/closing venue sides; mirrors the engine's direction mapping."""
    if direction == "SHORT":
        return "SELL", "BUY"
    return "BUY", "SELL"


def _fill_price(config: Config, raw: Q, side: str) -> Q:
    if side == "BUY":
        return align(raw * (1 + config.slippage), config.tick, up=True)
    return align(raw * (1 - config.slippage), config.tick, up=False)


def _execute(
    state: State,
    config: Config,
    *,
    order_id: str,
    role: str,
    side: str,
    qty: Q,
    fill: Q,
) -> tuple[State, Q]:
    state = apply(
        state,
        {"type": "INTENT", "order_id": order_id, "role": role, "qty": exact_text(qty), "limit_price": exact_text(fill)},
        config,
    )
    fee = round_quantum(qty * fill * config.fee_rate, config.fee_quantum)
    state = apply(
        state,
        {
            "type": "FILL",
            "execution_id": f"{order_id}:fill",
            "order_id": order_id,
            "side": side,
            "qty": exact_text(qty),
            "price": exact_text(fill),
            "fee": exact_text(fee),
            "fee_asset": config.quote_asset,
        },
        config,
    )
    state = apply(
        state,
        {"type": "ORDER_FINAL", "order_id": order_id, "status": "FILLED", "filled_qty": exact_text(qty), "coverage_complete": True},
        config,
    )
    return state, fee


def close_at_market(
    config: Config,
    state: State,
    deal: BotDeal,
    prev_net: Q,
    *,
    price: Q,
    now_us: int,
    reason: str = "MANUAL_CLOSE",
) -> DealActionResult:
    """Sell the whole position at the current market price (plus fees)."""
    _require_open(deal)
    if reason not in ("MANUAL_CLOSE", "TAKE_PROFIT"):
        raise DealActionError("DEAL_ACTION_INVALID", "Bilinmeyen kapanis nedeni.")
    if price <= 0:
        raise DealActionError("DEAL_ACTION_INVALID", "Fiyat pozitif olmalidir.")
    if not state.position.qty:
        raise DealActionError("DEAL_NOT_OPEN", "Acik pozisyon yok.")
    _, closing = _sides(config.direction)
    try:
        state = apply(state, {"type": "MARK", "price": exact_text(price)}, config)
        qty = state.position.qty
        fill = _fill_price(config, price, closing)
        order_id = f"manual:{deal.deal_sequence}:{now_us}:close:order"
        state, fee = _execute(state, config, order_id=order_id, role="EXIT", side=closing, qty=qty, fill=fill)
    except (ValueError, ZeroDivisionError) as exc:
        raise DealActionError("DEAL_ACTION_REJECTED", f"Motor kapatmayi reddetti: {exc}") from exc
    current_net = state.realized - state.fees - state.funding
    profit = exact_text(current_net - prev_net)
    closed = BotDeal(
        deal.bot_id, deal.deal_sequence, deal.started_at_us, now_us,
        deal.safety_orders_filled, profit, reason, deal.manual_orders_filled, deal.symbol,
    )
    event = BotEvent(
        deal.bot_id, now_us, "DEAL_CLOSED",
        {"deal": deal.deal_sequence, "reason": reason, "price": exact_text(fill),
         "qty": exact_text(qty), "fee": exact_text(fee), "profit": profit},
    )
    return DealActionResult(state, closed, event, current_net)


def cancel_deal(
    config: Config, state: State, deal: BotDeal, prev_net: Q, *, now_us: int
) -> DealActionResult:
    """Abandon the deal without a sale: the bought base stays with the user,
    the bot books profit "0". Buy fees stay sunk in the engine totals, exactly
    as a real cancellation leaves them on the account. Works even on a flat
    position, so it also repairs a skewed open-deal record."""
    _require_open(deal)
    flat = State(
        position=Position(),
        realized=state.realized,
        fees=state.fees,
        funding=state.funding,
        entry_notional=Q(0),
        mark=state.mark,
        anchor=None,
        peak=state.peak,
        max_dd=state.max_dd,
        halted=state.halted,
        safety_stopped=False,
        orders={},
        blockers=[],
        last_rejection=state.last_rejection,
    )
    closed = BotDeal(
        deal.bot_id, deal.deal_sequence, deal.started_at_us, now_us,
        deal.safety_orders_filled, "0", "CANCELLED", deal.manual_orders_filled, deal.symbol,
    )
    event = BotEvent(
        deal.bot_id, now_us, "DEAL_CLOSED",
        {"deal": deal.deal_sequence, "reason": "CANCELLED", "profit": "0"},
    )
    return DealActionResult(flat, closed, event, prev_net)


def add_funds(
    config: Config, state: State, deal: BotDeal, prev_net: Q, *, quote_amount: Q, price: Q, now_us: int
) -> DealActionResult:
    """Buy extra base at the market price, outside the safety plan. The
    MANUAL index comes from the engine's own orders (the authority for its
    sequence); the durable counter catches up if they ever skew."""
    _require_open(deal)
    if quote_amount <= 0 or price <= 0:
        raise DealActionError("DEAL_ACTION_INVALID", "Tutar ve fiyat pozitif olmalidir.")
    opening, _ = _sides(config.direction)
    fill = _fill_price(config, price, opening)
    qty = align(quote_amount / fill, config.qty_step, up=False)
    if qty <= 0:
        raise DealActionError("DEAL_ACTION_BELOW_MINIMUM", "Tutar islem alt limitinin altinda.")
    index = sum(1 for order in state.orders.values() if order.role.startswith("MANUAL:")) + 1
    try:
        state = apply(state, {"type": "MARK", "price": exact_text(price)}, config)
        order_id = f"manual:{deal.deal_sequence}:{index}:{now_us}:order"
        state, fee = _execute(state, config, order_id=order_id, role=f"MANUAL:{index}", side=opening, qty=qty, fill=fill)
    except (ValueError, ZeroDivisionError) as exc:
        raise DealActionError("DEAL_ACTION_REJECTED", f"Motor fon eklemeyi reddetti: {exc}") from exc
    updated = BotDeal(
        deal.bot_id, deal.deal_sequence, deal.started_at_us, None,
        deal.safety_orders_filled, None, None, max(deal.manual_orders_filled, index), deal.symbol,
    )
    event = BotEvent(
        deal.bot_id, now_us, "MANUAL_ORDER_FILLED",
        {"deal": deal.deal_sequence, "index": index, "price": exact_text(fill),
         "qty": exact_text(qty), "fee": exact_text(fee)},
    )
    return DealActionResult(state, updated, event, prev_net)
