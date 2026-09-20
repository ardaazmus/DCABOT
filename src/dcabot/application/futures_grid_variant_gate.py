"""Fail-closed gate for unverified Reverse and Infinity Grid variants."""

from dataclasses import dataclass
from enum import StrEnum


class FuturesGridVariantGateError(ValueError):
    """Raised when a Futures Grid variant is not typed safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class FuturesGridVariant(StrEnum):
    """Grid families that require separate exact contracts and oracles."""

    REVERSE_GRID = "REVERSE_GRID"
    INFINITY_GRID = "INFINITY_GRID"


@dataclass(frozen=True, slots=True)
class FuturesGridVariantGate:
    """An explicit block; it never creates a level, order, or state change."""

    variant: FuturesGridVariant
    decision: str
    order_authority: str
    economic_authority: str
    reason: str


@dataclass(frozen=True, slots=True)
class FuturesGridVariantAdmission:
    """Product-facing availability; it never grants operational authority."""

    variant: FuturesGridVariant
    availability: str
    admission: str
    order_authority: str
    economic_authority: str
    reason: str


def assess_futures_grid_variant(
    variant: FuturesGridVariant,
) -> FuturesGridVariantGate:
    """Keep unverified variants outside economic and order implementation."""

    if not isinstance(variant, FuturesGridVariant):
        raise FuturesGridVariantGateError(
            "FUTURES_GRID_VARIANT_INVALID",
            "Futures Grid varyantı güvenli enum değeri olmalıdır.",
        )
    return FuturesGridVariantGate(
        variant=variant,
        decision="BLOCKED_CONTRACT_REQUIRED",
        order_authority="NONE",
        economic_authority="NONE",
        reason="FUTURES_GRID_VARIANT_NOT_VERIFIED",
    )


def assess_futures_grid_variant_admission(
    variant: FuturesGridVariant,
) -> FuturesGridVariantAdmission:
    """Keep unverified variants visible as unsupported and blocked."""

    gate = assess_futures_grid_variant(variant)
    return FuturesGridVariantAdmission(
        variant=gate.variant,
        availability="NOT_SUPPORTED",
        admission="BLOCKED",
        order_authority=gate.order_authority,
        economic_authority=gate.economic_authority,
        reason=gate.reason,
    )
