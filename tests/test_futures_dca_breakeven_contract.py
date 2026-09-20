import ast
from pathlib import Path
import unittest

from dcabot.application.futures_dca_breakeven_contract import (
    FuturesDcaBreakevenError,
    FuturesDcaBreakevenStatus,
    FuturesDcaFeeAwareProfile,
    assess_futures_dca_breakeven,
)
from dcabot.application.futures_dca_fill_projection import (
    FuturesDcaFill,
    project_futures_dca_fills,
)
from dcabot.application.futures_dca_plan import project_futures_dca_plan


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


class FuturesDcaBreakevenContractTests(unittest.TestCase):
    def test_without_profile_exposes_only_gross_boundary(self):
        result = assess_futures_dca_breakeven(fills())

        self.assertEqual(
            (result.status, result.gross_breakeven_price, result.fee_aware_breakeven_price, result.reason),
            (FuturesDcaBreakevenStatus.GROSS_ONLY, "99.5", None, "FEE_AWARE_PROFILE_REQUIRED"),
        )

    def test_long_fee_aware_boundary_uses_explicit_entry_fee(self):
        result = assess_futures_dca_breakeven(fills(), fee_profile=profile())

        self.assertEqual(
            (result.status, result.gross_breakeven_price, result.fee_aware_breakeven_price),
            (FuturesDcaBreakevenStatus.FEE_AWARE_READY, "99.5", "100.495"),
        )

    def test_short_fee_aware_boundary_uses_opposite_direction(self):
        result = assess_futures_dca_breakeven(
            fills(side="SHORT"), fee_profile=profile()
        )

        self.assertEqual(result.fee_aware_breakeven_price, "99.495")

    def test_signed_funding_cashflow_is_explicit(self):
        result = assess_futures_dca_breakeven(
            fills(), fee_profile=profile(entry_fee_rate="0", funding_cashflow="-0.12")
        )

        self.assertEqual(result.fee_aware_breakeven_price, "100.5")

    def test_third_fee_asset_is_rejected(self):
        with self.assertRaisesRegex(FuturesDcaBreakevenError, "FEE_ASSET_UNSUPPORTED"):
            FuturesDcaFeeAwareProfile(
                settlement_asset="USDT",
                fee_asset="BNB",
                entry_fee_rate="0",
                exit_fee_rate="0",
                funding_cashflow="0",
                profile_revision="test-fees-v1",
            )

    def test_settlement_asset_mismatch_is_blocked(self):
        result = assess_futures_dca_breakeven(
            fills(), fee_profile=profile(settlement_asset="BUSD")
        )

        self.assertEqual(
            (result.status, result.fee_aware_breakeven_price, result.reason),
            (FuturesDcaBreakevenStatus.BLOCKED, None, "FEE_PROFILE_SETTLEMENT_ASSET_MISMATCH"),
        )

    def test_off_grid_fee_aware_boundary_is_blocked(self):
        result = assess_futures_dca_breakeven(
            fills(), fee_profile=profile(entry_fee_rate="0.001")
        )

        self.assertEqual(
            (result.status, result.fee_aware_breakeven_price, result.reason),
            (FuturesDcaBreakevenStatus.BLOCKED, None, "BREAKEVEN_TARGET_OFF_GRID"),
        )

    def test_profile_requires_explicit_numeric_contract(self):
        with self.assertRaisesRegex(FuturesDcaBreakevenError, "FEE_PROFILE_NUMERIC_INVALID"):
            profile(entry_fee_rate="0.1e-2")

    def test_source_has_no_persistence_or_transport_writes(self):
        source_path = (
            Path(__file__).parents[1]
            / "src"
            / "dcabot"
            / "application"
            / "futures_dca_breakeven_contract.py"
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
