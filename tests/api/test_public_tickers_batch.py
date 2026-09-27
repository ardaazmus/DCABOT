"""W-F2 prerequisite: GET /api/public/tickers-24h — batch 24h stats for the market list."""
import json
import unittest

from starlette.responses import Response

import dcabot.server.api as api
from dcabot.data_adapters.binance_public_transport import (
    BinancePublic24hTicker,
    BinancePublicTransportError,
    fetch_binance_public_24hr_tickers,
)


class _Resp:
    def __init__(self, body):
        self.status = 200
        self._body = json.dumps(body).encode()
        self.headers = {}

    def read(self, size=-1):
        data, self._body = self._body[:size], self._body[size:]
        return data

    def close(self):
        pass


class _Opener:
    def __init__(self, body):
        self.body = body
        self.urls = []

    def open(self, request, timeout):
        self.urls.append(request.full_url)
        return _Resp(self.body)


def _row(symbol, price="1.5"):
    return {"symbol": symbol, "lastPrice": price, "priceChangePercent": "-1.2", "quoteVolume": "1000"}


class BatchTickerTransportTests(unittest.TestCase):
    def test_order_follows_request_not_venue(self):
        opener = _Opener([_row("BTCUSDT", "84000.10"), _row("ETHUSDT", "2600")])
        result = fetch_binance_public_24hr_tickers(("ETHUSDT", "BTCUSDT"), opener=opener)
        self.assertEqual([t.symbol for t in result], ["ETHUSDT", "BTCUSDT"])
        self.assertEqual(result[1].last_price, "84000.1")
        self.assertIn("symbols=%5B%22ETHUSDT%22%2C%22BTCUSDT%22%5D", opener.urls[0])

    def test_missing_extra_or_duplicate_entries_reject_the_batch(self):
        cases = {
            "missing": [_row("BTCUSDT")],
            "foreign": [_row("BTCUSDT"), _row("XRPUSDT")],
            "duplicate": [_row("BTCUSDT"), _row("BTCUSDT")],
        }
        for name, body in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(BinancePublicTransportError):
                    fetch_binance_public_24hr_tickers(("BTCUSDT", "ETHUSDT"), opener=_Opener(body))

    def test_bad_requests_fail_before_network(self):
        opener = _Opener([])
        for symbols in ((), tuple(f"S{i}USDT" for i in range(51)), ("btcusdt",), ("BTCUSDT", "BTCUSDT")):
            with self.subTest(n=len(symbols)):
                with self.assertRaises(BinancePublicTransportError):
                    fetch_binance_public_24hr_tickers(symbols, opener=opener)
        self.assertEqual(opener.urls, [])


class BatchTickerApiTests(unittest.TestCase):
    def setUp(self):
        self._original = api.fetch_binance_public_24hr_tickers

    def tearDown(self):
        api.fetch_binance_public_24hr_tickers = self._original

    def test_rows_pass_through_exactly(self):
        api.fetch_binance_public_24hr_tickers = lambda symbols: tuple(
            BinancePublic24hTicker(s, "1.25", "-3.5", "900") for s in symbols
        )
        result = api.get_binance_public_24h_tickers("BTCUSDT,ETHUSDT", Response())
        self.assertEqual([row.symbol for row in result.data], ["BTCUSDT", "ETHUSDT"])
        self.assertEqual(result.data[0].last_price, "1.25")
        self.assertTrue(result.read_only)

    def test_invalid_symbol_list_is_422_problem(self):
        for symbols in ("", "btcusdt", "BTCUSDT,BTCUSDT", ",".join(f"S{i}USDT" for i in range(51))):
            with self.subTest(symbols=symbols[:20]):
                result = api.get_binance_public_24h_tickers(symbols, Response())
                self.assertEqual(result.status_code, 422)
                self.assertEqual(json.loads(result.body)["code"], "REQUEST_VALIDATION_FAILED")

    def test_upstream_failure_is_502_problem(self):
        def fail(symbols):
            raise BinancePublicTransportError("PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı.")

        api.fetch_binance_public_24hr_tickers = fail
        result = api.get_binance_public_24h_tickers("BTCUSDT", Response())
        self.assertEqual((result.status_code, json.loads(result.body)["code"]), (502, "PUBLIC_UPSTREAM_UNAVAILABLE"))


if __name__ == "__main__":
    unittest.main()
