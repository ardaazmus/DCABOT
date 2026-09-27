"""Faz W v2 bot endpoints: typed request/response models (OpenAPI → web types),
Problem Details errors, sector vocabulary on the wire.

Registered through `register_routes(app, deps)` directly on the app (not via
`include_router`): FastAPI 0.141 serves included routers through a wrapper
that bypasses the per-route body-limit middleware `BoundedAPIRoute` attaches.
"""

import copy
import json
import secrets
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Annotated, Callable, Literal, Protocol

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from dcabot.application.sector_dca import (
    SectorDcaError,
    SectorDcaParams,
    SymbolRules,
    derive_deal_config,
    max_deal_quote_cost,
    parse_sector_dca,
    summarize_deal_plan,
)
from dcabot.application.bot_stats import PRICE_PLACES, bot_statistics
from dcabot.application.futures_grid_engine import (
    FuturesGridEngineError,
    create_grid as create_futures_grid,
    describe_grid as describe_futures_grid,
    grid_equity_quote as futures_grid_equity_quote,
    restore_grid as restore_futures_grid,
)
from dcabot.application.futures_grid_runner import (
    build_futures_grid_config,
    futures_config_from_dict,
)
from dcabot.application.grid_runner import build_grid_config, config_from_dict
from dcabot.application.spot_grid_engine import (
    SpotGridEngineError,
    create_grid,
    describe_grid,
    grid_equity_quote,
    restore_grid,
)
from dcabot.application.deal_actions import DealActionError, add_funds, cancel_deal, close_at_market
from dcabot.domain.config import Config
from dcabot.domain.numbers import Q, exact_text, number, text
from dcabot.persistence.bot_store import BotDeal, BotEvent, BotPairRuntime, BotRecord, BotRuntime, BotStore, BotStoreError
from dcabot.server.bot_runner import ReplayError

DecimalText = Annotated[str, Field(min_length=1, max_length=50, pattern=r"^(0|[1-9][0-9]*)(\.[0-9]+)?$")]
BotMode = Literal["PAPER", "TESTNET"]
BotStatus = Literal["STOPPED", "RUNNING", "PAUSED", "ERROR"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DcaStrategy(_Strict):
    symbol: Annotated[str, Field(min_length=5, max_length=20, pattern=r"^[A-Z0-9]+$")]
    base_order: DecimalText
    safety_order: DecimalText
    max_safety_orders: Annotated[int, Field(ge=0, le=50)]
    max_active_safety_orders: Annotated[int, Field(ge=1, le=50)] | None
    price_deviation: DecimalText
    safety_order_volume_scale: DecimalText
    safety_order_step_scale: DecimalText
    take_profit: DecimalText
    stop_loss: DecimalText | None
    direction: Literal["LONG", "SHORT"] = "LONG"
    cooldown_seconds: Annotated[int, Field(ge=0, le=31_536_000)] = 0
    min_price: DecimalText | None = None
    max_price: DecimalText | None = None
    market_type: Literal["SPOT", "FUTURES"] = "SPOT"
    leverage: Annotated[int, Field(ge=1, le=10)] | None = None
    symbols: Annotated[
        list[Annotated[str, Field(min_length=5, max_length=20, pattern=r"^[A-Z0-9]+$")]],
        Field(min_length=1, max_length=10),
    ] | None = None
    max_active_deals: Annotated[int, Field(ge=1, le=10)] | None = None
    combined_take_profit: DecimalText | None = None
    # F09a: optional trailing TP percent; None keeps the fixed TP exit.
    trailing_take_profit: DecimalText | None = None


class BotPreviewRequest(_Strict):
    budget: DecimalText
    strategy: DcaStrategy


class BotCreateRequest(_Strict):
    name: Annotated[str, Field(min_length=1, max_length=64)]
    mode: BotMode
    budget: DecimalText
    strategy: DcaStrategy


class GridBotStrategy(_Strict):
    symbol: Annotated[str, Field(min_length=5, max_length=20, pattern=r"^[A-Z0-9]+$")]
    mode: Literal["ARITHMETIC", "GEOMETRIC"] = "ARITHMETIC"
    lower_price: DecimalText
    upper_price: DecimalText
    interval_count: Annotated[int, Field(ge=1, le=1000)]
    fee_rate: DecimalText = "0.001"
    stop_loss_price: DecimalText | None = None
    take_profit_pct: DecimalText | None = None
    trailing_up_pct: DecimalText | None = None
    trailing_down_pct: DecimalText | None = None


class GridBotCreateRequest(_Strict):
    name: Annotated[str, Field(min_length=1, max_length=64)]
    mode: BotMode
    budget: DecimalText
    strategy: GridBotStrategy


class GridBotPreviewRequest(_Strict):
    budget: DecimalText
    strategy: GridBotStrategy


class GridPreview(BaseModel):
    symbol: str
    reference_price: str
    entry_position: Literal["BELOW", "WITHIN", "ABOVE"]
    levels: list[str]
    interval_count: int
    investment_quote: str
    quote_per_grid: str
    base_step_size: str
    fee_rate: str
    within_min_notional: bool
    stop_loss_price: str | None
    take_profit_pct: str | None
    trailing_up_pct: str | None
    trailing_down_pct: str | None


class GridPreviewEnvelope(BaseModel):
    data: GridPreview


class GridFill(_Strict):
    fill_id: str
    side: str
    price: str
    base_quantity: str


class GridState(_Strict):
    grid_status: str
    entry_price: str | None
    last_price: str | None
    levels: list[str]
    pending: list[str]
    locked_quote: list[str]
    locked_base: list[str]
    quote_reserve: str
    base_free: str
    cycles_closed: int
    realized_profit_quote: str
    fees_paid_quote: str
    equity_at_last: str | None
    fills_recent: list[GridFill]
    trailing_shifts: int
    last_bar_open_us: int | None
    updated_at_us: int | None


class GridStateEnvelope(BaseModel):
    data: GridState


class FuturesGridBotStrategy(_Strict):
    symbol: Annotated[str, Field(min_length=5, max_length=20, pattern=r"^[A-Z0-9]+$")]
    direction: Literal["LONG", "SHORT"] = "LONG"
    mode: Literal["ARITHMETIC", "GEOMETRIC"] = "ARITHMETIC"
    lower_price: DecimalText
    upper_price: DecimalText
    interval_count: Annotated[int, Field(ge=1, le=1000)]
    leverage: Annotated[int, Field(ge=1, le=10)] = 1
    fee_rate: DecimalText = "0.0005"
    stop_loss_price: DecimalText | None = None
    take_profit_pct: DecimalText | None = None
    trailing_up_pct: DecimalText | None = None
    trailing_down_pct: DecimalText | None = None


class FuturesGridBotCreateRequest(_Strict):
    name: Annotated[str, Field(min_length=1, max_length=64)]
    mode: BotMode
    budget: DecimalText
    strategy: FuturesGridBotStrategy


class FuturesGridBotPreviewRequest(_Strict):
    budget: DecimalText
    strategy: FuturesGridBotStrategy


class FuturesGridPreview(BaseModel):
    symbol: str
    direction: str
    leverage: int
    reference_price: str
    entry_position: Literal["BELOW", "WITHIN", "ABOVE"]
    levels: list[str]
    interval_count: int
    investment_quote: str
    quote_per_grid: str
    notional_per_grid: str
    base_step_size: str
    fee_rate: str
    within_min_notional: bool
    stop_loss_price: str | None
    take_profit_pct: str | None
    trailing_up_pct: str | None
    trailing_down_pct: str | None


class FuturesGridPreviewEnvelope(BaseModel):
    data: FuturesGridPreview


class FuturesGridFill(_Strict):
    fill_id: str
    side: str
    price: str
    quantity: str


class FuturesGridLot(_Strict):
    interval: int
    quantity: str
    entry_price: str
    locked_margin: str


class FuturesGridState(_Strict):
    grid_status: str
    direction: str
    leverage: int
    entry_price: str | None
    last_price: str | None
    levels: list[str]
    pending: list[str]
    locked_margin: list[str]
    wallet_free: str
    open_lots: list[FuturesGridLot]
    cycles_closed: int
    realized_gross_pnl: str
    fees_paid_quote: str
    funding_cashflow: str
    funding_events_count: int
    equity_at_last: str | None
    fills_recent: list[FuturesGridFill]
    trailing_shifts: int
    liq_estimate_price: str | None
    liq_estimate_tier: str | None
    last_bar_open_us: int | None
    updated_at_us: int | None


class FuturesGridStateEnvelope(BaseModel):
    data: FuturesGridState


class BotActionRequest(_Strict):
    revision: Annotated[int, Field(ge=1)]


class BotCopyRequest(_Strict):
    name: Annotated[str, Field(min_length=1, max_length=64)] | None = None


ReplayDate = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]


