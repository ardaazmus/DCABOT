import unittest

from dcabot.application.signal_event_contract import (
    SignalEvent,
    SignalEventContractError,
    accept_signal,
    new_signal_event,
)


def signal(*, signal_id="sig-1", event_time_us=1_000, payload_hash="a" * 64):
    return new_signal_event(
        signal_id=signal_id,
        source="offline-fixture",
        event_time_us=event_time_us,
        schema_version="signal-v1",
        payload_hash=payload_hash,
    )


class SignalEventContractTests(unittest.TestCase):
    def test_signal_has_explicit_event_identity_and_accepts_in_order(self):
        event = signal()

        history, outcome = accept_signal((), event)

        self.assertEqual(history, (event,))
        self.assertEqual(outcome, "ACCEPTED")
        self.assertFalse(hasattr(event, "orders"))
        self.assertFalse(hasattr(event, "fills"))

    def test_exact_duplicate_is_noop_and_different_payload_conflicts(self):
        event = signal()
        history, _ = accept_signal((), event)

        duplicate_history, duplicate_outcome = accept_signal(history, event)
        self.assertEqual(duplicate_history, history)
        self.assertEqual(duplicate_outcome, "DUPLICATE")

        with self.assertRaisesRegex(
            SignalEventContractError, "SIGNAL_EVENT_CONFLICT"
        ):
            accept_signal(history, signal(payload_hash="b" * 64))

    def test_older_event_time_is_explicitly_rejected_as_stale(self):
        history, _ = accept_signal((), signal(event_time_us=2_000))

        with self.assertRaisesRegex(SignalEventContractError, "SIGNAL_EVENT_STALE"):
            accept_signal(history, signal(signal_id="sig-2", event_time_us=1_999))

    def test_invalid_identity_time_schema_or_hash_fails_closed(self):
        cases = (
            {"signal_id": "bad id"},
            {"event_time_us": -1},
            {"schema_version": ""},
            {"payload_hash": "not-a-sha256"},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides), self.assertRaises(
                SignalEventContractError
            ):
                values = {
                    "signal_id": "sig-1",
                    "source": "offline-fixture",
                    "event_time_us": 1_000,
                    "schema_version": "signal-v1",
                    "payload_hash": "a" * 64,
                }
                values.update(overrides)
                new_signal_event(**values)

    def test_history_must_be_valid_and_event_time_must_not_use_float(self):
        with self.assertRaisesRegex(
            SignalEventContractError, "SIGNAL_HISTORY_INVALID"
        ):
            accept_signal([], signal())
        with self.assertRaisesRegex(
            SignalEventContractError, "SIGNAL_EVENT_TIME_INVALID"
        ):
            new_signal_event(
                signal_id="sig-1",
                source="offline-fixture",
                event_time_us=True,
                schema_version="signal-v1",
                payload_hash="a" * 64,
            )

