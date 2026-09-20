"""Offline Futures DCA fill, average-entry and pending projection."""

from dataclasses import dataclass

from dcabot.application.futures_dca_plan import FuturesDcaProjection
from dcabot.domain.numbers import Q, align, bounded, exact_text, number, positive


class FuturesDcaFillError(ValueError):
    """Raised when a Futures DCA fill projection is unsafe or inconsistent."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FuturesDcaFill:
    """One immutable, already-observed fill fact; it is not an order command."""

    execution_id: str
    level_index: int
    quantity: str
    price: str

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, str) or not 1 <= len(self.execution_id) <= 100:
            raise FuturesDcaFillError("FUTURES_DCA_EXECUTION_ID_INVALID", "Execution kimliği boş olamaz.")
        if type(self.level_index) is not int or not 0 <= self.level_index <= 50:
            raise FuturesDcaFillError("FUTURES_DCA_LEVEL_INDEX_INVALID", "Level index 0..50 integer olmalıdır.")
        try:
            quantity = exact_text(positive(self.quantity))
            price = exact_text(positive(self.price))
        except ValueError as error:
            raise FuturesDcaFillError("FUTURES_DCA_FILL_NUMERIC_INVALID", "Fill miktarı ve fiyatı exact decimal olmalıdır.") from error
        object.__setattr__(self, "quantity", quantity)
        object.__setattr__(self, "price", price)


@dataclass(frozen=True, slots=True)
class FuturesDcaFillProjection:
    """Exact average-entry and bounded pending reservation preview."""

    plan: FuturesDcaProjection
    fills: tuple[FuturesDcaFill, ...]
    position_quantity: str
    position_notional: str
    average_entry: str | None
    completed_safety_count: int
    active_pending_levels: tuple[int, ...]
    pending_reserved_quote: str


def project_futures_dca_fills(
    plan: FuturesDcaProjection,
    fills: tuple[FuturesDcaFill, ...],
    *,
    max_active_safety_orders: int = 1,
) -> FuturesDcaFillProjection:
    """Project observed fills and the next bounded safety candidates offline."""

    if not isinstance(plan, FuturesDcaProjection):
        raise FuturesDcaFillError("FUTURES_DCA_PLAN_INVALID", "Futures DCA plan güvenli tipte olmalıdır.")
    if not isinstance(fills, tuple) or any(not isinstance(item, FuturesDcaFill) for item in fills):
        raise FuturesDcaFillError("FUTURES_DCA_FILLS_INVALID", "Fill listesi immutable tuple olmalıdır.")
    if type(max_active_safety_orders) is not int or not 1 <= max_active_safety_orders <= max(1, len(plan.levels)):
        raise FuturesDcaFillError("FUTURES_DCA_ACTIVE_LIMIT_INVALID", "Aktif safety order sınırı plan aralığında olmalıdır.")

    by_execution: dict[str, FuturesDcaFill] = {}
    quantities = [Q(0)] * (len(plan.levels) + 1)
    notionals = [Q(0)] * (len(plan.levels) + 1)
    for fill in fills:
        prior = by_execution.get(fill.execution_id)
        if prior is not None:
            if prior != fill:
                raise FuturesDcaFillError("FUTURES_DCA_FILL_CONFLICT", "Aynı execution kimliği farklı payload taşıyamaz.")
            continue
        by_execution[fill.execution_id] = fill
        if fill.level_index > len(plan.levels):
            raise FuturesDcaFillError("FUTURES_DCA_LEVEL_UNKNOWN", "Fill plan dışındaki safety seviyesine ait.")
        price = number(fill.price)
        quantity = number(fill.quantity)
        expected_price = number(plan.anchor_price) if fill.level_index == 0 else number(plan.levels[fill.level_index - 1].price)
        if align(price, number(plan.price_tick), up=False) != price:
            raise FuturesDcaFillError("FUTURES_DCA_FILL_OFF_GRID", "Fill fiyatı price tick üzerinde olmalıdır.")
        if (plan.side == "LONG" and price > expected_price) or (plan.side == "SHORT" and price < expected_price):
            raise FuturesDcaFillError("FUTURES_DCA_FILL_LIMIT_INVALID", "Fill plan limit yönünü ihlal ediyor.")
        target = number(plan.base_quantity) if fill.level_index == 0 else number(plan.levels[fill.level_index - 1].quantity)
        if quantities[fill.level_index] + quantity > target:
            raise FuturesDcaFillError("FUTURES_DCA_FILL_OVERFLOW", "Fill seviyesi plan miktarını aşamaz.")
        quantities[fill.level_index] = bounded(quantities[fill.level_index] + quantity)
        notionals[fill.level_index] = bounded(notionals[fill.level_index] + quantity * price)

    if quantities[0] < number(plan.base_quantity) and any(quantity for quantity in quantities[1:]):
        raise FuturesDcaFillError("FUTURES_DCA_BASE_INCOMPLETE", "Base tamamlanmadan safety fill kabul edilmez.")
    for index in range(1, len(quantities)):
        if quantities[index] and quantities[index - 1] < (number(plan.base_quantity) if index == 1 else number(plan.levels[index - 2].quantity)):
            raise FuturesDcaFillError("FUTURES_DCA_SAFETY_SEQUENCE_INVALID", "Safety seviyeleri sırayla tamamlanmalıdır.")

    total_quantity = bounded(sum(quantities, Q(0)))
    total_notional = bounded(sum(notionals, Q(0)))
    next_level = next((index for index in range(1, len(quantities)) if quantities[index] < number(plan.levels[index - 1].quantity)), None)
    pending = tuple(
        range(next_level, min(len(quantities), next_level + max_active_safety_orders))
    ) if quantities[0] == number(plan.base_quantity) and next_level is not None else ()
    pending_reserved = bounded(
        sum(
            (
                (number(plan.levels[index - 1].quantity) - quantities[index])
                * number(plan.levels[index - 1].price)
                for index in pending
            ),
            Q(0),
        )
    )
    completed = sum(quantity == number(plan.levels[index - 1].quantity) for index, quantity in enumerate(quantities[1:], 1))
    try:
        average_entry = None if not total_quantity else exact_text(total_notional / total_quantity)
    except ValueError as error:
        raise FuturesDcaFillError(
            "FUTURES_DCA_AVERAGE_NOT_EXACT", "Average entry dış decimal sözleşmesine sığmıyor."
        ) from error
    return FuturesDcaFillProjection(
        plan=plan,
        fills=tuple(by_execution.values()),
        position_quantity=exact_text(total_quantity),
        position_notional=exact_text(total_notional),
        average_entry=average_entry,
        completed_safety_count=completed,
        active_pending_levels=pending,
        pending_reserved_quote=exact_text(pending_reserved),
    )
