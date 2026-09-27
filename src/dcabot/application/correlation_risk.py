"""Faz 17 F.2: correlation-aware admission gate for `account_reservation`
(RG-05 17.3) -- **admission gate only**: it runs before a NEW reservation is
projected and can deny it; it never touches or resizes an existing open
deal's SO/TP ladder or any already-active reservation.

The actual breach DECISION is integer-only and sqrt-free:
``|corr| >= t  <=>  Cov^2 >= t^2 * VarX * VarY``  (both sides squared, so
sign never matters) -- cross-multiplied by the threshold's denominator to
stay in pure integers. Float log-return covariance/variance
(`analytics/correlation_scores.py`) is only ever an ADVISOR that gets
scaled to an integer at this boundary; the comparison itself is exact,
reproducible integer arithmetic, never a direct float `>=`.

Fail-closed directionality (RG-05): insufficient history / stale data /
PSD violation on a RISK-INCREASING action (admitting a new, possibly
correlated position) denies. This module only implements the
risk-increasing (admission) path, so every uncertain case here denies.
"""

from dataclasses import dataclass
from typing import Literal

from dcabot.analytics.correlation_scores import (
    implied_correlation,
    log_returns,
    sample_covariance,
    sample_variance,
)
from dcabot.application.account_reservation import (
    AccountCapacity,
    AccountReservation,
    ReservationProjection,
    project_reservation,
)
from dcabot.application.shared_account_identity import SharedAccountIdentity

GateReason = Literal["INSUFFICIENT_HISTORY", "INSUFFICIENT_PRECISION", "CORRELATION_BREACH", "OK"]
GateDecision = Literal["ALLOW", "DENY"]

# PSD sanity: sample |corr| must never exceed 1 by more than float rounding
# noise. A larger overshoot means the covariance/variance inputs are
# inconsistent (a genuine PSD violation for this pair) -- fail closed.
_PSD_TOLERANCE = 1e-9


