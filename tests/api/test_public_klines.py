"""AB.0: GET /api/public/klines -- credential-free live candles in the
historical-chart bar shape, so charts never depend on a downloaded dataset."""
import json
import time
import unittest

from starlette.responses import Response

import dcabot.server.api as api
from dcabot.data_adapters.binance_public_transport import BinancePublicKline


def _kline(open_us: int, close_us: int, close: str = "101") -> BinancePublicKline:
    return BinancePublicKline(
        open_time_us=open_us,
        close_time_us=close_us,
        open="100",
        high="102",
        low="99",
        close=close,
        base_volume="7.5",
    )


class PublicKlinesApiTests(unittest.TestCase):
    def setUp(self):
        self._original = api.fetch_binance_public_klines

    def tearDown(self):
        api.fetch_binance_public_klines = self._original

    def test_returns_exact_bars_in_chart_shape(self):
        calls: list[tuple] = []

        def spy(symbol, *, interval, limit, allowed_symbols):
            calls.append((symbol, interval, limit, allowed_symbols))
            return (_kline(0, 3_599_999_999), _kline(3_600_000_000, 7_199_999_999, "100.00000001"))

        api.fetch_binance_public_klines = spy
        response = Response()

        result = api.get_binance_public_klines("BTCUSDT", response, interval="1h", limit=2)

        data = result["data"]
        self.assertEqual(data["symbol"], "BTCUSDT")
        self.assertEqual(data["interval"], "1h")
        self.assertEqual(
            data["bars"][1],
            {
                "bar_index": 2,
                "open_time_us": 3_600_000_000,
                "close_time_us": 7_199_999_999,
                "open": "100",
                "high": "102",
                "low": "99",
                "close": "100.00000001",
                "base_volume": "7.5",
            },
        )
        self.assertEqual(data["bars"][0]["bar_index"], 1)
        self.assertIs(data["last_bar_closed"], True)
        self.assertIs(data["read_only"], True)
        self.assertIs(data["credential_required"], False)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(calls, [("BTCUSDT", "1h", 2, frozenset({"BTCUSDT"}))])

    def test_forming_last_bar_is_flagged_open(self):
        now_us = time.time_ns() // 1000
        api.fetch_binance_public_klines = lambda *a, **k: (_kline(now_us - 1000, now_us + 3_600_000_000),)
        result = api.get_binance_public_klines("BTCUSDT", Response(), interval="1h", limit=1)
        self.assertIs(result["data"]["last_bar_closed"], False)

    def test_empty_venue_answer_is_honest_empty(self):
        api.fetch_binance_public_klines = lambda *a, **k: ()
        result = api.get_binance_public_klines("BTCUSDT", Response(), interval="1h", limit=5)
        self.assertEqual(result["data"]["bars"], [])
        self.assertIs(result["data"]["last_bar_closed"], False)

    def test_invalid_query_is_422_without_touching_transport(self):
        calls: list[tuple] = []
        api.fetch_binance_public_klines = lambda *a, **k: calls.append((a, k)) or ()
        cases = [
            ("btcusdt", "1h", 10, "symbol"),
            ("BTCUSDT", "1M", 10, "interval"),
            ("BTCUSDT", "7m", 10, "interval"),
            ("BTCUSDT", "1h", 0, "limit"),
            ("BTCUSDT", "1h", 1001, "limit"),
        ]
        for symbol, interval, limit, field in cases:
            with self.subTest(symbol=symbol, interval=interval, limit=limit):
                result = api.get_binance_public_klines(symbol, Response(), interval=interval, limit=limit)
                self.assertEqual(result.status_code, 422)
                self.assertIn(field, json.loads(result.body)["error"]["fields"])
        self.assertEqual(calls, [])

    def test_transport_failure_is_a_bounded_502(self):
        def fail(*args, **kwargs):
            raise api.BinancePublicTransportError("PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı.")

        api.fetch_binance_public_klines = fail
        result = api.get_binance_public_klines("BTCUSDT", Response(), interval="1h", limit=5)
        self.assertEqual(result.status_code, 502)
        self.assertIn("PUBLIC_UPSTREAM_UNAVAILABLE", json.loads(result.body)["error"]["fields"]["market"])


if __name__ == "__main__":
    unittest.main()
