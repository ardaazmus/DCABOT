"""Faz 17 G.4 (RG-09): Bollinger Bands -- additive, does not touch
`signal_native_indicators.py`. Middle band (SMA) and variance are rational
(exact `Fraction`, no growth risk: each window is recomputed fresh from raw
closes, never a compounding recursion, so `bounded()` never approaches its
cap regardless of series length). Upper/lower bands and %B need a standard
deviation (sqrt) and therefore cross the Faz-14 analytics boundary --
`bollinger_stdev_series` in `analytics/bollinger_scores.py` is the only
bridge (`ANALYTICS_BRIDGE_ALLOWLIST`), converting to float64 at this module
only; nothing float ever flows back into the exact ledger.
"""

from dataclasses import dataclass
from fractions import Fraction

from dcabot.analytics.bollinger_scores import bollinger_stdev_series
from dcabot.domain.numbers import bounded, number, text


class BollingerBandsError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class BollingerPoint:
    """`middle`/`variance` are Fraction-backed decimal text quantized to 12
    places; `middle_exact`/`variance_exact` disclose whether that text
    round-trips to the true internal value (a repeating decimal like 2/3
    will not) -- the same "exact" disclosure convention as
    `signal_native_indicators.IndicatorPoint`. `upper`/`lower`/`percent_b`
    are float-quality text (sqrt boundary). All fields are `None` during
    warmup (window-1 bars)."""

    index: int
    middle: str | None
    middle_exact: bool
    variance: str | None
    variance_exact: bool
    upper: str | None
    lower: str | None
    percent_b: str | None


def _display(value: Fraction) -> tuple[str, bool]:
    shown = text(bounded(value), 12)
    assert shown is not None
    return shown, number(shown) == value


def _exact_closes(closes: tuple[str, ...]) -> tuple[Fraction, ...]:
    if not isinstance(closes, tuple) or len(closes) < 2:
        raise BollingerBandsError("BOLLINGER_SERIES_INVALID", "Closes en az 2 elemanlı tuple olmalıdır.")
    try:
        return tuple(number(c) for c in closes)
    except ValueError as exc:
        raise BollingerBandsError("BOLLINGER_VALUE_INVALID", "Close exact decimal metni olmalıdır.") from exc


def _sma_and_variance(values: tuple[Fraction, ...], window: int) -> list[tuple[Fraction, Fraction] | None]:
    """Exact population mean/variance per sliding window: Var =
    mean(x^2) - mean(x)^2, both terms exact Fraction, freshly summed per
    window (no recursive accumulation)."""

    out: list[tuple[Fraction, Fraction] | None] = []
    for i in range(len(values)):
        if i < window - 1:
            out.append(None)
            continue
        window_values = values[i - window + 1 : i + 1]
        mean = bounded(sum(window_values, Fraction(0)) / window)
        mean_sq = bounded(sum((v * v for v in window_values), Fraction(0)) / window)
        variance = bounded(mean_sq - mean * mean)
        out.append((mean, variance))
    return out


def bollinger_bands_series(
    closes: tuple[str, ...], *, window: int, num_std: str
) -> tuple[BollingerPoint, ...]:
    if type(window) is not int or window < 2:
        raise BollingerBandsError("BOLLINGER_WINDOW_INVALID", "window en az 2 olmalıdır.")
    values = _exact_closes(closes)
    if window > len(values):
        raise BollingerBandsError("BOLLINGER_WINDOW_INVALID", "Pencere seri uzunluğunu aşamaz.")
    try:
        num_std_q = number(num_std)
    except ValueError as exc:
        raise BollingerBandsError("BOLLINGER_VALUE_INVALID", "num_std exact decimal metni olmalıdır.") from exc
    if num_std_q < 0:
        raise BollingerBandsError("BOLLINGER_NUM_STD_INVALID", "num_std negatif olamaz.")

    exact = _sma_and_variance(values, window)
    closes_f = [float(v) for v in values]
    try:
        stdevs = bollinger_stdev_series(closes_f, window=window)
    except ValueError as exc:
        raise BollingerBandsError("BOLLINGER_STDEV_INPUT_INVALID", str(exc)) from exc
    num_std_f = float(num_std_q)

    points: list[BollingerPoint] = []
    for i, item in enumerate(exact):
        if item is None:
            points.append(
                BollingerPoint(
                    index=i, middle=None, middle_exact=True, variance=None, variance_exact=True,
                    upper=None, lower=None, percent_b=None,
                )
            )
            continue
        mean, variance = item
        stdev = stdevs[i]
        assert stdev is not None
        middle_shown, middle_exact = _display(mean)
        variance_shown, variance_exact = _display(variance)
        middle_f = float(mean)
        upper_f = middle_f + num_std_f * stdev
        lower_f = middle_f - num_std_f * stdev
        percent_b_f = None if upper_f == lower_f else (closes_f[i] - lower_f) / (upper_f - lower_f)
        points.append(
            BollingerPoint(
                index=i,
                middle=middle_shown,
                middle_exact=middle_exact,
                variance=variance_shown,
                variance_exact=variance_exact,
                upper=repr(upper_f),
                lower=repr(lower_f),
                percent_b=None if percent_b_f is None else repr(percent_b_f),
            )
        )
    return tuple(points)
