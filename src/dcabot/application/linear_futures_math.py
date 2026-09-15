"""Exact, profile-neutral linear futures PnL and funding projections."""

from dataclasses import dataclass
import re

from dcabot.domain.numbers import bounded, exact_text, number, positive


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)


class LinearFuturesError(ValueError):
    """Raised when an explicit linear-futures projection is not representable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class LinearFuturesPosition:
    """One linear position with an explicit contract-to-base quantity factor."""

    side: str
    quantity: str
    contract_size: str
    entry_price: str
    mark_price: str
    settlement_asset: str

    def __post_init__(self) -> None:
        if self.side not in ("LONG", "SHORT"):
            raise LinearFuturesError(
                "LINEAR_FUTURES_SIDE_INVALID", "Side LONG veya SHORT olmalıdır."
            )
        for field, value in (
            ("quantity", self.quantity),
            ("contract_size", self.contract_size),
            ("entry_price", self.entry_price),
            ("mark_price", self.mark_price),
        ):
            try:
                canonical = exact_text(positive(value))
            except ValueError as error:
                raise LinearFuturesError(
                    "LINEAR_FUTURES_NUMERIC_INVALID",
                    f"{field} pozitif exact decimal olmalıdır.",
                ) from error
            object.__setattr__(self, field, canonical)
        if not isinstance(self.settlement_asset, str) or _IDENTIFIER.fullmatch(
            self.settlement_asset
        ) is None:
            raise LinearFuturesError(
                "LINEAR_FUTURES_ASSET_INVALID", "Settlement asset kimliği geçersiz."
            )

    @property
    def effective_quantity(self) -> str:
        """Return base-equivalent quantity after applying contract size."""

        return exact_text(bounded(positive(self.quantity) * positive(self.contract_size)))

    @property
    def position_value(self) -> str:
        """Return mark notional in the declared settlement asset."""

        return exact_text(
            bounded(positive(self.effective_quantity) * positive(self.mark_price))
        )

    @property
    def unrealized_pnl(self) -> str:
        """Return signed mark-to-entry PnL without a leverage multiplier."""

        movement = positive(self.mark_price) - positive(self.entry_price)
        signed_movement = movement if self.side == "LONG" else -movement
        return exact_text(bounded(positive(self.effective_quantity) * signed_movement))


@dataclass(frozen=True, slots=True)
class LinearCloseProjection:
    """One partial or full close without fee/funding allocation."""

    closed_quantity: str
    remaining_quantity: str
    closed_effective_quantity: str
    realized_gross_pnl: str
    settlement_asset: str
    exit_price: str


def project_partial_close(
    position: LinearFuturesPosition, close_quantity: str, exit_price: str
) -> LinearCloseProjection:
    """Project quantity conservation and gross PnL for one close fill."""

    if not isinstance(position, LinearFuturesPosition):
        raise LinearFuturesError(
            "LINEAR_FUTURES_POSITION_INVALID", "Linear futures position geçersiz."
        )
    try:
        requested = positive(close_quantity)
        price = positive(exit_price)
    except ValueError as error:
        raise LinearFuturesError(
            "LINEAR_FUTURES_CLOSE_NUMERIC_INVALID",
            "Close quantity ve exit price pozitif exact decimal olmalıdır.",
        ) from error
    available = positive(position.quantity)
    if requested > available:
        raise LinearFuturesError(
            "LINEAR_FUTURES_CLOSE_OVERFLOW",
            "Close quantity açık contract quantity değerini aşamaz.",
        )
    remaining = bounded(available - requested)
    movement = price - positive(position.entry_price)
    signed_movement = movement if position.side == "LONG" else -movement
    effective = bounded(requested * positive(position.contract_size))
    return LinearCloseProjection(
        closed_quantity=exact_text(requested),
        remaining_quantity=exact_text(remaining),
        closed_effective_quantity=exact_text(effective),
        realized_gross_pnl=exact_text(bounded(effective * signed_movement)),
        settlement_asset=position.settlement_asset,
        exit_price=exact_text(price),
    )


@dataclass(frozen=True, slots=True)
class LinearLedgerEvent:
    """One typed fee or funding event before persistence/replay binding."""

    event_id: str
    event_type: str
    effective_time_us: int
    settlement_asset: str
    amount: str

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or _IDENTIFIER.fullmatch(self.event_id) is None:
            raise LinearFuturesError("LINEAR_LEDGER_EVENT_ID_INVALID", "Ledger event kimliği geçersiz.")
        if self.event_type not in ("TRADING_FEE", "FUNDING"):
            raise LinearFuturesError("LINEAR_LEDGER_EVENT_TYPE_INVALID", "Ledger event türü geçersiz.")
        if type(self.effective_time_us) is not int or self.effective_time_us < 0:
            raise LinearFuturesError("LINEAR_LEDGER_TIME_INVALID", "Ledger event zamanı geçersiz.")
        if not isinstance(self.settlement_asset, str) or _IDENTIFIER.fullmatch(self.settlement_asset) is None:
            raise LinearFuturesError("LINEAR_LEDGER_ASSET_INVALID", "Ledger asset kimliği geçersiz.")
        try:
            canonical = (
                exact_text(positive(self.amount))
                if self.event_type == "TRADING_FEE"
                else exact_text(number(self.amount))
            )
        except ValueError as error:
            raise LinearFuturesError("LINEAR_LEDGER_AMOUNT_INVALID", "Ledger amount exact decimal olmalıdır.") from error
        object.__setattr__(self, "amount", canonical)


@dataclass(frozen=True, slots=True)
class LinearLedgerState:
    """Immutable fee/funding totals and their ordered event identity set."""

    settlement_asset: str
    fee_expense: str = "0"
    funding_cashflow: str = "0"
    events: tuple[LinearLedgerEvent, ...] = ()


def new_linear_ledger_state(settlement_asset: str) -> LinearLedgerState:
    """Create an empty ledger state for one explicit settlement asset."""

    if not isinstance(settlement_asset, str) or _IDENTIFIER.fullmatch(settlement_asset) is None:
        raise LinearFuturesError("LINEAR_LEDGER_ASSET_INVALID", "Settlement asset kimliği geçersiz.")
    return LinearLedgerState(settlement_asset=settlement_asset)


def apply_linear_ledger_event(
    state: LinearLedgerState, event: LinearLedgerEvent
) -> LinearLedgerState:
    """Apply one ordered event, making exact duplicates a no-op."""

    if not isinstance(state, LinearLedgerState) or not isinstance(event, LinearLedgerEvent):
        raise LinearFuturesError("LINEAR_LEDGER_INPUT_INVALID", "Ledger state veya event geçersiz.")
    if event.settlement_asset != state.settlement_asset:
        raise LinearFuturesError(
            "LINEAR_LEDGER_ASSET_INVALID", "Ledger event settlement asset ile eşleşmiyor."
        )
    prior = next((item for item in state.events if item.event_id == event.event_id), None)
    if prior is not None:
        if prior != event:
            raise LinearFuturesError(
                "LINEAR_LEDGER_DUPLICATE_CONFLICT",
                "Aynı ledger event kimliği farklı payload ile kullanılamaz.",
            )
        return state
    if state.events and event.effective_time_us < state.events[-1].effective_time_us:
        raise LinearFuturesError(
            "LINEAR_LEDGER_EVENT_ORDER", "Yeni ledger event zamanı geriye gidemez."
        )
    fee = number(state.fee_expense)
    funding = number(state.funding_cashflow)
    if event.event_type == "TRADING_FEE":
        fee = bounded(fee + positive(event.amount))
    else:
        funding = bounded(funding + number(event.amount))
    return LinearLedgerState(
        settlement_asset=state.settlement_asset,
        fee_expense=exact_text(fee),
        funding_cashflow=exact_text(funding),
        events=state.events + (event,),
    )


def net_realized_result(gross_realized: str, state: LinearLedgerState) -> str:
    """Combine gross close PnL with separate fee expense and funding cashflow."""

    if not isinstance(state, LinearLedgerState):
        raise LinearFuturesError("LINEAR_LEDGER_INPUT_INVALID", "Ledger state geçersiz.")
    try:
        gross = number(gross_realized)
    except ValueError as error:
        raise LinearFuturesError("LINEAR_LEDGER_AMOUNT_INVALID", "Gross PnL exact decimal olmalıdır.") from error
    return exact_text(
        bounded(gross - number(state.fee_expense) + number(state.funding_cashflow))
    )


@dataclass(frozen=True, slots=True)
class FundingProjection:
    """One timestamped signed funding cashflow in settlement-asset units."""

    effective_time_us: int
    settlement_asset: str
    amount: str

    @property
    def core_expense(self) -> str:
        """Return the same event in the core reducer's expense-positive convention."""

        return funding_expense_from_cashflow(self.amount)


