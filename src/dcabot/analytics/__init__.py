"""Isolated advisory statistics (float64). Never imported by ledger code.

Boundary rule (Faz 14 §4, enforced by tests/test_analytics_boundary.py):
this package converts already-finalized Decimal-string results to float
at its own input boundary and returns advisory scores only. It never
writes back to any ledger, order, or position-sizing code path, and no
module outside ``dcabot.analytics`` and ``tests/`` may import it.
"""

from dcabot.analytics.scores import (
    AnalyticsError,
    deflated_sharpe_ratio,
    expected_max_sharpe,
    kurtosis_excess,
    probabilistic_sharpe_ratio,
    sharpe_ratio,
    skewness,
    to_float_series,
)

__all__ = [
    "AnalyticsError",
    "deflated_sharpe_ratio",
    "expected_max_sharpe",
    "kurtosis_excess",
    "probabilistic_sharpe_ratio",
    "sharpe_ratio",
    "skewness",
    "to_float_series",
]
