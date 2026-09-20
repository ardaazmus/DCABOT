"""The ONLY module in this codebase that can place or cancel a real order.

Every other Binance Testnet adapter (`binance_testnet_public.py`,
`binance_testnet_account.py`, `binance_testnet_user_stream.py`) is read-only
by design. This module is intentionally separate and intentionally the sole
place a signed mutating request (`order.place` / `order.cancel`) is built,
so "can this codebase place an order" has exactly one file to audit.

Faz 3.4's mutation gate (docs/KARARLAR.md, 2026-09-21) governs every call
here: kill-switch, `max_entry_notional`, execution-time confirmation,
idempotent clientOrderId + durable-before-send via `AttemptStore`, single
in-flight mutation, and the testnet-only base URL are enforced by the
caller (`application/testnet_order_execution.py`), not by this transport
layer alone — this file only refuses to run if the kill-switch is off, as a
second, independent check.
"""

import asyncio
from dataclasses import dataclass
import inspect
import json
import os
import re
from typing import Awaitable, Callable, Protocol
from uuid import uuid4

from websockets.asyncio.client import connect

from dcabot.application.credential_boundary import CredentialProvider
from dcabot.application.signed_request import (
    ApiKeyType,
    Clock,
    DEFAULT_RECV_WINDOW_MS,
    HmacSha256Signer,
    SignedRequestError,
    build_signed_ws_api_params,
)


BINANCE_SPOT_TESTNET_WS_API_URL = "wss://ws-api.testnet.binance.vision/ws-api/v3"
MAX_ORDER_FRAME_BYTES = 256 * 1024
DEFAULT_ORDER_TIMEOUT_SECONDS = 10
TRADING_ENABLED_ENV_VAR = "DCABOT_TRADING_ENABLED"
_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,128}\Z", re.ASCII)
_CLIENT_ORDER_ID = re.compile(r"[A-Za-z0-9_-]{1,36}\Z", re.ASCII)
_SYMBOL = re.compile(r"[A-Z0-9]{1,32}\Z", re.ASCII)


