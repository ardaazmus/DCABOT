import unittest

from dcabot.application.futures_dca_plan import (
    FuturesDcaPlanError,
    project_futures_dca_plan,
)


class FuturesDcaPlanTests(unittest.TestCase):
    def test_long_plan_uses_cumulative_deviation_and_volume_scale(self):
        result = project_futures_dca_plan(
            side="LONG", anchor_price="100", base_amount="10", base_sizing="QUOTE_NOTIONAL",
            safety_amount="2", safety_sizing="QUOTE_NOTIONAL", safety_count=2,
            deviation="0.01", step_multiplier="2", volume_multiplier="2",
            price_tick="0.01", quantity_step="0.0001",
        )
        self.assertEqual(tuple((level.price, level.quote_allocation) for level in result.levels), (("99", "1.9998"), ("97", "3.9964")))
        self.assertEqual((result.base_quantity, result.required_capital, result.max_covered_deviation), ("0.1", "15.9962", "0.03"))

    def test_short_plan_reverses_price_direction(self):
        result = project_futures_dca_plan(
            side="SHORT", anchor_price="100", base_amount="1", base_sizing="BASE_QTY",
            safety_amount="0.1", safety_sizing="BASE_QTY", safety_count=2,
            deviation="0.01", step_multiplier="1", volume_multiplier="1",
            price_tick="0.5", quantity_step="0.1",
        )
        self.assertEqual(tuple(level.price for level in result.levels), ("101", "102"))
        self.assertEqual(result.required_capital, "120.3")

    def test_budget_and_anchor_boundaries_fail_closed(self):
        with self.assertRaisesRegex(FuturesDcaPlanError, "FUTURES_DCA_BUDGET_EXCEEDED"):
            project_futures_dca_plan(
                side="LONG", anchor_price="100", base_amount="10", base_sizing="QUOTE_NOTIONAL",
                safety_amount="2", safety_sizing="QUOTE_NOTIONAL", safety_count=2,
                deviation="0.01", step_multiplier="2", volume_multiplier="2",
                price_tick="0.01", quantity_step="0.0001", budget="15",
            )
        with self.assertRaisesRegex(FuturesDcaPlanError, "FUTURES_DCA_ANCHOR_OFF_GRID"):
            project_futures_dca_plan(
                side="LONG", anchor_price="100.01", base_amount="1", base_sizing="BASE_QTY",
                safety_amount="0.1", safety_sizing="BASE_QTY", safety_count=1,
                deviation="0.01", step_multiplier="1", volume_multiplier="1",
                price_tick="0.5", quantity_step="0.1",
            )


if __name__ == "__main__":
    unittest.main()
