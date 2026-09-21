import asyncio
import json
import unittest
import urllib.error
from urllib.request import Request

from dcabot.data_adapters.binance_public import BinanceTimeUnit
from dcabot.data_adapters.binance_public_transport import (
    BinancePublicTradeStream,
    BinancePublicTransportError,
    fetch_binance_public_trades,
)

REST_RECORDS = [
    {
        "id": 28457, "price": "50000.00", "qty": "0.001",
        "quoteQty": "50.00", "time": 1700000001000,
        "isBuyerMaker": False, "isBestMatch": True,
    },
    {
        "id": 28458, "price": "49999.50", "qty": "0.002",
        "quoteQty": "99.999", "time": 1700000002000,
        "isBuyerMaker": True, "isBestMatch": True,
    },
]

WS_TRADE = {
    "e": "trade", "E": 1700000001000, "s": "BTCUSDT", "t": 12345,
    "p": "50000.00", "q": "0.001", "T": 1700000001000, "m": False,
}


class _FakeResponse:
    def __init__(self, status, body, headers=None):
        self.status = status
        self._body = body
        self.headers = headers or {}
        self.closed = False

    def read(self, size=-1):
        data = self._body[:size] if size is not None and size >= 0 else self._body
        self._body = self._body[len(data):]
        return data

    def close(self):
        self.closed = True


class _FakeOpener:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request.full_url, timeout))
        if self.error is not None:
            raise self.error
        return self.response


def _rest(**overrides):
    params = {
        "symbol": "BTCUSDT",
        "limit": 2,
        "allowed_symbols": frozenset({"BTCUSDT"}),
        "receive_time_us": 1700000003000000,
        "processing_time_us": 1700000003000100,
        "time_unit": BinanceTimeUnit.MILLISECONDS,
    }
    params.update(overrides)
    return params


class FetchBinancePublicTradesTests(unittest.TestCase):
    def test_records_normalize_to_exact_canonical_observations(self):
        body = json.dumps(REST_RECORDS).encode()
        opener = _FakeOpener(_FakeResponse(200, body))
        result = fetch_binance_public_trades(**_rest(), opener=opener)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].event_id, "28457")
        self.assertEqual(result[0].price, "50000")
        self.assertEqual(result[0].quantity, "0.001")
        self.assertEqual(result[0].transport, "REST")
        self.assertEqual(result[1].price, "49999.5")
        self.assertIn("symbol=BTCUSDT", opener.requests[0][0])
        self.assertIn("limit=2", opener.requests[0][0])

    def test_non_200_is_http_error(self):
        opener = _FakeOpener(_FakeResponse(429, b"{}"))
        with self.assertRaises(BinancePublicTransportError) as ctx:
            fetch_binance_public_trades(**_rest(), opener=opener)
        self.assertEqual(ctx.exception.code, "PUBLIC_UPSTREAM_HTTP_ERROR")

    def test_network_error_is_unavailable(self):
        opener = _FakeOpener(error=urllib.error.URLError("down"))
        with self.assertRaises(BinancePublicTransportError) as ctx:
            fetch_binance_public_trades(**_rest(), opener=opener)
        self.assertEqual(ctx.exception.code, "PUBLIC_UPSTREAM_UNAVAILABLE")

    def test_malformed_json_is_invalid(self):
        opener = _FakeOpener(_FakeResponse(200, b"{nope"))
        with self.assertRaises(BinancePublicTransportError) as ctx:
            fetch_binance_public_trades(**_rest(), opener=opener)
        self.assertEqual(ctx.exception.code, "PUBLIC_RESPONSE_INVALID")

    def test_non_list_json_is_invalid(self):
        opener = _FakeOpener(_FakeResponse(200, b'{"id": 1}'))
        with self.assertRaises(BinancePublicTransportError) as ctx:
            fetch_binance_public_trades(**_rest(), opener=opener)
        self.assertEqual(ctx.exception.code, "PUBLIC_RESPONSE_INVALID")

    def test_bad_record_fails_the_whole_batch(self):
        bad = [dict(REST_RECORDS[0])]
        del bad[0]["price"]
        opener = _FakeOpener(_FakeResponse(200, json.dumps(bad).encode()))
        with self.assertRaises(BinancePublicTransportError) as ctx:
            fetch_binance_public_trades(**_rest(limit=1), opener=opener)
        self.assertEqual(ctx.exception.code, "PUBLIC_UPSTREAM_RECORD_INVALID")

    def test_symbol_outside_allowlist_rejected(self):
        opener = _FakeOpener(_FakeResponse(200, b"[]"))
        with self.assertRaises(BinancePublicTransportError) as ctx:
            fetch_binance_public_trades(
                **_rest(allowed_symbols=frozenset({"ETHUSDT"})), opener=opener
            )
        self.assertEqual(ctx.exception.code, "PUBLIC_SYMBOL_NOT_ALLOWED")

    def test_limit_bounds_rejected(self):
        opener = _FakeOpener(_FakeResponse(200, b"[]"))
        for bad in (0, 1001, "10"):
            with self.assertRaises(BinancePublicTransportError) as ctx:
                fetch_binance_public_trades(**_rest(limit=bad), opener=opener)
            self.assertEqual(ctx.exception.code, "PUBLIC_LIMIT_INVALID")

    def test_oversized_response_rejected(self):
        big = b"x" * (256 * 1024 + 1)
        opener = _FakeOpener(_FakeResponse(200, big))
        with self.assertRaises(BinancePublicTransportError) as ctx:
            fetch_binance_public_trades(**_rest(), opener=opener)
        self.assertEqual(ctx.exception.code, "PUBLIC_RESPONSE_TOO_LARGE")


