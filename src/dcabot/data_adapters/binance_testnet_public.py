"""Bounded, credential-free Binance Spot Testnet public snapshot access."""

from dataclasses import dataclass
import hashlib
import json
import time
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener


BINANCE_SPOT_TESTNET_REST_BASE_URL = "https://testnet.binance.vision/api"
BINANCE_SPOT_TESTNET_EXCHANGE_INFO_URL = (
    f"{BINANCE_SPOT_TESTNET_REST_BASE_URL}/v3/exchangeInfo"
)
MAX_EXCHANGE_INFO_RESPONSE_BYTES = 256 * 1024
DEFAULT_TIMEOUT_SECONDS = 5
MAX_SYMBOL_LENGTH = 32


class BinanceTestnetPublicError(RuntimeError):
    """Raised when a public Testnet snapshot cannot be safely produced."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


class SnapshotResponse(Protocol):
    status: int
    headers: object

    def read(self, size: int = -1) -> bytes: ...

    def close(self) -> None: ...


class SnapshotOpener(Protocol):
    def open(self, request: Request, timeout: int) -> SnapshotResponse: ...


@dataclass(frozen=True, slots=True)
class BinanceTestnetExchangeInfoSnapshot:
    """Safe public symbol metadata; no account, credential, or order fields."""

    environment: str
    symbol: str
    status: str
    base_asset: str
    quote_asset: str
    permissions: tuple[str, ...]
    permission_sets: tuple[tuple[str, ...], ...]
    order_types: tuple[str, ...]
    filters: tuple[dict[str, str], ...]
    exchange_filters: tuple[dict[str, str], ...]
    rate_limits: tuple[dict[str, str], ...]
    response_sha256: str
    observed_at_us: int


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, new):
        raise BinanceTestnetPublicError(
            "TESTNET_REDIRECT_REJECTED", "Public snapshot yönlendirmesi reddedildi."
        )


def fetch_binance_testnet_exchange_info(
    symbol: str,
    *,
    opener: SnapshotOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> BinanceTestnetExchangeInfoSnapshot:
    """Fetch one public Testnet ``exchangeInfo`` symbol snapshot.

    The URL is fixed and the request never accepts credentials. The response is
    bounded before decoding and is reduced to non-secret symbol metadata.
    """

    _validate_options(symbol, timeout_seconds)
    query = urlencode({"symbol": symbol}, encoding="utf-8")
    request = Request(
        f"{BINANCE_SPOT_TESTNET_EXCHANGE_INFO_URL}?{query}",
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        method="GET",
    )
    active_opener = opener or build_opener(_NoRedirectHandler())
    response: SnapshotResponse | None = None
    try:
        response = active_opener.open(request, timeout=timeout_seconds)
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()  # type: ignore[attr-defined]
        if status != 200:
            raise BinanceTestnetPublicError(
                "TESTNET_UPSTREAM_HTTP_ERROR", "Public snapshot HTTP yanıtı başarılı değil."
            )
        payload_bytes = _read_bounded_response(response)
        payload = _decode_json(payload_bytes)
        return _normalize_snapshot(payload, symbol, payload_bytes)
    except BinanceTestnetPublicError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise BinanceTestnetPublicError(
            "TESTNET_UPSTREAM_UNAVAILABLE", "Public Testnet snapshot alınamadı."
        ) from exc
    finally:
        if response is not None:
            response.close()


def _validate_options(symbol: str, timeout_seconds: int) -> None:
    if (
        type(symbol) is not str
        or not symbol
        or len(symbol) > MAX_SYMBOL_LENGTH
        or symbol != symbol.strip()
        or any(char.isspace() or ord(char) == 0x7F for char in symbol)
    ):
        raise BinanceTestnetPublicError(
            "TESTNET_SYMBOL_INVALID", "Symbol boşluksuz ve sınırlı uzunlukta olmalıdır."
        )
    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30:
        raise BinanceTestnetPublicError(
            "TESTNET_TIMEOUT_INVALID", "Snapshot timeout değeri geçersiz."
        )


def _read_bounded_response(response: SnapshotResponse) -> bytes:
    headers = getattr(response, "headers", None)
    content_length = headers.get("Content-Length") if headers is not None else None
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except (TypeError, ValueError) as exc:
            raise BinanceTestnetPublicError(
                "TESTNET_RESPONSE_INVALID", "Public snapshot Content-Length geçersiz."
            ) from exc
        if declared_size < 0 or declared_size > MAX_EXCHANGE_INFO_RESPONSE_BYTES:
            raise BinanceTestnetPublicError(
                "TESTNET_RESPONSE_TOO_LARGE", "Public snapshot byte sınırını aşıyor."
            )
    encoding = headers.get("Content-Encoding") if headers is not None else None
    if encoding and encoding.lower() != "identity":
        raise BinanceTestnetPublicError(
            "TESTNET_ENCODING_INVALID", "Public snapshot sıkıştırma biçimi reddedildi."
        )
    payload = response.read(MAX_EXCHANGE_INFO_RESPONSE_BYTES + 1)
    if not isinstance(payload, bytes):
        raise BinanceTestnetPublicError(
            "TESTNET_RESPONSE_INVALID", "Public snapshot gövdesi bytes olmalıdır."
        )
    if len(payload) > MAX_EXCHANGE_INFO_RESPONSE_BYTES:
        raise BinanceTestnetPublicError(
            "TESTNET_RESPONSE_TOO_LARGE", "Public snapshot byte sınırını aşıyor."
        )
    return payload


def _decode_json(payload_bytes: bytes) -> dict[str, object]:
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BinanceTestnetPublicError(
            "TESTNET_RESPONSE_INVALID", "Public snapshot JSON olarak okunamadı."
        ) from exc
    if type(payload) is not dict:
        raise BinanceTestnetPublicError(
            "TESTNET_RESPONSE_INVALID", "Public snapshot nesne olmalıdır."
        )
    return payload


def _normalize_snapshot(
    payload: dict[str, object], symbol: str, payload_bytes: bytes
) -> BinanceTestnetExchangeInfoSnapshot:
    symbols = payload.get("symbols")
    if type(symbols) is not list or len(symbols) > 100:
        raise BinanceTestnetPublicError(
            "TESTNET_RESPONSE_INVALID", "Public snapshot symbols alanı geçersiz."
        )
    symbol_payload = next(
        (item for item in symbols if type(item) is dict and item.get("symbol") == symbol),
        None,
    )
    if symbol_payload is None:
        raise BinanceTestnetPublicError(
            "TESTNET_SYMBOL_NOT_FOUND", "İstenen Testnet symbol snapshot içinde bulunamadı."
        )
    required = ("symbol", "status", "baseAsset", "quoteAsset", "orderTypes", "filters")
    if any(
        type(symbol_payload.get(field)) is not (list if field in ("orderTypes", "filters") else str)
        for field in required
    ):
        raise BinanceTestnetPublicError(
            "TESTNET_RESPONSE_INVALID", "Public symbol metadata alanları geçersiz."
        )
    permissions = _string_tuple(symbol_payload.get("permissions", []), "permissions")
    permission_sets = _nested_string_tuple(symbol_payload.get("permissionSets", []), "permissionSets")
    order_types = _string_tuple(symbol_payload["orderTypes"], "orderTypes")
    filters = _string_maps(symbol_payload["filters"], "filters")
    exchange_filters = _string_maps(payload.get("exchangeFilters", []), "exchangeFilters")
    rate_limits = _string_maps(payload.get("rateLimits", []), "rateLimits")
    return BinanceTestnetExchangeInfoSnapshot(
        environment="BINANCE_SPOT_TESTNET",
        symbol=symbol,
        status=symbol_payload["status"],
        base_asset=symbol_payload["baseAsset"],
        quote_asset=symbol_payload["quoteAsset"],
        permissions=permissions,
        permission_sets=permission_sets,
        order_types=order_types,
        filters=filters,
        exchange_filters=exchange_filters,
        rate_limits=rate_limits,
        response_sha256=hashlib.sha256(payload_bytes).hexdigest(),
        observed_at_us=time.time_ns() // 1000,
    )


def _string_tuple(raw: object, field_name: str) -> tuple[str, ...]:
    if type(raw) is not list or len(raw) > 32 or any(
        type(item) is not str or not item or len(item) > 64 for item in raw
    ):
        raise BinanceTestnetPublicError(
            "TESTNET_RESPONSE_INVALID", f"Public {field_name} alanı geçersiz."
        )
    return tuple(raw)


def _nested_string_tuple(raw: object, field_name: str) -> tuple[tuple[str, ...], ...]:
    if type(raw) is not list or len(raw) > 32:
        raise BinanceTestnetPublicError(
            "TESTNET_RESPONSE_INVALID", f"Public {field_name} alanı geçersiz."
        )
    return tuple(_string_tuple(item, field_name) for item in raw)


def _string_maps(raw: object, field_name: str) -> tuple[dict[str, str], ...]:
    if type(raw) is not list or len(raw) > 128:
        raise BinanceTestnetPublicError(
            "TESTNET_RESPONSE_INVALID", f"Public {field_name} alanı geçersiz."
        )
    normalized: list[dict[str, str]] = []
    for item in raw:
        if type(item) is not dict or len(item) > 64:
            raise BinanceTestnetPublicError(
                "TESTNET_RESPONSE_INVALID", f"Public {field_name} öğesi geçersiz."
            )
        values: dict[str, str] = {}
        for key, value in item.items():
            if type(key) is not str or not key or len(key) > 64:
                raise BinanceTestnetPublicError(
                    "TESTNET_RESPONSE_INVALID", f"Public {field_name} anahtarı geçersiz."
                )
            if type(value) not in (str, int, bool) or isinstance(value, float):
                raise BinanceTestnetPublicError(
                    "TESTNET_RESPONSE_INVALID", f"Public {field_name} değeri geçersiz."
                )
            values[key] = value if type(value) is str else json.dumps(value)
        normalized.append(values)
    return tuple(normalized)
