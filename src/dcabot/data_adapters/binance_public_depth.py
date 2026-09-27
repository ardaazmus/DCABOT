"""Bounded, credential-free Binance Spot public order-book depth transport
(Faz 17 E.3, Whale Wall Detection Faz-0 -- data ingestion only).

**Correction vs. the original brief (verified 2026-09-22 against
developers.binance.com):** spot diff-depth (`@depth`) frames carry only
`e`/`E`/`s`/`U`/`u`/`b`/`a` -- there is NO `pu` field on spot (that field
exists only on the futures diff-book-depth stream). The official spot
local-order-book sync algorithm uses U/u and a REST snapshot's
`lastUpdateId` only:
  1. Buffer WS events while fetching a REST snapshot.
  2. Discard any buffered event whose `u` <= snapshot `lastUpdateId`.
  3. The first applied event must satisfy `U <= lastUpdateId+1 <= u`.
  4. Thereafter: if `event.u < local_last_id`, ignore (stale); if
     `event.U > local_last_id + 1`, a gap was missed -- resync from
     step 1; otherwise apply and set `local_last_id = event.u`.
The sync state machine itself lives in `application/whale_depth_sync.py`
(the RG-02 v2->v3 precedent -- brief text can be stale, the real API
contract wins).
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

from dcabot.domain.numbers import number

BINANCE_SPOT_PUBLIC_REST_BASE_URL = "https://data-api.binance.vision/api"
BINANCE_SPOT_PUBLIC_DEPTH_URL = f"{BINANCE_SPOT_PUBLIC_REST_BASE_URL}/v3/depth"
BINANCE_SPOT_PUBLIC_WS_BASE_URL = "wss://stream.binance.vision/ws"
MAX_DEPTH_RESPONSE_BYTES = 1024 * 1024
MAX_DEPTH_WS_FRAME_BYTES = 256 * 1024
MAX_DEPTH_LIMIT = 5000
MAX_DEPTH_LEVELS = 5000
DEFAULT_TIMEOUT_SECONDS = 5
_SYMBOL = re.compile(r"[A-Z0-9]{1,20}\Z", re.ASCII)


class BinancePublicDepthError(RuntimeError):
    """Raised when public depth data cannot be fetched or decoded safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class DepthTransportResponse(Protocol):
    status: int
    headers: object

    def read(self, size: int = -1) -> bytes: ...

    def close(self) -> None: ...


class DepthTransportOpener(Protocol):
    def open(self, request: Request, timeout: int) -> DepthTransportResponse: ...


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, new):
        raise BinancePublicDepthError(
            "PUBLIC_DEPTH_REDIRECT_REJECTED", "Depth yönlendirmesi reddedildi."
        )


@dataclass(frozen=True, slots=True)
class DepthSnapshot:
    """One `GET /api/v3/depth` response; exact price/qty text, unmodified."""

    last_update_id: int
    bids: tuple[tuple[str, str], ...]
    asks: tuple[tuple[str, str], ...]
    used_weight_1m: int | None


@dataclass(frozen=True, slots=True)
class DepthDiffEvent:
    """One normalized `@depth` WS frame; spot has no `pu` field (see module docstring)."""

    symbol: str
    event_time_ms: int
    first_update_id: int
    final_update_id: int
    bids: tuple[tuple[str, str], ...]
    asks: tuple[tuple[str, str], ...]


def _validate_symbol(symbol: str) -> None:
    if type(symbol) is not str or _SYMBOL.fullmatch(symbol) is None:
        raise BinancePublicDepthError(
            "PUBLIC_DEPTH_SYMBOL_INVALID", "Symbol büyük harf alfanumerik olmalıdır."
        )


def _validate_levels(raw: object, field_name: str) -> tuple[tuple[str, str], ...]:
    if type(raw) is not list or len(raw) > MAX_DEPTH_LEVELS:
        raise BinancePublicDepthError(
            "PUBLIC_DEPTH_RESPONSE_INVALID", f"{field_name} bounded liste olmalıdır."
        )
    levels: list[tuple[str, str]] = []
    for level in raw:
        if type(level) is not list or len(level) != 2:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_RESPONSE_INVALID", f"{field_name} seviyesi [price, qty] olmalıdır."
            )
        price, qty = level
        if type(price) is not str or type(qty) is not str:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_RESPONSE_INVALID", f"{field_name} price/qty metin olmalıdır."
            )
        try:
            if number(price) < 0 or number(qty) < 0:
                raise ValueError("negative")
        except ValueError as exc:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_RESPONSE_INVALID", f"{field_name} exact decimal olmalıdır."
            ) from exc
        levels.append((price, qty))
    return tuple(levels)


