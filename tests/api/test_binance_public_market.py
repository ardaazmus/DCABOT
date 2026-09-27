import json
import unittest
from starlette.responses import Response

import dcabot.server.api as api
from dcabot.data_adapters.binance_public_transport import (
    BinancePublic24hTicker,
    BinancePublicListedSymbol,
)
from dcabot.data_adapters.public_feed import PublicObservation


def _listed() -> tuple[BinancePublicListedSymbol, ...]:
    return (
        BinancePublicListedSymbol(
            symbol="BTCUSDT", status="TRADING", base_asset="BTC", quote_asset="USDT"
        ),
        BinancePublicListedSymbol(
            symbol="ETHUSDT", status="BREAK", base_asset="ETH", quote_asset="USDT"
        ),
    )


def _observation() -> PublicObservation:
    return PublicObservation(
        source_id="binance-spot-public",
        transport="REST",
        symbol="BTCUSDT",
        product="SPOT",
        event_id="28457",
        event_time_us=1_700_000_001_000_000,
        receive_time_us=1_700_000_003_000_000,
        processing_time_us=1_700_000_003_000_100,
        price="50000",
        quantity="0.001",
        payload_hash="b" * 64,
        source_sequence=28457,
    )


class BinancePublicMarketApiTests(unittest.TestCase):
    def setUp(self):
        self.original_symbols = api.fetch_binance_public_exchange_symbols
        self.original_trades = api.fetch_binance_public_trades
        self.original_ticker = api.fetch_binance_public_24hr_ticker
        api.fetch_binance_public_exchange_symbols = lambda: _listed()
        api.fetch_binance_public_trades = lambda *args, **kwargs: (_observation(),)
        api.fetch_binance_public_24hr_ticker = lambda *args, **kwargs: BinancePublic24hTicker(
            symbol="BTCUSDT", last_price="50000", price_change_percent="-1.23", quote_volume="1234567.89",
        )

    def tearDown(self):
        api.fetch_binance_public_exchange_symbols = self.original_symbols
        api.fetch_binance_public_trades = self.original_trades
        api.fetch_binance_public_24hr_ticker = self.original_ticker

    def test_symbol_list_is_read_only_and_counted(self):
        response = Response()

        result = api.get_binance_public_exchange_symbols(response).model_dump(mode="json")

        self.assertEqual(result["environment"], "BINANCE_SPOT")
        self.assertEqual(result["count"], 2)
        self.assertEqual(len(result["symbols"]), 2)
        self.assertEqual(result["symbols"][0]["symbol"], "BTCUSDT")
        self.assertEqual(result["symbols"][1]["status"], "BREAK")
        self.assertEqual(result["read_only"], True)
        self.assertEqual(result["credential_required"], False)
        self.assertGreaterEqual(result["observed_at_us"], 0)
        self.assertNotIn("secret", json.dumps(result).lower())
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_symbol_list_failures_map_to_sanitized_problem_details(self):
        cases = (
            ("PUBLIC_RESPONSE_INVALID", 502),
            ("PUBLIC_RESPONSE_TOO_LARGE", 502),
            ("PUBLIC_ENCODING_INVALID", 502),
            ("PUBLIC_UPSTREAM_HTTP_ERROR", 503),
            ("PUBLIC_UPSTREAM_UNAVAILABLE", 503),
        )

        for code, status_code in cases:
            with self.subTest(code=code):
                failure = api.BinancePublicTransportError(
                    code, "secret=must-not-cross-the-api-boundary"
                )

                def fail(*args, _failure=failure, **kwargs):
                    raise _failure

                api.fetch_binance_public_exchange_symbols = fail
                response = Response()
                result = api.get_binance_public_exchange_symbols(response)

                self.assertEqual(result.status_code, status_code)
                body = json.loads(result.body)
                self.assertEqual(body["code"], code)
                self.assertNotIn("secret", json.dumps(body).lower())
                self.assertNotIn("must-not-cross", json.dumps(body))
                self.assertEqual(result.media_type, "application/problem+json")

    def test_last_price_passes_the_exact_print_through(self):
        response = Response()

        result = api.get_binance_public_last_price("BTCUSDT", response).model_dump(mode="json")

        self.assertEqual(result["environment"], "BINANCE_SPOT")
        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["price"], "50000")
        self.assertEqual(result["event_id"], "28457")
        self.assertEqual(result["event_time_us"], 1_700_000_001_000_000)
        self.assertEqual(result["read_only"], True)
        self.assertEqual(result["credential_required"], False)
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_last_price_rejects_malformed_symbol_without_touching_transport(self):
        calls: list[tuple] = []

        def spy(*args, **kwargs):
            calls.append((args, kwargs))
            return (_observation(),)

        api.fetch_binance_public_trades = spy
        for bad in ("btcusdt", "BTC USDT", "BTCUSDT!", "", "A" * 21):
            with self.subTest(symbol=bad):
                response = Response()
                result = api.get_binance_public_last_price(bad, response)

                self.assertEqual(result.status_code, 422)
                body = json.loads(result.body)
                self.assertIn("symbol", body["error"]["fields"])
        self.assertEqual(calls, [])

    def test_last_price_without_trades_is_a_404_not_an_invented_price(self):
        api.fetch_binance_public_trades = lambda *args, **kwargs: ()
        response = Response()

        result = api.get_binance_public_last_price("BTCUSDT", response)

        self.assertEqual(result.status_code, 404)
        body = json.loads(result.body)
        self.assertEqual(body["code"], "PUBLIC_SYMBOL_NO_TRADES")

    def test_last_price_transport_failure_is_a_bounded_502(self):
        # Transport messages are static Turkish literals (no upstream bytes),
        # so the handler only ever forwards the bounded code/message pair.
        failure = api.BinancePublicTransportError(
            "PUBLIC_UPSTREAM_HTTP_ERROR", "Public market-data HTTP yanıtı başarılı değil."
        )

        def fail(*args, **kwargs):
            raise failure

        api.fetch_binance_public_trades = fail
        response = Response()

        result = api.get_binance_public_last_price("BTCUSDT", response)

        self.assertEqual(result.status_code, 502)
        body = json.loads(result.body)
        self.assertIn("PUBLIC_UPSTREAM_HTTP_ERROR", body["error"]["message"])
        self.assertIn("PUBLIC_UPSTREAM_HTTP_ERROR", body["error"]["fields"]["market"])


    def test_24h_ticker_passes_the_exact_stats_through(self):
        response = Response()

        result = api.get_binance_public_24h_ticker("BTCUSDT", response).model_dump(mode="json")

        self.assertEqual(result["environment"], "BINANCE_SPOT")
        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["last_price"], "50000")
        self.assertEqual(result["price_change_percent"], "-1.23")
        self.assertEqual(result["quote_volume"], "1234567.89")
        self.assertEqual(result["read_only"], True)
        self.assertEqual(result["credential_required"], False)
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_24h_ticker_rejects_malformed_symbol_without_touching_transport(self):
        calls: list[tuple] = []

        def spy(*args, **kwargs):
            calls.append((args, kwargs))
            return BinancePublic24hTicker(
                symbol="BTCUSDT", last_price="1", price_change_percent="0", quote_volume="0",
            )

        api.fetch_binance_public_24hr_ticker = spy
        for bad in ("btcusdt", "BTC USDT", "BTCUSDT!", "", "A" * 21):
            with self.subTest(symbol=bad):
                response = Response()
                result = api.get_binance_public_24h_ticker(bad, response)

                self.assertEqual(result.status_code, 422)
                body = json.loads(result.body)
                self.assertIn("symbol", body["error"]["fields"])
        self.assertEqual(calls, [])

    def test_24h_ticker_transport_failure_is_a_bounded_502(self):
        failure = api.BinancePublicTransportError(
            "PUBLIC_UPSTREAM_HTTP_ERROR", "Public market-data HTTP yanıtı başarılı değil."
        )

        def fail(*args, **kwargs):
            raise failure

        api.fetch_binance_public_24hr_ticker = fail
        response = Response()

        result = api.get_binance_public_24h_ticker("BTCUSDT", response)

        self.assertEqual(result.status_code, 502)
        body = json.loads(result.body)
        self.assertIn("PUBLIC_UPSTREAM_HTTP_ERROR", body["error"]["message"])


if __name__ == "__main__":
    unittest.main()
