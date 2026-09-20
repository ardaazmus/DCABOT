"""Offline Futures DCA exit-trigger priority contract."""

from dataclasses import dataclass
from enum import StrEnum


class FuturesDcaExitPriorityError(ValueError):
    """Raised when an exit-priority decision is not representable safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class FuturesDcaExitTrigger(StrEnum):
    """Independent trigger observations; none of them is an order."""

    STOP_LOSS = "STOP_LOSS"
    TRAILING_STOP = "TRAILING_STOP"
    TAKE_PROFIT = "TAKE_PROFIT"
    BREAKEVEN_ADJUSTMENT = "BREAKEVEN_ADJUSTMENT"


class FuturesDcaExitDecision(StrEnum):
    """Pure action class selected from simultaneous trigger observations."""

    NO_TRIGGER = "NO_TRIGGER"
    CLOSE = "CLOSE"
    ADJUST_STOP = "ADJUST_STOP"


_PRIORITY = (
    FuturesDcaExitTrigger.STOP_LOSS,
    FuturesDcaExitTrigger.TRAILING_STOP,
    FuturesDcaExitTrigger.TAKE_PROFIT,
    FuturesDcaExitTrigger.BREAKEVEN_ADJUSTMENT,
)


@dataclass(frozen=True, slots=True)
class FuturesDcaExitPriorityEvaluation:
    """Deterministic trigger choice without execution or fill authority."""

    observed_triggers: tuple[FuturesDcaExitTrigger, ...]
    selected_trigger: FuturesDcaExitTrigger | None
    suppressed_triggers: tuple[FuturesDcaExitTrigger, ...]
    decision: FuturesDcaExitDecision
    reason: str
    order_authority: str = "NONE"

    def __post_init__(self) -> None:
        if self.order_authority != "NONE":
            raise FuturesDcaExitPriorityError(
                "FUTURES_DCA_EXIT_PRIORITY_AUTHORITY_INVALID",
                "Exit priority order authority taşıyamaz.",
            )
        if self.selected_trigger is None and self.suppressed_triggers:
            raise FuturesDcaExitPriorityError(
                "FUTURES_DCA_EXIT_PRIORITY_RESULT_INVALID",
                "Seçilmiş trigger olmadan suppressed trigger bulunamaz.",
            )
        if self.selected_trigger is not None and self.selected_trigger in self.suppressed_triggers:
            raise FuturesDcaExitPriorityError(
                "FUTURES_DCA_EXIT_PRIORITY_RESULT_INVALID",
                "Seçilmiş trigger suppressed listesinde tekrarlanamaz.",
            )


def assess_futures_dca_exit_priority(
    triggered: tuple[FuturesDcaExitTrigger | str, ...],
) -> FuturesDcaExitPriorityEvaluation:
    """Choose one deterministic outcome for simultaneous trigger evidence.

    The local safety policy is STOP_LOSS, TRAILING_STOP, TAKE_PROFIT, then
    BREAKEVEN_ADJUSTMENT. Breakeven is a stop adjustment, not a close. When a
    close trigger exists it suppresses the adjustment; this function does not
    create, cancel, replace, or fill an order.
    """

    if not isinstance(triggered, tuple):
        raise FuturesDcaExitPriorityError(
            "FUTURES_DCA_EXIT_PRIORITY_INPUT_INVALID",
            "Trigger listesi immutable tuple olmalıdır.",
        )
    try:
        normalized = tuple(FuturesDcaExitTrigger(item) for item in triggered)
    except (TypeError, ValueError) as error:
        raise FuturesDcaExitPriorityError(
            "FUTURES_DCA_EXIT_TRIGGER_INVALID",
            "Trigger yalnız STOP_LOSS, TRAILING_STOP, TAKE_PROFIT veya BREAKEVEN_ADJUSTMENT olabilir.",
        ) from error
    if len(set(normalized)) != len(normalized):
        raise FuturesDcaExitPriorityError(
            "FUTURES_DCA_EXIT_TRIGGER_DUPLICATE",
            "Aynı gözlemde aynı trigger türü birden fazla taşınamaz.",
        )
    ordered = tuple(trigger for trigger in _PRIORITY if trigger in normalized)
    selected = ordered[0] if ordered else None
    suppressed = ordered[1:]
    if selected is None:
        decision = FuturesDcaExitDecision.NO_TRIGGER
        reason = "NO_EXIT_TRIGGER"
    elif selected is FuturesDcaExitTrigger.BREAKEVEN_ADJUSTMENT:
        decision = FuturesDcaExitDecision.ADJUST_STOP
        reason = "BREAKEVEN_ADJUSTMENT_ONLY"
    else:
        decision = FuturesDcaExitDecision.CLOSE
        reason = f"{selected}_HAS_PRIORITY"
    return FuturesDcaExitPriorityEvaluation(
        observed_triggers=ordered,
        selected_trigger=selected,
        suppressed_triggers=suppressed,
        decision=decision,
        reason=reason,
    )
