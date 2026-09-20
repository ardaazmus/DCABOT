"""Exact one-way Futures Grid position projection before P&L and margin state."""

from dataclasses import dataclass
from enum import StrEnum
import re

from dcabot.application.futures_grid_levels import FuturesGridProfile
from dcabot.domain.numbers import bounded, exact_text, number, positive


_IDENTITY = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)


class FuturesGridPositionError(ValueError):
    """Raised when an accepted Futures Grid fill cannot be projected safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class FuturesGridFillSide(StrEnum):
    """The two accepted fill sides used by the one-way projection."""

    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True, slots=True)
class FuturesGridFill:
    """One already accepted fill, not an order or a transport observation."""

    fill_id: str
    side: FuturesGridFillSide
    price: str
    quantity: str
    effective_time_us: int


@dataclass(frozen=True, slots=True)
class FuturesGridPositionState:
    """Exact one-way position quantity and average entry after accepted fills."""

    profile: FuturesGridProfile
    direction: str
    initial_position_policy: str
    position_side: str
    quantity: str
    average_entry: str | None
    fills: tuple[FuturesGridFill, ...]


def new_futures_grid_position(
    *,
    profile: FuturesGridProfile,
    direction: str,
    initial_position_policy: str = "FLAT",
) -> FuturesGridPositionState:
    """Create a flat one-way LONG or SHORT position projection."""

    if not isinstance(profile, FuturesGridProfile):
        raise FuturesGridPositionError(
            "FUTURES_GRID_PROFILE_INVALID",
            "Futures Grid profile güvenli tipte olmalıdır.",
        )
    if direction not in ("LONG", "SHORT"):
        raise FuturesGridPositionError(
            "FUTURES_GRID_POSITION_DIRECTION_UNSUPPORTED",
            "Bu position projection yalnız LONG veya SHORT yönünü destekler.",
        )
    if initial_position_policy != "FLAT":
        raise FuturesGridPositionError(
            "FUTURES_GRID_INITIAL_POSITION_UNSUPPORTED",
            "Position projection yalnız explicit FLAT başlangıç politikasını destekler.",
        )
    return FuturesGridPositionState(
        profile=profile,
        direction=direction,
        initial_position_policy=initial_position_policy,
        position_side="FLAT",
        quantity="0",
        average_entry=None,
        fills=(),
    )


def _canonical_fill(fill: FuturesGridFill) -> FuturesGridFill:
    if not isinstance(fill, FuturesGridFill):
        raise FuturesGridPositionError(
            "FUTURES_GRID_FILL_INVALID", "Fill güvenli tipte olmalıdır."
        )
    if _IDENTITY.fullmatch(fill.fill_id or "") is None:
        raise FuturesGridPositionError(
            "FUTURES_GRID_FILL_ID_INVALID", "fill_id geçerli bir kimlik olmalıdır."
        )
    if not isinstance(fill.side, FuturesGridFillSide):
        raise FuturesGridPositionError(
            "FUTURES_GRID_FILL_SIDE_INVALID", "Fill side BUY veya SELL olmalıdır."
        )
    if type(fill.effective_time_us) is not int or fill.effective_time_us < 0:
        raise FuturesGridPositionError(
            "FUTURES_GRID_FILL_TIME_INVALID", "Fill effective time geçersiz."
        )
    try:
        price = positive(fill.price)
        quantity = positive(fill.quantity)
        return FuturesGridFill(
            fill_id=fill.fill_id,
            side=fill.side,
            price=exact_text(price),
            quantity=exact_text(quantity),
            effective_time_us=fill.effective_time_us,
        )
    except ValueError as error:
        raise FuturesGridPositionError(
            "FUTURES_GRID_FILL_NUMERIC_INVALID",
            "Fill price ve quantity pozitif exact decimal olmalıdır.",
        ) from error


def _expected_open_side(direction: str) -> FuturesGridFillSide:
    return FuturesGridFillSide.BUY if direction == "LONG" else FuturesGridFillSide.SELL


def apply_accepted_futures_grid_fill(
    state: FuturesGridPositionState, fill: FuturesGridFill
) -> FuturesGridPositionState:
    """Apply one exact fill without allowing direction flips or P&L mutation."""

    if not isinstance(state, FuturesGridPositionState):
        raise FuturesGridPositionError(
            "FUTURES_GRID_STATE_INVALID", "Position state güvenli tipte olmalıdır."
        )
    canonical = _canonical_fill(fill)
    for previous in state.fills:
        if previous.fill_id == canonical.fill_id:
            if previous == canonical:
                return state
            raise FuturesGridPositionError(
                "FUTURES_GRID_FILL_CONFLICT",
                "Aynı fill_id farklı ekonomik kayıtla tekrarlandı.",
            )
    if state.fills and canonical.effective_time_us < state.fills[-1].effective_time_us:
        raise FuturesGridPositionError(
            "FUTURES_GRID_FILL_TIME_ORDER",
            "Yeni fill effective time geriye gidemez.",
        )

    current_quantity = number(state.quantity)
    fill_quantity = number(canonical.quantity)
    opening_side = _expected_open_side(state.direction)
    if state.position_side == "FLAT":
        if canonical.side is not opening_side:
            raise FuturesGridPositionError(
                "FUTURES_GRID_DIRECTION_CONFLICT",
                "Flat one-way position ters yönde açılıp flip edilemez.",
            )
        next_side = state.direction
        next_quantity = fill_quantity
        next_average = number(canonical.price)
    elif canonical.side is opening_side:
        current_average = number(state.average_entry or "0")
        next_quantity = bounded(current_quantity + fill_quantity)
        next_side = state.direction
        next_average = bounded(
            (current_quantity * current_average + fill_quantity * number(canonical.price))
            / next_quantity
        )
    else:
        if fill_quantity > current_quantity:
            raise FuturesGridPositionError(
                "FUTURES_GRID_POSITION_OVERFLOW",
                "Close fill mevcut position quantity değerini aşamaz; flip yok.",
            )
        next_quantity = bounded(current_quantity - fill_quantity)
        next_side = state.direction if next_quantity else "FLAT"
        next_average = None if not next_quantity else number(state.average_entry or "0")

    try:
        return FuturesGridPositionState(
            profile=state.profile,
            direction=state.direction,
            initial_position_policy=state.initial_position_policy,
            position_side=next_side,
            quantity=exact_text(next_quantity),
            average_entry=None if next_average is None else exact_text(next_average),
            fills=state.fills + (canonical,),
        )
    except ValueError as error:
        raise FuturesGridPositionError(
            "FUTURES_GRID_AVERAGE_NOT_EXACT",
            "Average entry exact decimal sözleşmesine sığmıyor; rounding yapılmadı.",
        ) from error
