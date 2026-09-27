"""Bounded, HMAC-signed Binance USDS-M Futures Testnet position-risk read
access (Faz 17 D.1).

RG-02 correction (binding, 2026-09-21/22): the endpoint is
``/fapi/v3/positionRisk``, NOT v2, and its response carries no
``marginRatio`` field -- that ratio must be derived separately from
``/fapi/v3/account``'s ``totalMaintMargin``/``totalMarginBalance`` totals
(see ``application/anti_liquidation_status.py``). DCABOT never computes its
own liquidation price (LCR-12); these two fetchers only read and bound-
validate the venue's own report. No credential exists in this repo yet for
the real host -- this module is exercised via the same fake Response/Opener
seam as ``binance_testnet_account.py``, ready to point at a real credential
once Faz D's gate (Arda) supplies one.
"""

from dataclasses import dataclass
import hashlib
import json
import time
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from dcabot.application.credential_boundary import CredentialProvider
from dcabot.application.signed_request import (
    ApiKeyType,
    Clock,
    DEFAULT_RECV_WINDOW_MS,
    HmacSha256Signer,
    SignedRequestError,
    build_signed_request,
)
from dcabot.domain.numbers import number


BINANCE_FUTURES_TESTNET_REST_BASE_URL = "https://testnet.binancefuture.com/fapi"
BINANCE_FUTURES_TESTNET_POSITION_RISK_URL = f"{BINANCE_FUTURES_TESTNET_REST_BASE_URL}/v3/positionRisk"
BINANCE_FUTURES_TESTNET_ACCOUNT_URL = f"{BINANCE_FUTURES_TESTNET_REST_BASE_URL}/v3/account"
MAX_POSITION_RISK_RESPONSE_BYTES = 256 * 1024
MAX_ACCOUNT_RESPONSE_BYTES = 256 * 1024
MAX_POSITIONS = 512
DEFAULT_TIMEOUT_SECONDS = 5


