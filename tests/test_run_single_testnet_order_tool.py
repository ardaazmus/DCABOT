import importlib.util
import unittest
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "run_single_testnet_order", Path(__file__).resolve().parents[1] / "tools" / "run_single_testnet_order.py"
)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


class FilterProfileExtractionTests(unittest.TestCase):
    def test_extracts_profile_from_real_shaped_filters(self):
        filters = [
            {"filterType": "PRICE_FILTER", "minPrice": "0.01", "maxPrice": "1000000", "tickSize": "0.01"},
            {"filterType": "LOT_SIZE", "minQty": "0.001", "maxQty": "9000", "stepSize": "0.001"},
            {"filterType": "MIN_NOTIONAL", "minNotional": "10.00000000", "applyToMarket": "True"},
        ]

        profile = _MODULE._filter_profile("BTCUSDT", filters)

        self.assertEqual(profile.qty_step, "0.001")
        self.assertEqual(profile.price_tick, "0.01")
        self.assertEqual(profile.min_qty, "0.001")
        self.assertEqual(profile.min_notional, "10.00000000")

    def test_accepts_newer_notional_filter_name(self):
        filters = [
            {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
            {"filterType": "LOT_SIZE", "minQty": "0.001", "stepSize": "0.001"},
            {"filterType": "NOTIONAL", "notional": "5"},
        ]

        profile = _MODULE._filter_profile("BTCUSDT", filters)

        self.assertEqual(profile.min_notional, "5")

    def test_missing_required_filter_fails_closed(self):
        filters = [{"filterType": "PRICE_FILTER", "tickSize": "0.01"}]

        with self.assertRaises(SystemExit):
            _MODULE._filter_profile("BTCUSDT", filters)


if __name__ == "__main__":
    unittest.main()
