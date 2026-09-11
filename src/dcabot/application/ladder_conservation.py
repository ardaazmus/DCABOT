"""Exact, pre-quantization conservation contract for ladder allocations."""

from dataclasses import dataclass

from dcabot.domain.numbers import Q, bounded, exact_text, positive


class LadderConservationError(ValueError):
    """Raised when ladder allocations violate their unit or budget contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class LadderConservation:
    """Exact allocation total and remaining budget in one declared unit."""

    allocation_unit: str
    total_allocated: str
    budget: str
    remaining_budget: str


def validate_ladder_allocations(
    *, allocation_unit: str, allocations: tuple[str, ...], budget: str
) -> LadderConservation:
    """Validate and sum positive ladder allocations without venue rounding.

    Every allocation and the budget share the explicit BASE or QUOTE unit.
    This function only checks exact conservation; it does not quantize orders,
    inspect instrument metadata, accept risk, or post an economic event.
    """

    if allocation_unit not in ("BASE_QTY", "QUOTE_NOTIONAL"):
        raise LadderConservationError(
            "LADDER_UNIT_INVALID",
            "Ladder unit BASE_QTY veya QUOTE_NOTIONAL olmalıdır.",
        )
    try:
        parsed_budget = positive(budget)
    except ValueError as error:
        raise LadderConservationError(
            "LADDER_BUDGET_INVALID", "Ladder budget pozitif decimal string olmalıdır."
        ) from error
    if not isinstance(allocations, tuple) or any(
        not isinstance(allocation, str) for allocation in allocations
    ):
        raise LadderConservationError(
            "LADDER_ALLOCATION_INVALID",
            "Ladder allocations decimal string tuple olmalıdır.",
        )
    try:
        parsed_allocations = tuple(positive(allocation) for allocation in allocations)
    except ValueError as error:
        raise LadderConservationError(
            "LADDER_ALLOCATION_INVALID",
            "Her ladder allocation pozitif decimal string olmalıdır.",
        ) from error
    total = bounded(sum(parsed_allocations, Q(0)))
    if total > parsed_budget:
        raise LadderConservationError(
            "LADDER_BUDGET_EXCEEDED",
            "Ladder allocation toplamı explicit budget’ı aşamaz.",
        )
    return LadderConservation(
        allocation_unit=allocation_unit,
        total_allocated=exact_text(total),
        budget=exact_text(parsed_budget),
        remaining_budget=exact_text(parsed_budget - total),
    )
