"""Application binding from exact ladder generation to conservation checks."""

from dataclasses import dataclass

from dcabot.application.ladder_conservation import (
    LadderConservation,
    LadderConservationError,
    validate_ladder_allocations,
)
from dcabot.domain.math import build_plan
from dcabot.domain.numbers import exact_text, positive


class LadderBindingError(ValueError):
    """Raised when ladder generation or its conservation binding fails."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class LadderLevelCandidate:
    """One exact generated level before venue order acceptance."""

    index: int
    price: str
    quantity: str
    allocation: str


@dataclass(frozen=True, slots=True)
class LadderBinding:
    """Generated levels and their same-unit exact budget proof."""

    levels: tuple[LadderLevelCandidate, ...]
    conservation: LadderConservation


def build_ladder_binding(
    *,
    anchor_price: str,
    safety_qty: str,
    safety_count: int,
    deviation: str,
    step_multiplier: str,
    volume_multiplier: str,
    price_tick: str,
    qty_step: str,
    allocation_unit: str,
    budget: str,
) -> LadderBinding:
    """Generate domain levels and prove their exact allocation conservation."""

    if type(safety_count) is not int or not 0 <= safety_count <= 50:
        raise LadderBindingError(
            "LADDER_GENERATION_INVALID", "Safety count integer 0..50 olmalıdır."
        )
    try:
        values = tuple(
            positive(value)
            for value in (
                anchor_price,
                safety_qty,
                deviation,
                step_multiplier,
                volume_multiplier,
                price_tick,
                qty_step,
            )
        )
    except ValueError as error:
        raise LadderBindingError(
            "LADDER_GENERATION_INVALID",
            "Ladder generation değerleri pozitif decimal string olmalıdır.",
        ) from error
    anchor, quantity, increment, step, volume, tick, quantity_step = values
    try:
        levels = build_plan(
            anchor,
            quantity,
            safety_count,
            increment,
            step,
            volume,
            tick,
            quantity_step,
        )
        candidates = tuple(
            LadderLevelCandidate(
                index=level.index,
                price=exact_text(level.price),
                quantity=exact_text(level.qty),
                allocation=exact_text(
                    level.qty
                    if allocation_unit == "BASE_QTY"
                    else level.qty * level.price
                ),
            )
            for level in levels
        )
    except ValueError as error:
        raise LadderBindingError(
            "LADDER_GENERATION_INVALID", "Ladder seviyeleri üretilemedi."
        ) from error
    try:
        conservation = validate_ladder_allocations(
            allocation_unit=allocation_unit,
            allocations=tuple(level.allocation for level in candidates),
            budget=budget,
        )
    except LadderConservationError as error:
        raise LadderBindingError(error.code, str(error)) from error
    return LadderBinding(levels=candidates, conservation=conservation)
