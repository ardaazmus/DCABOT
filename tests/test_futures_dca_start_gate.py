import ast
from pathlib import Path
import unittest

from dcabot.application.futures_dca_start_gate import (
    FuturesDcaStartGateError,
    FuturesDcaStartMode,
    FuturesDcaStartStatus,
    FuturesDcaStartEvaluation,
    assess_futures_dca_start,
)
from dcabot.application.signal_readiness import SignalReadiness


def ready_signal(*, event_time_us=1_000):
    return SignalReadiness(
        signal_id="sig-1",
        status="READY",
        event_time_us=event_time_us,
        closed_bar_time_us=event_time_us,
        warmup_bars_observed=5,
        required_warmup_bars=5,
        max_staleness_us=0,
    )


class FuturesDcaStartGateTests(unittest.TestCase):
    def test_immediate_is_eligible_without_order_authority(self):
        result = assess_futures_dca_start(
            mode=FuturesDcaStartMode.IMMEDIATE,
            event_time_us=1_000,
        )

        self.assertEqual(result.status, FuturesDcaStartStatus.ELIGIBLE)
        self.assertEqual(result.reason, "IMMEDIATE_CONDITION_MET")
        self.assertEqual(result.order_authority, "NONE")
        self.assertIsNone(result.signal_id)

    def test_closed_candle_waits_then_accepts_boundary(self):
        waiting = assess_futures_dca_start(
            mode="CLOSED_CANDLE",
            event_time_us=1_001,
            closed_bar_time_us=1_000,
        )
        accepted = assess_futures_dca_start(
            mode="CLOSED_CANDLE",
            event_time_us=1_000,
            closed_bar_time_us=1_000,
        )

        self.assertEqual(waiting.status, FuturesDcaStartStatus.BLOCKED)
        self.assertEqual(waiting.reason, "WAITING_FOR_CLOSED_BAR")
        self.assertEqual(accepted.status, FuturesDcaStartStatus.ELIGIBLE)
        self.assertEqual(accepted.reason, "CLOSED_CANDLE_CONFIRMED")

    def test_signal_delegates_ready_and_nonready_status(self):
        accepted = assess_futures_dca_start(
            mode=FuturesDcaStartMode.SIGNAL,
            event_time_us=1_000,
            signal_readiness=ready_signal(),
        )
        blocked = assess_futures_dca_start(
            mode=FuturesDcaStartMode.SIGNAL,
            event_time_us=1_000,
            signal_readiness=SignalReadiness(
                signal_id="sig-1",
                status="WARMING_UP",
                event_time_us=1_000,
                closed_bar_time_us=1_000,
                warmup_bars_observed=4,
                required_warmup_bars=5,
                max_staleness_us=0,
            ),
        )

        self.assertEqual(accepted.status, FuturesDcaStartStatus.ELIGIBLE)
        self.assertEqual(accepted.signal_id, "sig-1")
        self.assertEqual(blocked.status, FuturesDcaStartStatus.BLOCKED)
        self.assertEqual(blocked.reason, "SIGNAL_WARMING_UP")

    def test_invalid_context_and_source_time_fail_closed(self):
        cases = (
            {"mode": "UNKNOWN", "event_time_us": 1_000},
            {"mode": "IMMEDIATE", "event_time_us": -1},
            {
                "mode": "IMMEDIATE",
                "event_time_us": 1_000,
                "closed_bar_time_us": 1_000,
            },
            {"mode": "CLOSED_CANDLE", "event_time_us": 1_000},
            {"mode": "SIGNAL", "event_time_us": 1_000},
        )
        for values in cases:
            with self.subTest(values=values), self.assertRaises(
                FuturesDcaStartGateError
            ):
                assess_futures_dca_start(**values)

        with self.assertRaisesRegex(
            FuturesDcaStartGateError, "FUTURES_DCA_START_SIGNAL_TIME_CONFLICT"
        ):
            assess_futures_dca_start(
                mode="SIGNAL",
                event_time_us=1_001,
                signal_readiness=ready_signal(),
            )

    def test_evaluation_rejects_authority(self):
        with self.assertRaisesRegex(
            FuturesDcaStartGateError, "FUTURES_DCA_START_ORDER_AUTHORITY_INVALID"
        ):
            FuturesDcaStartEvaluation(
                mode=FuturesDcaStartMode.IMMEDIATE,
                status=FuturesDcaStartStatus.ELIGIBLE,
                event_time_us=1_000,
                reason="IMMEDIATE_CONDITION_MET",
                order_authority="CREATE_ORDER",
            )

    def test_source_has_no_persistence_or_transport_writes(self):
        source_path = (
            Path(__file__).parents[1]
            / "src"
            / "dcabot"
            / "application"
            / "futures_dca_start_gate.py"
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
        imports = {
            node.names[0].name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import) and node.names
        }
        self.assertTrue(imports.isdisjoint({"sqlite3", "httpx", "requests"}))


if __name__ == "__main__":
    unittest.main()