class BotReplayRequest(_Strict):
    start_date: ReplayDate
    end_date: ReplayDate


class BotReplayData(BaseModel):
    bars: int
    deals_opened: int
    deals_closed: int
    fills: int
    events: int
    first_bar_open_us: int
    last_bar_open_us: int
    symbols: list[str]
    stopped: str | None


class BotReplayEnvelope(BaseModel):
    data: BotReplayData


class PlannedOrder(BaseModel):
    price: str
    qty: str
    amount: str


class PlannedSafetyOrder(PlannedOrder):
    index: int
    deviation_percent: str


class DealPlan(BaseModel):
    symbol: str
    reference_price: str
    base_order: PlannedOrder
    safety_orders: list[PlannedSafetyOrder]
    required_funds: str
    orders_total: str
    estimated_fees: str
    budget: str
    within_budget: bool
    price_coverage_percent: str
    average_price_all_filled: str
    take_profit_price: str | None
    stop_loss_price_initial: str | None
    symbols: list[str] | None = None
    total_required_funds: str | None = None
    within_total_budget: bool | None = None


class Bot(BaseModel):
    bot_id: str
    name: str
    type: Literal["DCA", "GRID", "FUTURES_GRID"]
    mode: BotMode
    status: BotStatus
    status_reason: str | None
    symbol: str
    budget: str
    strategy: DcaStrategy | GridBotStrategy | FuturesGridBotStrategy
    revision: int
    created_at_us: int
    updated_at_us: int
    archived: bool


class DealPlanEnvelope(BaseModel):
    data: DealPlan


class BotEnvelope(BaseModel):
    data: Bot


class BotListEnvelope(BaseModel):
    data: list[Bot]


CloseReason = Literal["TAKE_PROFIT", "STOP_LOSS", "MANUAL_CLOSE", "CANCELLED"]


class BotDealModel(BaseModel):
    deal: int
    symbol: str
    started_at_us: int
    closed_at_us: int | None
    safety_orders_filled: int
    manual_orders_filled: int
    profit: str | None
    close_reason: CloseReason | None
    cumulative_profit: str | None


class BotDealsEnvelope(BaseModel):
    data: list[BotDealModel]


class BotEventModel(BaseModel):
    time_us: int
    kind: Literal[
        "DEAL_STARTED", "SAFETY_ORDER_FILLED", "MANUAL_ORDER_FILLED", "DEAL_CLOSED", "AMBIGUOUS_BAR_SAFETY_FIRST",
        "GRID_FILL", "GRID_INIT", "GRID_STOP_LOSS", "GRID_TAKE_PROFIT", "GRID_LIQ_ESTIMATE_HIT",
        "GRID_TRAIL_UP", "GRID_TRAIL_DOWN", "GRID_FUNDING",
    ]
    detail: dict[str, str | int | None]


class BotEventsEnvelope(BaseModel):
    data: list[BotEventModel]


class DealActionBody(_Strict):
    revision: Annotated[int, Field(ge=1)]


class AddFundsBody(_Strict):
    revision: Annotated[int, Field(ge=1)]
    amount: DecimalText


class DealV2(BaseModel):
    bot_id: str
    bot_name: str
    symbol: str
    mode: BotMode
    direction: str
    deal: int
    started_at_us: int
    closed_at_us: int | None
    safety_orders_filled: int
    manual_orders_filled: int
    profit: str | None
    close_reason: CloseReason | None


class DealListEnvelope(BaseModel):
    data: list[DealV2]


class DealDetailModel(DealV2):
    duration_us: int | None
    fees: str | None
    gross_profit: str | None
    qty: str | None
    cost: str | None
    average_price: str | None
    mark_price: str | None
    unrealized_profit: str | None
    unrealized_percent: str | None
    take_profit_price: str | None
    next_safety_order_price: str | None
    cumulative_profit: str | None
    events: list[BotEventModel]


class DealDetailEnvelope(BaseModel):
    data: DealDetailModel


class ActiveDeal(BaseModel):
    deal: int
    started_at_us: int
    safety_orders_filled: int
    max_safety_orders: int
    qty: str
    cost: str
    average_price: str
    mark_price: str | None
    unrealized_profit: str | None
    unrealized_percent: str | None
    take_profit_price: str | None
    next_safety_order_price: str | None


class BotStats(BaseModel):
    total_profit: str
    roi_percent: str
    deals_completed: int
    winning_deals: int
    win_rate_percent: str | None
    average_deal_profit: str | None
    average_deal_duration_us: int | None
    stop_loss_deals: int
    active_deal: ActiveDeal | None
    last_bar_open_us: int | None


class BotStatsEnvelope(BaseModel):
    data: BotStats


class Market(Protocol):
    def symbol_rules(self, symbol: str) -> SymbolRules: ...

    def last_price(self, symbol: str) -> Q: ...


