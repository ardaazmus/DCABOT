import ast
from fractions import Fraction
from pathlib import Path
import unittest

from dcabot.application.futures_dca_breakeven_contract import (
    FuturesDcaBreakevenError,
    FuturesDcaFeeAwareProfile,
)
from dcabot.application.futures_dca_fee_aware_exit import (
    FuturesDcaFeeAwareExitCandidate,
    bind_futures_dca_fee_aware_exit_candidate,
)
from dcabot.application.futures_dca_fill_projection import (
    FuturesDcaFill,
    project_futures_dca_fills,
)
from dcabot.application.futures_dca_plan import project_futures_dca_plan
from dcabot.application.futures_dca_exit_candidate import (
    FuturesDcaExitCandidateError,
)
from dcabot.application.futures_dca_exit_priority import (
    assess_futures_dca_exit_priority,
)


def plan(*, side="LONG"):
    return project_futures_dca_plan(
        side=side,
        anchor_price="100",
        base_amount="10",
        base_sizing="QUOTE_NOTIONAL",
        safety_amount="2.06" if side == "SHORT" else "2",
        safety_sizing="QUOTE_NOTIONAL",
        safety_count=2,
        deviation="0.01",
        step_multiplier="2",
        volume_multiplier="2",
        price_tick="0.001",
        quantity_step="0.0001",
    )


def fills(*, side="LONG"):
    return project_futures_dca_fills(
        plan(side=side),
        (
            FuturesDcaFill("base", 0, "0.1", "100"),
            FuturesDcaFill("s1", 1, "0.02", "97" if side == "LONG" else "103"),
        ),
    )


def profile(*, settlement_asset="USDT", entry_fee_rate="0.01", exit_fee_rate="0", funding_cashflow="0"):
    return FuturesDcaFeeAwareProfile(
        settlement_asset=settlement_asset,
        fee_asset=settlement_asset,
        entry_fee_rate=entry_fee_rate,
        exit_fee_rate=exit_fee_rate,
        funding_cashflow=funding_cashflow,
        profile_revision="test-fees-v1",
    )


class FuturesDcaFeeAwareExitTests(unittest.TestCase):
    def test_long_fee_aware_boundary_binds_exact_take_profit_candidate(self):
        result = bind_futures_dca_fee_aware_exit_candidate(
            fills(),
            assess_futures_dca_exit_priority(("TAKE_PROFIT",)),
            fee_profile=profile(),
            requested_qty="0.06",
            accepted_exit_fills=("0.02",),
            committed_exit_qty=("0.03",),
        )

        self.assertEqual(
            result,
            FuturesDcaFeeAwareExitCandidate(
                selected_trigger="TAKE_PROFIT",
                trigger_price="100.495",
                requested_qty="0.06",
                remaining_capacity="0.01",
                gross_breakeven_price="99.5",
                fee_aware_breakeven_price="100.495",
                fee_profile_revision="test-fees-v1",
            ),
        )

    def test_independent_capacity_oracle_matches_bound_candidate(self):
        result = bind_futures_dca_fee_aware_exit_candidate(
            fills(),
            assess_futures_dca_exit_priority(("TAKE_PROFIT",)),
            fee_profile=profile(),
            requested_qty="0.06",
            accepted_exit_fills=("0.02",),
            committed_exit_qty=("0.03",),
        )

        expected = Fraction("0.12") - Fraction("0.02") - Fraction("0.03") - Fraction("0.06")
        self.assertEqual(expected, Fraction(result.remaining_capacity))

    def test_short_fee_aware_boundary_binds_opposite_direction(self):
        result = bind_futures_dca_fee_aware_exit_candidate(
            fills(side="SHORT"),
            assess_futures_dca_exit_priority(("TAKE_PROFIT",)),
            fee_profile=profile(),
            requested_qty="0.06",
            accepted_exit_fills=(),
            committed_exit_qty=(),
        )

        self.assertEqual(result.fee_aware_breakeven_price, "99.495")
        self.assertEqual(result.trigger_price, "99.495")

    def test_profile_is_required_for_candidate(self):
        with self.assertRaisesRegex(FuturesDcaBreakevenError, "PROFILE_REQUIRED"):
            bind_futures_dca_fee_aware_exit_candidate(
                fills(),
                assess_futures_dca_exit_priority(("TAKE_PROFIT",)),
                fee_profile=None,
                requested_qty="0.04",
                accepted_exit_fills=(),
                committed_exit_qty=(),
            )

    def test_settlement_mismatch_is_not_bound(self):
        with self.assertRaisesRegex(FuturesDcaBreakevenError, "SETTLEMENT_ASSET_MISMATCH"):
            bind_futures_dca_fee_aware_exit_candidate(
                fills(),
                assess_futures_dca_exit_priority(("TAKE_PROFIT",)),
                fee_profile=profile(settlement_asset="BUSD"),
                requested_qty="0.04",
                accepted_exit_fills=(),
                committed_exit_qty=(),
            )

    def test_off_grid_boundary_is_rejected_without_rounding(self):
        with self.assertRaisesRegex(FuturesDcaBreakevenError, "TARGET_OFF_GRID"):
            bind_futures_dca_fee_aware_exit_candidate(
                fills(),
                assess_futures_dca_exit_priority(("TAKE_PROFIT",)),
                fee_profile=profile(entry_fee_rate="0.001"),
                requested_qty="0.04",
                accepted_exit_fills=(),
                committed_exit_qty=(),
            )

    def test_non_take_profit_trigger_is_not_given_breakeven_price(self):
        for trigger in ("STOP_LOSS", "TRAILING_STOP"):
            with self.subTest(trigger=trigger), self.assertRaisesRegex(
                FuturesDcaExitCandidateError, "UNSUPPORTED"
            ):
                bind_futures_dca_fee_aware_exit_candidate(
                    fills(),
                    assess_futures_dca_exit_priority((trigger,)),
                    fee_profile=profile(),
                    requested_qty="0.04",
                    accepted_exit_fills=(),
                    committed_exit_qty=(),
                )

    def test_overclose_is_rejected_by_shared_capacity_contract(self):
        with self.assertRaisesRegex(FuturesDcaExitCandidateError, "EXIT_CAPACITY_EXCEEDED"):
            bind_futures_dca_fee_aware_exit_candidate(
                fills(),
                assess_futures_dca_exit_priority(("TAKE_PROFIT",)),
                fee_profile=profile(),
                requested_qty="0.13",
                accepted_exit_fills=(),
                committed_exit_qty=(),
            )

    def test_source_has_no_persistence_or_transport_writes(self):
        source_path = (
            Path(__file__).parents[1]
            / "src"
            / "dcabot"
            / "application"
            / "futures_dca_fee_aware_exit.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        forbidden_calls = {"commit", "execute", "post", "put", "delete", "send", "request"}
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue(calls.isdisjoint(forbidden_calls))


if __name__ == "__main__":
    unittest.main()
