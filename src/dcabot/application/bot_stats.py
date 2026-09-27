"""Exact statistics for one bot from its persisted deals and runtime (Faz W).

Everything is Fraction arithmetic over values the runner stored; display
rounding happens only in `text()` for ratios that do not terminate.
"""

from fractions import Fraction

from dcabot.domain.config import Config
from dcabot.domain.engine import target
from dcabot.domain.numbers import exact_text, number, text
from dcabot.persistence.bot_store import BotDeal, BotRuntime

PERCENT_PLACES = 4
PRICE_PLACES = 12


def bot_statistics(deals: tuple[BotDeal, ...], runtime: BotRuntime | None, *, budget: str) -> dict:
    closed = [deal for deal in deals if deal.closed_at_us is not None]
    profits = [number(deal.profit) for deal in closed]
    total = sum(profits, Fraction(0))
    wins = sum(1 for profit in profits if profit > 0)
    durations = [deal.closed_at_us - deal.started_at_us for deal in closed]
    open_deal = next((deal for deal in deals if deal.closed_at_us is None), None)
    budget_value = number(budget)
    return {
        "total_profit": exact_text(total),
        "roi_percent": text(total / budget_value * 100, PERCENT_PLACES),
        "deals_completed": len(closed),
        "winning_deals": wins,
        "win_rate_percent": text(Fraction(wins, len(closed)) * 100, PERCENT_PLACES) if closed else None,
        "average_deal_profit": text(total / len(closed), 8) if closed else None,
        "average_deal_duration_us": sum(durations) // len(durations) if durations else None,
        "stop_loss_deals": sum(1 for deal in closed if deal.close_reason == "STOP_LOSS"),
        "active_deal": _active_deal(open_deal, runtime),
        "last_bar_open_us": runtime.last_bar_open_us if runtime is not None else None,
    }


def _active_deal(deal: BotDeal | None, runtime: BotRuntime | None) -> dict | None:
    if deal is None or runtime is None or not runtime.state.position.qty:
        return None
    config = Config.parse(runtime.config)
    state = runtime.state
    qty, cost, mark = state.position.qty, state.position.cost, state.mark
    short = runtime.config.get("direction", "LONG") == "SHORT"
    take_profit = target(state, config)
    next_safety = None
    if state.anchor is not None and deal.safety_orders_filled < config.safety_count:
        next_safety = exact_text(config.plan(state.anchor)[deal.safety_orders_filled].price)
    return {
        "deal": deal.deal_sequence,
        "started_at_us": deal.started_at_us,
        "safety_orders_filled": deal.safety_orders_filled,
        "max_safety_orders": config.safety_count,
        "qty": exact_text(qty),
        "cost": exact_text(cost),
        "average_price": text(cost / qty, PRICE_PLACES),
        "mark_price": exact_text(mark) if mark is not None else None,
        # SHORT holds the mirror: profit is cost minus cover value.
        "unrealized_profit": exact_text(cost - qty * mark if short else qty * mark - cost) if mark is not None else None,
        # qty > 0 implies cost > 0 (Position invariant): no division-by-zero.
        "unrealized_percent": text(
            (cost - qty * mark if short else qty * mark - cost) / cost * 100, PERCENT_PLACES
        ) if mark is not None else None,
        "take_profit_price": exact_text(take_profit) if take_profit is not None else None,
        "next_safety_order_price": next_safety,
    }
