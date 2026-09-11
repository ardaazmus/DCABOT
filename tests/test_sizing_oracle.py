from decimal import Decimal
import unittest

from dcabot.application.ladder_conservation import validate_ladder_allocations
from dcabot.application.ladder_binding import build_ladder_binding
from dcabot.application.sizing_units import build_sizing_candidate


def decimal_text(value: Decimal) -> str:
    text = format(value, "f").rstrip("0").rstrip(".")
    return text or "0"


class SizingOracleTests(unittest.TestCase):
    def test_quote_candidate_matches_independent_decimal_oracle(self):
        result = build_sizing_candidate(
            sizing_mode="QUOTE_NOTIONAL", amount="100", reference_price="250"
        )
        expected_quantity = Decimal("100") / Decimal("250")

        self.assertEqual(result.candidate_quantity, decimal_text(expected_quantity))
        self.assertEqual(result.candidate_notional, "100")

    def test_equivalent_decimal_spellings_and_allocation_order_are_invariant(self):
        canonical = build_sizing_candidate(
            sizing_mode="BASE_QTY", amount="0.4", reference_price="250"
        )
        alternate = build_sizing_candidate(
            sizing_mode="BASE_QTY", amount="0.40", reference_price="250.00"
        )
        self.assertEqual(canonical, alternate)

        first = validate_ladder_allocations(
            allocation_unit="QUOTE_NOTIONAL",
            allocations=("0.10", "0.20", "0.30"),
            budget="1",
        )
        reordered = validate_ladder_allocations(
            allocation_unit="QUOTE_NOTIONAL",
            allocations=("0.30", "0.10", "0.20"),
            budget="1.00",
        )
        self.assertEqual(first, reordered)

    def test_ladder_levels_match_independent_decimal_formula(self):
        result = build_ladder_binding(
            anchor_price="100",
            safety_qty="0.1",
            safety_count=2,
            deviation="0.1",
            step_multiplier="1",
            volume_multiplier="1",
            price_tick="0.5",
            qty_step="0.1",
            allocation_unit="QUOTE_NOTIONAL",
            budget="20",
        )
        anchor = Decimal("100")
        expected_prices = tuple(
            decimal_text(anchor * (Decimal("1") - Decimal("0.1") * index))
            for index in (1, 2)
        )

        self.assertEqual(
            tuple(level.price for level in result.levels), expected_prices
        )
        self.assertEqual(
            tuple(level.allocation for level in result.levels), ("9", "8")
        )


if __name__ == "__main__":
    unittest.main()
