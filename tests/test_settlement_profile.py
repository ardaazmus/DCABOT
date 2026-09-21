"""F10.4: single settlement authority, USDT-locked (F35)."""
import unittest

from dcabot.application.settlement_profile import (
    SUPPORTED_SETTLEMENT_ASSETS,
    SettlementProfileError,
    require_settlement_asset,
)


class SettlementProfileTests(unittest.TestCase):
    def test_supported_list_is_usdt_only(self):
        self.assertEqual(SUPPORTED_SETTLEMENT_ASSETS, ("USDT",))

    def test_usdt_passes(self):
        self.assertEqual(require_settlement_asset("USDT"), "USDT")

    def test_other_assets_rejected_with_reason(self):
        for asset in ("BTC", "ETH", "USDC", ""):
            with self.subTest(asset=asset):
                with self.assertRaises(SettlementProfileError) as ctx:
                    require_settlement_asset(asset)
                self.assertEqual(ctx.exception.code, "SETTLEMENT_ASSET_UNSUPPORTED")
                self.assertIn("USDT", str(ctx.exception))

    def test_non_string_rejected(self):
        with self.assertRaises(SettlementProfileError):
            require_settlement_asset(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
