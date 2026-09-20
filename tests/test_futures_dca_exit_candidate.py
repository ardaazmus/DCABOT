import ast
from fractions import Fraction
from pathlib import Path
import unittest

from dcabot.application.futures_dca_exit_candidate import (
    FuturesDcaExitCandidate,
    FuturesDcaExitCandidateError,
    bind_futures_dca_exit_candidate,
)
from dcabot.application.futures_dca_exit_priority import (
    assess_futures_dca_exit_priority,
)
from dcabot.application.futures_dca_fill_projection import (
    FuturesDcaFill,
    project_futures_dca_fills,
)
from dcabot.application.futures_dca_plan import project_futures_dca_plan


def plan():
    return project_futures_dca_plan(
        side="LONG",
        anchor_price="100",
        base_amount="10",
        base_sizing="QUOTE_NOTIONAL",
        safety_amount="2",
        safety_sizing="QUOTE_NOTIONAL",
        safety_count=2,
        deviation="0.01",
        step_multiplier="2",
        volume_multiplier="2",
        price_tick="0.001",
        quantity_step="0.0001",
    )


def fills():
    projection_plan = plan()
    return project_futures_dca_fills(
        projection_plan,
        (
            FuturesDcaFill("base", 0, "0.1", "100"),
            FuturesDcaFill("s1", 1, "0.02", "97"),
        ),
    )


class FuturesDcaExitCandidateTests(unittest.TestCase):
    def test_close_trigger_binds_exact_candidate_and_free_capacity(self):
        result = bind_futures_dca_exit_candidate(
            fills(),
            assess_futures_dca_exit_priority(("TAKE_PROFIT",)),
            trigger_price="100.495",
            requested_qty="0.06",
            accepted_exit_fills=("0.02",),
            committed_exit_qty=("0.03",),
        )

        self.assertEqual(
            result,
            FuturesDcaExitCandidate(
                selected_trigger="TAKE_PROFIT",
                trigger_price="100.495",
                requested_qty="0.06",
                remaining_capacity="0.01",
            ),
        )

    def test_stop_loss_and_trailing_stop_are_close_candidates(self):
        for trigger in ("STOP_LOSS", "TRAILING_STOP"):
            with self.subTest(trigger=trigger):
                result = bind_futures_dca_exit_candidate(
                    fills(),
                    assess_futures_dca_exit_priority((trigger,)),
                    trigger_price="99",
                    requested_qty="0.04",
                    accepted_exit_fills=(),
                    committed_exit_qty=(),
                )
                self.assertEqual(result.selected_trigger.value, trigger)
                self.assertEqual(result.remaining_capacity, "0.08")

    def test_breakeven_adjustment_and_no_trigger_cannot_close(self):
        for priority in (
            assess_futures_dca_exit_priority(("BREAKEVEN_ADJUSTMENT",)),
            assess_futures_dca_exit_priority(()),
        ):
            with self.subTest(priority=priority), self.assertRaisesRegex(
                FuturesDcaExitCandidateError, "NO_CLOSE_TRIGGER"
            ):
                bind_futures_dca_exit_candidate(
                    fills(),
                    priority,
                    trigger_price="100",
                    requested_qty="0.04",
                    accepted_exit_fills=(),
                    committed_exit_qty=(),
                )

    def test_empty_position_cannot_create_candidate(self):
        empty = project_futures_dca_fills(plan(), ())
        with self.assertRaisesRegex(
            FuturesDcaExitCandidateError, "POSITION_EMPTY"
        ):
            bind_futures_dca_exit_candidate(
                empty,
                assess_futures_dca_exit_priority(("TAKE_PROFIT",)),
                trigger_price="100",
                requested_qty="0.04",
                accepted_exit_fills=(),
                committed_exit_qty=(),
            )

    def test_candidate_rejects_overclose_and_off_grid_price(self):
        with self.assertRaisesRegex(
            FuturesDcaExitCandidateError, "EXIT_CAPACITY_EXCEEDED"
        ):
            bind_futures_dca_exit_candidate(
                fills(),
                assess_futures_dca_exit_priority(("TAKE_PROFIT",)),
                trigger_price="100.495",
                requested_qty="0.11",
                accepted_exit_fills=("0.02",),
                committed_exit_qty=(),
            )
        with self.assertRaisesRegex(
            FuturesDcaExitCandidateError, "CANDIDATE_OFF_GRID"
        ):
            bind_futures_dca_exit_candidate(
                fills(),
                assess_futures_dca_exit_priority(("TAKE_PROFIT",)),
                trigger_price="100.0005",
                requested_qty="0.04",
                accepted_exit_fills=(),
                committed_exit_qty=(),
            )

    def test_invalid_inputs_fail_closed(self):
        priority = assess_futures_dca_exit_priority(("TAKE_PROFIT",))
        with self.assertRaisesRegex(
            FuturesDcaExitCandidateError, "NUMERIC_INVALID"
        ):
            bind_futures_dca_exit_candidate(
                fills(),
                priority,
                trigger_price="bad",
                requested_qty="0.04",
                accepted_exit_fills=(),
                committed_exit_qty=(),
            )
        with self.assertRaisesRegex(
            FuturesDcaExitCandidateError, "INPUT_INVALID"
        ):
            bind_futures_dca_exit_candidate(
                fills(),
                priority,
                trigger_price="100",
                requested_qty="0.04",
                accepted_exit_fills=[],
                committed_exit_qty=(),
            )

    def test_result_rejects_order_authority(self):
        with self.assertRaisesRegex(
            FuturesDcaExitCandidateError, "AUTHORITY_INVALID"
        ):
            FuturesDcaExitCandidate(
                selected_trigger="TAKE_PROFIT",
                trigger_price="100",
                requested_qty="0.04",
                remaining_capacity="0.08",
                order_authority="CREATE_ORDER",
            )

    def test_independent_capacity_oracle_matches_projection(self):
        result = bind_futures_dca_exit_candidate(
            fills(),
            assess_futures_dca_exit_priority(("TAKE_PROFIT",)),
            trigger_price="100.495",
            requested_qty="0.06",
            accepted_exit_fills=("0.02",),
            committed_exit_qty=("0.03",),
        )
        expected = Fraction("0.12") - Fraction("0.02") - Fraction("0.03") - Fraction("0.06")
        self.assertEqual(expected, Fraction(result.remaining_capacity))

    def test_source_has_no_persistence_or_transport_writes(self):
        source_path = (
            Path(__file__).parents[1]
            / "src"
            / "dcabot"
            / "application"
            / "futures_dca_exit_candidate.py"
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
