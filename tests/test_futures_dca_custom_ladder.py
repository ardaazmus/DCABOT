import ast
from dataclasses import replace
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path
import unittest

from dcabot.application.balance_percent_sizing import BalancePercentBudget
from dcabot.application.futures_dca_candidate_acceptance import (
    FuturesDcaCustomCandidateAcceptance,
    assess_futures_dca_custom_candidate_acceptance,
    evaluate_futures_dca_custom_pre_acceptance,
)
from dcabot.application.instrument_filters import InstrumentFilterProfile
from dcabot.application.futures_dca_plan import (
    FuturesDcaCustomCandidateLevel,
    FuturesDcaCustomCandidateProjection,
    FuturesDcaCustomLevelSpec,
    FuturesDcaPlanError,
    bind_futures_dca_custom_candidates,
    project_futures_dca_custom_ladder,
)
from dcabot.application.ladder_conservation import LadderConservation


def quantize_price(value: Decimal, tick: Decimal, *, up: bool) -> Decimal:
    rounding = ROUND_CEILING if up else ROUND_FLOOR
    return (value / tick).to_integral_value(rounding=rounding) * tick


def decimal_text(value: Decimal) -> str:
    result = format(value, "f").rstrip("0").rstrip(".")
    return result or "0"


def quantize_quantity(value: Decimal, step: Decimal) -> Decimal:
    return (value / step).to_integral_value(rounding=ROUND_FLOOR) * step


