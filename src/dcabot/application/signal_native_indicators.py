"""DCABOT-native offline indicators: SMA, EMA, and MA crosses (exact).

This module is NOT Pine-parity: it makes no claim of matching
TradingView/Pine semantics (nz(), series-vs-scalar, rolling edge
conventions). It is a small, hand-verifiable, exact-arithmetic
alternative for offline backtest preparation. Averages are exact
Fractions internally; display text is quantized to 12 places with an
``exact`` round-trip flag, so repeating decimals are disclosed.
Crosses are evaluated on the exact internal values, not the display
text, so quantization can never flip an event.
"""

from dataclasses import dataclass
from fractions import Fraction

from dcabot.domain.numbers import bounded, number, text


class SignalIndicatorError(ValueError):
    """Raised when an indicator cannot be computed honestly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class IndicatorPoint:
    """One average value; warmup positions carry value None."""

    index: int
    value: str | None
    exact: bool


@dataclass(frozen=True, slots=True)
class CrossEvent:
    """One fast/slow crossing on exact internal values."""

    index: int
    direction: str


@dataclass(frozen=True, slots=True)
class CrossResult:
    """Both average series plus their crossing events."""

    fast: tuple[IndicatorPoint, ...]
    slow: tuple[IndicatorPoint, ...]
    events: tuple[CrossEvent, ...]


def _parse_closes(closes: tuple[str, ...]) -> tuple[Fraction, ...]:
    if not isinstance(closes, tuple) or len(closes) < 2:
        raise SignalIndicatorError("INDICATOR_SERIES_INVALID", "Closes en az 2 elemanlı tuple olmalıdır.")
    try:
        return tuple(number(value) for value in closes)
    except ValueError as error:
        raise SignalIndicatorError("INDICATOR_VALUE_INVALID", "Close exact decimal metni olmalıdır.") from error


def _validate_window(window: int) -> None:
    if type(window) is not int or window < 1:
        raise SignalIndicatorError("INDICATOR_WINDOW_INVALID", "Pencere pozitif integer olmalıdır.")


def _display(value: Fraction) -> tuple[str, bool]:
    shown = text(bounded(value), 12)
    assert shown is not None
    return shown, number(shown) == value


def sma_series(closes: tuple[str, ...], *, window: int) -> tuple[IndicatorPoint, ...]:
    """Return the simple moving average with a window-1 warmup prefix."""

    values = _parse_closes(closes)
    _validate_window(window)
    if window > len(values):
        raise SignalIndicatorError("INDICATOR_WINDOW_INVALID", "Pencere seri uzunluğunu aşamaz.")
    points: list[IndicatorPoint] = []
    running = Fraction(0)
    for index, value in enumerate(values):
        running += value
        if index >= window:
            running -= values[index - window]
        if index < window - 1:
            points.append(IndicatorPoint(index=index, value=None, exact=True))
        else:
            shown, exact = _display(bounded(running / window))
            points.append(IndicatorPoint(index=index, value=shown, exact=exact))
    return tuple(points)


def ema_series(closes: tuple[str, ...], *, window: int) -> tuple[IndicatorPoint, ...]:
    """Return the exponential moving average (k=2/(w+1), SMA-seeded)."""

    values = _parse_closes(closes)
    _validate_window(window)
    if window > len(values):
        raise SignalIndicatorError("INDICATOR_WINDOW_INVALID", "Pencere seri uzunluğunu aşamaz.")
    if window == 1:
        return tuple(
            IndicatorPoint(index=index, value=_display(value)[0], exact=True)
            for index, value in enumerate(values)
        )
    exacts = _ema_exact(values, window)
    points: list[IndicatorPoint] = []
    for index, exact_value in enumerate(exacts):
        if exact_value is None:
            points.append(IndicatorPoint(index=index, value=None, exact=True))
        else:
            shown, exact = _display(exact_value)
            points.append(IndicatorPoint(index=index, value=shown, exact=exact))
    return tuple(points)


def detect_crosses(
    closes: tuple[str, ...], *, fast_window: int, slow_window: int, kind: str = "sma"
) -> CrossResult:
    """Detect fast/slow MA crosses on exact internal values (SMA or EMA)."""

    if kind not in ("sma", "ema"):
        raise SignalIndicatorError("INDICATOR_KIND_INVALID", "kind yalnız sma ya da ema olabilir.")
    values = _parse_closes(closes)
    _validate_window(fast_window)
    _validate_window(slow_window)
    if max(fast_window, slow_window) > len(values):
        raise SignalIndicatorError("INDICATOR_WINDOW_INVALID", "Pencere seri uzunluğunu aşamaz.")
    series = _sma_exact if kind == "sma" else _ema_exact
    fast_exact = series(values, fast_window)
    slow_exact = series(values, slow_window)
    fast = _points_from_exact(fast_exact)
    slow = _points_from_exact(slow_exact)
    events: list[CrossEvent] = []
    previous: int | None = None
    for index in range(len(values)):
        quick, calm = fast_exact[index], slow_exact[index]
        if quick is None or calm is None:
            continue
        sign = 0 if quick == calm else (1 if quick > calm else -1)
        if sign != 0 and previous is not None and sign != previous and previous != 0:
            events.append(CrossEvent(index=index, direction="GOLDEN" if sign > 0 else "DEATH"))
        if sign != 0:
            previous = sign
    return CrossResult(fast=fast, slow=slow, events=tuple(events))


def _ema_exact(values: tuple[Fraction, ...], window: int) -> tuple[Fraction | None, ...]:
    if window == 1:
        return tuple(values)
    factor = Fraction(2, window + 1)
    seed = bounded(sum(values[:window], Fraction(0)) / window)
    exacts: list[Fraction | None] = [None] * len(values)
    exacts[window - 1] = seed
    for index in range(window, len(values)):
        prior = exacts[index - 1]
        assert prior is not None
        exacts[index] = bounded(values[index] * factor + prior * (1 - factor))
    return tuple(exacts)


def _sma_exact(values: tuple[Fraction, ...], window: int) -> tuple[Fraction | None, ...]:
    out: list[Fraction | None] = []
    running = Fraction(0)
    for index, value in enumerate(values):
        running += value
        if index >= window:
            running -= values[index - window]
        out.append(None if index < window - 1 else bounded(running / window))
    return tuple(out)


def _points_from_exact(exact: tuple[Fraction | None, ...]) -> tuple[IndicatorPoint, ...]:
    points: list[IndicatorPoint] = []
    for index, value in enumerate(exact):
        if value is None:
            points.append(IndicatorPoint(index=index, value=None, exact=True))
        else:
            shown, is_exact = _display(value)
            points.append(IndicatorPoint(index=index, value=shown, exact=is_exact))
    return tuple(points)
