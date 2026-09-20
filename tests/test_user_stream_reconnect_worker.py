import json
import unittest

from dcabot.application.credential_boundary import CredentialMaterial, EphemeralCredentialProvider
from dcabot.application.reconciliation import ConnectionState, EventDecision, ReconciliationCoordinator
from dcabot.application.signed_request import ApiKeyType
from dcabot.application.user_stream_reconnect_worker import (
    DEFAULT_BACKOFF_SCHEDULE_SECONDS,
    ReconnectWorkerError,
    ReconnectWorkerEvent,
    UserStreamReconnectWorker,
)
from dcabot.data_adapters.binance_testnet_user_stream import BinanceTestnetUserDataStream


class FixedClock:
    def now_ms(self) -> int:
        return 1_700_000_000_000


class FakeSocket:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.closed = False

    async def send(self, message: str) -> None:
        pass

    async def recv(self):
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response

    async def close(self) -> None:
        self.closed = True


def _provider() -> EphemeralCredentialProvider:
    result = EphemeralCredentialProvider()
    result.put(
        CredentialMaterial(
            credential_id="testnet-readonly",
            api_key="dummy-api-key",
            key_type=ApiKeyType.HMAC,
            secret=b"dummy-secret",
        )
    )
    return result


def _subscribe_response(request_id: str, subscription_id: int) -> str:
    return json.dumps({"id": request_id, "status": 200, "result": {"subscriptionId": subscription_id}})


def _execution_report(subscription_id: int, *, order_id: int, execution_id: int, event_time_ms: int) -> str:
    return json.dumps(
        {
            "subscriptionId": subscription_id,
            "event": {"e": "executionReport", "E": event_time_ms, "i": order_id, "I": execution_id},
        }
    )


def _make_stream(socket: FakeSocket, *, request_id: str = "request-1") -> BinanceTestnetUserDataStream:
    return BinanceTestnetUserDataStream(
        "testnet-readonly",
        provider=_provider(),
        clock=FixedClock(),
        websocket_factory=lambda _url, **_kwargs: socket,
        request_id_factory=lambda: request_id,
    )


class UserStreamReconnectWorkerConstructionTests(unittest.TestCase):
    def test_rejects_invalid_constructor_arguments(self):
        coordinator = ReconciliationCoordinator()
        with self.assertRaises(ReconnectWorkerError) as not_callable:
            UserStreamReconnectWorker(None, coordinator=coordinator)
        self.assertEqual(not_callable.exception.code, "WORKER_STREAM_FACTORY_INVALID")

        with self.assertRaises(ReconnectWorkerError) as bad_coordinator:
            UserStreamReconnectWorker(lambda: None, coordinator=object())
        self.assertEqual(bad_coordinator.exception.code, "WORKER_COORDINATOR_INVALID")

        with self.assertRaises(ReconnectWorkerError) as bad_backoff:
            UserStreamReconnectWorker(
                lambda: None, coordinator=coordinator, backoff_schedule_seconds=()
            )
        self.assertEqual(bad_backoff.exception.code, "WORKER_BACKOFF_INVALID")

        with self.assertRaises(ReconnectWorkerError) as bad_attempts:
            UserStreamReconnectWorker(lambda: None, coordinator=coordinator, max_attempts=0)
        self.assertEqual(bad_attempts.exception.code, "WORKER_MAX_ATTEMPTS_INVALID")


