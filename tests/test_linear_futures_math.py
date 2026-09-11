import unittest

from dcabot.application.linear_futures_math import (
    LinearFuturesPosition,
    project_funding,
)


def position(side="LONG", quantity="1.25", contract_size="1"):
    return LinearFuturesPosition(
        side=side,
        quantity=quantity,
        contract_size=contract_size,
        entry_price="40000",
        mark_price="42000",
        settlement_asset="USDT",
    )


class LinearFuturesMathTests(unittest.TestCase):
    def test_long_and_short_unrealized_pnl_use_explicit_contract_quantity(self):
        self.assertEqual(position().unrealized_pnl, "2500")
        self.assertEqual(position("SHORT").unrealized_pnl, "-2500")
        self.assertEqual(position().position_value, "52500")

    def test_contract_size_is_not_silently_assumed_to_be_one(self):
        contracted = position(quantity="100", contract_size="0.001")

        self.assertEqual(contracted.effective_quantity, "0.1")
        self.assertEqual(contracted.unrealized_pnl, "200")
        self.assertEqual(contracted.position_value, "4200")

    def test_funding_is_timestamped_and_side_signed(self):
        long_funding = project_funding(position(), "0.0001", effective_time_us=1_000)
        short_funding = project_funding(
            position("SHORT"), "0.0001", effective_time_us=1_000
        )
        received_funding = project_funding(
            position(), "-0.0001", effective_time_us=1_000
        )

        self.assertEqual(long_funding.amount, "-5.25")
        self.assertEqual(short_funding.amount, "5.25")
        self.assertEqual(received_funding.amount, "5.25")
        self.assertEqual(long_funding.effective_time_us, 1_000)

    def test_invalid_position_or_funding_context_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "LINEAR_FUTURES_SIDE_INVALID"):
            position("HEDGE")
        with self.assertRaisesRegex(ValueError, "LINEAR_FUTURES_ASSET_INVALID"):
            LinearFuturesPosition(
                "LONG", "1", "1", "100", "100", "USDT/USD"
            )
        with self.assertRaisesRegex(ValueError, "FUNDING_TIME_INVALID"):
            project_funding(position(), "0.0001", effective_time_us=-1)


if __name__ == "__main__":
    unittest.main()