def fetch_binance_public_depth_snapshot(
    symbol: str,
    *,
    limit: int,
    opener: DepthTransportOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> DepthSnapshot:
    """Fetch one bounded order-book snapshot; the venue's own weight usage
    (if reported) is returned for the caller to feed into `LabRateBudget.
    observe_used_weight_1m` -- this function does not consult any budget
    itself, keeping transport and rate-limiting concerns separate."""

    _validate_symbol(symbol)
    if type(limit) is not int or not 1 <= limit <= MAX_DEPTH_LIMIT:
        raise BinancePublicDepthError(
            "PUBLIC_DEPTH_LIMIT_INVALID", "Depth limiti 1 ile 5000 arasında olmalıdır."
        )
    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30:
        raise BinancePublicDepthError(
            "PUBLIC_DEPTH_TIMEOUT_INVALID", "Transport timeout değeri geçersiz."
        )
    query = urlencode({"symbol": symbol, "limit": limit}, encoding="utf-8")
    request = Request(
        f"{BINANCE_SPOT_PUBLIC_DEPTH_URL}?{query}",
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        method="GET",
    )
    active_opener = opener or build_opener(_NoRedirectHandler())
    response: DepthTransportResponse | None = None
    try:
        response = active_opener.open(request, timeout=timeout_seconds)
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()  # type: ignore[attr-defined]
        if status != 200:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_HTTP_ERROR", "Depth HTTP yanıtı başarılı değil."
            )
        payload_bytes = _read_bounded(response)
        used_weight = _read_used_weight_header(response)
        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_RESPONSE_INVALID", "Depth yanıtı JSON olarak okunamadı."
            ) from exc
        if type(payload) is not dict:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_RESPONSE_INVALID", "Depth yanıtı nesne olmalıdır."
            )
        last_update_id = payload.get("lastUpdateId")
        if type(last_update_id) is not int or last_update_id < 0:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_RESPONSE_INVALID", "lastUpdateId alanı geçersiz."
            )
        return DepthSnapshot(
            last_update_id=last_update_id,
            bids=_validate_levels(payload.get("bids"), "bids"),
            asks=_validate_levels(payload.get("asks"), "asks"),
            used_weight_1m=used_weight,
        )
    except BinancePublicDepthError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise BinancePublicDepthError(
            "PUBLIC_DEPTH_UNAVAILABLE", "Depth yanıtı alınamadı."
        ) from exc
    finally:
        if response is not None:
            response.close()


def _read_used_weight_header(response: DepthTransportResponse) -> int | None:
    headers = getattr(response, "headers", None)
    raw = headers.get("X-MBX-USED-WEIGHT-1M") if headers is not None else None
    if raw is None:
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


def _read_bounded(response: DepthTransportResponse) -> bytes:
    headers = getattr(response, "headers", None)
    content_length = headers.get("Content-Length") if headers is not None else None
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except (TypeError, ValueError) as exc:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_RESPONSE_INVALID", "Content-Length geçersiz."
            ) from exc
        if declared_size < 0 or declared_size > MAX_DEPTH_RESPONSE_BYTES:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_RESPONSE_TOO_LARGE", "Depth yanıt byte sınırını aşıyor."
            )
    encoding = headers.get("Content-Encoding") if headers is not None else None
    if encoding and encoding.lower() != "identity":
        raise BinancePublicDepthError(
            "PUBLIC_DEPTH_ENCODING_INVALID", "Depth yanıt sıkıştırma biçimi reddedildi."
        )
    payload = response.read(MAX_DEPTH_RESPONSE_BYTES + 1)
    if not isinstance(payload, bytes) or len(payload) > MAX_DEPTH_RESPONSE_BYTES:
        raise BinancePublicDepthError(
            "PUBLIC_DEPTH_RESPONSE_TOO_LARGE", "Depth yanıt byte sınırını aşıyor."
        )
    return payload


