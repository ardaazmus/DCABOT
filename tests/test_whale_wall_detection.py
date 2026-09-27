"""Faz 17 E.3: Whale Wall Detection Faz-0 analytics -- median/MAD anomaly
(z^2-comparison, no sqrt) + percentile + cumulative-band share + a
persistence tracker + trade cross-verification. Output is CONFIRMED-only;
no consumer (SO/TP nudging) exists yet -- that is a later, separate dilim.
"""
import unittest

from dcabot.application.whale_wall_detection import (
    WallCandidate,
    WhaleWallDetectionError,
    WhaleWallTracker,
    compute_mad,
    compute_median,
    cumulative_band_share,
    find_wall_candidates,
    is_statistically_anomalous,
    percentile_rank,
)


class MedianMadTests(unittest.TestCase):
    def test_median_of_odd_count(self):
        self.assertEqual(compute_median(("1", "5", "3")), "3")

    def test_median_of_even_count_averages_middle_two(self):
        self.assertEqual(compute_median(("1", "2", "3", "4")), "2.5")

    def test_median_rejects_empty(self):
        with self.assertRaises(WhaleWallDetectionError):
            compute_median(())

    def test_mad_is_median_of_absolute_deviations(self):
        # values 1,2,3,4,100 -> median 3 -> deviations 2,1,0,1,97 -> sorted 0,1,1,2,97 -> mad 1
        self.assertEqual(compute_mad(("1", "2", "3", "4", "100"), "3"), "1")


class StatisticalAnomalyTests(unittest.TestCase):
    def test_value_far_from_median_is_anomalous(self):
        # median 3, mad 1, threshold 2 -> boundary at median +/- 2 -> 100 is far beyond
        self.assertTrue(is_statistically_anomalous("100", "3", "1", z_threshold="2"))

    def test_value_near_median_is_not_anomalous(self):
        self.assertFalse(is_statistically_anomalous("4", "3", "1", z_threshold="2"))

    def test_boundary_is_anomalous_inclusive(self):
        # median 3, mad 1, threshold 2 -> boundary value 5 -> (5-3)^2=4 == (2*1)^2=4
        self.assertTrue(is_statistically_anomalous("5", "3", "1", z_threshold="2"))

    def test_zero_mad_never_flags_a_difference(self):
        # degenerate uniform book -- cannot establish significance, fail closed to False.
        self.assertFalse(is_statistically_anomalous("10", "3", "0", z_threshold="2"))
        self.assertFalse(is_statistically_anomalous("3", "3", "0", z_threshold="2"))


class PercentileRankTests(unittest.TestCase):
    def test_max_value_has_rank_one(self):
        self.assertEqual(percentile_rank("10", ("1", "2", "10")), "1")

    def test_min_value_has_rank_third(self):
        self.assertEqual(percentile_rank("1", ("1", "2", "10")), "0.333333333333")

    def test_rejects_value_not_in_population(self):
        with self.assertRaises(WhaleWallDetectionError):
            percentile_rank("99", ("1", "2", "10"))


class CumulativeBandShareTests(unittest.TestCase):
    def test_lone_level_has_full_band_share(self):
        levels = {"100": "50"}
        self.assertEqual(cumulative_band_share("100", "50", levels, band_width_fraction="0.01"), "1")

    def test_share_drops_when_neighbors_in_band_are_large(self):
        levels = {"100": "50", "100.5": "150"}
        # band = 1% of 100 -> [99, 101], both levels included -> 50/(50+150)=0.25
        self.assertEqual(cumulative_band_share("100", "50", levels, band_width_fraction="0.01"), "0.25")

    def test_neighbors_outside_band_are_excluded(self):
        levels = {"100": "50", "200": "999"}
        self.assertEqual(cumulative_band_share("100", "50", levels, band_width_fraction="0.01"), "1")


class FindWallCandidatesTests(unittest.TestCase):
    def test_finds_the_single_outlier_level(self):
        levels = {"99": "1", "100": "500", "101": "1.2", "102": "0.9"}
        candidates = find_wall_candidates(
            levels,
            side="bid",
            z_threshold="2",
            min_percentile="0.9",
            min_band_share="0.5",
            band_width_fraction="0.01",
        )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].price, "100")
        self.assertEqual(candidates[0].side, "bid")

    def test_uniform_book_has_no_candidates(self):
        levels = {"99": "10", "100": "10", "101": "10"}
        candidates = find_wall_candidates(
            levels, side="ask", z_threshold="2", min_percentile="0.9",
            min_band_share="0.5", band_width_fraction="0.01",
        )
        self.assertEqual(candidates, ())


class WhaleWallTrackerTests(unittest.TestCase):
    def _candidate(self, price="100", qty="500"):
        return WallCandidate(side="bid", price=price, qty=qty)

    def test_candidate_is_not_persistent_before_the_window(self):
        tracker = WhaleWallTracker(persistence_window=3)
        result = tracker.observe((self._candidate(),), now_us=1_000_000)
        self.assertEqual(result, ())

    def test_candidate_becomes_persistent_after_window_consecutive_observations(self):
        tracker = WhaleWallTracker(persistence_window=3)
        tracker.observe((self._candidate(),), now_us=1_000_000)
        tracker.observe((self._candidate(),), now_us=2_000_000)
        result = tracker.observe((self._candidate(),), now_us=3_000_000)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].price, "100")

    def test_missing_one_round_resets_the_streak(self):
        tracker = WhaleWallTracker(persistence_window=3)
        tracker.observe((self._candidate(),), now_us=1_000_000)
        tracker.observe((), now_us=2_000_000)  # gone for a round
        tracker.observe((self._candidate(),), now_us=3_000_000)
        result = tracker.observe((self._candidate(),), now_us=4_000_000)
        self.assertEqual(result, ())  # only 2 consecutive since the reset

    def test_confirm_rejects_a_wall_already_consumed_by_trades(self):
        tracker = WhaleWallTracker(persistence_window=1)
        (persistent,) = tracker.observe((self._candidate(qty="500"),), now_us=1_000_000)
        confirmed = tracker.confirm(persistent, traded_qty_since_first_seen="500")
        self.assertIsNone(confirmed)

    def test_confirm_accepts_a_wall_not_yet_consumed(self):
        tracker = WhaleWallTracker(persistence_window=1)
        (persistent,) = tracker.observe((self._candidate(qty="500"),), now_us=1_000_000)
        confirmed = tracker.confirm(persistent, traded_qty_since_first_seen="10")
        self.assertIsNotNone(confirmed)
        self.assertEqual(confirmed.price, "100")
        self.assertEqual(confirmed.consecutive_observations, 1)


if __name__ == "__main__":
    unittest.main()
