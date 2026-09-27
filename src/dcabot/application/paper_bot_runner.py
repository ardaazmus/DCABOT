"""Paper bot runner core (Faz W-B2): advance one bot over new closed bars.

Pure and deterministic: given the bot's persisted runtime, its open deal and
the venue's newly closed 1m klines, it returns the next runtime plus the deal
records and events to persist. Every bar goes through the same
`step_closed_bar` rule as backtests, so a paper bot and a backtest of the
same settings follow identical fills. Live bars cannot "stop honestly" on an
ambiguous bar the way a backtest does, so they take the conservative path
(safety order first) and say so in an event.
"""

from dataclasses import dataclass

from dcabot.application.historical_simulation import (
    DealCursor,
    HistoricalSimulationAction,
    step_closed_bar,
)
from dcabot.data_adapters.binance_public_transport import BinancePublicKline
from dcabot.data_adapters.historical import CanonicalBar
from dcabot.domain.config import Config
from dcabot.domain.numbers import Q
from dcabot.persistence.bot_store import BotDeal, BotEvent, BotRuntime

RUNNER_INTERVAL = "1m"
RUNNER_INTERVAL_US = 60_000_000
_CLOSE_REASONS = {"EXIT": "TAKE_PROFIT", "STOP": "STOP_LOSS"}


@dataclass(frozen=True, slots=True)
class BotAdvance:
    runtime: BotRuntime
    deals: tuple[BotDeal, ...]
    events: tuple[BotEvent, ...]


def advance_bot(
    runtime: BotRuntime,
    klines: tuple[BinancePublicKline, ...],
    *,
    open_deal: BotDeal | None,
    allow_new_deal: bool,
    now_us: int,
    cooldown_until_us: int = 0,
    symbol: str = "",
) -> BotAdvance:
    """Apply every kline newer than `runtime.last_bar_open_us`, oldest first.

    `symbol` stamps every touched deal; multi-pair callers pass the pair
    being advanced, single-pair callers the bot symbol.
    """

    config = Config.parse(runtime.config)
    cursor = DealCursor(runtime.state, runtime.deal_sequence, runtime.prev_net, cooldown_until_us)
    last_open = runtime.last_bar_open_us
    deal = open_deal
    touched: dict[int, BotDeal] = {}
    events: list[BotEvent] = []
    for kline in klines:
        if kline.open_time_us <= last_open:
            continue
        bar = CanonicalBar(
            kline.open_time_us, kline.close_time_us, kline.open, kline.high, kline.low, kline.close, kline.base_volume, True
        )
        actions: list[HistoricalSimulationAction] = []
        step = step_closed_bar(
            cursor,
            config,
            bar,
            kline.open_time_us // RUNNER_INTERVAL_US,
            actions,
            on_ambiguous="SAFETY_FIRST",
            allow_new_deal=allow_new_deal,
        )
        cursor = step.cursor
        last_open = kline.open_time_us
        if step.resolved_ambiguity:
            events.append(
                BotEvent(runtime.bot_id, kline.open_time_us, "AMBIGUOUS_BAR_SAFETY_FIRST", {"high": kline.high, "low": kline.low})
            )
        for action in actions:
            detail = {"price": action.fill_price, "qty": action.quantity, "fee": action.fee}
            if action.role == "BASE":
                deal = BotDeal(runtime.bot_id, action.deal_sequence, action.open_time_us, None, 0, None, None, 0, symbol)
                events.append(BotEvent(runtime.bot_id, action.open_time_us, "DEAL_STARTED", {**detail, "deal": action.deal_sequence}))
            elif action.role.startswith("SAFETY:"):
                if deal is None:
                    raise ValueError("Safety order without an open deal")
                deal = BotDeal(deal.bot_id, deal.deal_sequence, deal.started_at_us, None, deal.safety_orders_filled + 1, None, None, deal.manual_orders_filled, symbol or deal.symbol)
                events.append(
                    BotEvent(runtime.bot_id, action.open_time_us, "SAFETY_ORDER_FILLED", {**detail, "deal": action.deal_sequence, "index": deal.safety_orders_filled})
                )
            elif action.role in _CLOSE_REASONS:
                if deal is None or step.closed_deal_pnl is None:
                    raise ValueError("Deal close without an open deal or its result")
                reason = _CLOSE_REASONS[action.role]
                deal = BotDeal(deal.bot_id, deal.deal_sequence, deal.started_at_us, action.open_time_us, deal.safety_orders_filled, step.closed_deal_pnl, reason, deal.manual_orders_filled, symbol or deal.symbol)
                events.append(
                    BotEvent(runtime.bot_id, action.open_time_us, "DEAL_CLOSED", {**detail, "deal": action.deal_sequence, "reason": reason, "profit": step.closed_deal_pnl})
                )
            if deal is not None:
                touched[deal.deal_sequence] = deal
        if deal is not None and deal.closed_at_us is not None:
            deal = None
    next_runtime = BotRuntime(
        bot_id=runtime.bot_id,
        config=runtime.config,
        state=cursor.state,
        deal_sequence=cursor.deal_sequence,
        prev_net=cursor.prev_net,
        last_bar_open_us=last_open,
        updated_at_us=now_us,
    )
    return BotAdvance(next_runtime, tuple(touched[key] for key in sorted(touched)), tuple(events))


@dataclass(frozen=True, slots=True)
class ComboPosition:
    """One open deal as the combo trigger sees it: signed size, deployed cost, mark."""

    qty: Q
    cost: Q
    mark: Q | None
    direction: str


def combo_close_triggered(positions: tuple[ComboPosition, ...], target_percent: Q) -> bool:
    """True when the combined unrealized percent hits the target.

    Combined percent is total unrealized over total deployed cost (the
    same per-deal formula `bot_stats` shows, summed, SHORT mirrored).
    Empty, flat, or unmarked books never trigger: the runner must not
    close blind. Division-free: u*100 >= target*cost.
    """

    if not positions or target_percent <= 0:
        return False
    total_cost = Q(0)
    total_unrealized = Q(0)
    for position in positions:
        if position.mark is None or not position.qty or position.cost <= 0:
            return False
        if position.direction == "SHORT":
            total_unrealized += position.cost - position.qty * position.mark
        else:
            total_unrealized += position.qty * position.mark - position.cost
        total_cost += position.cost
    if total_cost <= 0:
        return False
    return total_unrealized * 100 >= target_percent * total_cost
