"""G3-b: POST /api/v2/futures-grid-backtests — futures klines + funding, typed result."""
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from dcabot.data_adapters.binance_futures_public_transport import BinanceFuturesFundingRate
from dcabot.data_adapters.binance_public_transport import BinancePublicTransportError
from dcabot.persistence.funding_cache import FundingCache
from dcabot.persistence.kline_cache import KlineCache
from dcabot.server import api as api_module
from dcabot.server import v2_futures_grid_backtests
from api.test_v2_bots import call
from test_sector_backtest import HOUR, _walk

DAY_US = 86_400_000_000
START_US = 1_767_225_600_000_000  # 2026-01-01T00:00:00Z


def _rules(symbol, *, allowed_symbols):
    from dcabot.data_adapters.binance_futures_public_transport import BinanceFuturesSymbolRules

    assert symbol in allowed_symbols
    return BinanceFuturesSymbolRules(symbol, "TRADING", symbol[:-4], "USDT", "PERPETUAL", "0.1", "0.001", "0.001", "5")


def _strategy(**overrides):
    body = {
        "symbol": "BTCUSDT",
        "direction": "LONG",
        "mode": "ARITHMETIC",
        "lower_price": "90",
        "upper_price": "110",
        "interval_count": 10,
        "leverage": 5,
        "fee_rate": "0.0005",
        "stop_loss_price": None,
        "take_profit_pct": None,
        "trailing_up_pct": None,
        "trailing_down_pct": None,
    }
    body.update(overrides)
    return body


class V2FuturesGridBacktestApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.kline_cache = KlineCache(Path(self.tmp.name) / "k.sqlite3")
        self.funding_cache = FundingCache(Path(self.tmp.name) / "f.sqlite3")
        self.kline_fetches = []
        self.funding_fetches = []
        self.fail = False

        def fetch_klines(symbol, *, interval, start_us, end_us, max_bars, now_us, allowed_symbols):
            self.kline_fetches.append((symbol, interval, start_us, end_us))
            if self.fail:
                raise BinancePublicTransportError("PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı.")
            return _walk((end_us - start_us) // HOUR, 7, start_us=start_us)

        def fetch_funding(symbol, *, start_us, end_us, allowed_symbols):
            self.funding_fetches.append((symbol, start_us, end_us))
            if self.fail:
                raise BinancePublicTransportError("PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı.")
            records = []
            cursor = start_us - (start_us % (8 * HOUR)) + (8 * HOUR)
            while cursor < end_us:
                records.append(BinanceFuturesFundingRate(funding_time_us=cursor, rate="0.0001"))
                cursor += 8 * HOUR
            return tuple(records)

        deps = v2_futures_grid_backtests.V2FuturesGridBacktestDeps(
            fetch_rules=_rules,
            fetch_klines_range=fetch_klines,
            fetch_funding=fetch_funding,
            kline_cache=self.kline_cache,
            funding_cache=self.funding_cache,
            clock_us=lambda: START_US + 400 * DAY_US,
            problem=api_module._problem,
            transport_error=BinancePublicTransportError,
        )
        self.app = FastAPI()
        self.app.router.route_class = api_module.BoundedAPIRoute
        self.app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_futures_grid_backtests.register_routes(self.app, deps)

    def tearDown(self):
        self.kline_cache.close()
        self.funding_cache.close()
        self.tmp.cleanup()

    def run_backtest(self, **overrides):
        body = {"investment": "1000", "strategy": _strategy(), "interval": "1h", "start_date": "2026-01-01", "end_date": "2026-01-07"}
        body.update(overrides)
        return call(self.app, "POST", "/api/v2/futures-grid-backtests", body)

    def test_first_run_hits_venue_second_from_cache(self):
        status, body, _ = self.run_backtest()
        self.assertEqual(status, 200, body)
        result = body["data"]
        self.assertEqual(
            (result["data_source"], result["funding_source"], result["bar_count"], result["interval"]),
            ("VENUE", "VENUE", 7 * 24, "1h"),
        )
        self.assertEqual((result["direction"], result["leverage"]), ("LONG", 5))
        self.assertGreater(result["summary"]["funding_events_applied"], 0)
        self.assertIn("FUNDING_VENUE_HISTORY", result["assumptions"])
        self.assertIn("LIQ_ESTIMATE_DISABLED_NO_TIERS", result["assumptions"])
        status, again, _ = self.run_backtest()
        self.assertEqual((status, again["data"]["data_source"], again["data"]["funding_source"]), (200, "CACHE", "CACHE"))
        self.assertEqual(again["data"]["summary"], result["summary"])
        self.assertEqual((len(self.kline_fetches), len(self.funding_fetches)), (1, 1))

    def test_range_and_grid_errors_are_problem_details(self):
        cases = [
            ({"start_date": "2026-03-01", "end_date": "2026-02-01"}, "BACKTEST_RANGE_INVALID", "end_date"),
            ({"interval": "15m", "start_date": "2026-01-01", "end_date": "2026-12-31"}, "BACKTEST_RANGE_TOO_LARGE", "start_date"),
            ({"start_date": "2026-02-30"}, "BACKTEST_DATE_INVALID", "start_date"),
            ({"strategy": _strategy(upper_price="80")}, "GRID_BOUNDS_INVALID", "strategy"),
            ({"strategy": _strategy(leverage=11)}, "REQUEST_VALIDATION_FAILED", None),
        ]
        for overrides, code, field in cases:
            with self.subTest(code=code):
                status, body, headers = self.run_backtest(**overrides)
                if field is None:
                    self.assertEqual((status, body["code"]), (422, code))
                else:
                    self.assertEqual((status, body["code"], body["errors"][0]["field"]), (422, code, field))
                self.assertEqual(headers["content-type"], "application/problem+json")

    def test_venue_outage_is_a_bounded_502(self):
        self.fail = True
        status, body, _ = self.run_backtest()
        self.assertEqual((status, body["code"]), (502, "PUBLIC_UPSTREAM_UNAVAILABLE"))


class RealAppFuturesGridBacktestContractTests(unittest.TestCase):
    def test_route_is_typed_and_bounded(self):
        import json

        schema = api_module.app.openapi()
        operation = schema["paths"]["/api/v2/futures-grid-backtests"]["post"]
        self.assertIn("$ref", json.dumps(operation["responses"]["200"]))
        self.assertIn("/api/v2/futures-grid-backtests", api_module.ROUTE_BODY_LIMITS)


if __name__ == "__main__":
    unittest.main()
