"""Faz 17 G.4 (RG-09): MACD and StochRSI via fixed-point scaled-integer
recursion -- additive, does not touch `signal_native_indicators.py`.

Research finding (konu 9/12, quantified): a raw `fractions.Fraction` EMA
recursion's denominator grows ~1.6 decimal digits per bar, reaching ~1400+
digits after 1000 bars -- close to or past this domain's 4096-bit
`bounded()` cap on realistic backtest lengths. `numbers.py`'s existing
Wilder-smoothing modules (ATR/ADX) accepted this growth as a known,
documented risk (RG-09 note); this brief explicitly bans it for MACD/
StochRSI instead: every recursive step here rounds back down to a FIXED
integer scale (round-half-even, via a momentary `Fraction` that is used and
discarded immediately -- never accumulated across steps), so the integer's
digit count never grows regardless of series length. Raw `Fraction` is used
only as an independent test-oracle on short series, never in this path.
"""

from dataclasses import dataclass
from fractions import Fraction

from dcabot.domain.numbers import number

_MIN_SCALE = 1
_MAX_SCALE = 18


class MomentumOscillatorError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _validate_scale(scale: int) -> None:
    if type(scale) is not int or not _MIN_SCALE <= scale <= _MAX_SCALE:
        raise MomentumOscillatorError(
            "MOMENTUM_SCALE_INVALID", f"scale {_MIN_SCALE}..{_MAX_SCALE} aralığında integer olmalıdır."
        )


def _scale_to_int(value: Fraction, scale: int) -> int:
    return round(value * 10**scale)


def _round_half_even_div(numerator: int, denominator: int) -> int:
    """Exact integer round-half-even division via a momentary Fraction --
    created and discarded in the same expression, never retained."""

    if denominator == 0:
        raise MomentumOscillatorError("MOMENTUM_DIVISION_BY_ZERO", "Payda sıfır olamaz.")
    return round(Fraction(numerator, denominator))


def _smoothed_fixed_point(values_int: list[int], window: int, *, k_num: int, k_den: int) -> list[int | None]:
    """SMA-seeded recursive smoothing in fixed-point integers: `next =
    round((value*k_num + prev*(k_den-k_num)) / k_den)`. `k_num/k_den` = 2/(w+1)
    for standard EMA or 1/w for Wilder smoothing."""

    if window < 1:
        raise MomentumOscillatorError("MOMENTUM_WINDOW_INVALID", "Pencere pozitif olmalıdır.")
    if window > len(values_int):
        raise MomentumOscillatorError("MOMENTUM_WINDOW_INVALID", "Pencere seri uzunluğunu aşamaz.")
    out: list[int | None] = [None] * len(values_int)
    seed = _round_half_even_div(sum(values_int[:window]), window)
    out[window - 1] = seed
    prev = seed
    for i in range(window, len(values_int)):
        numerator = values_int[i] * k_num + prev * (k_den - k_num)
        prev = _round_half_even_div(numerator, k_den)
        out[i] = prev
    return out


def _ema_fixed_point(values_int: list[int], window: int) -> list[int | None]:
    return _smoothed_fixed_point(values_int, window, k_num=2, k_den=window + 1)


def _wilder_fixed_point(values_int: list[int], window: int) -> list[int | None]:
    return _smoothed_fixed_point(values_int, window, k_num=1, k_den=window)


@dataclass(frozen=True, slots=True)
class MacdPoint:
    """`macd`/`signal`/`histogram` are integers scaled by `10**scale`;
    `None` during warmup. Never a `Fraction` -- see module docstring."""

    index: int
    macd: int | None
    signal: int | None
    histogram: int | None


def macd_series(
    closes: tuple[str, ...], *, fast: int, slow: int, signal: int, scale: int = 8
) -> tuple[MacdPoint, ...]:
    _validate_scale(scale)
    if type(fast) is not int or type(slow) is not int or fast < 1 or slow < 1 or fast >= slow:
        raise MomentumOscillatorError("MACD_WINDOWS_INVALID", "fast < slow, ikisi de pozitif integer olmalıdır.")
    if type(signal) is not int or signal < 1:
        raise MomentumOscillatorError("MACD_WINDOWS_INVALID", "signal pozitif integer olmalıdır.")
    if not isinstance(closes, tuple) or len(closes) < slow:
        raise MomentumOscillatorError("MACD_SERIES_INVALID", "Closes en az slow pencere kadar uzun olmalıdır.")
    try:
        raw_values = [number(c) for c in closes]
    except ValueError as exc:
        raise MomentumOscillatorError("MACD_VALUE_INVALID", "Close exact decimal metni olmalıdır.") from exc

    values_int = [_scale_to_int(v, scale) for v in raw_values]
    fast_ema = _ema_fixed_point(values_int, fast)
    slow_ema = _ema_fixed_point(values_int, slow)
    macd_line: list[int | None] = [
        None if (f is None or s is None) else f - s for f, s in zip(fast_ema, slow_ema)
    ]
    first_valid = next((i for i, v in enumerate(macd_line) if v is not None), None)
    signal_line: list[int | None] = [None] * len(macd_line)
    if first_valid is not None and len(macd_line) - first_valid >= signal:
        macd_valid = [v for v in macd_line[first_valid:] if v is not None]
        sub_ema = _ema_fixed_point(macd_valid, signal)
        for offset, value in enumerate(sub_ema):
            signal_line[first_valid + offset] = value

    points = []
    for i in range(len(closes)):
        m, sg = macd_line[i], signal_line[i]
        hist = None if (m is None or sg is None) else m - sg
        points.append(MacdPoint(index=i, macd=m, signal=sg, histogram=hist))
    return tuple(points)


