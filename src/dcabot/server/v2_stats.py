"""Faz W-B5 portfolio stats: summary, equity, daily profit, splits.

Read-only over the bot store; the runner feeds the equity series with
hourly snapshots. Money stays exact decimal strings; "today" is UTC.
"""

from dataclasses import dataclass
from threading import Lock
from typing import Annotated, Callable, Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from dcabot.application.portfolio_stats import (
    DAY_US,
    daily_profit,
    portfolio_summary,
    profit_by_bot,
    profit_by_pair,
)
from dcabot.persistence.bot_store import BotStore

RANGE_US = {"7d": 7 * DAY_US, "30d": 30 * DAY_US}


class PortfolioSummary(BaseModel):
    total_value: str
    today_profit: str
    active_bots: int
    deployed_capital: str


class EquityPoint(BaseModel):
    time_us: int
    equity: str
    realized: str
    unrealized: str


class DailyPoint(BaseModel):
    day_start_us: int
    profit: str


class BotProfitRow(BaseModel):
    bot_id: str
    bot_name: str
    profit: str
    deals_completed: int


class PairProfitRow(BaseModel):
    symbol: str
    profit: str
    deals_completed: int
    bots: int


class SummaryEnvelope(BaseModel):
    data: PortfolioSummary


class EquityEnvelope(BaseModel):
    data: list[EquityPoint]


class DailyEnvelope(BaseModel):
    data: list[DailyPoint]


class ByBotEnvelope(BaseModel):
    data: list[BotProfitRow]


class ByPairEnvelope(BaseModel):
    data: list[PairProfitRow]


@dataclass(frozen=True)
class V2StatsDeps:
    store: BotStore
    clock_us: Callable[[], int]
    problem: Callable[..., object]


def register_routes(app: FastAPI, deps: V2StatsDeps) -> None:
    lock = Lock()

    def _snapshot():
        with lock:
            records = deps.store.list()
            deals = {record.bot_id: deps.store.list_deals(record.bot_id) for record in records}
            runtimes = {}
            for record in records:
                runtime = deps.store.get_runtime(record.bot_id)
                if runtime is not None:
                    runtimes[record.bot_id] = runtime
        return records, deals, runtimes

    @app.get("/api/v2/stats/portfolio/summary", tags=["v2-stats"], response_model=SummaryEnvelope)
    def get_portfolio_summary():
        """Control-center KPIs: value, today's profit, active bots, capital."""
        records, deals, runtimes = _snapshot()
        return {"data": portfolio_summary(records, deals, runtimes, deps.clock_us())}

    @app.get("/api/v2/stats/portfolio/equity", tags=["v2-stats"], response_model=EquityEnvelope)
    def get_portfolio_equity(range: Literal["7d", "30d", "all"] = "30d"):
        """Hourly equity points, oldest first; 'all' is pruned to 90 days."""
        now = deps.clock_us()
        since_us = None if range == "all" else now - RANGE_US[range]
        with lock:
            rows = deps.store.list_portfolio_snapshots(since_us=since_us)
        return {"data": list(rows)}

    @app.get("/api/v2/stats/portfolio/daily-profit", tags=["v2-stats"], response_model=DailyEnvelope)
    def get_daily_profit(days: Annotated[int, Field(ge=1, le=90)] = 30):
        """Realized profit per UTC day, oldest first, zero-filled."""
        records, deals, _ = _snapshot()
        live = {record.bot_id for record in records if record.archived_at_us is None}
        flat = tuple(deal for bot_id, bot_deals in deals.items() if bot_id in live for deal in bot_deals)
        return {"data": daily_profit(flat, days, deps.clock_us())}

    @app.get("/api/v2/stats/portfolio/by-bot", tags=["v2-stats"], response_model=ByBotEnvelope)
    def get_profit_by_bot():
        """Realized profit per bot, in creation order."""
        records, deals, _ = _snapshot()
        return {"data": profit_by_bot(records, deals)}

    @app.get("/api/v2/stats/portfolio/by-pair", tags=["v2-stats"], response_model=ByPairEnvelope)
    def get_profit_by_pair():
        """Realized profit per symbol, symbols ascending."""
        records, deals, _ = _snapshot()
        return {"data": profit_by_pair(records, deals)}
