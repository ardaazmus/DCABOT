import unittest

from dcabot.application.signal_intake import (
    SignalIntakeError,
    check_replay_window,
    hash_signal_payload,
    verify_signal_signature,
)

PAYLOAD_HASH = "6d5092a32c7977230e61f3569261e2ae1735096f5896a550a6d1e8b98a9c6cec"
KEY_ID = "demo-key-1"
KEY_HEX = "0f" * 32
GOOD_SIG = "57a37fd91c5e930ff35576b57e1d314c250e379546d8f40337b22d67971f2191"


class HashSignalPayloadTests(unittest.TestCase):
    def test_canonical_hash_is_key_order_independent(self):
        first = hash_signal_payload({"action": "BUY", "symbol": "BTCUSDT"})
        second = hash_signal_payload({"symbol": "BTCUSDT", "action": "BUY"})
        self.assertEqual(first, PAYLOAD_HASH)
        self.assertEqual(second, PAYLOAD_HASH)

    def test_non_json_payload_is_rejected(self):
        with self.assertRaises(SignalIntakeError) as ctx:
            hash_signal_payload({"when": object()})
        self.assertEqual(ctx.exception.code, "SIGNAL_PAYLOAD_NOT_JSON")

    def test_non_dict_payload_is_rejected(self):
        with self.assertRaises(SignalIntakeError) as ctx:
            hash_signal_payload(["BUY"])
        self.assertEqual(ctx.exception.code, "SIGNAL_PAYLOAD_NOT_JSON")


class VerifySignalSignatureTests(unittest.TestCase):
    def test_valid_signature_passes(self):
        verify_signal_signature(
            payload_hash=PAYLOAD_HASH,
            signature=GOOD_SIG,
            key_id=KEY_ID,
            keys={KEY_ID: KEY_HEX},
        )

    def test_tampered_signature_fails(self):
        bad = "00" + GOOD_SIG[2:]
        with self.assertRaises(SignalIntakeError) as ctx:
            verify_signal_signature(
                payload_hash=PAYLOAD_HASH,
                signature=bad,
                key_id=KEY_ID,
                keys={KEY_ID: KEY_HEX},
            )
        self.assertEqual(ctx.exception.code, "SIGNAL_SIGNATURE_MISMATCH")

    def test_unknown_key_id_fails_closed(self):
        with self.assertRaises(SignalIntakeError) as ctx:
            verify_signal_signature(
                payload_hash=PAYLOAD_HASH,
                signature=GOOD_SIG,
                key_id="nope",
                keys={KEY_ID: KEY_HEX},
            )
        self.assertEqual(ctx.exception.code, "SIGNAL_KEY_UNKNOWN")

    def test_malformed_signature_fails_closed(self):
        with self.assertRaises(SignalIntakeError) as ctx:
            verify_signal_signature(
                payload_hash=PAYLOAD_HASH,
                signature="ZZZ",
                key_id=KEY_ID,
                keys={KEY_ID: KEY_HEX},
            )
        self.assertEqual(ctx.exception.code, "SIGNAL_SIGNATURE_MALFORMED")

    def test_error_carries_no_key_material(self):
        try:
            verify_signal_signature(
                payload_hash=PAYLOAD_HASH,
                signature="00" * 32,
                key_id=KEY_ID,
                keys={KEY_ID: KEY_HEX},
            )
            self.fail("expected mismatch")
        except SignalIntakeError as error:
            self.assertNotIn(KEY_HEX, str(error))
            self.assertNotIn("0f0f", str(error))


class CheckReplayWindowTests(unittest.TestCase):
    def test_fresh_unseen_signal_accepts(self):
        self.assertEqual(
            check_replay_window(
                event_time_us=1000,
                observation_time_us=2000,
                max_age_us=5000,
                seen_ids=frozenset(),
                signal_id="s1",
            ),
            "ACCEPT",
        )

    def test_expired_signal_is_rejected(self):
        with self.assertRaises(SignalIntakeError) as ctx:
            check_replay_window(
                event_time_us=1000,
                observation_time_us=7000,
                max_age_us=5000,
                seen_ids=frozenset(),
                signal_id="s1",
            )
        self.assertEqual(ctx.exception.code, "SIGNAL_REPLAY_EXPIRED")

    def test_future_signal_is_rejected(self):
        with self.assertRaises(SignalIntakeError) as ctx:
            check_replay_window(
                event_time_us=8000,
                observation_time_us=2000,
                max_age_us=5000,
                seen_ids=frozenset(),
                signal_id="s1",
            )
        self.assertEqual(ctx.exception.code, "SIGNAL_REPLAY_FUTURE")

    def test_seen_signal_id_is_rejected(self):
        with self.assertRaises(SignalIntakeError) as ctx:
            check_replay_window(
                event_time_us=1000,
                observation_time_us=2000,
                max_age_us=5000,
                seen_ids=frozenset({"s1"}),
                signal_id="s1",
            )
        self.assertEqual(ctx.exception.code, "SIGNAL_REPLAY_DUPLICATE")


if __name__ == "__main__":
    unittest.main()
