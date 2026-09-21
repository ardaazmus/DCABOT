"""Bounded, credential-free Binance Spot public market-data transport.

This is the ONLY module that opens public market-data connections (REST and
WebSocket) for paper trading. Requests never carry credentials; responses are
bounded before decoding and reduced to normalized read-only observations.
"""

import asyncio
import inspect
import json
import re
import time
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


BINANCE_SPOT_PUBLIC_REST_BASE_URL = "https://data-api.binance.vision/api"
BINANCE_SPOT_PUBLIC_TRADES_URL = f"{BINANCE_SPOT_PUBLIC_REST_BASE_URL}/v3/trades"
BINANCE_SPOT_PUBLIC_WS_BASE_URL = "wss://stream.binance.vision/ws"
MAX_PUBLIC_RESPONSE_BYTES = 256 * 1024
MAX_PUBLIC_WS_FRAME_BYTES = 64 * 1024
DEFAULT_TIMEOUT_SECONDS = 5
MAX_TRADES_LIMIT = 1000
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
