"""Explicit, conservative limit-order policy for bounded OHLCV experiments."""

from dataclasses import dataclass
import re

from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput
from dcabot.domain.config import Config
from dcabot.domain.numbers import Q, align, exact_text, number


FIXED_LIMIT_MODEL = "historical_ohlcv_partial_fixed_limit_v1"
FIXED_LIMIT_POLICY = "FIXED_LIMIT_STRICT_V1"
_ORDER_ID_PATTERN = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)


class HistoricalFixedLimitError(ValueError):
    """Raised when an explicit fixed-limit experiment is unsafe to run."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class FixedLimitOrder:
    """Immutable limit order identity and the bar after which it becomes active."""

    order_id: str
    side: str
    limit_price: str
    original_qty: str
    placement_bar_index: int
    placement_open_time_us: int


@dataclass(frozen=True, slots=True)
class FixedLimitObservation:
    """One OHLC observation, separated from any synthetic fill commitment."""

    bar_index: int
    open_time_us: int
    kind: str
    trigger_observed: bool
    fill_committed: bool


@dataclass(frozen=True, slots=True)
class FixedLimitAction:
    """One synthetic fixed-slice fill with exact quantity conservation fields."""

    event_sequence: int
    bar_index: int
    open_time_us: int
    order_id: str
    side: str
    observation_kind: str
    fill_price: str
    quantity: str
    cumulative_filled_qty: str
    leaves_qty: str


@dataclass(frozen=True, slots=True)
class FixedLimitResult:
    """Bounded result for the explicit fixed-limit policy."""

    model: str
    policy: str
    status: str
    application_code: str | None
    processed_bar_count: int
    first_ambiguous_bar_index: int | None
    last_observation_kind: str | None
    original_qty: str
    filled_qty: str
    leaves_qty: str
    actions: tuple[FixedLimitAction, ...]
    observations: tuple[FixedLimitObservation, ...]


def simulate_fixed_limit_order(
    dataset: HistoricalDatasetInput,
    config: Config,
    order: FixedLimitOrder,
    *,
    slice_qty: str,
    ambiguous_bar_indices: set[int] | frozenset[int] | None = None,
) -> FixedLimitResult:
    """Apply strict-penetration fills only on bars after explicit placement.

    Equality is recorded as an observation but never commits a fill. A strict
    penetration commits at most one exact fixed slice at the declared limit
    price. ``ambiguous_bar_indices`` is an application seam for a later
    strategy integration to fail closed when another same-bar event changes
    the economic ordering.
    """

    _validate_order(dataset, config, order, slice_qty)
    fixed_qty = number(slice_qty)
    original_qty = number(order.original_qty)
    limit_price = number(order.limit_price)
    ambiguous = ambiguous_bar_indices or set()
    actions: list[FixedLimitAction] = []
    observations: list[FixedLimitObservation] = []
    filled_qty = Q(0)
    leaves_qty = original_qty

    for index, bar in enumerate(dataset.bars, start=1):
        if index <= order.placement_bar_index:
            continue
        if index in ambiguous:
            return _result(
                order,
                original_qty,
                filled_qty,
                leaves_qty,
                actions,
                observations,
                status="INDETERMINATE",
                application_code="AMBIGUOUS_OHLC_PATH",
                processed_bar_count=index - 1,
                first_ambiguous_bar_index=index,
            )

        kind = _observation_kind(bar, order.side, limit_price)
        trigger_observed = kind != "NONE"
        fill_committed = kind == "STRICT_PENETRATION" and leaves_qty > 0
        observations.append(
            FixedLimitObservation(
                bar_index=index,
                open_time_us=bar.open_time_us,
                kind=kind,
                trigger_observed=trigger_observed,
                fill_committed=fill_committed,
            )
        )
        if not fill_committed:
            continue

        fill_qty = min(fixed_qty, leaves_qty)
        filled_qty += fill_qty
        leaves_qty -= fill_qty
        actions.append(
            FixedLimitAction(
                event_sequence=len(actions) + 1,
                bar_index=index,
                open_time_us=bar.open_time_us,
                order_id=order.order_id,
                side=order.side,
                observation_kind=kind,
                fill_price=exact_text(limit_price),
                quantity=exact_text(fill_qty),
                cumulative_filled_qty=exact_text(filled_qty),
                leaves_qty=exact_text(leaves_qty),
            )
        )
        if leaves_qty == 0:
            return _result(
                order,
                original_qty,
                filled_qty,
                leaves_qty,
                actions,
                observations,
                status="FILLED",
                application_code=None,
                processed_bar_count=index,
                first_ambiguous_bar_index=None,
            )

    return _result(
        order,
        original_qty,
        filled_qty,
        leaves_qty,
        actions,
        observations,
        status="OPEN_AT_END",
        application_code=None,
        processed_bar_count=len(dataset.bars),
        first_ambiguous_bar_index=None,
    )


def _validate_order(
    dataset: HistoricalDatasetInput,
    config: Config,
    order: FixedLimitOrder,
    slice_qty: str,
) -> None:
    if not _ORDER_ID_PATTERN.fullmatch(order.order_id):
        raise HistoricalFixedLimitError("ORDER_ID_INVALID", "Limit order kimliği geçersiz.")
    if order.side not in ("BUY", "SELL"):
        raise HistoricalFixedLimitError("ORDER_SIDE_INVALID", "Limit order yönü geçersiz.")
    if type(order.placement_bar_index) is not int or not 0 <= order.placement_bar_index <= len(dataset.bars):
        raise HistoricalFixedLimitError("PLACEMENT_BAR_INVALID", "Limit order placement barı geçersiz.")
    if type(order.placement_open_time_us) is not int:
        raise HistoricalFixedLimitError("PLACEMENT_IDENTITY_REQUIRED", "Placement zamanı tam sayı olmalıdır.")
    if order.placement_bar_index:
        placement_bar = dataset.bars[order.placement_bar_index - 1]
        if order.placement_open_time_us != placement_bar.open_time_us:
            raise HistoricalFixedLimitError("PLACEMENT_IDENTITY_MISMATCH", "Placement bar kimliği eşleşmiyor.")
    elif order.placement_open_time_us != 0:
        raise HistoricalFixedLimitError("PLACEMENT_IDENTITY_MISMATCH", "Dataset öncesi placement zamanı sıfır olmalıdır.")
    try:
        limit_price = number(order.limit_price)
        original_qty = number(order.original_qty)
        fixed_qty = number(slice_qty)
    except ValueError as exc:
        raise HistoricalFixedLimitError("INVALID_EXACT_DECIMAL", "Limit order exact decimal alanı geçersiz.") from exc
    if original_qty <= 0 or fixed_qty <= 0 or fixed_qty > original_qty:
        raise HistoricalFixedLimitError("QUANTITY_INVALID", "Limit order miktarları geçersiz.")
    try:
        config.check_order(original_qty, limit_price)
    except ValueError as exc:
        raise HistoricalFixedLimitError("ORDER_POLICY_REJECTED", "Limit order aktif config politikasına uymuyor.") from exc
    if align(fixed_qty, config.qty_step, up=False) != fixed_qty:
        raise HistoricalFixedLimitError("SLICE_QTY_OFF_GRID", "Fixed slice quantity mevcut quantity grid’inde değil.")


def _observation_kind(bar: CanonicalBar, side: str, limit_price: Q) -> str:
    if side == "BUY":
        low = number(bar.low)
        if low > limit_price:
            return "NONE"
        if low == limit_price:
            return "EQUALITY_TOUCH"
        return "STRICT_PENETRATION"
    high = number(bar.high)
    if high < limit_price:
        return "NONE"
    if high == limit_price:
        return "EQUALITY_TOUCH"
    return "STRICT_PENETRATION"


def _result(
    order: FixedLimitOrder,
    original_qty: Q,
    filled_qty: Q,
    leaves_qty: Q,
    actions: list[FixedLimitAction],
    observations: list[FixedLimitObservation],
    *,
    status: str,
    application_code: str | None,
    processed_bar_count: int,
    first_ambiguous_bar_index: int | None,
) -> FixedLimitResult:
    if filled_qty + leaves_qty != original_qty or leaves_qty < 0:
        raise HistoricalFixedLimitError("QUANTITY_CONSERVATION_VIOLATION", "Limit order quantity conservation bozuldu.")
    return FixedLimitResult(
        model=FIXED_LIMIT_MODEL,
        policy=FIXED_LIMIT_POLICY,
        status=status,
        application_code=application_code,
        processed_bar_count=processed_bar_count,
        first_ambiguous_bar_index=first_ambiguous_bar_index,
        last_observation_kind=observations[-1].kind if observations else None,
        original_qty=exact_text(original_qty),
        filled_qty=exact_text(filled_qty),
        leaves_qty=exact_text(leaves_qty),
        actions=tuple(actions),
        observations=tuple(observations),
    )
