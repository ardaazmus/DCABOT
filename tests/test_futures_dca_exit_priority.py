import ast
from pathlib import Path
import unittest

from dcabot.application.futures_dca_exit_priority import (
    FuturesDcaExitDecision,
    FuturesDcaExitPriorityError,
    FuturesDcaExitTrigger,
    assess_futures_dca_exit_priority,
)


class FuturesDcaExitPriorityTests(unittest.TestCase):
    def test_empty_trigger_set_is_a_noop(self):
        result = assess_futures_dca_exit_priority(())

        self.assertEqual(
            (result.selected_trigger, result.suppressed_triggers, result.decision, result.reason),
            (None, (), FuturesDcaExitDecision.NO_TRIGGER, "NO_EXIT_TRIGGER"),
        )

    def test_breakeven_alone_is_stop_adjustment_not_close(self):
        result = assess_futures_dca_exit_priority(("BREAKEVEN_ADJUSTMENT",))

        self.assertEqual(
            (result.selected_trigger, result.decision, result.reason),
            (FuturesDcaExitTrigger.BREAKEVEN_ADJUSTMENT, FuturesDcaExitDecision.ADJUST_STOP, "BREAKEVEN_ADJUSTMENT_ONLY"),
        )

    def test_take_profit_is_a_close_decision(self):
        result = assess_futures_dca_exit_priority((FuturesDcaExitTrigger.TAKE_PROFIT,))

        self.assertEqual(
            (result.selected_trigger, result.decision),
            (FuturesDcaExitTrigger.TAKE_PROFIT, FuturesDcaExitDecision.CLOSE),
        )

    def test_stop_loss_has_priority_over_every_other_trigger(self):
        result = assess_futures_dca_exit_priority(
            (
                FuturesDcaExitTrigger.BREAKEVEN_ADJUSTMENT,
                FuturesDcaExitTrigger.TAKE_PROFIT,
                FuturesDcaExitTrigger.TRAILING_STOP,
                FuturesDcaExitTrigger.STOP_LOSS,
            )
        )

        self.assertEqual(result.selected_trigger, FuturesDcaExitTrigger.STOP_LOSS)
        self.assertEqual(
            result.suppressed_triggers,
            (
                FuturesDcaExitTrigger.TRAILING_STOP,
                FuturesDcaExitTrigger.TAKE_PROFIT,
                FuturesDcaExitTrigger.BREAKEVEN_ADJUSTMENT,
            ),
        )

    def test_trailing_stop_has_priority_over_tp_and_breakeven(self):
        result = assess_futures_dca_exit_priority(
            (FuturesDcaExitTrigger.BREAKEVEN_ADJUSTMENT, "TAKE_PROFIT", "TRAILING_STOP")
        )

        self.assertEqual(
            (result.selected_trigger, result.suppressed_triggers),
            (
                FuturesDcaExitTrigger.TRAILING_STOP,
                (FuturesDcaExitTrigger.TAKE_PROFIT, FuturesDcaExitTrigger.BREAKEVEN_ADJUSTMENT),
            ),
        )

    def test_result_is_independent_of_input_order(self):
        first = assess_futures_dca_exit_priority(("TAKE_PROFIT", "STOP_LOSS"))
        second = assess_futures_dca_exit_priority(("STOP_LOSS", "TAKE_PROFIT"))

        self.assertEqual(first, second)

    def test_duplicate_trigger_is_rejected(self):
        with self.assertRaisesRegex(FuturesDcaExitPriorityError, "TRIGGER_DUPLICATE"):
            assess_futures_dca_exit_priority(("TAKE_PROFIT", "TAKE_PROFIT"))

    def test_mutable_or_unknown_input_is_rejected(self):
        with self.assertRaisesRegex(FuturesDcaExitPriorityError, "INPUT_INVALID"):
            assess_futures_dca_exit_priority(["TAKE_PROFIT"])
        with self.assertRaisesRegex(FuturesDcaExitPriorityError, "TRIGGER_INVALID"):
            assess_futures_dca_exit_priority(("UNKNOWN",))

    def test_source_has_no_persistence_or_transport_writes(self):
        source_path = (
            Path(__file__).parents[1]
            / "src"
            / "dcabot"
            / "application"
            / "futures_dca_exit_priority.py"
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
