import unittest

from dcabot.server.api import (
    _futures_grid_levels,
    _futures_position_pnl,
    _validate_futures_grid_levels_payload,
    _validate_futures_position_pnl_payload,
)


class FuturesGridLevelsApiTests(unittest.TestCase):
    def test_arithmetic_levels(self):
        validated, fields = _validate_futures_grid_levels_payload(
            {
                "direction": "LONG",
                "level_mode": "ARITHMETIC",
                "lower_price": "100",
                "upper_price": "200",
                "interval_count": 2,
                "price_tick": "1",
                "tick_origin": "0",
            }
        )
        self.assertEqual(fields, {})
        result = _futures_grid_levels(validated)
        self.assertEqual(result["levels"], ["100", "150", "200"])
        self.assertEqual(result["arithmetic_step"], "50")
        self.assertEqual(result["profile"]["margin_mode"], "ISOLATED")
        self.assertEqual(result["profile"]["leverage"], "1")

    def test_bad_direction_is_field_error(self):
        validated, fields = _validate_futures_grid_levels_payload(
            {
                "direction": "UP",
                "level_mode": "ARITHMETIC",
                "lower_price": "100",
                "upper_price": "200",
                "interval_count": 2,
                "price_tick": "1",
                "tick_origin": "0",
            }
        )
        self.assertIsNone(validated)
        self.assertIn("direction", fields)

    def test_non_integer_intervals_is_field_error(self):
        validated, fields = _validate_futures_grid_levels_payload(
            {
                "direction": "LONG",
                "level_mode": "ARITHMETIC",
                "lower_price": "100",
                "upper_price": "200",
                "interval_count": "2",
                "price_tick": "1",
                "tick_origin": "0",
            }
        )
        self.assertIsNone(validated)
        self.assertIn("interval_count", fields)


class FuturesPositionPnlApiTests(unittest.TestCase):
    def test_long_upl_without_leverage_multiplier(self):
        validated, fields = _validate_futures_position_pnl_payload(
            {
                "side": "LONG",
                "quantity": "2",
                "contract_size": "0.5",
                "entry_price": "50000",
                "mark_price": "51000",
                "settlement_asset": "USDT",
            }
        )
        self.assertEqual(fields, {})
        result = _futures_position_pnl(validated)
        self.assertEqual(result["effective_quantity"], "1")
        self.assertEqual(result["position_value"], "51000")
        self.assertEqual(result["unrealized_pnl"], "1000")

    def test_short_upl_is_signed(self):
        validated, fields = _validate_futures_position_pnl_payload(
            {
                "side": "SHORT",
                "quantity": "2",
                "contract_size": "0.5",
                "entry_price": "50000",
                "mark_price": "51000",
                "settlement_asset": "USDT",
            }
        )
        self.assertEqual(fields, {})
        result = _futures_position_pnl(validated)
        self.assertEqual(result["unrealized_pnl"], "-1000")

    def test_zero_mark_is_value_error(self):
        validated, fields = _validate_futures_position_pnl_payload(
            {
                "side": "LONG",
                "quantity": "1",
                "contract_size": "1",
                "entry_price": "50000",
                "mark_price": "0",
                "settlement_asset": "USDT",
            }
        )
        self.assertEqual(fields, {})
        with self.assertRaises(ValueError) as ctx:
            _futures_position_pnl(validated)
        self.assertIn("LINEAR_FUTURES_NUMERIC_INVALID", str(ctx.exception))

    def test_non_usdt_settlement_rejected(self):
        validated, fields = _validate_futures_position_pnl_payload(
            {
                "side": "LONG",
                "quantity": "1",
                "contract_size": "1",
                "entry_price": "50000",
                "mark_price": "51000",
                "settlement_asset": "BTC",
            }
        )
        self.assertEqual(fields, {})
        with self.assertRaises(ValueError) as ctx:
            _futures_position_pnl(validated)
        self.assertIn("SETTLEMENT_ASSET_UNSUPPORTED", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
