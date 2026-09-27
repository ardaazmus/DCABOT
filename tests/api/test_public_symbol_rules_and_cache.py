"""W-F2 follow-up: GET /api/public/symbol-rules (bot support decided by the
backend's own rule) and the bounded exchange-symbols cache."""
import json
import unittest
from unittest import mock

from starlette.responses import Response

import dcabot.server.api as api
from dcabot.data_adapters.binance_public_transport import (
    BinancePublicListedSymbol,
    BinancePublicSymbolRules,
    BinancePublicTransportError,
)


def _rules(symbol="BTCUSDT", status="TRADING", base="BTC", quote="USDT"):
    return BinancePublicSymbolRules(symbol, status, base, quote, "0.01", "0.00001", "0.00001", "5")


class SymbolRulesApiTests(unittest.TestCase):
    def test_bot_support_follows_the_sector_dca_rule(self):
        cases = [
            (_rules(), True, None),
            (_rules("BTCUSDC", quote="USDC"), False, "QUOTE_UNSUPPORTED"),
            (_rules(status="BREAK"), False, "NOT_TRADING"),
        ]
        for rules, supported, reason in cases:
            with self.subTest(symbol=rules.symbol, status=rules.status):
                with mock.patch.object(api, "fetch_binance_public_symbol_rules", return_value=rules):
                    result = api.get_binance_public_symbol_rules(rules.symbol, Response())
                self.assertEqual((result.data.bot_supported, result.data.bot_unsupported_reason), (supported, reason))
                self.assertEqual(result.data.min_notional, "5")

    def test_upstream_failure_is_502_problem(self):
        error = BinancePublicTransportError("PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı.")
        with mock.patch.object(api, "fetch_binance_public_symbol_rules", side_effect=error):
            result = api.get_binance_public_symbol_rules("BTCUSDT", Response())
        self.assertEqual((result.status_code, json.loads(result.body)["code"]), (502, "PUBLIC_UPSTREAM_UNAVAILABLE"))


class ExchangeSymbolsCacheTests(unittest.TestCase):
    def setUp(self):
        api._exchange_symbols_cache = None
        self.calls = 0

        def fetch():
            self.calls += 1
            return (BinancePublicListedSymbol("BTCUSDT", "TRADING", "BTC", "USDT"),)

        self.fetch = fetch

    def tearDown(self):
        api._exchange_symbols_cache = None

    def test_second_request_within_ttl_reuses_the_list_and_its_fetch_time(self):
        with mock.patch.object(api, "fetch_binance_public_exchange_symbols", self.fetch):
            first = api.get_binance_public_exchange_symbols(Response())
            second = api.get_binance_public_exchange_symbols(Response())
        self.assertEqual(self.calls, 1)
        self.assertEqual(first.observed_at_us, second.observed_at_us)
        self.assertEqual(second.count, 1)

    def test_expired_entry_is_refetched(self):
        with mock.patch.object(api, "fetch_binance_public_exchange_symbols", self.fetch):
            api.get_binance_public_exchange_symbols(Response())
            with mock.patch.object(api.time, "monotonic", return_value=api.time.monotonic() + api.EXCHANGE_SYMBOLS_TTL_SECONDS + 1):
                api.get_binance_public_exchange_symbols(Response())
        self.assertEqual(self.calls, 2)

    def test_failures_are_never_cached(self):
        error = BinancePublicTransportError("PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı.")
        with mock.patch.object(api, "fetch_binance_public_exchange_symbols", side_effect=error):
            self.assertEqual(api.get_binance_public_exchange_symbols(Response()).status_code, 503)
        with mock.patch.object(api, "fetch_binance_public_exchange_symbols", self.fetch):
            self.assertEqual(api.get_binance_public_exchange_symbols(Response()).count, 1)
        self.assertEqual(self.calls, 1)


if __name__ == "__main__":
    unittest.main()
