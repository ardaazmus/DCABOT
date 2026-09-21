"""Embargo primitive: a buffer zone right after each test block.

Embargo absorbs residual autocorrelation leaking from the test set into
later training observations. The width is always explicit microseconds
chosen by the caller — this module never invents a percentage policy.
"""

from dcabot.application.horizon_overlap import (
    HorizonOverlapError,
    TimeInterval,
    assess_purge_requirement,
)


class EmbargoWindowError(ValueError):
    """Raised when an embargo window cannot be constructed or applied."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def embargo_after(test: TimeInterval, *, embargo_us: int) -> TimeInterval:
    """Return ``[test.end, test.end + embargo_us)`` as a half-open window."""

    if not isinstance(test, TimeInterval):
        raise EmbargoWindowError("EMBARGO_INTERVAL_INVALID", "Test aralığı güvenli tipte olmalıdır.")
    if type(embargo_us) is not int or embargo_us <= 0:
        raise EmbargoWindowError("EMBARGO_WIDTH_INVALID", "Embargo genişliği pozitif integer olmalıdır.")
    try:
        return TimeInterval(
            interval_id=f"{test.interval_id}:embargo",
            start_time_us=test.end_time_us,
            end_time_us=test.end_time_us + embargo_us,
        )
    except HorizonOverlapError as error:
        raise EmbargoWindowError("EMBARGO_INTERVAL_INVALID", "Embargo aralığı kurulamadı.") from error


def drop_embargoed(
    train: tuple[TimeInterval, ...],
    embargo: TimeInterval,
) -> tuple[TimeInterval, ...]:
    """Drop train intervals overlapping the embargo window (half-open)."""

    if not isinstance(embargo, TimeInterval):
        raise EmbargoWindowError("EMBARGO_INTERVAL_INVALID", "Embargo aralığı güvenli tipte olmalıdır.")
    if type(train) is not tuple or not all(isinstance(item, TimeInterval) for item in train):
        raise EmbargoWindowError("EMBARGO_TRAIN_INVALID", "Train tuple[TimeInterval] olmalıdır.")
    if not train:
        return ()
    try:
        assessment = assess_purge_requirement(train, (embargo,))
    except HorizonOverlapError as error:
        raise EmbargoWindowError("EMBARGO_TRAIN_INVALID", "Train sırası değerlendirilemedi.") from error
    dropped = set(assessment.overlapping_interval_ids)
    dropped.discard(embargo.interval_id)
    return tuple(item for item in train if item.interval_id not in dropped)
