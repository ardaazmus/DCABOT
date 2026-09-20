import ast
from pathlib import Path
import unittest

from dcabot.application.futures_dca_stop_contract import (
    FuturesDcaStopContractError,
    FuturesDcaStopReason,
    FuturesDcaStopRequest,
    FuturesDcaStopStatus,
    assess_futures_dca_stop,
)


class FuturesDcaStopContractTests(unittest.TestCase):
    def test_continue_keeps_unconsumed_ladder_available(self):
        result = assess_futures_dca_stop(
            completed_dca_count=1,
            max_dca_count=3,
            ladder_level_count=5,
        )

        self.assertEqual(result.status, FuturesDcaStopStatus.CONTINUE)
        self.assertIsNone(result.reason)
        self.assertEqual(result.order_authority, "NONE")

    def test_max_dca_stops_before_remaining_ladder_levels(self):
        result = assess_futures_dca_stop(
            completed_dca_count=3,
            max_dca_count=3,
            ladder_level_count=5,
        )

        self.assertEqual(result.status, FuturesDcaStopStatus.STOP)
        self.assertEqual(result.reason, FuturesDcaStopReason.MAX_DCA_REACHED)

    def test_full_ladder_is_exhausted_and_not_recovery(self):
        result = assess_futures_dca_stop(
            completed_dca_count=5,
            max_dca_count=5,
            ladder_level_count=5,
        )

        self.assertEqual(result.status, FuturesDcaStopStatus.EXHAUSTED)
        self.assertEqual(result.reason, FuturesDcaStopReason.LADDER_EXHAUSTED)

    def test_explicit_stop_reason_remains_separate_from_exhaustion(self):
        result = assess_futures_dca_stop(
            completed_dca_count=1,
            max_dca_count=3,
            ladder_level_count=5,
            stop_request=FuturesDcaStopRequest(FuturesDcaStopReason.STOP_LOSS),
        )

        self.assertEqual(result.status, FuturesDcaStopStatus.STOP)
        self.assertEqual(result.reason, FuturesDcaStopReason.STOP_LOSS)

    def test_invalid_counts_and_internal_reasons_fail_closed(self):
        cases = (
            {"completed_dca_count": -1, "max_dca_count": 3, "ladder_level_count": 5},
            {"completed_dca_count": 1, "max_dca_count": 0, "ladder_level_count": 5},
            {"completed_dca_count": 1, "max_dca_count": 6, "ladder_level_count": 5},
            {"completed_dca_count": 6, "max_dca_count": 5, "ladder_level_count": 5},
        )
        for values in cases:
            with self.subTest(values=values), self.assertRaises(
                FuturesDcaStopContractError
            ):
                assess_futures_dca_stop(**values)

        with self.assertRaisesRegex(
            FuturesDcaStopContractError, "FUTURES_DCA_STOP_REQUEST_REASON_INVALID"
        ):
            FuturesDcaStopRequest(FuturesDcaStopReason.MAX_DCA_REACHED)

    def test_source_has_no_persistence_or_transport_writes(self):
        source_path = (
            Path(__file__).parents[1]
            / "src"
            / "dcabot"
            / "application"
            / "futures_dca_stop_contract.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        forbidden_calls = {
            "commit",
            "execute",
            "post",
            "put",
            "delete",
            "send",
            "request",
        }
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue(calls.isdisjoint(forbidden_calls))


if __name__ == "__main__":
    unittest.main()
