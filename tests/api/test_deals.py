"""F9.1: deal lifecycle + bulk API over LifecycleStore (F31)."""
import json
import tempfile
import unittest
from pathlib import Path

def _snapshot():
    root = Path(__file__).resolve().parents[2]
    return json.loads((root / "config/paper.json").read_text(encoding="utf-8"))

from dcabot.server.api import (
    _deal_append_event,
    _deal_bulk,
    _deal_create,
    _deal_replay,
    _validate_deal_bulk_payload,
    _validate_deal_create_payload,
    _validate_deal_event_payload,
)


def _create_body(**overrides):
    body = {
        "deal_id": "deal-1",
        "config_revision_id": "rev-1",
        "config_snapshot": _snapshot(),
    }
    body.update(overrides)
    return body


def _event_body(**overrides):
    body = {
        "event_id": "event-1",
        "config_revision_id": "rev-1",
        "config_snapshot": _snapshot(),
        "event": "START",
        "event_sequence": 1,
    }
    body.update(overrides)
    return body


class DealApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.deals_dir = Path(self.tmp.name) / "deals"

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_replay_roundtrip(self):
        validated, fields = _validate_deal_create_payload(_create_body())
        self.assertEqual(fields, {})
        created = _deal_create(self.deals_dir, validated)
        self.assertEqual(created["result"], "CREATED")
        self.assertEqual(created["deal_id"], "deal-1")
        replayed = _deal_replay(self.deals_dir, "deal-1")
        self.assertIsNone(replayed["lifecycle"])
        self.assertEqual(replayed["history"], [])

    def test_create_duplicate(self):
        _deal_create(self.deals_dir, _create_body())
        again = _deal_create(self.deals_dir, _create_body())
        self.assertEqual(again["result"], "DUPLICATE")

    def test_append_start_pause_replay(self):
        _deal_create(self.deals_dir, _create_body())
        validated, fields = _validate_deal_event_payload(_event_body())
        self.assertEqual(fields, {})
        first = _deal_append_event(self.deals_dir, "deal-1", validated)
        self.assertEqual(first["result"], "ACCEPTED")
        self.assertEqual(first["lifecycle"]["status"], "RUNNING")
        second = _deal_append_event(
            self.deals_dir, "deal-1",
            _event_body(event_id="event-2", event="PAUSE", event_sequence=2),
        )
        self.assertEqual(second["lifecycle"]["status"], "PAUSED")
        replayed = _deal_replay(self.deals_dir, "deal-1")
        self.assertEqual(replayed["lifecycle"]["status"], "PAUSED")
        self.assertEqual(len(replayed["history"]), 2)

    def test_invalid_transition_rejected(self):
        _deal_create(self.deals_dir, _create_body())
        with self.assertRaises(ValueError):
            _deal_append_event(
                self.deals_dir, "deal-1",
                _event_body(event="RESUME"),
            )

    def test_bulk_sequential_per_deal_results(self):
        _deal_create(self.deals_dir, _create_body())
        _deal_create(
            self.deals_dir,
            _create_body(deal_id="deal-2", config_revision_id="rev-2"),
        )
        validated, fields = _validate_deal_bulk_payload({
            "actions": [
                {"deal_id": "deal-1", **_event_body(event_id="b-1")},
                {"deal_id": "deal-2", **_event_body(
                    event_id="b-2", config_revision_id="rev-2")},
                {"deal_id": "deal-1", **_event_body(
                    event_id="b-3", event="RESUME", event_sequence=2)},
            ]
        })
        self.assertEqual(fields, {})
        result = _deal_bulk(self.deals_dir, validated)
        outcomes = result["results"]
        self.assertEqual(len(outcomes), 3)
        self.assertEqual(outcomes[0]["result"], "ACCEPTED")
        self.assertEqual(outcomes[1]["result"], "ACCEPTED")
        self.assertIn("error", outcomes[2])
        # non-atomic: the first two actions persisted despite the third failing
        self.assertEqual(
            _deal_replay(self.deals_dir, "deal-1")["lifecycle"]["status"], "RUNNING"
        )
        self.assertEqual(
            _deal_replay(self.deals_dir, "deal-2")["lifecycle"]["status"], "RUNNING"
        )

    def test_bad_event_is_field_error(self):
        validated, fields = _validate_deal_event_payload(_event_body(event="LAUNCH"))
        self.assertIsNone(validated)
        self.assertIn("event", fields)

    def test_non_dict_snapshot_is_field_error(self):
        validated, fields = _validate_deal_create_payload(
            _create_body(config_snapshot=["nope"])
        )
        self.assertIsNone(validated)
        self.assertIn("config_snapshot", fields)

    def test_replay_unknown_deal_raises(self):
        with self.assertRaises(ValueError):
            _deal_replay(self.deals_dir, "ghost")

    def test_missing_snapshot_falls_back_to_server_config(self):
        validated, fields = _validate_deal_create_payload(
            {"deal_id": "deal-9", "config_revision_id": "rev-9"}
        )
        self.assertEqual(fields, {})
        self.assertEqual(
            _deal_create(self.deals_dir, validated)["result"], "CREATED"
        )
        appended = _deal_append_event(
            self.deals_dir, "deal-9",
            {
                "event_id": "event-1",
                "config_revision_id": "rev-9",
                "event": "START",
                "event_sequence": 1,
            },
        )
        self.assertEqual(appended["lifecycle"]["status"], "RUNNING")


if __name__ == "__main__":
    unittest.main()
