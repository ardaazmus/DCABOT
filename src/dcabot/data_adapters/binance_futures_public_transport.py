"""Binance USD-M public futures transport: funding history + premium index.

Keyless GETs against the futures REST host, mirroring the spot public
transport discipline: bounded responses, no redirects, allowlisted
symbols, one bad record rejects the batch. Funding rates feed the
futures grid engine's explicit funding events; nothing here touches
orders, leverage brackets, or account state (those need credentials).
"""

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
import json
import re

from dcabot.data_adapters.binance_public_transport import (
    BinancePublicKline,
    BinancePublicTransportError,
    TransportOpener,
)
from dcabot.domain.numbers import exact_text, number

BINANCE_FUTURES_PUBLIC_REST_BASE_URL = "https://fapi.binance.com/fapi"
BINANCE_FUTURES_FUNDING_RATE_URL = f"{BINANCE_FUTURES_PUBLIC_REST_BASE_URL}/v1/fundingRate"
BINANCE_FUTURES_PREMIUM_INDEX_URL = f"{BINANCE_FUTURES_PUBLIC_REST_BASE_URL}/v1/premiumIndex"
BINANCE_FUTURES_EXCHANGE_INFO_URL = f"{BINANCE_FUTURES_PUBLIC_REST_BASE_URL}/v1/exchangeInfo"
BINANCE_FUTURES_KLINES_URL = f"{BINANCE_FUTURES_PUBLIC_REST_BASE_URL}/v1/klines"
FUTURES_KLINE_INTERVALS = frozenset(
    {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"}
)
FUTURES_KLINE_INTERVAL_US = {
    "1m": 60_000_000,
    "5m": 300_000_000,
    "15m": 900_000_000,
    "30m": 1_800_000_000,
    "1h": 3_600_000_000,
    "4h": 14_400_000_000,
    "1d": 86_400_000_000,
}
MAX_KLINES_LIMIT = 1000
_KLINE_ROW_LENGTH = 12

DEFAULT_TIMEOUT_SECONDS = 5
MAX_FUNDING_LIMIT = 1000
MAX_FUNDING_RECORDS = 5000
MAX_FUNDING_RESPONSE_BYTES = 256 * 1024
MAX_PREMIUM_RESPONSE_BYTES = 16 * 1024
# fapi ignores ?symbol and always returns every contract: observed
# 2026-09-27 at 1,127,625 bytes / 907 symbols. 2 MB keeps ~1.8x headroom.
MAX_SYMBOL_RULES_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_RULE_FIELD_LENGTH = 32
_FUNDING_INTERVAL_US = 8 * 3_600_000_000
_SYMBOL = re.compile(r"[A-Z0-9]{1,20}\Z", re.ASCII)


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, new):
        raise BinancePublicTransportError(
            "PUBLIC_REDIRECT_REJECTED", "Public market-data yönlendirmesi reddedildi."
        )


@dataclass(frozen=True, slots=True)
class BinanceFuturesFundingRate:
    """One settled 8h funding interval: venue time plus signed rate."""

    funding_time_us: int
    rate: str


@dataclass(frozen=True, slots=True)
class BinanceFuturesPremium:
    """Current mark/index snapshot plus the last settled funding rate."""

    symbol: str
    mark_price: str
    index_price: str
    last_funding_rate: str


def _validate_symbol(symbol: str) -> None:
    if type(symbol) is not str or _SYMBOL.fullmatch(symbol) is None:
        raise BinancePublicTransportError(
            "PUBLIC_SYMBOL_INVALID", "Symbol büyük harf alfanumerik olmalıdır."
        )


def _check_common(
    symbol: str, allowed_symbols: frozenset[str], timeout_seconds: int
) -> None:
    _validate_symbol(symbol)
    if not isinstance(allowed_symbols, frozenset) or symbol not in allowed_symbols:
        raise BinancePublicTransportError(
            "PUBLIC_SYMBOL_NOT_ALLOWED", "Symbol allowlist kapsamında değil."
        )
    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30:
        raise BinancePublicTransportError(
            "PUBLIC_TIMEOUT_INVALID", "Transport timeout değeri geçersiz."
        )


