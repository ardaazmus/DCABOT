"""Fail-closed gate for Futures Grid replacement, replay, and late fills."""

from dataclasses import dataclass
from enum import StrEnum


class FuturesGridLifecycleGateError(ValueError):
    """Raised when a Futures Grid lifecycle boundary is not typed safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class FuturesGridLifecycleBoundary(StrEnum):
    """Lifecycle boundaries that need an exact transition and replay oracle."""

    RANGE_REVISION = "RANGE_REVISION"
    CANCEL_REPLACE = "CANCEL_REPLACE"
    LATE_FILL = "LATE_FILL"
    REPLAY = "REPLAY"


@dataclass(frozen=True, slots=True)
class FuturesGridLifecycleGate:
    """A read-only contract checklist; it cannot create orders or state."""

    boundary: FuturesGridLifecycleBoundary
    decision: str
    order_authority: str
    required_contracts: tuple[str, ...]
    reason: str


_REQUIRED_BY_BOUNDARY = {
    FuturesGridLifecycleBoundary.RANGE_REVISION: (
        "EXACT_RANGE_TRANSITION",
        "REPLACEMENT_IDENTITY",
        "PENDING_RESERVE_LIFECYCLE",
        "LATE_FILL_AUTHORITY",
        "DETERMINISTIC_REPLAY_ORACLE",
    ),
    FuturesGridLifecycleBoundary.CANCEL_REPLACE: (
        "REPLACEMENT_IDENTITY",
        "PENDING_RESERVE_LIFECYCLE",
        "LATE_FILL_AUTHORITY",
        "DETERMINISTIC_REPLAY_ORACLE",
    ),
    FuturesGridLifecycleBoundary.LATE_FILL: (
        "LATE_FILL_AUTHORITY",
        "REPLACEMENT_IDENTITY",
        "PENDING_RESERVE_LIFECYCLE",
        "DETERMINISTIC_REPLAY_ORACLE",
    ),
    FuturesGridLifecycleBoundary.REPLAY: (
        "DETERMINISTIC_REPLAY_ORACLE",
        "REPLACEMENT_IDENTITY",
        "LATE_FILL_AUTHORITY",
        "EXACT_RANGE_TRANSITION",
        "PENDING_RESERVE_LIFECYCLE",
    ),
}


def assess_futures_grid_lifecycle_boundary(
    boundary: FuturesGridLifecycleBoundary,
) -> FuturesGridLifecycleGate:
    """Expose missing lifecycle evidence without enabling an economic path."""

    if not isinstance(boundary, FuturesGridLifecycleBoundary):
        raise FuturesGridLifecycleGateError(
            "FUTURES_GRID_LIFECYCLE_BOUNDARY_INVALID",
            "Futures Grid yaşam döngüsü sınırı güvenli enum değeri olmalıdır.",
        )
    return FuturesGridLifecycleGate(
        boundary=boundary,
        decision="BLOCKED_CONTRACT_REQUIRED",
        order_authority="NONE",
        required_contracts=_REQUIRED_BY_BOUNDARY[boundary],
        reason="FUTURES_GRID_LIFECYCLE_CONTRACT_NOT_VERIFIED",
    )
