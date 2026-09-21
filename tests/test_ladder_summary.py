import unittest

from dcabot.application.ladder_summary import (
    LadderLeg,
    LadderSummaryError,
    summarize_ladder,
)


def leg(price, shares):
    return LadderLeg(price=price, shares=shares)


class LadderSummaryTests(unittest.TestCase):
    def test_exact_weighted_average_reports_value_and_flag(self):
        summary = summarize_ladder(
            direction="LONG",
            legs=[leg("100", "1"), leg("150", "2"), leg("200", "1")],
        )

        self.assertEqual(summary.direction, "LONG")
        self.assertEqual(summary.leg_count, 3)
        self.assertEqual(summary.total_shares, "4")
        self.assertEqual(summary.weighted_average_entry, "150")
        self.assertTrue(summary.weighted_average_exact)

    def test_non_terminating_average_reports_inexact_without_rounding(self):
        summary = summarize_ladder(
            direction="LONG",
            legs=[leg("100", "1"), leg("150", "2")],
        )

        self.assertEqual(summary.total_shares, "3")
        self.assertIsNone(summary.weighted_average_entry)
        self.assertFalse(summary.weighted_average_exact)

    def test_short_direction_accepted(self):
        summary = summarize_ladder(direction="SHORT", legs=[leg("200", "3")])

        self.assertEqual((summary.total_shares, summary.weighted_average_entry), ("3", "200"))
        self.assertTrue(summary.weighted_average_exact)

    def test_zero_share_legs_do_not_move_totals(self):
        summary = summarize_ladder(
            direction="LONG",
            legs=[leg("100", "0"), leg("200", "2")],
        )

        self.assertEqual(summary.total_shares, "2")
        self.assertEqual(summary.weighted_average_entry, "200")

    def test_invalid_inputs_raise_coded_errors(self):
        with self.assertRaises(LadderSummaryError):
            summarize_ladder(direction="NEUTRAL", legs=[leg("100", "1")])
        with self.assertRaises(LadderSummaryError):
            summarize_ladder(direction="LONG", legs=[])
        with self.assertRaises(LadderSummaryError):
            summarize_ladder(direction="LONG", legs=[leg("100", "1")] * 129)
        with self.assertRaises(LadderSummaryError):
            summarize_ladder(direction="LONG", legs=[leg("bed", "1")])
        with self.assertRaises(LadderSummaryError):
            summarize_ladder(direction="LONG", legs=[leg("100", "1.5")])
        with self.assertRaises(LadderSummaryError):
            summarize_ladder(direction="LONG", legs=[leg("100", "0")])
        with self.assertRaises(LadderSummaryError):
            summarize_ladder(direction="LONG", legs=["not-a-leg"])


if __name__ == "__main__":
    unittest.main()
