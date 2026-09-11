import unittest

from dcabot.application.balance_percent_sizing import BalancePercentBudget
from dcabot.application.instrument_filters import InstrumentFilterProfile
from dcabot.application.ladder_binding import LadderBinding, LadderLevelCandidate
from dcabot.application.ladder_conservation import LadderConservation
from dcabot.application.sizing_pre_acceptance import (
    SizingPreAcceptance,
    SizingPreAcceptanceError,
    evaluate_sizing_pre_acceptance,
)
from dcabot.application.sizing_units import SizingCandidate


class SizingPreAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.candidate = SizingCandidate(
            sizing_mode="QUOTE_NOTIONAL",
            source_amount="100",
            reference_price="250",
            candidate_quantity="0.4",
            candidate_notional="100",
        )
        self.ladder = LadderBinding(
            levels=(
                LadderLevelCandidate(1, "90", "0.1", "9"),
                LadderLevelCandidate(2, "80", "0.1", "8"),
            ),
            conservation=LadderConservation(
                allocation_unit="QUOTE_NOTIONAL",
                total_allocated="17",
                budget="20",
                remaining_budget="3",
            ),
        )
        self.profile = InstrumentFilterProfile(
            profile_id="offline-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="10",
        )
        self.budget = BalancePercentBudget(
            balance_source="PAPER_SETTLED_BALANCE",
            asset="USDT",
            eligible_balance="1000",
            percent="0.2",
            budget="200",
        )

    def test_quote_candidate_ladder_and_budget_pass_as_validation_only(self):
        result = evaluate_sizing_pre_acceptance(
            candidate=self.candidate,
            ladder=self.ladder,
            profile=self.profile,
            eligible_budget=self.budget,
            quote_asset="USDT",
        )

        self.assertEqual(
            result,
            SizingPreAcceptance(
                profile_id="offline-btcusdt-v1",
                quote_asset="USDT",
                candidate_notional="100",
                ladder_notional="17",
                eligible_budget="200",
                total_commitment="117",
                order_authority="NONE",
            ),
        )

    def test_combined_commitment_cannot_exceed_eligible_budget(self):
        small_budget = BalancePercentBudget(
            balance_source="PAPER_SETTLED_BALANCE",
            asset="USDT",
            eligible_balance="1000",
            percent="0.1",
            budget="100",
        )
        with self.assertRaisesRegex(
            SizingPreAcceptanceError, "PRE_ACCEPTANCE_BUDGET_EXCEEDED"
        ):
            evaluate_sizing_pre_acceptance(
                candidate=self.candidate,
                ladder=self.ladder,
                profile=self.profile,
                eligible_budget=small_budget,
                quote_asset="USDT",
            )

    def test_cross_unit_or_asset_context_is_rejected(self):
        base_candidate = SizingCandidate(
            sizing_mode="BASE_QTY",
            source_amount="0.4",
            reference_price="250",
            candidate_quantity="0.4",
            candidate_notional="100",
        )
        base_ladder = LadderBinding(
            levels=(
                LadderLevelCandidate(1, "90", "0.1", "0.1"),
                LadderLevelCandidate(2, "80", "0.1", "0.1"),
            ),
            conservation=LadderConservation(
                allocation_unit="BASE_QTY",
                total_allocated="0.2",
                budget="1",
                remaining_budget="0.8",
            ),
        )
        with self.assertRaisesRegex(
            SizingPreAcceptanceError, "PRE_ACCEPTANCE_UNIT_CONFLICT"
        ):
            evaluate_sizing_pre_acceptance(
                candidate=self.candidate,
                ladder=base_ladder,
                profile=self.profile,
                eligible_budget=self.budget,
                quote_asset="USDT",
            )
        with self.assertRaisesRegex(
            SizingPreAcceptanceError, "PRE_ACCEPTANCE_ASSET_CONFLICT"
        ):
            evaluate_sizing_pre_acceptance(
                candidate=self.candidate,
                ladder=self.ladder,
                profile=self.profile,
                eligible_budget=self.budget,
                quote_asset="BTC",
            )

    def test_base_candidate_with_exact_quote_notional_is_accepted(self):
        base_candidate = SizingCandidate(
            sizing_mode="BASE_QTY",
            source_amount="0.4",
            reference_price="250",
            candidate_quantity="0.4",
            candidate_notional="100",
        )

        result = evaluate_sizing_pre_acceptance(
            candidate=base_candidate,
            ladder=self.ladder,
            profile=self.profile,
            eligible_budget=self.budget,
            quote_asset="USDT",
        )

        self.assertEqual(result.candidate_notional, "100")
        self.assertEqual(result.total_commitment, "117")
        self.assertEqual(result.order_authority, "NONE")


if __name__ == "__main__":
    unittest.main()
