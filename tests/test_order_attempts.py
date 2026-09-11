import tempfile
import unittest
from pathlib import Path

from dcabot.application.order_attempt import (
    AttemptState,
    OrderAttempt,
    request_fingerprint,
)
from dcabot.application.order_sender import (
    AmbiguousTransportError,
    DefinitiveTransportError,
    OrderSender,
    TransportAccepted,
)
from dcabot.persistence.attempt_store import AttemptStore


def attempt(attempt_id: str = "attempt-1") -> OrderAttempt:
    return OrderAttempt(
        attempt_id=attempt_id,
        run_id="run-1",
        venue="BINANCE_SPOT_TESTNET",
        operation="PLACE_ORDER",
        symbol="BTCUSDT",
        client_order_id="client-1",
        request_fingerprint_sha256=request_fingerprint(
            {"symbol": "BTCUSDT", "side": "BUY", "quantity": "0.001"}
        ),
        capability_snapshot_hash="a" * 64,
        filter_snapshot_hash="b" * 64,
        state=AttemptState.PREPARED,
        created_at_us=1_700_000_000_000_000,
        last_transition_at_us=1_700_000_000_000_000,
    )


class RecordingTransport:
    def __init__(self, outcome=None):
        self.outcome = outcome or TransportAccepted()
        self.calls = 0

    def send(self, _attempt, _payload):
        self.calls += 1
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


