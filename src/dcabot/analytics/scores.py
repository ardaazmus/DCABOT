"""Pure-stdlib float64 advisory scores (Sharpe family, PBO support).

Formulas follow Bailey & Lopez de Prado (PSR/DSR) and Bailey et al. (PBO).
Moment estimators are population (biased) moments — deterministic and
documented — rather than pandas-style unbiased sample moments.

No numpy/scipy: the offline-first, frozen-lockfile build cannot take new
binary dependencies, and these are one-shot summary statistics over
hundreds-to-thousands of observations, not hot loops.
"""

import math


_EULER_MASCHERONI = 0.5772156649015329


class AnalyticsError(ValueError):
    """Raised when an advisory score cannot be computed honestly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def to_float_series(values: tuple[str, ...]) -> tuple[float, ...]:
    """Convert finalized Decimal strings to float at the analytics boundary."""

    if not isinstance(values, tuple) or not values:
        raise AnalyticsError("ANALYTICS_SERIES_EMPTY", "Seri boş olmayan tuple[str] olmalıdır.")
    out: list[float] = []
    for value in values:
        if not isinstance(value, str):
            raise AnalyticsError("ANALYTICS_VALUE_INVALID", "Seri yalnız string içerebilir.")
        try:
            number = float(value)
        except ValueError as error:
            raise AnalyticsError("ANALYTICS_VALUE_INVALID", "Seri değeri parse edilemedi.") from error
        if not math.isfinite(number):
            raise AnalyticsError("ANALYTICS_VALUE_NON_FINITE", "Seri değeri sonlu olmalıdır.")
        out.append(number)
    return tuple(out)


def _mean(values: tuple[float, ...]) -> float:
    return math.fsum(values) / len(values)


def _central_moment(values: tuple[float, ...], order: int, mean: float) -> float:
    return math.fsum((v - mean) ** order for v in values) / len(values)


def sharpe_ratio(returns: tuple[float, ...]) -> float:
    """Return the per-period Sharpe ratio (mean / sample std, ddof=1)."""

    if not isinstance(returns, tuple) or len(returns) < 2:
        raise AnalyticsError("ANALYTICS_SAMPLE_TOO_SMALL", "Sharpe en az 2 gözlem ister.")
    mean = _mean(returns)
    variance = math.fsum((v - mean) ** 2 for v in returns) / (len(returns) - 1)
    if variance <= 0.0:
        raise AnalyticsError("ANALYTICS_ZERO_VOLATILITY", "Sıfır volatilitede Sharpe tanımsızdır.")
    return mean / math.sqrt(variance)


def skewness(values: tuple[float, ...]) -> float:
    """Return population-moment skewness (m3 / m2^1.5)."""

    if not isinstance(values, tuple) or len(values) < 2:
        raise AnalyticsError("ANALYTICS_SAMPLE_TOO_SMALL", "Skew en az 2 gözlem ister.")
    mean = _mean(values)
    m2 = _central_moment(values, 2, mean)
    if m2 <= 0.0:
        raise AnalyticsError("ANALYTICS_ZERO_VARIANCE", "Sabit seride skew tanımsızdır.")
    m3 = _central_moment(values, 3, mean)
    return m3 / (m2 ** 1.5)


def kurtosis_excess(values: tuple[float, ...]) -> float:
    """Return population-moment excess kurtosis (m4 / m2^2 - 3)."""

    if not isinstance(values, tuple) or len(values) < 2:
        raise AnalyticsError("ANALYTICS_SAMPLE_TOO_SMALL", "Kurtosis en az 2 gözlem ister.")
    mean = _mean(values)
    m2 = _central_moment(values, 2, mean)
    if m2 <= 0.0:
        raise AnalyticsError("ANALYTICS_ZERO_VARIANCE", "Sabit seride kurtosis tanımsızdır.")
    m4 = _central_moment(values, 4, mean)
    return m4 / (m2 ** 2) - 3.0


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _inverse_normal_cdf(probability: float) -> float:
    """Acklam's approximation of the probit function (|error| < 1.2e-9)."""

    if not 0.0 < probability < 1.0:
        raise AnalyticsError("ANALYTICS_PROBABILITY_INVALID", "Olasılık (0,1) aralığında olmalıdır.")
    a1, a2, a3, a4, a5, a6 = (
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    )
    b1, b2, b3, b4, b5 = (
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    )
    c1, c2, c3, c4, c5, c6 = (
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    )
    d1, d2, d3, d4 = (
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    )
    low, high = 0.02425, 1.0 - 0.02425
    if probability < low:
        q = math.sqrt(-2.0 * math.log(probability))
        return (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) / (
            (((d1 * q + d2) * q + d3) * q + d4) * q + 1.0
        )
    if probability <= high:
        q = probability - 0.5
        r = q * q
        return (((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6) * q / (
            ((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1.0
        )
    q = math.sqrt(-2.0 * math.log(1.0 - probability))
    return -(((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) / (
        (((d1 * q + d2) * q + d3) * q + d4) * q + 1.0
    )


def probabilistic_sharpe_ratio(
    *,
    sharpe: float,
    n_obs: int,
    skew: float,
    kurt: float,
    benchmark: float = 0.0,
) -> float:
    """Return Bailey & Lopez de Prado's Probabilistic Sharpe Ratio.

    ``kurt`` is raw (Pearson, normal = 3.0) kurtosis, matching the paper's
    ``(gamma4 - 1) / 4`` term.
    """

    for name, value in (("sharpe", sharpe), ("skew", skew), ("kurt", kurt), ("benchmark", benchmark)):
        if not isinstance(value, float) or not math.isfinite(value):
            raise AnalyticsError("ANALYTICS_INPUT_INVALID", f"PSR girdisi sonlu float olmalıdır: {name}.")
    if type(n_obs) is not int or n_obs < 2:
        raise AnalyticsError("ANALYTICS_SAMPLE_TOO_SMALL", "PSR en az 2 gözlem ister.")
    inner = 1.0 - skew * sharpe + ((kurt - 1.0) / 4.0) * sharpe * sharpe
    if inner <= 0.0:
        raise AnalyticsError("ANALYTICS_PSR_DEGENERATE", "PSR paydası tanımsız.")
    statistic = (sharpe - benchmark) * math.sqrt(n_obs - 1) / math.sqrt(inner)
    return _normal_cdf(statistic)


def expected_max_sharpe(n_trials: int) -> float:
    """Return E[max SR_N]: the expected best Sharpe under the null.

    Closed-form approximation with the Euler-Mascheroni constant. A
    single trial has no selection effect, so N=1 returns exactly 0.0.
    """

    if type(n_trials) is not int or n_trials < 1:
        raise AnalyticsError("ANALYTICS_TRIALS_INVALID", "Deneme sayısı pozitif integer olmalıdır.")
    if n_trials == 1:
        return 0.0
    gamma = _EULER_MASCHERONI
    return (1.0 - gamma) * _inverse_normal_cdf(1.0 - 1.0 / n_trials) + gamma * _inverse_normal_cdf(
        1.0 - 1.0 / (n_trials * math.e)
    )


def deflated_sharpe_ratio(
    *,
    sharpe: float,
    n_obs: int,
    skew: float,
    kurt: float,
    n_trials: int,
) -> float:
    """Return the Deflated Sharpe Ratio (PSR vs the selection benchmark)."""

    return probabilistic_sharpe_ratio(
        sharpe=sharpe,
        n_obs=n_obs,
        skew=skew,
        kurt=kurt,
        benchmark=expected_max_sharpe(n_trials),
    )
