"""Immutable, event-time ordered signal identity and deduplication contract."""

from dataclasses import dataclass
import re
from typing import Final


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_SIGNAL_SCHEMA: Final = "signal-v1"


class SignalEventContractError(ValueError):
    """Raised when a signal identity, event time, or replay is invalid."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class SignalEvent:
    """An immutable source signal without candidate or economic authority."""

    signal_id: str
    source: str
    event_time_us: int
    schema_version: str
    payload_hash: str

    def __post_init__(self) -> None:
        _validate_identifier(self.signal_id, "SIGNAL_ID_INVALID")
        _validate_identifier(self.source, "SIGNAL_SOURCE_INVALID")
        if type(self.event_time_us) is not int or self.event_time_us < 0:
            raise SignalEventContractError(
                "SIGNAL_EVENT_TIME_INVALID",
                "Signal event_time_us sıfır veya pozitif integer olmalıdır.",
            )
        if self.schema_version != _SIGNAL_SCHEMA:
            raise SignalEventContractError(
                "SIGNAL_SCHEMA_INVALID",
                "Yalnız desteklenen signal-v1 şeması kabul edilir.",
            )
        if not isinstance(self.payload_hash, str) or _SHA256.fullmatch(
            self.payload_hash
        ) is None:
            raise SignalEventContractError(
                "SIGNAL_PAYLOAD_HASH_INVALID",
                "Payload hash küçük harfli SHA-256 hex olmalıdır.",
            )


def new_signal_event(
    *,
    signal_id: str,
    source: str,
    event_time_us: int,
    schema_version: str,
    payload_hash: str,
) -> SignalEvent:
    """Validate and construct one caller-identified source signal."""

    return SignalEvent(
        signal_id=signal_id,
        source=source,
        event_time_us=event_time_us,
        schema_version=schema_version,
        payload_hash=payload_hash,
    )


def accept_signal(
    history: tuple[SignalEvent, ...], event: SignalEvent
) -> tuple[tuple[SignalEvent, ...], str]:
    """Return accepted signal history and explicit duplicate outcome.

    Signal event time is the source time and is never replaced by processing
    or wall-clock time. An exact repeated identity is a no-op; a reused ID
    with any different immutable field is a conflict. Older new signals are
    rejected by the explicit stale policy.
    """

    if not isinstance(history, tuple) or any(
        not isinstance(item, SignalEvent) for item in history
    ):
        raise SignalEventContractError(
            "SIGNAL_HISTORY_INVALID", "Signal geçmişi tuple ve geçerli eventlerden oluşmalıdır."
        )
    if not isinstance(event, SignalEvent):
        raise SignalEventContractError(
            "SIGNAL_EVENT_INVALID", "Signal event kaydı geçersiz."
        )
    if any(
        right.event_time_us < left.event_time_us
        for left, right in zip(history, history[1:])
    ):
        raise SignalEventContractError(
            "SIGNAL_HISTORY_ORDER_INVALID",
            "Signal geçmişi event_time_us sırasını korumalıdır.",
        )

    for prior in history:
        if prior.signal_id == event.signal_id:
            if prior == event:
                return history, "DUPLICATE"
            raise SignalEventContractError(
                "SIGNAL_EVENT_CONFLICT",
                "Aynı signal kimliği farklı payload veya metadata ile kullanılamaz.",
            )

    if history and event.event_time_us < history[-1].event_time_us:
        raise SignalEventContractError(
            "SIGNAL_EVENT_STALE",
            "Yeni signal event_time_us son kabul edilen zamandan eski olamaz.",
        )
    return (*history, event), "ACCEPTED"


def _validate_identifier(value: str, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise SignalEventContractError(code, "Signal kimliği/source değeri geçersiz.")
