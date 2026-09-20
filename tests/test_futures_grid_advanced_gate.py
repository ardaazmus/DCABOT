import unittest

from dcabot.application.futures_grid_advanced_gate import (
    FuturesGridAdvancedGateError,
    FuturesGridAdvancedVariant,
    assess_futures_grid_advanced_variant,
)


class FuturesGridAdvancedGateTests(unittest.TestCase):
    def test_every_advanced_variant_is_explicitly_blocked(self):
        for variant in FuturesGridAdvancedVariant:
            with self.subTest(variant=variant):
                result = assess_futures_grid_advanced_variant(variant)
                self.assertEqual(
                    (result.variant, result.decision, result.order_authority, result.reason),
                    (
                        variant,
                        "BLOCKED_CONTRACT_REQUIRED",
                        "NONE",
                        "FUTURES_GRID_ADVANCED_VARIANT_NOT_VERIFIED",
                    ),
                )

    def test_untyped_variant_fails_closed(self):
        with self.assertRaisesRegex(
            FuturesGridAdvancedGateError, "FUTURES_GRID_ADVANCED_VARIANT_INVALID"
        ):
            assess_futures_grid_advanced_variant("TRAILING_UP")

    def test_gate_has_no_order_or_replacement_authority(self):
        result = assess_futures_grid_advanced_variant(
            FuturesGridAdvancedVariant.REVERSAL
        )

        for field in ("order_id", "replacement_id", "candidate_levels", "store"):
            self.assertFalse(hasattr(result, field))


if __name__ == "__main__":
    unittest.main()
