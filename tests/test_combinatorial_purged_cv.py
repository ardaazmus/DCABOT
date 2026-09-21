"""Faz 14.3: kombinatoryal purge + embargo + path üretici (CPCV)."""
import unittest

from dcabot.application.chronological_split import ChronologicalPoint
from dcabot.application.combinatorial_purged_cv import (
    CombinatorialPurgedCvError,
    combinatorial_purged_paths,
    reconstruct_paths,
    score_paths,
    split_into_groups,
    test_combinations,
)
from dcabot.application.horizon_overlap import TimeInterval


def _points(count: int) -> tuple[ChronologicalPoint, ...]:
    return tuple(
        ChronologicalPoint(sample_id=f"s{i}", event_time_us=i * 100) for i in range(count)
    )


def _interval(identity: str, start: int, end: int) -> TimeInterval:
    return TimeInterval(interval_id=identity, start_time_us=start, end_time_us=end)


def _disjoint_horizons(count: int) -> dict[str, TimeInterval]:
    return {f"s{i}": _interval(f"h{i}", i * 100, i * 100 + 50) for i in range(count)}


class SplitIntoGroupsTests(unittest.TestCase):
    def test_contiguous_sizes_differ_by_at_most_one(self):
        groups = split_into_groups(_points(10), group_count=4)
        self.assertEqual([len(g) for g in groups], [3, 3, 2, 2])
        self.assertEqual(
            [p.sample_id for g in groups for p in g],
            [f"s{i}" for i in range(10)],
        )

    def test_invalid_group_counts_raise(self):
        for count in (0, 1, 11):
            with self.subTest(count=count):
                with self.assertRaises(CombinatorialPurgedCvError):
                    split_into_groups(_points(10), group_count=count)


class TestCombinationsTests(unittest.TestCase):
    def test_four_choose_two_is_six_lexicographic(self):
        combos = test_combinations(group_count=4, test_group_count=2)
        self.assertEqual(len(combos), 6)
        self.assertEqual(combos[0], (0, 1))
        self.assertEqual(combos[-1], (2, 3))
        self.assertEqual(tuple(sorted(combos)), combos)

    def test_invalid_k_raises(self):
        for k in (0, 4):
            with self.subTest(k=k):
                with self.assertRaises(CombinatorialPurgedCvError):
                    test_combinations(group_count=4, test_group_count=k)


class ReconstructPathsTests(unittest.TestCase):
    def test_each_path_covers_every_group_exactly_once(self):
        members = {0: ("a",), 1: ("b",), 2: ("c",), 3: ("d",)}
        paths = reconstruct_paths(group_count=4, test_group_count=2, test_members=members)
        self.assertEqual(len(paths), 3)  # phi = k*C(N,k)/N = 2*6/4
        for path in paths:
            self.assertEqual(tuple(sorted(path)), ("a", "b", "c", "d"))

    def test_single_test_group_gives_one_full_path(self):
        members = {0: ("a", "b"), 1: ("c",)}
        paths = reconstruct_paths(group_count=2, test_group_count=1, test_members=members)
        self.assertEqual(paths, (("a", "b", "c"),))


class CombinatorialPurgedPathsTests(unittest.TestCase):
    def test_no_overlap_no_purge_full_paths(self):
        points = _points(8)
        horizons = _disjoint_horizons(8)
        result = combinatorial_purged_paths(
            points,
            group_count=4,
            test_group_count=1,
            label_horizons=horizons,
            feature_intervals=horizons,
            embargo_us=10,
        )
        self.assertEqual(len(result.combos), 4)
        self.assertEqual(len(result.paths), 1)
        self.assertEqual(len(result.paths[0]), 8)
        for train in result.train_sets:
            self.assertEqual(len(train), 6)

    def test_overlapping_label_is_purged_from_train(self):
        points = _points(4)
        labels = _disjoint_horizons(4)
        labels["s0"] = _interval("h0", 0, 350)  # s0 etiketi s3 test aralığıyla çakışır
        features = _disjoint_horizons(4)
        result = combinatorial_purged_paths(
            points,
            group_count=4,
            test_group_count=1,
            label_horizons=labels,
            feature_intervals=features,
            embargo_us=10,
        )
        combo_with_s3 = next(c for c in result.combos if "s3" in c.test_sample_ids)
        train = result.train_sets[result.combos.index(combo_with_s3)]
        self.assertNotIn("s0", train)

    def test_embargo_drops_train_after_test(self):
        points = _points(4)
        horizons = _disjoint_horizons(4)
        result = combinatorial_purged_paths(
            points,
            group_count=2,
            test_group_count=1,
            label_horizons=horizons,
            feature_intervals=horizons,
            embargo_us=1_000,
        )
        combo_with_first = next(c for c in result.combos if "s0" in c.test_sample_ids)
        train = result.train_sets[result.combos.index(combo_with_first)]
        self.assertEqual(train, ())


class ScorePathsTests(unittest.TestCase):
    def test_scores_each_path_with_float_boundary(self):
        paths = (("s0", "s1", "s2"), ("s2", "s1", "s0"))
        returns = {"s0": "0.01", "s1": "0.02", "s2": "0.03"}
        scores = score_paths(paths, returns)
        self.assertEqual(len(scores), 2)
        self.assertAlmostEqual(scores[0], 2.0, places=9)

    def test_missing_return_raises(self):
        with self.assertRaises(CombinatorialPurgedCvError):
            score_paths((("s0", "s9"),), {"s0": "0.01"})

    def test_empty_paths_raise(self):
        with self.assertRaises(CombinatorialPurgedCvError):
            score_paths((), {"s0": "0.01"})
