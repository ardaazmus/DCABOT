"""G2-b: POST /api/v2/grid-backtests — venue-or-cache klines, typed result, Problem Details."""
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from dcabot.application.sector_dca import SymbolRules
from dcabot.data_adapters.binance_public_transport import BinancePublicTransportError
from dcabot.persistence.kline_cache import KlineCache
from dcabot.server import api as api_module
from dcabot.server import v2_grid_backtests
from api.test_v2_bots import call
from test_sector_backtest import HOUR, _walk

DAY_US = 86_400_000_000
START_US = 1_767_225_600_000_000  # 2026-01-01T00:00:00Z


class _Market:
    def symbol_rules(self, symbol):
        return SymbolRules(symbol, "TRADING", symbol[:-4], "USDT", "0.01", "0.00001", "0.00001", "5")

    def last_price(self, symbol):
        raise AssertionError("backtests must not need a live price")


def _strategy(**overrides):
    body = {
        "symbol": "BTCUSDT",
        "mode": "ARITHMETIC",
        "lower_price": "90",
        "upper_price": "110",
        "interval_count": 10,
        "fee_rate": "0.001",
        "stop_loss_price": None,
        "take_profit_pct": None,
        "trailing_up_pct": None,
        "trailing_down_pct": None,
    }
    body.update(overrides)
    return body


class V2GridBacktestApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = KlineCache(Path(self.tmp.name) / "k.sqlite3")
        self.fetches = []
        self.fail = False

        def fetch_range(symbol, *, interval, start_us, end_us, max_bars, now_us, allowed_symbols):
            self.fetches.append((symbol, interval, start_us, end_us))
            if self.fail:
                raise BinancePublicTransportError("PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı.")
            return _walk((end_us - start_us) // HOUR, 7, start_us=start_us)

        deps = v2_grid_backtests.V2GridBacktestDeps(
            market=_Market(),
            fetch_range=fetch_range,
            cache=self.cache,
            clock_us=lambda: START_US + 400 * DAY_US,
            problem=api_module._problem,
            transport_error=BinancePublicTransportError,
        )
        self.app = FastAPI()
        self.app.router.route_class = api_module.BoundedAPIRoute
        self.app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_grid_backtests.register_routes(self.app, deps)

    def tearDown(self):
        self.cache.close()
        self.tmp.cleanup()

    def run_backtest(self, **overrides):
        body = {"investment": "1000", "strategy": _strategy(), "interval": "1h", "start_date": "2026-01-01", "end_date": "2026-01-07"}
        body.update(overrides)
        return call(self.app, "POST", "/api/v2/grid-backtests", body)

    def test_first_run_fetches_from_venue_and_the_second_is_served_from_cache(self):
        status, body, _ = self.run_backtest()
        self.assertEqual(status, 200, body)
        result = body["data"]
        self.assertEqual((result["data_source"], result["bar_count"], result["interval"]), ("VENUE", 7 * 24, "1h"))
        self.assertEqual(result["period_start_us"], START_US)
        self.assertIn(result["status"], ("COMPLETED", "NEVER_ENTERED", "STOPPED_SL", "STOPPED_TP"))
        self.assertIn("OHLC_INTRABAR_PATH", result["assumptions"])
        self.assertEqual(len(result["levels"]), 11)
        status, again, _ = self.run_backtest()
        self.assertEqual((status, again["data"]["data_source"]), (200, "CACHE"))
        self.assertEqual(again["data"]["summary"], result["summary"])
        self.assertEqual(len(self.fetches), 1)

    def test_range_and_grid_errors_are_problem_details(self):
        cases = [
            ({"start_date": "2026-03-01", "end_date": "2026-02-01"}, "BACKTEST_RANGE_INVALID", "end_date"),
            ({"interval": "15m", "start_date": "2026-01-01", "end_date": "2026-12-31"}, "BACKTEST_RANGE_TOO_LARGE", "start_date"),
            ({"start_date": "2026-02-30"}, "BACKTEST_DATE_INVALID", "start_date"),
            ({"strategy": _strategy(upper_price="80")}, "GRID_BOUNDS_INVALID", "strategy"),
            ({"strategy": _strategy(lower_price="90", upper_price="111", interval_count=3)}, "SPOT_GRID_QUOTE_PER_GRID_UNREPRESENTABLE", "strategy"),
        ]
        for overrides, code, field in cases:
            with self.subTest(code=code):
                status, body, headers = self.run_backtest(**overrides)
                self.assertEqual((status, body["code"], body["errors"][0]["field"]), (422, code, field))
                self.assertEqual(headers["content-type"], "application/problem+json")

    def test_schema_violations_and_unsupported_interval(self):
        for overrides in ({"interval": "1m"}, {"start_date": "01.01.2026"}, {"investment": "1e3"}):
            with self.subTest(overrides=overrides):
                status, body, _ = self.run_backtest(**overrides)
                self.assertEqual((status, body["code"]), (422, "REQUEST_VALIDATION_FAILED"))

    def test_venue_outage_is_a_bounded_502(self):
        self.fail = True
        status, body, _ = self.run_backtest()
        self.assertEqual((status, body["code"]), (502, "PUBLIC_UPSTREAM_UNAVAILABLE"))


class RealAppGridBacktestContractTests(unittest.TestCase):
    def test_grid_backtest_route_is_typed_and_bounded(self):
        import json

        schema = api_module.app.openapi()
        operation = schema["paths"]["/api/v2/grid-backtests"]["post"]
        self.assertIn("$ref", json.dumps(operation["responses"]["200"]))
        self.assertIn("/api/v2/grid-backtests", api_module.ROUTE_BODY_LIMITS)


if __name__ == "__main__":
    unittest.main()
