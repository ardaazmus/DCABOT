"""Exact, in-memory projection for accepted fills of a hedge two-leg pair."""

from dataclasses import dataclass
import re
from typing import Final

from dcabot.application.hedge_two_leg_contract import (
    HedgePositionIdentity,
    HedgeTwoLegError,
    TwoLegState,
)
from dcabot.domain.numbers import bounded, exact_text, number, positive


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)
_LEG_IDS: Final = ("A", "B")
_FILL_STATUSES: Final = ("PARTIAL", "FULL")
_LEG_STATUSES: Final = ("NONE", "PARTIAL", "FULL")
_STATES: Final = (
    TwoLegState.NONE,
    TwoLegState.LEG_A_PENDING,
    TwoLegState.ONE_LEG_FILLED,
    TwoLegState.PARTIAL_HEDGE,
    TwoLegState.BOTH_ESTABLISHED,
    TwoLegState.RECOVERY_REQUIRED,
    TwoLegState.TIMEOUT,
)


def _error(code: str, message: str) -> HedgeTwoLegError:
    return HedgeTwoLegError(code, message)


def _nonnegative(value: object, code: str) -> str:
    try:
        result = number(value)
    except ValueError as error:
        raise _error(code, "Miktar geçerli exact decimal metni olmalıdır.") from error
    if result < 0:
        raise _error(code, "Miktar negatif olamaz.")
    try:
        return exact_text(bounded(result))
    except ValueError as error:
        raise _error(code, "Miktar dış sözleşmede exact temsil edilemiyor.") from error


