"""Bounded, credential-free Binance Spot public market-data transport.

This is the ONLY module that opens public market-data connections (REST and
WebSocket) for paper trading and read-only market display. Requests never
carry credentials; responses are bounded before decoding and reduced to
normalized read-only observations.
"""

import asyncio
import inspect
import json
import re
import time
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from websockets.asyncio.client import connect

from dcabot.data_adapters.binance_public import (
    BinanceTimeUnit,
    normalize_binance_rest_trade_payload,
    normalize_binance_trade_payload,
)
from dcabot.data_adapters.public_feed import (
    PublicFeedContractError,
    PublicObservation,
)
from dcabot.domain.numbers import exact_text, number, text


BINANCE_SPOT_PUBLIC_REST_BASE_URL = "https://data-api.binance.vision/api"
BINANCE_SPOT_PUBLIC_TRADES_URL = f"{BINANCE_SPOT_PUBLIC_REST_BASE_URL}/v3/trades"
BINANCE_SPOT_PUBLIC_EXCHANGE_INFO_URL = f"{BINANCE_SPOT_PUBLIC_REST_BASE_URL}/v3/exchangeInfo"
BINANCE_SPOT_PUBLIC_24HR_TICKER_URL = f"{BINANCE_SPOT_PUBLIC_REST_BASE_URL}/v3/ticker/24hr"
BINANCE_SPOT_PUBLIC_KLINES_URL = f"{BINANCE_SPOT_PUBLIC_REST_BASE_URL}/v3/klines"
# Fixed-length intervals only; "1M" is excluded because its duration varies.
PUBLIC_KLINE_INTERVALS = frozenset(
    {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"}
)
MAX_KLINES_LIMIT = 1000
_KLINE_ROW_LENGTH = 12
MAX_TICKER_RESPONSE_BYTES = 16 * 1024
BINANCE_SPOT_PUBLIC_WS_BASE_URL = "wss://stream.binance.vision/ws"
MAX_PUBLIC_RESPONSE_BYTES = 256 * 1024
MAX_PUBLIC_WS_FRAME_BYTES = 64 * 1024
DEFAULT_TIMEOUT_SECONDS = 5
MAX_TRADES_LIMIT = 1000
# Full spot exchangeInfo carries every listed pair with its filters. Observed
# against the real venue (2026-09-22): ~16.8 MB (17,620,275 bytes) and ~3700
# symbols (3707). Budgets keep ~1.4x byte and ~1.35x count headroom for venue
# growth while staying bounded: anything above still fails closed
# (PUBLIC_RESPONSE_TOO_LARGE / PUBLIC_RESPONSE_INVALID).
MAX_EXCHANGE_INFO_RESPONSE_BYTES = 24 * 1024 * 1024
MAX_LISTED_SYMBOLS = 5000
MAX_LISTED_FIELD_LENGTH = 32
_SYMBOL = re.compile(r"[A-Z0-9]{1,20}\Z", re.ASCII)


class BinancePublicTransportError(RuntimeError):
    """Raised when public market data cannot be fetched or decoded safely."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


class TransportResponse(Protocol):
    status: int
    headers: object

    def read(self, size: int = -1) -> bytes: ...

    def close(self) -> None: ...


class TransportOpener(Protocol):
    def open(self, request: Request, timeout: int) -> TransportResponse: ...


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, new):
        raise BinancePublicTransportError(
            "PUBLIC_REDIRECT_REJECTED", "Public market-data yönlendirmesi reddedildi."
        )


def fetch_binance_public_trades(
    symbol: str,
    *,
    limit: int,
    allowed_symbols: frozenset[str],
    receive_time_us: int,
    processing_time_us: int,
    time_unit: BinanceTimeUnit,
    opener: TransportOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[PublicObservation, ...]:
    """Fetch recent public trades and normalize every record or fail closed.

    A single bad record rejects the whole batch: partial acceptance would let
    a paper session fill against an incomplete tape.
    """

    _validate_symbol(symbol)
    if type(limit) is not int or not 1 <= limit <= MAX_TRADES_LIMIT:
        raise BinancePublicTransportError(
            "PUBLIC_LIMIT_INVALID", "Trade limiti 1 ile 1000 arasında olmalıdır."
        )
    if not isinstance(allowed_symbols, frozenset) or symbol not in allowed_symbols:
        raise BinancePublicTransportError(
            "PUBLIC_SYMBOL_NOT_ALLOWED", "Symbol allowlist kapsamında değil."
        )
    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30:
        raise BinancePublicTransportError(
            "PUBLIC_TIMEOUT_INVALID", "Transport timeout değeri geçersiz."
        )
    query = urlencode({"symbol": symbol, "limit": limit}, encoding="utf-8")
    request = Request(
        f"{BINANCE_SPOT_PUBLIC_TRADES_URL}?{query}",
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        method="GET",
    )
    active_opener = opener or build_opener(_NoRedirectHandler())
    response: TransportResponse | None = None
    try:
        response = active_opener.open(request, timeout=timeout_seconds)
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()  # type: ignore[attr-defined]
        if status != 200:
            raise BinancePublicTransportError(
                "PUBLIC_UPSTREAM_HTTP_ERROR", "Public market-data HTTP yanıtı başarılı değil."
            )
        payload = _decode_list(_read_bounded_response(response))
        observations: list[PublicObservation] = []
        for record in payload:
            try:
                observations.append(
                    normalize_binance_rest_trade_payload(
                        record,
                        symbol=symbol,
                        allowed_symbols=allowed_symbols,
                        receive_time_us=receive_time_us,
                        processing_time_us=processing_time_us,
                        time_unit=time_unit,
                    )
                )
            except PublicFeedContractError as exc:
                raise BinancePublicTransportError(
                    "PUBLIC_UPSTREAM_RECORD_INVALID",
                    "Public trade kaydı normalize edilemedi.",
                ) from exc
        return tuple(observations)
    except BinancePublicTransportError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı."
        ) from exc
    finally:
        if response is not None:
            response.close()


@dataclass(frozen=True, slots=True)
class BinancePublicListedSymbol:
    """One venue-reported spot pair; display metadata only, no market values."""

    symbol: str
    status: str
    base_asset: str
    quote_asset: str


def fetch_binance_public_exchange_symbols(
    *,
    opener: TransportOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[BinancePublicListedSymbol, ...]:
    """Fetch the full public spot symbol list and normalize every entry.

    Venue order is preserved (no invented ranking). A single bad entry
    rejects the whole batch, mirroring the trade-tape rule: partial
    acceptance would let the selector show an incomplete exchange.
    """

    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30:
        raise BinancePublicTransportError(
            "PUBLIC_TIMEOUT_INVALID", "Transport timeout değeri geçersiz."
        )
    request = Request(
        BINANCE_SPOT_PUBLIC_EXCHANGE_INFO_URL,
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        method="GET",
    )
    active_opener = opener or build_opener(_NoRedirectHandler())
    response: TransportResponse | None = None
    try:
        response = active_opener.open(request, timeout=timeout_seconds)
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()  # type: ignore[attr-defined]
        if status != 200:
            raise BinancePublicTransportError(
                "PUBLIC_UPSTREAM_HTTP_ERROR", "Public market-data HTTP yanıtı başarılı değil."
            )
        payload = _decode_exchange_info(_read_bounded_list_response(response))
        return _normalize_listed_symbols(payload)
    except BinancePublicTransportError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı."
        ) from exc
    finally:
        if response is not None:
            response.close()


@dataclass(frozen=True, slots=True)
class BinancePublic24hTicker:
    """One symbol's rolling 24h stats; display-only, never fed into economic state."""

    symbol: str
    last_price: str
    price_change_percent: str
    quote_volume: str


def fetch_binance_public_24hr_ticker(
    symbol: str,
    *,
    allowed_symbols: frozenset[str],
    opener: TransportOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> BinancePublic24hTicker:
    """Fetch one symbol's public 24h ticker stats or fail closed.

    Display-only (AA.2 market panel columns): last price, 24h % change,
    24h quote volume. Never used for economic decisions -- the engine's own
    `MARK` price always comes from the existing last-price/kline path.
    """

    _validate_symbol(symbol)
    if not isinstance(allowed_symbols, frozenset) or symbol not in allowed_symbols:
        raise BinancePublicTransportError(
            "PUBLIC_SYMBOL_NOT_ALLOWED", "Symbol allowlist kapsamında değil."
        )
    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30:
        raise BinancePublicTransportError(
            "PUBLIC_TIMEOUT_INVALID", "Transport timeout değeri geçersiz."
        )
    query = urlencode({"symbol": symbol}, encoding="utf-8")
    request = Request(
        f"{BINANCE_SPOT_PUBLIC_24HR_TICKER_URL}?{query}",
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        method="GET",
    )
    active_opener = opener or build_opener(_NoRedirectHandler())
    response: TransportResponse | None = None
    try:
        response = active_opener.open(request, timeout=timeout_seconds)
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()  # type: ignore[attr-defined]
        if status != 200:
            raise BinancePublicTransportError(
                "PUBLIC_UPSTREAM_HTTP_ERROR", "Public market-data HTTP yanıtı başarılı değil."
            )
        payload = _decode_ticker(_read_bounded_ticker_response(response))
        return _normalize_ticker(payload, symbol)
    except BinancePublicTransportError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı."
        ) from exc
    finally:
        if response is not None:
            response.close()


@dataclass(frozen=True, slots=True)
class BinancePublicSymbolRules:
    """One spot symbol's venue trading rules, exact text; no market values."""

    symbol: str
    status: str
    base_asset: str
    quote_asset: str
    tick: str
    qty_step: str
    min_qty: str
    min_notional: str


def fetch_binance_public_symbol_rules(
    symbol: str,
    *,
    allowed_symbols: frozenset[str],
    opener: TransportOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> BinancePublicSymbolRules:
    """Fetch one symbol's PRICE_FILTER/LOT_SIZE/(MIN_)NOTIONAL rules or fail closed."""

    _validate_symbol(symbol)
    if not isinstance(allowed_symbols, frozenset) or symbol not in allowed_symbols:
        raise BinancePublicTransportError(
            "PUBLIC_SYMBOL_NOT_ALLOWED", "Symbol allowlist kapsamında değil."
        )
    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30:
        raise BinancePublicTransportError(
            "PUBLIC_TIMEOUT_INVALID", "Transport timeout değeri geçersiz."
        )
    query = urlencode({"symbol": symbol}, encoding="utf-8")
    request = Request(
        f"{BINANCE_SPOT_PUBLIC_EXCHANGE_INFO_URL}?{query}",
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        method="GET",
    )
    active_opener = opener or build_opener(_NoRedirectHandler())
    response: TransportResponse | None = None
    try:
        response = active_opener.open(request, timeout=timeout_seconds)
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()  # type: ignore[attr-defined]
        if status != 200:
            raise BinancePublicTransportError(
                "PUBLIC_UPSTREAM_HTTP_ERROR", "Public market-data HTTP yanıtı başarılı değil."
            )
        payload = _decode_exchange_info(_read_bounded_response(response))
        return _normalize_symbol_rules(payload, symbol)
    except BinancePublicTransportError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı."
        ) from exc
    finally:
        if response is not None:
            response.close()


def _normalize_symbol_rules(payload: dict, expected_symbol: str) -> BinancePublicSymbolRules:
    try:
        symbols = payload.get("symbols")
        if type(symbols) is not list or len(symbols) != 1 or type(symbols[0]) is not dict:
            raise ValueError
        entry = symbols[0]
        if entry.get("symbol") != expected_symbol:
            raise ValueError
        names = (entry.get("status"), entry.get("baseAsset"), entry.get("quoteAsset"))
        if not all(type(name) is str and 0 < len(name) <= MAX_LISTED_FIELD_LENGTH for name in names):
            raise ValueError
        by_type: dict[str, dict] = {}
        for item in entry.get("filters", ()):
            if type(item) is dict and type(item.get("filterType")) is str:
                by_type[item["filterType"]] = item
        notional_filter = by_type.get("NOTIONAL") or by_type.get("MIN_NOTIONAL")
        tick = number(by_type["PRICE_FILTER"]["tickSize"])
        step = number(by_type["LOT_SIZE"]["stepSize"])
        min_qty = number(by_type["LOT_SIZE"]["minQty"])
        min_notional = number(notional_filter["minNotional"]) if notional_filter else None
        if tick <= 0 or step <= 0 or min_qty < 0 or min_notional is None or min_notional < 0:
            raise ValueError
    except (KeyError, TypeError, ValueError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_UPSTREAM_RECORD_INVALID", "Sembol kuralları normalize edilemedi."
        ) from exc
    return BinancePublicSymbolRules(
        symbol=expected_symbol,
        status=names[0],
        base_asset=names[1],
        quote_asset=names[2],
        tick=exact_text(tick),
        qty_step=exact_text(step),
        min_qty=exact_text(min_qty),
        min_notional=exact_text(min_notional),
    )


@dataclass(frozen=True, slots=True)
class BinancePublicKline:
    """One venue kline; display-only, never fed into economic state."""

    open_time_us: int
    close_time_us: int
    open: str
    high: str
    low: str
    close: str
    base_volume: str


def fetch_binance_public_klines(
    symbol: str,
    *,
    interval: str,
    limit: int,
    allowed_symbols: frozenset[str],
    opener: TransportOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[BinancePublicKline, ...]:
    """Fetch recent public klines, oldest first, or fail closed.

    Display-only (live charts). The venue's last kline is usually still
    forming; callers decide how to label it from `close_time_us`. A single
    malformed or out-of-order row rejects the whole batch.
    """

    _validate_symbol(symbol)
    if not isinstance(allowed_symbols, frozenset) or symbol not in allowed_symbols:
        raise BinancePublicTransportError(
            "PUBLIC_SYMBOL_NOT_ALLOWED", "Symbol allowlist kapsamında değil."
        )
    if type(interval) is not str or interval not in PUBLIC_KLINE_INTERVALS:
        raise BinancePublicTransportError(
            "PUBLIC_INTERVAL_INVALID", "Kline aralığı desteklenmiyor."
        )
    if type(limit) is not int or not 1 <= limit <= MAX_KLINES_LIMIT:
        raise BinancePublicTransportError(
            "PUBLIC_LIMIT_INVALID", "Kline limiti 1 ile 1000 arasında olmalıdır."
        )
    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30:
        raise BinancePublicTransportError(
            "PUBLIC_TIMEOUT_INVALID", "Transport timeout değeri geçersiz."
        )
    return _request_klines(
        {"symbol": symbol, "interval": interval, "limit": limit},
        limit=limit,
        opener=opener,
        timeout_seconds=timeout_seconds,
    )


def _request_klines(
    params: dict,
    *,
    limit: int,
    opener: TransportOpener | None,
    timeout_seconds: int,
) -> tuple[BinancePublicKline, ...]:
    query = urlencode(params, encoding="utf-8")
    request = Request(
        f"{BINANCE_SPOT_PUBLIC_KLINES_URL}?{query}",
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        method="GET",
    )
    active_opener = opener or build_opener(_NoRedirectHandler())
    response: TransportResponse | None = None
    try:
        response = active_opener.open(request, timeout=timeout_seconds)
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()  # type: ignore[attr-defined]
        if status != 200:
            raise BinancePublicTransportError(
                "PUBLIC_UPSTREAM_HTTP_ERROR", "Public market-data HTTP yanıtı başarılı değil."
            )
        payload = _decode_list(_read_bounded_response(response))
        if len(payload) > limit:
            raise BinancePublicTransportError(
                "PUBLIC_RESPONSE_INVALID", "Kline yanıtı istenen limiti aşıyor."
            )
        return _normalize_klines(payload)
    except BinancePublicTransportError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı."
        ) from exc
    finally:
        if response is not None:
            response.close()


KLINE_INTERVAL_US = {
    "1m": 60_000_000,
    "5m": 300_000_000,
    "15m": 900_000_000,
    "30m": 1_800_000_000,
    "1h": 3_600_000_000,
    "4h": 14_400_000_000,
    "1d": 86_400_000_000,
}


def fetch_binance_public_klines_range(
    symbol: str,
    *,
    interval: str,
    start_us: int,
    end_us: int,
    max_bars: int,
    now_us: int,
    allowed_symbols: frozenset[str],
    opener: TransportOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[BinancePublicKline, ...]:
    """Fetch every CLOSED kline with open time in [start_us, end_us), oldest
    first, paging 1000 at a time. The range is sized before any request so an
    oversized ask fails without touching the venue; still-forming bars
    (close time >= now) are dropped, never simulated."""

    _validate_symbol(symbol)
    if not isinstance(allowed_symbols, frozenset) or symbol not in allowed_symbols:
        raise BinancePublicTransportError("PUBLIC_SYMBOL_NOT_ALLOWED", "Symbol allowlist kapsamında değil.")
    interval_us = KLINE_INTERVAL_US.get(interval) if type(interval) is str else None
    if interval_us is None:
        raise BinancePublicTransportError("PUBLIC_INTERVAL_INVALID", "Kline aralığı desteklenmiyor.")
    if not all(type(v) is int for v in (start_us, end_us, max_bars, now_us)) or not 0 <= start_us < end_us:
        raise BinancePublicTransportError("PUBLIC_RANGE_INVALID", "Tarih aralığı geçersiz.")
    if not 1 <= max_bars or -(-(end_us - start_us) // interval_us) > max_bars:
        raise BinancePublicTransportError(
            "PUBLIC_RANGE_TOO_LARGE", f"Aralık en fazla {max_bars} mum içerebilir."
        )
    klines: list[BinancePublicKline] = []
    cursor_ms = start_us // 1000
    end_ms = (end_us - 1) // 1000
    while cursor_ms <= end_ms:
        page = _request_klines(
            {
                "symbol": symbol,
                "interval": interval,
                "startTime": cursor_ms,
                "endTime": end_ms,
                "limit": MAX_KLINES_LIMIT,
            },
            limit=MAX_KLINES_LIMIT,
            opener=opener,
            timeout_seconds=timeout_seconds,
        )
        if klines and page and page[0].open_time_us <= klines[-1].open_time_us:
            raise BinancePublicTransportError(
                "PUBLIC_UPSTREAM_RECORD_INVALID", "Kline sayfaları sıralı değil."
            )
        klines.extend(page)
        if len(klines) > max_bars:
            raise BinancePublicTransportError(
                "PUBLIC_RANGE_TOO_LARGE", f"Aralık en fazla {max_bars} mum içerebilir."
            )
        if len(page) < MAX_KLINES_LIMIT:
            break
        cursor_ms = page[-1].open_time_us // 1000 + interval_us // 1000
    return tuple(k for k in klines if start_us <= k.open_time_us < end_us and k.close_time_us < now_us)


def _normalize_klines(payload: list) -> tuple[BinancePublicKline, ...]:
    klines: list[BinancePublicKline] = []
    previous_close_ms: int | None = None
    for row in payload:
        try:
            if type(row) is not list or len(row) != _KLINE_ROW_LENGTH:
                raise ValueError
            open_ms, close_ms = row[0], row[6]
            if type(open_ms) is not int or type(close_ms) is not int:
                raise ValueError
            if open_ms < 0 or close_ms <= open_ms:
                raise ValueError
            if previous_close_ms is not None and open_ms <= previous_close_ms:
                raise ValueError
            open_, high, low, close = (number(row[i]) for i in (1, 2, 3, 4))
            volume = number(row[5])
            if min(open_, high, low, close) <= 0 or volume < 0:
                raise ValueError
            if high < max(open_, close, low) or low > min(open_, close):
                raise ValueError
            klines.append(
                BinancePublicKline(
                    open_time_us=open_ms * 1000,
                    close_time_us=close_ms * 1000 + 999,
                    open=exact_text(open_),
                    high=exact_text(high),
                    low=exact_text(low),
                    close=exact_text(close),
                    base_volume=exact_text(volume),
                )
            )
            previous_close_ms = close_ms
        except (ValueError, TypeError) as exc:
            raise BinancePublicTransportError(
                "PUBLIC_UPSTREAM_RECORD_INVALID", "Kline kaydı normalize edilemedi."
            ) from exc
    return tuple(klines)


MAX_BATCH_TICKER_SYMBOLS = 50


def fetch_binance_public_24hr_tickers(
    symbols: tuple[str, ...],
    *,
    opener: TransportOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[BinancePublic24hTicker, ...]:
    """Fetch up to 50 symbols' 24h stats in one request, in requested order.

    Display-only like the single-symbol variant; a missing, duplicated or
    malformed entry rejects the whole batch.
    """

    if not isinstance(symbols, tuple) or not 1 <= len(symbols) <= MAX_BATCH_TICKER_SYMBOLS:
        raise BinancePublicTransportError(
            "PUBLIC_LIMIT_INVALID", "Sembol sayısı 1 ile 50 arasında olmalıdır."
        )
    for symbol in symbols:
        _validate_symbol(symbol)
    if len(set(symbols)) != len(symbols):
        raise BinancePublicTransportError("PUBLIC_SYMBOL_INVALID", "Semboller tekrar edemez.")
    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30:
        raise BinancePublicTransportError(
            "PUBLIC_TIMEOUT_INVALID", "Transport timeout değeri geçersiz."
        )
    query = urlencode(
        {"symbols": json.dumps(list(symbols), separators=(",", ":"))}, encoding="utf-8"
    )
    request = Request(
        f"{BINANCE_SPOT_PUBLIC_24HR_TICKER_URL}?{query}",
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        method="GET",
    )
    active_opener = opener or build_opener(_NoRedirectHandler())
    response: TransportResponse | None = None
    try:
        response = active_opener.open(request, timeout=timeout_seconds)
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()  # type: ignore[attr-defined]
        if status != 200:
            raise BinancePublicTransportError(
                "PUBLIC_UPSTREAM_HTTP_ERROR", "Public market-data HTTP yanıtı başarılı değil."
            )
        payload = _decode_list(_read_bounded_response(response))
        by_symbol: dict[str, BinancePublic24hTicker] = {}
        for entry in payload:
            if type(entry) is not dict or entry.get("symbol") not in symbols or entry["symbol"] in by_symbol:
                raise BinancePublicTransportError(
                    "PUBLIC_UPSTREAM_RECORD_INVALID", "Ticker listesi beklenen sembollerle eşleşmiyor."
                )
            by_symbol[entry["symbol"]] = _normalize_ticker(entry, entry["symbol"])
        if set(by_symbol) != set(symbols):
            raise BinancePublicTransportError(
                "PUBLIC_UPSTREAM_RECORD_INVALID", "Ticker listesi eksik."
            )
        return tuple(by_symbol[symbol] for symbol in symbols)
    except BinancePublicTransportError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı."
        ) from exc
    finally:
        if response is not None:
            response.close()


def _read_bounded_ticker_response(response: TransportResponse) -> bytes:
    headers = getattr(response, "headers", None)
    content_length = headers.get("Content-Length") if headers is not None else None
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except (TypeError, ValueError) as exc:
            raise BinancePublicTransportError(
                "PUBLIC_RESPONSE_INVALID", "Public yanıt Content-Length geçersiz."
            ) from exc
        if declared_size < 0 or declared_size > MAX_TICKER_RESPONSE_BYTES:
            raise BinancePublicTransportError(
                "PUBLIC_RESPONSE_TOO_LARGE", "Public yanıt byte sınırını aşıyor."
            )
    encoding = headers.get("Content-Encoding") if headers is not None else None
    if encoding and encoding.lower() != "identity":
        raise BinancePublicTransportError(
            "PUBLIC_ENCODING_INVALID", "Public yanıt sıkıştırma biçimi reddedildi."
        )
    payload = response.read(MAX_TICKER_RESPONSE_BYTES + 1)
    if not isinstance(payload, bytes):
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_INVALID", "Public yanıt gövdesi bytes olmalıdır."
        )
    if len(payload) > MAX_TICKER_RESPONSE_BYTES:
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_TOO_LARGE", "Public yanıt byte sınırını aşıyor."
        )
    return payload


def _decode_ticker(payload_bytes: bytes) -> dict:
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_INVALID", "Public yanıt JSON olarak okunamadı."
        ) from exc
    if type(payload) is not dict:
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_INVALID", "Public ticker yanıtı nesne olmalıdır."
        )
    return payload


