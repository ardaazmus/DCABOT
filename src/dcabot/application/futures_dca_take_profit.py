"""Offline Futures DCA average-entry and split take-profit projection."""

from dataclasses import dataclass

from dcabot.application.futures_dca_fill_projection import FuturesDcaFillProjection
from dcabot.application.multi_tp_conservation import (
    ExitCapacityError,
    validate_exit_capacity,
)
from dcabot.domain.numbers import Q, align, bounded, exact_text, number, positive


class FuturesDcaTakeProfitError(ValueError):
    """Raised when a Futures DCA take-profit projection is unsafe."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FuturesDcaTakeProfitProjection:
    """Average-entry target and split quantity preview without exit authority."""

    fill_projection: FuturesDcaFillProjection
    average_entry: str
    profit_rate: str
    target_price: str
    split_quantities: tuple[str, ...]
    allocated_quantity: str
    remaining_quantity: str
    order_authority: str = "NONE"

    def __post_init__(self) -> None:
        if self.order_authority != "NONE":
            raise FuturesDcaTakeProfitError(
                "FUTURES_DCA_TP_ORDER_AUTHORITY_INVALID",
                "Take-profit projection order authority taşıyamaz.",
            )


def project_futures_dca_take_profit(
    fill_projection: FuturesDcaFillProjection,
    *,
    profit_rate: str,
    split_quantities: tuple[str, ...],
) -> FuturesDcaTakeProfitProjection:
    """Project an exact average-entry TP and conserved split quantities.

    The observed fill projection owns average-entry and position quantity.
    Target price is never silently rounded to a tick; an off-grid target is
    rejected until a later product decision defines directional quantization.
    Split quantities are validation-only allocations and never become orders.
    """

    if not isinstance(fill_projection, FuturesDcaFillProjection):
        raise FuturesDcaTakeProfitError(
            "FUTURES_DCA_TP_FILL_PROJECTION_INVALID",
            "Fill projection güvenli Futures DCA tipinde olmalıdır.",
        )
    if fill_projection.average_entry is None:
        raise FuturesDcaTakeProfitError(
            "FUTURES_DCA_TP_POSITION_EMPTY",
            "Average-entry TP için gözlenmiş pozisyon gereklidir.",
        )
    try:
        rate = positive(profit_rate)
        average_entry = positive(fill_projection.average_entry)
        position_quantity = positive(fill_projection.position_quantity)
        tick = positive(fill_projection.plan.price_tick)
    except ValueError as error:
        raise FuturesDcaTakeProfitError(
            "FUTURES_DCA_TP_NUMERIC_INVALID",
            "TP oranı, average-entry, pozisyon ve tick exact decimal olmalıdır.",
        ) from error
    normalized_splits = _normalize_split_quantities(split_quantities)
    side = fill_projection.plan.side
    target = (
        average_entry * (Q(1) + rate)
        if side == "LONG"
        else average_entry * (Q(1) - rate)
    )
    if target <= 0:
        raise FuturesDcaTakeProfitError(
            "FUTURES_DCA_TP_TARGET_INVALID",
            "TP hedef fiyatı pozitif kalmalıdır.",
        )
    if align(target, tick, up=False) != target:
        raise FuturesDcaTakeProfitError(
            "FUTURES_DCA_TP_TARGET_OFF_GRID",
            "TP hedefi price tick üzerinde exact temsil edilmelidir.",
        )
    try:
        capacity = validate_exit_capacity(
            open_qty=exact_text(position_quantity),
            accepted_exit_fills=(),
            committed_exit_qty=normalized_splits,
        )
    except ExitCapacityError as error:
        raise FuturesDcaTakeProfitError(error.code, str(error)) from error
    try:
        return FuturesDcaTakeProfitProjection(
            fill_projection=fill_projection,
            average_entry=exact_text(average_entry),
            profit_rate=exact_text(rate),
            target_price=exact_text(bounded(target)),
            split_quantities=normalized_splits,
            allocated_quantity=capacity.committed_exit_qty,
            remaining_quantity=capacity.free_exit_capacity,
        )
    except ValueError as error:
        raise FuturesDcaTakeProfitError(
            "FUTURES_DCA_TP_UNREPRESENTABLE",
            "TP projection exact decimal sözleşmesine sığmıyor.",
        ) from error


def _normalize_split_quantities(values: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple) or not values:
        raise FuturesDcaTakeProfitError(
            "FUTURES_DCA_TP_SPLIT_INVALID",
            "Split TP pozitif decimal tuple olmalıdır.",
        )
    normalized: list[str] = []
    for value in values:
        try:
            normalized.append(exact_text(positive(value)))
        except ValueError as error:
            raise FuturesDcaTakeProfitError(
                "FUTURES_DCA_TP_SPLIT_INVALID",
                "Split TP pozitif exact decimal miktarlardan oluşmalıdır.",
            ) from error
    return tuple(normalized)
