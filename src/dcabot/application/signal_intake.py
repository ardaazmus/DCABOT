"""Offline signal intake: payload hashing, HMAC auth, and replay window."""

import hashlib
import hmac
import json
import re
from collections.abc import Container, Mapping


_HEX64 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_KEY_ID = re.compile(r"[A-Za-z0-9:_-]{1,64}\Z", re.ASCII)
_MAX_PAYLOAD_BYTES = 65_536


class SignalIntakeError(ValueError):
    """Raised when a signal cannot be hashed, authenticated, or replay-checked."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def hash_signal_payload(payload: dict[str, object]) -> str:
    """Hash caller payload with canonical JSON (JCS-compatible profile).

    Key order never affects the hash. The payload must be a JSON object of
    JSON scalar values; anything else fails closed before any identity exists.
    """

    if not isinstance(payload, dict):
        raise SignalIntakeError(
            "SIGNAL_PAYLOAD_NOT_JSON", "Signal payload JSON object olmalıdır."
        )
    _validate_json_value(payload, depth=0)
    try:
        canonical = json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise SignalIntakeError(
            "SIGNAL_PAYLOAD_NOT_JSON", "Signal payload canonical JSON olmalıdır."
        ) from error
    if len(canonical.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
        raise SignalIntakeError(
            "SIGNAL_PAYLOAD_TOO_LARGE", "Signal payload boyutu sınırı aşıyor."
        )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_signal_signature(
    *,
    payload_hash: str,
    signature: str,
    key_id: str,
    keys: Mapping[str, str],
) -> None:
    """Verify an HMAC-SHA256 signature over the payload hash.

    ``keys`` maps key IDs to lowercase hex key material and is owned by the
    caller (offline demo: caller-managed test keys; never logged, never part
    of any error message). Comparison is constant-time. Returns None on
    success; any failure raises without revealing which secret was expected.
    """

    if (
        not isinstance(payload_hash, str)
        or _HEX64.fullmatch(payload_hash) is None
    ):
        raise SignalIntakeError(
            "SIGNAL_PAYLOAD_HASH_INVALID",
            "Payload hash küçük harfli SHA-256 hex olmalıdır.",
        )
    if not isinstance(signature, str) or _HEX64.fullmatch(signature) is None:
        raise SignalIntakeError(
            "SIGNAL_SIGNATURE_MALFORMED",
            "Signature küçük harfli SHA-256 hex olmalıdır.",
        )
    if not isinstance(key_id, str) or _KEY_ID.fullmatch(key_id) is None:
        raise SignalIntakeError("SIGNAL_KEY_UNKNOWN", "Signature anahtarı bilinmiyor.")
    if not isinstance(keys, Mapping):
        raise SignalIntakeError("SIGNAL_KEY_UNKNOWN", "Signature anahtarı bilinmiyor.")
    try:
        key_hex = keys[key_id]
    except KeyError as error:
        raise SignalIntakeError(
            "SIGNAL_KEY_UNKNOWN", "Signature anahtarı bilinmiyor."
        ) from error
    if (
        not isinstance(key_hex, str)
        or len(key_hex) < 32
        or len(key_hex) % 2 != 0
        or not all(c in "0123456789abcdef" for c in key_hex)
    ):
        raise SignalIntakeError("SIGNAL_KEY_UNKNOWN", "Signature anahtarı bilinmiyor.")
    expected = hmac.new(
        bytes.fromhex(key_hex), payload_hash.encode("ascii"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise SignalIntakeError(
            "SIGNAL_SIGNATURE_MISMATCH", "Signature doğrulanamadı."
        )


def check_replay_window(
    *,
    event_time_us: int,
    observation_time_us: int,
    max_age_us: int,
    seen_ids: Container[str],
    signal_id: str,
) -> str:
    """Accept a signal only inside its event-time replay window.

    Times are source/observation microseconds; wall-clock is absent by design.
    ``seen_ids`` is caller-owned (durable store binds later); membership here
    only reports DUPLICATE, it never mutates. Returns "ACCEPT" on success.
    """

    for value, code in (
        (event_time_us, "SIGNAL_REPLAY_TIME_INVALID"),
        (observation_time_us, "SIGNAL_REPLAY_TIME_INVALID"),
        (max_age_us, "SIGNAL_REPLAY_WINDOW_INVALID"),
    ):
        if type(value) is not int or value < 0:
            raise SignalIntakeError(code, "Zaman/pencere negatif olmayan integer olmalıdır.")
    if not isinstance(signal_id, str) or not signal_id:
        raise SignalIntakeError("SIGNAL_REPLAY_ID_INVALID", "Signal kimliği geçersiz.")
    if event_time_us > observation_time_us:
        raise SignalIntakeError(
            "SIGNAL_REPLAY_FUTURE",
            "Signal gözlem zamanından yeni olamaz.",
        )
    if observation_time_us - event_time_us > max_age_us:
        raise SignalIntakeError(
            "SIGNAL_REPLAY_EXPIRED",
            "Signal replay penceresi dışında.",
        )
    if signal_id in seen_ids:
        raise SignalIntakeError(
            "SIGNAL_REPLAY_DUPLICATE",
            "Signal kimliği zaten görüldü.",
        )
    return "ACCEPT"


def _validate_json_value(value: object, *, depth: int) -> None:
    if depth > 8:
        raise SignalIntakeError(
            "SIGNAL_PAYLOAD_NOT_JSON", "Signal payload derinliği sınırı aşıyor."
        )
    if value is None or isinstance(value, (bool, int, float, str)):
        if isinstance(value, float) and value != value:
            raise SignalIntakeError(
                "SIGNAL_PAYLOAD_NOT_JSON", "Signal payload NaN taşıyamaz."
            )
        return
    if isinstance(value, list):
        for item in value:
            _validate_json_value(item, depth=depth + 1)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise SignalIntakeError(
                    "SIGNAL_PAYLOAD_NOT_JSON", "Signal payload anahtarı string olmalıdır."
                )
            _validate_json_value(item, depth=depth + 1)
        return
    raise SignalIntakeError(
        "SIGNAL_PAYLOAD_NOT_JSON", "Signal payload yalnız JSON değer taşıyabilir."
    )
