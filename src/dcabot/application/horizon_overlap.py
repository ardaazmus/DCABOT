"""Feature/label horizon overlap check without choosing a purge duration."""

from dataclasses import dataclass
import re


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)


class HorizonOverlapError(ValueError):
    """Raised when interval inputs cannot support a safe boundary decision."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class HorizonStatus:
    """Explicit outcomes for train-label and test-feature interval overlap."""

    NO_OVERLAP = "NO_OVERLAP"
    PURGE_REQUIRED = "PURGE_REQUIRED"


@dataclass(frozen=True, slots=True)
class TimeInterval:
    """Half-open, non-economic interval [start_time_us, end_time_us)."""

    interval_id: str
    start_time_us: int
    end_time_us: int

    def __post_init__(self) -> None:
        if not isinstance(self.interval_id, str) or _IDENTIFIER.fullmatch(self.interval_id) is None:
            raise HorizonOverlapError(
                "HORIZON_INTERVAL_ID_INVALID", "Interval identity geçersiz."
            )
        if type(self.start_time_us) is not int or type(self.end_time_us) is not int:
            raise HorizonOverlapError(
                "HORIZON_INTERVAL_INVALID", "Interval zamanları integer olmalıdır."
            )
        if self.start_time_us < 0 or self.end_time_us <= self.start_time_us:
            raise HorizonOverlapError(
                "HORIZON_INTERVAL_INVALID", "Interval pozitif half-open aralık olmalıdır."
            )


@dataclass(frozen=True, slots=True)
class HorizonAssessment:
    """Read-only overlap result; it does not calculate a purge/embargo size."""

    status: str
    overlapping_interval_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in (HorizonStatus.NO_OVERLAP, HorizonStatus.PURGE_REQUIRED):
            raise HorizonOverlapError("HORIZON_STATUS_INVALID", "Horizon sonucu geçersiz.")
        if not isinstance(self.overlapping_interval_ids, tuple) or tuple(
            sorted(self.overlapping_interval_ids)
        ) != self.overlapping_interval_ids:
            raise HorizonOverlapError(
                "HORIZON_RESULT_INVALID", "Overlap identity sıralı tuple olmalıdır."
            )


def assess_purge_requirement(
    train_label_intervals: tuple[TimeInterval, ...],
    test_feature_intervals: tuple[TimeInterval, ...],
) -> HorizonAssessment:
    """Report overlap while leaving the purge/embargo horizon to local data policy."""

    _validate_intervals(train_label_intervals)
    _validate_intervals(test_feature_intervals)
    all_intervals = (*train_label_intervals, *test_feature_intervals)
    identities = [interval.interval_id for interval in all_intervals]
    if len(set(identities)) != len(identities):
        raise HorizonOverlapError(
            "HORIZON_INTERVAL_DUPLICATE", "Interval identity tekrar edemez."
        )
    overlapping: set[str] = set()
    for label in train_label_intervals:
        for feature in test_feature_intervals:
            if label.start_time_us < feature.end_time_us and feature.start_time_us < label.end_time_us:
                overlapping.update((label.interval_id, feature.interval_id))
    ids = tuple(sorted(overlapping))
    return HorizonAssessment(
        status=HorizonStatus.PURGE_REQUIRED if ids else HorizonStatus.NO_OVERLAP,
        overlapping_interval_ids=ids,
    )


def _validate_intervals(intervals: tuple[TimeInterval, ...]) -> None:
    if not isinstance(intervals, tuple) or not all(
        isinstance(interval, TimeInterval) for interval in intervals
    ):
        raise HorizonOverlapError(
            "HORIZON_INTERVAL_INVALID", "Intervals tuple[TimeInterval] olmalıdır."
        )
    previous: TimeInterval | None = None
    for interval in intervals:
        if previous is not None and (
            interval.start_time_us < previous.start_time_us
            or (
                interval.start_time_us == previous.start_time_us
                and interval.end_time_us < previous.end_time_us
            )
        ):
            raise HorizonOverlapError(
                "HORIZON_INTERVAL_ORDER", "Interval listesi zaman sırasını korumalıdır."
            )
        previous = interval
