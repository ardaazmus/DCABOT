"""Exact, valuation-only target projection for offline rebalancing."""

from dataclasses import dataclass
import re

from dcabot.domain.numbers import Q, bounded, exact_text, number, positive


_ASSET = re.compile(r"[A-Za-z0-9:_-]{1,32}\Z", re.ASCII)


class RebalanceProjectionError(ValueError):
    """Raised when a rebalancing target cannot be projected safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class RebalanceTarget:
    """One asset's exact target and signed valuation-unit delta."""

    asset: str
    target_weight: str
    target_value: str
    current_value: str
    trade_delta: str


@dataclass(frozen=True, slots=True)
class RebalanceProjection:
    """Canonical target projection before order, reserve, or fill authority."""

    valuation_asset: str
    total_equity: str
    targets: tuple[RebalanceTarget, ...]


def build_rebalance_projection(
    *,
    valuation_asset: str,
    total_equity: str,
    allocations: tuple[tuple[str, str, str], ...],
) -> RebalanceProjection:
    """Project exact target values and deltas in one valuation asset.

    Each allocation is ``(asset, target_weight, current_value)``. Current
    values are already expressed in ``valuation_asset``; no price conversion,
    fee, rounding, balance lookup, order, reserve, or fill is performed.
    Target weights must sum exactly to one and are canonicalized by asset.
    """

    _validate_asset(valuation_asset, "REBALANCE_VALUATION_ASSET_INVALID")
    try:
        equity = positive(total_equity)
    except ValueError as error:
        raise RebalanceProjectionError(
            "REBALANCE_EQUITY_INVALID",
            "Total equity pozitif decimal string olmalıdır.",
        ) from error
    if not isinstance(allocations, tuple) or not allocations:
        raise RebalanceProjectionError(
            "REBALANCE_ALLOCATIONS_INVALID",
            "En az bir allocation tuple gereklidir.",
        )

    parsed: dict[str, tuple[Q, Q]] = {}
    for allocation in allocations:
        if (
            not isinstance(allocation, tuple)
            or len(allocation) != 3
            or not all(isinstance(value, str) for value in allocation)
        ):
            raise RebalanceProjectionError(
                "REBALANCE_ALLOCATION_INVALID",
                "Allocation asset, weight ve current value string tuple olmalıdır.",
            )
        asset, raw_weight, raw_current = allocation
        _validate_asset(asset, "REBALANCE_ASSET_INVALID")
        if asset in parsed:
            raise RebalanceProjectionError(
                "REBALANCE_ASSET_DUPLICATE",
                "Aynı asset allocation içinde iki kez bulunamaz.",
            )
        try:
            weight = number(raw_weight)
        except ValueError as error:
            raise RebalanceProjectionError(
                "REBALANCE_WEIGHT_INVALID",
                "Target weight decimal string olmalıdır.",
            ) from error
        if weight < 0 or weight > 1:
            raise RebalanceProjectionError(
                "REBALANCE_WEIGHT_INVALID",
                "Target weight 0 ile 1 arasında olmalıdır.",
            )
        try:
            current = number(raw_current)
        except ValueError as error:
            raise RebalanceProjectionError(
                "REBALANCE_CURRENT_VALUE_INVALID",
                "Current value decimal string olmalıdır.",
            ) from error
        if current < 0:
            raise RebalanceProjectionError(
                "REBALANCE_CURRENT_VALUE_INVALID",
                "Current value negatif olamaz.",
            )
        parsed[asset] = weight, current

    if sum((weight for weight, _ in parsed.values()), Q(0)) != 1:
        raise RebalanceProjectionError(
            "REBALANCE_WEIGHTS_INVALID",
            "Target weight toplamı exact olarak 1 olmalıdır.",
        )

    targets: list[RebalanceTarget] = []
    try:
        for asset in sorted(parsed):
            weight, current = parsed[asset]
            target = bounded(equity * weight)
            delta = bounded(target - current)
            targets.append(
                RebalanceTarget(
                    asset=asset,
                    target_weight=exact_text(weight),
                    target_value=exact_text(target),
                    current_value=exact_text(current),
                    trade_delta=exact_text(delta),
                )
            )
        return RebalanceProjection(
            valuation_asset=valuation_asset,
            total_equity=exact_text(equity),
            targets=tuple(targets),
        )
    except ValueError as error:
        raise RebalanceProjectionError(
            "REBALANCE_VALUE_UNREPRESENTABLE",
            "Target projection mevcut exact decimal sözleşmesine sığmıyor.",
        ) from error


def _validate_asset(value: str, code: str) -> None:
    if not isinstance(value, str) or _ASSET.fullmatch(value) is None:
        raise RebalanceProjectionError(code, "Asset kimliği geçersiz.")
