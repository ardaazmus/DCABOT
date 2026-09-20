import unittest

from dcabot.application.futures_grid_variant_gate import (
    FuturesGridVariant,
    FuturesGridVariantAdmission,
    FuturesGridVariantGateError,
    assess_futures_grid_variant,
    assess_futures_grid_variant_admission,
)


class FuturesGridVariantBoundaryOracleTests(unittest.TestCase):
    def test_literal_oracle_keeps_both_variants_unsupported_and_blocked(self):
        expected = (
            FuturesGridVariantAdmission(
                variant=FuturesGridVariant.REVERSE_GRID,
                availability="NOT_SUPPORTED",
                admission="BLOCKED",
                order_authority="NONE",
                economic_authority="NONE",
                reason="FUTURES_GRID_VARIANT_NOT_VERIFIED",
            ),
            FuturesGridVariantAdmission(
                variant=FuturesGridVariant.INFINITY_GRID,
                availability="NOT_SUPPORTED",
                admission="BLOCKED",
                order_authority="NONE",
                economic_authority="NONE",
                reason="FUTURES_GRID_VARIANT_NOT_VERIFIED",
            ),
        )

        observed = tuple(
            assess_futures_grid_variant_admission(variant)
            for variant in FuturesGridVariant
        )

        self.assertEqual(observed, expected)

    def test_literal_oracle_preserves_the_underlying_fail_closed_gate(self):
        for variant in FuturesGridVariant:
            with self.subTest(variant=variant):
                gate = assess_futures_grid_variant(variant)
                admission = assess_futures_grid_variant_admission(variant)
                self.assertEqual(
                    (
                        admission.variant,
                        admission.availability,
                        admission.admission,
                        admission.order_authority,
                        admission.economic_authority,
                        admission.reason,
                    ),
                    (
                        gate.variant,
                        "NOT_SUPPORTED",
                        "BLOCKED",
                        "NONE",
                        "NONE",
                        "FUTURES_GRID_VARIANT_NOT_VERIFIED",
                    ),
                )

    def test_literal_oracle_rejects_untyped_values_at_both_seams(self):
        for check in (assess_futures_grid_variant, assess_futures_grid_variant_admission):
            with self.subTest(check=check.__name__):
                with self.assertRaisesRegex(
                    FuturesGridVariantGateError, "FUTURES_GRID_VARIANT_INVALID"
                ):
                    check("REVERSE_GRID")


if __name__ == "__main__":
    unittest.main()
