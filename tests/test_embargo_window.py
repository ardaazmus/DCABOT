"""Faz 14.2: embargo primitifi (test bloğu sonrası tampon bölge)."""
import unittest

from dcabot.application.embargo_window import (
    EmbargoWindowError,
    drop_embargoed,
    embargo_after,
)
from dcabot.application.horizon_overlap import TimeInterval


def _interval(identity: str, start: int, end: int) -> TimeInterval:
    return TimeInterval(interval_id=identity, start_time_us=start, end_time_us=end)


class EmbargoAfterTests(unittest.TestCase):
    def test_embargo_starts_where_test_ends(self):
        test = _interval("t0", 0, 100)
        window = embargo_after(test, embargo_us=25)
        self.assertEqual(window.interval_id, "t0:embargo")
        self.assertEqual(window.start_time_us, 100)
        self.assertEqual(window.end_time_us, 125)

    def test_non_positive_embargo_raises(self):
        test = _interval("t0", 0, 100)
        for width in (0, -10):
            with self.subTest(width=width):
                with self.assertRaises(EmbargoWindowError) as ctx:
                    embargo_after(test, embargo_us=width)
                self.assertEqual(ctx.exception.code, "EMBARGO_WIDTH_INVALID")

    def test_wrong_type_raises(self):
        with self.assertRaises(EmbargoWindowError):
            embargo_after("not-an-interval", embargo_us=10)  # type: ignore[arg-type]


class DropEmbargoedTests(unittest.TestCase):
    def test_overlapping_train_intervals_are_dropped(self):
        train = (_interval("a", 0, 10), _interval("b", 10, 20))
        window = _interval("embargo", 15, 25)
        self.assertEqual(drop_embargoed(train, window), (_interval("a", 0, 10),))

    def test_touching_boundary_is_kept(self):
        train = (_interval("a", 0, 10),)
        window = _interval("embargo", 10, 20)
        self.assertEqual(drop_embargoed(train, window), train)

    def test_empty_train_stays_empty(self):
        window = _interval("embargo", 10, 20)
        self.assertEqual(drop_embargoed((), window), ())
