"""Offline signed-request primitives with explicit timing boundaries.

This module deliberately stops before HTTP transport, API-key headers, and
secret persistence.  It provides deterministic request serialization and an
in-memory HMAC implementation for tests; asymmetric signer implementations
can be added behind the same protocol after their key lifecycle is approved.
"""

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import hmac
from typing import Protocol, Sequence
from urllib.parse import quote


DEFAULT_RECV_WINDOW_MS = 5_000
MAX_RECV_WINDOW_MS = 60_000
FUTURE_TIMESTAMP_TOLERANCE_MS = 1_000
MAX_SIGNED_PAYLOAD_BYTES = 64 * 1024
MAX_PARAMETER_COUNT = 64
MAX_SECRET_BYTES = 4 * 1024


class ApiKeyType(StrEnum):
    """Supported signer families; implementation support is explicit."""

    ED25519 = "ED25519"
    RSA = "RSA"
    HMAC = "HMAC"
    UNKNOWN = "UNKNOWN"


class SignedRequestError(ValueError):
    """Raised when signed-request data cannot pass the safe boundary."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class Clock(Protocol):
    """Provide a deterministic Unix timestamp in integer milliseconds."""

    def now_ms(self) -> int: ...


class RequestSigner(Protocol):
    """Sign already-encoded bytes without exposing key material."""

    @property
    def key_type(self) -> ApiKeyType: ...

    def sign(self, payload: bytes) -> str: ...


class HmacSha256Signer:
    """In-memory HMAC signer used only behind an explicit caller boundary."""

    __slots__ = ("_secret",)

    def __init__(self, secret: bytes) -> None:
        if not isinstance(secret, bytes) or not secret:
            raise SignedRequestError("SIGNER_SECRET_INVALID", "HMAC anahtarı boş bytes olmalıdır.")
        if len(secret) > MAX_SECRET_BYTES:
            raise SignedRequestError("SIGNER_SECRET_TOO_LARGE", "HMAC anahtarı sınırı aşıyor.")
        self._secret = bytes(secret)

    @property
    def key_type(self) -> ApiKeyType:
        return ApiKeyType.HMAC

    def sign(self, payload: bytes) -> str:
        if not isinstance(payload, bytes):
            raise SignedRequestError("SIGNED_PAYLOAD_INVALID", "İmza payload’ı bytes olmalıdır.")
        return hmac.new(self._secret, payload, hashlib.sha256).hexdigest()

    def __repr__(self) -> str:
        return "HmacSha256Signer(<redacted>)"


@dataclass(frozen=True, slots=True)
class SignedRequest:
    """Ephemeral signed payload; it contains no API key or secret."""

    payload: str
    signature: str
    key_type: ApiKeyType
    timestamp_ms: int
    recv_window_ms: int

    @property
    def query_string(self) -> str:
        """Return the payload plus its encoded signature for a future adapter."""

        return f"{self.payload}&signature={quote(self.signature, safe='-_.~')}"


def build_signed_request(
    params: Sequence[tuple[str, str]],
    *,
    clock: Clock,
    recv_window_ms: int = DEFAULT_RECV_WINDOW_MS,
    signer: RequestSigner,
) -> SignedRequest:
    """Build a deterministic REST signing payload without performing I/O."""

    timestamp_ms = _clock_timestamp_ms(clock)
    recv_window_ms = validate_recv_window_ms(recv_window_ms)
    key_type = _validated_key_type(signer)
    encoded_params = _encode_params(params)
    encoded_params.extend(
        (
            _encode_pair("timestamp", str(timestamp_ms)),
            _encode_pair("recvWindow", str(recv_window_ms)),
        )
    )
    payload = "&".join(encoded_params)
    if len(payload.encode("ascii")) > MAX_SIGNED_PAYLOAD_BYTES:
        raise SignedRequestError("SIGNED_PAYLOAD_TOO_LARGE", "İmzalanacak payload sınırı aşıyor.")
    signature = signer.sign(payload.encode("ascii"))
    if (
        not isinstance(signature, str)
        or not signature
        or len(signature) > MAX_SIGNED_PAYLOAD_BYTES
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in signature)
    ):
        raise SignedRequestError("SIGNED_SIGNATURE_INVALID", "İmza bounded metin olmalıdır.")
    return SignedRequest(
        payload=payload,
        signature=signature,
        key_type=key_type,
        timestamp_ms=timestamp_ms,
        recv_window_ms=recv_window_ms,
    )


def validate_recv_window_ms(value: int) -> int:
    """Validate the integer-millisecond application policy for recvWindow."""

    if type(value) is not int or not 1 <= value <= MAX_RECV_WINDOW_MS:
        raise SignedRequestError(
            "RECV_WINDOW_INVALID", "recvWindow 1..60000 integer milliseconds olmalıdır."
        )
    return value


def is_timestamp_within_window(
    timestamp_ms: int, server_time_ms: int, recv_window_ms: int
) -> bool:
    """Apply the venue timing predicate to supplied values without reading a clock."""

    _validate_nonnegative_ms(timestamp_ms, "TIMESTAMP_INVALID")
    _validate_nonnegative_ms(server_time_ms, "SERVER_TIME_INVALID")
    recv_window_ms = validate_recv_window_ms(recv_window_ms)
    return (
        timestamp_ms < server_time_ms + FUTURE_TIMESTAMP_TOLERANCE_MS
        and server_time_ms - timestamp_ms <= recv_window_ms
    )


def _clock_timestamp_ms(clock: Clock) -> int:
    try:
        timestamp_ms = clock.now_ms()
    except Exception as exc:
        raise SignedRequestError("CLOCK_UNAVAILABLE", "İstek zamanı alınamadı.") from exc
    _validate_nonnegative_ms(timestamp_ms, "TIMESTAMP_INVALID")
    return timestamp_ms


def _validated_key_type(signer: RequestSigner) -> ApiKeyType:
    try:
        key_type = ApiKeyType(signer.key_type)
    except (AttributeError, TypeError, ValueError) as exc:
        raise SignedRequestError(
            "SIGNED_KEY_TYPE_UNSUPPORTED", "İmza anahtarı türü tanınmıyor."
        ) from exc
    if key_type is ApiKeyType.UNKNOWN:
        raise SignedRequestError(
            "SIGNED_KEY_TYPE_UNSUPPORTED", "Bilinmeyen imza anahtarı türü reddedildi."
        )
    return key_type


def _encode_params(params: Sequence[tuple[str, str]]) -> list[str]:
    try:
        pairs = tuple(params)
    except TypeError as exc:
        raise SignedRequestError("SIGNED_PARAM_UNSAFE", "Parametreler sıralı çift olmalıdır.") from exc
    if len(pairs) > MAX_PARAMETER_COUNT:
        raise SignedRequestError("SIGNED_PARAM_TOO_MANY", "Parametre sayısı sınırı aşıyor.")
    encoded = []
    seen: set[str] = set()
    for pair in pairs:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise SignedRequestError("SIGNED_PARAM_UNSAFE", "Parametreler sıralı çift olmalıdır.")
        name, value = pair
        if not isinstance(name, str) or not isinstance(value, str):
            raise SignedRequestError("SIGNED_PARAM_UNSAFE", "Parametre adı ve değeri metin olmalıdır.")
        normalized = name.casefold().replace("-", "_")
        if normalized in {
            "apikey",
            "api_key",
            "authorization",
            "access_token",
            "password",
            "private_key",
            "privatekey",
            "secret",
            "signature",
            "timestamp",
            "recvwindow",
            "token",
        } or name in seen:
            raise SignedRequestError(
                "SIGNED_PARAM_UNSAFE", "Credential, timing veya duplicate parametre reddedildi."
            )
        seen.add(name)
        encoded.append(_encode_pair(name, value))
    return encoded


def _encode_pair(name: str, value: str) -> str:
    if any(ord(char) < 0x20 or ord(char) == 0x7F for char in name + value):
        raise SignedRequestError("SIGNED_PARAM_UNSAFE", "Kontrol karakteri taşıyan parametre reddedildi.")
    return f"{quote(name, safe='-_.~')}={quote(value, safe='-_.~')}"


def _validate_nonnegative_ms(value: object, code: str) -> None:
    if type(value) is not int or value < 0:
        raise SignedRequestError(code, "Zaman integer milliseconds olmalıdır.")
