import unittest

from dcabot.application.linear_futures_math import (
    LinearFuturesPosition,
    project_partial_close,
)


def position(side="LONG"):
    return LinearFuturesPosition(
        side=side,
        quantity="1.25",
        contract_size="1",
        entry_price="40000",
        mark_price="42000",
        settlement_asset="USDT",
    )


class LinearFuturesPartialCloseTests(unittest.TestCase):
    def test_long_partial_close_conserves_quantity_and_reports_gross_pnl(self):
        result = project_partial_close(position(), "0.5", "43000")

        self.assertEqual(result.closed_quantity, "0.5")
        self.assertEqual(result.remaining_quantity, "0.75")
        self.assertEqual(result.closed_effective_quantity, "0.5")
        self.assertEqual(result.realized_gross_pnl, "1500")
        self.assertEqual(result.settlement_asset, "USDT")

    def test_short_partial_close_uses_the_opposite_signed_price_difference(self):
        result = project_partial_close(position("SHORT"), "0.5", "37000")

        self.assertEqual(result.realized_gross_pnl, "1500")
        self.assertEqual(result.remaining_quantity, "0.75")

    def test_full_close_is_allowed_but_overclose_fails_closed(self):
        result = project_partial_close(position(), "1.25", "42000")
        self.assertEqual(result.remaining_quantity, "0")
        self.assertEqual(result.realized_gross_pnl, "2500")

        with self.assertRaisesRegex(ValueError, "LINEAR_FUTURES_CLOSE_OVERFLOW"):
            project_partial_close(position(), "1.26", "42000")


if __name__ == "__main__":
    unittest.main()
