"""G3-b: futures public funding history + premium index (keyless fapi).

Same fake-opener pattern as test_binance_public_klines.py; venue order
verified ascending (2026-09-27 probe: fundingTime strictly increasing)."""
import json
import unittest
from urllib.parse import parse_qs, urlparse

from dcabot.data_adapters.binance_futures_public_transport import (
    BINANCE_FUTURES_EXCHANGE_INFO_URL,
    BINANCE_FUTURES_FUNDING_RATE_URL,
    BINANCE_FUTURES_KLINES_URL,
    BINANCE_FUTURES_PREMIUM_INDEX_URL,
    BinanceFuturesPremium,
    BinancePublicTransportError,
    fetch_funding_rate_history,
    fetch_futures_public_klines_range,
    fetch_futures_symbol_rules,
    fetch_premium_index,
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
    def __init__(self, responses=None, error=None):
        self.responses = list(responses or [])
        self.error = error
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request.full_url, timeout, dict(request.header_items())))
        if self.error is not None:
            raise self.error
        return self.responses.pop(0)


def _funding(ms, rate, symbol="BTCUSDT"):
    return {"symbol": symbol, "fundingTime": ms, "fundingRate": rate, "markPrice": "80000"}


def _opener(payload, status=200, headers=None):
    body = json.dumps(payload).encode("utf-8")
    return _FakeOpener([_FakeResponse(status, body, headers)])


H8 = 8 * 3_600_000
T0 = 1_767_225_600_000


def _fetch(opener, *, start_us=T0 * 1000, end_us=(T0 + 3 * H8) * 1000, symbol="BTCUSDT"):
    return fetch_funding_rate_history(
        symbol,
        start_us=start_us,
        end_us=end_us,
        allowed_symbols=frozenset({symbol}),
        opener=opener,
    )


class FetchFundingRateHistoryTests(unittest.TestCase):
    def test_valid_records_oldest_first_exact_text(self):
        records = _fetch(
            _opener([_funding(T0, "0.00010000"), _funding(T0 + H8, "-0.00000545")])
        )
        self.assertEqual([r.funding_time_us for r in records], [T0 * 1000, (T0 + H8) * 1000])
        self.assertEqual([r.rate for r in records], ["0.0001", "-0.00000545"])

    def test_range_boundaries_half_open(self):
        records = _fetch(
            _opener(
                [
                    _funding(T0 - 1, "0.0001"),
                    _funding(T0, "0.0002"),
                    _funding(T0 + 3 * H8, "0.0003"),
                ]
            )
        )
        self.assertEqual([r.rate for r in records], ["0.0002"])

    def test_out_of_order_rejects_batch(self):
        with self.assertRaises(BinancePublicTransportError) as ctx:
            _fetch(_opener([_funding(T0 + H8, "0.0001"), _funding(T0, "0.0001")]))
        self.assertIn("PUBLIC_UPSTREAM_RECORD_INVALID", str(ctx.exception))

    def test_duplicate_time_rejects_batch(self):
        with self.assertRaises(BinancePublicTransportError) as ctx:
            _fetch(_opener([_funding(T0, "0.0001"), _funding(T0, "0.0002")]))
        self.assertIn("PUBLIC_UPSTREAM_RECORD_INVALID", str(ctx.exception))

    def test_bad_rate_rejects_batch(self):
        for bad in ("not-a-rate", "5.0", None):
            with self.assertRaises(BinancePublicTransportError, msg=bad):
                _fetch(_opener([_funding(T0, bad)]))

    def test_wrong_symbol_rejects_batch(self):
        with self.assertRaises(BinancePublicTransportError) as ctx:
            _fetch(_opener([_funding(T0, "0.0001", symbol="ETHUSDT")]))
        self.assertIn("PUBLIC_UPSTREAM_RECORD_INVALID", str(ctx.exception))

    def test_symbol_not_allowed(self):
        opener = _opener([_funding(T0, "0.0001")])
        with self.assertRaises(BinancePublicTransportError) as ctx:
            fetch_funding_rate_history(
                "BTCUSDT",
                start_us=T0 * 1000,
                end_us=(T0 + H8) * 1000,
                allowed_symbols=frozenset({"ETHUSDT"}),
                opener=opener,
            )
        self.assertIn("PUBLIC_SYMBOL_NOT_ALLOWED", str(ctx.exception))
        self.assertEqual(opener.requests, [])

    def test_invalid_range_no_request(self):
        opener = _opener([])
        with self.assertRaises(BinancePublicTransportError) as ctx:
            fetch_funding_rate_history(
                "BTCUSDT",
                start_us=T0 * 1000,
                end_us=T0 * 1000,
                allowed_symbols=frozenset({"BTCUSDT"}),
                opener=opener,
            )
        self.assertIn("PUBLIC_RANGE_INVALID", str(ctx.exception))
        self.assertEqual(opener.requests, [])

    def test_request_shape_get_identity(self):
        opener = _opener([_funding(T0, "0.0001")])
        _fetch(opener)
        (url, timeout, headers), *_ = opener.requests
        self.assertTrue(url.startswith(BINANCE_FUTURES_FUNDING_RATE_URL + "?"))
        query = parse_qs(urlparse(url).query)
        self.assertEqual(query["symbol"], ["BTCUSDT"])
        self.assertEqual(query["startTime"], [str(T0)])
        self.assertEqual(query["limit"], ["1000"])
        self.assertEqual(timeout, 5)
        lowered = {key.lower(): value for key, value in headers.items()}
        self.assertEqual(lowered["accept-encoding"], "identity")
        self.assertEqual(lowered["accept"], "application/json")

    def test_http_error_maps_unavailable(self):
        opener = _opener([], status=429)
        with self.assertRaises(BinancePublicTransportError) as ctx:
            _fetch(opener)
        self.assertIn("PUBLIC_UPSTREAM_HTTP_ERROR", str(ctx.exception))

    def test_gap_returned_as_is(self):
        records = _fetch(
            _opener([_funding(T0, "0.0001"), _funding(T0 + 2 * H8, "0.0002")])
        )
        self.assertEqual(len(records), 2)


