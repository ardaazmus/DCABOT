"""Bounded, read-only Binance Spot Testnet User Data Stream adapter."""

import asyncio
from dataclasses import dataclass
import inspect
import json
import re
from typing import Awaitable, Callable, Protocol
from uuid import uuid4

from websockets.asyncio.client import connect

from dcabot.application.credential_boundary import CredentialProvider
from dcabot.application.order_list_contract import (
    OrderListError,
    UserDataOrderListEvent,
    UserDataOrderListLeg,
)
from dcabot.application.reconciliation import OrderLookup, UserDataEvent
from dcabot.application.signed_request import (
    ApiKeyType,
    Clock,
    DEFAULT_RECV_WINDOW_MS,
    HmacSha256Signer,
    SignedRequestError,
    build_signed_ws_api_params,
    build_signed_user_stream_params,
)


BINANCE_SPOT_TESTNET_WS_API_URL = "wss://ws-api.testnet.binance.vision/ws-api/v3"
MAX_USER_STREAM_FRAME_BYTES = 256 * 1024
DEFAULT_USER_STREAM_TIMEOUT_SECONDS = 5
_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,128}\Z", re.ASCII)


class BinanceTestnetUserStreamError(RuntimeError):
    """Raised when the read-only User Data Stream boundary fails closed."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


class UserDataSocket(Protocol):
    async def send(self, message: str) -> None: ...

    async def recv(self) -> str | bytes: ...

    async def close(self) -> None: ...


WebSocketFactory = Callable[..., Awaitable[UserDataSocket] | UserDataSocket]


@dataclass(frozen=True, slots=True)
class UserStreamSubscription:
    """Redacted subscription identity returned by the venue."""

    request_id: str
    subscription_id: int


class BinanceTestnetUserDataStream:
    """Open one bounded read-only subscription; reconnect is deliberately absent."""

    __slots__ = (
        "_credential_id",
        "_provider",
        "_clock",
        "_websocket_factory",
        "_request_id_factory",
        "_timeout_seconds",
        "_socket",
        "_subscription",
    )

    def __init__(
        self,
        credential_id: str,
        *,
        provider: CredentialProvider,
        clock: Clock,
        websocket_factory: WebSocketFactory = connect,
        request_id_factory: Callable[[], str] = lambda: str(uuid4()),
        timeout_seconds: int = DEFAULT_USER_STREAM_TIMEOUT_SECONDS,
    ) -> None:
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 30:
            raise BinanceTestnetUserStreamError(
                "USER_STREAM_TIMEOUT_INVALID", "User Stream timeout değeri geçersiz."
            )
        self._credential_id = credential_id
        self._provider = provider
        self._clock = clock
        self._websocket_factory = websocket_factory
        self._request_id_factory = request_id_factory
        self._timeout_seconds = timeout_seconds
        self._socket: UserDataSocket | None = None
        self._subscription: UserStreamSubscription | None = None

    async def connect(self) -> UserStreamSubscription:
        """Connect and subscribe without exposing any mutation operation."""

        if self._socket is not None:
            raise BinanceTestnetUserStreamError(
                "USER_STREAM_ALREADY_CONNECTED", "User Stream zaten bağlı."
            )
        try:
            material = self._provider.load(self._credential_id)
            if material.key_type is not ApiKeyType.HMAC:
                raise BinanceTestnetUserStreamError(
                    "USER_STREAM_KEY_TYPE_UNSUPPORTED", "Yalnız HMAC User Stream destekleniyor."
                )
            request_id = self._request_id_factory()
            if not isinstance(request_id, str) or _IDENTIFIER.fullmatch(request_id) is None:
                raise BinanceTestnetUserStreamError(
                    "USER_STREAM_REQUEST_ID_INVALID", "User Stream request ID geçersiz."
                )
            params = build_signed_user_stream_params(
                material.api_key,
                clock=self._clock,
                recv_window_ms=DEFAULT_RECV_WINDOW_MS,
                signer=HmacSha256Signer(material.secret),
            )
            request = json.dumps(
                {
                    "id": request_id,
                    "method": "userDataStream.subscribe.signature",
                    "params": params,
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            socket = self._websocket_factory(
                BINANCE_SPOT_TESTNET_WS_API_URL,
                max_size=MAX_USER_STREAM_FRAME_BYTES,
                compression=None,
                open_timeout=self._timeout_seconds,
            )
            socket = await socket if inspect.isawaitable(socket) else socket
            self._socket = socket
            await asyncio.wait_for(socket.send(request), timeout=self._timeout_seconds)
            raw_response = await asyncio.wait_for(socket.recv(), timeout=self._timeout_seconds)
            subscription = _decode_subscription_response(raw_response, request_id)
            self._subscription = subscription
            return subscription
        except BinanceTestnetUserStreamError:
            await self.close()
            raise
        except (SignedRequestError, TimeoutError, OSError, ValueError) as exc:
            await self.close()
            raise BinanceTestnetUserStreamError(
                "USER_STREAM_CONNECT_FAILED", "Read-only User Stream bağlantısı kurulamadı."
            ) from exc
        except Exception as exc:
            await self.close()
            raise BinanceTestnetUserStreamError(
                "USER_STREAM_CONNECT_FAILED", "Read-only User Stream bağlantısı kurulamadı."
            ) from exc

    async def recv_execution_report(self) -> UserDataEvent:
        """Decode one bounded execution report into redacted event identity."""

        if self._socket is None or self._subscription is None:
            raise BinanceTestnetUserStreamError(
                "USER_STREAM_NOT_CONNECTED", "Önce read-only User Stream bağlantısı kurulmalıdır."
            )
        try:
            raw_frame = await asyncio.wait_for(
                self._socket.recv(), timeout=self._timeout_seconds
            )
            payload = _decode_json_frame(raw_frame)
            if payload.get("subscriptionId") != self._subscription.subscription_id:
                raise BinanceTestnetUserStreamError(
                    "USER_STREAM_SUBSCRIPTION_MISMATCH", "User Stream subscription kimliği eşleşmiyor."
                )
            event = payload.get("event")
            if not isinstance(event, dict) or event.get("e") != "executionReport":
                raise BinanceTestnetUserStreamError(
                    "USER_STREAM_EVENT_UNSUPPORTED", "Bu dilimde yalnız executionReport destekleniyor."
                )
            event_time_ms = _nonnegative_int(event.get("E"), "USER_STREAM_EVENT_INVALID")
            order_id = _nonnegative_int(event.get("i"), "USER_STREAM_EVENT_INVALID")
            execution_id = _nonnegative_int(event.get("I"), "USER_STREAM_EVENT_INVALID")
            return UserDataEvent.create(
                f"execution:{order_id}:{execution_id}",
                event_time_ms,
                "executionReport",
                order_id,
            )
        except BinanceTestnetUserStreamError:
            await self.close()
            raise
        except (TimeoutError, OSError, ValueError, TypeError) as exc:
            await self.close()
            raise BinanceTestnetUserStreamError(
                "USER_STREAM_EVENT_INVALID", "User Stream olayı güvenli biçimde çözümlenemedi."
            ) from exc

    async def recv_order_list_event(self) -> UserDataOrderListEvent:
        """Decode one bounded listStatus event without inferring leg status."""

        if self._socket is None or self._subscription is None:
            raise BinanceTestnetUserStreamError(
                "USER_STREAM_NOT_CONNECTED", "Önce read-only User Stream bağlantısı kurulmalıdır."
            )
        try:
            raw_frame = await asyncio.wait_for(
                self._socket.recv(), timeout=self._timeout_seconds
            )
            payload = _decode_json_frame(raw_frame)
            if payload.get("subscriptionId") != self._subscription.subscription_id:
                raise BinanceTestnetUserStreamError(
                    "USER_STREAM_SUBSCRIPTION_MISMATCH", "User Stream subscription kimliği eşleşmiyor."
                )
            event = payload.get("event")
            if not isinstance(event, dict) or event.get("e") != "listStatus":
                raise BinanceTestnetUserStreamError(
                    "USER_STREAM_EVENT_UNSUPPORTED", "Bu dilimde yalnız listStatus destekleniyor."
                )
            return _decode_order_list_event(event)
        except BinanceTestnetUserStreamError:
            await self.close()
            raise
        except (TimeoutError, OSError, ValueError, TypeError) as exc:
            await self.close()
            raise BinanceTestnetUserStreamError(
                "USER_STREAM_EVENT_INVALID", "User Stream listStatus olayı güvenli biçimde çözülemedi."
            ) from exc

    async def close(self) -> None:
        """Close the socket without sending unsubscribe or mutation commands."""

        socket, self._socket = self._socket, None
        self._subscription = None
        if socket is not None:
            try:
                await socket.close()
            except Exception:
                pass


async def query_binance_testnet_order_status(
    credential_id: str,
    symbol: str,
    venue_order_id: int,
    *,
    provider: CredentialProvider,
    clock: Clock,
    websocket_factory: WebSocketFactory = connect,
    request_id_factory: Callable[[], str] = lambda: str(uuid4()),
    timeout_seconds: int = DEFAULT_USER_STREAM_TIMEOUT_SECONDS,
) -> OrderLookup:
    """Query one order through a separate signed, read-only WebSocket call."""

    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 30:
        raise BinanceTestnetUserStreamError(
            "ORDER_STATUS_TIMEOUT_INVALID", "Order status timeout değeri geçersiz."
        )
    if (
        not isinstance(symbol, str)
        or not 1 <= len(symbol) <= 32
        or symbol != symbol.strip()
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in symbol)
    ):
        raise BinanceTestnetUserStreamError(
            "ORDER_STATUS_SYMBOL_INVALID", "Order status symbol değeri geçersiz."
        )
    if type(venue_order_id) is not int or venue_order_id < 0:
        raise BinanceTestnetUserStreamError(
            "ORDER_STATUS_ORDER_ID_INVALID", "Order status order ID değeri geçersiz."
        )
    socket: UserDataSocket | None = None
    try:
        material = provider.load(credential_id)
        if material.key_type is not ApiKeyType.HMAC:
            raise BinanceTestnetUserStreamError(
                "ORDER_STATUS_KEY_TYPE_UNSUPPORTED", "Yalnız HMAC order status destekleniyor."
            )
        request_id = request_id_factory()
        if not isinstance(request_id, str) or _IDENTIFIER.fullmatch(request_id) is None:
            raise BinanceTestnetUserStreamError(
                "ORDER_STATUS_REQUEST_ID_INVALID", "Order status request ID geçersiz."
            )
        params = build_signed_ws_api_params(
            material.api_key,
            (("orderId", venue_order_id), ("symbol", symbol)),
            clock=clock,
            recv_window_ms=DEFAULT_RECV_WINDOW_MS,
            signer=HmacSha256Signer(material.secret),
        )
        request = json.dumps(
            {"id": request_id, "method": "order.status", "params": params},
            ensure_ascii=True,
            separators=(",", ":"),
        )
        socket = websocket_factory(
            BINANCE_SPOT_TESTNET_WS_API_URL,
            max_size=MAX_USER_STREAM_FRAME_BYTES,
            compression=None,
            open_timeout=timeout_seconds,
        )
        socket = await socket if inspect.isawaitable(socket) else socket
        await asyncio.wait_for(socket.send(request), timeout=timeout_seconds)
        payload = _decode_json_frame(
            await asyncio.wait_for(socket.recv(), timeout=timeout_seconds)
        )
        if payload.get("id") != request_id:
            raise BinanceTestnetUserStreamError(
                "ORDER_STATUS_RESPONSE_ID_MISMATCH", "Order status yanıt ID eşleşmesi başarısız."
            )
        if payload.get("status") != 200:
            raise BinanceTestnetUserStreamError(
                "ORDER_STATUS_QUERY_REJECTED", "Order status sorgusu venue tarafından reddedildi."
            )
        result = payload.get("result")
        if (
            not isinstance(result, dict)
            or result.get("symbol") != symbol
            or result.get("orderId") != venue_order_id
        ):
            raise BinanceTestnetUserStreamError(
                "ORDER_STATUS_RESPONSE_INVALID", "Order status kimliği doğrulanamadı."
            )
        return OrderLookup.found(venue_order_id)
    except BinanceTestnetUserStreamError:
        raise
    except (SignedRequestError, TimeoutError, OSError, ValueError, TypeError) as exc:
        raise BinanceTestnetUserStreamError(
            "ORDER_STATUS_QUERY_FAILED", "Read-only order status sorgusu tamamlanamadı."
        ) from exc
    except Exception as exc:
        raise BinanceTestnetUserStreamError(
            "ORDER_STATUS_QUERY_FAILED", "Read-only order status sorgusu tamamlanamadı."
        ) from exc
    finally:
        if socket is not None:
            try:
                await socket.close()
            except Exception:
                pass


def _decode_subscription_response(raw_frame: str | bytes, request_id: str) -> UserStreamSubscription:
    payload = _decode_json_frame(raw_frame)
    if payload.get("id") != request_id:
        raise BinanceTestnetUserStreamError(
            "USER_STREAM_RESPONSE_ID_MISMATCH", "User Stream abonelik yanıtı request ID ile eşleşmiyor."
        )
    if payload.get("status") != 200:
        raise BinanceTestnetUserStreamError(
            "USER_STREAM_SUBSCRIPTION_REJECTED", "User Stream aboneliği venue tarafından reddedildi."
        )
    result = payload.get("result")
    if not isinstance(result, dict):
        raise BinanceTestnetUserStreamError(
            "USER_STREAM_RESPONSE_INVALID", "User Stream abonelik sonucu geçersiz."
        )
    subscription_id = _nonnegative_int(result.get("subscriptionId"), "USER_STREAM_RESPONSE_INVALID")
    return UserStreamSubscription(request_id, subscription_id)


def _decode_json_frame(raw_frame: str | bytes) -> dict[str, object]:
    if isinstance(raw_frame, bytes):
        frame_size = len(raw_frame)
        text = raw_frame.decode("utf-8")
    elif isinstance(raw_frame, str):
        text = raw_frame
        frame_size = len(raw_frame.encode("utf-8"))
    else:
        raise BinanceTestnetUserStreamError(
            "USER_STREAM_FRAME_INVALID", "User Stream frame metin veya bytes olmalıdır."
        )
    if frame_size > MAX_USER_STREAM_FRAME_BYTES:
        raise BinanceTestnetUserStreamError(
            "USER_STREAM_FRAME_TOO_LARGE", "User Stream frame byte sınırını aşıyor."
        )
    try:
        payload = json.loads(text)
    except (TypeError, ValueError) as exc:
        raise BinanceTestnetUserStreamError(
            "USER_STREAM_FRAME_INVALID", "User Stream JSON frame geçersiz."
        ) from exc
    if not isinstance(payload, dict):
        raise BinanceTestnetUserStreamError(
            "USER_STREAM_FRAME_INVALID", "User Stream JSON nesne olmalıdır."
        )
    return payload


def _nonnegative_int(value: object, code: str) -> int:
    if type(value) is not int or value < 0:
        raise BinanceTestnetUserStreamError(code, "User Stream integer alanı geçersiz.")
    return value


def _decode_order_list_event(event: dict[str, object]) -> UserDataOrderListEvent:
    try:
        raw_orders = event["O"]
        if type(raw_orders) is not list:
            raise TypeError("orders must be a list")
        orders = tuple(
            UserDataOrderListLeg(
                symbol=order["s"],
                order_id=order["i"],
                client_order_id=order["c"],
            )
            for order in raw_orders
        )
        if len(orders) != 2:
            raise ValueError("OCO listStatus must contain two orders")
        return UserDataOrderListEvent(
            event_id=f"list:{event['g']}:{event['T']}:{event['E']}",
            event_time_ms=event["E"],
            transaction_time_ms=event["T"],
            symbol=event["s"],
            order_list_id=event["g"],
            contingency_type=event["c"],
            list_status=event["l"],
            list_order_status=event["L"],
            list_client_order_id=event["C"],
            orders=orders,
        )
    except BinanceTestnetUserStreamError:
        raise
    except (KeyError, TypeError, ValueError, OrderListError) as exc:
        raise BinanceTestnetUserStreamError(
            "USER_STREAM_ORDER_LIST_INVALID", "listStatus payload kimliği doğrulanamadı."
        ) from exc


def _validate_identifier(value: object, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise BinanceTestnetUserStreamError(code, "Kimlik bounded ASCII metin olmalıdır.")


def _validate_symbol(value: object, code: str) -> None:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 32
        or value != value.strip()
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
    ):
        raise BinanceTestnetUserStreamError(code, "Symbol bounded metin olmalıdır.")


def _positive_int(value: object, code: str) -> None:
    if type(value) is not int or value <= 0:
        raise BinanceTestnetUserStreamError(code, "Pozitif integer bekleniyor.")