class BinanceTestnetOrderExecutionError(RuntimeError):
    """Raised when a real order placement/cancellation cannot safely proceed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class OrderRejectedByVenue(BinanceTestnetOrderExecutionError):
    """A definitive, synchronous "no" from the venue -- never ambiguous.

    Raised only when the venue itself answered with a clean non-200 response
    (e.g. a filter failure). Distinct from the base error so a caller can
    tell "the venue said no" (REJECTED, terminal, no reconciliation needed)
    apart from a genuine transport failure (UNKNOWN, needs REST catch-up) --
    found live: an early manual test conflated the two and marked a cleanly
    rejected order UNKNOWN, which would have queued it for catch-up it never
    needed.
    """

    def __init__(self, code: str, message: str, *, venue_error_code: int | None) -> None:
        super().__init__(code, message)
        self.venue_error_code = venue_error_code


class OrderSocket(Protocol):
    async def send(self, message: str) -> None: ...

    async def recv(self) -> str | bytes: ...

    async def close(self) -> None: ...


WebSocketFactory = Callable[..., Awaitable[OrderSocket] | OrderSocket]


@dataclass(frozen=True, slots=True)
class PlacedTestnetOrder:
    """Redacted evidence of one real LIMIT order accepted by the venue."""

    symbol: str
    order_id: int
    client_order_id: str
    status: str
    transact_time_ms: int


@dataclass(frozen=True, slots=True)
class CancelledTestnetOrder:
    """Redacted evidence of one real order cancellation accepted by the venue."""

    symbol: str
    order_id: int
    client_order_id: str
    status: str


def trading_kill_switch_enabled() -> bool:
    """Read the global kill-switch. Default is OFF; only the exact string "true" opens it."""

    return os.getenv(TRADING_ENABLED_ENV_VAR) == "true"


def _require_kill_switch() -> None:
    if not trading_kill_switch_enabled():
        raise BinanceTestnetOrderExecutionError(
            "TRADING_KILL_SWITCH_OFF",
            f"{TRADING_ENABLED_ENV_VAR} 'true' değil; hiçbir mutating istek gönderilmez.",
        )


async def place_binance_testnet_limit_order(
    credential_id: str,
    symbol: str,
    side: str,
    quantity: str,
    price: str,
    client_order_id: str,
    *,
    provider: CredentialProvider,
    clock: Clock,
    websocket_factory: WebSocketFactory = connect,
    request_id_factory: Callable[[], str] = lambda: str(uuid4()),
    timeout_seconds: int = DEFAULT_ORDER_TIMEOUT_SECONDS,
) -> PlacedTestnetOrder:
    """Place one real GTC LIMIT order on Binance Spot Testnet. Never MARKET, never OCO.

    The kill-switch is checked here too (independent of the caller) so this
    function can never be reached into and used to bypass it.
    """

    _require_kill_switch()
    if side not in ("BUY", "SELL"):
        raise BinanceTestnetOrderExecutionError("ORDER_SIDE_INVALID", "Side yalnız BUY veya SELL olabilir.")
    if not isinstance(symbol, str) or _SYMBOL.fullmatch(symbol) is None:
        raise BinanceTestnetOrderExecutionError("ORDER_SYMBOL_INVALID", "Symbol geçersiz.")
    if (
        not isinstance(client_order_id, str)
        or _CLIENT_ORDER_ID.fullmatch(client_order_id) is None
    ):
        raise BinanceTestnetOrderExecutionError(
            "ORDER_CLIENT_ORDER_ID_INVALID", "Client order ID geçersiz."
        )
    for label, value in (("quantity", quantity), ("price", price)):
        if (
            not isinstance(value, str)
            or not value
            or len(value) > 64
            or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
        ):
            raise BinanceTestnetOrderExecutionError(
                "ORDER_AMOUNT_INVALID", f"Order {label} bounded exact decimal metin olmalıdır."
            )
    return await _send_order_request(
        credential_id,
        method="order.place",
        params=(
            ("symbol", symbol),
            ("side", side),
            ("type", "LIMIT"),
            ("timeInForce", "GTC"),
            ("quantity", quantity),
            ("price", price),
            ("newClientOrderId", client_order_id),
        ),
        decode=_decode_placed_order,
        provider=provider,
        clock=clock,
        websocket_factory=websocket_factory,
        request_id_factory=request_id_factory,
        timeout_seconds=timeout_seconds,
    )


async def cancel_binance_testnet_order(
    credential_id: str,
    symbol: str,
    *,
    order_id: int | None = None,
    client_order_id: str | None = None,
    provider: CredentialProvider,
    clock: Clock,
    websocket_factory: WebSocketFactory = connect,
    request_id_factory: Callable[[], str] = lambda: str(uuid4()),
    timeout_seconds: int = DEFAULT_ORDER_TIMEOUT_SECONDS,
) -> CancelledTestnetOrder:
    """Cancel one real order by exactly one of venue order ID or client order ID."""

    _require_kill_switch()
    if not isinstance(symbol, str) or _SYMBOL.fullmatch(symbol) is None:
        raise BinanceTestnetOrderExecutionError("ORDER_SYMBOL_INVALID", "Symbol geçersiz.")
    if (order_id is None) == (client_order_id is None):
        raise BinanceTestnetOrderExecutionError(
            "ORDER_CANCEL_IDENTITY_INVALID",
            "Cancel için tam olarak biri: order_id veya client_order_id.",
        )
    if order_id is not None:
        if type(order_id) is not int or order_id < 0:
            raise BinanceTestnetOrderExecutionError("ORDER_ID_INVALID", "Order ID geçersiz.")
        id_param = ("orderId", order_id)
    else:
        if _CLIENT_ORDER_ID.fullmatch(client_order_id) is None:
            raise BinanceTestnetOrderExecutionError(
                "ORDER_CLIENT_ORDER_ID_INVALID", "Client order ID geçersiz."
            )
        id_param = ("origClientOrderId", client_order_id)
    return await _send_order_request(
        credential_id,
        method="order.cancel",
        params=(("symbol", symbol), id_param),
        decode=_decode_cancelled_order,
        provider=provider,
        clock=clock,
        websocket_factory=websocket_factory,
        request_id_factory=request_id_factory,
        timeout_seconds=timeout_seconds,
    )


async def _send_order_request(
    credential_id: str,
    *,
    method: str,
    params: tuple[tuple[str, str | int], ...],
    decode: Callable[[dict[str, object]], object],
    provider: CredentialProvider,
    clock: Clock,
    websocket_factory: WebSocketFactory,
    request_id_factory: Callable[[], str],
    timeout_seconds: int,
) -> object:
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 30:
        raise BinanceTestnetOrderExecutionError("ORDER_TIMEOUT_INVALID", "Timeout değeri geçersiz.")
    socket: OrderSocket | None = None
    try:
        material = provider.load(credential_id)
        if material.key_type is not ApiKeyType.HMAC:
            raise BinanceTestnetOrderExecutionError(
                "ORDER_KEY_TYPE_UNSUPPORTED", "Yalnız HMAC key destekleniyor."
            )
        request_id = request_id_factory()
        if not isinstance(request_id, str) or _IDENTIFIER.fullmatch(request_id) is None:
            raise BinanceTestnetOrderExecutionError("ORDER_REQUEST_ID_INVALID", "Request ID geçersiz.")
        signed = build_signed_ws_api_params(
            material.api_key,
            params,
            clock=clock,
            recv_window_ms=DEFAULT_RECV_WINDOW_MS,
            signer=HmacSha256Signer(material.secret),
        )
        request = json.dumps(
            {"id": request_id, "method": method, "params": signed},
            ensure_ascii=True,
            separators=(",", ":"),
        )
        socket = websocket_factory(
            BINANCE_SPOT_TESTNET_WS_API_URL,
            max_size=MAX_ORDER_FRAME_BYTES,
            compression=None,
            open_timeout=timeout_seconds,
        )
        socket = await socket if inspect.isawaitable(socket) else socket
        await asyncio.wait_for(socket.send(request), timeout=timeout_seconds)
        payload = _decode_json_frame(
            await asyncio.wait_for(socket.recv(), timeout=timeout_seconds)
        )
        if payload.get("id") != request_id:
            raise BinanceTestnetOrderExecutionError(
                "ORDER_RESPONSE_ID_MISMATCH", "Yanıt request ID ile eşleşmiyor."
            )
        if payload.get("status") != 200:
            error = payload.get("error")
            venue_error_code = error.get("code") if isinstance(error, dict) else None
            if type(venue_error_code) is not int:
                venue_error_code = None
            raise OrderRejectedByVenue(
                "ORDER_REQUEST_REJECTED",
                "İstek venue tarafından reddedildi.",
                venue_error_code=venue_error_code,
            )
        result = payload.get("result")
        if not isinstance(result, dict):
            raise BinanceTestnetOrderExecutionError(
                "ORDER_RESPONSE_INVALID", "Yanıt result nesnesi geçersiz."
            )
        return decode(result)
    except BinanceTestnetOrderExecutionError:
        raise
    except (SignedRequestError, TimeoutError, OSError, ValueError, TypeError) as exc:
        raise BinanceTestnetOrderExecutionError(
            "ORDER_REQUEST_FAILED", "Signed order isteği tamamlanamadı."
        ) from exc
    except Exception as exc:
        raise BinanceTestnetOrderExecutionError(
            "ORDER_REQUEST_FAILED", "Signed order isteği tamamlanamadı."
        ) from exc
    finally:
        if socket is not None:
            try:
                await socket.close()
            except Exception:
                pass


def _decode_placed_order(result: dict[str, object]) -> PlacedTestnetOrder:
    symbol = result.get("symbol")
    order_id = result.get("orderId")
    client_order_id = result.get("clientOrderId")
    status = result.get("status")
    transact_time = result.get("transactTime")
    if (
        type(symbol) is not str
        or not symbol
        or type(order_id) is not int
        or order_id < 0
        or type(client_order_id) is not str
        or not client_order_id
        or type(status) is not str
        or not status
        or type(transact_time) is not int
        or transact_time < 0
    ):
        raise BinanceTestnetOrderExecutionError(
            "ORDER_PLACE_RESPONSE_INVALID", "Order place yanıt alanları geçersiz."
        )
    return PlacedTestnetOrder(symbol, order_id, client_order_id, status, transact_time)


def _decode_cancelled_order(result: dict[str, object]) -> CancelledTestnetOrder:
    symbol = result.get("symbol")
    order_id = result.get("orderId")
    client_order_id = result.get("clientOrderId") or result.get("origClientOrderId")
    status = result.get("status")
    if (
        type(symbol) is not str
        or not symbol
        or type(order_id) is not int
        or order_id < 0
        or type(client_order_id) is not str
        or not client_order_id
        or type(status) is not str
        or not status
    ):
        raise BinanceTestnetOrderExecutionError(
            "ORDER_CANCEL_RESPONSE_INVALID", "Order cancel yanıt alanları geçersiz."
        )
    return CancelledTestnetOrder(symbol, order_id, client_order_id, status)


def _decode_json_frame(raw_frame: str | bytes) -> dict[str, object]:
    if isinstance(raw_frame, bytes):
        frame_size = len(raw_frame)
        text = raw_frame.decode("utf-8")
    elif isinstance(raw_frame, str):
        text = raw_frame
        frame_size = len(raw_frame.encode("utf-8"))
    else:
        raise BinanceTestnetOrderExecutionError(
            "ORDER_FRAME_INVALID", "Frame metin veya bytes olmalıdır."
        )
    if frame_size > MAX_ORDER_FRAME_BYTES:
        raise BinanceTestnetOrderExecutionError("ORDER_FRAME_TOO_LARGE", "Frame byte sınırını aşıyor.")
    try:
        payload = json.loads(text)
    except (TypeError, ValueError) as exc:
        raise BinanceTestnetOrderExecutionError("ORDER_FRAME_INVALID", "JSON frame geçersiz.") from exc
    if not isinstance(payload, dict):
        raise BinanceTestnetOrderExecutionError("ORDER_FRAME_INVALID", "JSON nesne olmalıdır.")
    return payload
