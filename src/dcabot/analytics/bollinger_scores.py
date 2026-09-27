"""Faz 17 G.4: Bollinger Bands' upper/lower/%B -- stdlib-only, float64,
isolated per the Faz-14 analytics-boundary discipline (stdev needs sqrt, so
it can never be exact Fraction). The middle band (SMA) and variance are
rational and computed in `application/bollinger_bands.py` instead; only the
sqrt itself, and everything downstream of it, lives here.
"""

import statistics


def bollinger_stdev_series(closes: list[float], *, window: int) -> list[float | None]:
    """Population stdev per sliding window. Warmup prefix (window-1) is
    None. Independent of `regime_scores.bollinger_band_width_series` (same
    sqrt boundary, different output shape) -- kept separate so this
    module's callers never need the width-specific ratio."""

    if not closes:
        raise ValueError("closes boş olamaz")
    if type(window) is not int or window < 2:
        raise ValueError("window en az 2 olmalıdır")
    result: list[float | None] = []
    for i in range(len(closes)):
        if i < window - 1:
            result.append(None)
            continue
        result.append(statistics.pstdev(closes[i - window + 1 : i + 1]))
    return result
