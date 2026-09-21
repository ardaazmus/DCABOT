"""F10.9: draft-level assembly helper (F29)."""
import unittest
from types import SimpleNamespace

from dcabot.server.api import _draft_level_data


def _loaded():
    return SimpleNamespace(
        metadata=SimpleNamespace(
            dataset_id="binance-btcusdt-1h",
            artifact_sha256="ab" * 32,
        ),
        bars=[
            SimpleNamespace(low="90", high="100"),
            SimpleNamespace(low="95", high="110"),
        ],
    )


class DraftLevelApiTests(unittest.TestCase):
    def test_accepted_bound_to_revision(self):
        data = _draft_level_data(_loaded(), "ab" * 32, "105.5")
        self.assertEqual(data["verdict"], "ACCEPTED")
        self.assertEqual(data["draft_price"], "105.5")
        self.assertEqual(data["dataset_id"], "binance-btcusdt-1h")
        self.assertEqual(data["artifact_sha256"], "ab" * 32)

    def test_rejected_outside_range(self):
        data = _draft_level_data(_loaded(), "ab" * 32, "200")
        self.assertEqual(data["verdict"], "REJECTED")
        self.assertTrue(data["reason"])

    def test_artifact_mismatch_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            _draft_level_data(_loaded(), "cd" * 32, "100")
        self.assertIn("DRAFT_ARTIFACT_MISMATCH", str(ctx.exception))

    def test_non_numeric_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            _draft_level_data(_loaded(), "ab" * 32, "high")
        self.assertIn("DRAFT_PRICE_INVALID", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
