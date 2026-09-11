import unittest

from dcabot.application.sizing_units import (
    SizingContractError,
    SizingCandidate,
    build_sizing_candidate,
)


class SizingUnitTests(unittest.TestCase):
    def test_base_and_quote_inputs_produce_equal_exact_candidate(self):
        base = build_sizing_candidate(
            sizing_mode="BASE_QTY", amount="0.4", reference_price="250"
        )
        quote = build_sizing_candidate(
            sizing_mode="QUOTE_NOTIONAL", amount="100", reference_price="250"
        )

        self.assertEqual(
            base,
            SizingCandidate(
                sizing_mode="BASE_QTY",
                source_amount="0.4",
                reference_price="250",
                candidate_quantity="0.4",
                candidate_notional="100",
            ),
        )
        self.assertEqual(base.candidate_quantity, quote.candidate_quantity)
        self.assertEqual(base.candidate_notional, quote.candidate_notional)

    def test_sizing_mode_is_not_a_mixed_unit_scalar(self):
        for mode in ("BALANCE_PERCENT", "BASE", "QUOTE"):
            with self.subTest(mode=mode):
                with self.assertRaisesRegex(
                    SizingContractError, "SIZING_MODE_UNSUPPORTED"
                ):
                    build_sizing_candidate(
                        sizing_mode=mode, amount="100", reference_price="250"
                    )

    def test_invalid_amount_or_price_fails_closed(self):
        with self.assertRaisesRegex(SizingContractError, "SIZING_AMOUNT_INVALID"):
            build_sizing_candidate(
                sizing_mode="BASE_QTY", amount="0", reference_price="250"
            )
        with self.assertRaisesRegex(SizingContractError, "SIZING_PRICE_INVALID"):
            build_sizing_candidate(
                sizing_mode="QUOTE_NOTIONAL", amount="100", reference_price="0"
            )


if __name__ == "__main__":
    unittest.main()
