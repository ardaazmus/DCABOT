import unittest

from dcabot.application.balance_percent_sizing import (
    BalancePercentError,
    BalancePercentBudget,
    build_balance_percent_budget,
)


class BalancePercentSizingTests(unittest.TestCase):
    def test_tagged_eligible_balance_produces_exact_budget(self):
        result = build_balance_percent_budget(
            balance_source="PAPER_SETTLED_BALANCE",
            asset="USDT",
            eligible_balance="1000",
            percent="0.25",
        )

        self.assertEqual(
            result,
            BalancePercentBudget(
                balance_source="PAPER_SETTLED_BALANCE",
                asset="USDT",
                eligible_balance="1000",
                percent="0.25",
                budget="250",
            ),
        )

    def test_missing_or_unbounded_balance_context_fails_closed(self):
        with self.assertRaisesRegex(
            BalancePercentError, "BALANCE_SOURCE_INVALID"
        ):
            build_balance_percent_budget(
                balance_source="", asset="USDT", eligible_balance="1000", percent="0.25"
            )
        with self.assertRaisesRegex(
            BalancePercentError, "BALANCE_PERCENT_INVALID"
        ):
            build_balance_percent_budget(
                balance_source="PAPER_SETTLED_BALANCE",
                asset="USDT",
                eligible_balance="1000",
                percent="1.01",
            )

    def test_asset_and_numeric_inputs_are_explicit(self):
        with self.assertRaisesRegex(BalancePercentError, "BALANCE_ASSET_INVALID"):
            build_balance_percent_budget(
                balance_source="PAPER_SETTLED_BALANCE",
                asset="usdt",
                eligible_balance="1000",
                percent="0.25",
            )
        with self.assertRaisesRegex(
            BalancePercentError, "ELIGIBLE_BALANCE_INVALID"
        ):
            build_balance_percent_budget(
                balance_source="PAPER_SETTLED_BALANCE",
                asset="USDT",
                eligible_balance="0",
                percent="0.25",
            )


if __name__ == "__main__":
    unittest.main()
