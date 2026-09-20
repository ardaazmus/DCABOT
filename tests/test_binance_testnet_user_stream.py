import asyncio
import hashlib
import hmac
import json
import unittest

from dcabot.application.credential_boundary import CredentialMaterial, EphemeralCredentialProvider
from dcabot.application.reconciliation import OrderLookup, UserDataEvent
from dcabot.application.signed_request import ApiKeyType
from dcabot.data_adapters.binance_testnet_user_stream import (
    BINANCE_SPOT_TESTNET_WS_API_URL,
    BinanceTestnetUserDataStream,
    BinanceTestnetUserStreamError,
    UserDataOrderListEvent,
    query_binance_testnet_order_status,
)


class FixedClock:
    def now_ms(self) -> int:
        return 1_700_000_000_000


class FakeSocket:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.sent = []
        self.closed = False

    async def send(self, message: str) -> None:
        self.sent.append(message)

    async def recv(self):
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response

    async def close(self) -> None:
        self.closed = True


def provider() -> EphemeralCredentialProvider:
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


class BinanceTestnetUserDataStreamTests(unittest.IsolatedAsyncioTestCase):
    async def test_signed_read_only_subscription_and_execution_report_are_bounded(self):
        socket = FakeSocket(
            json.dumps({"id": "request-1", "status": 200, "result": {"subscriptionId": 7}}),
            json.dumps(
                {
                    "subscriptionId": 7,
                    "event": {"e": "executionReport", "E": 1_700_000_000_123, "i": 777, "I": 9},
                }
            ),
        )
        stream = BinanceTestnetUserDataStream(
            "testnet-readonly",
            provider=provider(),
            clock=FixedClock(),
            websocket_factory=lambda _url, **_kwargs: socket,
            request_id_factory=lambda: "request-1",
        )

        subscription = await stream.connect()
        event = await stream.recv_execution_report()

        self.assertEqual(subscription.subscription_id, 7)
        self.assertEqual(event, UserDataEvent.create("execution:777:9", 1_700_000_000_123, "executionReport", 777))
        request = json.loads(socket.sent[0])
        self.assertEqual(request["method"], "userDataStream.subscribe.signature")
        self.assertEqual(request["params"]["apiKey"], "dummy-api-key")
        self.assertEqual(request["params"]["timestamp"], 1_700_000_000_000)
        self.assertEqual(request["params"]["recvWindow"], 5_000)
        expected = hmac.new(
            b"dummy-secret",
            b"apiKey=dummy-api-key&recvWindow=5000&timestamp=1700000000000",
            hashlib.sha256,
        ).hexdigest()
        self.assertEqual(request["params"]["signature"], expected)
        self.assertNotIn("dummy-secret", socket.sent[0])

    async def test_list_status_is_decoded_as_redacted_oco_identity_only(self):
        socket = FakeSocket(
            json.dumps({"id": "request-1", "status": 200, "result": {"subscriptionId": 7}}),
            json.dumps(
                {
                    "subscriptionId": 7,
                    "event": {
                        "e": "listStatus",
                        "E": 1_700_000_000_123,
                        "s": "BTCUSDT",
                        "g": 42,
                        "c": "OCO",
                        "l": "EXEC_STARTED",
                        "L": "EXECUTING",
                        "r": "NONE",
                        "C": "list-42",
                        "T": 1_700_000_000_120,
                        "O": [
                            {"s": "BTCUSDT", "i": 101, "c": "working-101"},
                            {"s": "BTCUSDT", "i": 102, "c": "pending-102"},
                        ],
                    },
                }
            ),
        )
        stream = BinanceTestnetUserDataStream(
            "testnet-readonly",
            provider=provider(),
            clock=FixedClock(),
            websocket_factory=lambda _url, **_kwargs: socket,
            request_id_factory=lambda: "request-1",
        )

        await stream.connect()
        event = await stream.recv_order_list_event()

        self.assertIsInstance(event, UserDataOrderListEvent)
        self.assertEqual(event.event_id, "list:42:1700000000120:1700000000123")
        self.assertEqual(event.order_list_id, 42)
        self.assertEqual(event.list_client_order_id, "list-42")
        self.assertEqual(tuple(order.order_id for order in event.orders), (101, 102))
        self.assertEqual(event.list_status.value, "EXEC_STARTED")
        self.assertEqual(event.list_order_status.value, "EXECUTING")
        self.assertFalse(hasattr(event, "price"))

    async def test_list_status_missing_or_ambiguous_leg_identity_fails_closed(self):
        socket = FakeSocket(
            json.dumps({"id": "request-1", "status": 200, "result": {"subscriptionId": 7}}),
            json.dumps(
                {
                    "subscriptionId": 7,
                    "event": {
                        "e": "listStatus",
                        "E": 1,
                        "s": "BTCUSDT",
                        "g": 42,
                        "c": "OCO",
                        "l": "EXEC_STARTED",
                        "L": "EXECUTING",
                        "C": "list-42",
                        "T": 1,
                        "O": [{"s": "BTCUSDT", "i": 101, "c": "working-101"}],
                    },
                }
            ),
        )
        stream = BinanceTestnetUserDataStream(
            "testnet-readonly",
            provider=provider(),
            clock=FixedClock(),
            websocket_factory=lambda _url, **_kwargs: socket,
            request_id_factory=lambda: "request-1",
        )
        await stream.connect()

        with self.assertRaisesRegex(BinanceTestnetUserStreamError, "USER_STREAM_ORDER_LIST_INVALID"):
            await stream.recv_order_list_event()
        self.assertTrue(socket.closed)

    async def test_subscription_error_closes_socket_and_fails_closed(self):
        socket = FakeSocket(json.dumps({"id": "request-1", "status": 400, "error": {"code": -1022}}))
        stream = BinanceTestnetUserDataStream(
            "testnet-readonly",
            provider=provider(),
            clock=FixedClock(),
            websocket_factory=lambda _url, **_kwargs: socket,
            request_id_factory=lambda: "request-1",
        )

        with self.assertRaisesRegex(BinanceTestnetUserStreamError, "USER_STREAM_SUBSCRIPTION_REJECTED"):
            await stream.connect()
        self.assertTrue(socket.closed)

    async def test_wrong_subscription_or_unsupported_event_never_becomes_reconciliation_event(self):
        socket = FakeSocket(
            json.dumps({"id": "request-1", "status": 200, "result": {"subscriptionId": 7}}),
            json.dumps({"subscriptionId": 8, "event": {"e": "executionReport", "E": 1, "i": 2, "I": 3}}),
        )
        stream = BinanceTestnetUserDataStream(
            "testnet-readonly",
            provider=provider(),
            clock=FixedClock(),
            websocket_factory=lambda _url, **_kwargs: socket,
            request_id_factory=lambda: "request-1",
        )
        await stream.connect()

        with self.assertRaisesRegex(BinanceTestnetUserStreamError, "USER_STREAM_SUBSCRIPTION_MISMATCH"):
            await stream.recv_execution_report()
        self.assertTrue(socket.closed)

        unsupported = FakeSocket(
            json.dumps({"id": "request-1", "status": 200, "result": {"subscriptionId": 7}}),
            json.dumps({"subscriptionId": 7, "event": {"e": "outboundAccountPosition", "E": 1}}),
        )
        second = BinanceTestnetUserDataStream(
            "testnet-readonly",
            provider=provider(),
            clock=FixedClock(),
            websocket_factory=lambda _url, **_kwargs: unsupported,
            request_id_factory=lambda: "request-1",
        )
        await second.connect()
        with self.assertRaisesRegex(BinanceTestnetUserStreamError, "USER_STREAM_EVENT_UNSUPPORTED"):
            await second.recv_execution_report()
        self.assertTrue(unsupported.closed)

    async def test_connection_is_read_only_and_uses_testnet_endpoint(self):
        socket = FakeSocket(json.dumps({"id": "request-1", "status": 200, "result": {"subscriptionId": 7}}))
        observed = {}

        def factory(url, **kwargs):
            observed.update(url=url, kwargs=kwargs)
            return socket

        stream = BinanceTestnetUserDataStream(
            "testnet-readonly",
            provider=provider(),
            clock=FixedClock(),
            websocket_factory=factory,
            request_id_factory=lambda: "request-1",
        )
        await stream.connect()

        self.assertEqual(observed["url"], BINANCE_SPOT_TESTNET_WS_API_URL)
        self.assertEqual(observed["kwargs"]["max_size"], 256 * 1024)
        self.assertNotIn("order", {json.loads(item)["method"] for item in socket.sent})

    async def test_event_transport_failure_closes_socket_and_clears_subscription(self):
        socket = FakeSocket(
            json.dumps({"id": "request-1", "status": 200, "result": {"subscriptionId": 7}}),
            TimeoutError(),
        )
        stream = BinanceTestnetUserDataStream(
            "testnet-readonly",
            provider=provider(),
            clock=FixedClock(),
            websocket_factory=lambda _url, **_kwargs: socket,
            request_id_factory=lambda: "request-1",
        )
        await stream.connect()

        with self.assertRaisesRegex(BinanceTestnetUserStreamError, "USER_STREAM_EVENT_INVALID"):
            await stream.recv_execution_report()
        self.assertTrue(socket.closed)
        with self.assertRaisesRegex(BinanceTestnetUserStreamError, "USER_STREAM_NOT_CONNECTED"):
            await stream.recv_execution_report()

    async def test_library_specific_close_exception_still_fails_closed(self):
        # A real disconnect can surface as websockets.exceptions.ConnectionClosedError,
        # which is Exception-derived but NOT an OSError/TimeoutError/ValueError/TypeError
        # (observed live against the real testnet: it escaped uncaught before this fix).
        from websockets.exceptions import ConnectionClosedError

        socket = FakeSocket(
            json.dumps({"id": "request-1", "status": 200, "result": {"subscriptionId": 7}}),
            ConnectionClosedError(None, None),
        )
        stream = BinanceTestnetUserDataStream(
            "testnet-readonly",
            provider=provider(),
            clock=FixedClock(),
            websocket_factory=lambda _url, **_kwargs: socket,
            request_id_factory=lambda: "request-1",
        )
        await stream.connect()

        with self.assertRaisesRegex(BinanceTestnetUserStreamError, "USER_STREAM_EVENT_INVALID"):
            await stream.recv_execution_report()
        self.assertTrue(socket.closed)

    async def test_order_list_library_specific_close_exception_still_fails_closed(self):
        from websockets.exceptions import ConnectionClosedError

        socket = FakeSocket(
            json.dumps({"id": "request-1", "status": 200, "result": {"subscriptionId": 7}}),
            ConnectionClosedError(None, None),
        )
        stream = BinanceTestnetUserDataStream(
            "testnet-readonly",
            provider=provider(),
            clock=FixedClock(),
            websocket_factory=lambda _url, **_kwargs: socket,
            request_id_factory=lambda: "request-1",
        )
        await stream.connect()

        with self.assertRaisesRegex(BinanceTestnetUserStreamError, "USER_STREAM_EVENT_INVALID"):
            await stream.recv_order_list_event()
        self.assertTrue(socket.closed)

    async def test_signed_order_status_lookup_is_read_only_and_redacted(self):
        socket = FakeSocket(
            json.dumps({
                "id": "request-1",
                "status": 200,
                "result": {"symbol": "BTCUSDT", "orderId": 777, "status": "FILLED"},
            })
        )

        result = await query_binance_testnet_order_status(
            "testnet-readonly",
            "BTCUSDT",
            777,
            provider=provider(),
            clock=FixedClock(),
            websocket_factory=lambda _url, **_kwargs: socket,
            request_id_factory=lambda: "request-1",
        )

        self.assertEqual(result, OrderLookup.found(777))
        request = json.loads(socket.sent[0])
        self.assertEqual(request["method"], "order.status")
        self.assertEqual(request["params"]["symbol"], "BTCUSDT")
        self.assertEqual(request["params"]["orderId"], 777)
        self.assertNotIn("dummy-secret", socket.sent[0])
        self.assertTrue(socket.closed)

    async def test_order_status_identity_mismatch_fails_closed(self):
        socket = FakeSocket(
            json.dumps({
                "id": "request-1",
                "status": 200,
                "result": {"symbol": "BTCUSDT", "orderId": 778},
            })
        )

        with self.assertRaisesRegex(BinanceTestnetUserStreamError, "ORDER_STATUS_RESPONSE_INVALID"):
            await query_binance_testnet_order_status(
                "testnet-readonly",
                "BTCUSDT",
                777,
                provider=provider(),
                clock=FixedClock(),
                websocket_factory=lambda _url, **_kwargs: socket,
                request_id_factory=lambda: "request-1",
            )
        self.assertTrue(socket.closed)


if __name__ == "__main__":
    unittest.main()
