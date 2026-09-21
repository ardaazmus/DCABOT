"""Bounded, HMAC-signed Binance Spot Testnet account read access."""

from dataclasses import dataclass
import hashlib
import json
import time
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from dcabot.application.credential_boundary import (
    AccountCapability,
    CapabilitySource,
    CredentialProvider,
)
from dcabot.application.signed_request import (
    ApiKeyType,
    Clock,
    DEFAULT_RECV_WINDOW_MS,
    HmacSha256Signer,
    SignedRequestError,
    build_signed_request,
)
from dcabot.domain.numbers import number


BINANCE_SPOT_TESTNET_REST_BASE_URL = "https://testnet.binance.vision/api"
BINANCE_SPOT_TESTNET_ACCOUNT_URL = f"{BINANCE_SPOT_TESTNET_REST_BASE_URL}/v3/account"
BINANCE_SPOT_TESTNET_OPEN_ORDERS_URL = f"{BINANCE_SPOT_TESTNET_REST_BASE_URL}/v3/openOrders"
BINANCE_SPOT_TESTNET_MY_TRADES_URL = f"{BINANCE_SPOT_TESTNET_REST_BASE_URL}/v3/myTrades"
MAX_ACCOUNT_RESPONSE_BYTES = 256 * 1024
MAX_OPEN_ORDERS_RESPONSE_BYTES = 256 * 1024
MAX_MY_TRADES_RESPONSE_BYTES = 256 * 1024
MAX_BALANCES = 5_000
MAX_NONZERO_BALANCES = 512
MAX_OPEN_ORDERS = 512
MAX_MY_TRADES = 512
MAX_PERMISSIONS = 32
DEFAULT_TIMEOUT_SECONDS = 5


