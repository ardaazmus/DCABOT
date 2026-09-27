"""Faz 17 F.1: ADX/DI (exact Fraction, RG-04) + BB-Width-informed 5-state
regime label -- **öneri-only**. This module never changes a deal/config
parameter; it only classifies. Automatic strategy switching is explicitly
out of scope (a separate, unapproved product decision).

ADX is entirely rational (max/abs/multiply/divide -- no sqrt), so it is
computed in Fraction here with Wilder recursive smoothing. Smoothing twice
(DM/TR, then DX) grows denominators by window^n per pass, which exceeded the
4096-bit bound after ~60 bars; every smoothed, DI and DX value is therefore
held on a fixed 10^-30 grid (round-half-even). ADX is an indicator, not a
ledger value, and 30 digits sits far beyond the 12 that are displayed.
Bollinger Band Width needs a standard deviation (sqrt) and therefore lives
in `analytics/regime_scores.py` (float64, isolated) -- this module is the
one allowlisted bridge that may import it (see `test_analytics_boundary.py`
`ANALYTICS_BRIDGE_ALLOWLIST`).

20/25 ADX thresholds are the common technical-analysis convention, NOT a
DCABOT-validated calibration -- flagged to Arda as an open question
(FAZ16 harita/TASK.md), unrelated to this module's own correctness.
"""

from dataclasses import dataclass
from fractions import Fraction

from dcabot.analytics.regime_scores import bollinger_band_width_series
from dcabot.domain.numbers import bounded, number, text

RegimeDirection = str  # "UP" | "DOWN" | None
RegimeState = str  # UNKNOWN/TREND_CANDIDATE/RANGE_CANDIDATE/COMPRESSION/TRANSITION


