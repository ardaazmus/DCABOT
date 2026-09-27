"""Faz 17 G.1 (RG-06, konu 2/5 entegrasyonu): CROSS margin mode makes a
single deal's isolated-liquidation framing meaningless -- the whole account
shares risk. Research decision (KARARLAR.md, konu 6/12): a new CROSS deal
must also pass D.1's account margin-ratio reliability check and F.2's
correlation-admission gate before it is admitted. ISOLATED deals are
unaffected -- this module is a no-op for them.

This is pure composition: callers already hold an evaluated
`LiquidationStatus` (`anti_liquidation_status.py`) and an evaluated
`CorrelationGateResult` (`correlation_risk.py`); nothing here calls a live
venue or recomputes either. Fail-closed direction matches the established
RG-05 principle: admitting a NEW position is risk-increasing, so any
uncertainty (missing/stale/inconsistent status) denies rather than allows.
LCR-12 is untouched: no liquidation price is computed or estimated here.
"""

from dcabot.application.anti_liquidation_status import LiquidationStatus

_UNRELIABLE_LIQUIDATION_STATES = frozenset({"INCONSISTENT", "STALE"})


class MarginModeCrossAdmissionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def evaluate_cross_admission(
    *,
    margin_mode: str,
    liquidation_status: LiquidationStatus | None,
    correlation_decision: str,
    correlation_reason: str,
) -> None:
    """Raise (fail-closed) if a new deal under CROSS should not be admitted.
    No-op for ISOLATED -- account-wide composition only applies to CROSS."""

    if margin_mode != "CROSS":
        return
    if liquidation_status is None or liquidation_status.state in _UNRELIABLE_LIQUIDATION_STATES:
        state = "MISSING" if liquidation_status is None else liquidation_status.state
        raise MarginModeCrossAdmissionError(
            "MARGIN_MODE_CROSS_ACCOUNT_STATUS_UNRELIABLE",
            f"Cross modda hesap marjin durumu güvenilir değil ({state}) -- yeni deal reddedildi.",
        )
    if correlation_decision != "ALLOW":
        raise MarginModeCrossAdmissionError(
            "MARGIN_MODE_CROSS_CORRELATION_DENY",
            f"Cross modda korelasyon kapısı reddetti: {correlation_reason}.",
        )