class BinanceTestnetAccountError(RuntimeError):
    """Raised when a signed account read cannot safely be completed."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


class AccountResponse(Protocol):
    status: int
    headers: object

    def read(self, size: int = -1) -> bytes: ...

    def close(self) -> None: ...


class AccountOpener(Protocol):
    def open(self, request: Request, timeout: int) -> AccountResponse: ...


class SystemClock:
    def now_ms(self) -> int:
        return time.time_ns() // 1_000_000


@dataclass(frozen=True, slots=True)
class BinanceTestnetBalance:
    """One non-zero testnet asset balance; exact decimal strings, no real money."""

    asset: str
    free: str
    locked: str


@dataclass(frozen=True, slots=True, repr=False)
class BinanceTestnetAccountSnapshot:
    """Signed testnet account evidence. Balances are real Testnet-play-money
    amounts (never mainnet), included for display; credentials never are.
    """

    credential_id: str
    account_type: str
    can_trade: bool
    can_withdraw: bool
    can_deposit: bool
    permissions: tuple[str, ...]
    update_time_ms: int
    balances_count: int
    balances: tuple[BinanceTestnetBalance, ...]
    capability: AccountCapability
    response_sha256: str
    observed_at_us: int

    def __repr__(self) -> str:
        return (
            "BinanceTestnetAccountSnapshot("
            f"credential_id={self.credential_id!r}, account_type={self.account_type!r}, "
            f"permissions={self.permissions!r}, balances_count={self.balances_count}, "
            "<redacted>)"
        )


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, new):
        raise BinanceTestnetAccountError(
            "TESTNET_ACCOUNT_REDIRECT_REJECTED", "Hesap isteği yönlendirmesi reddedildi."
        )


def fetch_binance_testnet_account(
    credential_id: str,
    *,
    provider: CredentialProvider,
    clock: Clock | None = None,
    opener: AccountOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    recv_window_ms: int = DEFAULT_RECV_WINDOW_MS,
) -> BinanceTestnetAccountSnapshot:
    """Fetch signed account evidence; no order or mutation endpoint is reachable."""

    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30:
        raise BinanceTestnetAccountError(
            "TESTNET_ACCOUNT_TIMEOUT_INVALID", "Hesap isteği timeout değeri geçersiz."
        )
    try:
        material = provider.load(credential_id)
        if material.key_type is not ApiKeyType.HMAC:
            raise BinanceTestnetAccountError(
                "TESTNET_ACCOUNT_KEY_TYPE_UNSUPPORTED", "Yalnız HMAC account key destekleniyor."
            )
        signed = build_signed_request(
            (),
            clock=clock or SystemClock(),
            recv_window_ms=recv_window_ms,
            signer=HmacSha256Signer(material.secret),
        )
    except BinanceTestnetAccountError:
        raise
    except SignedRequestError as exc:
        raise BinanceTestnetAccountError(exc.code, "İmzalı hesap isteği hazırlanamadı.") from exc
    request = Request(
        f"{BINANCE_SPOT_TESTNET_ACCOUNT_URL}?{signed.query_string}",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "X-MBX-APIKEY": material.api_key,
        },
        method="GET",
    )
    response: AccountResponse | None = None
    try:
        response = (opener or build_opener(_NoRedirectHandler())).open(
            request, timeout=timeout_seconds
        )
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()  # type: ignore[attr-defined]
        if status != 200:
            raise BinanceTestnetAccountError(
                "TESTNET_ACCOUNT_HTTP_ERROR", "İmzalı hesap HTTP yanıtı başarılı değil."
            )
        payload_bytes = _read_bounded_response(response)
        payload = _decode_json(payload_bytes)
        return _normalize_account(payload, credential_id, payload_bytes)
    except BinanceTestnetAccountError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise BinanceTestnetAccountError(
            "TESTNET_ACCOUNT_UNAVAILABLE", "İmzalı Testnet hesap yanıtı alınamadı."
        ) from exc
    finally:
        if response is not None:
            response.close()


def _read_bounded_response(response: AccountResponse) -> bytes:
    headers = getattr(response, "headers", None)
    content_length = headers.get("Content-Length") if headers is not None else None
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except (TypeError, ValueError) as exc:
            raise BinanceTestnetAccountError(
                "TESTNET_ACCOUNT_RESPONSE_INVALID", "Hesap Content-Length geçersiz."
            ) from exc
        if declared_size < 0 or declared_size > MAX_ACCOUNT_RESPONSE_BYTES:
            raise BinanceTestnetAccountError(
                "TESTNET_ACCOUNT_RESPONSE_TOO_LARGE", "Hesap yanıt byte sınırını aşıyor."
            )
    encoding = headers.get("Content-Encoding") if headers is not None else None
    if encoding and encoding.lower() != "identity":
        raise BinanceTestnetAccountError(
            "TESTNET_ACCOUNT_ENCODING_INVALID", "Hesap yanıt sıkıştırma biçimi reddedildi."
        )
    payload = response.read(MAX_ACCOUNT_RESPONSE_BYTES + 1)
    if not isinstance(payload, bytes):
        raise BinanceTestnetAccountError(
            "TESTNET_ACCOUNT_RESPONSE_INVALID", "Hesap yanıt gövdesi bytes olmalıdır."
        )
    if len(payload) > MAX_ACCOUNT_RESPONSE_BYTES:
        raise BinanceTestnetAccountError(
            "TESTNET_ACCOUNT_RESPONSE_TOO_LARGE", "Hesap yanıt byte sınırını aşıyor."
        )
    return payload


def _decode_json(payload_bytes: bytes) -> dict[str, object]:
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BinanceTestnetAccountError(
            "TESTNET_ACCOUNT_RESPONSE_INVALID", "Hesap yanıtı JSON olarak okunamadı."
        ) from exc
    if type(payload) is not dict:
        raise BinanceTestnetAccountError(
            "TESTNET_ACCOUNT_RESPONSE_INVALID", "Hesap yanıtı nesne olmalıdır."
        )
    return payload


def _normalize_account(
    payload: dict[str, object], credential_id: str, payload_bytes: bytes
) -> BinanceTestnetAccountSnapshot:
    required = ("accountType", "canTrade", "canWithdraw", "canDeposit", "updateTime")
    if (
        type(payload.get("accountType")) is not str
        or type(payload.get("canTrade")) is not bool
        or type(payload.get("canWithdraw")) is not bool
        or type(payload.get("canDeposit")) is not bool
        or type(payload.get("updateTime")) is not int
        or payload["updateTime"] < 0
        or any(field not in payload for field in required)
    ):
        raise BinanceTestnetAccountError(
            "TESTNET_ACCOUNT_RESPONSE_INVALID", "Hesap temel alanları geçersiz."
        )
    permissions = _string_tuple(payload.get("permissions"), "permissions", MAX_PERMISSIONS)
    balances = payload.get("balances")
    if type(balances) is not list or len(balances) > MAX_BALANCES:
        raise BinanceTestnetAccountError(
            "TESTNET_ACCOUNT_RESPONSE_INVALID", "Hesap balances alanı geçersiz."
        )
    nonzero_balances: list[BinanceTestnetBalance] = []
    for balance in balances:
        if type(balance) is not dict or set(balance) != {"asset", "free", "locked"}:
            raise BinanceTestnetAccountError(
                "TESTNET_ACCOUNT_RESPONSE_INVALID", "Hesap balance öğesi geçersiz."
            )
        if any(
            type(balance[field]) is not str
            or not balance[field]
            or len(balance[field]) > 128
            or any(ord(char) < 0x20 or ord(char) == 0x7F for char in balance[field])
            for field in ("asset", "free", "locked")
        ):
            raise BinanceTestnetAccountError(
                "TESTNET_ACCOUNT_RESPONSE_INVALID", "Hesap balance metni geçersiz."
            )
        asset = balance["asset"]
        if not 1 <= len(asset) <= 32:
            raise BinanceTestnetAccountError(
                "TESTNET_ACCOUNT_RESPONSE_INVALID", "Hesap balance asset alanı geçersiz."
            )
        try:
            # Binance pads to a fixed 8 decimals (e.g. "100.00000000"), which
            # is valid but not this project's own trimmed canonical form; only
            # parseability and sign are validated, the venue's own text is kept.
            free_value = number(balance["free"])
            locked_value = number(balance["locked"])
        except ValueError as exc:
            raise BinanceTestnetAccountError(
                "TESTNET_ACCOUNT_RESPONSE_INVALID", "Hesap balance miktarı exact decimal olmalıdır."
            ) from exc
        if free_value < 0 or locked_value < 0:
            raise BinanceTestnetAccountError(
                "TESTNET_ACCOUNT_RESPONSE_INVALID", "Hesap balance miktarı negatif olamaz."
            )
        if free_value != 0 or locked_value != 0:
            if len(nonzero_balances) >= MAX_NONZERO_BALANCES:
                raise BinanceTestnetAccountError(
                    "TESTNET_ACCOUNT_RESPONSE_TOO_LARGE", "Hesap sıfır olmayan balance sınırı aşıyor."
                )
            nonzero_balances.append(BinanceTestnetBalance(asset, balance["free"], balance["locked"]))
    can_trade = payload["canTrade"]
    trade_scope_verified = "SPOT" in permissions
    return BinanceTestnetAccountSnapshot(
        credential_id=credential_id,
        account_type=payload["accountType"],
        can_trade=can_trade,
        can_withdraw=payload["canWithdraw"],
        can_deposit=payload["canDeposit"],
        permissions=permissions,
        update_time_ms=payload["updateTime"],
        balances_count=len(balances),
        balances=tuple(nonzero_balances),
        capability=AccountCapability.from_evidence(
            source=CapabilitySource.SIGNED_ACCOUNT_CONTEXT,
            signed_request_verified=True,
            can_trade=can_trade,
            trade_scope_verified=trade_scope_verified,
        ),
        response_sha256=hashlib.sha256(payload_bytes).hexdigest(),
        observed_at_us=time.time_ns() // 1000,
    )


@dataclass(frozen=True, slots=True)
class BinanceTestnetOpenOrder:
    """One redacted open order snapshot; venue's own report, not a fill claim."""

    symbol: str
    order_id: int
    client_order_id: str
    side: str
    type: str
    status: str
    price: str
    orig_qty: str
    executed_qty: str
    time_ms: int
    update_time_ms: int


