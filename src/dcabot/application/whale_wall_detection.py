"""Faz 17 E.3: Whale Wall Detection Faz-0 -- statistical anomaly detection
over one order-book side (data ingestion only; no SO/TP nudging here, that
is a later, separate dilim per the roadmap's incrementalism principle).

Every threshold comparison is done on SQUARED quantities (z^2 vs.
(threshold*MAD)^2) so no square root is ever computed -- the whole pipeline
stays exact `Fraction` arithmetic (M-pass discipline), never float.

Pipeline: median/MAD anomaly -> percentile floor -> cumulative-band share
floor -> multi-round persistence -> trade-cross-verification. A signal is
CONFIRMED only after all five gates pass; nothing weaker is emitted.
"""

from dataclasses import dataclass, field
from fractions import Fraction

from dcabot.domain.numbers import bounded, number, text


class WhaleWallDetectionError(ValueError):
    """Raised when wall-detection inputs cannot be evaluated honestly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _shown(value: Fraction) -> str:
    result = text(bounded(value), 12)
    assert result is not None
    return result


def compute_median(values: tuple[str, ...]) -> str:
    if not values:
        raise WhaleWallDetectionError("WHALE_WALL_VALUES_EMPTY", "Değer listesi boş olamaz.")
    try:
        parsed = sorted(number(v) for v in values)
    except ValueError as exc:
        raise WhaleWallDetectionError(
            "WHALE_WALL_VALUE_INVALID", "Değerler exact decimal olmalıdır."
        ) from exc
    n = len(parsed)
    mid = n // 2
    median = parsed[mid] if n % 2 == 1 else (parsed[mid - 1] + parsed[mid]) / 2
    return _shown(median)


def compute_mad(values: tuple[str, ...], median: str) -> str:
    try:
        parsed = [number(v) for v in values]
        median_q = number(median)
    except ValueError as exc:
        raise WhaleWallDetectionError(
            "WHALE_WALL_VALUE_INVALID", "Değerler exact decimal olmalıdır."
        ) from exc
    deviations = tuple(_shown(abs(v - median_q)) for v in parsed)
    return compute_median(deviations)


def is_statistically_anomalous(
    value: str, median: str, mad: str, *, z_threshold: str
) -> bool:
    """(value-median)^2 >= (z_threshold*mad)^2 -- no sqrt. MAD==0 is a
    degenerate, perfectly uniform population: significance cannot be
    established, so this fails closed to False rather than flagging every
    non-identical value."""

    try:
        v = number(value)
        m = number(median)
        d = number(mad)
        z = number(z_threshold)
    except ValueError as exc:
        raise WhaleWallDetectionError(
            "WHALE_WALL_VALUE_INVALID", "Değerler exact decimal olmalıdır."
        ) from exc
    if d < 0 or z < 0:
        raise WhaleWallDetectionError(
            "WHALE_WALL_THRESHOLD_INVALID", "MAD/eşik negatif olamaz."
        )
    if d == 0:
        return False
    diff_sq = (v - m) ** 2
    bound_sq = (z * d) ** 2
    return diff_sq >= bound_sq


def percentile_rank(value: str, population: tuple[str, ...]) -> str:
    """Fraction of `population` <= `value` (`value` must be a member)."""

    try:
        v = number(value)
        parsed = tuple(number(p) for p in population)
    except ValueError as exc:
        raise WhaleWallDetectionError(
            "WHALE_WALL_VALUE_INVALID", "Değerler exact decimal olmalıdır."
        ) from exc
    if not parsed or v not in parsed:
        raise WhaleWallDetectionError(
            "WHALE_WALL_VALUE_NOT_IN_POPULATION", "Değer popülasyonda yok."
        )
    at_or_below = sum(1 for p in parsed if p <= v)
    return _shown(Fraction(at_or_below, len(parsed)))


def cumulative_band_share(
    candidate_price: str,
    candidate_qty: str,
    levels: dict[str, str],
    *,
    band_width_fraction: str,
) -> str:
    """`candidate_qty` / (sum of qty for every level whose price falls
    within `band_width_fraction` of `candidate_price`, inclusive)."""

    try:
        price = number(candidate_price)
        qty = number(candidate_qty)
        width = number(band_width_fraction)
    except ValueError as exc:
        raise WhaleWallDetectionError(
            "WHALE_WALL_VALUE_INVALID", "Değerler exact decimal olmalıdır."
        ) from exc
    if width < 0:
        raise WhaleWallDetectionError(
            "WHALE_WALL_BAND_WIDTH_INVALID", "Bant genişliği negatif olamaz."
        )
    low = price * (1 - width)
    high = price * (1 + width)
    total = Fraction(0)
    for level_price, level_qty in levels.items():
        try:
            p = number(level_price)
            q = number(level_qty)
        except ValueError as exc:
            raise WhaleWallDetectionError(
                "WHALE_WALL_VALUE_INVALID", "Değerler exact decimal olmalıdır."
            ) from exc
        if low <= p <= high:
            total += q
    if total <= 0:
        raise WhaleWallDetectionError(
            "WHALE_WALL_BAND_EMPTY", "Bant içinde pozitif hacim bulunamadı."
        )
    return _shown(qty / total)


@dataclass(frozen=True, slots=True)
class WallCandidate:
    """One level that cleared the statistical/percentile/band gates for one
    evaluation round; not yet persistent, not yet trade-cross-verified."""

    side: str
    price: str
    qty: str


def find_wall_candidates(
    levels: dict[str, str],
    *,
    side: str,
    z_threshold: str,
    min_percentile: str,
    min_band_share: str,
    band_width_fraction: str,
) -> tuple[WallCandidate, ...]:
    if side not in ("bid", "ask"):
        raise WhaleWallDetectionError("WHALE_WALL_SIDE_INVALID", "side yalnız bid/ask olabilir.")
    if not levels:
        return ()
    try:
        min_pct = number(min_percentile)
        min_share = number(min_band_share)
    except ValueError as exc:
        raise WhaleWallDetectionError(
            "WHALE_WALL_VALUE_INVALID", "Eşik değerleri exact decimal olmalıdır."
        ) from exc
    quantities = tuple(levels.values())
    if len(set(quantities)) == 1:
        return ()  # perfectly uniform book, no basis for an outlier claim
    median = compute_median(quantities)
    mad = compute_mad(quantities, median)
    candidates: list[WallCandidate] = []
    for price, qty in levels.items():
        if not is_statistically_anomalous(qty, median, mad, z_threshold=z_threshold):
            continue
        if number(percentile_rank(qty, quantities)) < min_pct:
            continue
        if number(cumulative_band_share(price, qty, levels, band_width_fraction=band_width_fraction)) < min_share:
            continue
        candidates.append(WallCandidate(side=side, price=price, qty=qty))
    return tuple(candidates)


@dataclass(frozen=True, slots=True)
class PersistentWall:
    """A candidate that has held at the same price for `persistence_window`
    consecutive observation rounds; still not trade-cross-verified."""

    side: str
    price: str
    qty: str
    consecutive_observations: int


@dataclass(frozen=True, slots=True)
class ConfirmedWall:
    """The Faz-0 output contract: CONFIRMED only, nothing weaker."""

    side: str
    price: str
    qty: str
    consecutive_observations: int


class WhaleWallTracker:
    """Multi-round persistence + trade-cross-verification, per (side, price)."""

    def __init__(self, *, persistence_window: int) -> None:
        if type(persistence_window) is not int or persistence_window < 1:
            raise WhaleWallDetectionError(
                "WHALE_WALL_WINDOW_INVALID", "persistence_window pozitif integer olmalıdır."
            )
        self._window = persistence_window
        self._streaks: dict[tuple[str, str], int] = {}

    def observe(self, candidates: tuple[WallCandidate, ...], *, now_us: int) -> tuple[PersistentWall, ...]:
        if type(now_us) is not int or now_us < 0:
            raise WhaleWallDetectionError("WHALE_WALL_NOW_INVALID", "now_us negatif olmayan integer olmalıdır.")
        seen = {(c.side, c.price): c for c in candidates}
        for key in list(self._streaks):
            if key not in seen:
                del self._streaks[key]
        newly_persistent: list[PersistentWall] = []
        for key, candidate in seen.items():
            streak = self._streaks.get(key, 0) + 1
            self._streaks[key] = streak
            if streak == self._window:
                newly_persistent.append(
                    PersistentWall(
                        side=candidate.side,
                        price=candidate.price,
                        qty=candidate.qty,
                        consecutive_observations=streak,
                    )
                )
        return tuple(newly_persistent)

    @staticmethod
    def confirm(persistent: PersistentWall, *, traded_qty_since_first_seen: str) -> ConfirmedWall | None:
        """Reject a wall the trade tape shows has already been consumed."""

        try:
            traded = number(traded_qty_since_first_seen)
            qty = number(persistent.qty)
        except ValueError as exc:
            raise WhaleWallDetectionError(
                "WHALE_WALL_VALUE_INVALID", "Trade hacmi exact decimal olmalıdır."
            ) from exc
        if traded < 0:
            raise WhaleWallDetectionError(
                "WHALE_WALL_TRADED_QTY_INVALID", "İşlem hacmi negatif olamaz."
            )
        if traded >= qty:
            return None
        return ConfirmedWall(
            side=persistent.side,
            price=persistent.price,
            qty=persistent.qty,
            consecutive_observations=persistent.consecutive_observations,
        )
