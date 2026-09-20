"""Read-only quote-fee spot-grid cycle and equity projection."""

from dataclasses import dataclass
from enum import StrEnum
import re

from dcabot.application.spot_inventory_projection import (
    SpotFill,
    SpotFillSide,
    SpotInventoryError,
    SpotInventoryState,
    apply_accepted_spot_fill,
)
from dcabot.domain.numbers import Q, bounded, exact_text, number, positive


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)
_ASSET = re.compile(r"[A-Z0-9]{1,24}\Z", re.ASCII)
_EXACT_NO_ROUNDING = "EXACT_NO_ROUNDING"


class SpotGridCycleError(ValueError):
    """Raised when a spot-grid economic projection is unsafe."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class SpotGridCycleStatus(StrEnum):
    """Read-only projection status."""

    READY = "READY"


@dataclass(frozen=True, slots=True)
class SpotGridFeeProfile:
    """Explicit quote-asset fee policy for the first offline spot profile."""

    fee_asset: str
    fee_rate: str
    fee_quantum: str
    profile_revision: str
    rounding_mode: str = _EXACT_NO_ROUNDING

    def __post_init__(self) -> None:
        if not isinstance(self.fee_asset, str) or _ASSET.fullmatch(self.fee_asset) is None:
            raise SpotGridCycleError(
                "SPOT_GRID_FEE_ASSET_INVALID",
                "fee_asset açık bir büyük harfli asset kodu olmalıdır.",
            )
        if (
            not isinstance(self.profile_revision, str)
            or _IDENTIFIER.fullmatch(self.profile_revision) is None
        ):
            raise SpotGridCycleError(
                "SPOT_GRID_FEE_PROFILE_INVALID",
                "profile_revision açık bir identifier taşımalıdır.",
            )
        if self.rounding_mode != _EXACT_NO_ROUNDING:
            raise SpotGridCycleError(
                "SPOT_GRID_FEE_ROUNDING_UNSUPPORTED",
                "İlk spot profili yalnız exact, sessiz yuvarlamasız hesap taşır.",
            )
        try:
            fee_rate = number(self.fee_rate)
            fee_quantum = number(self.fee_quantum)
        except ValueError as error:
            raise SpotGridCycleError(
                "SPOT_GRID_FEE_NUMERIC_INVALID",
                "Fee rate ve quantum exact decimal olmalıdır.",
            ) from error
        if not 0 <= fee_rate < 1:
            raise SpotGridCycleError(
                "SPOT_GRID_FEE_RATE_INVALID",
                "Fee rate 0 dahil, 1 hariç aralıkta olmalıdır.",
            )
        if fee_quantum != 0:
            raise SpotGridCycleError(
                "SPOT_GRID_FEE_QUANTUM_UNSUPPORTED",
                "Venue fee quantum profili doğrulanmadan yuvarlama yapılamaz.",
            )
        object.__setattr__(self, "fee_rate", exact_text(fee_rate))
        object.__setattr__(self, "fee_quantum", exact_text(fee_quantum))


@dataclass(frozen=True, slots=True)
class SpotGridCycleEvaluation:
    """Matched realized profit and mark-to-market equity kept separate."""

    status: SpotGridCycleStatus
    matched_cycle_profit_quote: str
    total_equity_quote: str
    open_inventory_mark_quote: str
    quote_cashflow_after_cycle: str
    fee_quote: str
    profile_revision: str
    reason: str
    order_authority: str = "NONE"

    def __post_init__(self) -> None:
        if self.order_authority != "NONE":
            raise SpotGridCycleError(
                "SPOT_GRID_CYCLE_ORDER_AUTHORITY_INVALID",
                "Projection order veya mutation authority taşıyamaz.",
            )


def project_spot_grid_cycle(
    state: SpotInventoryState,
    *,
    buy_fill: SpotFill,
    sell_fill: SpotFill,
    fee_profile: SpotGridFeeProfile,
    mark_price: str,
) -> SpotGridCycleEvaluation:
    """Project one accepted buy/sell pair without persistence or order authority.

    Grid profit is the quote-asset net of the matched pair. Total equity is the
    post-cycle quote cashflow plus the remaining base inventory at the explicit
    mark price; it is not a second name for cycle profit.
    """

    if not isinstance(state, SpotInventoryState):
        raise SpotGridCycleError("SPOT_GRID_STATE_INVALID", "Inventory state geçersiz.")
    if not isinstance(buy_fill, SpotFill) or not isinstance(sell_fill, SpotFill):
        raise SpotGridCycleError("SPOT_GRID_FILL_INVALID", "Buy ve sell fill geçersiz.")
    if not isinstance(fee_profile, SpotGridFeeProfile):
        raise SpotGridCycleError("SPOT_GRID_FEE_PROFILE_INVALID", "Fee profili geçersiz.")
    if buy_fill.side is not SpotFillSide.BUY or sell_fill.side is not SpotFillSide.SELL:
        raise SpotGridCycleError(
            "SPOT_GRID_CYCLE_SIDE_INVALID", "Matched cycle buy sonra sell olmalıdır."
        )
    if buy_fill.fill_id == sell_fill.fill_id:
        raise SpotGridCycleError(
            "SPOT_GRID_CYCLE_ID_INVALID", "Buy ve sell farklı accepted fill kimlikleri taşımalıdır."
        )
    if any(fill.fill_id in {buy_fill.fill_id, sell_fill.fill_id} for fill in state.fills):
        raise SpotGridCycleError(
            "SPOT_GRID_CYCLE_DUPLICATE_UNSAFE",
            "State fee posting taşımadığı için önceden projekte edilmiş fill tekrar ücretlenemez.",
        )
    if state.quote_asset != fee_profile.fee_asset:
        raise SpotGridCycleError(
            "SPOT_GRID_FEE_ASSET_UNSUPPORTED",
            "İlk profil yalnız state quote asset’inde fee kabul eder.",
        )

    try:
        buy_price = positive(buy_fill.price)
        sell_price = positive(sell_fill.price)
        buy_quantity = positive(buy_fill.base_quantity)
        sell_quantity = positive(sell_fill.base_quantity)
        mark = positive(mark_price)
        fee_rate = number(fee_profile.fee_rate)
        if buy_quantity != sell_quantity or sell_price <= buy_price:
            raise SpotGridCycleError(
                "SPOT_GRID_CYCLE_MATCH_INVALID",
                "Matched cycle aynı miktarı ve üst seviyede sell fiyatını taşımalıdır.",
            )
        after_buy = apply_accepted_spot_fill(state, buy_fill)
        after_cycle = apply_accepted_spot_fill(after_buy, sell_fill)
        buy_notional = bounded(buy_price * buy_quantity)
        sell_notional = bounded(sell_price * sell_quantity)
        fee = bounded((buy_notional + sell_notional) * fee_rate)
        cycle_profit = bounded(sell_notional - buy_notional - fee)
        quote_after = bounded(number(after_cycle.quote_cashflow) - fee)
        inventory_mark = bounded(number(after_cycle.base_quantity) * mark)
        total_equity = bounded(quote_after + inventory_mark)
        return SpotGridCycleEvaluation(
            status=SpotGridCycleStatus.READY,
            matched_cycle_profit_quote=exact_text(cycle_profit),
            total_equity_quote=exact_text(total_equity),
            open_inventory_mark_quote=exact_text(inventory_mark),
            quote_cashflow_after_cycle=exact_text(quote_after),
            fee_quote=exact_text(fee),
            profile_revision=fee_profile.profile_revision,
            reason="QUOTE_ASSET_FEE_EXACT_NO_ROUNDING",
        )
    except SpotInventoryError as error:
        raise SpotGridCycleError(error.code, str(error)) from error
    except ValueError as error:
        if isinstance(error, SpotGridCycleError):
            raise
        raise SpotGridCycleError(
            "SPOT_GRID_CYCLE_UNREPRESENTABLE",
            "Cycle sonucu exact decimal sözleşmesine sığmıyor.",
        ) from error
