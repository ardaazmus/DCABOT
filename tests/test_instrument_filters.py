import unittest

from dcabot.application.instrument_filters import (
    InstrumentFilterProfile,
    InstrumentFilterError,
    ValidatedOrderCandidate,
    validate_order_candidate,
)


class InstrumentFilterTests(unittest.TestCase):
    def setUp(self):
        self.profile = InstrumentFilterProfile(
            profile_id="offline-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="10",
        )

    def test_profile_validates_exact_grid_and_minimums(self):
        result = validate_order_candidate(
            self.profile, quantity="0.2", price="100.5"
        )

        self.assertEqual(
            result,
            ValidatedOrderCandidate(
                profile_id="offline-btcusdt-v1",
                quantity="0.2",
                price="100.5",
                notional="20.1",
            ),
        )

    def test_off_grid_or_below_minimum_candidate_is_rejected(self):
        with self.assertRaisesRegex(
            InstrumentFilterError, "ORDER_QUANTITY_OFF_GRID"
        ):
            validate_order_candidate(self.profile, quantity="0.15", price="100")
        with self.assertRaisesRegex(
            InstrumentFilterError, "ORDER_NOTIONAL_BELOW_MINIMUM"
        ):
            validate_order_candidate(self.profile, quantity="0.1", price="50")

    def test_profile_metadata_and_candidate_values_are_exact_strings(self):
        with self.assertRaisesRegex(
            InstrumentFilterError, "FILTER_PROFILE_INVALID"
        ):
            InstrumentFilterProfile(
                profile_id="", qty_step="0.1", price_tick="0.5", min_qty="0.1", min_notional="10"
            )
        with self.assertRaisesRegex(
            InstrumentFilterError, "ORDER_PRICE_INVALID"
        ):
            validate_order_candidate(self.profile, quantity="0.2", price="0")


if __name__ == "__main__":
    unittest.main()
