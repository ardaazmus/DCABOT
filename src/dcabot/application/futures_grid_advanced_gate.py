"""Fail-closed gate for unverified Futures Grid advanced variants."""

from dataclasses import dataclass
from enum import StrEnum


class FuturesGridAdvancedGateError(ValueError):
    """Raised when an advanced Futures Grid variant is not typed safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class FuturesGridAdvancedVariant(StrEnum):
    """Advanced behaviors that need separate exact contracts and oracles."""

    TRAILING_UP = "TRAILING_UP"
    TRAILING_DOWN = "TRAILING_DOWN"
    EXPANSION = "EXPANSION"
    REVERSAL = "REVERSAL"
    RANGE_REVISION = "RANGE_REVISION"
    CANCEL_REPLACE = "CANCEL_REPLACE"
    REPLAY = "REPLAY"


@dataclass(frozen=True, slots=True)
class FuturesGridAdvancedGate:
    """An explicit block; it never creates a level, order, or state change."""

    variant: FuturesGridAdvancedVariant
    decision: str
    order_authority: str
    reason: str


def assess_futures_grid_advanced_variant(
    variant: FuturesGridAdvancedVariant,
) -> FuturesGridAdvancedGate:
    """Keep unverified advanced behavior outside the economic implementation.

    The research establishes high-level product families but not an exact
    transition, replacement identity, reserve, late-fill, or replay oracle.
    Consequently every advanced variant remains explicitly blocked.
    """

    if not isinstance(variant, FuturesGridAdvancedVariant):
        raise FuturesGridAdvancedGateError(
            "FUTURES_GRID_ADVANCED_VARIANT_INVALID",
            "İleri Futures Grid varyantı güvenli enum değeri olmalıdır.",
        )
    return FuturesGridAdvancedGate(
        variant=variant,
        decision="BLOCKED_CONTRACT_REQUIRED",
        order_authority="NONE",
        reason="FUTURES_GRID_ADVANCED_VARIANT_NOT_VERIFIED",
    )
