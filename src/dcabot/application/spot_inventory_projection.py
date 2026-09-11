"""Exact spot inventory projection for already accepted fills."""

from dataclasses import dataclass
from enum import StrEnum
import re

from dcabot.domain.numbers import Q, bounded, exact_text, number, positive


_IDENTITY = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
_ASSET = re.compile(r"[A-Z0-9]{1,24}\Z", re.ASCII)


class SpotInventoryError(ValueError):
    """Raised when an accepted spot fill cannot be projected safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class SpotFillSide(StrEnum):
    """The two spot fill directions and their inventory effects."""

    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True, slots=True)
class SpotFill:
    """One already accepted fill, not a pending order or an observation."""

    fill_id: str
    side: SpotFillSide
    price: str
    base_quantity: str


@dataclass(frozen=True, slots=True)
class SpotInventoryState:
    """Base inventory and signed quote cashflow after accepted fills."""

    base_asset: str
    quote_asset: str
    base_quantity: str
    quote_cashflow: str
    fills: tuple[SpotFill, ...]


def _asset(value: str, field_name: str) -> str:
    if not isinstance(value, str) or _ASSET.fullmatch(value) is None:
        raise SpotInventoryError(
            "SPOT_ASSET_INVALID", f"{field_name} büyük harfli asset kodu olmalıdır."
        )
    return value


def _non_negative(value: str, field_name: str) -> Q:
    try:
        result = number(value)
    except ValueError as error:
        raise SpotInventoryError(
            "SPOT_QUANTITY_INVALID", f"{field_name} decimal string olmalıdır."
        ) from error
    if result < 0:
        raise SpotInventoryError(
            "SPOT_QUANTITY_INVALID", f"{field_name} negatif olamaz."
        )
    return bounded(result)


def new_spot_inventory_state(
    *, base_asset: str, quote_asset: str, base_quantity: str = "0"
) -> SpotInventoryState:
    """Create an exact inventory projection with zero quote cashflow."""

    normalized_base_asset = _asset(base_asset, "base_asset")
    normalized_quote_asset = _asset(quote_asset, "quote_asset")
    if normalized_base_asset == normalized_quote_asset:
        raise SpotInventoryError(
            "SPOT_ASSET_INVALID", "base_asset ve quote_asset farklı olmalıdır."
        )
    try:
        return SpotInventoryState(
            base_asset=normalized_base_asset,
            quote_asset=normalized_quote_asset,
            base_quantity=exact_text(_non_negative(base_quantity, "base_quantity")),
            quote_cashflow="0",
            fills=(),
        )
    except ValueError as error:
        raise SpotInventoryError(
            "SPOT_STATE_UNREPRESENTABLE",
            "Başlangıç envanteri exact decimal sözleşmesine sığmıyor.",
        ) from error


def apply_accepted_spot_fill(
    state: SpotInventoryState, fill: SpotFill
) -> SpotInventoryState:
    """Apply one accepted fill with exact inventory conservation.

    BUY increases base quantity and decreases quote cashflow; SELL consumes
    owned base quantity and increases quote cashflow. Fee, order state, reserve,
    replacement and total-equity semantics intentionally remain outside this
    projection until their asset and rounding owners are explicit.
    """

    if not isinstance(state, SpotInventoryState) or not isinstance(fill, SpotFill):
        raise SpotInventoryError("SPOT_INPUT_INVALID", "State veya fill sözleşmesi geçersiz.")
    if _IDENTITY.fullmatch(fill.fill_id) is None:
        raise SpotInventoryError("SPOT_FILL_ID_INVALID", "fill_id geçerli bir kimlik olmalıdır.")
    if not isinstance(fill.side, SpotFillSide):
        raise SpotInventoryError("SPOT_SIDE_INVALID", "Spot fill yönü geçersiz.")
    try:
        price = positive(fill.price)
        base_quantity = positive(fill.base_quantity)
        current_base = _non_negative(state.base_quantity, "base_quantity")
        current_quote = number(state.quote_cashflow)
    except ValueError as error:
        raise SpotInventoryError(
            "SPOT_FILL_INVALID", "Fill ve state miktarları exact decimal olmalıdır."
        ) from error

    canonical_fill = SpotFill(
        fill_id=fill.fill_id,
        side=fill.side,
        price=exact_text(price),
        base_quantity=exact_text(base_quantity),
    )
    for previous in state.fills:
        if previous.fill_id == canonical_fill.fill_id:
            if previous == canonical_fill:
                return state
            raise SpotInventoryError(
                "SPOT_FILL_CONFLICT", "Aynı fill_id farklı ekonomik kayıtla tekrarlandı."
            )

    quote_amount = bounded(price * base_quantity)
    if fill.side is SpotFillSide.BUY:
        next_base = bounded(current_base + base_quantity)
        next_quote = bounded(current_quote - quote_amount)
    else:
        if base_quantity > current_base:
            raise SpotInventoryError(
                "SPOT_INVENTORY_INSUFFICIENT",
                "Sell fill mevcut sahip olunan base envanterini aşamaz.",
            )
        next_base = bounded(current_base - base_quantity)
        next_quote = bounded(current_quote + quote_amount)

    try:
        return SpotInventoryState(
            base_asset=state.base_asset,
            quote_asset=state.quote_asset,
            base_quantity=exact_text(next_base),
            quote_cashflow=exact_text(next_quote),
            fills=(*state.fills, canonical_fill),
        )
    except ValueError as error:
        raise SpotInventoryError(
            "SPOT_RESULT_UNREPRESENTABLE",
            "Spot inventory sonucu exact decimal sözleşmesine sığmıyor.",
        ) from error