def _normalize_ticker(payload: dict, expected_symbol: str) -> BinancePublic24hTicker:
    if payload.get("symbol") != expected_symbol:
        raise BinancePublicTransportError(
            "PUBLIC_UPSTREAM_RECORD_INVALID", "Ticker sembolü istenenle eşleşmiyor."
        )
    try:
        last_price = number(payload.get("lastPrice"))
        if last_price <= 0:
            raise ValueError
        price_change_percent = number(payload.get("priceChangePercent"))
        quote_volume = number(payload.get("quoteVolume"))
        if quote_volume < 0:
            raise ValueError
    except (ValueError, TypeError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_UPSTREAM_RECORD_INVALID", "Ticker kaydı normalize edilemedi."
        ) from exc
    return BinancePublic24hTicker(
        symbol=expected_symbol,
        last_price=text(last_price),
        price_change_percent=text(price_change_percent),
        quote_volume=text(quote_volume),
    )


class BinancePublicTradeStream:
    """Read-only public `@trade` stream with an injected socket factory."""

    def __init__(
        self,
        symbol: str,
        *,
        allowed_symbols: frozenset[str],
        time_unit: BinanceTimeUnit,
        clock=time.time_ns,
        websocket_factory=connect,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        _validate_symbol(symbol)
        if not isinstance(allowed_symbols, frozenset) or symbol not in allowed_symbols:
            raise BinancePublicTransportError(
                "PUBLIC_SYMBOL_NOT_ALLOWED", "Symbol allowlist kapsamında değil."
            )
        if not isinstance(time_unit, BinanceTimeUnit):
            raise BinancePublicTransportError(
                "PUBLIC_TIME_UNIT_INVALID", "Timestamp unit açıkça seçilmelidir."
            )
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 30:
            raise BinancePublicTransportError(
                "PUBLIC_TIMEOUT_INVALID", "Stream timeout değeri geçersiz."
            )
        self._symbol = symbol
        self._allowed_symbols = allowed_symbols
        self._time_unit = time_unit
        self._clock = clock
        self._websocket_factory = websocket_factory
        self._timeout_seconds = timeout_seconds
        self._socket = None

    async def connect(self) -> None:
        """Open the public stream; no subscription message, no credentials."""

        if self._socket is not None:
            raise BinancePublicTransportError(
                "PUBLIC_STREAM_ALREADY_CONNECTED", "Public stream zaten bağlı."
            )
        try:
            socket = self._websocket_factory(
                f"{BINANCE_SPOT_PUBLIC_WS_BASE_URL}/{self._symbol.lower()}@trade",
                max_size=MAX_PUBLIC_WS_FRAME_BYTES,
                compression=None,
                open_timeout=self._timeout_seconds,
            )
            self._socket = await socket if inspect.isawaitable(socket) else socket
        except (TimeoutError, OSError) as exc:
            raise BinancePublicTransportError(
                "PUBLIC_STREAM_UNAVAILABLE", "Public stream açılamadı."
            ) from exc
        except Exception as exc:
            raise BinancePublicTransportError(
                "PUBLIC_STREAM_UNAVAILABLE", "Public stream açılamadı."
            ) from exc

    async def recv_observation(self) -> PublicObservation:
        """Decode one bounded trade frame into a read-only observation."""

        if self._socket is None:
            raise BinancePublicTransportError(
                "PUBLIC_STREAM_NOT_CONNECTED", "Önce public stream bağlantısı kurulmalıdır."
            )
        try:
            raw_frame = await asyncio.wait_for(
                self._socket.recv(), timeout=self._timeout_seconds
            )
        except (TimeoutError, OSError) as exc:
            raise BinancePublicTransportError(
                "PUBLIC_STREAM_UNAVAILABLE", "Public stream okunamadı."
            ) from exc
        except Exception as exc:
            raise BinancePublicTransportError(
                "PUBLIC_STREAM_UNAVAILABLE", "Public stream okunamadı."
            ) from exc
        try:
            text = raw_frame.decode("utf-8") if isinstance(raw_frame, bytes) else raw_frame
            payload = json.loads(text)
            stamp = self._clock() // 1000
            return normalize_binance_trade_payload(
                payload,
                allowed_symbols=self._allowed_symbols,
                receive_time_us=stamp,
                processing_time_us=stamp,
                time_unit=self._time_unit,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
            raise BinancePublicTransportError(
                "PUBLIC_STREAM_FRAME_INVALID", "Public stream çerçevesi okunamadı."
            ) from exc
        except PublicFeedContractError as exc:
            raise BinancePublicTransportError(
                "PUBLIC_STREAM_FRAME_INVALID", "Public stream kaydı normalize edilemedi."
            ) from exc

    async def close(self) -> None:
        """Close the socket; never raises on an already-closed stream."""

        socket, self._socket = self._socket, None
        if socket is not None:
            try:
                await socket.close()
            except Exception:
                pass


def _validate_symbol(symbol: str) -> None:
    if type(symbol) is not str or _SYMBOL.fullmatch(symbol) is None:
        raise BinancePublicTransportError(
            "PUBLIC_SYMBOL_INVALID", "Symbol büyük harf alfanumerik olmalıdır."
        )


def _read_bounded_response(response: TransportResponse) -> bytes:
    headers = getattr(response, "headers", None)
    content_length = headers.get("Content-Length") if headers is not None else None
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except (TypeError, ValueError) as exc:
            raise BinancePublicTransportError(
                "PUBLIC_RESPONSE_INVALID", "Public yanıt Content-Length geçersiz."
            ) from exc
        if declared_size < 0 or declared_size > MAX_PUBLIC_RESPONSE_BYTES:
            raise BinancePublicTransportError(
                "PUBLIC_RESPONSE_TOO_LARGE", "Public yanıt byte sınırını aşıyor."
            )
    encoding = headers.get("Content-Encoding") if headers is not None else None
    if encoding and encoding.lower() != "identity":
        raise BinancePublicTransportError(
            "PUBLIC_ENCODING_INVALID", "Public yanıt sıkıştırma biçimi reddedildi."
        )
    payload = response.read(MAX_PUBLIC_RESPONSE_BYTES + 1)
    if not isinstance(payload, bytes):
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_INVALID", "Public yanıt gövdesi bytes olmalıdır."
        )
    if len(payload) > MAX_PUBLIC_RESPONSE_BYTES:
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_TOO_LARGE", "Public yanıt byte sınırını aşıyor."
        )
    return payload