class BinanceFuturesPositionRiskError(RuntimeError):
    """Raised when a signed futures position-risk/account read cannot safely complete."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


class PositionRiskResponse(Protocol):
    status: int
    headers: object

    def read(self, size: int = -1) -> bytes: ...

    def close(self) -> None: ...


class PositionRiskOpener(Protocol):
    def open(self, request: Request, timeout: int) -> PositionRiskResponse: ...


class SystemClock:
    def now_ms(self) -> int:
        return time.time_ns() // 1_000_000


@dataclass(frozen=True, slots=True)
class FuturesPositionRisk:
    """One venue-reported position row. `liquidation_price == "0"` means the
    field is not meaningful (e.g. no position or cross-margin without an
    isolated liquidation price) -- it is NEVER read as "no risk"."""

    symbol: str
    position_amt: str
    entry_price: str
    mark_price: str
    liquidation_price: str
    leverage: str
    unrealized_profit: str
    position_side: str
    update_time_ms: int


@dataclass(frozen=True, slots=True, repr=False)
class FuturesAccountMargin:
    """Account-level margin totals; the source for the derived margin ratio
    (RG-02: the venue does not report a ready-made ratio on positionRisk)."""

    total_maint_margin: str
    total_margin_balance: str
    update_time_ms: int

    def __repr__(self) -> str:
        return "FuturesAccountMargin(<redacted totals>)"


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, new):
        raise BinanceFuturesPositionRiskError(
            "FUTURES_POSITION_RISK_REDIRECT_REJECTED", "Position-risk isteği yönlendirmesi reddedildi."
        )


def _sign_and_request(
    url: str,
    params: tuple[tuple[str, str], ...],
    *,
    credential_id: str,
    provider: CredentialProvider,
    clock: Clock | None,
    recv_window_ms: int,
    error_prefix: str,
) -> Request:
    try:
        material = provider.load(credential_id)
        if material.key_type is not ApiKeyType.HMAC:
            raise BinanceFuturesPositionRiskError(
                f"{error_prefix}_KEY_TYPE_UNSUPPORTED", "Yalnız HMAC key destekleniyor."
            )
        signed = build_signed_request(
            params,
            clock=clock or SystemClock(),
            recv_window_ms=recv_window_ms,
            signer=HmacSha256Signer(material.secret),
        )
    except BinanceFuturesPositionRiskError:
        raise
    except SignedRequestError as exc:
        raise BinanceFuturesPositionRiskError(exc.code, "İmzalı istek hazırlanamadı.") from exc
    return Request(
        f"{url}?{signed.query_string}",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "X-MBX-APIKEY": material.api_key,
        },
        method="GET",
    )


def _open_and_read(
    request: Request,
    *,
    opener: PositionRiskOpener | None,
    timeout_seconds: int,
    max_bytes: int,
    error_prefix: str,
) -> bytes:
    response: PositionRiskResponse | None = None
    try:
        response = (opener or build_opener(_NoRedirectHandler())).open(
            request, timeout=timeout_seconds
        )
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()  # type: ignore[attr-defined]
        if status != 200:
            raise BinanceFuturesPositionRiskError(
                f"{error_prefix}_HTTP_ERROR", "İmzalı futures yanıtı başarılı değil."
            )
        return _read_bounded(response, max_bytes, error_prefix)
    except BinanceFuturesPositionRiskError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise BinanceFuturesPositionRiskError(
            f"{error_prefix}_UNAVAILABLE", "İmzalı futures yanıtı alınamadı."
        ) from exc
    finally:
        if response is not None:
            response.close()


def _read_bounded(response: PositionRiskResponse, max_bytes: int, error_prefix: str) -> bytes:
    headers = getattr(response, "headers", None)
    content_length = headers.get("Content-Length") if headers is not None else None
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except (TypeError, ValueError) as exc:
            raise BinanceFuturesPositionRiskError(
                f"{error_prefix}_RESPONSE_INVALID", "Content-Length geçersiz."
            ) from exc
        if declared_size < 0 or declared_size > max_bytes:
            raise BinanceFuturesPositionRiskError(
                f"{error_prefix}_RESPONSE_TOO_LARGE", "Yanıt byte sınırını aşıyor."
            )
    encoding = headers.get("Content-Encoding") if headers is not None else None
    if encoding and encoding.lower() != "identity":
        raise BinanceFuturesPositionRiskError(
            f"{error_prefix}_ENCODING_INVALID", "Yanıt sıkıştırma biçimi reddedildi."
        )
    payload = response.read(max_bytes + 1)
    if not isinstance(payload, bytes) or len(payload) > max_bytes:
        raise BinanceFuturesPositionRiskError(
            f"{error_prefix}_RESPONSE_TOO_LARGE", "Yanıt byte sınırını aşıyor."
        )
    return payload


def fetch_binance_futures_position_risk(
    credential_id: str,
    symbol: str,
    *,
    provider: CredentialProvider,
    clock: Clock | None = None,
    opener: PositionRiskOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    recv_window_ms: int = DEFAULT_RECV_WINDOW_MS,
) -> tuple[FuturesPositionRisk, ...]:
    """Fetch the venue's own position-risk rows for one symbol; read-only."""

    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30:
        raise BinanceFuturesPositionRiskError(
            "FUTURES_POSITION_RISK_TIMEOUT_INVALID", "Timeout değeri geçersiz."
        )
    if (
        not isinstance(symbol, str)
        or not 1 <= len(symbol) <= 32
        or symbol != symbol.strip()
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in symbol)
    ):
        raise BinanceFuturesPositionRiskError(
            "FUTURES_POSITION_RISK_SYMBOL_INVALID", "Symbol değeri geçersiz."
        )
    request = _sign_and_request(
        BINANCE_FUTURES_TESTNET_POSITION_RISK_URL,
        (("symbol", symbol),),
        credential_id=credential_id,
        provider=provider,
        clock=clock,
        recv_window_ms=recv_window_ms,
        error_prefix="FUTURES_POSITION_RISK",
    )
    payload_bytes = _open_and_read(
        request,
        opener=opener,
        timeout_seconds=timeout_seconds,
        max_bytes=MAX_POSITION_RISK_RESPONSE_BYTES,
        error_prefix="FUTURES_POSITION_RISK",
    )
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BinanceFuturesPositionRiskError(
            "FUTURES_POSITION_RISK_RESPONSE_INVALID", "Yanıt JSON olarak okunamadı."
        ) from exc
    if type(payload) is not list or len(payload) > MAX_POSITIONS:
        raise BinanceFuturesPositionRiskError(
            "FUTURES_POSITION_RISK_RESPONSE_INVALID", "Yanıt bounded liste olmalıdır."
        )
    return _normalize_position_risk(payload, symbol)


