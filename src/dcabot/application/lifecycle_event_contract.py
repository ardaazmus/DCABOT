"""Pure identity and ordering contract for future lifecycle events."""

from dataclasses import dataclass
import re
from typing import Final


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
_EVENTS: Final = frozenset({"START", "PAUSE", "RESUME", "COMPLETE", "ABORT", "FAIL"})


class LifecycleEventContractError(ValueError):
    """Raised when lifecycle event identity, scope, or order is invalid."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    """Immutable lifecycle event record without economic meaning or storage."""

    event_id: str
    deal_id: str
    config_revision_id: str
    event: str
    event_sequence: int

    def __post_init__(self) -> None:
        _validate_identifier(self.event_id, "LIFECYCLE_EVENT_ID_INVALID")
        _validate_identifier(self.deal_id, "DEAL_ID_INVALID")
        _validate_identifier(self.config_revision_id, "CONFIG_REVISION_ID_INVALID")
        if not isinstance(self.event, str) or self.event not in _EVENTS:
            raise LifecycleEventContractError(
                "LIFECYCLE_EVENT_TYPE_INVALID", "Lifecycle olay türü geçersiz."
            )
        if type(self.event_sequence) is not int or self.event_sequence < 1:
            raise LifecycleEventContractError(
                "LIFECYCLE_EVENT_SEQUENCE_INVALID", "Lifecycle olay sırası pozitif olmalıdır."
            )


def new_lifecycle_event(
    event_id: str,
    deal_id: str,
    config_revision_id: str,
    event: str,
    event_sequence: int,
) -> LifecycleEvent:
    """Validate and construct one caller-identified lifecycle event."""

    _validate_identifier(event_id, "LIFECYCLE_EVENT_ID_INVALID")
    _validate_identifier(deal_id, "DEAL_ID_INVALID")
    _validate_identifier(config_revision_id, "CONFIG_REVISION_ID_INVALID")
    if not isinstance(event, str) or event not in _EVENTS:
        raise LifecycleEventContractError(
            "LIFECYCLE_EVENT_TYPE_INVALID", "Lifecycle olay türü geçersiz."
        )
    if type(event_sequence) is not int or event_sequence < 1:
        raise LifecycleEventContractError(
            "LIFECYCLE_EVENT_SEQUENCE_INVALID", "Lifecycle olay sırası pozitif olmalıdır."
        )
    return LifecycleEvent(
        event_id=event_id,
        deal_id=deal_id,
        config_revision_id=config_revision_id,
        event=event,
        event_sequence=event_sequence,
    )


def accept_lifecycle_event(
    history: tuple[LifecycleEvent, ...], event: LifecycleEvent
) -> tuple[tuple[LifecycleEvent, ...], str]:
    """Return accepted history and outcome for one non-persistent event.

    The same event ID is idempotent only when every immutable field matches.
    Lifecycle state transition remains owned by the lifecycle reducer; this
    function only checks identity, deal/revision scope, and sequence order.
    """

    if not isinstance(history, tuple) or any(
        not isinstance(item, LifecycleEvent) for item in history
    ):
        raise LifecycleEventContractError(
            "LIFECYCLE_HISTORY_INVALID", "Lifecycle event geçmişi geçersiz."
        )
    if not isinstance(event, LifecycleEvent):
        raise LifecycleEventContractError(
            "LIFECYCLE_EVENT_INVALID", "Lifecycle event kaydı geçersiz."
        )

    for prior in history:
        if prior.event_id == event.event_id:
            if prior == event:
                return history, "DUPLICATE"
            raise LifecycleEventContractError(
                "LIFECYCLE_EVENT_CONFLICT",
                "Aynı lifecycle event kimliği farklı kayıtla kullanılamaz.",
            )

    if history:
        first = history[0]
        if (event.deal_id, event.config_revision_id) != (
            first.deal_id,
            first.config_revision_id,
        ):
            raise LifecycleEventContractError(
                "LIFECYCLE_EVENT_SCOPE_CONFLICT",
                "Lifecycle event başka deal veya config revision kapsamına ait.",
            )
        if event.event_sequence != history[-1].event_sequence + 1:
            raise LifecycleEventContractError(
                "LIFECYCLE_EVENT_SEQUENCE_INVALID",
                "Lifecycle event sırası ardışık olmalıdır.",
            )
    elif event.event_sequence != 1:
        raise LifecycleEventContractError(
            "LIFECYCLE_EVENT_SEQUENCE_INVALID",
            "İlk lifecycle event sırası 1 olmalıdır.",
        )

    return (*history, event), "ACCEPTED"


def _validate_identifier(value: str, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise LifecycleEventContractError(code, "Lifecycle kimliği geçersiz.")
