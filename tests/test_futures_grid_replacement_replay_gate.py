import unittest

from dcabot.application.futures_grid_replacement_replay_gate import (
    FuturesGridLifecycleBoundary,
    FuturesGridLifecycleGateError,
    assess_futures_grid_lifecycle_boundary,
)


class FuturesGridReplacementReplayGateTests(unittest.TestCase):
    def test_each_boundary_is_blocked_with_explicit_contract_checklist(self):
        for boundary in FuturesGridLifecycleBoundary:
            with self.subTest(boundary=boundary):
                result = assess_futures_grid_lifecycle_boundary(boundary)
                self.assertEqual(
                    (result.boundary, result.decision, result.order_authority),
                    (boundary, "BLOCKED_CONTRACT_REQUIRED", "NONE"),
                )
                self.assertTrue(result.required_contracts)
                self.assertEqual(
                    result.reason, "FUTURES_GRID_LIFECYCLE_CONTRACT_NOT_VERIFIED"
                )

    def test_untyped_boundary_fails_closed(self):
        with self.assertRaisesRegex(
            FuturesGridLifecycleGateError,
            "FUTURES_GRID_LIFECYCLE_BOUNDARY_INVALID",
        ):
            assess_futures_grid_lifecycle_boundary("REPLAY")

    def test_gate_has_no_order_or_state_authority(self):
        result = assess_futures_grid_lifecycle_boundary(
            FuturesGridLifecycleBoundary.CANCEL_REPLACE
        )

        for field in (
            "order_id",
            "replacement_id",
            "candidate_levels",
            "position",
            "store",
        ):
            self.assertFalse(hasattr(result, field))


if __name__ == "__main__":
    unittest.main()
