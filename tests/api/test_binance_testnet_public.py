import json
import unittest
from dataclasses import replace
from datetime import datetime
from starlette.responses import Response

import dcabot.server.api as api
from dcabot.data_adapters.binance_testnet_public import BinanceTestnetExchangeInfoSnapshot


def _snapshot() -> BinanceTestnetExchangeInfoSnapshot:
    return BinanceTestnetExchangeInfoSnapshot(
        environment="BINANCE_SPOT_TESTNET",
        symbol="BTCUSDT",
        status="TRADING",
        base_asset="BTC",
        quote_asset="USDT",
        permissions=("SPOT",),
        permission_sets=(("SPOT",),),
        order_types=("LIMIT", "MARKET"),
        filters=({"filterType": "PRICE_FILTER", "minPrice": "0.01000000"},),
        exchange_filters=(),
        rate_limits=({"rateLimitType": "REQUEST_WEIGHT", "limit": "6000"},),
        response_sha256="a" * 64,
        observed_at_us=1_700_000_000_000_000,
    )


class BinanceTestnetPublicApiTests(unittest.TestCase):
    def setUp(self):
        self.original_fetch = api.fetch_binance_testnet_exchange_info
        api.fetch_binance_testnet_exchange_info = lambda symbol: replace(_snapshot(), symbol=symbol)

    def tearDown(self):
        api.fetch_binance_testnet_exchange_info = self.original_fetch

    def test_snapshot_is_read_only_and_has_no_credentials(self):
        response = Response()

        result = api.get_binance_testnet_exchange_info("BTCUSDT", response).model_dump(mode="json")

        self.assertEqual(result["environment"], "BINANCE_SPOT_TESTNET")
        self.assertEqual(result["read_only"], True)
        self.assertEqual(result["credential_required"], False)
        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["order_types"], ["LIMIT", "MARKET"])
        self.assertNotIn("api_key", json.dumps(result).lower())
        self.assertNotIn("secret", json.dumps(result).lower())
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_upstream_failures_map_to_sanitized_problem_details(self):
        cases = (
            ("TESTNET_SYMBOL_NOT_FOUND", 404),
            ("TESTNET_RESPONSE_INVALID", 502),
            ("TESTNET_RESPONSE_TOO_LARGE", 502),
            ("TESTNET_UPSTREAM_UNAVAILABLE", 503),
        )

        for code, status_code in cases:
            with self.subTest(code=code):
                failure = api.BinanceTestnetPublicError(
                    code, "secret=must-not-cross-the-api-boundary"
                )

                def fail(_symbol: str, *, failure=failure):
                    raise failure

                api.fetch_binance_testnet_exchange_info = fail
                response = Response()
                result = api.get_binance_testnet_exchange_info("BTCUSDT", response)

                self.assertEqual(result.status_code, status_code)
                body = json.loads(result.body)
                self.assertEqual(body["code"], code)
                self.assertNotIn("secret", json.dumps(body).lower())
                self.assertNotIn("must-not-cross", json.dumps(body))
                self.assertEqual(result.media_type, "application/problem+json")
