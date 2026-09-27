"""Exchange adapter capability matrix (Faz 17 C.4).

Explicit, read-only record of which venue/mode supports which deal
direction. Unknown venues, modes, or non-Direction values are
fail-closed (CapabilityError) so a typo can never silently enable or
disable a direction. Consumption of this matrix (C.5/P4) is separate work.
"""

from dataclasses import dataclass

from dcabot.domain.math import Direction


class CapabilityError(ValueError):
    """Raised when a venue/mode/direction is not explicitly registered."""


@dataclass(frozen=True, slots=True)
class VenueCapability:
    """One row of the matrix; frozen so runtime code cannot widen it."""

    venue: str
    mode: str
    supports_long: bool
    supports_short: bool
    note: str


CAPABILITY_MATRIX: tuple[VenueCapability, ...] = (
    VenueCapability(
        venue="binance_spot",
        mode="public",
        supports_long=False,
        supports_short=False,
        note="market-data only; no order path exists on this surface",
    ),
    VenueCapability(
        venue="binance_spot",
        mode="testnet",
        supports_long=True,
        supports_short=False,
        note="spot; no margin/futures adapter exists",
    ),
    VenueCapability(
        venue="binance_futures",
        mode="testnet_position_risk_readonly",
        supports_long=False,
        supports_short=False,
        note="Faz 17 D.1: positionRisk/account-margin read-only; no order adapter exists on this surface",
    ),
)

_MATRIX_INDEX = {(row.venue, row.mode): row for row in CAPABILITY_MATRIX}


def capability(venue: str, mode: str) -> VenueCapability:
    """Return the registered row, or raise CapabilityError."""
    if not isinstance(venue, str) or not isinstance(mode, str):
        raise CapabilityError("Venue and mode must be strings.")
    try:
        return _MATRIX_INDEX[(venue, mode)]
    except KeyError:
        raise CapabilityError(f"Unregistered venue/mode: {venue!r}/{mode!r}.") from None


def supports(venue: str, mode: str, direction: Direction) -> bool:
    """True only when the registered row explicitly supports the direction."""
    if not isinstance(direction, Direction):
        raise CapabilityError("Direction must be a Direction enum member.")
    row = capability(venue, mode)
    return row.supports_long if direction is Direction.LONG else row.supports_short
