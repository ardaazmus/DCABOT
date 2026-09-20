"""Offline, fee-aware Futures DCA breakeven contract."""

from dataclasses import dataclass
from enum import StrEnum
import re

from dcabot.application.futures_dca_fill_projection import FuturesDcaFillProjection
from dcabot.domain.numbers import Q, align, bounded, exact_text, number, positive


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)
_FEE_MODEL = "PROPORTIONAL_SETTLEMENT_NOTIONAL"
_ROUNDING_MODE = "EXACT_NO_ROUNDING"


class FuturesDcaBreakevenError(ValueError):
    """Raised when a breakeven contract cannot be represented safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class FuturesDcaBreakevenStatus(StrEnum):
    """Read-only fee-aware boundary status."""

    FEE_AWARE_READY = "FEE_AWARE_READY"
    GROSS_ONLY = "GROSS_ONLY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class FuturesDcaFeeAwareProfile:
    """Explicit fee/funding inputs; no venue rate is inferred."""

    settlement_asset: str
    fee_asset: str
    entry_fee_rate: str
    exit_fee_rate: str
    funding_cashflow: str
    profile_revision: str
    fee_model: str = _FEE_MODEL
    rounding_mode: str = _ROUNDING_MODE

    def __post_init__(self) -> None:
        for field, value in (
            ("settlement_asset", self.settlement_asset),
            ("fee_asset", self.fee_asset),
            ("profile_revision", self.profile_revision),
        ):
            if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
                raise FuturesDcaBreakevenError(
                    "FUTURES_DCA_FEE_PROFILE_IDENTIFIER_INVALID",
                    f"{field} açık bir identifier taşımalıdır.",
                )
        if self.fee_asset != self.settlement_asset:
            raise FuturesDcaBreakevenError(
                "FUTURES_DCA_FEE_ASSET_UNSUPPORTED",
                "Üçüncü fee asset’i için ayrı conversion profili gerekir.",
            )
        if self.fee_model != _FEE_MODEL:
            raise FuturesDcaBreakevenError(
                "FUTURES_DCA_FEE_MODEL_UNSUPPORTED",
                "Yalnız explicit settlement-notional fee modeli desteklenir.",
            )
        if self.rounding_mode != _ROUNDING_MODE:
            raise FuturesDcaBreakevenError(
                "FUTURES_DCA_FEE_ROUNDING_UNSUPPORTED",
                "Breakeven contract sessiz rounding yapamaz.",
            )
        try:
            entry_rate = number(self.entry_fee_rate)
            exit_rate = number(self.exit_fee_rate)
            funding = number(self.funding_cashflow)
        except ValueError as error:
            raise FuturesDcaBreakevenError(
                "FUTURES_DCA_FEE_PROFILE_NUMERIC_INVALID",
                "Fee rate ve funding cashflow exact decimal olmalıdır.",
            ) from error
        if not 0 <= entry_rate < 1 or not 0 <= exit_rate < 1:
            raise FuturesDcaBreakevenError(
                "FUTURES_DCA_FEE_RATE_INVALID",
                "Fee oranları 0 dahil, 1 hariç aralıkta olmalıdır.",
            )
        object.__setattr__(self, "entry_fee_rate", exact_text(entry_rate))
        object.__setattr__(self, "exit_fee_rate", exact_text(exit_rate))
        object.__setattr__(self, "funding_cashflow", exact_text(funding))


@dataclass(frozen=True, slots=True)
class FuturesDcaBreakevenEvaluation:
    """Gross and explicitly fee-aware boundary without exit authority."""

    status: FuturesDcaBreakevenStatus
    gross_breakeven_price: str
    fee_aware_breakeven_price: str | None
    reason: str
    profile_revision: str | None
    order_authority: str = "NONE"

    def __post_init__(self) -> None:
        if self.order_authority != "NONE":
            raise FuturesDcaBreakevenError(
                "FUTURES_DCA_BREAKEVEN_ORDER_AUTHORITY_INVALID",
                "Breakeven değerlendirmesi order authority taşıyamaz.",
            )
        if self.status is FuturesDcaBreakevenStatus.FEE_AWARE_READY:
            if self.fee_aware_breakeven_price is None:
                raise FuturesDcaBreakevenError(
                    "FUTURES_DCA_BREAKEVEN_RESULT_INVALID",
                    "Hazır fee-aware sonuç fiyat taşımalıdır.",
                )
        elif self.fee_aware_breakeven_price is not None:
            raise FuturesDcaBreakevenError(
                "FUTURES_DCA_BREAKEVEN_RESULT_INVALID",
                "Hazır olmayan sonuç fee-aware fiyat taşıyamaz.",
            )


def assess_futures_dca_breakeven(
    fill_projection: FuturesDcaFillProjection,
    *,
    fee_profile: FuturesDcaFeeAwareProfile | None = None,
) -> FuturesDcaBreakevenEvaluation:
    """Evaluate an exact boundary from observed fills and explicit economics.

    ``funding_cashflow`` is signed settlement-asset cashflow for the whole
    projected position: positive means received, negative means paid. The
    fee-aware result is intentionally blocked when the profile, asset model,
    or price grid is incomplete; no venue commission or funding is inferred.
    """

    if not isinstance(fill_projection, FuturesDcaFillProjection):
        raise FuturesDcaBreakevenError(
            "FUTURES_DCA_BREAKEVEN_FILL_PROJECTION_INVALID",
            "Fill projection güvenli Futures DCA tipinde olmalıdır.",
        )
    if fill_projection.average_entry is None:
        raise FuturesDcaBreakevenError(
            "FUTURES_DCA_BREAKEVEN_POSITION_EMPTY",
            "Breakeven için gözlenmiş pozisyon gereklidir.",
        )
    try:
        average_entry = positive(fill_projection.average_entry)
        quantity = positive(fill_projection.position_quantity)
        tick = positive(fill_projection.plan.price_tick)
    except ValueError as error:
        raise FuturesDcaBreakevenError(
            "FUTURES_DCA_BREAKEVEN_NUMERIC_INVALID",
            "Average-entry, quantity ve tick exact decimal olmalıdır.",
        ) from error
    gross_text = exact_text(average_entry)
    if fee_profile is None:
        return FuturesDcaBreakevenEvaluation(
            status=FuturesDcaBreakevenStatus.GROSS_ONLY,
            gross_breakeven_price=gross_text,
            fee_aware_breakeven_price=None,
            reason="FEE_AWARE_PROFILE_REQUIRED",
            profile_revision=None,
        )
    if not isinstance(fee_profile, FuturesDcaFeeAwareProfile):
        raise FuturesDcaBreakevenError(
            "FUTURES_DCA_FEE_PROFILE_INVALID",
            "Fee profile güvenli Futures DCA tipinde olmalıdır.",
        )
    if fee_profile.settlement_asset != fill_projection.plan.profile.settlement_asset:
        return FuturesDcaBreakevenEvaluation(
            status=FuturesDcaBreakevenStatus.BLOCKED,
            gross_breakeven_price=gross_text,
            fee_aware_breakeven_price=None,
            reason="FEE_PROFILE_SETTLEMENT_ASSET_MISMATCH",
            profile_revision=fee_profile.profile_revision,
        )
    entry_rate = number(fee_profile.entry_fee_rate)
    exit_rate = number(fee_profile.exit_fee_rate)
    funding = number(fee_profile.funding_cashflow)
    if fill_projection.plan.side == "LONG":
        numerator = bounded(average_entry * (Q(1) + entry_rate) - funding / quantity)
        target = bounded(numerator / (Q(1) - exit_rate))
    else:
        numerator = bounded(average_entry * (Q(1) - entry_rate) + funding / quantity)
        target = bounded(numerator / (Q(1) + exit_rate))
    if target <= 0:
        return _blocked(gross_text, fee_profile.profile_revision, "BREAKEVEN_TARGET_INVALID")
    if align(target, tick, up=False) != target:
        return _blocked(gross_text, fee_profile.profile_revision, "BREAKEVEN_TARGET_OFF_GRID")
    try:
        target_text = exact_text(target)
    except ValueError:
        return _blocked(gross_text, fee_profile.profile_revision, "BREAKEVEN_UNREPRESENTABLE")
    return FuturesDcaBreakevenEvaluation(
        status=FuturesDcaBreakevenStatus.FEE_AWARE_READY,
        gross_breakeven_price=gross_text,
        fee_aware_breakeven_price=target_text,
        reason="EXPLICIT_FEE_AND_FUNDING_PROFILE",
        profile_revision=fee_profile.profile_revision,
    )


def _blocked(
    gross_price: str, profile_revision: str, reason: str
) -> FuturesDcaBreakevenEvaluation:
    return FuturesDcaBreakevenEvaluation(
        status=FuturesDcaBreakevenStatus.BLOCKED,
        gross_breakeven_price=gross_price,
        fee_aware_breakeven_price=None,
        reason=reason,
        profile_revision=profile_revision,
    )
