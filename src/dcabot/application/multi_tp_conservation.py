"""Exact multi-exit quantity conservation without order-side effects."""

from dataclasses import dataclass

from dcabot.domain.numbers import Q, bounded, exact_text, positive


class ExitCapacityError(ValueError):
    """Raised when exit quantities cannot fit within an open position."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class ExitCapacity:
    """Exact open, consumed, committed and still-free exit quantities."""

    open_qty: str
    accepted_exit_fills: str
    committed_exit_qty: str
    free_exit_capacity: str


def _sum_exit_quantities(values: tuple[str, ...], label: str) -> Q:
    if not isinstance(values, tuple):
        raise ExitCapacityError(
            "EXIT_CAPACITY_QTY_INVALID", f"{label} tuple olmalıdır."
        )
    total = Q(0)
    for value in values:
        try:
            parsed = positive(value)
        except ValueError as error:
            raise ExitCapacityError(
                "EXIT_CAPACITY_QTY_INVALID",
                f"{label} pozitif decimal miktarlardan oluşmalıdır.",
            ) from error
        total = bounded(total + parsed)
    return total


def validate_exit_capacity(
    *,
    open_qty: str,
    accepted_exit_fills: tuple[str, ...],
    committed_exit_qty: tuple[str, ...],
) -> ExitCapacity:
    """Prove that accepted and still-committed exits cannot over-close.

    ``committed_exit_qty`` contains only currently free quantity committed to
    exit orders; a partially filled order must contribute its remaining
    commitment, not its original requested quantity. This function is a
    validation projection and never accepts, cancels, fills, or posts orders.
    """

    try:
        open_quantity = positive(open_qty)
    except ValueError as error:
        raise ExitCapacityError(
            "EXIT_CAPACITY_QTY_INVALID",
            "Open quantity pozitif decimal string olmalıdır.",
        ) from error
    filled = _sum_exit_quantities(accepted_exit_fills, "Accepted exit fill")
    committed = _sum_exit_quantities(committed_exit_qty, "Committed exit")
    consumed = bounded(filled + committed)
    if consumed > open_quantity:
        raise ExitCapacityError(
            "EXIT_CAPACITY_EXCEEDED",
            "Accepted ve committed exit miktarı açık pozisyonu aşamaz.",
        )
    free = bounded(open_quantity - consumed)
    try:
        return ExitCapacity(
            open_qty=exact_text(open_quantity),
            accepted_exit_fills=exact_text(filled),
            committed_exit_qty=exact_text(committed),
            free_exit_capacity=exact_text(free),
        )
    except ValueError as error:
        raise ExitCapacityError(
            "EXIT_CAPACITY_UNREPRESENTABLE",
            "Exit kapasitesi exact decimal sözleşmesine sığmıyor.",
        ) from error