@dataclass(frozen=True, slots=True)
class StochRsiPoint:
    """`rsi`/`stoch_rsi` are integers scaled by `10**scale` representing a
    0..100 percentage (i.e. 100 * 10**scale is the maximum value). `None`
    during warmup."""

    index: int
    rsi: int | None
    stoch_rsi: int | None


def stoch_rsi_series(
    closes: tuple[str, ...], *, rsi_window: int, stoch_window: int, scale: int = 8
) -> tuple[StochRsiPoint, ...]:
    """StochRSI = the Stochastic oscillator APPLIED TO the RSI series (not
    "the RSI of the RSI" -- konu 9/12 explicitly flagged this as a common
    library confusion). RSI itself uses Wilder smoothing (k=1/period), the
    same recursive pattern as ATR/ADX, but fixed-point here per this
    module's ban on raw Fraction accumulation."""

    _validate_scale(scale)
    if type(rsi_window) is not int or rsi_window < 1:
        raise MomentumOscillatorError("STOCH_RSI_WINDOW_INVALID", "rsi_window pozitif integer olmalıdır.")
    if type(stoch_window) is not int or stoch_window < 1:
        raise MomentumOscillatorError("STOCH_RSI_WINDOW_INVALID", "stoch_window pozitif integer olmalıdır.")
    if not isinstance(closes, tuple) or len(closes) < rsi_window + 1:
        raise MomentumOscillatorError(
            "STOCH_RSI_SERIES_INVALID", "Closes en az rsi_window+1 kadar uzun olmalıdır."
        )
    try:
        raw_values = [number(c) for c in closes]
    except ValueError as exc:
        raise MomentumOscillatorError("STOCH_RSI_VALUE_INVALID", "Close exact decimal metni olmalıdır.") from exc

    scale_unit = 10**scale
    values_int = [_scale_to_int(v, scale) for v in raw_values]
    gains = [max(values_int[i] - values_int[i - 1], 0) for i in range(1, len(values_int))]
    losses = [max(values_int[i - 1] - values_int[i], 0) for i in range(1, len(values_int))]
    avg_gain = _wilder_fixed_point(gains, rsi_window)
    avg_loss = _wilder_fixed_point(losses, rsi_window)

    rsi: list[int | None] = [None] * len(values_int)
    for i, (g, l) in enumerate(zip(avg_gain, avg_loss)):
        if g is None or l is None:
            continue
        # RSI = 100 * avg_gain / (avg_gain + avg_loss); avg_gain==avg_loss==0
        # (perfectly flat prices) has no direction to report -- the
        # conventional neutral midpoint (50), same convention used below
        # for StochRSI's own degenerate flat-window case, not a warmup None.
        total = g + l
        rsi_index = i + 1  # `avg_gain[i]` covers deltas up to values_int[i+1]
        rsi[rsi_index] = (
            50 * scale_unit if total == 0 else _round_half_even_div(g * 100 * scale_unit, total)
        )

    stoch: list[int | None] = [None] * len(values_int)
    for i in range(len(rsi)):
        if i + 1 < stoch_window:
            continue
        window_values = [v for v in rsi[i - stoch_window + 1 : i + 1] if v is not None]
        if len(window_values) < stoch_window:
            continue
        lo, hi = min(window_values), max(window_values)
        current = rsi[i]
        assert current is not None
        stoch[i] = (
            50 * scale_unit
            if hi == lo
            else _round_half_even_div((current - lo) * 100 * scale_unit, hi - lo)
        )

    return tuple(
        StochRsiPoint(index=i, rsi=rsi[i], stoch_rsi=stoch[i]) for i in range(len(values_int))
    )
