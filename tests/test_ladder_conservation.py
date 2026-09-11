import unittest

from dcabot.application.ladder_conservation import (
    LadderConservationError,
    LadderConservation,
    validate_ladder_allocations,
)


class LadderConservationTests(unittest.TestCase):
    def test_allocations_are_summed_exactly_with_remaining_budget(self):
        result = validate_ladder_allocations(
            allocation_unit="QUOTE_NOTIONAL",
            allocations=("0.10", "0.20", "0.30"),
            budget="1.00",
        )

        self.assertEqual(
            result,
            LadderConservation(
                allocation_unit="QUOTE_NOTIONAL",
                total_allocated="0.6",
                budget="1",
                remaining_budget="0.4",
            ),
        )

    def test_allocation_over_budget_is_rejected(self):
        with self.assertRaisesRegex(
            LadderConservationError, "LADDER_BUDGET_EXCEEDED"
        ):
            validate_ladder_allocations(
                allocation_unit="BASE_QTY",
                allocations=("0.3", "0.3"),
                budget="0.5",
            )

    def test_unknown_unit_or_invalid_allocation_fails_closed(self):
        with self.assertRaisesRegex(
            LadderConservationError, "LADDER_UNIT_INVALID"
        ):
            validate_ladder_allocations(
                allocation_unit="MIXED", allocations=("1",), budget="2"
            )
        with self.assertRaisesRegex(
            LadderConservationError, "LADDER_ALLOCATION_INVALID"
        ):
            validate_ladder_allocations(
                allocation_unit="BASE_QTY", allocations=("0",), budget="2"
            )


if __name__ == "__main__":
    unittest.main()