class MarketUnavailable(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class V2BotDeps:
    store: BotStore
    market: Market
    template_loader: Callable[[], dict]
    clock_us: Callable[[], int]
    runner_available: Callable[[], bool]
    problem: Callable[..., JSONResponse]
    on_start: Callable[[BotRecord], None] | None = None
    on_replay: Callable[[str, int, int], dict] | None = None
    futures_market: Market | None = None
    record_event: Callable[[str, str, str, int], None] | None = None


_ACTION_LANDMARK = {
    "start": ("BOT_STARTED", "başlatıldı"),
    "pause": ("BOT_PAUSED", "duraklatıldı"),
    "resume": ("BOT_RESUMED", "devam ettirildi"),
    "stop": ("BOT_STOPPED", "durduruldu"),
    "archive": ("BOT_ARCHIVED", "arşivlendi"),
}
_DEAL_LANDMARK = {
    "close": ("DEAL_CLOSED", "kapandı (MANUAL_CLOSE)"),
    "cancel": ("DEAL_CANCELLED", "iptal edildi"),
    "add-funds": ("DEAL_FUNDS_ADDED", "fon eklendi"),
}


def _plan_from(strategy: DcaStrategy, budget: str, deps: V2BotDeps) -> tuple[dict, SectorDcaParams]:
    from dataclasses import replace as _replace

    params = parse_sector_dca(strategy.model_dump())
    rules = deps.market.symbol_rules(params.symbol)
    price = deps.market.last_price(params.symbol)
    raw_config = derive_deal_config(
        params, rules=rules, reference_price=price, budget=number(budget), template=deps.template_loader()
    )
    summary = summarize_deal_plan(raw_config, price)
    summary["reference_price"] = exact_text(price)
    del summary["base_price"]
    if len(params.symbols) > 1:
        template = deps.template_loader()
        cap = max_deal_quote_cost(
            params, fee_rate=number(template["fee_rate"]), fee_quantum=number(template["fee_quantum"])
        )
        # Every pair must validate at its own rules and price, not just the primary.
        for symbol in params.symbols[1:]:
            pair_params = _replace(params, symbol=symbol)
            pair_rules = deps.market.symbol_rules(symbol)
            pair_price = deps.market.last_price(symbol)
            derive_deal_config(
                pair_params, rules=pair_rules, reference_price=pair_price, budget=cap, template=template
            )
        total = cap * params.max_active_deals
        summary["symbols"] = list(params.symbols)
        summary["total_required_funds"] = exact_text(total)
        summary["within_total_budget"] = total <= number(budget)
    return summary, params


def _strategy_model(record: BotRecord) -> DcaStrategy | GridBotStrategy | FuturesGridBotStrategy:
    if record.strategy_type == "GRID":
        return GridBotStrategy(**record.strategy)
    if record.strategy_type == "FUTURES_GRID":
        return FuturesGridBotStrategy(**record.strategy)
    return DcaStrategy(**record.strategy)


def _bot(record: BotRecord) -> Bot:
    return Bot(
        bot_id=record.bot_id,
        name=record.name,
        type=record.strategy_type,
        mode=record.mode,
        status=record.status,
        status_reason=record.status_reason,
        symbol=record.symbol,
        budget=record.budget,
        strategy=_strategy_model(record),
        revision=record.revision,
        created_at_us=record.created_at_us,
        updated_at_us=record.updated_at_us,
        archived=record.archived_at_us is not None,
    )


_GRID_FIELD = {
    "GRID_BOUNDS_INVALID": "strategy.lower_price",
    "GRID_PRICE_INVALID": "strategy.lower_price",
    "GRID_INTERVAL_INVALID": "strategy.interval_count",
    "GRID_QUOTE_PER_GRID_UNREPRESENTABLE": "strategy.interval_count",
    "GRID_QTY_TOO_SMALL": "strategy.interval_count",
    "GRID_LEVEL_UNREPRESENTABLE": "strategy.interval_count",
    "GRID_GEOMETRIC_RATIO_UNREPRESENTABLE": "strategy.interval_count",
    "GRID_GEOMETRIC_TICK_OFF_GRID": "strategy.interval_count",
    "GRID_TICK_INVALID": "strategy.mode",
    "GRID_MODE_INVALID": "strategy.mode",
    "GRID_SL_INVALID": "strategy.stop_loss_price",
    "GRID_TP_INVALID": "strategy.take_profit_pct",
    "GRID_TRAIL_INVALID": "strategy.trailing_up_pct",
    "GRID_MIN_NOTIONAL_TOO_SMALL": "budget",
    "GRID_INVESTMENT_INVALID": "budget",
    "GRID_FEE_INVALID": "strategy.fee_rate",
}

_FGRID_FIELD = {
    "GRID_BOUNDS_INVALID": "strategy.lower_price",
    "FUTURES_GRID_DIRECTION_INVALID": "strategy.direction",
    "FUTURES_GRID_LEVERAGE_INVALID": "strategy.leverage",
    "FUTURES_GRID_MARGIN_PER_GRID_UNREPRESENTABLE": "strategy.leverage",
    "FUTURES_GRID_QUOTE_PER_GRID_UNREPRESENTABLE": "strategy.interval_count",
    "FUTURES_GRID_QTY_TOO_SMALL": "strategy.interval_count",
    "FUTURES_GRID_MODE_INVALID": "strategy.mode",
    "FUTURES_GRID_SL_INVALID": "strategy.stop_loss_price",
    "FUTURES_GRID_TP_INVALID": "strategy.take_profit_pct",
    "FUTURES_GRID_TRAIL_INVALID": "strategy.trailing_up_pct",
    "FGRID_MIN_NOTIONAL_TOO_SMALL": "budget",
    "FGRID_SYMBOL_HALTED": "strategy.symbol",
    "FUTURES_GRID_CONTRACT_UNSUPPORTED": "strategy.symbol",
    "FUTURES_GRID_SETTLEMENT_UNSUPPORTED": "strategy.symbol",
    "FUTURES_GRID_FEE_INVALID": "strategy.fee_rate",
}

_STORE_STATUS = {
    "BOT_NOT_FOUND": 404,
    "BOT_ID_INVALID": 404,
    "BOT_TRANSITION_INVALID": 409,
    "BOT_REVISION_CONFLICT": 409,
    "BOT_ARCHIVED": 409,
    "BOT_ID_CONFLICT": 409,
    "DEAL_NOT_FOUND": 404,
}


def _deal_rows(deals: tuple[BotDeal, ...]) -> list[dict]:
    """Per-bot deal rows, oldest first, with exact cumulative realized profit.

    Multi-pair deals close out of sequence, so the running sum follows
    closing order while rows stay in sequence order; the final total is
    exact either way."""
    cumulative_by_seq: dict[int, str] = {}
    running = Q(0)
    for d in sorted(
        (deal for deal in deals if deal.closed_at_us is not None),
        key=lambda deal: (deal.closed_at_us, deal.deal_sequence),
    ):
        running += number(d.profit)
        cumulative_by_seq[d.deal_sequence] = exact_text(running)
    rows = []
    for d in deals:
        rows.append(
            {
                "deal": d.deal_sequence,
                "symbol": d.symbol,
                "started_at_us": d.started_at_us,
                "closed_at_us": d.closed_at_us,
                "safety_orders_filled": d.safety_orders_filled,
                "manual_orders_filled": d.manual_orders_filled,
                "profit": d.profit,
                "close_reason": d.close_reason,
                "cumulative_profit": cumulative_by_seq.get(d.deal_sequence),
            }
        )
    return rows


def _replay_buys(events: list[BotEvent]) -> tuple[str, str, str] | None:
    """Rebuild qty/cost/average of a closed deal from its buy-side fills.

    Closed deals store only their result; the fills stay in the event log,
    so the detail view replays them instead of trusting a second copy. Any
    malformed fill fails the whole replay to nulls, never to a wrong number.
    """
    qty = Q(0)
    cost = Q(0)
    try:
        for event in events:
            if event.kind in ("DEAL_STARTED", "SAFETY_ORDER_FILLED", "MANUAL_ORDER_FILLED"):
                fill_qty = number(event.detail["qty"])
                qty += fill_qty
                cost += fill_qty * number(event.detail["price"])
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None
    if not qty:
        return None
    return exact_text(qty), exact_text(cost), text(cost / qty, PRICE_PLACES)


def _replay_fees(events: list[BotEvent], *, close_reason: str | None) -> str | None:
    """Sum the exact per-fill fees of one deal from its fill events.

    Every fill (base, safety, manual top-up, exit) persists its own fee;
    the deal row keeps only net profit, so the detail view replays them.
    A cancelled close carries no exit fill, hence no fee key, by
    construction; any other malformed fill fails the sum to None, never
    to a wrong number.
    """

    total = Q(0)
    try:
        for event in events:
            if event.kind in ("DEAL_STARTED", "SAFETY_ORDER_FILLED", "MANUAL_ORDER_FILLED"):
                total += number(event.detail["fee"])
            elif event.kind == "DEAL_CLOSED":
                if "fee" in event.detail:
                    total += number(event.detail["fee"])
                elif close_reason != "CANCELLED":
                    return None
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None
    return exact_text(total)


def _deal_detail(
    record: BotRecord,
    deals: tuple[BotDeal, ...],
    deal: BotDeal,
    runtime: BotRuntime | None,
    events: tuple[BotEvent, ...],
) -> dict:
    scoped = [event for event in events if event.detail.get("deal") == deal.deal_sequence]
    scoped.reverse()
    base = {
        "bot_id": record.bot_id,
        "bot_name": record.name,
        "symbol": deal.symbol or record.symbol,
        "mode": record.mode,
        "direction": record.strategy.get("direction", "LONG"),
        "deal": deal.deal_sequence,
        "started_at_us": deal.started_at_us,
        "closed_at_us": deal.closed_at_us,
        "safety_orders_filled": deal.safety_orders_filled,
        "manual_orders_filled": deal.manual_orders_filled,
        "profit": deal.profit,
        "close_reason": deal.close_reason,
        "events": [{"time_us": e.time_us, "kind": e.kind, "detail": e.detail} for e in scoped],
    }
    fees = _replay_fees(scoped, close_reason=deal.close_reason)
    if deal.closed_at_us is None:
        stats_deals = deals
        if runtime is not None and deal.symbol:
            stats_deals = tuple(d for d in deals if d.symbol == deal.symbol) or deals
        stats = bot_statistics(stats_deals, runtime, budget=record.budget)
        live = stats["active_deal"] or {}
        return {
            **base,
            "duration_us": None,
            "qty": live.get("qty"),
            "cost": live.get("cost"),
            "average_price": live.get("average_price"),
            "mark_price": live.get("mark_price"),
            "unrealized_profit": live.get("unrealized_profit"),
            "unrealized_percent": live.get("unrealized_percent"),
            "take_profit_price": live.get("take_profit_price"),
            "next_safety_order_price": live.get("next_safety_order_price"),
            "cumulative_profit": None,
            "fees": fees,
            "gross_profit": None,
        }
    replayed = _replay_buys(scoped)
    cumulative = next(
        (row["cumulative_profit"] for row in _deal_rows(deals) if row["deal"] == deal.deal_sequence), None
    )
    # Cancelled books profit "0" by convention while buy fees stay sunk,
    # so gross is undefined there; everywhere else net + fees reconstructs
    # the exact gross result the engine realized.
    gross = None
    if deal.profit is not None and fees is not None and deal.close_reason != "CANCELLED":
        gross = exact_text(number(deal.profit) + number(fees))
    return {
        **base,
        "duration_us": deal.closed_at_us - deal.started_at_us,
        "qty": replayed[0] if replayed else None,
        "cost": replayed[1] if replayed else None,
        "average_price": replayed[2] if replayed else None,
        "mark_price": None,
        "unrealized_profit": None,
        "unrealized_percent": None,
        "take_profit_price": None,
        "next_safety_order_price": None,
        "cumulative_profit": cumulative,
        "fees": fees,
        "gross_profit": gross,
    }


def _day_start_us(value: str) -> int:
    parsed = date.fromisoformat(value)
    return int(datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc).timestamp()) * 1_000_000


