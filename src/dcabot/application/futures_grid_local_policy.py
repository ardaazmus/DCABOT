"""Explicit DCABOT-only lifecycle policy for future offline simulation."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FuturesGridLocalLifecyclePolicy:
    """Record local race and replay choices without granting any authority."""

    scope: str
    late_fill_authority: str
    replacement_admission: str
    reserve_release: str
    duplicate_trade: str
    unknown_or_conflict: str
    replay: str
    order_authority: str
    economic_authority: str
    persistence_authority: str
    venue_authority: str


def declare_futures_grid_local_lifecycle_policy() -> FuturesGridLocalLifecyclePolicy:
    """Declare conservative local rules; do not apply an order or state change.

    These are DCABOT product rules for a future offline simulator, not claims
    about 3Commas, Pionex, Binance, or any other venue implementation.
    """

    return FuturesGridLocalLifecyclePolicy(
        scope="DCABOT_OFFLINE_SIMULATION_ONLY",
        late_fill_authority="FILL_WINS_OVER_CANCEL",
        replacement_admission="CANCEL_ACK_REQUIRED",
        reserve_release="TERMINAL_EXCHANGE_EVENT",
        duplicate_trade="IGNORE_EXACT_DUPLICATE",
        unknown_or_conflict="QUARANTINE_FAIL_CLOSED",
        replay="DETERMINISTIC_REQUIRED",
        order_authority="NONE",
        economic_authority="NONE",
        persistence_authority="NONE",
        venue_authority="NONE",
    )
