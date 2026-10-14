"""Q2 risk matrix: pairwise correlation over aligned venue closes.

`POST /api/v2/risk/correlation-matrix` serves the last closed klines per
symbol (cache first, venue fallback), inner-joins them on bar open time
so every pair compares the SAME bars, then runs the tested Faz 17 F.2
core per pair. Coefficients are display-grade floats; breach verdicts
are exact integer comparisons. Read-only; nothing is stored.
"""

from dataclasses import dataclass
from threading import Lock
from typing import Annotated, Callable, Literal

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from dcabot.application.correlation_matrix import correlation_matrix_cells
from dcabot.data_adapters.binance_public_transport import KLINE_INTERVAL_US
from dcabot.domain.numbers import number
from dcabot.persistence.kline_cache import KlineCache, KlineCacheError
from dcabot.server.v2_bots import DecimalText, Market, MarketUnavailable, _Strict

MatrixInterval = Literal["15m", "30m", "1h", "4h", "1d"]

# Fixed-point scale for the integer breach comparison (mirrors the
# legacy /api/risk/correlation contract's client scale, fixed here).
_CORRELATION_SCALE = 10**12
# Extra bars fetched beyond window+1 so listings that lag still overlap.
_FETCH_BUFFER_BARS = 32
_MAX_WINDOW = 200
_MAX_SYMBOLS = 10


class MatrixRequest(_Strict):
    symbols: Annotated[
        list[Annotated[str, Field(min_length=5, max_length=20, pattern=r"^[A-Z0-9]+$")]],
        Field(min_length=2, max_length=_MAX_SYMBOLS),
    ]
    interval: MatrixInterval = "1h"
    window: Annotated[int, Field(ge=2, le=_MAX_WINDOW)] = 30
    threshold: DecimalText = "0.7"


class MatrixCellModel(BaseModel):
    x: str
    y: str
    coefficient: str | None
    verdict: Literal["BREACH", "OK", "INSUFFICIENT"]
    detail: Literal["INSUFFICIENT_HISTORY", "INSUFFICIENT_PRECISION", "PSD_VIOLATION"] | None
    samples: int


class MatrixResult(BaseModel):
    symbols: list[str]
    interval: str
    window: int
    threshold: str
    computed_at_us: int
    overlap_bars: int
    data_source: Literal["CACHE", "VENUE", "MIXED"]
    cells: list[MatrixCellModel]


class MatrixEnvelope(BaseModel):
    data: MatrixResult


@dataclass(frozen=True)
class V2RiskDeps:
    market: Market
    fetch_range: Callable[..., tuple]
    cache: KlineCache
    clock_us: Callable[[], int]
    problem: Callable[..., JSONResponse]
    transport_error: type[Exception]


def register_routes(app: FastAPI, deps: V2RiskDeps) -> None:
    lock = Lock()

    def invalid(field: str, code: str, detail: str) -> JSONResponse:
        return deps.problem(422, code, "Korelasyon ayarları geçersiz", detail, errors=[{"field": field, "code": code}])

    @app.post("/api/v2/risk/correlation-matrix", tags=["v2-risk"], response_model=MatrixEnvelope)
    def correlation_matrix(body: MatrixRequest):
        """Pairwise correlation matrix; the result is not stored."""

        if len(set(body.symbols)) != len(body.symbols):
            return invalid("symbols", "CORRELATION_SYMBOLS_INVALID", "Semboller benzersiz olmalıdır.")
        threshold = number(body.threshold)
        if threshold <= 0 or threshold > 1:
            return invalid("threshold", "CORRELATION_THRESHOLD_INVALID", "Eşik 0 ile 1 arasında olmalıdır.")
        try:
            rules = {symbol: deps.market.symbol_rules(symbol) for symbol in body.symbols}
        except MarketUnavailable as exc:
            return deps.problem(502, exc.code, "Piyasa verisi alınamadı", str(exc))
        halted = sorted(symbol for symbol, rule in rules.items() if rule.status != "TRADING")
        if halted:
            return invalid("symbols", "CORRELATION_SYMBOL_HALTED", f"İşlemde olmayan semboller: {', '.join(halted)}.")
        now_us = deps.clock_us()
        interval_us = KLINE_INTERVAL_US[body.interval]
        need = body.window + 1 + _FETCH_BUFFER_BARS
        end_us = (now_us // interval_us) * interval_us
        start_us = end_us - need * interval_us
        closes: dict[str, dict[int, float]] = {}
        from_cache = True
        from_venue = True
        with lock:
            for symbol in body.symbols:
                bars = deps.cache.get_range(symbol, body.interval, start_us, end_us, interval_us)
                if bars is None:
                    try:
                        bars = deps.fetch_range(
                            symbol,
                            interval=body.interval,
                            start_us=start_us,
                            end_us=end_us,
                            max_bars=need,
                            now_us=now_us,
                            allowed_symbols=frozenset({symbol}),
                        )
                    except deps.transport_error as exc:
                        return deps.problem(502, getattr(exc, "code", "PUBLIC_UPSTREAM_UNAVAILABLE"), "Geçmiş veri alınamadı", str(exc))
                    try:
                        deps.cache.put(symbol, body.interval, bars, now_us=now_us)
                    except KlineCacheError:
                        pass  # a cache write failure must not fail an otherwise valid matrix
                    from_cache = False
                else:
                    from_venue = False
                closes[symbol] = {bar.open_time_us: float(bar.close) for bar in bars}
        common = sorted(set.intersection(*(set(series) for series in closes.values())))
        windowed = {symbol: [closes[symbol][t] for t in common[-(body.window + 1):]] for symbol in body.symbols}
        cells = correlation_matrix_cells(
            windowed,
            window=body.window,
            threshold_numerator=threshold.numerator,
            threshold_denominator=threshold.denominator,
            scale=_CORRELATION_SCALE,
        )
        return {
            "data": {
                "symbols": sorted(body.symbols),
                "interval": body.interval,
                "window": body.window,
                "threshold": body.threshold,
                "computed_at_us": now_us,
                "overlap_bars": len(common),
                "data_source": "CACHE" if from_cache else "VENUE" if from_venue else "MIXED",
                "cells": [
                    {
                        "x": cell.x,
                        "y": cell.y,
                        "coefficient": cell.coefficient,
                        "verdict": cell.verdict,
                        "detail": cell.detail,
                        "samples": cell.samples,
                    }
                    for cell in cells
                ],
            }
        }
