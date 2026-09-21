"""Combinatorial purged cross-validation paths (Lopez de Prado, AFML ch. 7).

Consumes ``chronological_split`` points, ``horizon_overlap`` purge
decisions, and ``embargo_window`` buffers. Produces C(N,k) train/test
splits plus phi = k*C(N,k)/N full-length stitched paths for scoring.

Purge rule: a train sample is dropped when its label horizon overlaps
any test feature interval of the split. Embargo rule: a train sample
is dropped when its feature interval overlaps the embargo window after
the test block. Both inputs are caller-supplied; nothing is inferred.
"""

from dataclasses import dataclass
from itertools import combinations
from math import comb

from dcabot.application.chronological_split import ChronologicalPoint
from dcabot.application.embargo_window import EmbargoWindowError, drop_embargoed, embargo_after
from dcabot.application.horizon_overlap import (
    HorizonOverlapError,
    TimeInterval,
    assess_purge_requirement,
)
from dcabot.analytics.scores import AnalyticsError, sharpe_ratio, to_float_series


class CombinatorialPurgedCvError(ValueError):
    """Raised when a CPCV split cannot be constructed honestly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class PurgedSplit:
    """One train/test split with purge+embargo already applied to train."""

    test_sample_ids: tuple[str, ...]
    train_sample_ids: tuple[str, ...]
    purged_sample_ids: tuple[str, ...]
    embargoed_sample_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CombinatorialPurgedResult:
    """All splits and stitched paths for one CPCV configuration."""

    combos: tuple[PurgedSplit, ...]
    paths: tuple[tuple[str, ...], ...]

    @property
    def train_sets(self) -> tuple[tuple[str, ...], ...]:
        return tuple(combo.train_sample_ids for combo in self.combos)


def split_into_groups(
    points: tuple[ChronologicalPoint, ...],
    *,
    group_count: int,
) -> tuple[tuple[ChronologicalPoint, ...], ...]:
    """Split ordered samples into contiguous groups (sizes differ by ≤1)."""

    if not isinstance(points, tuple) or not points or not all(
        isinstance(point, ChronologicalPoint) for point in points
    ):
        raise CombinatorialPurgedCvError(
            "CPCV_POINTS_INVALID", "Points tuple[ChronologicalPoint] olmalıdır."
        )
    if type(group_count) is not int or group_count < 2 or group_count > len(points):
        raise CombinatorialPurgedCvError(
            "CPCV_GROUP_COUNT_INVALID", "Grup sayısı 2 ile örnek sayısı arasında olmalıdır."
        )
    base, extra = divmod(len(points), group_count)
    groups: list[tuple[ChronologicalPoint, ...]] = []
    start = 0
    for index in range(group_count):
        width = base + (1 if index < extra else 0)
        groups.append(points[start : start + width])
        start += width
    return tuple(groups)


def test_combinations(*, group_count: int, test_group_count: int) -> tuple[tuple[int, ...], ...]:
    """Return all C(N,k) test-group index combinations in lexicographic order."""

    if type(group_count) is not int or type(test_group_count) is not int:
        raise CombinatorialPurgedCvError("CPCV_COMBINATION_INVALID", "Kombinasyon girdileri integer olmalıdır.")
    if group_count < 2 or not 1 <= test_group_count < group_count:
        raise CombinatorialPurgedCvError(
            "CPCV_COMBINATION_INVALID", "k 1 ile N-1 arasında olmalıdır (N≥2)."
        )
    return tuple(combinations(range(group_count), test_group_count))


def reconstruct_paths(
    *,
    group_count: int,
    test_group_count: int,
    test_members: dict[int, tuple[str, ...]],
) -> tuple[tuple[str, ...], ...]:
    """Stitch per-group test appearances into phi full-length paths.

    Each group appears as test in exactly phi = k*C(N,k)/N combinations;
    path j takes the j-th test appearance of every group, in group order,
    so every path covers all groups exactly once. Members are sample
    identities: per-fold estimate differences need a future fitting
    layer and are not invented here.
    """

    combos = test_combinations(group_count=group_count, test_group_count=test_group_count)
    if set(test_members) != set(range(group_count)):
        raise CombinatorialPurgedCvError("CPCV_MEMBERS_INVALID", "Her grup için test üyeleri verilmelidir.")
    appearances: dict[int, list[int]] = {group: [] for group in range(group_count)}
    for combo_index, combo in enumerate(combos):
        for group in combo:
            appearances[group].append(combo_index)
    phi = test_group_count * comb(group_count, test_group_count) // group_count
    for group in range(group_count):
        if len(appearances[group]) != phi:
            raise CombinatorialPurgedCvError("CPCV_PATH_SLOT_INVALID", "Path slot sayımı tutarsız.")
    paths: list[tuple[str, ...]] = []
    for _slot in range(phi):
        path: list[str] = []
        for group in range(group_count):
            path.extend(test_members[group])
        paths.append(tuple(path))
    return tuple(paths)


def combinatorial_purged_paths(
    points: tuple[ChronologicalPoint, ...],
    *,
    group_count: int,
    test_group_count: int,
    label_horizons: dict[str, TimeInterval],
    feature_intervals: dict[str, TimeInterval],
    embargo_us: int,
) -> CombinatorialPurgedResult:
    """Build purged splits and stitched paths for one CPCV configuration."""

    groups = split_into_groups(points, group_count=group_count)
    combos = test_combinations(group_count=group_count, test_group_count=test_group_count)
    sample_ids = {point.sample_id for point in points}
    for name, mapping in (("label_horizons", label_horizons), ("feature_intervals", feature_intervals)):
        if not isinstance(mapping, dict) or set(mapping) != sample_ids:
            raise CombinatorialPurgedCvError(
                "CPCV_HORIZON_COVERAGE_INVALID", f"{name} tüm sample_id'leri kapsamalıdır."
            )
        if not all(isinstance(item, TimeInterval) for item in mapping.values()):
            raise CombinatorialPurgedCvError(
                "CPCV_HORIZON_TYPE_INVALID", f"{name} değerleri TimeInterval olmalıdır."
            )
    if type(embargo_us) is not int or embargo_us <= 0:
        raise CombinatorialPurgedCvError("CPCV_EMBARGO_INVALID", "embargo_us pozitif integer olmalıdır.")

    group_members = tuple(tuple(point.sample_id for point in group) for group in groups)
    splits: list[PurgedSplit] = []
    for combo in combos:
        test_ids = tuple(sample for group in combo for sample in group_members[group])
        test_set = set(test_ids)
        train_ids = tuple(point.sample_id for point in points if point.sample_id not in test_set)
        purged = _purged_train(train_ids, test_ids, label_horizons, feature_intervals)
        kept = tuple(sample for sample in train_ids if sample not in purged)
        embargoed = _embargoed_train(kept, test_ids, feature_intervals, embargo_us)
        final_train = tuple(sample for sample in kept if sample not in embargoed)
        splits.append(
            PurgedSplit(
                test_sample_ids=test_ids,
                train_sample_ids=final_train,
                purged_sample_ids=tuple(sorted(purged)),
                embargoed_sample_ids=tuple(sorted(embargoed)),
            )
        )
    members = {index: group_members[index] for index in range(group_count)}
    paths = reconstruct_paths(
        group_count=group_count, test_group_count=test_group_count, test_members=members
    )
    return CombinatorialPurgedResult(combos=tuple(splits), paths=paths)


def score_paths(
    paths: tuple[tuple[str, ...], ...],
    returns_by_sample: dict[str, str],
) -> tuple[float, ...]:
    """Score each stitched path with a per-period Sharpe ratio."""

    if not isinstance(paths, tuple) or not paths:
        raise CombinatorialPurgedCvError("CPCV_PATHS_INVALID", "Paths boş olmayan tuple olmalıdır.")
    if not isinstance(returns_by_sample, dict):
        raise CombinatorialPurgedCvError("CPCV_RETURNS_INVALID", "Returns dict[str, str] olmalıdır.")
    scores: list[float] = []
    for path in paths:
        if not isinstance(path, tuple) or not path:
            raise CombinatorialPurgedCvError("CPCV_PATHS_INVALID", "Her path boş olmayan tuple olmalıdır.")
        missing = [sample for sample in path if sample not in returns_by_sample]
        if missing:
            raise CombinatorialPurgedCvError(
                "CPCV_RETURNS_COVERAGE_INVALID", f"Returnu eksik sample: {missing[0]}."
            )
        try:
            series = to_float_series(tuple(returns_by_sample[sample] for sample in path))
            scores.append(sharpe_ratio(series))
        except AnalyticsError as error:
            raise CombinatorialPurgedCvError("CPCV_SCORING_INVALID", "Path skoru hesaplanamadı.") from error
    return tuple(scores)


def _purged_train(
    train_ids: tuple[str, ...],
    test_ids: tuple[str, ...],
    label_horizons: dict[str, TimeInterval],
    feature_intervals: dict[str, TimeInterval],
) -> set[str]:
    labels = tuple(
        TimeInterval(
            interval_id=f"lbl:{sample}",
            start_time_us=label_horizons[sample].start_time_us,
            end_time_us=label_horizons[sample].end_time_us,
        )
        for sample in sorted(train_ids)
    )
    features = tuple(
        TimeInterval(
            interval_id=f"feat:{sample}",
            start_time_us=feature_intervals[sample].start_time_us,
            end_time_us=feature_intervals[sample].end_time_us,
        )
        for sample in sorted(test_ids)
    )
    try:
        assessment = assess_purge_requirement(labels, features)
    except HorizonOverlapError as error:
        raise CombinatorialPurgedCvError("CPCV_PURGE_INVALID", "Purge kararı verilemedi.") from error
    purged: set[str] = set()
    for identity in assessment.overlapping_interval_ids:
        if identity.startswith("lbl:"):
            purged.add(identity[4:])
    return purged


def _embargoed_train(
    train_ids: tuple[str, ...],
    test_ids: tuple[str, ...],
    feature_intervals: dict[str, TimeInterval],
    embargo_us: int,
) -> set[str]:
    test_features = [feature_intervals[sample] for sample in test_ids]
    test_end = max(item.end_time_us for item in test_features)
    anchor = TimeInterval(interval_id="cpcv:test-block", start_time_us=test_end - 1, end_time_us=test_end)
    try:
        window = embargo_after(anchor, embargo_us=embargo_us)
    except EmbargoWindowError as error:
        raise CombinatorialPurgedCvError("CPCV_EMBARGO_INVALID", "Embargo penceresi kurulamadı.") from error
    train_intervals = tuple(
        TimeInterval(
            interval_id=f"tr:{sample}",
            start_time_us=feature_intervals[sample].start_time_us,
            end_time_us=feature_intervals[sample].end_time_us,
        )
        for sample in sorted(train_ids)
    )
    try:
        kept = drop_embargoed(train_intervals, window)
    except EmbargoWindowError as error:
        raise CombinatorialPurgedCvError("CPCV_EMBARGO_INVALID", "Embargo uygulanamadı.") from error
    kept_ids = {item.interval_id[3:] for item in kept}
    return {sample for sample in train_ids if sample not in kept_ids}