def register_routes(app: FastAPI, deps: V2BotDeps) -> None:
    lock = Lock()

    def sector_problem(exc: SectorDcaError) -> JSONResponse:
        if exc.field is None:
            field = "strategy"
        elif exc.field == "budget":
            field = "budget"
        else:
            field = f"strategy.{exc.field}"
        errors = [{"field": field, "code": exc.code}]
        return deps.problem(422, exc.code, "Bot ayarları geçersiz", str(exc).split(": ", 1)[-1], errors=errors)

    def grid_problem(exc: SpotGridEngineError) -> JSONResponse:
        errors = [{"field": _GRID_FIELD.get(exc.code, "strategy"), "code": exc.code}]
        return deps.problem(422, exc.code, "Grid bot ayarları geçersiz", str(exc).split(": ", 1)[-1], errors=errors)

    def fgrid_problem(exc: FuturesGridEngineError) -> JSONResponse:
        errors = [{"field": _FGRID_FIELD.get(exc.code, "strategy"), "code": exc.code}]
        return deps.problem(422, exc.code, "Futures grid bot ayarları geçersiz", str(exc).split(": ", 1)[-1], errors=errors)

    def market_problem(exc: MarketUnavailable) -> JSONResponse:
        return deps.problem(502, exc.code, "Piyasa verisi alınamadı", str(exc))

    def store_problem(exc: BotStoreError) -> JSONResponse:
        status = _STORE_STATUS.get(exc.code, 500)
        return deps.problem(status, exc.code, "Bot işlemi yapılamadı", str(exc).split(": ", 1)[-1])

    def action_problem(exc: DealActionError) -> JSONResponse:
        return deps.problem(409, exc.code, "Deal işlemi yapılamadı", str(exc).split(": ", 1)[-1])

    def replay_problem(exc: ReplayError) -> JSONResponse:
        title = (
            "Geçmiş veri alınamadı"
            if exc.status == 502
            else "Bot geçmişte çalıştırılamaz"
            if exc.status == 409
            else "Geçmiş çalıştırma ayarları geçersiz"
        )
        errors = [{"field": exc.field, "code": exc.code}] if exc.field is not None else None
        return deps.problem(exc.status, exc.code, title, str(exc), errors=errors)

    @app.post("/api/v2/bots/preview", tags=["v2-bots"], response_model=DealPlanEnvelope)
    def preview_bot(body: BotPreviewRequest):
        """Deal plan in sector terms at the current price; nothing is stored."""
        try:
            return {"data": _plan_from(body.strategy, body.budget, deps)[0]}
        except SectorDcaError as exc:
            return sector_problem(exc)
        except MarketUnavailable as exc:
            return market_problem(exc)

    @app.post("/api/v2/bots", tags=["v2-bots"], response_model=BotEnvelope, status_code=201)
    def create_bot(body: BotCreateRequest):
        """Validate against live venue rules and price, then store as STOPPED."""
        try:
            plan, params = _plan_from(body.strategy, body.budget, deps)
        except SectorDcaError as exc:
            return sector_problem(exc)
        except MarketUnavailable as exc:
            return market_problem(exc)
        if not plan["within_budget"]:
            return sector_problem(
                SectorDcaError(
                    "SECTOR_BUDGET_TOO_LOW",
                    f"Gereken sermaye ({plan['required_funds']} USDT) bütçeyi aşıyor.",
                    field="budget",
                )
            )
        if plan.get("within_total_budget") is False:
            return sector_problem(
                SectorDcaError(
                    "SECTOR_MULTI_BUDGET_EXCEEDED",
                    f"{params.max_active_deals} eşzamanlı deal için gereken ({plan['total_required_funds']} USDT) bütçeyi aşıyor.",
                    field="budget",
                )
            )
        now = deps.clock_us()
        # Stored strategies stay explicit: an unset leverage resolves here
        # to the market default (futures 3x, spot 1x), never downstream.
        strategy_data = body.strategy.model_dump()
        strategy_data["leverage"] = params.leverage
        strategy_data["symbols"] = list(params.symbols)
        strategy_data["max_active_deals"] = params.max_active_deals
        record = BotRecord(
            bot_id=f"bot_{secrets.token_hex(6)}",
            name=body.name.strip() or body.strategy.symbol,
            strategy_type="DCA",
            mode=body.mode,
            symbol=body.strategy.symbol,
            strategy=strategy_data,
            budget=exact_text(number(body.budget)),
            status="STOPPED",
            status_reason=None,
            revision=1,
            created_at_us=now,
            updated_at_us=now,
            archived_at_us=None,
        )
        try:
            with lock:
                stored = deps.store.create(record)
        except BotStoreError as exc:
            return store_problem(exc)
        if deps.record_event is not None:
            deps.record_event("BOT_CREATED", stored.bot_id, f"Bot oluşturuldu ({stored.name}).", now)
        return JSONResponse(status_code=201, content={"data": _bot(stored).model_dump()})

    def _grid_plan_from(strategy: GridBotStrategy, budget: str, *, enforce_min_notional: bool):
        rules = deps.market.symbol_rules(strategy.symbol)
        price = deps.market.last_price(strategy.symbol)
        config = build_grid_config(
            strategy.model_dump(), rules, investment=exact_text(number(budget)), enforce_min_notional=enforce_min_notional
        )
        return config, rules, price

    @app.post("/api/v2/grid-bots/preview", tags=["v2-bots"], response_model=GridPreviewEnvelope)
    def preview_grid_bot(body: GridBotPreviewRequest):
        """Grid levels and entry position at the current price; nothing is stored."""
        try:
            config, rules, price = _grid_plan_from(body.strategy, body.budget, enforce_min_notional=False)
        except SpotGridEngineError as exc:
            return grid_problem(exc)
        except MarketUnavailable as exc:
            return market_problem(exc)
        summary = describe_grid(config)
        if price < number(config.lower_price):
            position = "BELOW"
        elif price > number(config.upper_price):
            position = "ABOVE"
        else:
            position = "WITHIN"
        return {
            "data": {
                "symbol": body.strategy.symbol,
                "reference_price": exact_text(price),
                "entry_position": position,
                "levels": summary["levels"],
                "interval_count": summary["interval_count"],
                "investment_quote": summary["investment_quote"],
                "quote_per_grid": summary["quote_per_grid"],
                "base_step_size": summary["base_step_size"],
                "fee_rate": summary["fee_rate"],
                "within_min_notional": number(config.quote_per_grid) >= number(rules.min_notional),
                "stop_loss_price": summary["stop_loss_price"],
                "take_profit_pct": summary["take_profit_pct"],
                "trailing_up_pct": summary["trailing_up_pct"],
                "trailing_down_pct": summary["trailing_down_pct"],
            }
        }

    @app.post("/api/v2/grid-bots", tags=["v2-bots"], response_model=BotEnvelope, status_code=201)
    def create_grid_bot(body: GridBotCreateRequest):
        """Validate against live venue rules and price, then store as STOPPED."""
        try:
            _grid_plan_from(body.strategy, body.budget, enforce_min_notional=True)
        except SpotGridEngineError as exc:
            return grid_problem(exc)
        except MarketUnavailable as exc:
            return market_problem(exc)
        now = deps.clock_us()
        record = BotRecord(
            bot_id=f"bot_{secrets.token_hex(6)}",
            name=body.name.strip() or body.strategy.symbol,
            strategy_type="GRID",
            mode=body.mode,
            symbol=body.strategy.symbol,
            strategy=body.strategy.model_dump(),
            budget=exact_text(number(body.budget)),
            status="STOPPED",
            status_reason=None,
            revision=1,
            created_at_us=now,
            updated_at_us=now,
            archived_at_us=None,
        )
        try:
            with lock:
                stored = deps.store.create(record)
        except BotStoreError as exc:
            return store_problem(exc)
        if deps.record_event is not None:
            deps.record_event("BOT_CREATED", stored.bot_id, f"Grid bot oluşturuldu ({stored.name}).", now)
        return JSONResponse(status_code=201, content={"data": _bot(stored).model_dump()})

    def _fgrid_plan_from(strategy: FuturesGridBotStrategy, budget: str, *, enforce_min_notional: bool):
        if deps.futures_market is None:
            raise MarketUnavailable("FUTURES_MARKET_UNAVAILABLE", "Futures market bağlı değil.")
        rules = deps.futures_market.symbol_rules(strategy.symbol)
        if rules.status != "TRADING":
            raise FuturesGridEngineError("FGRID_SYMBOL_HALTED", "Sembol işlemde değil.")
        if rules.contract_type != "PERPETUAL":
            raise FuturesGridEngineError("FUTURES_GRID_CONTRACT_UNSUPPORTED", "Yalnız USDT-M perpetual desteklenir.")
        price = deps.futures_market.last_price(strategy.symbol)
        config = build_futures_grid_config(
            strategy.model_dump(), rules, investment=exact_text(number(budget)), enforce_min_notional=enforce_min_notional
        )
        return config, rules, price

    @app.post("/api/v2/futures-grid-bots/preview", tags=["v2-bots"], response_model=FuturesGridPreviewEnvelope)
    def preview_futures_grid_bot(body: FuturesGridBotPreviewRequest):
        """Futures grid levels and entry position at the current mark; nothing is stored."""
        try:
            config, rules, price = _fgrid_plan_from(body.strategy, body.budget, enforce_min_notional=False)
        except FuturesGridEngineError as exc:
            return fgrid_problem(exc)
        except MarketUnavailable as exc:
            return market_problem(exc)
        summary = describe_futures_grid(config)
        if price < number(config.lower_price):
            position = "BELOW"
        elif price > number(config.upper_price):
            position = "ABOVE"
        else:
            position = "WITHIN"
        return {
            "data": {
                "symbol": body.strategy.symbol,
                "direction": summary["direction"],
                "leverage": summary["leverage"],
                "reference_price": exact_text(price),
                "entry_position": position,
                "levels": summary["levels"],
                "interval_count": summary["interval_count"],
                "investment_quote": summary["investment_quote"],
                "quote_per_grid": summary["quote_per_grid"],
                "notional_per_grid": exact_text(number(config.quote_per_grid) * config.leverage),
                "base_step_size": summary["base_step_size"],
                "fee_rate": summary["fee_rate"],
                "within_min_notional": number(config.quote_per_grid) * config.leverage >= number(rules.min_notional),
                "stop_loss_price": summary["stop_loss_price"],
                "take_profit_pct": summary["take_profit_pct"],
                "trailing_up_pct": summary["trailing_up_pct"],
                "trailing_down_pct": summary["trailing_down_pct"],
            }
        }

    @app.post("/api/v2/futures-grid-bots", tags=["v2-bots"], response_model=BotEnvelope, status_code=201)
    def create_futures_grid_bot(body: FuturesGridBotCreateRequest):
        """Validate against live venue rules and mark, then store as STOPPED."""
        try:
            _fgrid_plan_from(body.strategy, body.budget, enforce_min_notional=True)
        except FuturesGridEngineError as exc:
            return fgrid_problem(exc)
        except MarketUnavailable as exc:
            return market_problem(exc)
        now = deps.clock_us()
        record = BotRecord(
            bot_id=f"bot_{secrets.token_hex(6)}",
            name=body.name.strip() or body.strategy.symbol,
            strategy_type="FUTURES_GRID",
            mode=body.mode,
            symbol=body.strategy.symbol,
            strategy=body.strategy.model_dump(),
            budget=exact_text(number(body.budget)),
            status="STOPPED",
            status_reason=None,
            revision=1,
            created_at_us=now,
            updated_at_us=now,
            archived_at_us=None,
        )
        try:
            with lock:
                stored = deps.store.create(record)
        except BotStoreError as exc:
            return store_problem(exc)
        if deps.record_event is not None:
            deps.record_event("BOT_CREATED", stored.bot_id, f"Futures grid bot oluşturuldu ({stored.name}).", now)
        return JSONResponse(status_code=201, content={"data": _bot(stored).model_dump()})

    def _futures_grid_state(record: BotRecord, runtime):
        if deps.futures_market is None:
            raise MarketUnavailable("FUTURES_MARKET_UNAVAILABLE", "Futures market bağlı değil.")
        if runtime is None:
            rules = deps.futures_market.symbol_rules(record.symbol)
            config = build_futures_grid_config(record.strategy, rules, investment=record.budget)
            state = create_futures_grid(config)
            last_bar_open_us = None
            updated_at_us = None
        else:
            config = futures_config_from_dict(runtime.config)
            state = restore_futures_grid(runtime.snapshot, config)
            last_bar_open_us = runtime.last_bar_open_us
            updated_at_us = runtime.updated_at_us
        last_price = deps.futures_market.last_price(record.symbol)
        fills = state.fills
        recent = fills[-50:] if len(fills) > 50 else fills
        return {
            "data": {
                "grid_status": state.status.value,
                "direction": config.direction.value,
                "leverage": config.leverage,
                "entry_price": state.entry_price,
                "last_price": exact_text(last_price),
                "levels": list(state.levels),
                "pending": list(state.pending),
                "locked_margin": list(state.locked_margin),
                "wallet_free": state.wallet_free,
                "open_lots": [
                    {
                        "interval": lot.interval,
                        "quantity": lot.quantity,
                        "entry_price": lot.entry_price,
                        "locked_margin": lot.locked_margin,
                    }
                    for lot in state.open_lots
                ],
                "cycles_closed": state.cycles_closed,
                "realized_gross_pnl": state.realized_gross_pnl,
                "fees_paid_quote": state.fees_paid_quote,
                "funding_cashflow": state.funding_cashflow,
                "funding_events_count": len(state.funding_events),
                "equity_at_last": futures_grid_equity_quote(state, config, mark_price=exact_text(last_price)),
                "fills_recent": [
                    {"fill_id": fill.fill_id, "side": fill.side.value, "price": fill.price, "quantity": fill.quantity}
                    for fill in reversed(recent)
                ],
                "trailing_shifts": state.trailing_shifts,
                "liq_estimate_price": state.liq_estimate_price,
                "liq_estimate_tier": state.liq_estimate_tier,
                "last_bar_open_us": last_bar_open_us,
                "updated_at_us": updated_at_us,
            }
        }

    @app.get("/api/v2/bots/{bot_id}/grid", tags=["v2-bots"], response_model=GridStateEnvelope | FuturesGridStateEnvelope)
    def get_grid_state(bot_id: str):
        """Live grid holdings: levels, pendings, equity at the last price."""
        try:
            with lock:
                record = deps.store.get(bot_id)
                runtime = deps.store.get_grid_runtime(bot_id)
        except BotStoreError as exc:
            return store_problem(exc)
        if record.strategy_type == "FUTURES_GRID":
            try:
                return _futures_grid_state(record, runtime)
            except FuturesGridEngineError as exc:
                return fgrid_problem(exc)
            except MarketUnavailable as exc:
                return market_problem(exc)
        if record.strategy_type != "GRID":
            return deps.problem(404, "GRID_STATE_UNAVAILABLE", "Grid durumu yok", "Bu bot grid botu değil.")
        try:
            if runtime is None:
                rules = deps.market.symbol_rules(record.symbol)
                config = build_grid_config(record.strategy, rules, investment=record.budget)
                state = create_grid(config)
                last_bar_open_us = None
                updated_at_us = None
            else:
                config = config_from_dict(runtime.config)
                state = restore_grid(runtime.snapshot, config)
                last_bar_open_us = runtime.last_bar_open_us
                updated_at_us = runtime.updated_at_us
            last_price = deps.market.last_price(record.symbol)
        except SpotGridEngineError as exc:
            return grid_problem(exc)
        except MarketUnavailable as exc:
            return market_problem(exc)
        fills = state.inventory.fills
        recent = fills[-50:] if len(fills) > 50 else fills
        return {
            "data": {
                "grid_status": state.status.value,
                "entry_price": state.entry_price,
                "last_price": exact_text(last_price),
                "levels": list(state.levels),
                "pending": list(state.pending),
                "locked_quote": list(state.locked_quote),
                "locked_base": list(state.locked_base),
                "quote_reserve": state.quote_reserve,
                "base_free": state.base_free,
                "cycles_closed": state.cycles_closed,
                "realized_profit_quote": state.realized_profit_quote,
                "fees_paid_quote": state.fees_paid_quote,
                "equity_at_last": grid_equity_quote(state, mark_price=exact_text(last_price)),
                "fills_recent": [
                    {"fill_id": fill.fill_id, "side": fill.side.value, "price": fill.price, "base_quantity": fill.base_quantity}
                    for fill in reversed(recent)
                ],
                "trailing_shifts": state.trailing_shifts,
                "last_bar_open_us": last_bar_open_us,
                "updated_at_us": updated_at_us,
            }
        }

    @app.get("/api/v2/bots", tags=["v2-bots"], response_model=BotListEnvelope)
    def list_bots(include_archived: bool = False):
        with lock:
            records = deps.store.list(include_archived=include_archived)
        return {"data": [_bot(record) for record in records]}

    @app.get("/api/v2/bots/{bot_id}", tags=["v2-bots"], response_model=BotEnvelope)
    def get_bot(bot_id: str):
        try:
            with lock:
                return {"data": _bot(deps.store.get(bot_id))}
        except BotStoreError as exc:
            return store_problem(exc)

    # NOTE: fixed sub-paths must register before `/{bot_id}/{action}`,
    # otherwise the action route shadows them (FastAPI matches in order).
    @app.post("/api/v2/bots/{bot_id}/copy", tags=["v2-bots"], response_model=BotEnvelope)
    def copy_bot(bot_id: str, body: BotCopyRequest):
        """Duplicate a bot's setup as a fresh STOPPED bot.

        Strategy, budget, mode and symbol carry over untouched; no
        runtime, deals or events are copied. The stored setup is not
        re-validated against venue rules (offline-first); starting the
        copy is the honest gate if rules moved on.
        """
        try:
            with lock:
                source = deps.store.get(bot_id)
        except BotStoreError as exc:
            return store_problem(exc)
        given = (body.name or "").strip()
        if given:
            name = given
        else:
            head = (source.name.strip() or source.symbol)[:60].rstrip()
            name = f"{head} (2)"
        now = deps.clock_us()
        record = BotRecord(
            bot_id=f"bot_{secrets.token_hex(6)}",
            name=name,
            strategy_type=source.strategy_type,
            mode=source.mode,
            symbol=source.symbol,
            strategy=copy.deepcopy(source.strategy),
            budget=source.budget,
            status="STOPPED",
            status_reason=None,
            revision=1,
            created_at_us=now,
            updated_at_us=now,
            archived_at_us=None,
        )
        try:
            with lock:
                stored = deps.store.create(record)
        except BotStoreError as exc:
            return store_problem(exc)
        if deps.record_event is not None:
            deps.record_event("BOT_CREATED", stored.bot_id, f"Bot kopyalandı ({stored.name}).", now)
        return JSONResponse(status_code=201, content={"data": _bot(stored).model_dump()})

    @app.post("/api/v2/bots/{bot_id}/replay", tags=["v2-bots"], response_model=BotReplayEnvelope)
    def replay_bot(bot_id: str, body: BotReplayRequest):
        """Run a fresh STOPPED bot over closed 1m history; runtime, deals and
        events persist. Afterwards the bot can start and continue live."""
        if deps.on_replay is None:
            return deps.problem(
                409,
                "BOT_RUNNER_UNAVAILABLE",
                "Bot çalıştırıcı henüz yok",
                "Botları çalıştıran servis henüz devrede değil; geçmiş çalıştırma yapılamaz.",
            )
        try:
            start_us = _day_start_us(body.start_date)
            end_us = _day_start_us(body.end_date) + 86_400_000_000
        except ValueError:
            return deps.problem(
                422,
                "REPLAY_DATE_INVALID",
                "Geçmiş çalıştırma ayarları geçersiz",
                "Tarih geçersiz.",
                errors=[{"field": "start_date", "code": "REPLAY_DATE_INVALID"}],
            )
        try:
            with lock:
                record = deps.store.get(bot_id)
        except BotStoreError as exc:
            return store_problem(exc)
        if record.mode != "PAPER":
            return deps.problem(
                409,
                "TESTNET_REPLAY_NOT_ENABLED",
                "Bot geçmişte çalıştırılamaz",
                "Geçmiş çalıştırma şimdilik yalnız Paper botlarda yapılabilir.",
            )
        try:
            result = deps.on_replay(bot_id, start_us, end_us)
        except ReplayError as exc:
            return replay_problem(exc)
        except SectorDcaError as exc:
            return sector_problem(exc)
        except SpotGridEngineError as exc:
            return grid_problem(exc)
        except FuturesGridEngineError as exc:
            return fgrid_problem(exc)
        except MarketUnavailable as exc:
            return market_problem(exc)
        if deps.record_event is not None:
            deps.record_event(
                "BOT_REPLAYED",
                bot_id,
                f"Bot geçmişte çalıştı ({result['bars']} mum, {result['deals_opened']} deal).",
                deps.clock_us(),
            )
        return {"data": result}

    @app.post("/api/v2/bots/{bot_id}/{action}", tags=["v2-bots"], response_model=BotEnvelope)
    def act_on_bot(bot_id: str, action: Literal["start", "pause", "resume", "stop", "archive"], body: BotActionRequest):
        """Lifecycle change with optimistic concurrency on `revision`.

        start/resume are refused while no runner exists: a bot must never be
        shown as RUNNING when nothing drives it."""
        if action in ("start", "resume") and not deps.runner_available():
            return deps.problem(
                409,
                "BOT_RUNNER_UNAVAILABLE",
                "Bot çalıştırıcı henüz yok",
                "Botları otomatik çalıştıran servis henüz devrede değil; bot kaydedildi ama başlatılamaz.",
            )
        if action == "start":
            try:
                with lock:
                    record = deps.store.get(bot_id)
            except BotStoreError as exc:
                return store_problem(exc)
            if record.mode != "PAPER":
                return deps.problem(
                    409,
                    "TESTNET_RUNNER_NOT_ENABLED",
                    "Testnet otomatik çalışma kapalı",
                    "Testnet botlarının otomatik çalışması için ayrı onay gerekiyor; şimdilik yalnız Paper botlar başlatılabilir.",
                )
            if deps.on_start is not None:
                try:
                    try:
                        deps.on_start(record)
                    except SpotGridEngineError as grid_exc:
                        return grid_problem(grid_exc)
                    except FuturesGridEngineError as fgrid_exc:
                        return fgrid_problem(fgrid_exc)
                except SectorDcaError as exc:
                    return sector_problem(exc)
                except MarketUnavailable as exc:
                    return market_problem(exc)
        try:
            with lock:
                if action == "archive":
                    record = deps.store.archive(bot_id, expected_revision=body.revision, now_us=deps.clock_us())
                else:
                    record = deps.store.apply_action(
                        bot_id, action, expected_revision=body.revision, now_us=deps.clock_us()
                    )
        except BotStoreError as exc:
            return store_problem(exc)
        if deps.record_event is not None:
            kind, verb = _ACTION_LANDMARK[action]
            deps.record_event(kind, record.bot_id, f"Bot {verb} ({record.name}).", deps.clock_us())
        return {"data": _bot(record)}

    @app.get("/api/v2/bots/{bot_id}/deals", tags=["v2-bots"], response_model=BotDealsEnvelope)
    def list_bot_deals(bot_id: str):
        """Every deal the runner recorded for this bot, oldest first."""
        try:
            with lock:
                deps.store.get(bot_id)
                deals = deps.store.list_deals(bot_id)
        except BotStoreError as exc:
            return store_problem(exc)
        return {"data": _deal_rows(deals)}

    @app.get("/api/v2/bots/{bot_id}/events", tags=["v2-bots"], response_model=BotEventsEnvelope)
    def list_bot_events(bot_id: str, limit: Annotated[int, Field(ge=1, le=500)] = 50):
        """Newest runner events first."""
        try:
            with lock:
                deps.store.get(bot_id)
                events = deps.store.list_events(bot_id, limit=limit)
        except BotStoreError as exc:
            return store_problem(exc)
        return {"data": [{"time_us": e.time_us, "kind": e.kind, "detail": e.detail} for e in events]}

    @app.get("/api/v2/deals", tags=["v2-bots"], response_model=DealListEnvelope)
    def list_deals(
        status: Literal["active", "closed"] | None = None,
        limit: Annotated[int, Field(ge=1, le=500)] = 100,
        offset: Annotated[int, Field(ge=0)] = 0,
    ):
        """Every deal across bots, newest first; the unified deal list."""
        try:
            with lock:
                rows = deps.store.list_all_deals(status=status, limit=limit, offset=offset)
        except BotStoreError as exc:
            return store_problem(exc)
        return {
            "data": [
                {
                    "bot_id": record.bot_id,
                    "bot_name": record.name,
                    "symbol": deal.symbol or record.symbol,
                    "mode": record.mode,
                    "direction": record.strategy.get("direction", "LONG"),
                    "deal": deal.deal_sequence,
                    "started_at_us": deal.started_at_us,
                    "closed_at_us": deal.closed_at_us,
                    "safety_orders_filled": deal.safety_orders_filled,
                    "manual_orders_filled": deal.manual_orders_filled,
                    "profit": deal.profit,
                    "close_reason": deal.close_reason,
                }
                for record, deal in rows
            ]
        }

    @app.get("/api/v2/bots/{bot_id}/deals/{deal_seq}", tags=["v2-bots"], response_model=DealDetailEnvelope)
    def get_deal(bot_id: str, deal_seq: int):
        """One deal with live economics (open) or replayed fills (closed)."""
        try:
            with lock:
                record = deps.store.get(bot_id)
                deals = deps.store.list_deals(bot_id)
                runtime = deps.store.get_runtime(bot_id)
                events = deps.store.list_events(bot_id, limit=500)
        except BotStoreError as exc:
            return store_problem(exc)
        deal = next((d for d in deals if d.deal_sequence == deal_seq), None)
        if deal is None:
            return deps.problem(404, "DEAL_NOT_FOUND", "Deal bulunamadı", "Bu botta böyle bir deal yok.")
        if runtime is None and deal.symbol:
            pair = next(
                (row for row in deps.store.get_pair_runtimes(bot_id) if row.symbol == deal.symbol), None
            )
            if pair is not None:
                runtime = BotRuntime(
                    bot_id, pair.config, pair.state, 0, pair.prev_net,
                    pair.last_bar_open_us, pair.updated_at_us,
                )
        return {"data": _deal_detail(record, deals, deal, runtime, events)}

    def run_deal_action(bot_id: str, deal_seq: int, revision: int, action: str, amount: str | None):
        # Market read stays outside the guard; everything mutating runs
        # inside it, so a runner tick cannot interleave and lose the write.
        record = deps.store.get(bot_id)
        if record.archived_at_us is not None:
            raise BotStoreError("BOT_ARCHIVED", "Arşivlenmiş bot değiştirilemez.")
        if record.status == "ERROR" and action == "add-funds":
            raise DealActionError("DEAL_ACTION_BLOCKED", "Hatalı bota fon eklenemez; önce kapatın veya durdurun.")
        price = None
        if action in ("close", "add-funds"):
            price = deps.market.last_price(record.symbol)
        with deps.store.guarded():
            record = deps.store.get(bot_id)
            if record.revision != revision:
                raise BotStoreError("BOT_REVISION_CONFLICT", "Bot başka bir yerde değişti; sayfayı yenileyin.")
            runtime = deps.store.get_runtime(bot_id)
            pair = None
            if runtime is None:
                pairs = {row.symbol: row for row in deps.store.get_pair_runtimes(bot_id)}
                deal_row = next(
                    (d for d in deps.store.list_deals(bot_id) if d.deal_sequence == deal_seq), None
                )
                if deal_row is None:
                    raise BotStoreError("DEAL_NOT_FOUND", "Bu botta böyle bir deal yok.")
                pair = pairs.get(deal_row.symbol or record.symbol)
                if pair is None:
                    raise BotStoreError("DEAL_NOT_FOUND", "Botun kayıtlı koşusu yok.")
                if action in ("close", "add-funds") and pair.symbol != record.symbol:
                    price = deps.market.last_price(pair.symbol)
                runtime = BotRuntime(
                    bot_id, pair.config, pair.state, 0, pair.prev_net,
                    pair.last_bar_open_us, pair.updated_at_us,
                )
            deals = deps.store.list_deals(bot_id)
            deal = next((d for d in deals if d.deal_sequence == deal_seq), None)
            if deal is None:
                raise BotStoreError("DEAL_NOT_FOUND", "Bu botta böyle bir deal yok.")
            config = Config.parse(runtime.config)
            now = deps.clock_us()
            if action == "close":
                assert price is not None
                result = close_at_market(config, runtime.state, deal, runtime.prev_net, price=price, now_us=now)
            elif action == "cancel":
                result = cancel_deal(config, runtime.state, deal, runtime.prev_net, now_us=now)
            else:
                assert price is not None and amount is not None
                result = add_funds(
                    config, runtime.state, deal, runtime.prev_net,
                    quote_amount=number(amount), price=price, now_us=now,
                )
            if pair is None:
                next_runtime = BotRuntime(
                    runtime.bot_id, runtime.config, result.state, runtime.deal_sequence,
                    result.prev_net, runtime.last_bar_open_us, now,
                )
                deps.store.save_runtime(next_runtime, deals=(result.deal,), events=(result.event,))
            else:
                next_pair = BotPairRuntime(
                    pair.bot_id, pair.symbol, pair.config, result.state,
                    result.prev_net, pair.last_bar_open_us, now,
                )
                deps.store.save_pair_step((next_pair,), deals=(result.deal,), events=(result.event,))
                next_runtime = BotRuntime(
                    runtime.bot_id, runtime.config, result.state, runtime.deal_sequence,
                    result.prev_net, runtime.last_bar_open_us, now,
                )
            updated = deps.store.bump_revision(bot_id, expected_revision=revision, now_us=now)
            deals = deps.store.list_deals(bot_id)
            events = deps.store.list_events(bot_id, limit=500)
        if deps.record_event is not None:
            kind, verb = _DEAL_LANDMARK[action]
            deps.record_event(kind, f"{bot_id}:{deal_seq}", f"Deal {deal_seq} {verb}.", now)
        return {"data": _deal_detail(updated, deals, result.deal, next_runtime, events)}

    @app.post("/api/v2/bots/{bot_id}/deals/{deal_seq}/close", tags=["v2-bots"], response_model=DealDetailEnvelope)
    def close_deal(bot_id: str, deal_seq: int, body: DealActionBody):
        """Close the open deal at the current market price (plus fees)."""
        try:
            return run_deal_action(bot_id, deal_seq, body.revision, "close", None)
        except BotStoreError as exc:
            return store_problem(exc)
        except DealActionError as exc:
            return action_problem(exc)
        except MarketUnavailable as exc:
            return market_problem(exc)

    @app.post("/api/v2/bots/{bot_id}/deals/{deal_seq}/cancel", tags=["v2-bots"], response_model=DealDetailEnvelope)
    def cancel_deal_endpoint(bot_id: str, deal_seq: int, body: DealActionBody):
        """Abandon the deal without a sale; books profit zero."""
        try:
            return run_deal_action(bot_id, deal_seq, body.revision, "cancel", None)
        except BotStoreError as exc:
            return store_problem(exc)
        except DealActionError as exc:
            return action_problem(exc)
        except MarketUnavailable as exc:
            return market_problem(exc)

    @app.post("/api/v2/bots/{bot_id}/deals/{deal_seq}/add-funds", tags=["v2-bots"], response_model=DealDetailEnvelope)
    def add_funds_endpoint(bot_id: str, deal_seq: int, body: AddFundsBody):
        """Buy extra base into the open deal, outside the safety plan."""
        try:
            return run_deal_action(bot_id, deal_seq, body.revision, "add-funds", body.amount)
        except BotStoreError as exc:
            return store_problem(exc)
        except DealActionError as exc:
            return action_problem(exc)
        except MarketUnavailable as exc:
            return market_problem(exc)

    @app.get("/api/v2/bots/{bot_id}/stats", tags=["v2-bots"], response_model=BotStatsEnvelope)
    def get_bot_stats(bot_id: str):
        """Exact totals over closed deals plus the live state of the open deal."""
        try:
            with lock:
                record = deps.store.get(bot_id)
                deals = deps.store.list_deals(bot_id)
                runtime = deps.store.get_runtime(bot_id)
                pairs = {row.symbol: row for row in deps.store.get_pair_runtimes(bot_id)}
        except BotStoreError as exc:
            return store_problem(exc)
        if runtime is None and pairs:
            first_open = next((d for d in deals if d.closed_at_us is None), None)
            pair = pairs.get(first_open.symbol) if first_open is not None else None
            if pair is None:
                pair = next(iter(pairs.values()))
            runtime = BotRuntime(
                bot_id, pair.config, pair.state, 0, pair.prev_net,
                min(row.last_bar_open_us for row in pairs.values()), pair.updated_at_us,
            )
        return {"data": bot_statistics(deals, runtime, budget=record.budget)}


