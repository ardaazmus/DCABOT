"""Faz 17 E.3: bind depth REST snapshot fetches to E.1's shared Lab budget.

A denied budget request never touches the network -- the whole point of a
rate budget is that a caller finds out it is over budget without spending
any real request quota to learn that.
"""

from dcabot.application.lab_rate_budget import LabRateBudget
from dcabot.data_adapters.binance_public_depth import (
    DepthSnapshot,
    DepthTransportOpener,
    fetch_binance_public_depth_snapshot,
)

WHALE_FEATURE_NAME = "whale"


class WhaleDepthPollingError(ValueError):
    """Raised when a budgeted depth poll is denied or misconfigured."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def fetch_depth_snapshot_within_budget(
    symbol: str,
    *,
    limit: int,
    budget: LabRateBudget,
    weight: int,
    now_us: int,
    opener: DepthTransportOpener | None = None,
) -> DepthSnapshot:
    """Consult the shared Lab budget before spending any real REST weight;
    on success, feed the venue's own reported used-weight back as the
    budget's observation floor (if the header was present)."""

    if not isinstance(budget, LabRateBudget):
        raise WhaleDepthPollingError(
            "WHALE_DEPTH_BUDGET_INVALID", "Bütçe nesnesi geçersiz."
        )
    if not budget.allow(WHALE_FEATURE_NAME, weight, now_us=now_us):
        raise WhaleDepthPollingError(
            "WHALE_DEPTH_BUDGET_DENIED", "Lab rate bütçesi bu isteğe izin vermiyor."
        )
    snapshot = fetch_binance_public_depth_snapshot(symbol, limit=limit, opener=opener)
    if snapshot.used_weight_1m is not None:
        budget.observe_used_weight_1m(snapshot.used_weight_1m, now_us=now_us)
    return snapshot
