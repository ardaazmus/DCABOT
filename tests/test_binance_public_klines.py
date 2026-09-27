"""AB.0: public kline fetch (display-only live charts).
Same fake-opener pattern as test_binance_public_ticker.py."""
import json
import random
import unittest
import urllib.error
from fractions import Fraction
from urllib.parse import parse_qs, urlparse

from dcabot.data_adapters.binance_public_transport import (
    BINANCE_SPOT_PUBLIC_KLINES_URL,
    BinancePublicTransportError,
    fetch_binance_public_klines,
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
        self.requests.append((request.full_url, timeout, dict(request.header_items())))
        if self.error is not None:
            raise self.error
        return self.response


HOUR_MS = 3_600_000


def _row(open_ms, o, h, l, c, v="12.5"):
    return [open_ms, o, h, l, c, v, open_ms + HOUR_MS - 1, "0", 10, "0", "0", "0"]


def _opener(rows, status=200, headers=None):
    return _FakeOpener(_FakeResponse(status, json.dumps(rows).encode("utf-8"), headers))


def _fetch(opener, *, symbol="BTCUSDT", interval="1h", limit=500):
    return fetch_binance_public_klines(
        symbol,
        interval=interval,
        limit=limit,
        allowed_symbols=frozenset({symbol}),
        opener=opener,
    )


class FetchBinancePublicKlinesTests(unittest.TestCase):
    def test_valid_rows_become_exact_chart_bars(self):
        opener = _opener(
            [
                _row(0, "100.10", "105.00", "99.00", "104.00"),
                _row(HOUR_MS, "104.00", "104.50", "101.25", "102.00000001", "0"),
            ]
        )
        bars = _fetch(opener, limit=2)
        self.assertEqual(len(bars), 2)
        first = bars[0]
        self.assertEqual(first.open_time_us, 0)
        self.assertEqual(first.close_time_us, HOUR_MS * 1000 - 1)
        self.assertEqual((first.open, first.high, first.low, first.close), ("100.1", "105", "99", "104"))
        self.assertEqual(first.base_volume, "12.5")
        self.assertEqual(bars[1].close, "102.00000001")
        self.assertEqual(bars[1].base_volume, "0")
        self.assertTrue(opener.response.closed)

    def test_request_is_credential_free_and_carries_only_the_three_params(self):
        opener = _opener([])
        _fetch(opener, symbol="ETHUSDC", interval="15m", limit=50)
        url, _timeout, headers = opener.requests[0]
        parsed = urlparse(url)
        self.assertEqual(f"{parsed.scheme}://{parsed.netloc}{parsed.path}", BINANCE_SPOT_PUBLIC_KLINES_URL)
        self.assertEqual(parse_qs(parsed.query), {"symbol": ["ETHUSDC"], "interval": ["15m"], "limit": ["50"]})
        self.assertFalse(any("key" in name.lower() or "auth" in name.lower() for name in headers))

    def test_invalid_arguments_fail_before_any_request(self):
        cases = [
            dict(symbol="btcusdt"),
            dict(interval="1M"),
            dict(interval="2m"),
            dict(limit=0),
            dict(limit=1001),
        ]
        for overrides in cases:
            with self.subTest(**overrides):
                opener = _opener([])
                with self.assertRaises(BinancePublicTransportError):
                    _fetch(opener, **overrides)
                self.assertEqual(opener.requests, [])

    def test_symbol_outside_allowlist_is_rejected(self):
        opener = _opener([])
        with self.assertRaises(BinancePublicTransportError) as ctx:
            fetch_binance_public_klines(
                "BTCUSDT", interval="1h", limit=5, allowed_symbols=frozenset({"ETHUSDT"}), opener=opener
            )
        self.assertEqual(ctx.exception.code, "PUBLIC_SYMBOL_NOT_ALLOWED")

    def test_any_malformed_row_rejects_the_whole_batch(self):
        good = _row(0, "100", "101", "99", "100")
        bad_rows = {
            "short_row": good[:6],
            "float_price": [0, 100.5, "101", "99", "100", "1", HOUR_MS - 1, "0", 1, "0", "0", "0"],
            "exponent": _row(0, "1e2", "101", "99", "100"),
            "zero_price": _row(0, "0", "101", "0", "100"),
            "negative_volume": _row(0, "100", "101", "99", "100", "-1"),
            "high_below_close": _row(0, "100", "100.5", "99", "101"),
            "low_above_open": _row(0, "100", "102", "100.5", "101"),
            "close_before_open": [5, "100", "101", "99", "100", "1", 5, "0", 1, "0", "0", "0"],
            "string_time": ["0", "100", "101", "99", "100", "1", HOUR_MS - 1, "0", 1, "0", "0", "0"],
        }
        for name, bad in bad_rows.items():
            with self.subTest(case=name):
                with self.assertRaises(BinancePublicTransportError) as ctx:
                    _fetch(_opener([bad]))
                self.assertEqual(ctx.exception.code, "PUBLIC_UPSTREAM_RECORD_INVALID")

    def test_out_of_order_or_overlapping_rows_are_rejected(self):
        a = _row(HOUR_MS, "100", "101", "99", "100")
        b = _row(0, "100", "101", "99", "100")
        with self.assertRaises(BinancePublicTransportError) as ctx:
            _fetch(_opener([a, b]))
        self.assertEqual(ctx.exception.code, "PUBLIC_UPSTREAM_RECORD_INVALID")
        with self.assertRaises(BinancePublicTransportError):
            _fetch(_opener([a, a]))

    def test_more_rows_than_requested_limit_is_rejected(self):
        rows = [_row(i * HOUR_MS, "100", "101", "99", "100") for i in range(3)]
        with self.assertRaises(BinancePublicTransportError) as ctx:
            _fetch(_opener(rows), limit=2)
        self.assertEqual(ctx.exception.code, "PUBLIC_RESPONSE_INVALID")

    def test_upstream_failures_are_bounded_errors(self):
        with self.assertRaises(BinancePublicTransportError) as ctx:
            _fetch(_opener([], status=500))
        self.assertEqual(ctx.exception.code, "PUBLIC_UPSTREAM_HTTP_ERROR")
        with self.assertRaises(BinancePublicTransportError) as ctx:
            _fetch(_FakeOpener(error=urllib.error.URLError("down")))
        self.assertEqual(ctx.exception.code, "PUBLIC_UPSTREAM_UNAVAILABLE")
        with self.assertRaises(BinancePublicTransportError) as ctx:
            _fetch(_opener([], headers={"Content-Encoding": "gzip"}))
        self.assertEqual(ctx.exception.code, "PUBLIC_ENCODING_INVALID")

    def test_property_valid_random_batches_round_trip_exactly(self):
        rng = random.Random(20260924)
        for _trial in range(200):
            count = rng.randint(0, 40)
            rows, expected = [], []
            open_ms = rng.randint(0, 10**12)
            for _ in range(count):
                scale = rng.randint(0, 8)
                prices = sorted(rng.randint(1, 10**9) for _ in range(4))
                low, a, b, high = (Fraction(p, 10**scale) for p in prices)
                o, c = (a, b) if rng.random() < 0.5 else (b, a)
                volume = Fraction(rng.randint(0, 10**12), 10**4)
                rows.append(
                    _row(
                        open_ms,
                        _decimal(o, scale),
                        _decimal(high, scale),
                        _decimal(low, scale),
                        _decimal(c, scale),
                        _decimal(volume, 4),
                    )
                )
                expected.append((open_ms, o, high, low, c, volume))
                open_ms += HOUR_MS * rng.randint(1, 3)
            bars = _fetch(_opener(rows), limit=max(count, 1))
            self.assertEqual(len(bars), count)
            previous_close = -1
            for bar, (om, o, h, l, c, v) in zip(bars, expected):
                self.assertEqual(bar.open_time_us, om * 1000)
                self.assertGreater(bar.open_time_us, previous_close)
                self.assertGreater(bar.close_time_us, bar.open_time_us)
                previous_close = bar.close_time_us
                self.assertEqual(
                    (Fraction(bar.open), Fraction(bar.high), Fraction(bar.low), Fraction(bar.close), Fraction(bar.base_volume)),
                    (o, h, l, c, v),
                )
                self.assertLessEqual(Fraction(bar.low), min(Fraction(bar.open), Fraction(bar.close)))
                self.assertGreaterEqual(Fraction(bar.high), max(Fraction(bar.open), Fraction(bar.close)))


def _decimal(value: Fraction, scale: int) -> str:
    units = value * 10**scale
    assert units.denominator == 1
    digits = str(units.numerator).rjust(scale + 1, "0")
    return digits if scale == 0 else f"{digits[:-scale]}.{digits[-scale:]}"


if __name__ == "__main__":
    unittest.main()