class LiveBinanceMarket:
    """Credential-free Binance spot rules and last price for bot validation."""

    RULES_TTL_SECONDS = 600

    def __init__(self, *, fetch_rules, fetch_trades, transport_error: type[Exception], time_unit) -> None:
        self._fetch_rules = fetch_rules
        self._fetch_trades = fetch_trades
        self._error = transport_error
        self._time_unit = time_unit
        self._rules_cache: dict[str, tuple[float, SymbolRules]] = {}
        self._rules_lock = Lock()

    def symbol_rules(self, symbol: str) -> SymbolRules:
        """Venue rules change rarely; a successful answer is reused for a
        bounded TTL so a live wizard preview is not a ~1.5 s venue call."""
        with self._rules_lock:
            cached = self._rules_cache.get(symbol)
            if cached is not None and time.monotonic() - cached[0] < self.RULES_TTL_SECONDS:
                return cached[1]
        try:
            rules = self._fetch_rules(symbol, allowed_symbols=frozenset({symbol}))
        except self._error as exc:
            raise MarketUnavailable(getattr(exc, "code", "PUBLIC_UPSTREAM_UNAVAILABLE"), str(exc)) from exc
        result = SymbolRules(
            symbol=rules.symbol,
            status=rules.status,
            base_asset=rules.base_asset,
            quote_asset=rules.quote_asset,
            tick=rules.tick,
            qty_step=rules.qty_step,
            min_qty=rules.min_qty,
            min_notional=rules.min_notional,
        )
        with self._rules_lock:
            self._rules_cache[symbol] = (time.monotonic(), result)
        return result

    def last_price(self, symbol: str) -> Q:
        now_us = time.time_ns() // 1000
        try:
            prints = self._fetch_trades(
                symbol,
                limit=1,
                allowed_symbols=frozenset({symbol}),
                receive_time_us=now_us,
                processing_time_us=now_us,
                time_unit=self._time_unit,
            )
        except self._error as exc:
            raise MarketUnavailable(getattr(exc, "code", "PUBLIC_UPSTREAM_UNAVAILABLE"), str(exc)) from exc
        if not prints:
            raise MarketUnavailable("PUBLIC_SYMBOL_NO_TRADES", "Bu sembol için son işlem yok.")
        return number(prints[-1].price)


