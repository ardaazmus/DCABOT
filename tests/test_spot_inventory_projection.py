import unittest

from dcabot.application.spot_inventory_projection import (
    SpotFill,
    SpotFillSide,
    SpotInventoryState,
    SpotInventoryError,
    apply_accepted_spot_fill,
    new_spot_inventory_state,
)


class SpotInventoryProjectionTests(unittest.TestCase):
    def setUp(self):
        self.state = new_spot_inventory_state(
            base_asset="BTC", quote_asset="USDT", base_quantity="1"
        )

    def test_buy_increases_base_and_records_exact_quote_cashflow(self):
        result = apply_accepted_spot_fill(
            self.state,
            SpotFill(
                fill_id="fill-buy-1",
                side=SpotFillSide.BUY,
                price="100",
                base_quantity="0.25",
            ),
        )

        self.assertEqual(result.base_quantity, "1.25")
        self.assertEqual(result.quote_cashflow, "-25")

    def test_sell_consumes_owned_base_capacity(self):
        result = apply_accepted_spot_fill(
            self.state,
            SpotFill(
                fill_id="fill-sell-1",
                side=SpotFillSide.SELL,
                price="120",
                base_quantity="0.4",
            ),
        )

        self.assertEqual(result.base_quantity, "0.6")
        self.assertEqual(result.quote_cashflow, "48")
        with self.assertRaisesRegex(SpotInventoryError, "SPOT_INVENTORY_INSUFFICIENT"):
            apply_accepted_spot_fill(
                result,
                SpotFill(
                    fill_id="fill-sell-2",
                    side=SpotFillSide.SELL,
                    price="120",
                    base_quantity="0.7",
                ),
            )

    def test_duplicate_is_idempotent_and_conflict_is_rejected(self):
        fill = SpotFill(
            fill_id="fill-1",
            side=SpotFillSide.BUY,
            price="100",
            base_quantity="0.1",
        )
        first = apply_accepted_spot_fill(self.state, fill)
        duplicate = apply_accepted_spot_fill(first, fill)

        self.assertEqual(duplicate, first)
        with self.assertRaisesRegex(SpotInventoryError, "SPOT_FILL_CONFLICT"):
            apply_accepted_spot_fill(
                first,
                SpotFill(
                    fill_id="fill-1",
                    side=SpotFillSide.BUY,
                    price="101",
                    base_quantity="0.1",
                ),
            )

    def test_projection_has_no_fee_or_pending_order_authority(self):
        result = apply_accepted_spot_fill(
            self.state,
            SpotFill(
                fill_id="fill-buy-2",
                side=SpotFillSide.BUY,
                price="100",
                base_quantity="0.1",
            ),
        )

        self.assertFalse(hasattr(result, "fee"))
        self.assertFalse(hasattr(result, "pending_order"))
        self.assertFalse(hasattr(result, "replacement"))


if __name__ == "__main__":
    unittest.main()