def _decode_list(payload_bytes: bytes) -> list:
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_INVALID", "Public yanıt JSON olarak okunamadı."
        ) from exc
    if type(payload) is not list or len(payload) > MAX_TRADES_LIMIT:
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_INVALID", "Public trade yanıtı sınırlı liste olmalıdır."
        )
    return payload


def _read_bounded_list_response(response: TransportResponse) -> bytes:
    headers = getattr(response, "headers", None)
    content_length = headers.get("Content-Length") if headers is not None else None
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except (TypeError, ValueError) as exc:
            raise BinancePublicTransportError(
                "PUBLIC_RESPONSE_INVALID", "Public yanıt Content-Length geçersiz."
            ) from exc
        if declared_size < 0 or declared_size > MAX_EXCHANGE_INFO_RESPONSE_BYTES:
            raise BinancePublicTransportError(
                "PUBLIC_RESPONSE_TOO_LARGE", "Public yanıt byte sınırını aşıyor."
            )
    encoding = headers.get("Content-Encoding") if headers is not None else None
    if encoding and encoding.lower() != "identity":
        raise BinancePublicTransportError(
            "PUBLIC_ENCODING_INVALID", "Public yanıt sıkıştırma biçimi reddedildi."
        )
    payload = response.read(MAX_EXCHANGE_INFO_RESPONSE_BYTES + 1)
    if not isinstance(payload, bytes):
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_INVALID", "Public yanıt gövdesi bytes olmalıdır."
        )
    if len(payload) > MAX_EXCHANGE_INFO_RESPONSE_BYTES:
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_TOO_LARGE", "Public yanıt byte sınırını aşıyor."
        )
    return payload