def normalize_depth_diff_event(raw_frame: str | bytes) -> DepthDiffEvent:
    """Decode+validate one `@depth` WS text frame into a `DepthDiffEvent`.

    Pure function (no I/O) so sync-logic tests can feed frame sequences
    directly without a real socket. No `pu` field is read or required.
    """

    if isinstance(raw_frame, bytes):
        if len(raw_frame) > MAX_DEPTH_WS_FRAME_BYTES:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_FRAME_TOO_LARGE", "Depth çerçevesi byte sınırını aşıyor."
            )
        try:
            raw_frame = raw_frame.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_FRAME_INVALID", "Depth çerçevesi UTF-8 değil."
            ) from exc
    elif len(raw_frame.encode("utf-8")) > MAX_DEPTH_WS_FRAME_BYTES:
        raise BinancePublicDepthError(
            "PUBLIC_DEPTH_FRAME_TOO_LARGE", "Depth çerçevesi byte sınırını aşıyor."
        )
    try:
        payload = json.loads(raw_frame)
    except json.JSONDecodeError as exc:
        raise BinancePublicDepthError(
            "PUBLIC_DEPTH_FRAME_INVALID", "Depth çerçevesi JSON olarak okunamadı."
        ) from exc
    if type(payload) is not dict or payload.get("e") != "depthUpdate":
        raise BinancePublicDepthError(
            "PUBLIC_DEPTH_FRAME_INVALID", "Depth çerçevesi depthUpdate olmalıdır."
        )
    symbol = payload.get("s")
    _validate_symbol(symbol) if isinstance(symbol, str) else (_ for _ in ()).throw(
        BinancePublicDepthError("PUBLIC_DEPTH_FRAME_INVALID", "Depth symbol alanı geçersiz.")
    )
    event_time = payload.get("E")
    first_id = payload.get("U")
    final_id = payload.get("u")
    if (
        type(event_time) is not int or event_time < 0
        or type(first_id) is not int or first_id < 0
        or type(final_id) is not int or final_id < first_id
    ):
        raise BinancePublicDepthError(
            "PUBLIC_DEPTH_FRAME_INVALID", "Depth E/U/u alanları geçersiz."
        )
    return DepthDiffEvent(
        symbol=symbol,
        event_time_ms=event_time,
        first_update_id=first_id,
        final_update_id=final_id,
        bids=_validate_levels(payload.get("b"), "b"),
        asks=_validate_levels(payload.get("a"), "a"),
    )


class BinancePublicDepthStream:
    """Read-only public `@depth` stream with an injected socket factory
    (mirrors `BinancePublicTradeStream`'s tested connection pattern)."""

    def __init__(
        self,
        symbol: str,
        *,
        websocket_factory=connect,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        _validate_symbol(symbol)
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 30:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_TIMEOUT_INVALID", "Stream timeout değeri geçersiz."
            )
        self._symbol = symbol
        self._websocket_factory = websocket_factory
        self._timeout_seconds = timeout_seconds
        self._socket = None

    async def connect(self) -> None:
        if self._socket is not None:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_STREAM_ALREADY_CONNECTED", "Depth stream zaten bağlı."
            )
        try:
            socket = self._websocket_factory(
                f"{BINANCE_SPOT_PUBLIC_WS_BASE_URL}/{self._symbol.lower()}@depth",
                max_size=MAX_DEPTH_WS_FRAME_BYTES,
                compression=None,
                open_timeout=self._timeout_seconds,
            )
            self._socket = await socket if inspect.isawaitable(socket) else socket
        except (TimeoutError, OSError) as exc:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_STREAM_UNAVAILABLE", "Depth stream açılamadı."
            ) from exc
        except Exception as exc:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_STREAM_UNAVAILABLE", "Depth stream açılamadı."
            ) from exc

    async def recv_event(self) -> DepthDiffEvent:
        if self._socket is None:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_STREAM_NOT_CONNECTED", "Önce depth stream bağlantısı kurulmalıdır."
            )
        try:
            raw_frame = await asyncio.wait_for(
                self._socket.recv(), timeout=self._timeout_seconds
            )
        except (TimeoutError, OSError) as exc:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_STREAM_UNAVAILABLE", "Depth stream okunamadı."
            ) from exc
        except Exception as exc:
            raise BinancePublicDepthError(
                "PUBLIC_DEPTH_STREAM_UNAVAILABLE", "Depth stream okunamadı."
            ) from exc
        return normalize_depth_diff_event(raw_frame)

    async def close(self) -> None:
        socket, self._socket = self._socket, None
        if socket is not None:
            try:
                await socket.close()
            except Exception:
                pass
