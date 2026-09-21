import unittest

from dcabot.server.api import (
    _signal_assess,
    _signal_bind_candidate,
    _signal_hash,
    _validate_signal_assess_payload,
    _validate_signal_candidate_payload,
    _validate_signal_hash_payload,
)

HASH = "6d5092a32c7977230e61f3569261e2ae1735096f5896a550a6d1e8b98a9c6cec"


def _signal():
    return {
        "signal_id": "s1",
        "source": "offline-fixture",
        "event_time_us": 1700000000000000,
        "schema_version": "signal-v1",
        "payload_hash": HASH,
    }


class SignalHashApiTests(unittest.TestCase):
    def test_hash_matches_canonical_vector(self):
        validated, fields = _validate_signal_hash_payload(
            {"payload": {"action": "BUY", "symbol": "BTCUSDT"}}
        )
        self.assertEqual(fields, {})
        self.assertEqual(_signal_hash(validated), {"payload_hash": HASH})

    def test_non_object_payload_is_field_error(self):
        validated, fields = _validate_signal_hash_payload({"payload": ["BUY"]})
        self.assertIsNone(validated)
        self.assertIn("payload", fields)


class SignalAssessApiTests(unittest.TestCase):
    def test_ready_assessment(self):
        validated, fields = _validate_signal_assess_payload(
            {
                "signal": _signal(),
                "closed_bar_time_us": 1700000000000000,
                "warmup_bars_observed": 10,
                "required_warmup_bars": 5,
                "max_staleness_us": 5_000_000,
            }
        )
        self.assertEqual(fields, {})
        result = _signal_assess(validated)
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["signal_id"], "s1")


class SignalCandidateApiTests(unittest.TestCase):
    def test_bind_returns_candidate(self):
        validated, fields = _validate_signal_candidate_payload(
            {
                "signal": _signal(),
                "closed_bar_time_us": 1700000000000000,
                "warmup_bars_observed": 10,
                "required_warmup_bars": 5,
                "max_staleness_us": 5_000_000,
                "action": "BUY",
                "symbol": "BTCUSDT",
                "action_map": [["BUY", "BUY"], ["SELL", "SELL"]],
                "qty": "0.01",
                "ttl_us": 60_000_000,
            }
        )
        self.assertEqual(fields, {})
        result = _signal_bind_candidate(validated, 1700000002000000)
        self.assertEqual(result["status"], "CANDIDATE")
        self.assertEqual(result["side"], "BUY")
        self.assertEqual(result["expires_us"], 1700000060000000)
        self.assertRegex(result["candidate_id"], r"\A[0-9a-f]{64}\Z")

    def test_warming_up_cannot_bind(self):
        validated, fields = _validate_signal_candidate_payload(
            {
                "signal": _signal(),
                "closed_bar_time_us": 1700000000000000,
                "warmup_bars_observed": 2,
                "required_warmup_bars": 5,
                "max_staleness_us": 5_000_000,
                "action": "BUY",
                "symbol": "BTCUSDT",
                "action_map": [["BUY", "BUY"], ["SELL", "SELL"]],
                "qty": "0.01",
                "ttl_us": 60_000_000,
            }
        )
        self.assertEqual(fields, {})
        with self.assertRaises(ValueError) as ctx:
            _signal_bind_candidate(validated, 1700000002000000)
        self.assertIn("SIGNAL_CANDIDATE_NOT_READY", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
