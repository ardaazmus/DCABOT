"""Faz W-B3: one symbol's venue trading rules from public exchangeInfo."""
import json
import unittest

from dcabot.data_adapters.binance_public_transport import (
    BinancePublicTransportError,
    fetch_binance_public_symbol_rules,
)


class _Response:
    def __init__(self, body, status=200):
        self.status = status
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
        return _Response(self.body)


def _entry(**overrides):
    entry = {
        "symbol": "BTCUSDT",
        "status": "TRADING",
        "baseAsset": "BTC",
        "quoteAsset": "USDT",
        "filters": [
            {"filterType": "PRICE_FILTER", "minPrice": "0.01000000", "maxPrice": "1000000.00000000", "tickSize": "0.01000000"},
            {"filterType": "LOT_SIZE", "minQty": "0.00001000", "maxQty": "9000.00000000", "stepSize": "0.00001000"},
            {"filterType": "NOTIONAL", "minNotional": "5.00000000", "applyMinToMarket": True},
        ],
    }
    entry.update(overrides)
    return entry


def _fetch(body):
    opener = _Opener(body)
    return fetch_binance_public_symbol_rules("BTCUSDT", allowed_symbols=frozenset({"BTCUSDT"}), opener=opener), opener


class SymbolRulesTests(unittest.TestCase):
    def test_filters_become_exact_rules(self):
        rules, opener = _fetch({"symbols": [_entry()]})
        self.assertEqual(
            (rules.tick, rules.qty_step, rules.min_qty, rules.min_notional, rules.quote_asset, rules.status),
            ("0.01", "0.00001", "0.00001", "5", "USDT", "TRADING"),
        )
        self.assertTrue(opener.urls[0].endswith("/v3/exchangeInfo?symbol=BTCUSDT"))

    def test_legacy_min_notional_filter_is_accepted(self):
        entry = _entry()
        entry["filters"][2] = {"filterType": "MIN_NOTIONAL", "minNotional": "10.00000000"}
        rules, _ = _fetch({"symbols": [entry]})
        self.assertEqual(rules.min_notional, "10")

    def test_incomplete_or_foreign_payloads_fail_closed(self):
        without_lot = _entry()
        without_lot["filters"] = [f for f in without_lot["filters"] if f["filterType"] != "LOT_SIZE"]
        cases = {
            "missing_lot_size": {"symbols": [without_lot]},
            "other_symbol": {"symbols": [_entry(symbol="ETHUSDT")]},
            "two_symbols": {"symbols": [_entry(), _entry()]},
            "zero_tick": {"symbols": [_entry(filters=[
                {"filterType": "PRICE_FILTER", "tickSize": "0"},
                {"filterType": "LOT_SIZE", "minQty": "1", "stepSize": "1"},
                {"filterType": "NOTIONAL", "minNotional": "5"},
            ])]},
            "no_symbols": {},
        }
        for name, body in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(BinancePublicTransportError) as ctx:
                    _fetch(body)
                self.assertEqual(ctx.exception.code, "PUBLIC_UPSTREAM_RECORD_INVALID")

    def test_symbol_outside_allowlist_is_rejected_before_request(self):
        opener = _Opener({})
        with self.assertRaises(BinancePublicTransportError):
            fetch_binance_public_symbol_rules("BTCUSDT", allowed_symbols=frozenset({"ETHUSDT"}), opener=opener)
        self.assertEqual(opener.urls, [])


if __name__ == "__main__":
    unittest.main()