class FuturesDcaCustomLadderTests(unittest.TestCase):
    def test_quote_custom_acceptance_joins_existing_pre_acceptance_gate(self):
        ladder = project_futures_dca_custom_ladder(
            side="LONG",
            anchor_price="100",
            levels=(
                FuturesDcaCustomLevelSpec(1, "0.10", "20"),
                FuturesDcaCustomLevelSpec(2, "0.20", "30"),
            ),
            price_tick="0.5",
            allocation_unit="QUOTE_NOTIONAL",
            budget="50",
        )
        instrument = InstrumentFilterProfile(
            profile_id="offline-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="5",
        )
        candidate = bind_futures_dca_custom_candidates(ladder, instrument)
        acceptance = assess_futures_dca_custom_candidate_acceptance(candidate)

        result = evaluate_futures_dca_custom_pre_acceptance(
            candidate=candidate,
            acceptance=acceptance,
            eligible_budget=BalancePercentBudget(
                balance_source="PAPER_SETTLED_BALANCE",
                asset="USDT",
                eligible_balance="1000",
                percent="0.1",
                budget="100",
            ),
            quote_asset="USDT",
        )

        self.assertEqual(result.acceptance, acceptance)
        self.assertEqual(
            result.sizing.total_commitment,
            "42",
        )
        self.assertEqual(result.sizing.order_authority, "NONE")

    def test_custom_pre_acceptance_keeps_quote_budget_fail_closed(self):
        ladder = project_futures_dca_custom_ladder(
            side="LONG",
            anchor_price="100",
            levels=(
                FuturesDcaCustomLevelSpec(1, "0.10", "20"),
                FuturesDcaCustomLevelSpec(2, "0.20", "30"),
            ),
            price_tick="0.5",
            allocation_unit="QUOTE_NOTIONAL",
            budget="50",
        )
        instrument = InstrumentFilterProfile(
            profile_id="offline-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="5",
        )
        candidate = bind_futures_dca_custom_candidates(ladder, instrument)
        acceptance = assess_futures_dca_custom_candidate_acceptance(candidate)

        with self.assertRaisesRegex(
            FuturesDcaPlanError, "PRE_ACCEPTANCE_BUDGET_EXCEEDED"
        ):
            evaluate_futures_dca_custom_pre_acceptance(
                candidate=candidate,
                acceptance=acceptance,
                eligible_budget=BalancePercentBudget(
                    balance_source="PAPER_SETTLED_BALANCE",
                    asset="USDT",
                    eligible_balance="1000",
                    percent="0.04",
                    budget="40",
                ),
                quote_asset="USDT",
            )

    def test_base_custom_acceptance_does_not_invent_quote_budget(self):
        ladder = project_futures_dca_custom_ladder(
            side="LONG",
            anchor_price="100",
            levels=(
                FuturesDcaCustomLevelSpec(1, "0.10", "0.2"),
                FuturesDcaCustomLevelSpec(2, "0.20", "0.3"),
            ),
            price_tick="0.5",
            allocation_unit="BASE_QTY",
            budget="0.5",
        )
        instrument = InstrumentFilterProfile(
            profile_id="offline-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="5",
        )
        candidate = bind_futures_dca_custom_candidates(ladder, instrument)
        acceptance = assess_futures_dca_custom_candidate_acceptance(candidate)

        with self.assertRaisesRegex(
            FuturesDcaPlanError,
            "FUTURES_DCA_CUSTOM_PRE_ACCEPTANCE_UNIT_UNSUPPORTED",
        ):
            evaluate_futures_dca_custom_pre_acceptance(
                candidate=candidate,
                acceptance=acceptance,
                eligible_budget=BalancePercentBudget(
                    balance_source="PAPER_SETTLED_BALANCE",
                    asset="USDT",
                    eligible_balance="1000",
                    percent="0.1",
                    budget="100",
                ),
                quote_asset="USDT",
            )

    def test_acceptance_snapshot_freezes_identity_and_has_no_authority(self):
        ladder = project_futures_dca_custom_ladder(
            side="LONG",
            anchor_price="100",
            levels=(FuturesDcaCustomLevelSpec(1, "0.10", "0.15"),),
            price_tick="0.5",
            allocation_unit="BASE_QTY",
            budget="0.2",
        )
        instrument = InstrumentFilterProfile(
            profile_id="offline-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="5",
        )
        candidate = bind_futures_dca_custom_candidates(ladder, instrument)

        result = assess_futures_dca_custom_candidate_acceptance(candidate)
        repeated = assess_futures_dca_custom_candidate_acceptance(candidate)
        changed = assess_futures_dca_custom_candidate_acceptance(
            bind_futures_dca_custom_candidates(
                ladder, replace(instrument, min_notional="6")
            )
        )

        self.assertEqual(
            result,
            FuturesDcaCustomCandidateAcceptance(
                candidate_id=result.candidate_id,
                instrument_profile_id="offline-btcusdt-v1",
                qty_step="0.1",
                price_tick="0.5",
                min_qty="0.1",
                min_notional="5",
                side="LONG",
                allocation_unit="BASE_QTY",
                level_count=1,
                actual_total_allocation="0.1",
                budget="0.2",
                remaining_budget="0.1",
                order_authority="NONE",
            ),
        )
        self.assertEqual(result, repeated)
        self.assertNotEqual(result.candidate_id, changed.candidate_id)

    def test_acceptance_rejects_tampered_candidate_projection(self):
        ladder = project_futures_dca_custom_ladder(
            side="LONG",
            anchor_price="100",
            levels=(FuturesDcaCustomLevelSpec(1, "0.10", "0.15"),),
            price_tick="0.5",
            allocation_unit="BASE_QTY",
            budget="0.2",
        )
        instrument = InstrumentFilterProfile(
            profile_id="offline-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="5",
        )
        candidate = bind_futures_dca_custom_candidates(ladder, instrument)
        tampered = replace(
            candidate,
            levels=(replace(candidate.levels[0], quantity="0.2"),),
        )

        with self.assertRaisesRegex(
            FuturesDcaPlanError, "FUTURES_DCA_CUSTOM_ACCEPTANCE_CONFLICT"
        ):
            assess_futures_dca_custom_candidate_acceptance(tampered)

    def test_acceptance_snapshot_has_no_persistence_or_transport_write_surface(self):
        source_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "dcabot"
            / "application"
            / "futures_dca_candidate_acceptance.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        write_calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr
            in {"commit", "rollback", "execute", "executemany", "post", "put", "delete", "send"}
        }
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }

        self.assertEqual(write_calls, set())
        self.assertNotIn("sqlite3", imported_modules)
        self.assertNotIn("httpx", imported_modules)

    def test_independent_decimal_oracle_matches_base_candidates(self):
        ladder = project_futures_dca_custom_ladder(
            side="LONG",
            anchor_price="100",
            levels=(
                FuturesDcaCustomLevelSpec(1, "0.10", "0.15"),
                FuturesDcaCustomLevelSpec(2, "0.20", "0.25"),
            ),
            price_tick="0.5",
            allocation_unit="BASE_QTY",
            budget="0.4",
        )
        instrument = InstrumentFilterProfile(
            profile_id="offline-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="5",
        )

        result = bind_futures_dca_custom_candidates(ladder, instrument)
        expected = tuple(
            (
                level.price,
                decimal_text(quantize_quantity(Decimal(level.allocation), Decimal("0.1"))),
                decimal_text(
                    quantize_quantity(Decimal(level.allocation), Decimal("0.1"))
                    * Decimal(level.price)
                ),
            )
            for level in ladder.levels
        )

        self.assertEqual(
            tuple(
                (level.price, level.quantity, level.quote_notional)
                for level in result.levels
            ),
            expected,
        )

    def test_independent_decimal_oracle_matches_quote_candidates(self):
        ladder = project_futures_dca_custom_ladder(
            side="LONG",
            anchor_price="100",
            levels=(
                FuturesDcaCustomLevelSpec(1, "0.10", "20"),
                FuturesDcaCustomLevelSpec(2, "0.20", "30"),
            ),
            price_tick="0.5",
            allocation_unit="QUOTE_NOTIONAL",
            budget="50",
        )
        instrument = InstrumentFilterProfile(
            profile_id="offline-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="5",
        )

        result = bind_futures_dca_custom_candidates(ladder, instrument)
        expected = tuple(
            (
                level.price,
                decimal_text(
                    quantize_quantity(
                        Decimal(level.allocation) / Decimal(level.price), Decimal("0.1")
                    )
                ),
                decimal_text(
                    quantize_quantity(
                        Decimal(level.allocation) / Decimal(level.price), Decimal("0.1")
                    )
                    * Decimal(level.price)
                ),
            )
            for level in ladder.levels
        )

        self.assertEqual(
            tuple(
                (level.price, level.quantity, level.quote_notional)
                for level in result.levels
            ),
            expected,
        )

    def test_candidate_binding_has_no_persistence_or_transport_write_surface(self):
        source_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "dcabot"
            / "application"
            / "futures_dca_plan.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        function = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "bind_futures_dca_custom_candidates"
        )
        write_calls = {
            node.func.attr
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr
            in {"commit", "rollback", "execute", "executemany", "post", "put", "delete", "send"}
        }
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }

        self.assertEqual(write_calls, set())
        self.assertNotIn("sqlite3", imported_modules)
        self.assertNotIn("httpx", imported_modules)

    def test_base_allocation_binds_to_post_quantized_candidates(self):
        ladder = project_futures_dca_custom_ladder(
            side="LONG",
            anchor_price="100",
            levels=(
                FuturesDcaCustomLevelSpec(1, "0.10", "0.15"),
                FuturesDcaCustomLevelSpec(2, "0.20", "0.25"),
            ),
            price_tick="0.5",
            allocation_unit="BASE_QTY",
            budget="0.4",
        )
        instrument = InstrumentFilterProfile(
            profile_id="offline-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="5",
        )

        result = bind_futures_dca_custom_candidates(ladder, instrument)

        self.assertEqual(
            result,
            FuturesDcaCustomCandidateProjection(
                ladder=ladder,
                instrument=instrument,
                levels=(
                    FuturesDcaCustomCandidateLevel(
                        index=1,
                        price="90",
                        requested_allocation="0.15",
                        quantity="0.1",
                        actual_allocation="0.1",
                        quote_notional="9",
                    ),
                    FuturesDcaCustomCandidateLevel(
                        index=2,
                        price="80",
                        requested_allocation="0.25",
                        quantity="0.2",
                        actual_allocation="0.2",
                        quote_notional="16",
                    ),
                ),
                conservation=LadderConservation(
                    allocation_unit="BASE_QTY",
                    total_allocated="0.3",
                    budget="0.4",
                    remaining_budget="0.1",
                ),
            ),
        )

    def test_quote_allocation_uses_post_quantization_notional(self):
        ladder = project_futures_dca_custom_ladder(
            side="LONG",
            anchor_price="100",
            levels=(
                FuturesDcaCustomLevelSpec(1, "0.10", "20"),
                FuturesDcaCustomLevelSpec(2, "0.20", "30"),
            ),
            price_tick="0.5",
            allocation_unit="QUOTE_NOTIONAL",
            budget="50",
        )
        instrument = InstrumentFilterProfile(
            profile_id="offline-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="5",
        )

        result = bind_futures_dca_custom_candidates(ladder, instrument)

        self.assertEqual(
            tuple(
                (level.quantity, level.actual_allocation, level.quote_notional)
                for level in result.levels
            ),
            (("0.2", "18", "18"), ("0.3", "24", "24")),
        )
        self.assertEqual(result.conservation.total_allocated, "42")
        self.assertEqual(result.conservation.remaining_budget, "8")

    def test_candidate_binding_fails_closed_for_collapse_minimum_and_tick_mismatch(self):
        collapsed = project_futures_dca_custom_ladder(
            side="LONG",
            anchor_price="100",
            levels=(FuturesDcaCustomLevelSpec(1, "0.10", "1"),),
            price_tick="0.5",
            allocation_unit="QUOTE_NOTIONAL",
            budget="1",
        )
        instrument = InstrumentFilterProfile(
            profile_id="offline-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="5",
        )
        with self.assertRaisesRegex(
            FuturesDcaPlanError, "FUTURES_DCA_CUSTOM_QUANTITY_COLLAPSED"
        ):
            bind_futures_dca_custom_candidates(collapsed, instrument)

        below_minimum = project_futures_dca_custom_ladder(
            side="LONG",
            anchor_price="100",
            levels=(FuturesDcaCustomLevelSpec(1, "0.10", "0.1"),),
            price_tick="0.5",
            allocation_unit="BASE_QTY",
            budget="0.1",
        )
        high_minimum = InstrumentFilterProfile(
            profile_id="offline-btcusdt-v1",
            qty_step="0.1",
            price_tick="0.5",
            min_qty="0.1",
            min_notional="10",
        )
        with self.assertRaisesRegex(
            FuturesDcaPlanError, "ORDER_NOTIONAL_BELOW_MINIMUM"
        ):
            bind_futures_dca_custom_candidates(below_minimum, high_minimum)

        mismatched_tick = InstrumentFilterProfile(
            profile_id="offline-btcusdt-v1",
            qty_step="0.1",
            price_tick="1",
            min_qty="0.1",
            min_notional="5",
        )
        with self.assertRaisesRegex(
            FuturesDcaPlanError, "FUTURES_DCA_CUSTOM_PRICE_TICK_MISMATCH"
        ):
            bind_futures_dca_custom_candidates(below_minimum, mismatched_tick)

    def test_long_custom_levels_match_independent_oracle(self):
        levels = (
            FuturesDcaCustomLevelSpec(1, "0.10", "0.1"),
            FuturesDcaCustomLevelSpec(2, "0.25", "0.2"),
        )
        result = project_futures_dca_custom_ladder(
            side="LONG",
            anchor_price="100",
            levels=levels,
            price_tick="0.5",
            allocation_unit="BASE_QTY",
            budget="0.4",
        )

        anchor = Decimal("100")
        tick = Decimal("0.5")
        expected_prices = tuple(
            decimal_text(quantize_price(anchor * (Decimal("1") - Decimal(deviation)), tick, up=False))
            for deviation in ("0.10", "0.25")
        )
        self.assertEqual(
            tuple((level.price, level.allocation) for level in result.levels),
            ((expected_prices[0], "0.1"), (expected_prices[1], "0.2")),
        )
        self.assertEqual(result.conservation.total_allocated, "0.3")
        self.assertEqual(result.conservation.remaining_budget, "0.1")

    def test_short_custom_quote_allocations_preserve_exact_budget(self):
        result = project_futures_dca_custom_ladder(
            side="SHORT",
            anchor_price="100",
            levels=(
                FuturesDcaCustomLevelSpec(1, "0.10", "10"),
                FuturesDcaCustomLevelSpec(2, "0.25", "20"),
            ),
            price_tick="0.5",
            allocation_unit="QUOTE_NOTIONAL",
            budget="30",
        )

        self.assertEqual(
            tuple((level.price, level.allocation) for level in result.levels),
            (("110", "10"), ("125", "20")),
        )
        self.assertEqual(result.conservation.total_allocated, "30")
        self.assertEqual(result.conservation.remaining_budget, "0")

    def test_custom_ladder_rejects_share_and_non_monotonic_levels(self):
        with self.assertRaisesRegex(FuturesDcaPlanError, "FUTURES_DCA_CUSTOM_UNIT_INVALID"):
            project_futures_dca_custom_ladder(
                side="LONG",
                anchor_price="100",
                levels=(FuturesDcaCustomLevelSpec(1, "0.1", "1"),),
                price_tick="0.1",
                allocation_unit="SHARE",
                budget="1",
            )
        with self.assertRaisesRegex(FuturesDcaPlanError, "FUTURES_DCA_CUSTOM_DEVIATION_INVALID"):
            project_futures_dca_custom_ladder(
                side="LONG",
                anchor_price="100",
                levels=(
                    FuturesDcaCustomLevelSpec(1, "0.2", "1"),
                    FuturesDcaCustomLevelSpec(2, "0.1", "1"),
                ),
                price_tick="0.1",
                allocation_unit="BASE_QTY",
                budget="2",
            )

    def test_custom_ladder_rejects_index_gap_and_budget_overrun(self):
        with self.assertRaisesRegex(FuturesDcaPlanError, "FUTURES_DCA_CUSTOM_INDEX_INVALID"):
            project_futures_dca_custom_ladder(
                side="LONG",
                anchor_price="100",
                levels=(FuturesDcaCustomLevelSpec(2, "0.1", "1"),),
                price_tick="0.1",
                allocation_unit="BASE_QTY",
                budget="2",
            )
        with self.assertRaisesRegex(FuturesDcaPlanError, "LADDER_BUDGET_EXCEEDED"):
            project_futures_dca_custom_ladder(
                side="LONG",
                anchor_price="100",
                levels=(
                    FuturesDcaCustomLevelSpec(1, "0.1", "0.6"),
                    FuturesDcaCustomLevelSpec(2, "0.2", "0.5"),
                ),
                price_tick="0.1",
                allocation_unit="BASE_QTY",
                budget="1",
            )

    def test_empty_custom_ladder_preserves_declared_budget(self):
        result = project_futures_dca_custom_ladder(
            side="LONG",
            anchor_price="100",
            levels=(),
            price_tick="0.1",
            allocation_unit="QUOTE_NOTIONAL",
            budget="10",
        )

        self.assertEqual(result.levels, ())
        self.assertEqual(result.conservation.total_allocated, "0")
        self.assertEqual(result.conservation.remaining_budget, "10")


if __name__ == "__main__":
    unittest.main()
