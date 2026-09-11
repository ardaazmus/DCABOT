import hashlib
import unittest

from dcabot.application.stress_lineage import (
    StressLineage,
    new_stress_lineage,
)


class StressLineageTests(unittest.TestCase):
    def test_stress_result_has_separate_deterministic_identity(self):
        first = new_stress_lineage(
            "result-base-1",
            stress_profile_id="slippage-wide-1",
            stress_profile_hash="a" * 64,
        )
        repeat = new_stress_lineage(
            "result-base-1",
            stress_profile_id="slippage-wide-1",
            stress_profile_hash="a" * 64,
        )
        changed = new_stress_lineage(
            "result-base-1",
            stress_profile_id="slippage-wide-2",
            stress_profile_hash="b" * 64,
        )

        self.assertEqual(first, repeat)
        self.assertNotEqual(first.stress_result_id, first.base_result_id)
        self.assertNotEqual(first.stress_result_id, changed.stress_result_id)
        self.assertEqual(first.label, "STRESS")

    def test_identity_is_independent_of_input_ordering(self):
        lineage = new_stress_lineage(
            "result-base-1",
            stress_profile_id="ohlc-worst-1",
            stress_profile_hash="c" * 64,
        )
        canonical = "stress-lineage-v1|result-base-1|ohlc-worst-1|" + "c" * 64
        expected = "stress-v1:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        self.assertEqual(lineage.stress_result_id, expected)

    def test_invalid_or_colliding_identity_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "STRESS_BASE_RESULT_ID_INVALID"):
            new_stress_lineage(
                "",
                stress_profile_id="profile-1",
                stress_profile_hash="d" * 64,
            )
        with self.assertRaisesRegex(ValueError, "STRESS_PROFILE_HASH_INVALID"):
            new_stress_lineage(
                "result-base-1",
                stress_profile_id="profile-1",
                stress_profile_hash="not-a-hash",
            )
        with self.assertRaisesRegex(ValueError, "STRESS_IDENTITY_CONFLICT"):
            StressLineage(
                base_result_id="result-base-1",
                stress_profile_id="profile-1",
                stress_profile_hash="e" * 64,
                stress_result_id="result-base-1",
            )


if __name__ == "__main__":
    unittest.main()