def _normalize_position_risk(payload: list[object], symbol: str) -> tuple[FuturesPositionRisk, ...]:
    rows: list[FuturesPositionRisk] = []
    for item in payload:
        if type(item) is not dict:
            raise BinanceFuturesPositionRiskError(
                "FUTURES_POSITION_RISK_RESPONSE_INVALID", "Position-risk öğesi nesne olmalıdır."
            )
        for text_field, limit in (
            ("symbol", 32),
            ("positionAmt", 128),
            ("entryPrice", 128),
            ("markPrice", 128),
            ("liquidationPrice", 128),
            ("leverage", 32),
            ("unRealizedProfit", 128),
            ("positionSide", 16),
        ):
            value = item.get(text_field)
            if (
                type(value) is not str
                or not value
                or len(value) > limit
                or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
            ):
                raise BinanceFuturesPositionRiskError(
                    "FUTURES_POSITION_RISK_RESPONSE_INVALID", f"Position-risk {text_field} alanı geçersiz."
                )
        if item["symbol"] != symbol:
            raise BinanceFuturesPositionRiskError(
                "FUTURES_POSITION_RISK_RESPONSE_INVALID", "Position-risk symbol kimliği doğrulanamadı."
            )
        update_time = item.get("updateTime", 0)
        if type(update_time) is not int or update_time < 0:
            raise BinanceFuturesPositionRiskError(
                "FUTURES_POSITION_RISK_RESPONSE_INVALID", "Position-risk updateTime alanı geçersiz."
            )
        try:
            # positionAmt is signed (negative for SHORT); others are non-negative.
            number(item["positionAmt"].removeprefix("-") if item["positionAmt"].startswith("-") else item["positionAmt"])
            for field in ("entryPrice", "markPrice", "leverage"):
                if number(item[field]) < 0:
                    raise ValueError("negative")
            liquidation = item["liquidationPrice"]
            if number(liquidation) < 0:
                raise ValueError("negative")
        except ValueError as exc:
            raise BinanceFuturesPositionRiskError(
                "FUTURES_POSITION_RISK_RESPONSE_INVALID", "Position-risk miktarı exact decimal olmalıdır."
            ) from exc
        rows.append(
            FuturesPositionRisk(
                symbol=item["symbol"],
                position_amt=item["positionAmt"],
                entry_price=item["entryPrice"],
                mark_price=item["markPrice"],
                liquidation_price=item["liquidationPrice"],
                leverage=item["leverage"],
                unrealized_profit=item["unRealizedProfit"],
                position_side=item["positionSide"],
                update_time_ms=update_time,
            )
        )
    return tuple(rows)


def fetch_binance_futures_account_margin(
    credential_id: str,
    *,
    provider: CredentialProvider,
    clock: Clock | None = None,
    opener: PositionRiskOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    recv_window_ms: int = DEFAULT_RECV_WINDOW_MS,
) -> FuturesAccountMargin:
    """Fetch the account's margin totals; the source for the derived margin
    ratio (RG-02: positionRisk carries no marginRatio field)."""

    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30:
        raise BinanceFuturesPositionRiskError(
            "FUTURES_ACCOUNT_MARGIN_TIMEOUT_INVALID", "Timeout değeri geçersiz."
        )
    request = _sign_and_request(
        BINANCE_FUTURES_TESTNET_ACCOUNT_URL,
        (),
        credential_id=credential_id,
        provider=provider,
        clock=clock,
        recv_window_ms=recv_window_ms,
        error_prefix="FUTURES_ACCOUNT_MARGIN",
    )
    payload_bytes = _open_and_read(
        request,
        opener=opener,
        timeout_seconds=timeout_seconds,
        max_bytes=MAX_ACCOUNT_RESPONSE_BYTES,
        error_prefix="FUTURES_ACCOUNT_MARGIN",
    )
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BinanceFuturesPositionRiskError(
            "FUTURES_ACCOUNT_MARGIN_RESPONSE_INVALID", "Yanıt JSON olarak okunamadı."
        ) from exc
    if type(payload) is not dict:
        raise BinanceFuturesPositionRiskError(
            "FUTURES_ACCOUNT_MARGIN_RESPONSE_INVALID", "Yanıt nesne olmalıdır."
        )
    for text_field in ("totalMaintMargin", "totalMarginBalance"):
        value = payload.get(text_field)
        if (
            type(value) is not str
            or not value
            or len(value) > 128
            or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
        ):
            raise BinanceFuturesPositionRiskError(
                "FUTURES_ACCOUNT_MARGIN_RESPONSE_INVALID", f"Account {text_field} alanı geçersiz."
            )
    update_time = payload.get("updateTime", 0)
    if type(update_time) is not int or update_time < 0:
        raise BinanceFuturesPositionRiskError(
            "FUTURES_ACCOUNT_MARGIN_RESPONSE_INVALID", "Account updateTime alanı geçersiz."
        )
    try:
        number(payload["totalMaintMargin"])
        number(payload["totalMarginBalance"])
    except ValueError as exc:
        raise BinanceFuturesPositionRiskError(
            "FUTURES_ACCOUNT_MARGIN_RESPONSE_INVALID", "Account tutarı exact decimal olmalıdır."
        ) from exc
    return FuturesAccountMargin(
        total_maint_margin=payload["totalMaintMargin"],
        total_margin_balance=payload["totalMarginBalance"],
        update_time_ms=update_time,
    )