def _read_bounded(response, limit: int) -> bytes:
    headers = getattr(response, "headers", None)
    declared = headers.get("Content-Length") if headers is not None else None
    if declared is not None:
        try:
            size = int(declared)
        except (TypeError, ValueError) as exc:
            raise BinancePublicTransportError(
                "PUBLIC_RESPONSE_INVALID", "Public yanıt Content-Length geçersiz."
            ) from exc
        if size < 0 or size > limit:
            raise BinancePublicTransportError(
                "PUBLIC_RESPONSE_TOO_LARGE", "Public yanıt byte sınırını aşıyor."
            )
    encoding = headers.get("Content-Encoding") if headers is not None else None
    if encoding and str(encoding).lower() != "identity":
        raise BinancePublicTransportError(
            "PUBLIC_ENCODING_INVALID", "Public yanıt sıkıştırma biçimi reddedildi."
        )
    payload = response.read(limit + 1)
    if not isinstance(payload, bytes):
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_INVALID", "Public yanıt gövdesi bytes olmalıdır."
        )
    if len(payload) > limit:
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_TOO_LARGE", "Public yanıt byte sınırını aşıyor."
        )
    return payload


def _get_json(url: str, *, limit: int, opener: TransportOpener | None, timeout_seconds: int):
    request = Request(
        url,
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        method="GET",
    )
    active_opener = opener or build_opener(_NoRedirectHandler())
    response = None
    try:
        response = active_opener.open(request, timeout=timeout_seconds)
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()  # type: ignore[attr-defined]
        if status != 200:
            raise BinancePublicTransportError(
                "PUBLIC_UPSTREAM_HTTP_ERROR", "Public market-data HTTP yanıtı başarılı değil."
            )
        raw = _read_bounded(response, limit)
    except BinancePublicTransportError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı."
        ) from exc
    finally:
        if response is not None:
            response.close()
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_INVALID", "Public yanıt JSON olarak okunamadı."
        ) from exc


def _normalize_funding_rate(record: dict, expected_symbol: str) -> BinanceFuturesFundingRate:
    try:
        if type(record) is not dict or record.get("symbol") != expected_symbol:
            raise ValueError
        funding_ms = record.get("fundingTime")
        if type(funding_ms) is not int or funding_ms < 0:
            raise ValueError
        rate = number(record.get("fundingRate"))
        if abs(rate) > 1:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_UPSTREAM_RECORD_INVALID", "Funding kaydı normalize edilemedi."
        ) from exc
    return BinanceFuturesFundingRate(funding_time_us=funding_ms * 1000, rate=exact_text(rate))


