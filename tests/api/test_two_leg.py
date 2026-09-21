"""F6.2: two-leg session API over the durable journal."""
import tempfile
import unittest
from pathlib import Path

from dcabot.persistence.two_leg_journal import TwoLegJournal
from dcabot.server.api import (
    _two_leg_accept_fill,
    _two_leg_mark,
    _two_leg_replay,
    _two_leg_start,
    _validate_two_leg_fill_payload,
    _validate_two_leg_session_payload,
)


def _fill_body(**overrides):
    body = {
        "fill_id": "f-a1",
        "leg_id": "A",
        "account_id": "acct-1",
        "venue_profile": "BINANCE-SPOT",
        "product_id": "BTCUSDT",
        "symbol": "BTCUSDT",
        "hedge_side": "LONG",
        "quantity": "0.5",
        "fill_status": "FULL",
        "event_time_us": 1000,
    }
    body.update(overrides)
    return body


class TwoLegApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.journal = TwoLegJournal(Path(self.tmp.name) / "two_leg.db")

    def tearDown(self):
        self.journal.close()
        self.tmp.cleanup()

    def test_start_replay_roundtrip(self):
        validated, fields = _validate_two_leg_session_payload({"session_id": "s-1"})
        self.assertEqual(fields, {})
        started = _two_leg_start(self.journal, validated)
        self.assertEqual(started["result"], "CREATED")
        self.assertEqual(started["projection"]["state"], "LEG_A_PENDING")
        replayed = _two_leg_replay(self.journal, "s-1")
        self.assertEqual(replayed["projection"]["state"], "LEG_A_PENDING")

    def test_accept_fill_returns_projection(self):
        _two_leg_start(self.journal, {"session_id": "s-1"})
        validated, fields = _validate_two_leg_fill_payload(_fill_body())
        self.assertEqual(fields, {})
        result = _two_leg_accept_fill(self.journal, "s-1", validated)
        self.assertEqual(result["result"], "ACCEPTED")
        projection = result["projection"]
        self.assertEqual(projection["state"], "ONE_LEG_FILLED")
        self.assertEqual(projection["leg_a_quantity"], "0.5")
        self.assertEqual(len(projection["fills"]), 1)
        self.assertEqual(projection["fills"][0]["fill_id"], "f-a1")

    def test_mark_recovery_terminal(self):
        _two_leg_start(self.journal, {"session_id": "s-1"})
        _two_leg_accept_fill(self.journal, "s-1", _fill_body())
        result = _two_leg_mark(self.journal, "s-1", "RECOVERY_REQUIRED")
        self.assertEqual(result["projection"]["state"], "RECOVERY_REQUIRED")
        self.assertEqual(result["projection"]["leg_a_quantity"], "0.5")

    def test_mark_timeout_from_pending(self):
        _two_leg_start(self.journal, {"session_id": "s-1"})
        result = _two_leg_mark(self.journal, "s-1", "TIMEOUT")
        self.assertEqual(result["projection"]["state"], "TIMEOUT")

    def test_bad_session_id_is_field_error(self):
        validated, fields = _validate_two_leg_session_payload({"session_id": "no spaces!"})
        self.assertIsNone(validated)
        self.assertIn("session_id", fields)

    def test_bad_leg_is_field_error(self):
        validated, fields = _validate_two_leg_fill_payload(_fill_body(leg_id="C"))
        self.assertIsNone(validated)
        self.assertIn("leg_id", fields)

    def test_non_integer_event_time_is_field_error(self):
        validated, fields = _validate_two_leg_fill_payload(_fill_body(event_time_us="1000"))
        self.assertIsNone(validated)
        self.assertIn("event_time_us", fields)

    def test_unknown_session_raises_value_error(self):
        with self.assertRaises(ValueError):
            _two_leg_replay(self.journal, "ghost")


if __name__ == "__main__":
    unittest.main()