class FetchPremiumIndexTests(unittest.TestCase):
    def _fetch(self, opener, symbol="BTCUSDT"):
        return fetch_premium_index(
            symbol, allowed_symbols=frozenset({symbol}), opener=opener
        )

    def test_valid_snapshot_exact_text(self):
        premium = self._fetch(
            _opener(
                {
                    "symbol": "BTCUSDT",
                    "markPrice": "84483.95799850",
                    "indexPrice": "84529.91434783",
                    "lastFundingRate": "0.00001526",
                }
            )
        )
        self.assertIsInstance(premium, BinanceFuturesPremium)
        self.assertEqual(premium.mark_price, "84483.9579985")
        self.assertEqual(premium.index_price, "84529.91434783")
        self.assertEqual(premium.last_funding_rate, "0.00001526")

    def test_zero_mark_rejected(self):
        with self.assertRaises(BinancePublicTransportError) as ctx:
            self._fetch(
                _opener(
                    {
                        "symbol": "BTCUSDT",
                        "markPrice": "0",
                        "indexPrice": "84529.91",
                        "lastFundingRate": "0.00001",
                    }
                )
            )
        self.assertIn("PUBLIC_UPSTREAM_RECORD_INVALID", str(ctx.exception))

    def test_request_shape(self):
        opener = _opener(
            {
                "symbol": "BTCUSDT",
                "markPrice": "84483.95",
                "indexPrice": "84529.91",
                "lastFundingRate": "0.00001",
            }
        )
        self._fetch(opener)
        (url, _timeout, _headers), *_ = opener.requests
        self.assertTrue(url.startswith(BINANCE_FUTURES_PREMIUM_INDEX_URL + "?"))
        self.assertEqual(parse_qs(urlparse(url).query)["symbol"], ["BTCUSDT"])


def _rules_payload(**overrides):
    payload = {
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "status": "TRADING",
                "baseAsset": "BTC",
                "quoteAsset": "USDT",
                "contractType": "PERPETUAL",
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.10"},
                    {"filterType": "LOT_SIZE", "stepSize": "0.001", "minQty": "0.001"},
                    {"filterType": "MIN_NOTIONAL", "notional": "50"},
                ],
            }
        ]
    }
    payload["symbols"][0].update(overrides)
    return payload


