import unittest

from dcabot.application.futures_dca_plan import FuturesDcaProfile


class FuturesDcaProfileScopeGateTests(unittest.TestCase):
    def test_profile_does_not_claim_symbol_or_revision_authority(self):
        profile = FuturesDcaProfile()

        self.assertFalse(hasattr(profile, "symbol"))
        self.assertFalse(hasattr(profile, "effective_time_us"))
        self.assertFalse(hasattr(profile, "profile_revision_id"))
        self.assertEqual(
            (profile.venue, profile.product_family, profile.margin_mode),
            ("BINANCE", "USD_M", "ISOLATED"),
        )


if __name__ == "__main__":
    unittest.main()