def fetch_binance_testnet_open_orders(
    credential_id: str,
    *,
    provider: CredentialProvider,
    clock: Clock | None = None,
    opener: AccountOpener | None = None,
    symbol: str | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    recv_window_ms: int = DEFAULT_RECV_WINDOW_MS,
) -> tuple[BinanceTestnetOpenOrder, ...]:
    """Fetch the account's current open orders; no order/cancel endpoint is reachable."""

    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30:
        raise BinanceTestnetAccountError(
            "TESTNET_OPEN_ORDERS_TIMEOUT_INVALID", "Açık emir isteği timeout değeri geçersiz."
        )
    if symbol is not None and (
        not isinstance(symbol, str)
        or not 1 <= len(symbol) <= 32
        or symbol != symbol.strip()
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in symbol)
    ):
        raise BinanceTestnetAccountError(
            "TESTNET_OPEN_ORDERS_SYMBOL_INVALID", "Açık emir symbol değeri geçersiz."
        )
    try:
        material = provider.load(credential_id)
        if material.key_type is not ApiKeyType.HMAC:
            raise BinanceTestnetAccountError(
                "TESTNET_OPEN_ORDERS_KEY_TYPE_UNSUPPORTED", "Yalnız HMAC key destekleniyor."
            )
        signed = build_signed_request(
            (("symbol", symbol),) if symbol is not None else (),
            clock=clock or SystemClock(),
            recv_window_ms=recv_window_ms,
            signer=HmacSha256Signer(material.secret),
        )
    except BinanceTestnetAccountError:
        raise
    except SignedRequestError as exc:
        raise BinanceTestnetAccountError(exc.code, "İmzalı açık emir isteği hazırlanamadı.") from exc
    request = Request(
        f"{BINANCE_SPOT_TESTNET_OPEN_ORDERS_URL}?{signed.query_string}",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "X-MBX-APIKEY": material.api_key,
        },
        method="GET",
    )
    response: AccountResponse | None = None
    try:
        response = (opener or build_opener(_NoRedirectHandler())).open(
            request, timeout=timeout_seconds
        )
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()  # type: ignore[attr-defined]
        if status != 200:
            raise BinanceTestnetAccountError(
                "TESTNET_OPEN_ORDERS_HTTP_ERROR", "İmzalı açık emir HTTP yanıtı başarılı değil."
            )
        payload_bytes = _read_bounded_open_orders_response(response)
        payload = _decode_open_orders_json(payload_bytes)
        return _normalize_open_orders(payload)
    except BinanceTestnetAccountError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise BinanceTestnetAccountError(
            "TESTNET_OPEN_ORDERS_UNAVAILABLE", "İmzalı açık emir yanıtı alınamadı."
        ) from exc
    finally:
        if response is not None:
            response.close()