class CorrelationRiskError(ValueError):
    """Raised when a correlation-gated admission is denied or misconfigured."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def scale_to_integer(value: float, *, scale: int) -> int:
    """Deterministic fixed-point conversion at the float->integer boundary."""

    if type(scale) is not int or scale <= 0:
        raise CorrelationRiskError("CORRELATION_SCALE_INVALID", "scale pozitif integer olmalıdır.")
    return round(value * scale)


def is_correlation_breach(
    *,
    covariance_scaled: int,
    variance_x_scaled: int,
    variance_y_scaled: int,
    threshold_numerator: int,
    threshold_denominator: int,
) -> bool:
    """``Cov^2 * denom^2 >= num^2 * VarX * VarY`` -- integer-only, no sqrt."""

    if variance_x_scaled < 0 or variance_y_scaled < 0:
        raise CorrelationRiskError(
            "CORRELATION_VARIANCE_NEGATIVE", "Varyans negatif olamaz."
        )
    if threshold_denominator <= 0 or threshold_numerator < 0:
        raise CorrelationRiskError(
            "CORRELATION_THRESHOLD_INVALID", "Eşik pay/payda geçersiz."
        )
    if variance_x_scaled == 0 or variance_y_scaled == 0:
        # Fixed-point rounding collapsed a genuinely tiny (but nonzero)
        # variance to zero -- the ratio is numerically meaningless, not
        # "zero risk". Raise rather than silently returning an accidental
        # True/False; the caller (an admission/risk-increasing gate) must
        # fail closed on this, not guess.
        raise CorrelationRiskError(
            "CORRELATION_SCALE_UNDERFLOW",
            "Ölçeklenmiş varyans sıfıra yuvarlandı; scale parametresi çok küçük.",
        )
    lhs = (covariance_scaled ** 2) * (threshold_denominator ** 2)
    rhs = (threshold_numerator ** 2) * variance_x_scaled * variance_y_scaled
    return lhs >= rhs


@dataclass(frozen=True, slots=True)
class CorrelationGateResult:
    decision: GateDecision
    reason: GateReason
    worst_window: int | None


_WindowVerdict = Literal["BREACH", "NO_BREACH", "INSUFFICIENT_HISTORY", "INSUFFICIENT_PRECISION"]


def _window_breach(
    prices_x: list[float], prices_y: list[float], window: int, *,
    threshold_numerator: int, threshold_denominator: int, scale: int,
) -> _WindowVerdict:
    if len(prices_x) < window + 1 or len(prices_y) < window + 1:
        return "INSUFFICIENT_HISTORY"
    rx = log_returns(prices_x[-(window + 1):])
    ry = log_returns(prices_y[-(window + 1):])
    var_x = sample_variance(rx)
    var_y = sample_variance(ry)
    cov = sample_covariance(rx, ry)
    corr = implied_correlation(cov, var_x, var_y)
    if corr is not None and abs(corr) > 1 + _PSD_TOLERANCE:
        raise CorrelationRiskError(
            "CORRELATION_PSD_VIOLATION",
            "Hesaplanan korelasyon [-1,1] dışına taştı; girdi tutarsız.",
        )
    try:
        breached = is_correlation_breach(
            covariance_scaled=scale_to_integer(cov, scale=scale),
            variance_x_scaled=scale_to_integer(var_x, scale=scale),
            variance_y_scaled=scale_to_integer(var_y, scale=scale),
            threshold_numerator=threshold_numerator,
            threshold_denominator=threshold_denominator,
        )
    except CorrelationRiskError as error:
        if error.code == "CORRELATION_SCALE_UNDERFLOW":
            return "INSUFFICIENT_PRECISION"
        raise
    return "BREACH" if breached else "NO_BREACH"


def evaluate_correlation_gate(
    prices_x: list[float],
    prices_y: list[float],
    *,
    windows: tuple[int, ...],
    threshold_numerator: int,
    threshold_denominator: int,
    scale: int,
) -> CorrelationGateResult:
    """Multi-window, floor-enforced evaluation: the SHORTEST window is the
    floor (must have enough history or the whole gate denies); the verdict
    is the most conservative (any window breaching denies the whole gate).
    """

    if len(prices_x) != len(prices_y):
        raise CorrelationRiskError(
            "CORRELATION_PRICE_LENGTH_MISMATCH", "İki fiyat serisi aynı uzunlukta olmalıdır."
        )
    if not windows or any(type(w) is not int or w < 2 for w in windows):
        raise CorrelationRiskError(
            "CORRELATION_WINDOWS_INVALID", "windows en az bir, her biri >=2 integer olmalıdır."
        )
    floor_window = min(windows)
    if len(prices_x) < floor_window + 1:
        return CorrelationGateResult(decision="DENY", reason="INSUFFICIENT_HISTORY", worst_window=floor_window)

    for window in sorted(windows):
        verdict = _window_breach(
            prices_x, prices_y, window,
            threshold_numerator=threshold_numerator,
            threshold_denominator=threshold_denominator,
            scale=scale,
        )
        if verdict in ("INSUFFICIENT_HISTORY", "INSUFFICIENT_PRECISION"):
            return CorrelationGateResult(decision="DENY", reason=verdict, worst_window=window)
        if verdict == "BREACH":
            return CorrelationGateResult(decision="DENY", reason="CORRELATION_BREACH", worst_window=window)
    return CorrelationGateResult(decision="ALLOW", reason="OK", worst_window=None)


def correlation_admission_gate(
    *,
    capacity: AccountCapacity,
    active_reservations: tuple[AccountReservation, ...],
    reservation_id: str,
    amount: str,
    expected_version: int,
    owner: SharedAccountIdentity,
    prices_x: list[float],
    prices_y: list[float],
    windows: tuple[int, ...],
    threshold_numerator: int,
    threshold_denominator: int,
    scale: int,
) -> ReservationProjection:
    """Deny BEFORE the real capacity/version projection runs if the new
    position is too correlated with the reference series; otherwise defers
    entirely to the unmodified `project_reservation` (no SO/TP resizing,
    no touching existing reservations -- see module docstring).
    """

    del owner  # scope carried for future multi-position aggregation; not used yet
    gate = evaluate_correlation_gate(
        prices_x, prices_y, windows=windows,
        threshold_numerator=threshold_numerator, threshold_denominator=threshold_denominator,
        scale=scale,
    )
    if gate.decision == "DENY":
        raise CorrelationRiskError(
            gate.reason, f"Korelasyon riski nedeniyle yeni deal reddedildi (pencere={gate.worst_window})."
        )
    return project_reservation(capacity, active_reservations, reservation_id, amount, expected_version)
