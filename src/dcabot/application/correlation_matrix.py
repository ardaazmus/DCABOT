"""Q2: pairwise correlation matrix over aligned close series.

Display-grade coefficients (float, 4 decimals) plus exact integer breach
verdicts. No new math: every number flows through the tested Faz 17 F.2
core (`correlation_scores` advisors + `is_correlation_breach` integer
comparison); this module only composes per-cell and maps every uncertain
case to INSUFFICIENT (fail closed, never a guessed verdict).

The caller aligns series (same length, same timestamps); a length
mismatch is INSUFFICIENT, not an exception, because venue listings lag.
"""

from dataclasses import dataclass
from typing import Literal

from dcabot.analytics.correlation_scores import (
    implied_correlation,
    log_returns,
    sample_covariance,
    sample_variance,
)
from dcabot.application.correlation_risk import (
    CorrelationRiskError,
    is_correlation_breach,
    scale_to_integer,
)

CellVerdict = Literal["BREACH", "OK", "INSUFFICIENT"]
CellDetail = Literal["INSUFFICIENT_HISTORY", "INSUFFICIENT_PRECISION", "PSD_VIOLATION"]

_PSD_TOLERANCE = 1e-9


@dataclass(frozen=True, slots=True)
class MatrixCell:
    x: str
    y: str
    coefficient: str | None
    verdict: CellVerdict
    detail: CellDetail | None
    samples: int


def _cell(
    x: str,
    y: str,
    prices_x: list[float],
    prices_y: list[float],
    *,
    window: int,
    threshold_numerator: int,
    threshold_denominator: int,
    scale: int,
) -> MatrixCell:
    if len(prices_x) != len(prices_y) or len(prices_x) < window + 1:
        return MatrixCell(x, y, None, "INSUFFICIENT", "INSUFFICIENT_HISTORY", min(len(prices_x), len(prices_y)))
    rx = log_returns(prices_x[-(window + 1):])
    ry = log_returns(prices_y[-(window + 1):])
    var_x = sample_variance(rx)
    var_y = sample_variance(ry)
    cov = sample_covariance(rx, ry)
    corr = implied_correlation(cov, var_x, var_y)
    if corr is not None and abs(corr) > 1 + _PSD_TOLERANCE:
        return MatrixCell(x, y, None, "INSUFFICIENT", "PSD_VIOLATION", len(prices_x))
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
            return MatrixCell(x, y, None, "INSUFFICIENT", "INSUFFICIENT_PRECISION", len(prices_x))
        raise
    return MatrixCell(
        x, y,
        coefficient=None if corr is None else f"{corr:.4f}",
        verdict="BREACH" if breached else "OK",
        detail=None,
        samples=len(prices_x),
    )


def correlation_matrix_cells(
    series: dict[str, list[float]],
    *,
    window: int,
    threshold_numerator: int,
    threshold_denominator: int,
    scale: int,
) -> list[MatrixCell]:
    """Upper-triangle cells (x < y, symbols sorted) for the matrix UI."""

    if type(window) is not int or window < 2:
        raise CorrelationRiskError("CORRELATION_WINDOWS_INVALID", "window >=2 integer olmalıdır.")
    if type(scale) is not int or scale <= 0:
        raise CorrelationRiskError("CORRELATION_SCALE_INVALID", "scale pozitif integer olmalıdır.")
    if type(threshold_denominator) is not int or threshold_denominator <= 0 or type(threshold_numerator) is not int or threshold_numerator < 0:
        raise CorrelationRiskError("CORRELATION_THRESHOLD_INVALID", "Eşik pay/payda geçersiz.")
    names = sorted(series)
    return [
        _cell(
            names[i], names[j], series[names[i]], series[names[j]],
            window=window,
            threshold_numerator=threshold_numerator,
            threshold_denominator=threshold_denominator,
            scale=scale,
        )
        for i in range(len(names))
        for j in range(i + 1, len(names))
    ]
