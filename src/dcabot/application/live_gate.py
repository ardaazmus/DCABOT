"""Live gate: the single choke point that must approve mainnet trading.

Faz 4 builds the gate and keeps it CLOSED: no canary approval artifact
exists, no mainnet sender exists, and no test may construct an approval.
Every future mainnet mutation path must call assert_live_trading_allowed()
first; while any reason fires, the call raises and nothing may proceed.
"""

from dataclasses import dataclass
from pathlib import Path

from dcabot.application.canary_policy import (
    CanaryObservations,
    CanarySpec,
    evaluate_canary,
    read_kill_switch,
)


class LiveTradingBlocked(ValueError):
    """Raised whenever live trading is not explicitly allowed."""

    def __init__(self, reasons: tuple[str, ...]):
        self.reasons = reasons
        super().__init__(f"Live trading blocked: {', '.join(reasons)}")


@dataclass(frozen=True, slots=True)
class LiveGateDecision:
    allowed: bool
    reasons: tuple[str, ...]


def assert_live_trading_allowed(
    *,
    spec: CanarySpec,
    obs: CanaryObservations,
    approval_path: Path | str,
    kill_switch_path: Path | str,
) -> LiveGateDecision:
    """Allow live trading only with approval + disengaged switch + GO policy.

    The approval artifact is an explicit, out-of-band operator decision
    (Arda's written approval); its absence blocks everything.
    """
    reasons: list[str] = []
    approval = Path(approval_path)
    if not approval.is_file():
        reasons.append("CANARY_APPROVAL_MISSING")
    if read_kill_switch(kill_switch_path):
        reasons.append("KILL_SWITCH_ENGAGED")
    verdict = evaluate_canary(spec, obs)
    if verdict.verdict != "CANARY_GO":
        reasons.extend(verdict.reasons)
    if reasons:
        raise LiveTradingBlocked(tuple(reasons))
    return LiveGateDecision(True, ())
