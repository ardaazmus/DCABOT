import unittest

from dcabot.server.api import (
    _calculate_rebalance_valuation,
    _validate_rebalance_valuation_payload,
)


class RebalanceValuationApiContractTests(unittest.TestCase):
    def test_valid_payload_delegates_to_exact_valuation(self):
        payload = {
            "valuation_asset": "USDT",
            "holdings": [["BTC", "0.01"], ["USDT", "100"]],
            "prices": [["BTC", "50000"]],
        }
        validated, fields = _validate_rebalance_valuation_payload(payload)
        self.assertEqual(fields, {})
        self.assertEqual(
            _calculate_rebalance_valuation(validated),
            {
                "valuation_asset": "USDT",
                "total_equity": "600",
                "positions": [
                    {"asset": "BTC", "qty": "0.01", "price": "50000", "value": "500"},
                    {"asset": "USDT", "qty": "100", "price": "1", "value": "100"},
                ],
            },
        )

    def test_non_string_qty_is_a_field_error(self):
        payload = {
            "valuation_asset": "USDT",
            "holdings": [["BTC", 0.01]],
            "prices": [["BTC", "50000"]],
        }
        validated, fields = _validate_rebalance_valuation_payload(payload)
        self.assertIsNone(validated)
        self.assertIn("holdings", fields)

    def test_missing_keys_are_reported_on_body(self):
        validated, fields = _validate_rebalance_valuation_payload(
            {"valuation_asset": "USDT"}
        )
        self.assertIsNone(validated)
        self.assertIn("Eksik alanlar", fields["body"])

    def test_unknown_keys_are_rejected(self):
        validated, fields = _validate_rebalance_valuation_payload(
            {
                "valuation_asset": "USDT",
                "holdings": [["USDT", "1"]],
                "prices": [],
                "orders": [],
            }
        )
        self.assertIsNone(validated)
        self.assertIn("Bilinmeyen alanlar", fields["body"])

    def test_holdings_must_be_a_bounded_list(self):
        validated, fields = _validate_rebalance_valuation_payload(
            {"valuation_asset": "USDT", "holdings": "BTC", "prices": []}
        )
        self.assertIsNone(validated)
        self.assertIn("holdings", fields)

    def test_domain_failures_surface_as_value_errors(self):
        payload = {
            "valuation_asset": "USDT",
            "holdings": [["BTC", "0.01"]],
            "prices": [],
        }
        validated, fields = _validate_rebalance_valuation_payload(payload)
        self.assertEqual(fields, {})
        with self.assertRaises(ValueError) as ctx:
            _calculate_rebalance_valuation(validated)
        self.assertIn("REBALANCE_VALUATION_PRICE_MISSING", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
