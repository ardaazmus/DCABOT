import json
import os
import unittest

from dcabot.application.credential_boundary import CredentialMaterial, EphemeralCredentialProvider
from dcabot.application.signed_request import ApiKeyType
from dcabot.data_adapters.binance_testnet_order_execution import (
    BinanceTestnetOrderExecutionError,
    TRADING_ENABLED_ENV_VAR,
    cancel_binance_testnet_order,
    place_binance_testnet_limit_order,
    trading_kill_switch_enabled,
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


def _place_response(*, order_id=999, client_order_id="attempt-1") -> str:
    return json.dumps(
        {
            "id": "request-1",
            "status": 200,
            "result": {
                "symbol": "BTCUSDT",
                "orderId": order_id,
                "clientOrderId": client_order_id,
                "status": "NEW",
                "transactTime": 1_700_000_000_001,
            },
        }
    )


def _cancel_response(*, order_id=999, client_order_id="attempt-1") -> str:
    return json.dumps(
        {
            "id": "request-1",
            "status": 200,
            "result": {
                "symbol": "BTCUSDT",
                "orderId": order_id,
                "clientOrderId": client_order_id,
                "status": "CANCELED",
            },
        }
    )


class KillSwitchTests(unittest.TestCase):
    def test_default_is_off(self):
        os.environ.pop(TRADING_ENABLED_ENV_VAR, None)
        self.assertFalse(trading_kill_switch_enabled())

    def test_only_exact_string_true_opens_it(self):
        os.environ[TRADING_ENABLED_ENV_VAR] = "1"
        self.assertFalse(trading_kill_switch_enabled())
        os.environ[TRADING_ENABLED_ENV_VAR] = "True"
        self.assertFalse(trading_kill_switch_enabled())
        os.environ[TRADING_ENABLED_ENV_VAR] = "true"
        self.assertTrue(trading_kill_switch_enabled())
        os.environ.pop(TRADING_ENABLED_ENV_VAR, None)


class PlaceOrderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        os.environ.pop(TRADING_ENABLED_ENV_VAR, None)

    def tearDown(self):
        os.environ.pop(TRADING_ENABLED_ENV_VAR, None)

    async def test_kill_switch_off_blocks_placement_before_any_network_call(self):
        with self.assertRaisesRegex(BinanceTestnetOrderExecutionError, "TRADING_KILL_SWITCH_OFF"):
            await place_binance_testnet_limit_order(
                "testnet-readonly",
                "BTCUSDT",
                "BUY",
                "0.001",
                "50000",
                "attempt-1",
                provider=_provider(),
                clock=FixedClock(),
                websocket_factory=lambda _url, **_kwargs: (_ for _ in ()).throw(
                    AssertionError("network must not be reached when kill switch is off")
                ),
            )

    async def test_placement_succeeds_when_kill_switch_is_on(self):
        os.environ[TRADING_ENABLED_ENV_VAR] = "true"
        socket = FakeSocket(_place_response())

        result = await place_binance_testnet_limit_order(
            "testnet-readonly",
            "BTCUSDT",
            "BUY",
            "0.001",
            "50000",
            "attempt-1",
            provider=_provider(),
            clock=FixedClock(),
            websocket_factory=lambda _url, **_kwargs: socket,
            request_id_factory=lambda: "request-1",
        )

        self.assertEqual(result.order_id, 999)
        self.assertEqual(result.client_order_id, "attempt-1")
        self.assertEqual(result.status, "NEW")
        request = json.loads(socket.sent[0])
        self.assertEqual(request["method"], "order.place")
        self.assertEqual(request["params"]["type"], "LIMIT")
        self.assertEqual(request["params"]["timeInForce"], "GTC")
        self.assertEqual(request["params"]["side"], "BUY")
        self.assertNotIn("dummy-secret", socket.sent[0])
        self.assertTrue(socket.closed)

    async def test_market_side_or_type_cannot_be_requested(self):
        os.environ[TRADING_ENABLED_ENV_VAR] = "true"

        with self.assertRaisesRegex(BinanceTestnetOrderExecutionError, "ORDER_SIDE_INVALID"):
            await place_binance_testnet_limit_order(
                "testnet-readonly",
                "BTCUSDT",
                "MARKET_BUY",
                "0.001",
                "50000",
                "attempt-1",
                provider=_provider(),
                clock=FixedClock(),
                websocket_factory=lambda _url, **_kwargs: None,
            )

    async def test_rejected_request_fails_closed(self):
        os.environ[TRADING_ENABLED_ENV_VAR] = "true"
        socket = FakeSocket(
            json.dumps({"id": "request-1", "status": 400, "error": {"code": -1013, "msg": "Filter failure."}})
        )

        with self.assertRaisesRegex(BinanceTestnetOrderExecutionError, "ORDER_REQUEST_REJECTED"):
            await place_binance_testnet_limit_order(
                "testnet-readonly",
                "BTCUSDT",
                "BUY",
                "0.001",
                "50000",
                "attempt-1",
                provider=_provider(),
                clock=FixedClock(),
                websocket_factory=lambda _url, **_kwargs: socket,
                request_id_factory=lambda: "request-1",
            )


class CancelOrderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        os.environ.pop(TRADING_ENABLED_ENV_VAR, None)

    def tearDown(self):
        os.environ.pop(TRADING_ENABLED_ENV_VAR, None)

    async def test_kill_switch_off_blocks_cancel(self):
        with self.assertRaisesRegex(BinanceTestnetOrderExecutionError, "TRADING_KILL_SWITCH_OFF"):
            await cancel_binance_testnet_order(
                "testnet-readonly",
                "BTCUSDT",
                order_id=999,
                provider=_provider(),
                clock=FixedClock(),
                websocket_factory=lambda _url, **_kwargs: (_ for _ in ()).throw(
                    AssertionError("network must not be reached when kill switch is off")
                ),
            )

    async def test_cancel_by_order_id_succeeds(self):
        os.environ[TRADING_ENABLED_ENV_VAR] = "true"
        socket = FakeSocket(_cancel_response())

        result = await cancel_binance_testnet_order(
            "testnet-readonly",
            "BTCUSDT",
            order_id=999,
            provider=_provider(),
            clock=FixedClock(),
            websocket_factory=lambda _url, **_kwargs: socket,
            request_id_factory=lambda: "request-1",
        )

        self.assertEqual(result.status, "CANCELED")
        request = json.loads(socket.sent[0])
        self.assertEqual(request["method"], "order.cancel")
        self.assertEqual(request["params"]["orderId"], 999)
        self.assertNotIn("origClientOrderId", request["params"])

    async def test_cancel_requires_exactly_one_identity(self):
        os.environ[TRADING_ENABLED_ENV_VAR] = "true"

        with self.assertRaisesRegex(BinanceTestnetOrderExecutionError, "ORDER_CANCEL_IDENTITY_INVALID"):
            await cancel_binance_testnet_order(
                "testnet-readonly",
                "BTCUSDT",
                provider=_provider(),
                clock=FixedClock(),
                websocket_factory=lambda _url, **_kwargs: None,
            )

        with self.assertRaisesRegex(BinanceTestnetOrderExecutionError, "ORDER_CANCEL_IDENTITY_INVALID"):
            await cancel_binance_testnet_order(
                "testnet-readonly",
                "BTCUSDT",
                order_id=999,
                client_order_id="attempt-1",
                provider=_provider(),
                clock=FixedClock(),
                websocket_factory=lambda _url, **_kwargs: None,
            )


if __name__ == "__main__":
    unittest.main()
