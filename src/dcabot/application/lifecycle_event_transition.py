"""Pure adapter from accepted lifecycle events to lifecycle projections."""

from dcabot.application.deal_lifecycle import (
    DealLifecycle,
    transition_deal_lifecycle,
)
from dcabot.application.lifecycle_event_contract import (
    LifecycleEvent,
    LifecycleEventContractError,
    accept_lifecycle_event,
)


def apply_lifecycle_event(
    lifecycle: DealLifecycle,
    history: tuple[LifecycleEvent, ...],
    event: LifecycleEvent,
) -> tuple[DealLifecycle, tuple[LifecycleEvent, ...], str]:
    """Apply one lifecycle event without persistence or economic mutation.

    Identity/scope/order validation happens before transition. A rejected
    transition therefore cannot append an event to the returned history.
    """

    if not isinstance(lifecycle, DealLifecycle):
        raise LifecycleEventContractError(
            "LIFECYCLE_PROJECTION_INVALID", "Lifecycle projection geçersiz."
        )
    if not isinstance(event, LifecycleEvent):
        raise LifecycleEventContractError(
            "LIFECYCLE_EVENT_INVALID", "Lifecycle event kaydı geçersiz."
        )
    if (event.deal_id, event.config_revision_id) != (
        lifecycle.deal_id,
        lifecycle.config_revision_id,
    ):
        raise LifecycleEventContractError(
            "LIFECYCLE_EVENT_SCOPE_CONFLICT",
            "Event mevcut lifecycle scope’una ait değil.",
        )
    if not history and lifecycle.event_sequence != 0:
        raise LifecycleEventContractError(
            "LIFECYCLE_PROJECTION_OUT_OF_SYNC",
            "Lifecycle projection event geçmişiyle uyumsuz.",
        )
    if history and history[-1].event_sequence != lifecycle.event_sequence:
        raise LifecycleEventContractError(
            "LIFECYCLE_PROJECTION_OUT_OF_SYNC",
            "Lifecycle projection event geçmişiyle uyumsuz.",
        )

    candidate_history, outcome = accept_lifecycle_event(history, event)
    if outcome == "DUPLICATE":
        return lifecycle, history, outcome

    next_lifecycle = transition_deal_lifecycle(lifecycle, event.event)
    return next_lifecycle, candidate_history, outcome
