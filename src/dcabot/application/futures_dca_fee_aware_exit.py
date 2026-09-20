"""Offline fee-aware Futures DCA exit-candidate contract."""

from dataclasses import dataclass

from dcabot.application.futures_dca_breakeven_contract import (
    FuturesDcaBreakevenError,
    FuturesDcaBreakevenStatus,
    FuturesDcaFeeAwareProfile,
    assess_futures_dca_breakeven,
)
from dcabot.application.futures_dca_exit_candidate import (
    FuturesDcaExitCandidateError,
    bind_futures_dca_exit_candidate,
)
from dcabot.application.futures_dca_exit_priority import (
    FuturesDcaExitPriorityEvaluation,
    FuturesDcaExitTrigger,
)
from dcabot.application.futures_dca_fill_projection import FuturesDcaFillProjection


_ROUNDING_MODE = "EXACT_NO_ROUNDING"


@dataclass(frozen=True, slots=True)
class FuturesDcaFeeAwareExitCandidate:
    """Exact fee-aware TP candidate with no order authority."""

    selected_trigger: FuturesDcaExitTrigger
    trigger_price: str
    requested_qty: str
    remaining_capacity: str
    gross_breakeven_price: str
    fee_aware_breakeven_price: str
    fee_profile_revision: str
    rounding_mode: str = _ROUNDING_MODE
    order_authority: str = "NONE"

    def __post_init__(self) -> None:
        if self.rounding_mode != _ROUNDING_MODE:
            raise FuturesDcaBreakevenError(
                "FUTURES_DCA_FEE_AWARE_ROUNDING_INVALID",
                "Fee-aware exit adayı sessiz rounding politikası taşıyamaz.",
            )
        if self.order_authority != "NONE":
            raise FuturesDcaExitCandidateError(
                "FUTURES_DCA_FEE_AWARE_EXIT_AUTHORITY_INVALID",
                "Fee-aware exit adayı order authority taşıyamaz.",
            )


def bind_futures_dca_fee_aware_exit_candidate(
    fill_projection: FuturesDcaFillProjection,
    priority: FuturesDcaExitPriorityEvaluation,
    *,
    fee_profile: FuturesDcaFeeAwareProfile | None,
    requested_qty: str,
    accepted_exit_fills: tuple[str, ...],
    committed_exit_qty: tuple[str, ...],
) -> FuturesDcaFeeAwareExitCandidate:
    """Bind an exact fee-aware breakeven boundary to a TAKE_PROFIT candidate.

    Fee-aware breakeven is a TP boundary, not a stop or trailing trigger. An
    incomplete or off-grid boundary remains blocked; this function never
    rounds it down or up.
    """

    evaluation = assess_futures_dca_breakeven(
        fill_projection,
        fee_profile=fee_profile,
    )
    if evaluation.status is not FuturesDcaBreakevenStatus.FEE_AWARE_READY:
        raise FuturesDcaBreakevenError(
            "FUTURES_DCA_FEE_AWARE_EXIT_BLOCKED",
            evaluation.reason,
        )
    if (
        isinstance(priority, FuturesDcaExitPriorityEvaluation)
        and priority.selected_trigger is not FuturesDcaExitTrigger.TAKE_PROFIT
    ):
        raise FuturesDcaExitCandidateError(
            "FUTURES_DCA_FEE_AWARE_EXIT_TRIGGER_UNSUPPORTED",
            "Fee-aware breakeven yalnız TAKE_PROFIT exit adayına bağlanabilir.",
        )
    if evaluation.fee_aware_breakeven_price is None or fee_profile is None:
        raise FuturesDcaBreakevenError(
            "FUTURES_DCA_FEE_AWARE_EXIT_RESULT_INVALID",
            "Fee-aware exit adayı için hazır exact boundary ve profil gereklidir.",
        )
    candidate = bind_futures_dca_exit_candidate(
        fill_projection,
        priority,
        trigger_price=evaluation.fee_aware_breakeven_price,
        requested_qty=requested_qty,
        accepted_exit_fills=accepted_exit_fills,
        committed_exit_qty=committed_exit_qty,
    )
    return FuturesDcaFeeAwareExitCandidate(
        selected_trigger=candidate.selected_trigger,
        trigger_price=candidate.trigger_price,
        requested_qty=candidate.requested_qty,
        remaining_capacity=candidate.remaining_capacity,
        gross_breakeven_price=evaluation.gross_breakeven_price,
        fee_aware_breakeven_price=evaluation.fee_aware_breakeven_price,
        fee_profile_revision=fee_profile.profile_revision,
        rounding_mode=fee_profile.rounding_mode,
    )
