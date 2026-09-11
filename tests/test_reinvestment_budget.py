import unittest

from dcabot.application.reinvestment_budget import (
    ReinvestmentBudget,
    ReinvestmentBudgetError,
    build_reinvestment_budget,
)


class ReinvestmentBudgetTests(unittest.TestCase):
    def test_realized_profit_pool_produces_exact_reinvestment_budget(self):
        result = build_reinvestment_budget(
            asset="USDT", realized_profit_eligible="100", percent="0.5"
        )

        self.assertEqual(
            result,
            ReinvestmentBudget(
                asset="USDT",
                pool_kind="REALIZED_PROFIT_ELIGIBLE",
                realized_profit_eligible="100",
                percent="0.5",
                budget="50",
            ),
        )

    def test_zero_percent_or_pool_does_not_create_hidden_budget(self):
        self.assertEqual(
            build_reinvestment_budget(
                asset="USDT", realized_profit_eligible="0", percent="0.5"
            ).budget,
            "0",
        )
        self.assertEqual(
            build_reinvestment_budget(
                asset="USDT", realized_profit_eligible="100", percent="0"
            ).budget,
            "0",
        )

    def test_unrealized_or_wrong_asset_context_fails_closed(self):
        with self.assertRaisesRegex(
            ReinvestmentBudgetError, "REINVESTMENT_POOL_INVALID"
        ):
            build_reinvestment_budget(
                asset="USDT", realized_profit_eligible="-1", percent="0.5"
            )
        with self.assertRaisesRegex(
            ReinvestmentBudgetError, "REINVESTMENT_ASSET_INVALID"
        ):
            build_reinvestment_budget(
                asset="usdt", realized_profit_eligible="100", percent="0.5"
            )


if __name__ == "__main__":
    unittest.main()
