"""Exact isolated initial-margin reserve projection without venue authority."""

from dataclasses import dataclass

from dcabot.application.futures_grid_position import FuturesGridPositionState
from dcabot.domain.numbers import bounded, exact_text, number, positive


class FuturesGridMarginReserveError(ValueError):
    """Raised when an isolated reserve projection is not provable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FuturesGridMarginReserveProjection:
    """Required initial margin, not an exchange balance or reservation."""

    state: FuturesGridPositionState
    reference_price: str
    contract_size: str
    leverage: str
    notional: str
    required_initial_margin: str
    reserve_asset: str
    reserve_policy: str
    available_margin: str | None
    capacity_status: str


def project_futures_grid_margin_reserve(
    state: FuturesGridPositionState,
    *,
    reference_price: str,
    contract_size: str,
    available_margin: str | None = None,
    reserve_policy: str = "INITIAL_MARGIN_ONLY",
) -> FuturesGridMarginReserveProjection:
    """Project explicit isolated initial margin without mutating or reserving funds.

    The caller must provide contract size and a reference price. The result uses
    only ``notional / leverage``; maintenance margin, fees, funding, mark price,
    liquidation, venue balance and order authority are deliberately absent.
    """

    if not isinstance(state, FuturesGridPositionState):
        raise FuturesGridMarginReserveError(
            "FUTURES_GRID_MARGIN_STATE_INVALID",
            "Position state güvenli tipte olmalıdır.",
        )
    if state.position_side not in ("LONG", "SHORT"):
        raise FuturesGridMarginReserveError(
            "FUTURES_GRID_MARGIN_FLAT_POSITION",
            "Initial margin projection yalnız açık LONG veya SHORT position için yapılır.",
        )
    if reserve_policy != "INITIAL_MARGIN_ONLY":
        raise FuturesGridMarginReserveError(
            "FUTURES_GRID_RESERVE_POLICY_UNSUPPORTED",
            "Yalnız INITIAL_MARGIN_ONLY reserve policy desteklenir.",
        )
    try:
        price = positive(reference_price)
        multiplier = positive(contract_size)
        quantity = positive(state.quantity)
        leverage = positive(state.profile.leverage)
        available = None if available_margin is None else number(available_margin)
    except ValueError as error:
        raise FuturesGridMarginReserveError(
            "FUTURES_GRID_MARGIN_NUMERIC_INVALID",
            "Fiyat, contract-size ve margin alanları exact decimal olmalıdır.",
        ) from error
    if available is not None and available < 0:
        raise FuturesGridMarginReserveError(
            "FUTURES_GRID_AVAILABLE_MARGIN_INVALID",
            "Available margin negatif olamaz.",
        )

    try:
        notional = bounded(quantity * multiplier * price)
        required = bounded(notional / leverage)
        result = FuturesGridMarginReserveProjection(
            state=state,
            reference_price=exact_text(price),
            contract_size=exact_text(multiplier),
            leverage=exact_text(leverage),
            notional=exact_text(notional),
            required_initial_margin=exact_text(required),
            reserve_asset=state.profile.margin_asset,
            reserve_policy=reserve_policy,
            available_margin=None if available is None else exact_text(available),
            capacity_status=(
                "UNVERIFIED"
                if available is None
                else "ELIGIBLE"
                if available >= required
                else "INSUFFICIENT_AVAILABLE_MARGIN"
            ),
        )
    except ValueError as error:
        raise FuturesGridMarginReserveError(
            "FUTURES_GRID_MARGIN_NOT_EXACT",
            "Initial margin exact decimal sözleşmesinde temsil edilemiyor; rounding yapılmadı.",
        ) from error
    return result
