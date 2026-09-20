import unittest

from dcabot.application.futures_grid_local_policy import (
    FuturesGridLocalLifecyclePolicy,
    declare_futures_grid_local_lifecycle_policy,
)


class FuturesGridLocalPolicyTests(unittest.TestCase):
    def test_declares_explicit_local_policy_without_authority(self):
        self.assertEqual(
            declare_futures_grid_local_lifecycle_policy(),
            FuturesGridLocalLifecyclePolicy(
                scope="DCABOT_OFFLINE_SIMULATION_ONLY",
                late_fill_authority="FILL_WINS_OVER_CANCEL",
                replacement_admission="CANCEL_ACK_REQUIRED",
                reserve_release="TERMINAL_EXCHANGE_EVENT",
                duplicate_trade="IGNORE_EXACT_DUPLICATE",
                unknown_or_conflict="QUARANTINE_FAIL_CLOSED",
                replay="DETERMINISTIC_REQUIRED",
                order_authority="NONE",
                economic_authority="NONE",
                persistence_authority="NONE",
                venue_authority="NONE",
            ),
        )

    def test_policy_is_not_vendor_or_order_authority(self):
        result = declare_futures_grid_local_lifecycle_policy()

        self.assertEqual(result.scope, "DCABOT_OFFLINE_SIMULATION_ONLY")
        for field in (
            "order_id",
            "replacement_id",
            "candidate_levels",
            "state",
            "store",
            "venue",
        ):
            self.assertFalse(hasattr(result, field))


if __name__ == "__main__":
    unittest.main()