def funding_expense_from_cashflow(funding_cashflow: str) -> str:
    """Convert receipt-positive funding cashflow to core expense-positive form."""

    try:
        return exact_text(bounded(-number(funding_cashflow)))
    except ValueError as error:
        raise LinearFuturesError(
            "FUNDING_CASHFLOW_INVALID", "Funding cashflow exact decimal olmalıdır."
        ) from error


def project_funding(
    position: LinearFuturesPosition,
    funding_rate: str,
    *,
    effective_time_us: int,
) -> FundingProjection:
    """Project one funding event; positive rate charges long and credits short."""

    if not isinstance(position, LinearFuturesPosition):
        raise LinearFuturesError(
            "LINEAR_FUTURES_POSITION_INVALID", "Linear futures position geçersiz."
        )
    if type(effective_time_us) is not int or effective_time_us < 0:
        raise LinearFuturesError(
            "FUNDING_TIME_INVALID", "Funding effective time negatif olmayan integer olmalıdır."
        )
    try:
        rate = number(funding_rate)
    except ValueError as error:
        raise LinearFuturesError(
            "FUNDING_RATE_INVALID", "Funding rate exact decimal olmalıdır."
        ) from error
    direction = 1 if position.side == "LONG" else -1
    amount = bounded(-direction * positive(position.position_value) * rate)
    return FundingProjection(
        effective_time_us=effective_time_us,
        settlement_asset=position.settlement_asset,
        amount=exact_text(amount),
    )