def fetch_funding_rate_history(
    symbol: str,
    *,
    start_us: int,
    end_us: int,
    allowed_symbols: frozenset[str],
    opener: TransportOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[BinanceFuturesFundingRate, ...]:
    """Fetch settled funding intervals with fundingTime in [start_us, end_us).

    Oldest first, strictly increasing; a single malformed or
    out-of-order record rejects the batch. Gaps are returned as-is
    (callers treat a missing interval as unknown, never as zero).
    """

    _check_common(symbol, allowed_symbols, timeout_seconds)
    if (
        not all(type(value) is int for value in (start_us, end_us))
        or not 0 <= start_us < end_us
    ):
        raise BinancePublicTransportError("PUBLIC_RANGE_INVALID", "Tarih aralığı geçersiz.")
    expected_pages = -(-(end_us - start_us) // _FUNDING_INTERVAL_US) + 1
    if expected_pages * 1 > MAX_FUNDING_RECORDS:
        raise BinancePublicTransportError(
            "PUBLIC_RANGE_TOO_LARGE", f"Aralık en fazla {MAX_FUNDING_RECORDS} funding kaydı içerebilir."
        )
    records: list[BinanceFuturesFundingRate] = []
    cursor_ms = start_us // 1000
    end_ms = (end_us - 1) // 1000
    while cursor_ms <= end_ms:
        query = urlencode(
            {"symbol": symbol, "startTime": cursor_ms, "endTime": end_ms, "limit": MAX_FUNDING_LIMIT},
            encoding="utf-8",
        )
        payload = _get_json(
            f"{BINANCE_FUTURES_FUNDING_RATE_URL}?{query}",
            limit=MAX_FUNDING_RESPONSE_BYTES,
            opener=opener,
            timeout_seconds=timeout_seconds,
        )
        if type(payload) is not list or len(payload) > MAX_FUNDING_LIMIT:
            raise BinancePublicTransportError(
                "PUBLIC_RESPONSE_INVALID", "Funding yanıtı sınırlı liste olmalıdır."
            )
        page = tuple(_normalize_funding_rate(record, symbol) for record in payload)
        for item in page:
            if records and item.funding_time_us <= records[-1].funding_time_us:
                raise BinancePublicTransportError(
                    "PUBLIC_UPSTREAM_RECORD_INVALID", "Funding kayıtları sıralı değil."
                )
            records.append(item)
        if len(records) > MAX_FUNDING_RECORDS:
            raise BinancePublicTransportError(
                "PUBLIC_RANGE_TOO_LARGE", f"Aralık en fazla {MAX_FUNDING_RECORDS} funding kaydı içerebilir."
            )
        if len(page) < MAX_FUNDING_LIMIT:
            break
        cursor_ms = page[-1].funding_time_us // 1000 + 1
    return tuple(item for item in records if start_us <= item.funding_time_us < end_us)


@dataclass(frozen=True, slots=True)
class BinanceFuturesSymbolRules:
    """One USDT-M symbol's venue trading rules, exact text; no market values."""

    symbol: str
    status: str
    base_asset: str
    quote_asset: str
    contract_type: str
    tick: str
    qty_step: str
    min_qty: str
    min_notional: str


def fetch_futures_symbol_rules(
    symbol: str,
    *,
    allowed_symbols: frozenset[str],
    opener: TransportOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> BinanceFuturesSymbolRules:
    """Fetch one symbol's PRICE_FILTER/LOT_SIZE/MIN_NOTIONAL rules or fail closed."""

    _check_common(symbol, allowed_symbols, timeout_seconds)
    query = urlencode({"symbol": symbol}, encoding="utf-8")
    payload = _get_json(
        f"{BINANCE_FUTURES_EXCHANGE_INFO_URL}?{query}",
        limit=MAX_SYMBOL_RULES_RESPONSE_BYTES,
        opener=opener,
        timeout_seconds=timeout_seconds,
    )
    try:
        if type(payload) is not dict:
            raise ValueError
        symbols = payload.get("symbols")
        if type(symbols) is not list or not symbols or len(symbols) > 5000:
            raise ValueError
        matches = [entry for entry in symbols if type(entry) is dict and entry.get("symbol") == symbol]
        if len(matches) != 1:
            raise ValueError
        entry = matches[0]
        names = (
            entry.get("status"),
            entry.get("baseAsset"),
            entry.get("quoteAsset"),
            entry.get("contractType"),
        )
        if not all(type(name) is str and 0 < len(name) <= MAX_RULE_FIELD_LENGTH for name in names):
            raise ValueError
        by_type: dict[str, dict] = {}
        for item in entry.get("filters", ()):
            if type(item) is dict and type(item.get("filterType")) is str:
                by_type[item["filterType"]] = item
        tick = number(by_type["PRICE_FILTER"]["tickSize"])
        step = number(by_type["LOT_SIZE"]["stepSize"])
        min_qty = number(by_type["LOT_SIZE"]["minQty"])
        min_notional = number(by_type["MIN_NOTIONAL"]["notional"])
        if tick <= 0 or step <= 0 or min_qty < 0 or min_notional < 0:
            raise ValueError
    except (KeyError, TypeError, ValueError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_UPSTREAM_RECORD_INVALID", "Sembol kuralları normalize edilemedi."
        ) from exc
    assert all(type(name) is str for name in names)
    return BinanceFuturesSymbolRules(
        symbol=symbol,
        status=names[0],  # type: ignore[arg-type]
        base_asset=names[1],  # type: ignore[arg-type]
        quote_asset=names[2],  # type: ignore[arg-type]
        contract_type=names[3],  # type: ignore[arg-type]
        tick=exact_text(tick),
        qty_step=exact_text(step),
        min_qty=exact_text(min_qty),
        min_notional=exact_text(min_notional),
    )


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
                    close_time_us=close_ms * 1000,
                    open=exact_text(open_),
                    high=exact_text(high),
                    low=exact_text(low),
                    close=exact_text(close),
                    base_volume=exact_text(volume),
                )
            )
            previous_close_ms = close_ms
        except (TypeError, ValueError) as exc:
            raise BinancePublicTransportError(
                "PUBLIC_UPSTREAM_RECORD_INVALID", "Kline kaydı normalize edilemedi."
            ) from exc
    return tuple(klines)


def _request_klines(
    params: dict,
    *,
    limit: int,
    opener: TransportOpener | None,
    timeout_seconds: int,
) -> tuple[BinancePublicKline, ...]:
    query = urlencode(params, encoding="utf-8")
    payload = _get_json(
        f"{BINANCE_FUTURES_KLINES_URL}?{query}",
        limit=MAX_FUNDING_RESPONSE_BYTES,
        opener=opener,
        timeout_seconds=timeout_seconds,
    )
    if type(payload) is not list or len(payload) > limit:
        raise BinancePublicTransportError(
            "PUBLIC_RESPONSE_INVALID", "Kline yanıtı istenen limiti aşıyor."
        )
    return _normalize_klines(payload)


def fetch_futures_public_klines_range(
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
    """Fetch every CLOSED futures kline in [start_us, end_us), oldest first.

    Trade-price klines (fills happen at traded prices); the mark/trade
    basis is not modeled and is recorded by callers as an assumption.
    """

    _check_common(symbol, allowed_symbols, timeout_seconds)
    interval_us = FUTURES_KLINE_INTERVAL_US.get(interval) if type(interval) is str else None
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


def fetch_premium_index(
    symbol: str,
    *,
    allowed_symbols: frozenset[str],
    opener: TransportOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> BinanceFuturesPremium:
    """Fetch the current mark/index snapshot plus last funding rate."""

    _check_common(symbol, allowed_symbols, timeout_seconds)
    query = urlencode({"symbol": symbol}, encoding="utf-8")
    payload = _get_json(
        f"{BINANCE_FUTURES_PREMIUM_INDEX_URL}?{query}",
        limit=MAX_PREMIUM_RESPONSE_BYTES,
        opener=opener,
        timeout_seconds=timeout_seconds,
    )
    try:
        if type(payload) is not dict or payload.get("symbol") != symbol:
            raise ValueError
        mark = number(payload.get("markPrice"))
        index = number(payload.get("indexPrice"))
        rate = number(payload.get("lastFundingRate"))
        if mark <= 0 or index <= 0 or abs(rate) > 1:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise BinancePublicTransportError(
            "PUBLIC_UPSTREAM_RECORD_INVALID", "Premium index kaydı normalize edilemedi."
        ) from exc
    return BinanceFuturesPremium(
        symbol=symbol,
        mark_price=exact_text(mark),
        index_price=exact_text(index),
        last_funding_rate=exact_text(rate),
    )
