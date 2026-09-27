"""Canary status assembly: bind the policy verdict to real trigger inputs.

B.3 (=17.8/16.9): ``canary_policy``/``live_gate`` were test-only — no
production path ever evaluated them. This module assembles a status verdict
from REAL inputs on every call: the kill-switch marker file, the approval
artifact presence, an optional spec file, and paper-trade counts.

Honesty rules (no fabrication, no new math — only calls into
:func:`canary_policy.evaluate_canary`):
- No spec file (or corrupt/invalid/DRAFT) short-circuits to
  ``CANARY_NOGO`` + ``SPEC_NOT_ACTIVE``; the evaluator never runs on
  invented thresholds. Arda's canary values are still open.
- ``evaluate_canary`` runs ONLY with a real ACTIVE spec AND an exactly
  known observation. Today that means zero paper fills (zero trades
  implies zero duplicates/unknowns/realized-PnL — definitional, not
  estimated). With fills present, realized-PnL accounting does not exist
  yet (engine follow-up), so the verdict is ``CANARY_NOGO`` +
  ``OBS_UNAVAILABLE`` instead of a guessed number.
"""

import json
from pathlib import Path
from typing import Any, Literal

from dcabot.application.canary_policy import (
    CanaryObservations,
    CanarySpec,
    evaluate_canary,
    read_kill_switch,
)

SpecStatus = Literal["MISSING", "INVALID", "DRAFT", "ACTIVE"]


def paper_fill_count(paper_store: Any) -> int:
    """Total fills across paper sessions. Unknown shapes count as zero."""
    try:
        sessions = paper_store.get("sessions", {})
    except AttributeError:
        return 0
    if not isinstance(sessions, dict):
        return 0
    total = 0
    for session in sessions.values():
        fills = getattr(session, "fills", ())
        if isinstance(fills, (tuple, list)):
            total += len(fills)
    return total


def load_canary_spec(path: Path | str) -> CanarySpec | None:
    """Parse a spec file. Missing/corrupt/invalid files yield None (never raise)."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    try:
        return CanarySpec(
            status=payload.get("status"),
            amount_cap_quote=payload.get("amount_cap_quote"),
            daily_loss_limit_quote=payload.get("daily_loss_limit_quote"),
            starts_at=payload.get("starts_at"),
            ends_at=payload.get("ends_at"),
            min_trades=payload.get("min_trades"),
        )
    except (ValueError, TypeError):
        return None


def _spec_status(spec_path: Path | str, spec: CanarySpec | None) -> SpecStatus:
    if spec is not None:
        return "ACTIVE" if spec.status == "ACTIVE" else "DRAFT"
    try:
        Path(spec_path).read_text(encoding="utf-8")
    except OSError:
        return "MISSING"
    # Present but unusable (load_canary_spec already returned None).
    return "INVALID"


def canary_status(
    *,
    spec_path: Path | str,
    kill_switch_path: Path | str,
    approval_path: Path | str,
    paper_store: Any,
    now_iso: str,
) -> dict:
    """Assemble the live canary verdict from real trigger inputs."""
    kill_engaged = read_kill_switch(kill_switch_path)
    approval_present = Path(approval_path).is_file()
    spec = load_canary_spec(spec_path)
    fills = paper_fill_count(paper_store)

    reasons: list[str] = []
    if not approval_present:
        reasons.append("CANARY_APPROVAL_MISSING")
    if kill_engaged:
        reasons.append("KILL_SWITCH_ENGAGED")

    base: dict = {
        "kill_switch_engaged": kill_engaged,
        "approval_present": approval_present,
        "spec_status": _spec_status(spec_path, spec),
        "paper_fill_count": fills,
        "observed_at": now_iso,
    }
    if spec is None or spec.status != "ACTIVE":
        reasons.append("SPEC_NOT_ACTIVE")
        return {"verdict": "CANARY_NOGO", "reasons": reasons, **base}
    if fills > 0:
        reasons.append("OBS_UNAVAILABLE")
        return {"verdict": "CANARY_NOGO", "reasons": reasons, **base}
    obs = CanaryObservations(
        trade_count=0,
        duplicate_count=0,
        unresolved_unknown_count=0,
        realized_pnl_quote="0",
        now=now_iso,
        kill_switch_engaged=kill_engaged,
    )
    verdict = evaluate_canary(spec, obs)
    return {"verdict": verdict.verdict, "reasons": reasons + list(verdict.reasons), **base}
