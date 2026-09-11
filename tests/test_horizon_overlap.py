import unittest

from dcabot.application.horizon_overlap import (
    HorizonStatus,
    TimeInterval,
    assess_purge_requirement,
)


def interval(interval_id, start, end):
    return TimeInterval(interval_id, start, end)


class HorizonOverlapTests(unittest.TestCase):
    def test_adjacent_feature_and_label_intervals_need_no_purge(self):
        result = assess_purge_requirement(
            (interval("label-1", 100, 200),),
            (interval("feature-1", 200, 300),),
        )

        self.assertEqual(result.status, HorizonStatus.NO_OVERLAP)
        self.assertEqual(result.overlapping_interval_ids, ())

    def test_overlapping_label_horizon_requires_purge_decision(self):
        result = assess_purge_requirement(
            (interval("label-1", 100, 250),),
            (interval("feature-1", 200, 300),),
        )

        self.assertEqual(result.status, HorizonStatus.PURGE_REQUIRED)
        self.assertEqual(result.overlapping_interval_ids, ("feature-1", "label-1"))

    def test_multiple_overlaps_are_reported_deterministically(self):
        result = assess_purge_requirement(
            (
                interval("label-a", 100, 250),
                interval("label-b", 400, 500),
            ),
            (
                interval("feature-a", 200, 300),
                interval("feature-z", 450, 600),
            ),
        )

        self.assertEqual(
            result.overlapping_interval_ids,
            ("feature-a", "feature-z", "label-a", "label-b"),
        )

    def test_invalid_or_duplicate_intervals_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "HORIZON_INTERVAL_INVALID"):
            interval("bad", 300, 300)
        with self.assertRaisesRegex(ValueError, "HORIZON_INTERVAL_ORDER"):
            assess_purge_requirement(
                (interval("label-1", 200, 300), interval("label-2", 100, 150)),
                (),
            )
        with self.assertRaisesRegex(ValueError, "HORIZON_INTERVAL_DUPLICATE"):
            assess_purge_requirement(
                (interval("same", 100, 200),),
                (interval("same", 200, 300),),
            )


if __name__ == "__main__":
    unittest.main()
