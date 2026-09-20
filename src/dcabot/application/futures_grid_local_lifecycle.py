"""Deterministic, non-economic Futures Grid lifecycle simulation."""

from dataclasses import dataclass
from enum import StrEnum
import re


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)


class FuturesGridLocalLifecycleError(ValueError):
    """Raised when a local lifecycle event violates its bounded contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class FuturesGridLocalEventType(StrEnum):
    """Offline observations accepted by the local lifecycle reducer."""

    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCEL_CONFIRMED = "CANCEL_CONFIRMED"
    REPLACEMENT_REQUESTED = "REPLACEMENT_REQUESTED"
    FILL_ACCEPTED = "FILL_ACCEPTED"
    UNKNOWN_OBSERVATION = "UNKNOWN_OBSERVATION"
    CONFLICT_OBSERVATION = "CONFLICT_OBSERVATION"


class FuturesGridLocalLifecycleStatus(StrEnum):
    """Non-economic lifecycle statuses used only by the offline simulator."""

    OPEN = "OPEN"
    CANCEL_PENDING = "CANCEL_PENDING"
    CANCELED = "CANCELED"
    REPLACEMENT_READY = "REPLACEMENT_READY"
    FILLED = "FILLED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True, slots=True)
class FuturesGridLocalEvent:
    """An immutable local observation; it is not an exchange order event."""

    event_id: str
    event_type: FuturesGridLocalEventType
    event_sequence: int
    fill_id: str | None


@dataclass(frozen=True, slots=True)
class FuturesGridLocalLifecycle:
    """Pure lifecycle projection with no order, reserve, or persistence fields."""

    status: FuturesGridLocalLifecycleStatus
    events: tuple[FuturesGridLocalEvent, ...]
    fill_ids: tuple[str, ...]
    replacement_admitted: bool


def new_futures_grid_local_event(
    event_id: str,
    event_type: FuturesGridLocalEventType,
    event_sequence: int,
    fill_id: str | None = None,
) -> FuturesGridLocalEvent:
    """Construct one validated local observation."""

    _validate_identifier(event_id, "FUTURES_GRID_LOCAL_EVENT_ID_INVALID")
    if not isinstance(event_type, FuturesGridLocalEventType):
        raise FuturesGridLocalLifecycleError(
            "FUTURES_GRID_LOCAL_EVENT_TYPE_INVALID",
            "Yerel lifecycle event tipi güvenli enum değeri olmalıdır.",
        )
    if type(event_sequence) is not int or event_sequence < 1:
        raise FuturesGridLocalLifecycleError(
            "FUTURES_GRID_LOCAL_EVENT_SEQUENCE_INVALID",
            "Yerel lifecycle event sırası pozitif integer olmalıdır.",
        )
    if event_type is FuturesGridLocalEventType.FILL_ACCEPTED:
        _validate_identifier(fill_id, "FUTURES_GRID_LOCAL_FILL_ID_INVALID")
    elif fill_id is not None:
        raise FuturesGridLocalLifecycleError(
            "FUTURES_GRID_LOCAL_FILL_ID_UNEXPECTED",
            "Fill ID yalnız FILL_ACCEPTED gözleminde bulunabilir.",
        )
    return FuturesGridLocalEvent(event_id, event_type, event_sequence, fill_id)


def new_futures_grid_local_lifecycle() -> FuturesGridLocalLifecycle:
    """Start a local offline lifecycle projection in the OPEN state."""

    return FuturesGridLocalLifecycle(
        status=FuturesGridLocalLifecycleStatus.OPEN,
        events=(),
        fill_ids=(),
        replacement_admitted=False,
    )


def apply_futures_grid_local_event(
    state: FuturesGridLocalLifecycle, event: FuturesGridLocalEvent
) -> tuple[FuturesGridLocalLifecycle, str]:
    """Apply one local observation without external side effects.

    A fill wins a cancel race, replacement waits for cancel confirmation, and
    unknown/conflicting observations quarantine the projection. Repeated fill
    identities are ignored without changing the local state.
    """

    if not isinstance(state, FuturesGridLocalLifecycle):
        raise FuturesGridLocalLifecycleError(
            "FUTURES_GRID_LOCAL_STATE_INVALID", "Yerel lifecycle state geçersiz."
        )
    if not isinstance(event, FuturesGridLocalEvent):
        raise FuturesGridLocalLifecycleError(
            "FUTURES_GRID_LOCAL_EVENT_INVALID", "Yerel lifecycle event geçersiz."
        )
    if state.status is FuturesGridLocalLifecycleStatus.QUARANTINED:
        return state, "BLOCKED_QUARANTINED"
    if event.event_sequence != len(state.events) + 1:
        raise FuturesGridLocalLifecycleError(
            "FUTURES_GRID_LOCAL_EVENT_SEQUENCE_INVALID",
            "Yerel lifecycle event sırası ardışık olmalıdır.",
        )
    for prior in state.events:
        if prior.event_id == event.event_id:
            if prior == event:
                return state, "DUPLICATE"
            return _quarantine(state), "QUARANTINED"

    if event.event_type is FuturesGridLocalEventType.FILL_ACCEPTED:
        if event.fill_id in state.fill_ids:
            return state, "DUPLICATE"
        return _append(
            state,
            event,
            status=FuturesGridLocalLifecycleStatus.FILLED,
            fill_id=event.fill_id,
        ), "ACCEPTED"
    if event.event_type is FuturesGridLocalEventType.UNKNOWN_OBSERVATION:
        return _quarantine(state), "QUARANTINED"
    if event.event_type is FuturesGridLocalEventType.CONFLICT_OBSERVATION:
        return _quarantine(state), "QUARANTINED"
    if event.event_type is FuturesGridLocalEventType.CANCEL_REQUESTED:
        if state.status not in (
            FuturesGridLocalLifecycleStatus.OPEN,
            FuturesGridLocalLifecycleStatus.CANCEL_PENDING,
        ):
            return _quarantine(state), "QUARANTINED"
        return _append(
            state,
            event,
            status=FuturesGridLocalLifecycleStatus.CANCEL_PENDING,
        ), "ACCEPTED"
    if event.event_type is FuturesGridLocalEventType.CANCEL_CONFIRMED:
        if state.status is not FuturesGridLocalLifecycleStatus.CANCEL_PENDING:
            return _quarantine(state), "QUARANTINED"
        return _append(
            state,
            event,
            status=FuturesGridLocalLifecycleStatus.CANCELED,
        ), "ACCEPTED"
    if event.event_type is FuturesGridLocalEventType.REPLACEMENT_REQUESTED:
        if state.status is not FuturesGridLocalLifecycleStatus.CANCELED:
            return _quarantine(state), "QUARANTINED"
        return _append(
            state,
            event,
            status=FuturesGridLocalLifecycleStatus.REPLACEMENT_READY,
            replacement_admitted=True,
        ), "ACCEPTED"
    raise FuturesGridLocalLifecycleError(
        "FUTURES_GRID_LOCAL_EVENT_UNSUPPORTED",
        "Yerel lifecycle event tipi desteklenmiyor.",
    )


def replay_futures_grid_local_events(
    events: tuple[FuturesGridLocalEvent, ...],
) -> tuple[FuturesGridLocalLifecycle, tuple[str, ...]]:
    """Replay bounded local observations deterministically in memory."""

    if not isinstance(events, tuple) or any(
        not isinstance(event, FuturesGridLocalEvent) for event in events
    ):
        raise FuturesGridLocalLifecycleError(
            "FUTURES_GRID_LOCAL_EVENTS_INVALID",
            "Replay girdisi immutable event tuple olmalıdır.",
        )
    state = new_futures_grid_local_lifecycle()
    outcomes: list[str] = []
    for event in events:
        state, outcome = apply_futures_grid_local_event(state, event)
        outcomes.append(outcome)
    return state, tuple(outcomes)


def _append(
    state: FuturesGridLocalLifecycle,
    event: FuturesGridLocalEvent,
    *,
    status: FuturesGridLocalLifecycleStatus,
    fill_id: str | None = None,
    replacement_admitted: bool | None = None,
) -> FuturesGridLocalLifecycle:
    return FuturesGridLocalLifecycle(
        status=status,
        events=state.events + (event,),
        fill_ids=state.fill_ids + ((fill_id,) if fill_id is not None else ()),
        replacement_admitted=(
            state.replacement_admitted
            if replacement_admitted is None
            else replacement_admitted
        ),
    )


def _quarantine(state: FuturesGridLocalLifecycle) -> FuturesGridLocalLifecycle:
    return FuturesGridLocalLifecycle(
        status=FuturesGridLocalLifecycleStatus.QUARANTINED,
        events=state.events,
        fill_ids=state.fill_ids,
        replacement_admitted=state.replacement_admitted,
    )


def _validate_identifier(value: str | None, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise FuturesGridLocalLifecycleError(code, "Kimlik güvenli biçimde geçersiz.")
