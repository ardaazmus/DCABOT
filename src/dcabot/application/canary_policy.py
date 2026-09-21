"""Canary policy: pure, exact evaluation of whether live trading may proceed.

This module only computes a verdict from a spec and typed observations. It
sends no orders and performs no I/O besides the kill-switch marker file. The
live gate (live_gate.py) consumes the verdict; while no canary approval
exists the gate stays closed regardless of this verdict.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from dcabot.domain.numbers import number


@dataclass(frozen=True, slots=True)
class CanarySpec:
    status: Literal["DRAFT", "ACTIVE"]
    amount_cap_quote: str
    daily_loss_limit_quote: str
    starts_at: str
    ends_at: str
    min_trades: int

    def __post_init__(self) -> None:
        if self.status not in ("DRAFT", "ACTIVE"):
            raise ValueError("Canary status must be DRAFT or ACTIVE")
        cap = number(self.amount_cap_quote)
        limit = number(self.daily_loss_limit_quote)
        if cap <= 0 or limit <= 0:
            raise ValueError("Canary cap and loss limit must be positive")
        start = _parse_time(self.starts_at)
        end = _parse_time(self.ends_at)
        if end <= start:
            raise ValueError("Canary window must end after it starts")
        if not isinstance(self.min_trades, int) or self.min_trades < 1:
            raise ValueError("Canary minimum trades must be a positive integer")


@dataclass(frozen=True, slots=True)
class CanaryObservations:
    trade_count: int
    duplicate_count: int
    unresolved_unknown_count: int
    realized_pnl_quote: str
    now: str
    kill_switch_engaged: bool


@dataclass(frozen=True, slots=True)
class CanaryVerdict:
    verdict: Literal["CANARY_GO", "CANARY_NOGO"]
    reasons: tuple[str, ...]


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("Canary timestamps require an explicit offset")
    return parsed


def evaluate_canary(spec: CanarySpec, obs: CanaryObservations) -> CanaryVerdict:
    reasons: list[str] = []
    if spec.status != "ACTIVE":
        reasons.append("SPEC_NOT_ACTIVE")
    if obs.kill_switch_engaged:
        reasons.append("KILL_SWITCH_ENGAGED")
    try:
        start = _parse_time(spec.starts_at)
        end = _parse_time(spec.ends_at)
        now = _parse_time(obs.now)
        pnl = number(obs.realized_pnl_quote)
        limit = number(spec.daily_loss_limit_quote)
    except (ValueError, TypeError):
        reasons.append("INVALID_OBSERVATION")
        return CanaryVerdict("CANARY_NOGO", tuple(reasons))
    if not (start <= now <= end):
        reasons.append("OUTSIDE_WINDOW")
    for field in (obs.trade_count, obs.duplicate_count, obs.unresolved_unknown_count):
        if not isinstance(field, int) or field < 0:
            reasons.append("INVALID_OBSERVATION")
            return CanaryVerdict("CANARY_NOGO", tuple(reasons))
    if obs.duplicate_count > 0:
        reasons.append("DUPLICATE_DETECTED")
    if obs.unresolved_unknown_count > 0:
        reasons.append("UNRESOLVED_UNKNOWN")
    if -pnl > limit:
        reasons.append("DAILY_LOSS_EXCEEDED")
    if obs.trade_count < spec.min_trades:
        reasons.append("BELOW_MINIMUM_TRADES")
    if not reasons:
        return CanaryVerdict("CANARY_GO", ())
    return CanaryVerdict("CANARY_NOGO", tuple(reasons))


def read_kill_switch(path: Path | str) -> bool:
    """True when the switch is engaged. Missing file is disengaged; any
    unreadable or corrupt file fails closed to engaged."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False
    except (OSError, ValueError):
        return True
    if not isinstance(payload, dict):
        return True
    engaged = payload.get("engaged")
    if engaged is True:
        return True
    if engaged is False:
        return False
    return True


def engage_kill_switch(path: Path | str, reason: str) -> None:
    if not isinstance(reason, str) or not reason or len(reason) > 200:
        raise ValueError("Kill-switch reason must be 1..200 characters")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"engaged": True, "reason": reason}), encoding="utf-8")


def disengage_kill_switch(path: Path | str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"engaged": False}), encoding="utf-8")
