"""Static/dynamic Futures Grid placement boundary without order authority."""

from dataclasses import dataclass

from dcabot.application.futures_grid_levels import FuturesGridLevelProjection


class FuturesGridPlacementError(ValueError):
    """Raised when the placement boundary cannot be assessed safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FuturesGridPlacementAssessment:
    """A static candidate list or an explicit dynamic-placement block."""

    projection: FuturesGridLevelProjection
    placement_mode: str
    range_policy: str
    decision: str
    candidate_levels: tuple[str, ...]
    order_authority: str = "NONE"
    reason: str | None = None


def assess_futures_grid_order_placement(
    projection: FuturesGridLevelProjection,
    *,
    placement_mode: str,
    range_policy: str = "FIXED",
) -> FuturesGridPlacementAssessment:
    """Separate static candidates from unverified dynamic placement behavior.

    Static placement exposes the already projected levels as inert candidates.
    Dynamic placement and range revision remain blocked until their exact
    current-price selection, replacement, reserve, and replay contracts exist.
    No order ID, request, mutation, or persistence is produced.
    """

    if not isinstance(projection, FuturesGridLevelProjection):
        raise FuturesGridPlacementError(
            "FUTURES_GRID_PLACEMENT_PROJECTION_INVALID",
            "Futures Grid level projection güvenli tipte olmalıdır.",
        )
    if placement_mode not in ("STATIC", "DYNAMIC"):
        raise FuturesGridPlacementError(
            "FUTURES_GRID_PLACEMENT_MODE_INVALID",
            "Placement mode STATIC veya DYNAMIC olmalıdır.",
        )
    if range_policy not in ("FIXED", "RANGE_REVISION"):
        raise FuturesGridPlacementError(
            "FUTURES_GRID_RANGE_POLICY_INVALID",
            "Range policy FIXED veya RANGE_REVISION olmalıdır.",
        )
    if placement_mode == "STATIC" and range_policy == "FIXED":
        return FuturesGridPlacementAssessment(
            projection=projection,
            placement_mode=placement_mode,
            range_policy=range_policy,
            decision="STATIC_CANDIDATE_ONLY",
            candidate_levels=projection.levels,
        )
    if placement_mode == "DYNAMIC":
        reason = "FUTURES_GRID_DYNAMIC_PLACEMENT_UNVERIFIED"
    else:
        reason = "FUTURES_GRID_RANGE_REVISION_SEPARATE_CONTRACT_REQUIRED"
    return FuturesGridPlacementAssessment(
        projection=projection,
        placement_mode=placement_mode,
        range_policy=range_policy,
        decision="BLOCKED_CONTRACT_REQUIRED",
        candidate_levels=(),
        reason=reason,
    )
