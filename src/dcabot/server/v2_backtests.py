"""Faz W v2 backtest endpoint: sector parameters over venue klines.

`POST /api/v2/backtests` serves closed klines from the local cache when the
whole range is present, otherwise fetches the range from the venue once and
caches it, then runs `sector_backtest.run_sector_backtest`. Registered with
`register_routes(app, deps)` directly on the app (see v2_bots for why).
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from threading import Lock
from typing import Annotated, Callable, Literal

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from dcabot.application.historical_simulation import MAX_SECTOR_BACKTEST_BARS
from dcabot.application.sector_backtest import SectorBacktestError, run_sector_backtest
from dcabot.application.sector_dca import SectorDcaError, parse_sector_dca
from dcabot.data_adapters.binance_public_transport import KLINE_INTERVAL_US
from dcabot.domain.numbers import number
from dcabot.persistence.kline_cache import KlineCache, KlineCacheError
from dcabot.server.v2_bots import DcaStrategy, DecimalText, Market, MarketUnavailable, _Strict

BacktestInterval = Literal["15m", "30m", "1h", "4h", "1d"]
IsoDate = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]


class BacktestRequest(_Strict):
    budget: DecimalText
    strategy: DcaStrategy
    interval: BacktestInterval
    start_date: IsoDate
    end_date: IsoDate


class BacktestDeal(BaseModel):
    deal: int
    started_at_us: int | None
    closed_at_us: int | None
    safety_orders_filled: int
    profit: str | None
    entry_price: str | None
    exit_price: str | None


class BacktestSummary(BaseModel):
    net_profit: str
    roi_percent: str
    annualized_roi_percent: str
    final_equity: str
    deals_completed: int
    winning_deals: int
    win_rate_percent: str | None
    average_deal_profit: str | None
    average_deal_duration_us: int | None
    max_safety_orders_used: int
    max_drawdown_percent: str
    total_fees: str
    profit_factor: str | None
    sharpe_ratio_annualized: str | None


class BacktestOpenDeal(BaseModel):
    unrealized: str
    cost: str
    qty: str


class SafetyOrderUsage(BaseModel):
    safety_orders_filled: int
    deals: int


class EquityPoint(BaseModel):
    time_us: int
    equity: str


class PricePoint(BaseModel):
    time_us: int
    close: str


class DrawdownPoint(BaseModel):
    time_us: int
    drawdown_percent: str


class MonthlyReturn(BaseModel):
    month: str
    return_percent: str
    complete: bool


class BacktestResult(BaseModel):
    symbol: str
    interval: str
    period_start_us: int
    period_end_us: int
    bar_count: int
    processed_bar_count: int
    status: Literal["COMPLETED", "INDETERMINATE"]
    indeterminate_at_us: int | None
    budget: str
    summary: BacktestSummary
    open_deal: BacktestOpenDeal | None
    deals: list[BacktestDeal]
    safety_order_usage: list[SafetyOrderUsage]
    equity_curve: list[EquityPoint]
    price_curve: list[PricePoint]
    drawdown_curve: list[DrawdownPoint]
    monthly_returns: list[MonthlyReturn]
    assumptions: list[str]
    data_source: Literal["CACHE", "VENUE"]


class BacktestEnvelope(BaseModel):
    data: BacktestResult


@dataclass(frozen=True)
class V2BacktestDeps:
    market: Market
    fetch_range: Callable[..., tuple]
    cache: KlineCache
    template_loader: Callable[[], dict]
    clock_us: Callable[[], int]
    problem: Callable[..., JSONResponse]
    transport_error: type[Exception]


def _day_start_us(value: str) -> int:
    parsed = date.fromisoformat(value)
    return int(datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc).timestamp()) * 1_000_000


def register_routes(app: FastAPI, deps: V2BacktestDeps) -> None:
    lock = Lock()

    def invalid(field: str, code: str, detail: str) -> JSONResponse:
        return deps.problem(422, code, "Backtest ayarları geçersiz", detail, errors=[{"field": field, "code": code}])

    def sector_invalid(exc: SectorDcaError) -> JSONResponse:
        if exc.field is None:
            field = "strategy"
        elif exc.field == "budget":
            field = "budget"
        else:
            field = f"strategy.{exc.field}"
        return invalid(field, exc.code, str(exc).split(": ", 1)[-1])

    @app.post("/api/v2/backtests", tags=["v2-backtests"], response_model=BacktestEnvelope)
    def run_backtest(body: BacktestRequest):
        """Run one sector DCA backtest; the result is not stored."""

        try:
            start_us = _day_start_us(body.start_date)
            end_us = _day_start_us(body.end_date) + 86_400_000_000
        except ValueError:
            return invalid("start_date", "BACKTEST_DATE_INVALID", "Tarih geçersiz.")
        now_us = deps.clock_us()
        interval_us = KLINE_INTERVAL_US[body.interval]
        if start_us >= end_us:
            return invalid("end_date", "BACKTEST_RANGE_INVALID", "Bitiş tarihi başlangıçtan sonra olmalıdır.")
        if end_us > now_us:
            end_us = (now_us // interval_us) * interval_us
            if start_us >= end_us:
                return invalid("start_date", "BACKTEST_RANGE_INVALID", "Seçilen aralıkta kapanmış mum yok.")
        if -(-(end_us - start_us) // interval_us) > MAX_SECTOR_BACKTEST_BARS:
            return invalid(
                "start_date",
                "BACKTEST_RANGE_TOO_LARGE",
                f"Bu aralık {MAX_SECTOR_BACKTEST_BARS} mumdan fazla; tarih aralığını kısaltın ya da daha büyük zaman dilimi seçin.",
            )
        try:
            params = parse_sector_dca(body.strategy.model_dump())
            rules = deps.market.symbol_rules(params.symbol)
        except SectorDcaError as exc:
            return sector_invalid(exc)
        except MarketUnavailable as exc:
            return deps.problem(502, exc.code, "Piyasa verisi alınamadı", str(exc))
        with lock:
            bars = deps.cache.get_range(params.symbol, body.interval, start_us, end_us, interval_us)
            source = "CACHE"
            if bars is None:
                try:
                    bars = deps.fetch_range(
                        params.symbol,
                        interval=body.interval,
                        start_us=start_us,
                        end_us=end_us,
                        max_bars=MAX_SECTOR_BACKTEST_BARS,
                        now_us=now_us,
                        allowed_symbols=frozenset({params.symbol}),
                    )
                except deps.transport_error as exc:
                    return deps.problem(502, getattr(exc, "code", "PUBLIC_UPSTREAM_UNAVAILABLE"), "Geçmiş veri alınamadı", str(exc))
                try:
                    deps.cache.put(params.symbol, body.interval, bars, now_us=now_us)
                except KlineCacheError:
                    pass  # a cache write failure must not fail an otherwise valid backtest
                source = "VENUE"
        if len(bars) < 2:
            return invalid("start_date", "BACKTEST_RANGE_INVALID", "Aralıkta yeterli mum yok (en az 2).")
        try:
            result = run_sector_backtest(
                params,
                rules=rules,
                budget=number(body.budget),
                interval=body.interval,
                interval_us=interval_us,
                bars=bars,
                template=deps.template_loader(),
            )
        except SectorDcaError as exc:
            return sector_invalid(exc)
        except SectorBacktestError as exc:
            return deps.problem(422, exc.code, "Backtest çalıştırılamadı", str(exc).split(": ", 1)[-1])
        result["data_source"] = source
        return {"data": result}