def _read_bounded_open_orders_response(response: AccountResponse) -> bytes:
    headers = getattr(response, "headers", None)
    content_length = headers.get("Content-Length") if headers is not None else None
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except (TypeError, ValueError) as exc:
            raise BinanceTestnetAccountError(
                "TESTNET_OPEN_ORDERS_RESPONSE_INVALID", "Açık emir Content-Length geçersiz."
            ) from exc
        if declared_size < 0 or declared_size > MAX_OPEN_ORDERS_RESPONSE_BYTES:
            raise BinanceTestnetAccountError(
                "TESTNET_OPEN_ORDERS_RESPONSE_TOO_LARGE", "Açık emir yanıt byte sınırını aşıyor."
            )
    encoding = headers.get("Content-Encoding") if headers is not None else None
    if encoding and encoding.lower() != "identity":
        raise BinanceTestnetAccountError(
            "TESTNET_OPEN_ORDERS_ENCODING_INVALID", "Açık emir yanıt sıkıştırma biçimi reddedildi."
        )
    payload = response.read(MAX_OPEN_ORDERS_RESPONSE_BYTES + 1)
    if not isinstance(payload, bytes):
        raise BinanceTestnetAccountError(
            "TESTNET_OPEN_ORDERS_RESPONSE_INVALID", "Açık emir yanıt gövdesi bytes olmalıdır."
        )
    if len(payload) > MAX_OPEN_ORDERS_RESPONSE_BYTES:
        raise BinanceTestnetAccountError(
            "TESTNET_OPEN_ORDERS_RESPONSE_TOO_LARGE", "Açık emir yanıt byte sınırını aşıyor."
        )
    return payload


