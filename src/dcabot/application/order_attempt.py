"""Safe, non-economic attempt identity and state-transition contracts."""

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import re
from typing import Mapping


class AttemptState(StrEnum):
    """Durable state of one external-operation attempt."""

    PREPARED = "PREPARED"
    PERSISTED = "PERSISTED"
    SENDING = "SENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    UNKNOWN = "UNKNOWN"
    RECONCILING = "RECONCILING"
    REJECTED = "REJECTED"
    UNRESOLVED = "UNRESOLVED"


class AttemptOperation(StrEnum):
    """External operation classes reserved for the future signed adapter."""

    PLACE_ORDER = "PLACE_ORDER"
    CANCEL_ORDER = "CANCEL_ORDER"
    AMEND_ORDER = "AMEND_ORDER"


class OrderAttemptError(ValueError):
    """Raised when an attempt identity or transition is unsafe."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,128}\Z", re.ASCII)
_CLIENT_ORDER_ID = re.compile(r"[A-Za-z0-9_-]{1,36}\Z", re.ASCII)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_SAFE_REASON = re.compile(r"[A-Z0-9_:-]{1,64}\Z", re.ASCII)
MAX_REQUEST_FINGERPRINT_BYTES = 64 * 1024
_FORBIDDEN_PAYLOAD_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "access_token",
        "password",
        "private_key",
        "privatekey",
        "secret",
        "signature",
        "token",
        "x_mbx_api_key",
        "x_mbx_apikey",
    }
)


@dataclass(frozen=True, slots=True)
class OrderAttempt:
    """Redacted durable identity; raw request and credentials are never stored."""

    attempt_id: str
    run_id: str
    venue: str
    operation: AttemptOperation
    symbol: str
    client_order_id: str | None
    request_fingerprint_sha256: str
    capability_snapshot_hash: str
    filter_snapshot_hash: str
    state: AttemptState
    created_at_us: int
    last_transition_at_us: int
    send_started_at_us: int | None = None
    venue_order_id: int | None = None
    venue_event_time_ms: int | None = None
    venue_transaction_time_ms: int | None = None
    http_status: int | None = None
    venue_error_code: int | None = None
    recovery_query_count: int = 0
    last_recovery_at_us: int | None = None
    terminal_reason: str | None = None

    def __post_init__(self) -> None:
        _validate_identifier(self.attempt_id, "ATTEMPT_ID_INVALID")
        _validate_identifier(self.run_id, "ATTEMPT_RUN_ID_INVALID")
        if self.venue != "BINANCE_SPOT_TESTNET":
            raise OrderAttemptError(
                "ATTEMPT_VENUE_INVALID", "Bu dilim yalnız Binance Spot Testnet içindir."
            )
        try:
            operation = AttemptOperation(self.operation)
        except (TypeError, ValueError) as exc:
            raise OrderAttemptError("ATTEMPT_OPERATION_INVALID", "Operation geçersiz.") from exc
        object.__setattr__(self, "operation", operation)
        _validate_symbol(self.symbol)
        if self.client_order_id is not None and _CLIENT_ORDER_ID.fullmatch(self.client_order_id) is None:
            raise OrderAttemptError("ATTEMPT_CLIENT_ORDER_ID_INVALID", "Client order ID geçersiz.")
        for value, code in (
            (self.request_fingerprint_sha256, "ATTEMPT_REQUEST_HASH_INVALID"),
            (self.capability_snapshot_hash, "ATTEMPT_CAPABILITY_HASH_INVALID"),
            (self.filter_snapshot_hash, "ATTEMPT_FILTER_HASH_INVALID"),
        ):
            if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
                raise OrderAttemptError(code, "SHA-256 değeri geçersiz.")
        try:
            state = AttemptState(self.state)
        except (TypeError, ValueError) as exc:
            raise OrderAttemptError("ATTEMPT_STATE_INVALID", "Attempt state geçersiz.") from exc
        object.__setattr__(self, "state", state)
        for value, code in (
            (self.created_at_us, "ATTEMPT_CREATED_TIME_INVALID"),
            (self.last_transition_at_us, "ATTEMPT_TRANSITION_TIME_INVALID"),
        ):
            _validate_timestamp(value, code)
        for value, code in (
            (self.send_started_at_us, "ATTEMPT_SEND_TIME_INVALID"),
            (self.last_recovery_at_us, "ATTEMPT_RECOVERY_TIME_INVALID"),
        ):
            if value is not None:
                _validate_timestamp(value, code)
        for value, code in (
            (self.venue_order_id, "ATTEMPT_VENUE_ORDER_ID_INVALID"),
            (self.venue_event_time_ms, "ATTEMPT_VENUE_EVENT_TIME_INVALID"),
            (self.venue_transaction_time_ms, "ATTEMPT_VENUE_TRANSACTION_TIME_INVALID"),
            (self.http_status, "ATTEMPT_HTTP_STATUS_INVALID"),
        ):
            if value is not None and (type(value) is not int or value < 0):
                raise OrderAttemptError(code, "Integer alan negatif olamaz.")
        # Binance's own venue error codes are signed (e.g. -1013, -2013), unlike
        # the other venue_* fields above, which are genuinely non-negative IDs
        # and timestamps -- found live when a real -1013 rejection failed this
        # check. Bounded to a sane magnitude, sign allowed either way.
        if self.venue_error_code is not None and (
            type(self.venue_error_code) is not int or abs(self.venue_error_code) > 1_000_000
        ):
            raise OrderAttemptError(
                "ATTEMPT_VENUE_ERROR_CODE_INVALID", "Venue error code bounded integer olmalıdır."
            )
        if type(self.recovery_query_count) is not int or self.recovery_query_count < 0:
            raise OrderAttemptError(
                "ATTEMPT_RECOVERY_COUNT_INVALID", "Recovery sorgu sayısı geçersiz."
            )
        if self.terminal_reason is not None and _SAFE_REASON.fullmatch(self.terminal_reason) is None:
            raise OrderAttemptError("ATTEMPT_REASON_INVALID", "Terminal reason güvenli biçimde saklanamaz.")


def request_fingerprint(payload: Mapping[str, object]) -> str:
    """Hash a bounded, secret-free request without retaining its raw contents."""

    if not isinstance(payload, Mapping):
        raise OrderAttemptError("ATTEMPT_PAYLOAD_UNSAFE", "Payload nesne olmalıdır.")
    _validate_payload(payload)
    try:
        canonical = json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise OrderAttemptError("ATTEMPT_PAYLOAD_UNSAFE", "Payload güvenli JSON olarak kodlanamadı.") from exc
    encoded = canonical.encode("utf-8")
    if len(encoded) > MAX_REQUEST_FINGERPRINT_BYTES:
        raise OrderAttemptError(
            "ATTEMPT_PAYLOAD_TOO_LARGE", "Payload fingerprint byte sınırını aşıyor."
        )
    return hashlib.sha256(encoded).hexdigest()


def can_transition(current: AttemptState, target: AttemptState) -> bool:
    """Return whether a durable attempt may move between explicit states."""

    allowed = {
        # UNKNOWN is also reachable directly from PREPARED/PERSISTED: a
        # process restart (Faz 3.6, docs/KARARLAR.md 2026-09-21) cannot tell
        # whether a crash between prepare() and mark_sending() truly never
        # reached the network, so it quarantines conservatively the same way
        # a crash during SENDING does, instead of leaving the attempt with
        # no way out of a non-terminal state.
        AttemptState.PREPARED: {AttemptState.PERSISTED, AttemptState.UNKNOWN},
        AttemptState.PERSISTED: {AttemptState.SENDING, AttemptState.UNKNOWN},
        AttemptState.SENDING: {
            AttemptState.ACKNOWLEDGED,
            AttemptState.REJECTED,
            AttemptState.UNKNOWN,
        },
        AttemptState.UNKNOWN: {AttemptState.RECONCILING},
        AttemptState.RECONCILING: {
            AttemptState.ACKNOWLEDGED,
            AttemptState.REJECTED,
            AttemptState.UNRESOLVED,
        },
        AttemptState.ACKNOWLEDGED: set(),
        AttemptState.REJECTED: set(),
        AttemptState.UNRESOLVED: set(),
    }
    return target in allowed[current]


def _validate_identifier(value: object, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise OrderAttemptError(code, "Kimlik geçersiz.")


def _validate_symbol(value: object) -> None:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 32
        or value != value.strip()
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
    ):
        raise OrderAttemptError("ATTEMPT_SYMBOL_INVALID", "Symbol bounded UTF-8 metin olmalıdır.")


def _validate_timestamp(value: object, code: str) -> None:
    if type(value) is not int or value < 0:
        raise OrderAttemptError(code, "Timestamp negatif olmayan integer olmalıdır.")


def _validate_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise OrderAttemptError("ATTEMPT_PAYLOAD_UNSAFE", "Payload anahtarları metin olmalıdır.")
            normalized = key.casefold().replace("-", "_")
            if normalized in _FORBIDDEN_PAYLOAD_KEYS:
                raise OrderAttemptError(
                    "ATTEMPT_PAYLOAD_UNSAFE", "Credential içeren payload reddedildi."
                )
            _validate_payload(nested)
        return
    if isinstance(value, (list, tuple)):
        for nested in value:
            _validate_payload(nested)
        return
    if value is None or type(value) in (str, int, bool):
        return
    raise OrderAttemptError("ATTEMPT_PAYLOAD_UNSAFE", "Payload yalnız güvenli JSON primitive değerleri taşıyabilir.")
