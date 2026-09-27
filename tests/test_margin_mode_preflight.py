"""Faz 17 G.1-motor (RG-06): margin-mode pre-flight read-change-read state
machine, LOCAL/fake-seam only (no live venue). Covers the no-op-if-already
path, the change-then-confirm path, the -4046..-4051 error map, and the
same-mode race on -4046.
"""
import unittest

from dcabot.application.margin_mode_preflight import (
    MarginModePreflightError,
    VenueMarginTypeError,
    run_margin_mode_preflight,
)


class FakeVenue:
    def __init__(self, initial_mode: str, *, set_error: VenueMarginTypeError | None = None):
        self.mode = initial_mode
        self.set_error = set_error
        self.set_calls: list[tuple[str, str]] = []

    def read_margin_type(self, symbol: str) -> str:
        return self.mode

    def set_margin_type(self, symbol: str, mode: str) -> None:
        self.set_calls.append((symbol, mode))
        if self.set_error is not None:
            raise self.set_error
        self.mode = mode


class NoOpWhenAlreadySetTests(unittest.TestCase):
    def test_already_in_requested_mode_never_calls_set(self):
        venue = FakeVenue("ISOLATED")
        result = run_margin_mode_preflight(venue, symbol="BTCUSDT", requested_mode="ISOLATED")
        self.assertFalse(result.changed)
        self.assertEqual(result.confirmed_mode, "ISOLATED")
        self.assertEqual(venue.set_calls, [])


class ChangeThenConfirmTests(unittest.TestCase):
    def test_change_is_applied_and_confirmed(self):
        venue = FakeVenue("CROSS")
        result = run_margin_mode_preflight(venue, symbol="BTCUSDT", requested_mode="ISOLATED")
        self.assertTrue(result.changed)
        self.assertEqual(result.previous_mode, "CROSS")
        self.assertEqual(result.confirmed_mode, "ISOLATED")
        self.assertEqual(venue.set_calls, [("BTCUSDT", "ISOLATED")])

    def test_confirmation_mismatch_after_change_fails_closed(self):
        class LyingVenue(FakeVenue):
            def set_margin_type(self, symbol, mode):
                self.set_calls.append((symbol, mode))
                # Claims success but never actually changes -- must be caught
                # by the post-change read, not assumed from a clean call.

        venue = LyingVenue("CROSS")
        with self.assertRaises(MarginModePreflightError) as ctx:
            run_margin_mode_preflight(venue, symbol="BTCUSDT", requested_mode="ISOLATED")
        self.assertEqual(ctx.exception.code, "MARGIN_TYPE_CONFIRMATION_MISMATCH")


class VenueErrorMapTests(unittest.TestCase):
    def test_open_orders_error_maps_to_domain_code(self):
        venue = FakeVenue("CROSS", set_error=VenueMarginTypeError(-4047, "open orders"))
        with self.assertRaises(MarginModePreflightError) as ctx:
            run_margin_mode_preflight(venue, symbol="BTCUSDT", requested_mode="ISOLATED")
        self.assertEqual(ctx.exception.code, "MARGIN_TYPE_OPEN_ORDERS")

    def test_open_position_error_maps_to_domain_code(self):
        venue = FakeVenue("CROSS", set_error=VenueMarginTypeError(-4048))
        with self.assertRaises(MarginModePreflightError) as ctx:
            run_margin_mode_preflight(venue, symbol="BTCUSDT", requested_mode="ISOLATED")
        self.assertEqual(ctx.exception.code, "MARGIN_TYPE_OPEN_POSITION")

    def test_insufficient_balance_errors_map_to_the_same_domain_code(self):
        for code in (-4050, -4051):
            venue = FakeVenue("CROSS", set_error=VenueMarginTypeError(code))
            with self.assertRaises(MarginModePreflightError) as ctx:
                run_margin_mode_preflight(venue, symbol="BTCUSDT", requested_mode="ISOLATED")
            self.assertEqual(ctx.exception.code, "MARGIN_TYPE_INSUFFICIENT_BALANCE")

    def test_unknown_error_code_fails_closed_with_its_own_code(self):
        venue = FakeVenue("CROSS", set_error=VenueMarginTypeError(-9999))
        with self.assertRaises(MarginModePreflightError) as ctx:
            run_margin_mode_preflight(venue, symbol="BTCUSDT", requested_mode="ISOLATED")
        self.assertEqual(ctx.exception.code, "MARGIN_TYPE_UNKNOWN_VENUE_ERROR")

    def test_race_already_set_by_another_actor_is_reconciled_by_reread(self):
        venue = FakeVenue("CROSS", set_error=VenueMarginTypeError(-4046, "already set"))

        def read_after_race(symbol: str) -> str:
            return "ISOLATED"

        venue.read_margin_type = read_after_race  # simulate the race landing first
        result = run_margin_mode_preflight(venue, symbol="BTCUSDT", requested_mode="ISOLATED")
        self.assertFalse(result.changed)
        self.assertEqual(result.confirmed_mode, "ISOLATED")

    def test_race_4046_but_reread_disagrees_still_fails_closed(self):
        venue = FakeVenue("CROSS", set_error=VenueMarginTypeError(-4046, "already set"))
        # read_margin_type still returns "CROSS" (the -4046 claim doesn't hold up).
        with self.assertRaises(MarginModePreflightError) as ctx:
            run_margin_mode_preflight(venue, symbol="BTCUSDT", requested_mode="ISOLATED")
        self.assertEqual(ctx.exception.code, "MARGIN_TYPE_ALREADY_SET")


class InputValidationTests(unittest.TestCase):
    def test_invalid_requested_mode_is_rejected(self):
        venue = FakeVenue("ISOLATED")
        with self.assertRaises(MarginModePreflightError):
            run_margin_mode_preflight(venue, symbol="BTCUSDT", requested_mode="SPOT")

    def test_invalid_venue_response_is_rejected(self):
        venue = FakeVenue("SPOT")  # type: ignore[arg-type]
        with self.assertRaises(MarginModePreflightError) as ctx:
            run_margin_mode_preflight(venue, symbol="BTCUSDT", requested_mode="ISOLATED")
        self.assertEqual(ctx.exception.code, "MARGIN_TYPE_VENUE_RESPONSE_INVALID")


if __name__ == "__main__":
    unittest.main()
