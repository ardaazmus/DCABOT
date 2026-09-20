"""Pure identity and ordering contract for offline Futures DCA fills."""

from dataclasses import dataclass
import re

from dcabot.application.futures_dca_fill_projection import FuturesDcaFill


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)


class FuturesDcaEventError(ValueError):
    """Raised when a Futures DCA event identity, scope, or order is invalid."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FuturesDcaFillEvent:
    """Immutable local fill event; it is not a venue transport sequence."""

    event_id: str
    deal_id: str
    config_revision_id: str
    event_sequence: int
    fill: FuturesDcaFill

    def __post_init__(self) -> None:
        for value, code in (
            (self.event_id, "FUTURES_DCA_EVENT_ID_INVALID"),
            (self.deal_id, "FUTURES_DCA_DEAL_ID_INVALID"),
            (self.config_revision_id, "FUTURES_DCA_CONFIG_REVISION_INVALID"),
        ):
            _validate_identifier(value, code)
        if type(self.event_sequence) is not int or self.event_sequence < 1:
            raise FuturesDcaEventError("FUTURES_DCA_EVENT_SEQUENCE_INVALID", "Event sırası pozitif olmalıdır.")
        if not isinstance(self.fill, FuturesDcaFill):
            raise FuturesDcaEventError("FUTURES_DCA_FILL_INVALID", "Event fill güvenli tipte olmalıdır.")


def new_futures_dca_fill_event(
    event_id: str,
    deal_id: str,
    config_revision_id: str,
    event_sequence: int,
    fill: FuturesDcaFill,
) -> FuturesDcaFillEvent:
    """Construct one validated local Futures DCA fill event."""

    return FuturesDcaFillEvent(event_id, deal_id, config_revision_id, event_sequence, fill)


def accept_futures_dca_fill_event(
    history: tuple[FuturesDcaFillEvent, ...], event: FuturesDcaFillEvent
) -> tuple[tuple[FuturesDcaFillEvent, ...], str]:
    """Accept one event with exact duplicate, scope, sequence and fill dedupe checks."""

    if not isinstance(history, tuple) or any(not isinstance(item, FuturesDcaFillEvent) for item in history):
        raise FuturesDcaEventError("FUTURES_DCA_HISTORY_INVALID", "Event geçmişi immutable tuple olmalıdır.")
    if not isinstance(event, FuturesDcaFillEvent):
        raise FuturesDcaEventError("FUTURES_DCA_EVENT_INVALID", "Event güvenli tipte olmalıdır.")
    for prior in history:
        if prior.event_id == event.event_id:
            if prior == event:
                return history, "DUPLICATE"
            raise FuturesDcaEventError("FUTURES_DCA_EVENT_CONFLICT", "Aynı event kimliği farklı kayıtla kullanılamaz.")
        if prior.fill.execution_id == event.fill.execution_id:
            raise FuturesDcaEventError("FUTURES_DCA_EXECUTION_CONFLICT", "Aynı execution kimliği ikinci event’e bağlanamaz.")
    if history:
        first = history[0]
        if (event.deal_id, event.config_revision_id) != (first.deal_id, first.config_revision_id):
            raise FuturesDcaEventError("FUTURES_DCA_EVENT_SCOPE_CONFLICT", "Event başka deal veya config revision kapsamına ait.")
        if event.event_sequence != history[-1].event_sequence + 1:
            raise FuturesDcaEventError("FUTURES_DCA_EVENT_SEQUENCE_INVALID", "Event sırası ardışık olmalıdır.")
    elif event.event_sequence != 1:
        raise FuturesDcaEventError("FUTURES_DCA_EVENT_SEQUENCE_INVALID", "İlk event sırası 1 olmalıdır.")
    return (*history, event), "ACCEPTED"


def _validate_identifier(value: object, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise FuturesDcaEventError(code, "Event scope kimliği geçersiz.")