def _decode_open_orders_json(payload_bytes: bytes) -> list[object]:
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BinanceTestnetAccountError(
            "TESTNET_OPEN_ORDERS_RESPONSE_INVALID", "Açık emir yanıtı JSON olarak okunamadı."
        ) from exc
    if type(payload) is not list or len(payload) > MAX_OPEN_ORDERS:
        raise BinanceTestnetAccountError(
            "TESTNET_OPEN_ORDERS_RESPONSE_INVALID", "Açık emir yanıtı bounded liste olmalıdır."
        )
    return payload


def _normalize_open_orders(payload: list[object]) -> tuple[BinanceTestnetOpenOrder, ...]:
    orders: list[BinanceTestnetOpenOrder] = []
    for item in payload:
        if type(item) is not dict:
            raise BinanceTestnetAccountError(
                "TESTNET_OPEN_ORDERS_RESPONSE_INVALID", "Açık emir öğesi nesne olmalıdır."
            )
        for text_field, limit in (
            ("symbol", 32),
            ("clientOrderId", 128),
            ("side", 8),
            ("type", 32),
            ("status", 32),
            ("price", 128),
            ("origQty", 128),
            ("executedQty", 128),
        ):
            value = item.get(text_field)
            if (
                type(value) is not str
                or not value
                or len(value) > limit
                or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
            ):
                raise BinanceTestnetAccountError(
                    "TESTNET_OPEN_ORDERS_RESPONSE_INVALID", f"Açık emir {text_field} alanı geçersiz."
                )
        for int_field in ("orderId", "time", "updateTime"):
            value = item.get(int_field)
            if type(value) is not int or value < 0:
                raise BinanceTestnetAccountError(
                    "TESTNET_OPEN_ORDERS_RESPONSE_INVALID", f"Açık emir {int_field} alanı geçersiz."
                )
        try:
            price = number(item["price"])
            orig_qty = number(item["origQty"])
            executed_qty = number(item["executedQty"])
        except ValueError as exc:
            raise BinanceTestnetAccountError(
                "TESTNET_OPEN_ORDERS_RESPONSE_INVALID", "Açık emir miktarı exact decimal olmalıdır."
            ) from exc
        if price < 0 or orig_qty < 0 or executed_qty < 0:
            raise BinanceTestnetAccountError(
                "TESTNET_OPEN_ORDERS_RESPONSE_INVALID", "Açık emir miktarı negatif olamaz."
            )
        orders.append(
            BinanceTestnetOpenOrder(
                symbol=item["symbol"],
                order_id=item["orderId"],
                client_order_id=item["clientOrderId"],
                side=item["side"],
                type=item["type"],
                status=item["status"],
                price=item["price"],
                orig_qty=item["origQty"],
                executed_qty=item["executedQty"],
                time_ms=item["time"],
                update_time_ms=item["updateTime"],
            )
        )
    return tuple(orders)


