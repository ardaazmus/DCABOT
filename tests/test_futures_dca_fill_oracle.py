from decimal import Decimal
import unittest

from dcabot.application.futures_dca_fill_projection import (
    FuturesDcaFill,
    project_futures_dca_fills,
)
from dcabot.application.futures_dca_plan import project_futures_dca_plan


class FuturesDcaFillOracleTests(unittest.TestCase):
    def test_long_average_and_pending_reserve_match_independent_decimal_math(self):
        plan = project_futures_dca_plan(
            side="LONG", anchor_price="100", base_amount="10", base_sizing="QUOTE_NOTIONAL",
            safety_amount="2", safety_sizing="QUOTE_NOTIONAL", safety_count=2,
            deviation="0.01", step_multiplier="2", volume_multiplier="2",
            price_tick="0.01", quantity_step="0.0001",
        )
        result = project_futures_dca_fills(
            plan,
            (FuturesDcaFill("base", 0, "0.1", "100"), FuturesDcaFill("s1", 1, "0.02", "97")),
        )
        quantity = Decimal("0.1") + Decimal("0.02")
        notional = Decimal("0.1") * Decimal("100") + Decimal("0.02") * Decimal("97")
        pending = (Decimal("0.0202") - Decimal("0.02")) * Decimal("99")
        self.assertEqual((result.average_entry, result.pending_reserved_quote), (str(notional / quantity), str(pending)))

    def test_short_average_matches_independent_decimal_math(self):
        plan = project_futures_dca_plan(
            side="SHORT", anchor_price="100", base_amount="0.1", base_sizing="BASE_QTY",
            safety_amount="0.1", safety_sizing="BASE_QTY", safety_count=1,
            deviation="0.01", step_multiplier="1", volume_multiplier="1",
            price_tick="0.5", quantity_step="0.1",
        )
        result = project_futures_dca_fills(
            plan,
            (FuturesDcaFill("base", 0, "0.1", "100"), FuturesDcaFill("s1", 1, "0.1", "101")),
        )
        expected = (Decimal("0.1") * Decimal("100") + Decimal("0.1") * Decimal("101")) / Decimal("0.2")
        self.assertEqual(result.average_entry, str(expected))


if __name__ == "__main__":
    unittest.main()
