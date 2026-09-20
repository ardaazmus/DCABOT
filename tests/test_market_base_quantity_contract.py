from fractions import Fraction as F
import unittest

from dcabot.application.market_base_quantity import (
    MarketExecutionOutcome,
    MarketExecutionStatus,
    MarketBaseExecutionError,
    create_market_base_execution,
)
from dcabot.application.spot_order_lifecycle import SpotSide


class MarketBaseQuantityContractTests(unittest.TestCase):
    def _execution(self, *, side=SpotSide.BUY, reference="100", slippage=100):
        return create_market_base_execution(
            order_id="order-1",
            symbol="BTCUSDT",
            side=side,
            requested_quantity="1",
            reference_price=reference,
            max_slippage_bps=slippage,
        )

    def test_base_quantity_fills_conserve_quote_and_derive_exact_effective_price(self):
        execution = self._execution(slippage=200)
        first = execution.apply_fill(
            execution_id="fill-1",
            base_quantity="0.5",
            quote_quantity="50",
            fee="0.05",
            fee_asset="USDT",
        )
        second = first.execution.apply_fill(
            execution_id="fill-2",
            base_quantity="0.5",
            quote_quantity="51",
            fee="0.051",
            fee_asset="USDT",
        )

        self.assertEqual(second.outcome, MarketExecutionOutcome.ACCEPTED)
        self.assertEqual(second.execution.status, MarketExecutionStatus.PARTIALLY_FILLED)
        self.assertEqual(second.execution.cumulative_base_quantity, "1")
        self.assertEqual(second.execution.cumulative_quote_quantity, "101")
        self.assertEqual(second.execution.effective_price, "101")
        self.assertEqual(second.execution.fee_totals, (("USDT", "0.101"),))
        self.assertEqual(second.execution.remaining_quantity, "0")
        self.assertEqual(second.execution.effective_price_fraction, F(101))

    def test_slippage_is_checked_against_side_and_does_not_mutate_on_rejection(self):
        execution = self._execution(slippage=50)

        with self.assertRaisesRegex(MarketBaseExecutionError, "MARKET_SLIPPAGE_EXCEEDED"):
            execution.apply_fill(
                execution_id="fill-1",
                base_quantity="1",
                quote_quantity="101",
                fee="0",
                fee_asset="USDT",
            )

        self.assertEqual(execution.cumulative_base_quantity, "0")
        self.assertEqual(execution.fills, ())

    def test_sell_slippage_is_directional_and_cancel_preserves_residual(self):
        execution = self._execution(side=SpotSide.SELL, slippage=100)
        result = execution.apply_fill(
            execution_id="fill-1",
            base_quantity="0.4",
            quote_quantity="39.6",
            fee="0.0396",
            fee_asset="USDT",
        )
        canceled = result.execution.close(MarketExecutionStatus.CANCELED)

        self.assertEqual(canceled.status, MarketExecutionStatus.CANCELED)
        self.assertEqual(canceled.remaining_quantity, "0.6")
        self.assertEqual(canceled.effective_price, "99")

    def test_fill_duplicate_is_idempotent_and_conflict_is_rejected(self):
        execution = self._execution()
        first = execution.apply_fill(
            execution_id="fill-1",
            base_quantity="1",
            quote_quantity="100",
            fee="0",
            fee_asset="USDT",
        )
        duplicate = first.execution.apply_fill(
            execution_id="fill-1",
            base_quantity="1",
            quote_quantity="100",
            fee="0",
            fee_asset="USDT",
        )

        self.assertEqual(duplicate.outcome, MarketExecutionOutcome.DUPLICATE)
        with self.assertRaisesRegex(MarketBaseExecutionError, "MARKET_FILL_CONFLICT"):
            first.execution.apply_fill(
                execution_id="fill-1",
                base_quantity="1",
                quote_quantity="101",
                fee="0",
                fee_asset="USDT",
            )

    def test_filled_close_requires_requested_base_quantity(self):
        execution = self._execution()
        result = execution.apply_fill(
            execution_id="fill-1",
            base_quantity="0.4",
            quote_quantity="40",
            fee="0",
            fee_asset="USDT",
        )

        with self.assertRaisesRegex(MarketBaseExecutionError, "MARKET_FILL_COVERAGE_INVALID"):
            result.execution.close(MarketExecutionStatus.FILLED)

    def test_non_terminating_effective_price_fails_closed(self):
        with self.assertRaisesRegex(MarketBaseExecutionError, "MARKET_FILL_NOT_EXACT"):
            self._execution(slippage=2_000).apply_fill(
                execution_id="fill-1",
                base_quantity="0.6",
                quote_quantity="61",
                fee="0",
                fee_asset="USDT",
            )


if __name__ == "__main__":
    unittest.main()
