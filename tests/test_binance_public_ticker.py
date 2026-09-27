"""Faz 17 AA.-1: 24h public ticker fetch (display-only, AA.2 market panel).
Same fake-opener pattern as test_binance_public_transport.py."""
import json
import unittest
import urllib.error

from dcabot.data_adapters.binance_public_transport import (
    MAX_TICKER_RESPONSE_BYTES,
    BinancePublicTransportError,
    fetch_binance_public_24hr_ticker,
)


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


TICKER_BODY = {
    "symbol": "BTCUSDT",
    "lastPrice": "50000.00",
    "priceChangePercent": "-1.23",
    "quoteVolume": "1234567.89",
}


class FetchBinancePublic24hTickerTests(unittest.TestCase):
    def test_valid_ticker_is_normalized(self):
        opener = _FakeOpener(_FakeResponse(200, json.dumps(TICKER_BODY).encode()))
        result = fetch_binance_public_24hr_ticker(
            "BTCUSDT", allowed_symbols=frozenset({"BTCUSDT"}), opener=opener
        )
        self.assertEqual(result.symbol, "BTCUSDT")
        self.assertEqual(result.last_price, "50000")
        self.assertEqual(result.price_change_percent, "-1.23")
        self.assertEqual(result.quote_volume, "1234567.89")

    def test_symbol_not_allowed_is_rejected(self):
        opener = _FakeOpener(_FakeResponse(200, b"{}"))
        with self.assertRaises(BinancePublicTransportError):
            fetch_binance_public_24hr_ticker(
                "ETHUSDT", allowed_symbols=frozenset({"BTCUSDT"}), opener=opener
            )
        self.assertEqual(opener.requests, [])

    def test_non_200_status_fails_closed(self):
        opener = _FakeOpener(_FakeResponse(429, b"{}"))
        with self.assertRaises(BinancePublicTransportError):
            fetch_binance_public_24hr_ticker(
                "BTCUSDT", allowed_symbols=frozenset({"BTCUSDT"}), opener=opener
            )

    def test_network_error_fails_closed(self):
        opener = _FakeOpener(error=urllib.error.URLError("down"))
        with self.assertRaises(BinancePublicTransportError):
            fetch_binance_public_24hr_ticker(
                "BTCUSDT", allowed_symbols=frozenset({"BTCUSDT"}), opener=opener
            )

    def test_bad_json_fails_closed(self):
        opener = _FakeOpener(_FakeResponse(200, b"{nope"))
        with self.assertRaises(BinancePublicTransportError):
            fetch_binance_public_24hr_ticker(
                "BTCUSDT", allowed_symbols=frozenset({"BTCUSDT"}), opener=opener
            )

    def test_symbol_mismatch_in_body_is_rejected(self):
        body = dict(TICKER_BODY)
        body["symbol"] = "ETHUSDT"
        opener = _FakeOpener(_FakeResponse(200, json.dumps(body).encode()))
        with self.assertRaises(BinancePublicTransportError):
            fetch_binance_public_24hr_ticker(
                "BTCUSDT", allowed_symbols=frozenset({"BTCUSDT"}), opener=opener
            )

    def test_non_positive_last_price_is_rejected(self):
        body = dict(TICKER_BODY)
        body["lastPrice"] = "0"
        opener = _FakeOpener(_FakeResponse(200, json.dumps(body).encode()))
        with self.assertRaises(BinancePublicTransportError):
            fetch_binance_public_24hr_ticker(
                "BTCUSDT", allowed_symbols=frozenset({"BTCUSDT"}), opener=opener
            )

    def test_negative_quote_volume_is_rejected(self):
        body = dict(TICKER_BODY)
        body["quoteVolume"] = "-5"
        opener = _FakeOpener(_FakeResponse(200, json.dumps(body).encode()))
        with self.assertRaises(BinancePublicTransportError):
            fetch_binance_public_24hr_ticker(
                "BTCUSDT", allowed_symbols=frozenset({"BTCUSDT"}), opener=opener
            )

    def test_oversized_response_fails_closed(self):
        big = json.dumps({**TICKER_BODY, "pad": "x" * MAX_TICKER_RESPONSE_BYTES}).encode()
        opener = _FakeOpener(_FakeResponse(200, big))
        with self.assertRaises(BinancePublicTransportError):
            fetch_binance_public_24hr_ticker(
                "BTCUSDT", allowed_symbols=frozenset({"BTCUSDT"}), opener=opener
            )

    def test_invalid_symbol_format_is_rejected(self):
        with self.assertRaises(BinancePublicTransportError):
            fetch_binance_public_24hr_ticker(
                "btcusdt", allowed_symbols=frozenset({"btcusdt"}), opener=_FakeOpener()
            )


if __name__ == "__main__":
    unittest.main()
