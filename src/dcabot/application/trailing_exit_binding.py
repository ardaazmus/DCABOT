"""Bind a triggered trailing observation to an exact exit-capacity check."""

from dataclasses import dataclass

from dcabot.application.multi_tp_conservation import (
    ExitCapacityError,
    validate_exit_capacity,
)
from dcabot.application.trailing_ratchet import (
    TrailingLongPercentageState,
    TrailingLongState,
    TrailingShortPercentageState,
    TrailingShortState,
)
from dcabot.domain.numbers import exact_text, positive


class TrailingExitBindingError(ValueError):
    """Raised when a trailing exit candidate cannot pass capacity checks."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class TrailingExitBinding:
    """Trigger and capacity projection with order authority disabled."""

    trigger_price: str
    requested_qty: str
    remaining_capacity: str
    order_authority: str


def bind_trailing_exit_candidate(
    *,
    trailing: (
        TrailingLongState
        | TrailingShortState
        | TrailingLongPercentageState
        | TrailingShortPercentageState
    ),
    open_qty: str,
    accepted_exit_fills: tuple[str, ...],
    committed_exit_qty: tuple[str, ...],
    requested_qty: str,
) -> TrailingExitBinding:
    """Validate one triggered trailing exit without accepting or posting it."""

    if not isinstance(
        trailing,
        (
            TrailingLongState,
            TrailingShortState,
            TrailingLongPercentageState,
            TrailingShortPercentageState,
        ),
    ):
        raise TrailingExitBindingError(
            "TRAILING_EXIT_STATE_INVALID", "Trailing state geçersiz."
        )
    if trailing.status != "TRIGGERED" or trailing.stop_price is None:
        raise TrailingExitBindingError(
            "TRAILING_EXIT_NOT_TRIGGERED",
            "Trailing exit adayı yalnız tetiklenmiş state ile üretilebilir.",
        )
    if not isinstance(accepted_exit_fills, tuple) or not isinstance(
        committed_exit_qty, tuple
    ):
        raise TrailingExitBindingError(
            "TRAILING_EXIT_INPUT_INVALID", "Exit miktarları tuple olmalıdır."
        )
    try:
        trigger_price = exact_text(positive(trailing.stop_price))
    except ValueError as error:
        raise TrailingExitBindingError(
            "TRAILING_EXIT_STATE_INVALID", "Trigger fiyatı geçersiz."
        ) from error
    try:
        requested = exact_text(positive(requested_qty))
    except ValueError as error:
        raise TrailingExitBindingError(
            "TRAILING_EXIT_QTY_INVALID", "Requested exit miktarı geçersiz."
        ) from error
    try:
        capacity = validate_exit_capacity(
            open_qty=open_qty,
            accepted_exit_fills=accepted_exit_fills,
            committed_exit_qty=(*committed_exit_qty, requested_qty),
        )
    except ExitCapacityError as error:
        raise TrailingExitBindingError(error.code, str(error)) from error
    return TrailingExitBinding(
        trigger_price=trigger_price,
        requested_qty=requested,
        remaining_capacity=capacity.free_exit_capacity,
        order_authority="NONE",
    )