def _decode_exchange_info(payload_bytes: bytes) -> dict:
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_INVALID", "Public yanıt JSON olarak okunamadı."
        ) from exc
    if type(payload) is not dict:
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_INVALID", "Public exchangeInfo yanıtı nesne olmalıdır."
        )
    return payload


def _normalize_listed_symbols(payload: dict) -> tuple[BinancePublicListedSymbol, ...]:
    symbols = payload.get("symbols")
    if type(symbols) is not list or len(symbols) > MAX_LISTED_SYMBOLS:
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_INVALID", "Public symbols alanı sınırlı liste olmalıdır."
        )
    normalized: list[BinancePublicListedSymbol] = []
    for entry in symbols:
        if type(entry) is not dict:
            raise BinancePublicTransportError(
                "PUBLIC_UPSTREAM_RECORD_INVALID", "Public symbol kaydı normalize edilemedi."
            )
        fields = (
            _listed_field(entry.get("symbol")),
            _listed_field(entry.get("status")),
            _listed_field(entry.get("baseAsset")),
            _listed_field(entry.get("quoteAsset")),
        )
        if any(field is None for field in fields):
            raise BinancePublicTransportError(
                "PUBLIC_UPSTREAM_RECORD_INVALID", "Public symbol kaydı normalize edilemedi."
            )
        symbol, status, base_asset, quote_asset = fields
        assert symbol is not None and status is not None
        assert base_asset is not None and quote_asset is not None
        normalized.append(
            BinancePublicListedSymbol(
                symbol=symbol, status=status, base_asset=base_asset, quote_asset=quote_asset
            )
        )
    return tuple(normalized)


def _listed_field(raw: object) -> str | None:
    if type(raw) is not str or not raw or len(raw) > MAX_LISTED_FIELD_LENGTH:
        return None
    if raw != raw.strip() or any(char.isspace() or ord(char) == 0x7F for char in raw):
        return None
    return raw
