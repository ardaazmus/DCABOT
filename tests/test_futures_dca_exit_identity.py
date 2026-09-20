import ast
from pathlib import Path
import unittest

from dcabot.application.futures_dca_exit_candidate import FuturesDcaExitCandidate
from dcabot.application.futures_dca_exit_identity import (
    FuturesDcaExitCandidateIdentity,
    FuturesDcaExitIdentityError,
    FuturesDcaLateFillObservation,
    identify_futures_dca_exit_candidate,
    observe_futures_dca_late_fill,
)
from dcabot.application.futures_dca_exit_priority import FuturesDcaExitTrigger


def candidate():
    return FuturesDcaExitCandidate(
        selected_trigger=FuturesDcaExitTrigger.TAKE_PROFIT,
        trigger_price="100.495",
        requested_qty="0.06",
        remaining_capacity="0.01",
    )


def identity(*, observed_at_ms=100):
    return identify_futures_dca_exit_candidate(
        candidate(), open_qty="0.12", candidate_observed_at_ms=observed_at_ms
    )


class FuturesDcaExitIdentityTests(unittest.TestCase):
    def test_candidate_identity_is_deterministic_and_snapshot_bound(self):
        first = identity()
        second = identity()
        later = identity(observed_at_ms=101)

        self.assertEqual(first, second)
        self.assertEqual(len(first.candidate_identity_sha256), 64)
        self.assertNotEqual(first.candidate_identity_sha256, later.candidate_identity_sha256)
        self.assertEqual(first.order_authority, "NONE")

    def test_identity_snapshot_keeps_candidate_fields_and_rejects_tamper(self):
        result = identity()
        self.assertEqual(
            (
                result.selected_trigger,
                result.trigger_price,
                result.requested_qty,
                result.remaining_capacity,
                result.open_qty,
            ),
            (FuturesDcaExitTrigger.TAKE_PROFIT, "100.495", "0.06", "0.01", "0.12"),
        )
        with self.assertRaisesRegex(
            FuturesDcaExitIdentityError, "IDENTITY_TAMPERED"
        ):
            FuturesDcaExitCandidateIdentity(
                selected_trigger="TAKE_PROFIT",
                trigger_price="100.495",
                requested_qty="0.06",
                remaining_capacity="0.01",
                open_qty="0.12",
                candidate_observed_at_ms=100,
                candidate_identity_sha256="0" * 64,
            )

    def test_zero_remaining_capacity_is_valid_for_full_close_candidate(self):
        full_close = FuturesDcaExitCandidate(
            selected_trigger=FuturesDcaExitTrigger.STOP_LOSS,
            trigger_price="99",
            requested_qty="0.12",
            remaining_capacity="0",
        )

        result = identify_futures_dca_exit_candidate(
            full_close, open_qty="0.12", candidate_observed_at_ms=100
        )

        self.assertEqual(result.remaining_capacity, "0")

    def test_late_fill_is_observation_only_and_keeps_candidate_identity(self):
        observation = observe_futures_dca_late_fill(
            identity(),
            fill_event_id="fill-event-1",
            filled_qty="0.04",
            fill_price="100.4",
            observed_at_ms=101,
        )

        self.assertEqual(
            observation,
            FuturesDcaLateFillObservation(
                candidate_identity_sha256=identity().candidate_identity_sha256,
                fill_event_id="fill-event-1",
                filled_qty="0.04",
                fill_price="100.4",
                observed_at_ms=101,
            ),
        )
        self.assertFalse(hasattr(observation, "execution_order_id"))
        self.assertEqual(observation.order_authority, "NONE")

    def test_late_fill_must_be_ordered_and_within_candidate_quantity(self):
        for kwargs, code in (
            ({"observed_at_ms": 99, "filled_qty": "0.04"}, "OUT_OF_ORDER"),
            ({"observed_at_ms": 101, "filled_qty": "0.07"}, "OVER_REQUESTED"),
        ):
            with self.subTest(code=code), self.assertRaisesRegex(
                FuturesDcaExitIdentityError, code
            ):
                observe_futures_dca_late_fill(
                    identity(),
                    fill_event_id="fill-event-1",
                    filled_qty=kwargs["filled_qty"],
                    fill_price="100.4",
                    observed_at_ms=kwargs["observed_at_ms"],
                )

    def test_invalid_candidate_and_late_fill_inputs_fail_closed(self):
        with self.assertRaisesRegex(
            FuturesDcaExitIdentityError, "CANDIDATE_INVALID"
        ):
            identify_futures_dca_exit_candidate(
                object(), open_qty="0.12", candidate_observed_at_ms=100
            )
        with self.assertRaisesRegex(
            FuturesDcaExitIdentityError, "LATE_FILL_EVENT_INVALID"
        ):
            observe_futures_dca_late_fill(
                identity(),
                fill_event_id="bad event",
                filled_qty="0.04",
                fill_price="100.4",
                observed_at_ms=101,
            )
        with self.assertRaisesRegex(
            FuturesDcaExitIdentityError, "LATE_FILL_NUMERIC_INVALID"
        ):
            observe_futures_dca_late_fill(
                identity(),
                fill_event_id="fill-event-1",
                filled_qty="bad",
                fill_price="100.4",
                observed_at_ms=101,
            )

    def test_source_has_no_persistence_or_transport_writes(self):
        source_path = (
            Path(__file__).parents[1]
            / "src"
            / "dcabot"
            / "application"
            / "futures_dca_exit_identity.py"
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
