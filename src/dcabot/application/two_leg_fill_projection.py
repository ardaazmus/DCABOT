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
    if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
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
        if type(self.leg_id) is not str or self.leg_id not in _LEG_IDS:
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
        if type(self.fill_status) is not str or self.fill_status not in _FILL_STATUSES:
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
        if type(self.state) is not str or self.state not in _STATES:
            raise _error("TWO_LEG_STATE_INVALID", "Projection state geçersiz.")
        for identity in (self.leg_a_identity, self.leg_b_identity):
            if identity is not None and not isinstance(identity, HedgePositionIdentity):
                raise _error("TWO_LEG_POSITION_INVALID", "Position identity geçersiz.")
            if identity is not None and (
                type(identity.position_mode) is not str
                or identity.position_mode != "HEDGE"
                or type(identity.hedge_side) is not str
                or identity.hedge_side not in ("LONG", "SHORT")
            ):
                raise _error(
                    "TWO_LEG_POSITION_MODE_INVALID",
                    "İki-leg projection yalnızca HEDGE identity kabul eder.",
                )
        for attribute, code in (
            ("leg_a_quantity", "TWO_LEG_A_QUANTITY_INVALID"),
            ("leg_b_quantity", "TWO_LEG_B_QUANTITY_INVALID"),
        ):
            quantity = getattr(self, attribute)
            canonical = _nonnegative(quantity, code)
            if quantity != canonical:
                object.__setattr__(self, attribute, canonical)
        if type(self.leg_a_status) is not str or self.leg_a_status not in _LEG_STATUSES:
            raise _error("TWO_LEG_A_STATUS_INVALID", "Leg A status geçersiz.")
        if type(self.leg_b_status) is not str or self.leg_b_status not in _LEG_STATUSES:
            raise _error("TWO_LEG_B_STATUS_INVALID", "Leg B status geçersiz.")
        if not isinstance(self.fills, tuple) or not all(isinstance(fill, LegFill) for fill in self.fills):
            raise _error("TWO_LEG_FILLS_INVALID", "Projection fills tuple[LegFill] olmalıdır.")
        self._validate_consistency()

    def _validate_consistency(self) -> None:
        if self.leg_a_identity is not None and self.leg_b_identity is not None:
            if (
                self.leg_a_identity.account_id != self.leg_b_identity.account_id
                or self.leg_a_identity.venue_profile != self.leg_b_identity.venue_profile
                or self.leg_a_identity.product_id != self.leg_b_identity.product_id
                or self.leg_a_identity.symbol != self.leg_b_identity.symbol
            ):
                raise _error("TWO_LEG_SCOPE_CONFLICT", "İki leg aynı scope içinde olmalıdır.")
            if self.leg_a_identity.hedge_side == self.leg_b_identity.hedge_side:
                raise _error("TWO_LEG_SIDE_CONFLICT", "İki hedge leg aynı side olamaz.")

        if not self.fills:
            if self.state in (TwoLegState.NONE, TwoLegState.LEG_A_PENDING):
                if (
                    self.leg_a_quantity != "0"
                    or self.leg_b_quantity != "0"
                    or self.leg_a_status != "NONE"
                    or self.leg_b_status != "NONE"
                ):
                    raise _error(
                        "TWO_LEG_STATE_INCONSISTENT",
                        "Fill olmadan pending/none projection aggregate taşıyamaz.",
                    )
                return
            raise _error(
                "TWO_LEG_STATE_INCONSISTENT",
                "Fill history olmadan filled lifecycle state kurulamaz.",
            )

        seen_ids: set[str] = set()
        last_event_time = -1
        leg_identities: dict[str, HedgePositionIdentity] = {}
        leg_quantities = {"A": number("0"), "B": number("0")}
        leg_statuses = {"A": "NONE", "B": "NONE"}
        reference: HedgePositionIdentity | None = None
        for fill in self.fills:
            if fill.fill_id in seen_ids:
                raise _error("TWO_LEG_FILL_HISTORY_INVALID", "Fill identity tekrar edemez.")
            seen_ids.add(fill.fill_id)
            if fill.event_time_us < last_event_time:
                raise _error(
                    "TWO_LEG_FILL_HISTORY_INVALID",
                    "Fill history event time geriye gidemez.",
                )
            last_event_time = fill.event_time_us
            if not leg_identities and fill.leg_id != "A":
                raise _error("TWO_LEG_FILL_HISTORY_INVALID", "İlk fill leg A olmalıdır.")
            if reference is None:
                reference = fill.position
            elif (
                fill.position.account_id != reference.account_id
                or fill.position.venue_profile != reference.venue_profile
                or fill.position.product_id != reference.product_id
                or fill.position.symbol != reference.symbol
            ):
                raise _error("TWO_LEG_SCOPE_CONFLICT", "İki leg aynı scope içinde olmalıdır.")
            previous_identity = leg_identities.get(fill.leg_id)
            if previous_identity is not None and previous_identity != fill.position:
                raise _error("TWO_LEG_POSITION_CONFLICT", "Leg identity değişemez.")
            opposite = "B" if fill.leg_id == "A" else "A"
            opposite_identity = leg_identities.get(opposite)
            if opposite_identity is not None and opposite_identity.hedge_side == fill.position.hedge_side:
                raise _error("TWO_LEG_SIDE_CONFLICT", "İki hedge leg aynı side olamaz.")
            if leg_statuses[fill.leg_id] == "FULL":
                raise _error(
                    "TWO_LEG_FILL_HISTORY_INVALID",
                    "Tamamlanan leg history içinde yeni fill taşıyamaz.",
                )
            leg_identities[fill.leg_id] = fill.position
            leg_quantities[fill.leg_id] += positive(fill.quantity)
            leg_statuses[fill.leg_id] = fill.fill_status

        expected_state = _state_from_statuses(leg_statuses["A"], leg_statuses["B"])
        if (
            self.leg_a_identity != leg_identities.get("A")
            or self.leg_b_identity != leg_identities.get("B")
            or self.leg_a_quantity != exact_text(bounded(leg_quantities["A"]))
            or self.leg_b_quantity != exact_text(bounded(leg_quantities["B"]))
            or self.leg_a_status != leg_statuses["A"]
            or self.leg_b_status != leg_statuses["B"]
        ):
            raise _error(
                "TWO_LEG_AGGREGATE_INCONSISTENT",
                "Projection aggregate fill history ile eşleşmiyor.",
            )
        if self.state in (TwoLegState.RECOVERY_REQUIRED, TwoLegState.TIMEOUT):
            if expected_state == TwoLegState.BOTH_ESTABLISHED:
                raise _error(
                    "TWO_LEG_STATE_INCONSISTENT",
                    "Recovery/timeout established projection üzerine uygulanamaz.",
                )
        elif self.state != expected_state:
            raise _error(
                "TWO_LEG_STATE_INCONSISTENT",
                "Projection state fill history ile eşleşmiyor.",
            )


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


def _state_from_statuses(a_status: str, b_status: str) -> str:
    if a_status == "FULL" and b_status == "FULL":
        return TwoLegState.BOTH_ESTABLISHED
    if a_status == "PARTIAL" or b_status == "PARTIAL":
        return TwoLegState.PARTIAL_HEDGE
    if a_status == "FULL" and b_status == "NONE":
        return TwoLegState.ONE_LEG_FILLED
    raise _error(
        "TWO_LEG_STATE_INCONSISTENT",
        "Leg A accepted fill olmadan leg durumu oluşamaz.",
    )


def _next_state(
    projection: TwoLegFillProjection,
    fill: LegFill,
    new_status: str,
) -> str:
    a_status = new_status if fill.leg_id == "A" else projection.leg_a_status
    b_status = new_status if fill.leg_id == "B" else projection.leg_b_status
    return _state_from_statuses(a_status, b_status)
