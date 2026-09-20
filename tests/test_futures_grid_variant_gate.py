import unittest

from dcabot.application.futures_grid_variant_gate import (
    FuturesGridVariant,
    FuturesGridVariantAdmission,
    FuturesGridVariantGateError,
    assess_futures_grid_variant,
    assess_futures_grid_variant_admission,
)


class FuturesGridVariantGateTests(unittest.TestCase):
    def test_reverse_and_infinity_are_separate_fail_closed_variants(self):
        for variant in FuturesGridVariant:
            with self.subTest(variant=variant):
                result = assess_futures_grid_variant(variant)
                self.assertEqual(
                    (
                        result.variant,
                        result.decision,
                        result.order_authority,
                        result.economic_authority,
                        result.reason,
                    ),
                    (
                        variant,
                        "BLOCKED_CONTRACT_REQUIRED",
                        "NONE",
                        "NONE",
                        "FUTURES_GRID_VARIANT_NOT_VERIFIED",
                    ),
                )

    def test_untyped_variant_fails_closed(self):
        with self.assertRaisesRegex(
            FuturesGridVariantGateError, "FUTURES_GRID_VARIANT_INVALID"
        ):
            assess_futures_grid_variant("REVERSE_GRID")

    def test_gate_has_no_order_or_state_authority(self):
        result = assess_futures_grid_variant(FuturesGridVariant.INFINITY_GRID)

        for field in (
            "order_id",
            "replacement_id",
            "candidate_levels",
            "position",
            "store",
        ):
            self.assertFalse(hasattr(result, field))

    def test_product_admission_exposes_unverified_variants_as_not_supported(self):
        for variant in FuturesGridVariant:
            with self.subTest(variant=variant):
                self.assertEqual(
                    assess_futures_grid_variant_admission(variant),
                    FuturesGridVariantAdmission(
                        variant=variant,
                        availability="NOT_SUPPORTED",
                        admission="BLOCKED",
                        order_authority="NONE",
                        economic_authority="NONE",
                        reason="FUTURES_GRID_VARIANT_NOT_VERIFIED",
                    ),
                )

    def test_product_admission_rejects_untyped_variant(self):
        with self.assertRaisesRegex(
            FuturesGridVariantGateError, "FUTURES_GRID_VARIANT_INVALID"
        ):
            assess_futures_grid_variant_admission("INFINITY_GRID")

    def test_product_admission_has_no_operational_fields(self):
        result = assess_futures_grid_variant_admission(FuturesGridVariant.REVERSE_GRID)

        for field in (
            "order_id",
            "replacement_id",
            "candidate_levels",
            "position",
            "reserve",
            "store",
        ):
            self.assertFalse(hasattr(result, field))


if __name__ == "__main__":
    unittest.main()