class OrderAttemptTests(unittest.TestCase):
    def test_transport_is_forbidden_until_attempt_is_durable(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AttemptStore(Path(directory) / "attempts.sqlite")
            store.prepare(attempt())
            transport = RecordingTransport()
            sender = OrderSender(store, clock_us=lambda: 1_700_000_000_000_100)

            with self.assertRaisesRegex(ValueError, "ATTEMPT_NOT_PERSISTED"):
                sender.send(
                    "attempt-1",
                    {"symbol": "BTCUSDT", "side": "BUY", "quantity": "0.001"},
                    transport,
                )
            self.assertEqual(transport.calls, 0)

            store.persist("attempt-1", now_us=1_700_000_000_000_050)
            result = sender.send(
                "attempt-1",
                {"symbol": "BTCUSDT", "side": "BUY", "quantity": "0.001"},
                transport,
            )

            self.assertEqual(result.state, AttemptState.ACKNOWLEDGED)
            self.assertEqual(transport.calls, 1)
            store.close()

    def test_ambiguous_transport_becomes_unknown_and_cannot_be_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AttemptStore(Path(directory) / "attempts.sqlite")
            store.prepare(attempt())
            store.persist("attempt-1", now_us=1_700_000_000_000_050)
            transport = RecordingTransport(AmbiguousTransportError())
            sender = OrderSender(store, clock_us=lambda: 1_700_000_000_000_100)
            payload = {"symbol": "BTCUSDT", "side": "BUY", "quantity": "0.001"}

            result = sender.send("attempt-1", payload, transport)
            self.assertEqual(result.state, AttemptState.UNKNOWN)
            with self.assertRaisesRegex(
                ValueError, "ATTEMPT_RECONCILIATION_REQUIRED"
            ):
                sender.send("attempt-1", payload, transport)
            self.assertEqual(transport.calls, 1)
            store.close()

    def test_restart_converts_in_flight_send_to_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "attempts.sqlite"
            store = AttemptStore(path)
            store.prepare(attempt())
            store.persist("attempt-1", now_us=1_700_000_000_000_050)
            store.mark_sending("attempt-1", now_us=1_700_000_000_000_100)
            store.close()

            reopened = AttemptStore(path)
            recovered = reopened.recover_after_restart(
                now_us=1_700_000_000_000_200
            )

            self.assertEqual(recovered, (reopened.get("attempt-1"),))
            self.assertEqual(recovered[0].state, AttemptState.UNKNOWN)
            self.assertEqual(
                recovered[0].terminal_reason, "RESTART_DURING_SEND"
            )
            reopened.close()

    def test_unknown_can_only_enter_reconciliation(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AttemptStore(Path(directory) / "attempts.sqlite")
            store.prepare(attempt())
            store.persist("attempt-1", now_us=1_700_000_000_000_050)
            store.mark_sending("attempt-1", now_us=1_700_000_000_000_100)
            store.mark_unknown(
                "attempt-1",
                now_us=1_700_000_000_000_150,
                reason="TRANSPORT_AMBIGUOUS",
            )

            result = store.begin_reconciliation(
                "attempt-1", now_us=1_700_000_000_000_200
            )

            self.assertEqual(result.state, AttemptState.RECONCILING)
            store.close()

    def test_secret_bearing_payload_is_rejected_before_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AttemptStore(Path(directory) / "attempts.sqlite")
            with self.assertRaisesRegex(ValueError, "ATTEMPT_PAYLOAD_UNSAFE"):
                request_fingerprint(
                    {
                        "symbol": "BTCUSDT",
                        "secret": "never-store-me",
                    }
                )
            self.assertEqual(store.count(), 0)
            self.assertNotIn(
                "payload",
                {
                    row[1]
                    for row in store.db.execute("PRAGMA table_info(attempts)").fetchall()
                },
            )
            store.close()

    def test_request_fingerprint_has_a_bounded_serialized_size(self):
        with self.assertRaisesRegex(ValueError, "ATTEMPT_PAYLOAD_TOO_LARGE"):
            request_fingerprint({"symbol": "BTCUSDT", "blob": "x" * 65536})

    def test_payload_mismatch_does_not_enter_sending(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AttemptStore(Path(directory) / "attempts.sqlite")
            store.prepare(attempt())
            store.persist("attempt-1", now_us=1_700_000_000_000_050)
            transport = RecordingTransport()
            sender = OrderSender(store, clock_us=lambda: 1_700_000_000_000_100)

            with self.assertRaisesRegex(ValueError, "ATTEMPT_PAYLOAD_MISMATCH"):
                sender.send(
                    "attempt-1",
                    {"symbol": "BTCUSDT", "side": "SELL", "quantity": "0.001"},
                    transport,
                )
            self.assertEqual(store.get("attempt-1").state, AttemptState.PERSISTED)
            self.assertEqual(transport.calls, 0)
            store.close()

    def test_existing_unrelated_sqlite_file_is_not_adopted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unrelated.sqlite"
            import sqlite3

            db = sqlite3.connect(path)
            try:
                db.execute("CREATE TABLE user_data(value TEXT NOT NULL)")
                db.execute("INSERT INTO user_data(value) VALUES ('keep')")
                db.commit()
            finally:
                db.close()

            with self.assertRaisesRegex(ValueError, "ATTEMPT_STORE_UNSUPPORTED"):
                AttemptStore(path)

            db = sqlite3.connect(path)
            try:
                self.assertEqual(
                    db.execute("SELECT value FROM user_data").fetchone(), ("keep",)
                )
            finally:
                db.close()

    def test_definitive_rejection_is_terminal_without_raw_error_text(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AttemptStore(Path(directory) / "attempts.sqlite")
            store.prepare(attempt())
            store.persist("attempt-1", now_us=1_700_000_000_000_050)
            transport = RecordingTransport(
                DefinitiveTransportError("FILTER_REJECTED", "untrusted-detail")
            )
            sender = OrderSender(store, clock_us=lambda: 1_700_000_000_000_100)

            result = sender.send(
                "attempt-1",
                {"symbol": "BTCUSDT", "side": "BUY", "quantity": "0.001"},
                transport,
            )

            self.assertEqual(result.state, AttemptState.REJECTED)
            self.assertEqual(result.terminal_reason, "FILTER_REJECTED")
            self.assertNotIn("untrusted-detail", repr(result))
            store.close()

    def test_unexpected_transport_error_is_not_reclassified_as_venue_ambiguity(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AttemptStore(Path(directory) / "attempts.sqlite")
            store.prepare(attempt())
            store.persist("attempt-1", now_us=1_700_000_000_000_050)
            sender = OrderSender(store, clock_us=lambda: 1_700_000_000_000_100)

            with self.assertRaisesRegex(RuntimeError, "programming bug"):
                sender.send(
                    "attempt-1",
                    {"symbol": "BTCUSDT", "side": "BUY", "quantity": "0.001"},
                    RecordingTransport(RuntimeError("programming bug")),
                )

            self.assertEqual(store.get("attempt-1").state, AttemptState.SENDING)
            store.close()


if __name__ == "__main__":
    unittest.main()
