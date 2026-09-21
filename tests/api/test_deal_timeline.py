"""F10.5: deal timeline step/seek over stored history (F40)."""
import json
import tempfile
import unittest
from pathlib import Path

from dcabot.server.api import _deal_create, _deal_append_event, _deal_timeline


def _snapshot():
    root = Path(__file__).resolve().parents[2]
    return json.loads((root / "config/paper.json").read_text(encoding="utf-8"))


class DealTimelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.deals_dir = Path(self.tmp.name) / "deals"
        _deal_create(self.deals_dir, {
            "deal_id": "deal-1", "config_revision_id": "rev-1",
            "config_snapshot": _snapshot(),
        })
        _deal_append_event(self.deals_dir, "deal-1", {
            "event_id": "e-1", "config_revision_id": "rev-1",
            "config_snapshot": _snapshot(), "event": "START", "event_sequence": 1,
        })
        _deal_append_event(self.deals_dir, "deal-1", {
            "event_id": "e-2", "config_revision_id": "rev-1",
            "config_snapshot": _snapshot(), "event": "PAUSE", "event_sequence": 2,
        })

    def tearDown(self):
        self.tmp.cleanup()

    def test_step_zero_is_draft(self):
        frame = _deal_timeline(self.deals_dir, "deal-1", 0)
        self.assertEqual(frame["step"], 0)
        self.assertEqual(frame["of"], 2)
        self.assertEqual(frame["lifecycle"]["status"], "DRAFT")
        self.assertIsNone(frame["event"])

    def test_step_seeks_exact_prefix(self):
        first = _deal_timeline(self.deals_dir, "deal-1", 1)
        self.assertEqual(first["lifecycle"]["status"], "RUNNING")
        self.assertEqual(first["event"]["event"], "START")
        second = _deal_timeline(self.deals_dir, "deal-1", 2)
        self.assertEqual(second["lifecycle"]["status"], "PAUSED")
        self.assertEqual(second["event"]["event"], "PAUSE")

    def test_timeline_does_not_mutate_history(self):
        _deal_timeline(self.deals_dir, "deal-1", 1)
        frame = _deal_timeline(self.deals_dir, "deal-1", 2)
        self.assertEqual(frame["of"], 2)
        self.assertEqual(frame["lifecycle"]["status"], "PAUSED")

    def test_out_of_range_rejected(self):
        with self.assertRaises(ValueError):
            _deal_timeline(self.deals_dir, "deal-1", 3)
        with self.assertRaises(ValueError):
            _deal_timeline(self.deals_dir, "deal-1", -1)

    def test_unknown_deal_rejected(self):
        with self.assertRaises(ValueError):
            _deal_timeline(self.deals_dir, "ghost", 0)


if __name__ == "__main__":
    unittest.main()