class FetchFuturesSymbolRulesTests(unittest.TestCase):
    def _fetch(self, opener, symbol="BTCUSDT"):
        return fetch_futures_symbol_rules(
            symbol, allowed_symbols=frozenset({symbol}), opener=opener
        )

    def test_valid_rules_exact_text(self):
        rules = self._fetch(_opener(_rules_payload()))
        self.assertEqual(
            (rules.tick, rules.qty_step, rules.min_qty, rules.min_notional),
            ("0.1", "0.001", "0.001", "50"),
        )
        self.assertEqual(rules.contract_type, "PERPETUAL")

    def test_missing_notional_filter_rejected(self):
        payload = _rules_payload()
        payload["symbols"][0]["filters"] = [
            {"filterType": "PRICE_FILTER", "tickSize": "0.10"},
            {"filterType": "LOT_SIZE", "stepSize": "0.001", "minQty": "0.001"},
        ]
        with self.assertRaises(BinancePublicTransportError) as ctx:
            self._fetch(_opener(payload))
        self.assertIn("PUBLIC_UPSTREAM_RECORD_INVALID", str(ctx.exception))

    def test_non_trading_status_surfaced_not_rejected(self):
        rules = self._fetch(_opener(_rules_payload(status="HALT")))
        self.assertEqual(rules.status, "HALT")

    def test_request_shape(self):
        opener = _opener(_rules_payload())
        self._fetch(opener)
        (url, _timeout, _headers), *_ = opener.requests
        self.assertTrue(url.startswith(BINANCE_FUTURES_EXCHANGE_INFO_URL + "?"))
        self.assertEqual(parse_qs(urlparse(url).query)["symbol"], ["BTCUSDT"])

    def test_full_list_picks_exact_symbol(self):
        payload = _rules_payload()
        payload["symbols"].append(
            {
                "symbol": "ETHUSDT",
                "status": "TRADING",
                "baseAsset": "ETH",
                "quoteAsset": "USDT",
                "contractType": "PERPETUAL",
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
                    {"filterType": "LOT_SIZE", "stepSize": "0.01", "minQty": "0.01"},
                    {"filterType": "MIN_NOTIONAL", "notional": "20"},
                ],
            }
        )
        rules = self._fetch(_opener(payload))
        self.assertEqual((rules.symbol, rules.tick, rules.min_notional), ("BTCUSDT", "0.1", "50"))

    def test_missing_symbol_rejected(self):
        payload = _rules_payload()
        payload["symbols"][0]["symbol"] = "ETHUSDT"
        with self.assertRaises(BinancePublicTransportError) as ctx:
            self._fetch(_opener(payload))
        self.assertIn("PUBLIC_UPSTREAM_RECORD_INVALID", str(ctx.exception))


KHOUR_MS = 3_600_000


def _krow(open_ms, o="100", h="101", l="99", c="100.5", v="12.5"):
    return [open_ms, o, h, l, c, v, open_ms + KHOUR_MS - 1, "0", 10, "0", "0", "0"]


class FetchFuturesPublicKlinesRangeTests(unittest.TestCase):
    def _fetch(self, opener, **overrides):
        args = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "start_us": T0 * 1000,
            "end_us": (T0 + 2 * KHOUR_MS) * 1000,
            "max_bars": 100,
            "now_us": (T0 + 10 * KHOUR_MS) * 1000,
            "allowed_symbols": frozenset({"BTCUSDT"}),
            "opener": opener,
        }
        args.update(overrides)
        return fetch_futures_public_klines_range(**args)

    def test_closed_bars_oldest_first(self):
        bars = self._fetch(_opener([_krow(T0), _krow(T0 + KHOUR_MS)]))
        self.assertEqual([b.open_time_us for b in bars], [T0 * 1000, (T0 + KHOUR_MS) * 1000])
        self.assertEqual(bars[0].close, "100.5")

    def test_still_forming_bar_dropped(self):
        bars = self._fetch(
            _opener([_krow(T0), _krow(T0 + KHOUR_MS)]),
            now_us=(T0 + KHOUR_MS) * 1000,
        )
        self.assertEqual(len(bars), 1)

    def test_bad_row_rejects_batch(self):
        bad = _krow(T0)
        bad[4] = "not-a-price"
        with self.assertRaises(BinancePublicTransportError) as ctx:
            self._fetch(_opener([bad]))
        self.assertIn("PUBLIC_UPSTREAM_RECORD_INVALID", str(ctx.exception))

    def test_request_shape(self):
        opener = _opener([_krow(T0)])
        self._fetch(opener)
        (url, _timeout, _headers), *_ = opener.requests
        self.assertTrue(url.startswith(BINANCE_FUTURES_KLINES_URL + "?"))
        query = parse_qs(urlparse(url).query)
        self.assertEqual(query["symbol"], ["BTCUSDT"])
        self.assertEqual(query["interval"], ["1h"])


if __name__ == "__main__":
    unittest.main()
