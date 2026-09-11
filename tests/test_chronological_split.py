import unittest

from dcabot.application.chronological_split import (
    ChronologicalPoint,
    split_chronological,
)


def points(*times):
    return tuple(ChronologicalPoint(f"row-{index}", time) for index, time in enumerate(times))


class ChronologicalSplitTests(unittest.TestCase):
    def test_train_precedes_test_without_future_rows_in_train(self):
        result = split_chronological(points(100, 200, 300, 400, 500), train_count=3)

        self.assertEqual(tuple(point.event_time_us for point in result.train), (100, 200, 300))
        self.assertEqual(tuple(point.event_time_us for point in result.test), (400, 500))
        self.assertLess(max(point.event_time_us for point in result.train), min(point.event_time_us for point in result.test))
        self.assertEqual(result.gap, ())

    def test_explicit_gap_is_excluded_and_does_not_claim_purge_horizon(self):
        result = split_chronological(points(100, 200, 300, 400, 500, 600), train_count=2, gap_count=2)

        self.assertEqual(tuple(point.event_time_us for point in result.train), (100, 200))
        self.assertEqual(tuple(point.event_time_us for point in result.gap), (300, 400))
        self.assertEqual(tuple(point.event_time_us for point in result.test), (500, 600))

    def test_appending_future_rows_preserves_the_existing_prefix(self):
        prefix = points(100, 200, 300, 400, 500)
        original = split_chronological(prefix, train_count=2, gap_count=1)
        extended = split_chronological((*prefix, ChronologicalPoint("row-5", 600)), train_count=2, gap_count=1)

        self.assertEqual(extended.train, original.train)
        self.assertEqual(extended.gap, original.gap)
        self.assertEqual(extended.test[:2], original.test)

    def test_rows_must_be_strictly_chronological_without_implicit_sorting(self):
        with self.assertRaisesRegex(ValueError, "CHRONOLOGY_INVALID"):
            split_chronological(points(100, 300, 200, 400), train_count=2)
        with self.assertRaisesRegex(ValueError, "CHRONOLOGY_INVALID"):
            split_chronological(points(100, 200, 200, 400), train_count=2)

    def test_invalid_boundary_does_not_create_a_partial_split(self):
        with self.assertRaisesRegex(ValueError, "CHRONOLOGICAL_SPLIT_INVALID"):
            split_chronological(points(100, 200, 300), train_count=0)
        with self.assertRaisesRegex(ValueError, "CHRONOLOGICAL_SPLIT_INVALID"):
            split_chronological(points(100, 200, 300), train_count=3)
        with self.assertRaisesRegex(ValueError, "CHRONOLOGICAL_SPLIT_INVALID"):
            split_chronological(points(100, 200, 300), train_count=1, gap_count=2)


if __name__ == "__main__":
    unittest.main()