@dataclass(frozen=True, slots=True)
class BinanceTestnetTrade:
    """One redacted real fill; the only source of exact fill price/qty/fee."""

    trade_id: int
    order_id: int
    symbol: str
    price: str
    qty: str
    commission: str
    commission_asset: str
    is_buyer: bool
    time_ms: int


def fetch_binance_testnet_my_trades(
    credential_id: str,
    symbol: str,
    *,
    order_id: int,
    provider: CredentialProvider,
    clock: Clock | None = None,
    opener: AccountOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    recv_window_ms: int = DEFAULT_RECV_WINDOW_MS,
) -> tuple[BinanceTestnetTrade, ...]:
    """Fetch the exact real fills for one order -- price/qty/fee never come
    from anywhere else (order-status only gives cumulative totals).
    """

    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30:
        raise BinanceTestnetAccountError(
            "TESTNET_MY_TRADES_TIMEOUT_INVALID", "Trade isteği timeout değeri geçersiz."
        )
    if (
        not isinstance(symbol, str)
        or not 1 <= len(symbol) <= 32
        or symbol != symbol.strip()
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in symbol)
    ):
        raise BinanceTestnetAccountError(
            "TESTNET_MY_TRADES_SYMBOL_INVALID", "Trade symbol değeri geçersiz."
        )
    if type(order_id) is not int or order_id < 0:
        raise BinanceTestnetAccountError(
            "TESTNET_MY_TRADES_ORDER_ID_INVALID", "Trade order ID değeri geçersiz."
        )
    try:
        material = provider.load(credential_id)
        if material.key_type is not ApiKeyType.HMAC:
            raise BinanceTestnetAccountError(
                "TESTNET_MY_TRADES_KEY_TYPE_UNSUPPORTED", "Yalnız HMAC key destekleniyor."
            )
        signed = build_signed_request(
            (("symbol", symbol), ("orderId", str(order_id))),
            clock=clock or SystemClock(),
            recv_window_ms=recv_window_ms,
            signer=HmacSha256Signer(material.secret),
        )
    except BinanceTestnetAccountError:
        raise
    except SignedRequestError as exc:
        raise BinanceTestnetAccountError(exc.code, "İmzalı trade isteği hazırlanamadı.") from exc
    request = Request(
        f"{BINANCE_SPOT_TESTNET_MY_TRADES_URL}?{signed.query_string}",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "X-MBX-APIKEY": material.api_key,
        },
        method="GET",
    )
    response: AccountResponse | None = None
    try:
        response = (opener or build_opener(_NoRedirectHandler())).open(
            request, timeout=timeout_seconds
        )
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()  # type: ignore[attr-defined]
        if status != 200:
            raise BinanceTestnetAccountError(
                "TESTNET_MY_TRADES_HTTP_ERROR", "İmzalı trade HTTP yanıtı başarılı değil."
            )
        headers = getattr(response, "headers", None)
        content_length = headers.get("Content-Length") if headers is not None else None
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except (TypeError, ValueError) as exc:
                raise BinanceTestnetAccountError(
                    "TESTNET_MY_TRADES_RESPONSE_INVALID", "Trade Content-Length geçersiz."
                ) from exc
            if declared_size < 0 or declared_size > MAX_MY_TRADES_RESPONSE_BYTES:
                raise BinanceTestnetAccountError(
                    "TESTNET_MY_TRADES_RESPONSE_TOO_LARGE", "Trade yanıt byte sınırını aşıyor."
                )
        encoding = headers.get("Content-Encoding") if headers is not None else None
        if encoding and encoding.lower() != "identity":
            raise BinanceTestnetAccountError(
                "TESTNET_MY_TRADES_ENCODING_INVALID", "Trade yanıt sıkıştırma biçimi reddedildi."
            )
        payload_bytes = response.read(MAX_MY_TRADES_RESPONSE_BYTES + 1)
        if not isinstance(payload_bytes, bytes) or len(payload_bytes) > MAX_MY_TRADES_RESPONSE_BYTES:
            raise BinanceTestnetAccountError(
                "TESTNET_MY_TRADES_RESPONSE_TOO_LARGE", "Trade yanıt byte sınırını aşıyor."
            )
        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BinanceTestnetAccountError(
                "TESTNET_MY_TRADES_RESPONSE_INVALID", "Trade yanıtı JSON olarak okunamadı."
            ) from exc
        if type(payload) is not list or len(payload) > MAX_MY_TRADES:
            raise BinanceTestnetAccountError(
                "TESTNET_MY_TRADES_RESPONSE_INVALID", "Trade yanıtı bounded liste olmalıdır."
            )
        return _normalize_trades(payload, symbol)
    except BinanceTestnetAccountError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise BinanceTestnetAccountError(
            "TESTNET_MY_TRADES_UNAVAILABLE", "İmzalı trade yanıtı alınamadı."
        ) from exc
    finally:
        if response is not None:
            response.close()