class _FakeSocket:
    def __init__(self, frames=None, error=None):
        self.frames = list(frames or [])
        self.error = error
        self.closed = False
        self.sent = []

    async def send(self, message):
        self.sent.append(message)

    async def recv(self):
        if self.error is not None:
            raise self.error
        if not self.frames:
            raise asyncio.TimeoutError()
        return self.frames.pop(0)

    async def close(self):
        self.closed = True


class _FakeFactory:
    def __init__(self, socket):
        self.socket = socket
        self.urls = []

    async def __call__(self, url, **kwargs):
        self.urls.append(url)
        return self.socket


class BinancePublicTradeStreamTests(unittest.IsolatedAsyncioTestCase):
    def _stream(self, socket, **overrides):
        params = {
            "symbol": "BTCUSDT",
            "allowed_symbols": frozenset({"BTCUSDT"}),
            "time_unit": BinanceTimeUnit.MILLISECONDS,
            "clock": lambda: 1700000003000000000,
        }
        params.update(overrides)
        return BinancePublicTradeStream(
            params.pop("symbol"), websocket_factory=_FakeFactory(socket), **params
        )

    async def test_connect_uses_public_stream_url(self):
        stream = self._stream(_FakeSocket())
        await stream.connect()
        factory = stream._websocket_factory
        self.assertEqual(len(factory.urls), 1)
        self.assertIn("btcusdt@trade", factory.urls[0])
        self.assertNotIn("testnet", factory.urls[0])
        await stream.close()

    async def test_recv_yields_canonical_observation(self):
        stream = self._stream(_FakeSocket([json.dumps(WS_TRADE)]))
        await stream.connect()
        obs = await stream.recv_observation()
        self.assertEqual(obs.event_id, "12345")
        self.assertEqual(obs.price, "50000")
        self.assertEqual(obs.transport, "WEBSOCKET")
        self.assertEqual(obs.receive_time_us, 1700000003000000)
        self.assertEqual(obs.processing_time_us, 1700000003000000)
        await stream.close()

    async def test_garbage_frame_fails_closed(self):
        stream = self._stream(_FakeSocket(["{nope"]))
        await stream.connect()
        with self.assertRaises(BinancePublicTransportError) as ctx:
            await stream.recv_observation()
        self.assertEqual(ctx.exception.code, "PUBLIC_STREAM_FRAME_INVALID")
        await stream.close()

    async def test_timeout_is_unavailable(self):
        stream = self._stream(_FakeSocket())
        await stream.connect()
        with self.assertRaises(BinancePublicTransportError) as ctx:
            await stream.recv_observation()
        self.assertEqual(ctx.exception.code, "PUBLIC_STREAM_UNAVAILABLE")
        await stream.close()

    async def test_library_close_error_still_fails_closed(self):
        stream = self._stream(_FakeSocket(error=ConnectionError("boom")))
        await stream.connect()
        with self.assertRaises(BinancePublicTransportError) as ctx:
            await stream.recv_observation()
        self.assertEqual(ctx.exception.code, "PUBLIC_STREAM_UNAVAILABLE")
        await stream.close()

    async def test_recv_before_connect_rejected(self):
        stream = self._stream(_FakeSocket())
        with self.assertRaises(BinancePublicTransportError) as ctx:
            await stream.recv_observation()
        self.assertEqual(ctx.exception.code, "PUBLIC_STREAM_NOT_CONNECTED")

    async def test_double_connect_rejected(self):
        stream = self._stream(_FakeSocket())
        await stream.connect()
        with self.assertRaises(BinancePublicTransportError) as ctx:
            await stream.connect()
        self.assertEqual(ctx.exception.code, "PUBLIC_STREAM_ALREADY_CONNECTED")
        await stream.close()


if __name__ == "__main__":
    unittest.main()
