"""Deterministic chronological train/gap/test boundary without economic authority."""

from dataclasses import dataclass
import re


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)


class ChronologicalSplitError(ValueError):
    """Raised when an evaluation split cannot prove its time boundary."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class ChronologicalPoint:
    """One non-economic sample identity used only to establish temporal order."""

    sample_id: str
    event_time_us: int

    def __post_init__(self) -> None:
        if type(self.sample_id) is not str or _IDENTIFIER.fullmatch(self.sample_id) is None:
            raise ChronologicalSplitError(
                "CHRONOLOGICAL_SAMPLE_ID_INVALID", "Sample identity geçersiz."
            )
        if type(self.event_time_us) is not int or self.event_time_us < 0:
            raise ChronologicalSplitError(
                "CHRONOLOGICAL_TIME_INVALID", "event_time_us sıfır veya pozitif integer olmalıdır."
            )


@dataclass(frozen=True, slots=True)
class ChronologicalSplit:
    """Immutable train/gap/test view; gap count is structural, not purge policy."""

    train: tuple[ChronologicalPoint, ...]
    gap: tuple[ChronologicalPoint, ...]
    test: tuple[ChronologicalPoint, ...]

    def __post_init__(self) -> None:
        for name, points in (("train", self.train), ("gap", self.gap), ("test", self.test)):
            if not isinstance(points, tuple) or not all(
                isinstance(point, ChronologicalPoint) for point in points
            ):
                raise ChronologicalSplitError(
                    "CHRONOLOGICAL_SPLIT_INVALID", f"{name} tuple[ChronologicalPoint] olmalıdır."
                )
        if not self.train or not self.test:
            raise ChronologicalSplitError(
                "CHRONOLOGICAL_SPLIT_INVALID", "Train ve test bölümleri boş olamaz."
            )
        _validate_order(self.train + self.gap + self.test)
        if self.train[-1].event_time_us >= self.test[0].event_time_us:
            raise ChronologicalSplitError(
                "CHRONOLOGICAL_BOUNDARY_INVALID",
                "Train son zamanı test ilk zamanından küçük olmalıdır.",
            )


def split_chronological(
    points: tuple[ChronologicalPoint, ...],
    *,
    train_count: int,
    gap_count: int = 0,
) -> ChronologicalSplit:
    """Split already ordered samples without sorting or inventing purge duration.

    ``gap_count`` excludes an explicit number of observations between train and
    test. It is not a claim that those observations satisfy financial purge or
    embargo requirements; the required horizon remains a caller/data decision.
    """

    if not isinstance(points, tuple) or not points or not all(
        isinstance(point, ChronologicalPoint) for point in points
    ):
        raise ChronologicalSplitError(
            "CHRONOLOGICAL_SPLIT_INVALID", "Points tuple[ChronologicalPoint] olmalıdır."
        )
    if type(train_count) is not int or train_count < 1:
        raise ChronologicalSplitError(
            "CHRONOLOGICAL_SPLIT_INVALID", "train_count pozitif integer olmalıdır."
        )
    if type(gap_count) is not int or gap_count < 0:
        raise ChronologicalSplitError(
            "CHRONOLOGICAL_SPLIT_INVALID", "gap_count sıfır veya pozitif integer olmalıdır."
        )
    _validate_order(points)
    test_start = train_count + gap_count
    if train_count >= len(points) or test_start >= len(points):
        raise ChronologicalSplitError(
            "CHRONOLOGICAL_SPLIT_INVALID", "Train, gap ve test sınırları veri içinde olmalıdır."
        )
    return ChronologicalSplit(
        train=points[:train_count],
        gap=points[train_count:test_start],
        test=points[test_start:],
    )


def _validate_order(points: tuple[ChronologicalPoint, ...]) -> None:
    previous_time: int | None = None
    seen_ids: set[str] = set()
    for point in points:
        if point.sample_id in seen_ids:
            raise ChronologicalSplitError(
                "CHRONOLOGY_INVALID", "Sample identity tekrar edemez."
            )
        if previous_time is not None and point.event_time_us <= previous_time:
            raise ChronologicalSplitError(
                "CHRONOLOGY_INVALID", "Points event time strict artan sırada olmalıdır."
            )
        seen_ids.add(point.sample_id)
        previous_time = point.event_time_us
