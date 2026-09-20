"""Fixed-tier isolated liquidation estimates; never a venue liquidation engine."""

from dataclasses import dataclass
import re

from dcabot.domain.numbers import bounded, exact_text, number, positive


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)


class IsolatedLiquidationError(ValueError):
    """Raised when an isolated liquidation estimate is not provable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class IsolatedRiskTier:
    """One immutable maintenance-margin bracket snapshot."""

    tier_id: str
    notional_floor: str
    notional_cap: str | None
    maintenance_rate: str
    maintenance_amount: str
    effective_time_us: int

    def __post_init__(self) -> None:
        if not isinstance(self.tier_id, str) or _IDENTIFIER.fullmatch(self.tier_id) is None:
            raise IsolatedLiquidationError("LIQUIDATION_TIER_ID_INVALID", "Risk tier kimliği geçersiz.")
        try:
            floor = number(self.notional_floor)
            cap = None if self.notional_cap is None else positive(self.notional_cap)
            rate = number(self.maintenance_rate)
            amount = number(self.maintenance_amount)
        except ValueError as error:
            raise IsolatedLiquidationError("LIQUIDATION_TIER_NUMERIC_INVALID", "Risk tier sayısal alanı geçersiz.") from error
        if floor < 0 or (cap is not None and floor >= cap) or not 0 <= rate < 1 or amount < 0:
            raise IsolatedLiquidationError("LIQUIDATION_TIER_INVALID", "Risk tier sınırları geçersiz.")
        if type(self.effective_time_us) is not int or self.effective_time_us < 0:
            raise IsolatedLiquidationError("LIQUIDATION_TIER_TIME_INVALID", "Risk tier zamanı geçersiz.")
        object.__setattr__(self, "notional_floor", exact_text(floor))
        if cap is not None:
            object.__setattr__(self, "notional_cap", exact_text(cap))
        object.__setattr__(self, "maintenance_rate", exact_text(rate))
        object.__setattr__(self, "maintenance_amount", exact_text(amount))


@dataclass(frozen=True, slots=True)
class IsolatedMarginSnapshot:
    """Timestamped isolated wallet and mark-price authority snapshot."""

    settlement_asset: str
    isolated_wallet: str
    mark_price: str
    captured_at_us: int

    def __post_init__(self) -> None:
        if not isinstance(self.settlement_asset, str) or _IDENTIFIER.fullmatch(self.settlement_asset) is None:
            raise IsolatedLiquidationError("LIQUIDATION_ASSET_INVALID", "Settlement asset kimliği geçersiz.")
        try:
            wallet = number(self.isolated_wallet)
            mark = positive(self.mark_price)
        except ValueError as error:
            raise IsolatedLiquidationError("LIQUIDATION_MARGIN_NUMERIC_INVALID", "Margin snapshot sayısal alanı geçersiz.") from error
        if wallet < 0 or type(self.captured_at_us) is not int or self.captured_at_us < 0:
            raise IsolatedLiquidationError("LIQUIDATION_SNAPSHOT_INVALID", "Margin snapshot sınırları geçersiz.")
        object.__setattr__(self, "isolated_wallet", exact_text(wallet))
        object.__setattr__(self, "mark_price", exact_text(mark))


@dataclass(frozen=True, slots=True)
class IsolatedLiquidationEstimate:
    """An analytical fixed-tier estimate explicitly marked as non-venue output."""

    side: str
    liquidation_price: str
    notional_at_liquidation: str
    tier_id: str
    settlement_asset: str
    mark_price: str
    status: str = "ESTIMATE_ONLY"


def project_isolated_liquidation(
    side: str,
    quantity: str,
    contract_size: str,
    entry_price: str,
    margin: IsolatedMarginSnapshot,
    tier: IsolatedRiskTier,
) -> IsolatedLiquidationEstimate:
    """Project one fixed-tier isolated root without claiming venue liquidation."""

    if side not in ("LONG", "SHORT"):
        raise IsolatedLiquidationError("LIQUIDATION_SIDE_INVALID", "Side LONG veya SHORT olmalıdır.")
    if not isinstance(margin, IsolatedMarginSnapshot) or not isinstance(tier, IsolatedRiskTier):
        raise IsolatedLiquidationError("LIQUIDATION_INPUT_INVALID", "Margin snapshot ve risk tier güvenli tipte olmalıdır.")
    if margin.captured_at_us < tier.effective_time_us:
        raise IsolatedLiquidationError("LIQUIDATION_SNAPSHOT_TIME_INVALID", "Snapshot risk tier etkinliğinden önce olamaz.")
    try:
        qty = positive(quantity)
        multiplier = positive(contract_size)
        entry = positive(entry_price)
        wallet = number(margin.isolated_wallet)
        rate = number(tier.maintenance_rate)
        maintenance = number(tier.maintenance_amount)
    except ValueError as error:
        raise IsolatedLiquidationError("LIQUIDATION_INPUT_NUMERIC_INVALID", "Liquidation girdisi exact decimal olmalıdır.") from error
    effective_quantity = bounded(qty * multiplier)
    if side == "LONG":
        root = bounded((effective_quantity * entry - wallet - maintenance) / (effective_quantity * (1 - rate)))
    else:
        root = bounded((wallet + effective_quantity * entry + maintenance) / (effective_quantity * (1 + rate)))
    if root <= 0:
        raise IsolatedLiquidationError("LIQUIDATION_NO_POSITIVE_ROOT", "Pozitif liquidation kökü oluşmadı.")
    notional = bounded(effective_quantity * root)
    floor = number(tier.notional_floor)
    cap = None if tier.notional_cap is None else number(tier.notional_cap)
    if not floor <= notional or (cap is not None and notional >= cap):
        raise IsolatedLiquidationError("LIQUIDATION_TIER_MISMATCH", "Kök, seçilen risk tier aralığında değil.")
    try:
        return IsolatedLiquidationEstimate(
            side=side,
            liquidation_price=exact_text(root),
            notional_at_liquidation=exact_text(notional),
            tier_id=tier.tier_id,
            settlement_asset=margin.settlement_asset,
            mark_price=margin.mark_price,
        )
    except ValueError as error:
        raise IsolatedLiquidationError(
            "LIQUIDATION_RESULT_NOT_REPRESENTABLE",
            "Liquidation kökü exact decimal sözleşmesinde temsil edilemiyor.",
        ) from error