class LiveBinanceFuturesMarket:
    """Credential-free Binance USDT-M rules and mark price for bot validation."""

    RULES_TTL_SECONDS = 600

    def __init__(self, *, fetch_rules, fetch_premium, transport_error: type[Exception]) -> None:
        self._fetch_rules = fetch_rules
        self._fetch_premium = fetch_premium
        self._error = transport_error
        self._rules_cache: dict[str, tuple[float, object]] = {}
        self._rules_lock = Lock()

    def symbol_rules(self, symbol: str):
        """Venue rules change rarely; a successful answer is reused for a
        bounded TTL so a live wizard preview is not a ~1.5 s venue call."""
        with self._rules_lock:
            cached = self._rules_cache.get(symbol)
            if cached is not None and time.monotonic() - cached[0] < self.RULES_TTL_SECONDS:
                return cached[1]
        try:
            rules = self._fetch_rules(symbol, allowed_symbols=frozenset({symbol}))
        except self._error as exc:
            raise MarketUnavailable(getattr(exc, "code", "PUBLIC_UPSTREAM_UNAVAILABLE"), str(exc)) from exc
        with self._rules_lock:
            self._rules_cache[symbol] = (time.monotonic(), rules)
        return rules

    def last_price(self, symbol: str) -> Q:
        """Current mark price; grids plan and value equity against mark."""
        try:
            premium = self._fetch_premium(symbol, allowed_symbols=frozenset({symbol}))
        except self._error as exc:
            raise MarketUnavailable(getattr(exc, "code", "PUBLIC_UPSTREAM_UNAVAILABLE"), str(exc)) from exc
        return number(premium.mark_price)


def load_template(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
