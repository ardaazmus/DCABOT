"""Faz G3-b futures grid backtest endpoint: futures-grid engine over venue data.

`POST /api/v2/futures-grid-backtests` serves closed futures klines from
the local futures cache when the whole range is present (otherwise
fetches once and caches), resolves settled funding history from the
funding cache or the venue, then runs
`futures_grid_backtest.run_futures_grid_backtest`. Registered with
`register_routes(app, deps)` directly on the app (see v2_bots for why).
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from threading import Lock
from typing import Annotated, Callable, Literal

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import Field

from dcabot.application.futures_grid_backtest import (
    FuturesGridBacktestError,
    parse_futures_grid_backtest,
    run_futures_grid_backtest,
)
from dcabot.application.grid_backtest import MAX_GRID_BACKTEST_BARS
from dcabot.data_adapters.binance_futures_public_transport import FUTURES_KLINE_INTERVAL_US
from dcabot.persistence.funding_cache import FundingCache, FundingCacheError
from dcabot.persistence.kline_cache import KlineCache, KlineCacheError
from dcabot.server.v2_backtests import BacktestInterval, IsoDate
from dcabot.server.v2_bots import DecimalText, _Strict

GridMode = Literal["ARITHMETIC", "GEOMETRIC"]
GridDirection = Literal["LONG", "SHORT"]


class FuturesGridStrategy(_Strict):
    symbol: Annotated[str, Field(min_length=5, max_length=20, pattern=r"^[A-Z0-9]+$")]
    direction: GridDirection = "LONG"
    mode: GridMode = "ARITHMETIC"
    lower_price: DecimalText
    upper_price: DecimalText
    interval_count: Annotated[int, Field(ge=1, le=1000)]
    leverage: Annotated[int, Field(ge=1, le=10)] = 1
    fee_rate: DecimalText = "0.0005"
    stop_loss_price: DecimalText | None = None
    take_profit_pct: DecimalText | None = None
    trailing_up_pct: DecimalText | None = None
    trailing_down_pct: DecimalText | None = None


class FuturesGridBacktestRequest(_Strict):
    investment: DecimalText
    strategy: FuturesGridStrategy
    interval: BacktestInterval
    start_date: IsoDate
    end_date: IsoDate


class FuturesGridBacktestSummary(_Strict):
    net_profit: str
    roi_percent: str
    annualized_roi_percent: str
    final_equity: str
    cycles_closed: int
    fills_count: int
    max_drawdown_percent: str
    total_fees: str
    funding_cashflow: str
    funding_events_applied: int
    realized_gross_pnl: str
    trailing_shifts: int
    grid_status: str
    entry_price: str | None
    liq_estimate_price: str | None
    sharpe_ratio_annualized: str | None


class FuturesGridEquityPoint(_Strict):
    time_us: int
    equity: str


class FuturesGridDrawdownPoint(_Strict):
    time_us: int
    drawdown_percent: str


class FuturesGridMonthlyReturn(_Strict):
    month: str
    return_percent: str
    complete: bool


class FuturesGridBacktestResult(_Strict):
    symbol: str
    direction: str
    leverage: int
    interval: str
    period_start_us: int
    period_end_us: int
    bar_count: int
    processed_bar_count: int
    status: Literal["COMPLETED", "STOPPED_SL", "STOPPED_TP", "STOPPED_LIQ_ESTIMATE", "NEVER_ENTERED"]
    stopped_at_us: int | None
    investment: str
    summary: FuturesGridBacktestSummary
    levels: list[str]
    equity_curve: list[FuturesGridEquityPoint]
    drawdown_curve: list[FuturesGridDrawdownPoint]
    monthly_returns: list[FuturesGridMonthlyReturn]
    assumptions: list[str]
    data_source: Literal["CACHE", "VENUE"]
    funding_source: Literal["CACHE", "VENUE"]


class FuturesGridBacktestEnvelope(_Strict):
    data: FuturesGridBacktestResult


@dataclass(frozen=True)
class V2FuturesGridBacktestDeps:
    fetch_rules: Callable[..., object]
    fetch_klines_range: Callable[..., tuple]
    fetch_funding: Callable[..., tuple]
    kline_cache: KlineCache
    funding_cache: FundingCache
    clock_us: Callable[[], int]
    problem: Callable[..., JSONResponse]
    transport_error: type[Exception]


def _day_start_us(value: str) -> int:
    parsed = date.fromisoformat(value)
    return int(datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc).timestamp()) * 1_000_000


def register_routes(app: FastAPI, deps: V2FuturesGridBacktestDeps) -> None:
    lock = Lock()

    def invalid(field: str, code: str, detail: str) -> JSONResponse:
        return deps.problem(422, code, "Futures grid backtest ayarları geçersiz", detail, errors=[{"field": field, "code": code}])

    def grid_invalid(exc: FuturesGridBacktestError) -> JSONResponse:
        return invalid(exc.field or "strategy", exc.code, str(exc).split(": ", 1)[-1])

    @app.post("/api/v2/futures-grid-backtests", tags=["v2-futures-grid-backtests"], response_model=FuturesGridBacktestEnvelope)
    def run_backtest(body: FuturesGridBacktestRequest):
        """Run one futures-grid backtest; the result is not stored."""

        try:
            start_us = _day_start_us(body.start_date)
            end_us = _day_start_us(body.end_date) + 86_400_000_000
        except ValueError:
            return invalid("start_date", "BACKTEST_DATE_INVALID", "Tarih geçersiz.")
        now_us = deps.clock_us()
        interval_us = FUTURES_KLINE_INTERVAL_US[body.interval]
        if start_us >= end_us:
            return invalid("end_date", "BACKTEST_RANGE_INVALID", "Bitiş tarihi başlangıçtan sonra olmalıdır.")
        if end_us > now_us:
            end_us = (now_us // interval_us) * interval_us
            if start_us >= end_us:
                return invalid("start_date", "BACKTEST_RANGE_INVALID", "Seçilen aralıkta kapanmış mum yok.")
        if -(-(end_us - start_us) // interval_us) > MAX_GRID_BACKTEST_BARS:
            return invalid(
                "start_date",
                "BACKTEST_RANGE_TOO_LARGE",
                f"Bu aralık {MAX_GRID_BACKTEST_BARS} mumdan fazla; tarih aralığını kısaltın ya da daha büyük zaman dilimi seçin.",
            )
        try:
            params = parse_futures_grid_backtest({"investment": body.investment, **body.strategy.model_dump()})
        except FuturesGridBacktestError as exc:
            return grid_invalid(exc)
        try:
            rules = deps.fetch_rules(params.symbol, allowed_symbols=frozenset({params.symbol}))
        except deps.transport_error as exc:
            return deps.problem(502, getattr(exc, "code", "PUBLIC_UPSTREAM_UNAVAILABLE"), "Piyasa verisi alınamadı", str(exc))
        with lock:
            bars = deps.kline_cache.get_range(params.symbol, body.interval, start_us, end_us, interval_us)
            source = "CACHE"
            if bars is None:
                try:
                    bars = deps.fetch_klines_range(
                        params.symbol,
                        interval=body.interval,
                        start_us=start_us,
                        end_us=end_us,
                        max_bars=MAX_GRID_BACKTEST_BARS,
                        now_us=now_us,
                        allowed_symbols=frozenset({params.symbol}),
                    )
                except deps.transport_error as exc:
                    return deps.problem(502, getattr(exc, "code", "PUBLIC_UPSTREAM_UNAVAILABLE"), "Geçmiş veri alınamadı", str(exc))
                try:
                    deps.kline_cache.put(params.symbol, body.interval, bars, now_us=now_us)
                except KlineCacheError:
                    pass  # a cache write failure must not fail an otherwise valid backtest
                source = "VENUE"
            funding = deps.funding_cache.get_range(params.symbol, start_us, end_us)
            funding_source = "CACHE"
            if funding is None:
                try:
                    funding = deps.fetch_funding(
                        params.symbol,
                        start_us=start_us,
                        end_us=end_us,
                        allowed_symbols=frozenset({params.symbol}),
                    )
                except deps.transport_error as exc:
                    return deps.problem(502, getattr(exc, "code", "PUBLIC_UPSTREAM_UNAVAILABLE"), "Funding verisi alınamadı", str(exc))
                try:
                    deps.funding_cache.put_range(params.symbol, funding, start_us=start_us, end_us=end_us)
                except FundingCacheError:
                    pass
                funding_source = "VENUE"
        if len(bars) < 2:
            return invalid("start_date", "BACKTEST_RANGE_INVALID", "Aralıkta yeterli mum yok (en az 2).")
        try:
            result = run_futures_grid_backtest(
                params,
                rules=rules,
                interval=body.interval,
                interval_us=interval_us,
                bars=bars,
                funding=funding,
            )
        except FuturesGridBacktestError as exc:
            return grid_invalid(exc)
        result["data_source"] = source
        result["funding_source"] = funding_source
        return {"data": result}
