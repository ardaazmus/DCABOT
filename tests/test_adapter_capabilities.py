"""Faz 17 C.4: exchange adapter capability matrisi — hangi borsa/mod hangi
yönü destekliyor. Matris salt-okunur bir sözleşmedir; tüketimi (C.5/P4)
ayrı dilimlerin işidir."""

import dataclasses
import unittest

from dcabot.data_adapters.capabilities import (
    CAPABILITY_MATRIX,
    CapabilityError,
    capability,
    supports,
)
from dcabot.domain.math import Direction


class AdapterCapabilityMatrixTests(unittest.TestCase):
    def test_matrix_lists_exactly_the_three_known_surfaces(self):
        self.assertEqual(
            [(row.venue, row.mode) for row in CAPABILITY_MATRIX],
            [
                ("binance_spot", "public"),
                ("binance_spot", "testnet"),
                ("binance_futures", "testnet_position_risk_readonly"),
            ],
        )

    def test_futures_position_risk_surface_is_read_only_no_direction(self):
        row = capability("binance_futures", "testnet_position_risk_readonly")
        self.assertFalse(row.supports_long)
        self.assertFalse(row.supports_short)

    def test_testnet_spot_supports_long_only(self):
        row = capability("binance_spot", "testnet")
        self.assertTrue(row.supports_long)
        self.assertFalse(row.supports_short)

    def test_public_surface_has_no_order_capability(self):
        row = capability("binance_spot", "public")
        self.assertFalse(row.supports_long)
        self.assertFalse(row.supports_short)

    def test_supports_matches_matrix_flags(self):
        self.assertTrue(supports("binance_spot", "testnet", Direction.LONG))
        self.assertFalse(supports("binance_spot", "testnet", Direction.SHORT))
        self.assertFalse(supports("binance_spot", "public", Direction.LONG))
        self.assertFalse(supports("binance_spot", "public", Direction.SHORT))

    def test_unknown_venue_is_fail_closed(self):
        with self.assertRaises(CapabilityError):
            capability("bybit", "testnet")
        with self.assertRaises(CapabilityError):
            supports("bybit", "testnet", Direction.LONG)

    def test_unknown_mode_is_fail_closed(self):
        with self.assertRaises(CapabilityError):
            capability("binance_spot", "mainnet")
        with self.assertRaises(CapabilityError):
            supports("binance_spot", "mainnet", Direction.LONG)

    def test_non_direction_values_are_rejected(self):
        for bad in ("LONG", "SHORT", 1, -1, True, None):
            with self.assertRaises(CapabilityError, msg=repr(bad)):
                supports("binance_spot", "testnet", bad)

    def test_matrix_is_immutable(self):
        self.assertIsInstance(CAPABILITY_MATRIX, tuple)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            CAPABILITY_MATRIX[0].supports_short = True  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
