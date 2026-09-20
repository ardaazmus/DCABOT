import unittest

from dcabot.application.futures_dca_fill_projection import (
    FuturesDcaFill,
    FuturesDcaFillError,
    project_futures_dca_fills,
)
from dcabot.application.futures_dca_plan import project_futures_dca_plan


def plan():
    return project_futures_dca_plan(
        side="LONG", anchor_price="100", base_amount="10", base_sizing="QUOTE_NOTIONAL",
        safety_amount="2", safety_sizing="QUOTE_NOTIONAL", safety_count=2,
        deviation="0.01", step_multiplier="2", volume_multiplier="2",
        price_tick="0.01", quantity_step="0.0001",
    )


class FuturesDcaFillProjectionTests(unittest.TestCase):
    def test_average_entry_uses_observed_base_and_safety_prices(self):
        result = project_futures_dca_fills(
            plan(),
            (FuturesDcaFill("base", 0, "0.1", "100"), FuturesDcaFill("s1", 1, "0.02", "97")),
        )
        self.assertEqual((result.position_quantity, result.position_notional, result.average_entry), ("0.12", "11.94", "99.5"))
        self.assertEqual((result.completed_safety_count, result.active_pending_levels, result.pending_reserved_quote), (0, (1,), "0.0198"))

    def test_active_limit_and_exact_duplicate_are_bounded_and_idempotent(self):
        fills = (FuturesDcaFill("base", 0, "0.1", "100"), FuturesDcaFill("s1", 1, "0.02", "97"), FuturesDcaFill("s1", 1, "0.02", "97"))
        result = project_futures_dca_fills(plan(), fills, max_active_safety_orders=2)
        self.assertEqual((result.fills, result.active_pending_levels), (fills[:2], (1, 2)))

    def test_non_terminating_average_fails_closed_instead_of_rounding(self):
        with self.assertRaisesRegex(FuturesDcaFillError, "FUTURES_DCA_AVERAGE_NOT_EXACT"):
            project_futures_dca_fills(
                plan(),
                (FuturesDcaFill("base", 0, "0.1", "100"), FuturesDcaFill("s1", 1, "0.0202", "98")),
            )

    def test_safety_cannot_precede_complete_base_or_skip_level(self):
        with self.assertRaisesRegex(FuturesDcaFillError, "FUTURES_DCA_BASE_INCOMPLETE"):
            project_futures_dca_fills(plan(), (FuturesDcaFill("s1", 1, "0.02", "97"),))
        with self.assertRaisesRegex(FuturesDcaFillError, "FUTURES_DCA_SAFETY_SEQUENCE_INVALID"):
            project_futures_dca_fills(plan(), (FuturesDcaFill("base", 0, "0.1", "100"), FuturesDcaFill("s2", 2, "0.0412", "96")))


if __name__ == "__main__":
    unittest.main()