class RegimeDetectionError(ValueError):
    """Raised when regime inputs cannot be evaluated honestly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


ADX_FIXED_DIGITS = 30
_FIXED_SCALE = 10**ADX_FIXED_DIGITS


def _fixed(value: Fraction) -> Fraction:
    return Fraction(round(value * _FIXED_SCALE), _FIXED_SCALE)


def _shown(value: Fraction) -> str:
    result = text(bounded(value), 12)
    assert result is not None
    return result


@dataclass(frozen=True, slots=True)
class AdxPoint:
    """One bar's ADX/DI reading; None wherever Wilder warmup hasn't seeded
    or the inputs are degenerate (e.g. zero true range -> DI undefined)."""

    index: int
    adx: str | None
    plus_di: str | None
    minus_di: str | None


def _wilder_smooth(values: tuple[Fraction, ...], window: int) -> tuple[Fraction | None, ...]:
    """SMA-seeded, then `v[i] = (prev*(window-1) + v[i]) / window` -- same
    recursive smoothing as `volatility_adaptive_dca.atr_series`."""

    if window > len(values):
        return tuple(None for _ in values)
    smoothed: list[Fraction | None] = [None] * len(values)
    seed = _fixed(bounded(sum(values[:window], Fraction(0)) / window))
    smoothed[window - 1] = seed
    for i in range(window, len(values)):
        prior = smoothed[i - 1]
        assert prior is not None
        smoothed[i] = _fixed(bounded((prior * (window - 1) + values[i]) / window))
    return tuple(smoothed)


def adx_series(
    bars: tuple[dict[str, str], ...], *, window: int
) -> tuple[AdxPoint, ...]:
    """Each bar: {"high": ..., "low": ..., "close": ...} exact decimal text."""

    if not bars:
        raise RegimeDetectionError("REGIME_BARS_EMPTY", "Bar dizisi boş olamaz.")
    if type(window) is not int or window < 1:
        raise RegimeDetectionError("REGIME_WINDOW_INVALID", "Pencere pozitif integer olmalıdır.")
    highs: list[Fraction] = []
    lows: list[Fraction] = []
    closes: list[Fraction] = []
    for bar in bars:
        try:
            high = number(bar["high"])
            low = number(bar["low"])
            close = number(bar["close"])
        except (KeyError, ValueError) as exc:
            raise RegimeDetectionError(
                "REGIME_BAR_INVALID", "Bar high/low/close exact decimal olmalıdır."
            ) from exc
        if high < low:
            raise RegimeDetectionError("REGIME_BAR_INVALID", "high, low'dan küçük olamaz.")
        highs.append(high)
        lows.append(low)
        closes.append(close)

    n = len(bars)
    tr: list[Fraction] = []
    plus_dm: list[Fraction] = []
    minus_dm: list[Fraction] = []
    for i in range(1, n):
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]
        plus_dm.append(up_move if (up_move > down_move and up_move > 0) else Fraction(0))
        minus_dm.append(down_move if (down_move > up_move and down_move > 0) else Fraction(0))
        tr.append(
            max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        )

    smoothed_tr = _wilder_smooth(tuple(tr), window)
    smoothed_plus_dm = _wilder_smooth(tuple(plus_dm), window)
    smoothed_minus_dm = _wilder_smooth(tuple(minus_dm), window)

    plus_di: list[Fraction | None] = [None] * len(tr)
    minus_di: list[Fraction | None] = [None] * len(tr)
    dx: list[Fraction | None] = [None] * len(tr)
    for i in range(len(tr)):
        stt, spd, smd = smoothed_tr[i], smoothed_plus_dm[i], smoothed_minus_dm[i]
        if stt is None or spd is None or smd is None or stt == 0:
            continue
        p_di = _fixed(bounded(100 * spd / stt))
        m_di = _fixed(bounded(100 * smd / stt))
        plus_di[i] = p_di
        minus_di[i] = m_di
        denom = p_di + m_di
        if denom != 0:
            dx[i] = _fixed(bounded(100 * abs(p_di - m_di) / denom))

    known_dx = tuple(value for value in dx if value is not None)
    # ADX is Wilder-smoothed DX; align by re-walking with the same warmup
    # rule but skipping leading Nones (DX itself is undefined pre-warmup).
    adx_values: list[Fraction | None] = [None] * len(tr)
    first_dx_index = next((i for i, v in enumerate(dx) if v is not None), None)
    if first_dx_index is not None:
        dx_tail = tuple(v for v in dx[first_dx_index:] if v is not None)
        # If any None interrupts the tail (degenerate mid-series bar), ADX
        # cannot be computed past that point without inventing a value.
        contiguous = dx[first_dx_index:]
        if all(v is not None for v in contiguous):
            smoothed_adx = _wilder_smooth(dx_tail, window)
            for offset, value in enumerate(smoothed_adx):
                adx_values[first_dx_index + offset] = value

    points: list[AdxPoint] = []
    points.append(AdxPoint(index=0, adx=None, plus_di=None, minus_di=None))
    for i in range(len(tr)):
        points.append(
            AdxPoint(
                index=i + 1,
                adx=_shown(adx_values[i]) if adx_values[i] is not None else None,
                plus_di=_shown(plus_di[i]) if plus_di[i] is not None else None,
                minus_di=_shown(minus_di[i]) if minus_di[i] is not None else None,
            )
        )
    return tuple(points)


def bb_width_series(
    closes: tuple[str, ...], *, window: int, num_std: str
) -> tuple[str | None, ...]:
    """The one allowlisted bridge into `analytics/regime_scores.py`
    (`ANALYTICS_BRIDGE_ALLOWLIST`). Exact decimal closes are converted to
    float64 ONLY at this boundary; results are float-quality text, never
    written back as if they were exact."""

    try:
        closes_f = [float(number(c)) for c in closes]
        num_std_f = float(number(num_std))
    except ValueError as exc:
        raise RegimeDetectionError(
            "REGIME_VALUE_INVALID", "Girdiler exact decimal olmalıdır."
        ) from exc
    try:
        raw = bollinger_band_width_series(closes_f, window=window, num_std=num_std_f)
    except ValueError as exc:
        raise RegimeDetectionError("REGIME_BBW_INPUT_INVALID", str(exc)) from exc
    return tuple(None if v is None else repr(v) for v in raw)


@dataclass(frozen=True, slots=True)
class RegimeResult:
    """Deterministic, rule-based label -- `confidence` is NOT a probability."""

    state: RegimeState
    direction: RegimeDirection | None
    confidence: str


def classify_regime(
    *,
    adx: str | None,
    plus_di: str | None,
    minus_di: str | None,
    bb_width: str | None,
    trend_threshold: str,
    range_threshold: str,
    squeeze_threshold: str,
    min_di_separation: str = "0",
) -> RegimeResult:
    """5-state label: UNKNOWN / COMPRESSION / TREND_CANDIDATE /
    RANGE_CANDIDATE / TRANSITION. Squeeze (low BB-Width) is checked first --
    a volatility contraction is its own regime regardless of ADX, since ADX
    itself is unreliable input during a squeeze (RG-04's Squeeze!=Range
    warning)."""

    if adx is None or plus_di is None or minus_di is None or bb_width is None:
        return RegimeResult(state="UNKNOWN", direction=None, confidence="0")
    try:
        adx_q = number(adx)
        plus_q = number(plus_di)
        minus_q = number(minus_di)
        bbw_q = number(bb_width)
        trend_t = number(trend_threshold)
        range_t = number(range_threshold)
        squeeze_t = number(squeeze_threshold)
        min_sep = number(min_di_separation)
    except ValueError as exc:
        raise RegimeDetectionError(
            "REGIME_VALUE_INVALID", "Girdiler exact decimal olmalıdır."
        ) from exc
    if adx_q < 0 or bbw_q < 0 or trend_t <= range_t or squeeze_t < 0 or min_sep < 0:
        raise RegimeDetectionError("REGIME_THRESHOLD_INVALID", "Eşik/girdi ilişkisi geçersiz.")

    di_gap = plus_q - minus_q
    direction = "UP" if di_gap > 0 else ("DOWN" if di_gap < 0 else None)
    separated = abs(di_gap) >= min_sep

    if bbw_q < squeeze_t:
        confidence = _shown(bounded((squeeze_t - bbw_q) / squeeze_t)) if squeeze_t > 0 else "0"
        return RegimeResult(state="COMPRESSION", direction=None, confidence=confidence)

    if adx_q >= trend_t and separated:
        span = adx_q - trend_t
        confidence = _shown(bounded(span / (span + trend_t))) if (span + trend_t) > 0 else "0"
        return RegimeResult(state="TREND_CANDIDATE", direction=direction, confidence=confidence)

    if adx_q < range_t:
        span = range_t - adx_q
        confidence = _shown(bounded(span / range_t)) if range_t > 0 else "0"
        return RegimeResult(state="RANGE_CANDIDATE", direction=None, confidence=confidence)

    return RegimeResult(state="TRANSITION", direction=direction, confidence="0")
