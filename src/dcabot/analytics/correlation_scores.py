"""Faz 17 F.2: log-return + winsorize + sample covariance/variance --
stdlib-only, float64, isolated per the Faz-14 analytics-boundary discipline
(log/sqrt are irrational; never exact Fraction, never written to the ledger).
"""

import math
import statistics


def log_returns(prices: list[float]) -> list[float]:
    if len(prices) < 2:
        raise ValueError("En az 2 fiyat noktası gerekir")
    if any(p <= 0 for p in prices):
        raise ValueError("Fiyatlar pozitif olmalıdır")
    return [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]


def winsorize(values: list[float], *, lower_pct: float, upper_pct: float) -> list[float]:
    """Clamp each value to the [lower_pct, upper_pct] empirical quantile
    range, preserving order (not sorted output)."""

    if not values:
        raise ValueError("values boş olamaz")
    if not (0 <= lower_pct <= upper_pct <= 1):
        raise ValueError("lower_pct/upper_pct [0,1] aralığında ve sıralı olmalıdır")
    ordered = sorted(values)
    n = len(ordered)

    def _quantile(q: float) -> float:
        if n == 1:
            return ordered[0]
        pos = q * (n - 1)
        lo = int(pos)
        hi = min(lo + 1, n - 1)
        frac = pos - lo
        return ordered[lo] + (ordered[hi] - ordered[lo]) * frac

    low_bound = _quantile(lower_pct)
    high_bound = _quantile(upper_pct)
    return [min(max(v, low_bound), high_bound) for v in values]


def sample_variance(values: list[float]) -> float:
    if len(values) < 2:
        raise ValueError("En az 2 değer gerekir")
    return statistics.variance(values)


def implied_correlation(covariance: float, variance_x: float, variance_y: float) -> float | None:
    """cov / sqrt(varx*vary); the one place this module takes a square
    root. None when the product is non-positive (undefined correlation)."""

    product = variance_x * variance_y
    if product <= 0:
        return None
    return covariance / math.sqrt(product)


def sample_covariance(x: list[float], y: list[float]) -> float:
    if len(x) != len(y):
        raise ValueError("Seriler aynı uzunlukta olmalıdır")
    if len(x) < 2:
        raise ValueError("En az 2 nokta çifti gerekir")
    mean_x = statistics.fmean(x)
    mean_y = statistics.fmean(y)
    total = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    return total / (len(x) - 1)
