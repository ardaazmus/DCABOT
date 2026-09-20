import unittest

from dcabot.application.isolated_liquidation import (
    IsolatedLiquidationError,
    IsolatedMarginSnapshot,
    IsolatedRiskTier,
    project_isolated_liquidation,
)


class IsolatedLiquidationTests(unittest.TestCase):
    def setUp(self):
        self.tier = IsolatedRiskTier("tier-1", "0", "200", "0.25", "0", 1_000)
        self.margin = IsolatedMarginSnapshot("USDT", "40", "100", 2_000)

    def test_long_and_short_use_independent_fixed_tier_roots(self):
        long = project_isolated_liquidation("LONG", "1", "1", "100", self.margin, self.tier)
        short = project_isolated_liquidation("SHORT", "1", "1", "100", self.margin, self.tier)
        self.assertEqual(long.liquidation_price, "80")
        self.assertEqual(short.liquidation_price, "112")
        self.assertEqual((long.status, long.mark_price, short.settlement_asset), ("ESTIMATE_ONLY", "100", "USDT"))

    def test_missing_or_outdated_authority_fails_closed(self):
        with self.assertRaisesRegex(IsolatedLiquidationError, "LIQUIDATION_SNAPSHOT_TIME_INVALID"):
            project_isolated_liquidation(
                "LONG", "1", "1", "100", IsolatedMarginSnapshot("USDT", "40", "100", 999), self.tier
            )
        with self.assertRaisesRegex(IsolatedLiquidationError, "LIQUIDATION_TIER_MISMATCH"):
            project_isolated_liquidation(
                "LONG", "1", "1", "100", self.margin,
                IsolatedRiskTier("tier-small", "0", "50", "0.25", "0", 1_000),
            )

    def test_non_terminating_root_is_not_silently_rounded(self):
        with self.assertRaisesRegex(IsolatedLiquidationError, "LIQUIDATION_RESULT_NOT_REPRESENTABLE"):
            project_isolated_liquidation(
                "LONG", "1", "1", "100", IsolatedMarginSnapshot("USDT", "40", "100", 2_000),
                IsolatedRiskTier("tier-recurring", "0", "200", "0.30", "0", 1_000),
            )


if __name__ == "__main__":
    unittest.main()
