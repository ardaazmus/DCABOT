"""Offline Futures DCA exit-candidate and position-capacity contract."""

from dataclasses import dataclass

from dcabot.application.futures_dca_exit_priority import (
    FuturesDcaExitDecision,
    FuturesDcaExitPriorityEvaluation,
    FuturesDcaExitTrigger,
)
from dcabot.application.futures_dca_fill_projection import FuturesDcaFillProjection
from dcabot.application.multi_tp_conservation import (
    ExitCapacityError,
    validate_exit_capacity,
)
from dcabot.domain.numbers import align, exact_text, number, positive


class FuturesDcaExitCandidateError(ValueError):
    """Raised when a selected exit cannot become a safe local candidate."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FuturesDcaExitCandidate:
    """Selected close trigger and conserved capacity without order authority."""

    selected_trigger: FuturesDcaExitTrigger
    trigger_price: str
    requested_qty: str
    remaining_capacity: str
    order_authority: str = "NONE"

    def __post_init__(self) -> None:
        if self.order_authority != "NONE":
            raise FuturesDcaExitCandidateError(
                "FUTURES_DCA_EXIT_CANDIDATE_AUTHORITY_INVALID",
                "Exit adayı order authority taşıyamaz.",
            )


def bind_futures_dca_exit_candidate(
    fill_projection: FuturesDcaFillProjection,
    priority: FuturesDcaExitPriorityEvaluation,
    *,
    trigger_price: str,
    requested_qty: str,
    accepted_exit_fills: tuple[str, ...],
    committed_exit_qty: tuple[str, ...],
) -> FuturesDcaExitCandidate:
    """Bind one selected close trigger to exact price and free capacity.

    The trigger price is supplied by the relevant trigger projection (for
    example the TP projection or trailing state). This function only verifies
    its exact tick representation and proves that the requested candidate does
    not over-close the observed position.
    """

    if not isinstance(fill_projection, FuturesDcaFillProjection):
        raise FuturesDcaExitCandidateError(
            "FUTURES_DCA_EXIT_CANDIDATE_FILL_PROJECTION_INVALID",
            "Fill projection güvenli Futures DCA tipinde olmalıdır.",
        )
    if fill_projection.average_entry is None:
        raise FuturesDcaExitCandidateError(
            "FUTURES_DCA_EXIT_CANDIDATE_POSITION_EMPTY",
            "Exit adayı için gözlenmiş pozisyon gereklidir.",
        )
    if not isinstance(priority, FuturesDcaExitPriorityEvaluation):
        raise FuturesDcaExitCandidateError(
            "FUTURES_DCA_EXIT_CANDIDATE_PRIORITY_INVALID",
            "Exit öncelik değerlendirmesi güvenli tipte olmalıdır.",
        )
    close_triggers = {
        FuturesDcaExitTrigger.STOP_LOSS,
        FuturesDcaExitTrigger.TRAILING_STOP,
        FuturesDcaExitTrigger.TAKE_PROFIT,
    }
    if (
        priority.decision is not FuturesDcaExitDecision.CLOSE
        or priority.selected_trigger not in close_triggers
    ):
        raise FuturesDcaExitCandidateError(
            "FUTURES_DCA_EXIT_CANDIDATE_NO_CLOSE_TRIGGER",
            "Yalnız seçilmiş CLOSE trigger exit adayı üretebilir.",
        )
    if not isinstance(accepted_exit_fills, tuple) or not isinstance(
        committed_exit_qty, tuple
    ):
        raise FuturesDcaExitCandidateError(
            "FUTURES_DCA_EXIT_CANDIDATE_INPUT_INVALID",
            "Exit miktarları immutable tuple olmalıdır.",
        )
    try:
        price = positive(trigger_price)
        tick = positive(fill_projection.plan.price_tick)
        requested = exact_text(positive(requested_qty))
        normalized_price = exact_text(price)
    except ValueError as error:
        raise FuturesDcaExitCandidateError(
            "FUTURES_DCA_EXIT_CANDIDATE_NUMERIC_INVALID",
            "Trigger fiyatı, tick ve requested miktar exact decimal olmalıdır.",
        ) from error
    if align(number(normalized_price), tick, up=False) != number(normalized_price):
        raise FuturesDcaExitCandidateError(
            "FUTURES_DCA_EXIT_CANDIDATE_OFF_GRID",
            "Exit trigger fiyatı price tick üzerinde exact temsil edilmelidir.",
        )
    try:
        capacity = validate_exit_capacity(
            open_qty=fill_projection.position_quantity,
            accepted_exit_fills=accepted_exit_fills,
            committed_exit_qty=(*committed_exit_qty, requested),
        )
    except ExitCapacityError as error:
        raise FuturesDcaExitCandidateError(error.code, str(error)) from error
    return FuturesDcaExitCandidate(
        selected_trigger=priority.selected_trigger,
        trigger_price=normalized_price,
        requested_qty=requested,
        remaining_capacity=capacity.free_exit_capacity,
    )
