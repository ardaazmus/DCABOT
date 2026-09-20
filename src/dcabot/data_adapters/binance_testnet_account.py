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


BINANCE_SPOT_TESTNET_REST_BASE_URL = "https://testnet.binance.vision/api"
BINANCE_SPOT_TESTNET_ACCOUNT_URL = f"{BINANCE_SPOT_TESTNET_REST_BASE_URL}/v3/account"
MAX_ACCOUNT_RESPONSE_BYTES = 256 * 1024
MAX_BALANCES = 5_000
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


@dataclass(frozen=True, slots=True, repr=False)
class BinanceTestnetAccountSnapshot:
    """Ephemeral signed account evidence without balance values or credentials."""

    credential_id: str
    account_type: str
    can_trade: bool
    can_withdraw: bool
    can_deposit: bool
    permissions: tuple[str, ...]
    update_time_ms: int
    balances_count: int
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
        capability=AccountCapability.from_evidence(
            source=CapabilitySource.SIGNED_ACCOUNT_CONTEXT,
            signed_request_verified=True,
            can_trade=can_trade,
            trade_scope_verified=trade_scope_verified,
        ),
        response_sha256=hashlib.sha256(payload_bytes).hexdigest(),
        observed_at_us=time.time_ns() // 1000,
    )


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
