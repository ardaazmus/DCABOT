"""Faz 17 B.1: Volatility-Adaptive DCA -- ATR-based dynamic SO deviation (exact).

qwen modul 1 (RG-QWEN-HTML): SO sapmasi/TP, ATR'ye gore dinamik hesaplanir --
``dev_dinamik = dev_baz * (ATR_simdi / ATR_ref)``. Bu modul yalniz motor
matematigini (True Range, ATR, olcekli sapma) saglar; hicbir UI/API
baglamasi, ekonomik politika (cap/clamp) veya `build_plan` cagrisi yapmaz --
ciktisi (`dynamic_deviation`), cagiranin dogrudan mevcut `build_plan`'in
`deviation` parametresine gecebilecegi, bagimsiz bir Fraction-uyumlu
decimal string'tir; mevcut sozlesme/davranis degismez.

ATR, Wilder'in klasik tanimiyla hesaplanir: ilk `window` True Range'in basit
ortalamasiyla tohumlanir, sonrasinda `atr[i] = (atr[i-1]*(window-1) + tr[i])
/ window` recursive agirlikli ortalamasiyla surer. Bu, signal_native_
indicators.py'deki EMA ile ayni "recursive + bounded() fail-closed" desenidir
(Faz 17 arastirma bulgusu RG-09: cig Fraction birikimi sinirsiz basamak
buyumesine yol acabilir -- coz olarak quantize-her-adim degil, mevcut
projedeki gibi bounded()'in kaynak sinirinda ACIKCA hata vermesi tercih
edildi; sessiz kirpma/yuvarlama yok).
"""

from dataclasses import dataclass
from fractions import Fraction

from dcabot.domain.numbers import bounded, number, text


class VolatilityAdaptiveError(ValueError):
    """Raised when ATR/dynamic-deviation inputs cannot be computed honestly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class AtrPoint:
    """One ATR value; warmup positions (before the seed) carry value None."""

    index: int
    value: str | None
    exact: bool


def _parse_series(label: str, values: tuple[str, ...]) -> tuple[Fraction, ...]:
    if not isinstance(values, tuple) or len(values) == 0:
        raise VolatilityAdaptiveError(
            "VOLADAPT_SERIES_INVALID", f"{label} en az 1 elemanli tuple olmalidir."
        )
    try:
        return tuple(number(value) for value in values)
    except ValueError as error:
        raise VolatilityAdaptiveError(
            "VOLADAPT_VALUE_INVALID", f"{label} exact decimal metni olmalidir."
        ) from error


def _display(value: Fraction) -> tuple[str, bool]:
    shown = text(bounded(value), 12)
    assert shown is not None
    return shown, number(shown) == value


def true_range_series(
    highs: tuple[str, ...], lows: tuple[str, ...], closes: tuple[str, ...]
) -> tuple[str, ...]:
    """Return True Range per bar (exact, no rounding -- max/abs/subtract only).

    TR[0] = high[0]-low[0] (no prior close). TR[i] (i>=1) =
    max(high[i]-low[i], |high[i]-close[i-1]|, |low[i]-close[i-1]|).
    """

    highs_q = _parse_series("highs", highs)
    lows_q = _parse_series("lows", lows)
    closes_q = _parse_series("closes", closes)
    if not (len(highs_q) == len(lows_q) == len(closes_q)):
        raise VolatilityAdaptiveError(
            "VOLADAPT_SERIES_MISMATCH", "highs/lows/closes ayni uzunlukta olmalidir."
        )
    out: list[str] = []
    for index, (high, low, close) in enumerate(zip(highs_q, lows_q, closes_q)):
        if high < low:
            raise VolatilityAdaptiveError(
                "VOLADAPT_BAR_INVALID", f"index {index}: high, low'dan kucuk olamaz."
            )
        if index == 0:
            tr = high - low
        else:
            prev_close = closes_q[index - 1]
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        shown, _exact = _display(bounded(tr))
        out.append(shown)
    return tuple(out)


def atr_series(
    highs: tuple[str, ...], lows: tuple[str, ...], closes: tuple[str, ...], *, window: int
) -> tuple[AtrPoint, ...]:
    """Return Wilder ATR with a window-1 warmup prefix (SMA-seeded, then recursive)."""

    if type(window) is not int or window < 1:
        raise VolatilityAdaptiveError(
            "VOLADAPT_WINDOW_INVALID", "Pencere pozitif integer olmalidir."
        )
    tr_text = true_range_series(highs, lows, closes)
    tr = tuple(number(value) for value in tr_text)
    if window > len(tr):
        raise VolatilityAdaptiveError(
            "VOLADAPT_WINDOW_INVALID", "Pencere seri uzunlugunu asamaz."
        )
    exacts: list[Fraction | None] = [None] * len(tr)
    seed = bounded(sum(tr[:window], Fraction(0)) / window)
    exacts[window - 1] = seed
    for index in range(window, len(tr)):
        prior = exacts[index - 1]
        assert prior is not None
        exacts[index] = bounded((prior * (window - 1) + tr[index]) / window)
    points: list[AtrPoint] = []
    for index, value in enumerate(exacts):
        if value is None:
            points.append(AtrPoint(index=index, value=None, exact=True))
        else:
            shown, is_exact = _display(value)
            points.append(AtrPoint(index=index, value=shown, exact=is_exact))
    return tuple(points)


def dynamic_deviation(base_deviation: str, atr_now: str, atr_reference: str) -> str:
    """dev_dynamic = base_deviation * (atr_now / atr_reference), exact Fraction.

    Positive-only. No cap/clamp is applied here (that would be an economic
    policy choice, out of this dilim's scope) -- an extreme ratio is left to
    surface downstream, e.g. `build_plan` already rejects a collapsed or
    inverted ladder level rather than silently clamping it.
    """

    try:
        base = number(base_deviation)
        now = number(atr_now)
        reference = number(atr_reference)
    except ValueError as error:
        raise VolatilityAdaptiveError(
            "VOLADAPT_VALUE_INVALID", "Girdiler exact decimal metni olmalidir."
        ) from error
    if base <= 0 or now <= 0 or reference <= 0:
        raise VolatilityAdaptiveError(
            "VOLADAPT_INPUT_INVALID",
            "base_deviation, atr_now ve atr_reference pozitif olmalidir.",
        )
    scaled = bounded(base * (now / reference))
    shown = text(scaled, 24)
    assert shown is not None
    return shown
