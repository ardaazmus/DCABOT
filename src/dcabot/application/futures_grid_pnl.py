"""Exact Futures Grid P&L projection from accepted fills and explicit events."""

from dataclasses import dataclass
import re

from dcabot.application.futures_grid_position import (
    FuturesGridFillSide,
    FuturesGridPositionState,
)
from dcabot.domain.numbers import bounded, exact_text, number, positive


_IDENTITY = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)


class FuturesGridPnlError(ValueError):
    """Raised when a Futures Grid P&L projection is not provable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FuturesGridFundingEvent:
    """One explicit signed funding cashflow, not a funding-rate estimate."""

    event_id: str
    effective_time_us: int
    asset: str
    cashflow: str

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or _IDENTITY.fullmatch(self.event_id) is None:
            raise FuturesGridPnlError("FUTURES_GRID_FUNDING_ID_INVALID", "Funding event kimliği geçersiz.")
        if type(self.effective_time_us) is not int or self.effective_time_us < 0:
            raise FuturesGridPnlError("FUTURES_GRID_FUNDING_TIME_INVALID", "Funding event zamanı geçersiz.")
        if not isinstance(self.asset, str) or _IDENTITY.fullmatch(self.asset) is None:
            raise FuturesGridPnlError("FUTURES_GRID_FUNDING_ASSET_INVALID", "Funding asset kimliği geçersiz.")
        try:
            amount = exact_text(number(self.cashflow))
        except ValueError as error:
            raise FuturesGridPnlError(
                "FUTURES_GRID_FUNDING_AMOUNT_INVALID",
                "Funding cashflow signed exact decimal olmalıdır.",
            ) from error
        object.__setattr__(self, "cashflow", amount)


@dataclass(frozen=True, slots=True)
class FuturesGridPnlProjection:
    """Signed local P&L split into matched-cycle and open-inventory parts."""

    state: FuturesGridPositionState
    settlement_asset: str
    contract_size: str
    mark_price: str
    as_of_time_us: int
    realized_gross_pnl: str
    unrealized_pnl: str
    funding_cashflow: str
    matched_cycle_profit: str
    total_pnl: str
    status: str = "LOCAL_PROJECTION_ONLY"


def project_futures_grid_pnl(
    state: FuturesGridPositionState,
    *,
    contract_size: str,
    mark_price: str,
    as_of_time_us: int,
    funding_events: tuple[FuturesGridFundingEvent, ...] = (),
) -> FuturesGridPnlProjection:
    """Project P&L without balance, liquidation, order, or venue authority.

    ``matched_cycle_profit`` excludes the current open inventory. ``total_pnl``
    adds its mark-to-entry movement and explicit signed funding cashflow. Fees,
    maintenance margin, and an exchange-provided mark/funding rate are absent.
    """

    if not isinstance(state, FuturesGridPositionState):
        raise FuturesGridPnlError(
            "FUTURES_GRID_PNL_STATE_INVALID", "Position state güvenli tipte olmalıdır."
        )
    if type(as_of_time_us) is not int or as_of_time_us < 0:
        raise FuturesGridPnlError("FUTURES_GRID_PNL_TIME_INVALID", "P&L snapshot zamanı geçersiz.")
    try:
        multiplier = positive(contract_size)
        mark = positive(mark_price)
    except ValueError as error:
        raise FuturesGridPnlError(
            "FUTURES_GRID_PNL_NUMERIC_INVALID",
            "Contract-size ve mark price pozitif exact decimal olmalıdır.",
        ) from error
    if any(item.effective_time_us > as_of_time_us for item in state.fills):
        raise FuturesGridPnlError(
            "FUTURES_GRID_PNL_FILL_AFTER_SNAPSHOT",
            "P&L snapshot zamanı accepted fill zamanından önce olamaz.",
        )
    if not isinstance(funding_events, tuple):
        raise FuturesGridPnlError(
            "FUTURES_GRID_FUNDING_SEQUENCE_INVALID",
            "Funding events immutable tuple olmalıdır.",
        )

    funding_total = number("0")
    prior_events: dict[str, FuturesGridFundingEvent] = {}
    prior_time = -1
    for event in funding_events:
        if not isinstance(event, FuturesGridFundingEvent):
            raise FuturesGridPnlError(
                "FUTURES_GRID_FUNDING_INVALID", "Funding event güvenli tipte olmalıdır."
            )
        if event.asset != state.profile.settlement_asset:
            raise FuturesGridPnlError(
                "FUTURES_GRID_FUNDING_ASSET_MISMATCH",
                "Funding asset selected settlement asset ile eşleşmiyor.",
            )
        if event.effective_time_us > as_of_time_us:
            raise FuturesGridPnlError(
                "FUTURES_GRID_FUNDING_AFTER_SNAPSHOT",
                "Funding event snapshot zamanından sonra olamaz.",
            )
        previous = prior_events.get(event.event_id)
        if previous is not None:
            if previous != event:
                raise FuturesGridPnlError(
                    "FUTURES_GRID_FUNDING_CONFLICT",
                    "Aynı funding event kimliği farklı payload ile kullanılamaz.",
                )
            continue
        if event.effective_time_us < prior_time:
            raise FuturesGridPnlError(
                "FUTURES_GRID_FUNDING_ORDER",
                "Funding event zamanı geriye gidemez.",
            )
        prior_events[event.event_id] = event
        prior_time = event.effective_time_us
        funding_total = bounded(funding_total + number(event.cashflow))

    quantity = number("0")
    average_entry = None
    realized = number("0")
    opening_side = FuturesGridFillSide.BUY if state.direction == "LONG" else FuturesGridFillSide.SELL
    for fill in state.fills:
        fill_quantity = positive(fill.quantity)
        fill_price = positive(fill.price)
        if fill.side is opening_side:
            if average_entry is None:
                average_entry = fill_price
            else:
                average_entry = bounded(
                    (quantity * average_entry + fill_quantity * fill_price)
                    / (quantity + fill_quantity)
                )
            quantity = bounded(quantity + fill_quantity)
            continue
        signed_movement = (
            fill_price - (average_entry or number("0"))
            if state.direction == "LONG"
            else (average_entry or number("0")) - fill_price
        )
        realized = bounded(realized + fill_quantity * multiplier * signed_movement)
        quantity = bounded(quantity - fill_quantity)
        if not quantity:
            average_entry = None

    if state.position_side == "FLAT":
        unrealized = number("0")
    else:
        if average_entry is None:
            raise FuturesGridPnlError(
                "FUTURES_GRID_PNL_AVERAGE_MISSING",
                "Açık position için average entry bulunamadı.",
            )
        movement = mark - average_entry
        if state.direction == "SHORT":
            movement = -movement
        unrealized = bounded(quantity * multiplier * movement)
    matched = bounded(realized + funding_total)
    total = bounded(matched + unrealized)
    try:
        return FuturesGridPnlProjection(
            state=state,
            settlement_asset=state.profile.settlement_asset,
            contract_size=exact_text(multiplier),
            mark_price=exact_text(mark),
            as_of_time_us=as_of_time_us,
            realized_gross_pnl=exact_text(realized),
            unrealized_pnl=exact_text(unrealized),
            funding_cashflow=exact_text(funding_total),
            matched_cycle_profit=exact_text(matched),
            total_pnl=exact_text(total),
        )
    except ValueError as error:
        raise FuturesGridPnlError(
            "FUTURES_GRID_PNL_NOT_EXACT",
            "P&L sonucu exact decimal sözleşmesinde temsil edilemiyor; rounding yapılmadı.",
        ) from error