def _normalize_trades(payload: list[object], symbol: str) -> tuple[BinanceTestnetTrade, ...]:
    trades: list[BinanceTestnetTrade] = []
    for item in payload:
        if type(item) is not dict:
            raise BinanceTestnetAccountError(
                "TESTNET_MY_TRADES_RESPONSE_INVALID", "Trade öğesi nesne olmalıdır."
            )
        for text_field, limit in (
            ("symbol", 32),
            ("price", 128),
            ("qty", 128),
            ("commission", 128),
            ("commissionAsset", 32),
        ):
            value = item.get(text_field)
            if (
                type(value) is not str
                or not value
                or len(value) > limit
                or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
            ):
                raise BinanceTestnetAccountError(
                    "TESTNET_MY_TRADES_RESPONSE_INVALID", f"Trade {text_field} alanı geçersiz."
                )
        if item["symbol"] != symbol:
            raise BinanceTestnetAccountError(
                "TESTNET_MY_TRADES_RESPONSE_INVALID", "Trade symbol kimliği doğrulanamadı."
            )
        for int_field in ("id", "orderId", "time"):
            value = item.get(int_field)
            if type(value) is not int or value < 0:
                raise BinanceTestnetAccountError(
                    "TESTNET_MY_TRADES_RESPONSE_INVALID", f"Trade {int_field} alanı geçersiz."
                )
        is_buyer = item.get("isBuyer")
        if type(is_buyer) is not bool:
            raise BinanceTestnetAccountError(
                "TESTNET_MY_TRADES_RESPONSE_INVALID", "Trade isBuyer alanı geçersiz."
            )
        try:
            price = number(item["price"])
            qty = number(item["qty"])
            commission = number(item["commission"])
        except ValueError as exc:
            raise BinanceTestnetAccountError(
                "TESTNET_MY_TRADES_RESPONSE_INVALID", "Trade miktarı exact decimal olmalıdır."
            ) from exc
        if price < 0 or qty < 0 or commission < 0:
            raise BinanceTestnetAccountError(
                "TESTNET_MY_TRADES_RESPONSE_INVALID", "Trade miktarı negatif olamaz."
            )
        trades.append(
            BinanceTestnetTrade(
                trade_id=item["id"],
                order_id=item["orderId"],
                symbol=item["symbol"],
                price=item["price"],
                qty=item["qty"],
                commission=item["commission"],
                commission_asset=item["commissionAsset"],
                is_buyer=is_buyer,
                time_ms=item["time"],
            )
        )
    return tuple(trades)


def _string_tuple(raw: object, field_name: str, limit: int) -> tuple[str, ...]:
    if type(raw) is not list or len(raw) > limit or any(
        type(item) is not str
        or not item
        or len(item) > 64
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in item)
        for item in raw
    ):
        raise BinanceTestnetAccountError(
            "TESTNET_ACCOUNT_RESPONSE_INVALID", f"Hesap {field_name} alanı geçersiz."
        )
    return tuple(raw)
