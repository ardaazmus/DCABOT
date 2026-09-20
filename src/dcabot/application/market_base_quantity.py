"""Exact offline economics for explicit base-quantity MARKET fills."""

from dataclasses import dataclass, replace
from enum import StrEnum
import re

from dcabot.application.spot_order_lifecycle import SpotSide
from dcabot.domain.numbers import exact_text, number, positive


class MarketBaseExecutionError(ValueError):
    """Raised when a base-quantity MARKET execution breaks its contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class MarketExecutionStatus(StrEnum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"


class MarketExecutionOutcome(StrEnum):
    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True, slots=True)
class MarketFill:
    """One exact execution; quote quantity is gross, positive notional."""

    execution_id: str
    base_quantity: str
    quote_quantity: str
    effective_price: str
    fee: str
    fee_asset: str


@dataclass(frozen=True, slots=True)
class MarketExecutionResult:
    execution: "MarketBaseExecution"
    outcome: MarketExecutionOutcome


@dataclass(frozen=True, slots=True)
class MarketBaseExecution:
    """Immutable base-quantity MARKET economics without core/order authority."""

    order_id: str
    symbol: str
    side: SpotSide
    requested_quantity: str
    reference_price: str
    max_slippage_bps: int
    status: MarketExecutionStatus = MarketExecutionStatus.NEW
    fills: tuple[MarketFill, ...] = ()

    def __post_init__(self) -> None:
        _identifier(self.order_id, "MARKET_ORDER_ID_INVALID")
        _symbol(self.symbol)
        try:
            object.__setattr__(self, "side", SpotSide(self.side))
            status = MarketExecutionStatus(self.status)
            object.__setattr__(self, "status", status)
            requested = positive(self.requested_quantity)
            positive(self.reference_price)
        except (TypeError, ValueError) as exc:
            raise MarketBaseExecutionError(
                "MARKET_EXECUTION_INPUT_INVALID", "MARKET execution girdisi geçersiz."
            ) from exc
        if type(self.max_slippage_bps) is not int or not 0 <= self.max_slippage_bps <= 10_000:
            raise MarketBaseExecutionError(
                "MARKET_SLIPPAGE_POLICY_INVALID", "Slippage bps 0..10000 integer olmalıdır."
            )
        if sum(number(fill.base_quantity) for fill in self.fills) > requested:
            raise MarketBaseExecutionError(
                "MARKET_FILL_OVERFLOW", "Toplam base fill istenen miktarı aşamaz."
            )

    @property
    def cumulative_base_quantity(self) -> str:
        return exact_text(sum(number(fill.base_quantity) for fill in self.fills))

    @property
    def cumulative_quote_quantity(self) -> str:
        return exact_text(sum(number(fill.quote_quantity) for fill in self.fills))

    @property
    def effective_price_fraction(self):
        base = number(self.cumulative_base_quantity)
        if not base:
            return None
        return number(self.cumulative_quote_quantity) / base

    @property
    def effective_price(self) -> str | None:
        value = self.effective_price_fraction
        return exact_text(value) if value is not None else None

    @property
    def remaining_quantity(self) -> str:
        return exact_text(number(self.requested_quantity) - number(self.cumulative_base_quantity))

    @property
    def fee_totals(self) -> tuple[tuple[str, str], ...]:
        totals: dict[str, object] = {}
        for fill in self.fills:
            totals[fill.fee_asset] = totals.get(fill.fee_asset, 0) + number(fill.fee)
        return tuple((asset, exact_text(totals[asset])) for asset in sorted(totals))

    def apply_fill(
        self,
        *,
        execution_id: str,
        base_quantity: str,
        quote_quantity: str,
        fee: str,
        fee_asset: str,
    ) -> MarketExecutionResult:
        """Accept one exact fill after quantity, price and slippage checks."""

        _identifier(execution_id, "MARKET_EXECUTION_ID_INVALID")
        try:
            base = positive(base_quantity)
            quote = positive(quote_quantity)
            fee_value = number(fee)
        except ValueError as exc:
            raise MarketBaseExecutionError(
                "MARKET_FILL_INPUT_INVALID", "MARKET fill decimal alanları geçersiz."
            ) from exc
        if fee_value < 0 or not isinstance(fee_asset, str) or not 1 <= len(fee_asset) <= 32:
            raise MarketBaseExecutionError("MARKET_FILL_INPUT_INVALID", "Fee alanı geçersiz.")
        if any(ord(char) < 0x20 or ord(char) == 0x7F for char in fee_asset):
            raise MarketBaseExecutionError("MARKET_FILL_INPUT_INVALID", "Fee asset kontrol karakteri taşıyor.")
        effective = quote / base
        reference = number(self.reference_price)
        if self.side is SpotSide.BUY and effective > reference * (10_000 + self.max_slippage_bps) / 10_000:
            raise MarketBaseExecutionError("MARKET_SLIPPAGE_EXCEEDED", "BUY effective price slippage sınırını aşıyor.")
        if self.side is SpotSide.SELL and effective < reference * (10_000 - self.max_slippage_bps) / 10_000:
            raise MarketBaseExecutionError("MARKET_SLIPPAGE_EXCEEDED", "SELL effective price slippage sınırını aşıyor.")
        try:
            fill = MarketFill(
                execution_id=execution_id,
                base_quantity=exact_text(base),
                quote_quantity=exact_text(quote),
                effective_price=exact_text(effective),
                fee=exact_text(fee_value),
                fee_asset=fee_asset,
            )
        except ValueError as exc:
            raise MarketBaseExecutionError(
                "MARKET_FILL_NOT_EXACT", "MARKET fill external decimal sözleşmesine sığmıyor."
            ) from exc
        for prior in self.fills:
            if prior.execution_id == execution_id:
                if prior == fill:
                    return MarketExecutionResult(self, MarketExecutionOutcome.DUPLICATE)
                raise MarketBaseExecutionError("MARKET_FILL_CONFLICT", "Execution kimliği farklı payload ile tekrarlandı.")
        if number(self.cumulative_base_quantity) + base > number(self.requested_quantity):
            raise MarketBaseExecutionError("MARKET_FILL_OVERFLOW", "Toplam base fill istenen miktarı aşamaz.")
        return MarketExecutionResult(
            replace(self, status=MarketExecutionStatus.PARTIALLY_FILLED, fills=(*self.fills, fill)),
            MarketExecutionOutcome.ACCEPTED,
        )

    def close(self, status: MarketExecutionStatus) -> "MarketBaseExecution":
        """Close only with explicit venue coverage; residual remains visible."""

        try:
            status = MarketExecutionStatus(status)
        except (TypeError, ValueError) as exc:
            raise MarketBaseExecutionError("MARKET_STATUS_INVALID", "MARKET terminal status geçersiz.") from exc
        if status not in {MarketExecutionStatus.FILLED, MarketExecutionStatus.CANCELED, MarketExecutionStatus.EXPIRED}:
            raise MarketBaseExecutionError("MARKET_STATUS_INVALID", "Yalnız terminal status kabul edilir.")
        if self.status in {MarketExecutionStatus.FILLED, MarketExecutionStatus.CANCELED, MarketExecutionStatus.EXPIRED}:
            raise MarketBaseExecutionError("MARKET_TERMINAL_EVENT", "Terminal MARKET execution tekrar kapanamaz.")
        if status is MarketExecutionStatus.FILLED and number(self.cumulative_base_quantity) != number(self.requested_quantity):
            raise MarketBaseExecutionError("MARKET_FILL_COVERAGE_INVALID", "FILLED base miktarı istenen miktarı karşılamıyor.")
        return replace(self, status=status)


def create_market_base_execution(
    *,
    order_id: str,
    symbol: str,
    side: SpotSide,
    requested_quantity: str,
    reference_price: str,
    max_slippage_bps: int,
) -> MarketBaseExecution:
    """Create the deliberately narrow MARKET/BASE_QUANTITY contract."""

    try:
        SpotSide(side)
    except (TypeError, ValueError) as exc:
        raise MarketBaseExecutionError("MARKET_SIDE_INVALID", "MARKET side geçersiz.") from exc
    return MarketBaseExecution(
        order_id=order_id,
        symbol=symbol,
        side=side,
        requested_quantity=requested_quantity,
        reference_price=reference_price,
        max_slippage_bps=max_slippage_bps,
    )


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)


def _identifier(value: object, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise MarketBaseExecutionError(code, "Kimlik geçersiz.")


def _symbol(value: object) -> None:
    if not isinstance(value, str) or not 1 <= len(value) <= 32 or value != value.strip() or any(
        ord(char) < 0x20 or ord(char) == 0x7F for char in value
    ):
        raise MarketBaseExecutionError("MARKET_SYMBOL_INVALID", "Symbol bounded metin olmalıdır.")
