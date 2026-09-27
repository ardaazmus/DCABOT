"""Faz 17 F.1: Bollinger Band Width -- stdlib-only, float64, isolated per
the Faz-14 analytics-boundary discipline (stdev needs sqrt, so it can never
be exact Fraction; this module never writes back into the exact ledger).
"""

import statistics


def bollinger_band_width_series(
    closes: list[float], *, window: int, num_std: float
) -> list[float | None]:
    """BB-Width = (upper-lower)/middle, middle=SMA(window), band=+-num_std*
    population-stdev(window). Warmup prefix (window-1 bars) is None."""

    if not closes:
        raise ValueError("closes boş olamaz")
    if type(window) is not int or window < 2:
        raise ValueError("window en az 2 olmalıdır")
    if num_std < 0:
        raise ValueError("num_std negatif olamaz")
    result: list[float | None] = []
    for i in range(len(closes)):
        if i < window - 1:
            result.append(None)
            continue
        slice_ = closes[i - window + 1 : i + 1]
        middle = statistics.fmean(slice_)
        spread = statistics.pstdev(slice_)
        if middle == 0:
            result.append(None)
            continue
        result.append((2 * num_std * spread) / middle)
    return result