class UserStreamReconnectWorkerTests(unittest.IsolatedAsyncioTestCase):
    async def test_connects_and_accepts_events_reaching_connected_read_only(self):
        socket = FakeSocket(
            _subscribe_response("request-1", 7),
            _execution_report(7, order_id=1, execution_id=1, event_time_ms=1_700_000_000_100),
        )
        coordinator = ReconciliationCoordinator()
        transitions: list[ReconnectWorkerEvent] = []
        worker = UserStreamReconnectWorker(
            lambda: _make_stream(socket),
            coordinator=coordinator,
            on_transition=transitions.append,
        )

        final_state = await worker.run(max_events=1)

        self.assertEqual(final_state, ConnectionState.CONNECTED_READ_ONLY)
        self.assertEqual([event.kind for event in transitions], ["CONNECTED", "EVENT"])
        self.assertEqual(transitions[-1].detail, EventDecision.ACCEPTED.value)

    async def test_disconnect_then_successful_reconnect_reaches_reconciliation_required(self):
        first_socket = FakeSocket(
            _subscribe_response("request-1", 7),
            _execution_report(7, order_id=1, execution_id=1, event_time_ms=1_700_000_000_100),
            OSError("connection dropped"),
        )
        second_socket = FakeSocket(
            _subscribe_response("request-1", 8),
            _execution_report(8, order_id=1, execution_id=2, event_time_ms=1_700_000_000_200),
        )
        sockets = iter([first_socket, second_socket])
        sleeps: list[float] = []
        coordinator = ReconciliationCoordinator()
        transitions: list[ReconnectWorkerEvent] = []
        worker = UserStreamReconnectWorker(
            lambda: _make_stream(next(sockets)),
            coordinator=coordinator,
            sleep=_recording_sleep(sleeps),
            on_transition=transitions.append,
        )

        final_state = await worker.run(max_events=2)

        self.assertEqual(final_state, ConnectionState.RECONCILIATION_REQUIRED)
        self.assertEqual(
            [event.kind for event in transitions],
            ["CONNECTED", "EVENT", "DISCONNECTED", "RECONNECTING", "RECONNECTED", "EVENT"],
        )
        self.assertEqual(sleeps, [1])  # a recv-drop also backs off before the next connect attempt

    async def test_real_gap_after_reconnect_is_detected_via_out_of_order_event(self):
        first_socket = FakeSocket(
            _subscribe_response("request-1", 7),
            _execution_report(7, order_id=1, execution_id=1, event_time_ms=1_700_000_000_500),
            OSError("connection dropped"),
        )
        # Missed an update while disconnected: the next event the venue redelivers is older.
        second_socket = FakeSocket(
            _subscribe_response("request-1", 8),
            _execution_report(8, order_id=1, execution_id=2, event_time_ms=1_700_000_000_100),
        )
        sockets = iter([first_socket, second_socket])
        coordinator = ReconciliationCoordinator()
        transitions: list[ReconnectWorkerEvent] = []
        worker = UserStreamReconnectWorker(
            lambda: _make_stream(next(sockets)),
            coordinator=coordinator,
            on_transition=transitions.append,
        )

        final_state = await worker.run(max_events=2)

        self.assertEqual(final_state, ConnectionState.GAP)
        self.assertEqual(transitions[-1].detail, EventDecision.OUT_OF_ORDER.value)
        self.assertEqual(transitions[-1].connection_state, ConnectionState.GAP)

    async def test_connect_failures_exhaust_bounded_retries_and_fail_closed(self):
        sockets = [FakeSocket(OSError("refused")) for _ in range(4)]
        sockets_iter = iter(sockets)
        sleeps: list[float] = []
        coordinator = ReconciliationCoordinator()
        transitions: list[ReconnectWorkerEvent] = []
        worker = UserStreamReconnectWorker(
            lambda: _make_stream(next(sockets_iter)),
            coordinator=coordinator,
            sleep=_recording_sleep(sleeps),
            backoff_schedule_seconds=(1, 2),
            max_attempts=3,
            on_transition=transitions.append,
        )

        with self.assertRaises(ReconnectWorkerError) as exhausted:
            await worker.run()

        self.assertEqual(exhausted.exception.code, "WORKER_RECONNECT_EXHAUSTED")
        self.assertEqual(coordinator.state, ConnectionState.STALE)
        self.assertEqual(sleeps, [1, 2, 2])  # backoff schedule clamps to its last value past its length
        self.assertEqual(transitions[-1].kind, "FAILED")

    async def test_default_backoff_schedule_is_bounded_and_positive(self):
        self.assertTrue(DEFAULT_BACKOFF_SCHEDULE_SECONDS)
        self.assertTrue(all(value > 0 for value in DEFAULT_BACKOFF_SCHEDULE_SECONDS))


def _recording_sleep(sink: list[float]):
    async def sleep(seconds: float) -> None:
        sink.append(seconds)

    return sleep


if __name__ == "__main__":
    unittest.main()