def _identifier(value: object, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise _error(code, "Kimlik değeri geçersiz.")


@dataclass(frozen=True, slots=True)
class LegFill:
    """One accepted fill observation for exactly one hedge leg."""

    fill_id: str
    leg_id: str
    position: HedgePositionIdentity
    quantity: str
    fill_status: str
    event_time_us: int

    def __post_init__(self) -> None:
        _identifier(self.fill_id, "TWO_LEG_FILL_ID_INVALID")
        if self.leg_id not in _LEG_IDS:
            raise _error("TWO_LEG_LEG_ID_INVALID", "Leg A veya B olmalıdır.")
        if not isinstance(self.position, HedgePositionIdentity):
            raise _error("TWO_LEG_POSITION_INVALID", "Position identity geçersiz.")
        if self.position.position_mode != "HEDGE":
            raise _error(
                "TWO_LEG_POSITION_MODE_INVALID",
                "İki-leg projection yalnızca HEDGE identity kabul eder.",
            )
        try:
            quantity = exact_text(positive(self.quantity))
        except ValueError as error:
            raise _error(
                "TWO_LEG_FILL_QUANTITY_INVALID",
                "Fill quantity pozitif exact decimal metni olmalıdır.",
            ) from error
        object.__setattr__(self, "quantity", quantity)
        if self.fill_status not in _FILL_STATUSES:
            raise _error(
                "TWO_LEG_FILL_STATUS_INVALID",
                "Fill status PARTIAL veya FULL olmalıdır.",
            )
        if isinstance(self.event_time_us, bool) or not isinstance(self.event_time_us, int):
            raise _error("TWO_LEG_EVENT_TIME_INVALID", "event_time_us integer olmalıdır.")
        if self.event_time_us < 0:
            raise _error("TWO_LEG_EVENT_TIME_INVALID", "event_time_us negatif olamaz.")


@dataclass(frozen=True, slots=True)
class TwoLegFillProjection:
    """Immutable accepted-fill view; it is not order, reserve, or persistence authority."""

    state: str
    leg_a_identity: HedgePositionIdentity | None = None
    leg_b_identity: HedgePositionIdentity | None = None
    leg_a_quantity: str = "0"
    leg_b_quantity: str = "0"
    leg_a_status: str = "NONE"
    leg_b_status: str = "NONE"
    fills: tuple[LegFill, ...] = ()

    def __post_init__(self) -> None:
        if self.state not in _STATES:
            raise _error("TWO_LEG_STATE_INVALID", "Projection state geçersiz.")
        for identity in (self.leg_a_identity, self.leg_b_identity):
            if identity is not None and not isinstance(identity, HedgePositionIdentity):
                raise _error("TWO_LEG_POSITION_INVALID", "Position identity geçersiz.")
        for attribute, code in (
            ("leg_a_quantity", "TWO_LEG_A_QUANTITY_INVALID"),
            ("leg_b_quantity", "TWO_LEG_B_QUANTITY_INVALID"),
        ):
            quantity = getattr(self, attribute)
            canonical = _nonnegative(quantity, code)
            if quantity != canonical:
                object.__setattr__(self, attribute, canonical)
        if self.leg_a_status not in _LEG_STATUSES:
            raise _error("TWO_LEG_A_STATUS_INVALID", "Leg A status geçersiz.")
        if self.leg_b_status not in _LEG_STATUSES:
            raise _error("TWO_LEG_B_STATUS_INVALID", "Leg B status geçersiz.")
        if not isinstance(self.fills, tuple) or not all(isinstance(fill, LegFill) for fill in self.fills):
            raise _error("TWO_LEG_FILLS_INVALID", "Projection fills tuple[LegFill] olmalıdır.")


def new_two_leg_projection() -> TwoLegFillProjection:
    """Create an empty projection without claiming any economic state."""

    return TwoLegFillProjection(state=TwoLegState.NONE)


def start_two_leg_projection(projection: TwoLegFillProjection) -> TwoLegFillProjection:
    """Open the explicit leg-A-pending boundary without creating an order."""

    _validate_projection(projection)
    if projection.state != TwoLegState.NONE or projection.fills:
        raise _error(
            "TWO_LEG_TRANSITION_INVALID",
            "Only an empty NONE projection can start.",
        )
    return TwoLegFillProjection(
        state=TwoLegState.LEG_A_PENDING,
        leg_a_identity=projection.leg_a_identity,
        leg_b_identity=projection.leg_b_identity,
    )


def accept_two_leg_fill(
    projection: TwoLegFillProjection, fill: LegFill
) -> tuple[TwoLegFillProjection, str]:
    """Accept one ordered fill, returning a new projection and ACCEPTED/DUPLICATE."""

    _validate_projection(projection)
    if not isinstance(fill, LegFill):
        raise _error("TWO_LEG_FILL_INVALID", "Fill geçersiz.")
    for previous in projection.fills:
        if previous.fill_id == fill.fill_id:
            if previous == fill:
                return projection, "DUPLICATE"
            raise _error(
                "TWO_LEG_FILL_CONFLICT",
                "Aynı fill identity farklı payload ile tekrarlandı.",
            )
    if projection.state not in (
        TwoLegState.LEG_A_PENDING,
        TwoLegState.ONE_LEG_FILLED,
        TwoLegState.PARTIAL_HEDGE,
    ):
        raise _error(
            "TWO_LEG_TRANSITION_INVALID",
            "Bu state yeni accepted fill kabul edemez.",
        )
    if not projection.fills and fill.leg_id != "A":
        raise _error(
            "TWO_LEG_LEG_ORDER",
            "İlk accepted fill leg A olmalıdır.",
        )
    if projection.fills and fill.event_time_us < projection.fills[-1].event_time_us:
        raise _error(
            "TWO_LEG_EVENT_TIME_ORDER",
            "Accepted fill event time geriye gidemez.",
        )
    _validate_scope(projection, fill)
    if fill.leg_id == "B" and projection.leg_a_identity is not None:
        if fill.position.hedge_side == projection.leg_a_identity.hedge_side:
            raise _error(
                "TWO_LEG_SIDE_CONFLICT",
                "İki hedge leg aynı side olamaz.",
            )
    current_status = (
        projection.leg_a_status if fill.leg_id == "A" else projection.leg_b_status
    )
    if current_status == "FULL":
        raise _error(
            "TWO_LEG_LEG_ALREADY_COMPLETE",
            "Tamamlanan leg yeni non-duplicate fill kabul edemez.",
        )
    quantity_name = "leg_a_quantity" if fill.leg_id == "A" else "leg_b_quantity"
    old_quantity = number(getattr(projection, quantity_name))
    new_quantity = exact_text(bounded(old_quantity + positive(fill.quantity)))
    new_status = fill.fill_status
    next_projection = TwoLegFillProjection(
        state=_next_state(
            projection,
            fill,
            new_status,
        ),
        leg_a_identity=fill.position if fill.leg_id == "A" else projection.leg_a_identity,
        leg_b_identity=fill.position if fill.leg_id == "B" else projection.leg_b_identity,
        leg_a_quantity=new_quantity if fill.leg_id == "A" else projection.leg_a_quantity,
        leg_b_quantity=new_quantity if fill.leg_id == "B" else projection.leg_b_quantity,
        leg_a_status=new_status if fill.leg_id == "A" else projection.leg_a_status,
        leg_b_status=new_status if fill.leg_id == "B" else projection.leg_b_status,
        fills=(*projection.fills, fill),
    )
    return next_projection, "ACCEPTED"


def _validate_projection(projection: TwoLegFillProjection) -> None:
    if not isinstance(projection, TwoLegFillProjection):
        raise _error("TWO_LEG_PROJECTION_INVALID", "Projection geçersiz.")


def _validate_scope(projection: TwoLegFillProjection, fill: LegFill) -> None:
    existing = projection.leg_a_identity or projection.leg_b_identity
    if existing is not None:
        if fill.position.account_id != existing.account_id:
            raise _error("TWO_LEG_SCOPE_CONFLICT", "Account scope değişemez.")
        if fill.position.venue_profile != existing.venue_profile:
            raise _error("TWO_LEG_SCOPE_CONFLICT", "Venue profile değişemez.")
        if fill.position.product_id != existing.product_id:
            raise _error("TWO_LEG_SCOPE_CONFLICT", "Product scope değişemez.")
        if fill.position.symbol != existing.symbol:
            raise _error("TWO_LEG_SCOPE_CONFLICT", "Symbol scope değişemez.")
    identity = (
        projection.leg_a_identity if fill.leg_id == "A" else projection.leg_b_identity
    )
    if identity is not None and identity != fill.position:
        raise _error("TWO_LEG_POSITION_CONFLICT", "Leg identity değişemez.")


def _next_state(
    projection: TwoLegFillProjection,
    fill: LegFill,
    new_status: str,
) -> str:
    a_status = new_status if fill.leg_id == "A" else projection.leg_a_status
    b_status = new_status if fill.leg_id == "B" else projection.leg_b_status
    if a_status == "FULL" and b_status == "FULL":
        return TwoLegState.BOTH_ESTABLISHED
    if a_status == "PARTIAL" or b_status == "PARTIAL":
        return TwoLegState.PARTIAL_HEDGE
    return TwoLegState.ONE_LEG_FILLED
