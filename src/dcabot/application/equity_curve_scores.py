"""Bridge into `analytics/scores.py`'s Sharpe family for one already-computed
exact equity curve (`historical_simulation.py`'s own `state.equity()`
samples, Faz 17 AA.7a-2). The one allowlisted bridge for this concern
(`ANALYTICS_BRIDGE_ALLOWLIST`, tests/test_analytics_boundary.py) -- bar-over-
bar returns are exact Fraction arithmetic; only the final Sharpe statistic
(mean/stdev, both irrational-producing) crosses the float64 boundary.
"""

import math

from dcabot.analytics import AnalyticsError, sharpe_ratio, to_float_series
from dcabot.domain.numbers import number, text


def bar_returns(equity_curve: tuple[str, ...]) -> tuple[str, ...]:
    """Bar-over-bar percentage returns, computed in exact Fraction and
    rounded to a 24-fractional-digit decimal text ONLY because the sole
    caller (`equity_curve_sharpe_ratio`) immediately converts to float64
    anyway -- a return like 1/15 has no finite exact-decimal form, so
    `exact_text`'s round-trip requirement cannot apply here (unlike this
    project's ledger-facing exact fields). A bar where equity was zero has
    an undefined return -- skipped, never fabricated as 0 or inf."""

    values = [number(v) for v in equity_curve]
    returns: list[str] = []
    for prev, curr in zip(values, values[1:]):
        if prev == 0:
            continue
        returns.append(text((curr - prev) / prev, 24))
    return tuple(returns)


def equity_curve_sharpe_ratio(equity_curve: tuple[str, ...]) -> str | None:
    """Per-bar Sharpe ratio (mean / sample-stdev, ddof=1) over the exact bar
    returns. `None` (never 0 or inf) marks an honestly undefined result --
    fewer than 2 usable returns, or zero volatility -- matching this
    project's established "degenerate denominator -> null" convention
    (see `historical_run_contract.performance_metrics`)."""

    if not isinstance(equity_curve, tuple) or len(equity_curve) < 2:
        return None
    returns = bar_returns(equity_curve)
    if len(returns) < 2:
        return None
    try:
        return repr(sharpe_ratio(to_float_series(returns)))
    except AnalyticsError:
        return None


def annualized_sharpe_ratio(equity_curve: tuple[str, ...], *, bars_per_year: int) -> str | None:
    """Per-bar Sharpe scaled by sqrt(bars per year), the convention sector
    backtest reports use; `None` exactly when the per-bar ratio is undefined."""

    if type(bars_per_year) is not int or bars_per_year < 1:
        raise ValueError("bars_per_year must be a positive integer")
    per_bar = equity_curve_sharpe_ratio(equity_curve)
    if per_bar is None:
        return None
    return repr(float(per_bar) * math.sqrt(bars_per_year))
