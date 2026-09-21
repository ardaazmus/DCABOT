"""Bind READY offline signals to immutable strategy candidates.

The event carries identity only (no action, no symbol, no quantity): the
caller supplies action, symbol, and sizing explicitly, and an explicit
action→side map resolves direction. Candidates carry an event-time expiry
and hold no order, reserve, or fill authority.
"""

from dataclasses import dataclass
import hashlib
import json
import re

from dcabot.application.signal_event_contract import SignalEvent
from dcabot.application.signal_readiness import SignalReadiness
from dcabot.domain.numbers import exact_text, positive


_SYMBOL = re.compile(r"[A-Za-z0-9:_-]{1,32}\Z", re.ASCII)
_SCHEMA = "signal-candidate-v1"
_SIDES = frozenset({"BUY", "SELL"})


class SignalCandidateBindingError(ValueError):
    """Raised when a signal cannot bind to a strategy candidate safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class SignalCandidate:
    """Immutable candidate intent; still not an order or a fill."""

    candidate_id: str
    schema_version: str
    status: str
    signal_id: str
    payload_hash: str
    symbol: str
    side: str
    qty: str
    expires_us: int


def bind_signal_candidate(
    *,
    signal: SignalEvent,
    readiness: SignalReadiness,
    action: str,
    symbol: str,
    action_map: tuple[tuple[str, str], ...],
    qty: str,
    ttl_us: int,
    binding_time_us: int,
) -> SignalCandidate:
    """Bind one READY signal to one expiring candidate with explicit sizing."""

    if not isinstance(signal, SignalEvent):
        raise SignalCandidateBindingError(
            "SIGNAL_CANDIDATE_SIGNAL_INVALID", "Signal kaydı geçersiz."
        )
    if not isinstance(readiness, SignalReadiness):
        raise SignalCandidateBindingError(
            "SIGNAL_CANDIDATE_READINESS_INVALID", "Readiness kaydı geçersiz."
        )
    if readiness.signal_id != signal.signal_id:
        raise SignalCandidateBindingError(
            "SIGNAL_CANDIDATE_ASSESSMENT_MISMATCH",
            "Readiness başka bir signala ait.",
        )
    if readiness.status != "READY":
        raise SignalCandidateBindingError(
            "SIGNAL_CANDIDATE_NOT_READY",
            "Yalnız READY signal aday bağlayabilir.",
        )
    sides = _checked_action_map(action_map)
    if not isinstance(action, str) or action not in sides:
        raise SignalCandidateBindingError(
            "SIGNAL_CANDIDATE_ACTION_UNMAPPED",
            "Signal action yön eşlemesinde yok.",
        )
    if not isinstance(symbol, str) or _SYMBOL.fullmatch(symbol) is None:
        raise SignalCandidateBindingError(
            "SIGNAL_CANDIDATE_SYMBOL_INVALID", "Symbol kimliği geçersiz."
        )
    try:
        amount = positive(qty)
    except ValueError as error:
        raise SignalCandidateBindingError(
            "SIGNAL_CANDIDATE_QTY_INVALID",
            "Qty pozitif decimal string olmalıdır.",
        ) from error
    if type(ttl_us) is not int or ttl_us <= 0:
        raise SignalCandidateBindingError(
            "SIGNAL_CANDIDATE_TTL_INVALID",
            "TTL pozitif integer microseconds olmalıdır.",
        )
    if type(binding_time_us) is not int or binding_time_us < 0:
        raise SignalCandidateBindingError(
            "SIGNAL_CANDIDATE_TIME_INVALID",
            "Binding zamanı sıfır veya pozitif integer olmalıdır.",
        )

    try:
        qty_text = exact_text(amount)
    except ValueError as error:
        raise SignalCandidateBindingError(
            "SIGNAL_CANDIDATE_QTY_INVALID",
            "Qty exact decimal sözleşmesine sığmıyor.",
        ) from error
    expires_us = signal.event_time_us + ttl_us
    candidate_id = hashlib.sha256(
        json.dumps(
            {
                "action": action,
                "binding_time_us": binding_time_us,
                "expires_us": expires_us,
                "payload_hash": signal.payload_hash,
                "qty": qty_text,
                "schema": _SCHEMA,
                "side": sides[action],
                "signal_id": signal.signal_id,
                "symbol": symbol,
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    return SignalCandidate(
        candidate_id=candidate_id,
        schema_version=_SCHEMA,
        status="CANDIDATE",
        signal_id=signal.signal_id,
        payload_hash=signal.payload_hash,
        symbol=symbol,
        side=sides[action],
        qty=qty_text,
        expires_us=expires_us,
    )


def _checked_action_map(action_map: tuple[tuple[str, str], ...]) -> dict[str, str]:
    if not isinstance(action_map, tuple) or not action_map:
        raise SignalCandidateBindingError(
            "SIGNAL_CANDIDATE_MAP_INVALID", "Action eşlemesi boş olamaz."
        )
    sides: dict[str, str] = {}
    for entry in action_map:
        if (
            not isinstance(entry, tuple)
            or len(entry) != 2
            or not all(isinstance(v, str) and v for v in entry)
        ):
            raise SignalCandidateBindingError(
                "SIGNAL_CANDIDATE_MAP_INVALID",
                "Eşleme (action, side) string tuple olmalıdır.",
            )
        mapped_action, side = entry
        if side not in _SIDES:
            raise SignalCandidateBindingError(
                "SIGNAL_CANDIDATE_MAP_INVALID",
                "Side yalnız BUY veya SELL olabilir.",
            )
        if mapped_action in sides:
            raise SignalCandidateBindingError(
                "SIGNAL_CANDIDATE_MAP_INVALID",
                "Aynı action iki kez eşlenemez.",
            )
        sides[mapped_action] = side
    return sides
