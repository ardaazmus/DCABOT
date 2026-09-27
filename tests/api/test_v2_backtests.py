"""Faz W: POST /api/v2/backtests — venue-or-cache klines, typed result, Problem Details."""
import json
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from dcabot.application.sector_dca import SymbolRules
from dcabot.data_adapters.binance_public_transport import BinancePublicTransportError
from dcabot.persistence.kline_cache import KlineCache
from dcabot.server import api as api_module
from dcabot.server import v2_backtests
from api.test_v2_bots import call
from test_sector_backtest import HOUR, _walk

ROOT = Path(__file__).resolve().parents[2]
DAY_US = 86_400_000_000
START_US = 1_767_225_600_000_000  # 2026-01-01T00:00:00Z


class _Market:
    def symbol_rules(self, symbol):
        return SymbolRules(symbol, "TRADING", symbol[:-4], "USDT", "0.01", "0.00001", "0.00001", "5")

    def last_price(self, symbol):
        raise AssertionError("backtests must not need a live price")


def _strategy(**overrides):
    body = {
        "symbol": "BTCUSDT", "base_order": "25", "safety_order": "25", "max_safety_orders": 6,
        "max_active_safety_orders": 2, "price_deviation": "1.5", "safety_order_volume_scale": "1.5",
        "safety_order_step_scale": "1.2", "take_profit": "2", "stop_loss": None,
    }
    body.update(overrides)
    return body


class V2BacktestApiTests(unittest.TestCase):
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

        template = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
        deps = v2_backtests.V2BacktestDeps(
            market=_Market(),
            fetch_range=fetch_range,
            cache=self.cache,
            template_loader=lambda: template,
            clock_us=lambda: START_US + 400 * DAY_US,
            problem=api_module._problem,
            transport_error=BinancePublicTransportError,
        )
        self.app = FastAPI()
        self.app.router.route_class = api_module.BoundedAPIRoute
        self.app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_backtests.register_routes(self.app, deps)

    def tearDown(self):
        self.cache.close()
        self.tmp.cleanup()

    def run_backtest(self, **overrides):
        body = {"budget": "1000", "strategy": _strategy(), "interval": "1h", "start_date": "2026-01-01", "end_date": "2026-02-28"}
        body.update(overrides)
        return call(self.app, "POST", "/api/v2/backtests", body)

    def test_first_run_fetches_from_venue_and_the_second_is_served_from_cache(self):
        status, body, _ = self.run_backtest()
        self.assertEqual(status, 200, body)
        result = body["data"]
        self.assertEqual((result["data_source"], result["bar_count"], result["interval"]), ("VENUE", 59 * 24, "1h"))
        self.assertEqual(result["period_start_us"], START_US)
        status, again, _ = self.run_backtest()
        self.assertEqual((status, again["data"]["data_source"]), (200, "CACHE"))
        self.assertEqual(again["data"]["summary"], result["summary"])
        self.assertEqual(len(self.fetches), 1)

    def test_range_and_date_errors_are_problem_details(self):
        cases = [
            ({"start_date": "2026-03-01", "end_date": "2026-02-01"}, "BACKTEST_RANGE_INVALID", "end_date"),
            ({"interval": "15m", "start_date": "2026-01-01", "end_date": "2026-12-31"}, "BACKTEST_RANGE_TOO_LARGE", "start_date"),
            ({"start_date": "2026-02-30"}, "BACKTEST_DATE_INVALID", "start_date"),
            ({"strategy": _strategy(base_order="3")}, "SECTOR_BASE_ORDER_TOO_SMALL", "strategy.base_order"),
            ({"budget": "100"}, "SECTOR_BUDGET_TOO_LOW", "budget"),
        ]
        for overrides, code, field in cases:
            with self.subTest(code=code):
                status, body, headers = self.run_backtest(**overrides)
                self.assertEqual((status, body["code"], body["errors"][0]["field"]), (422, code, field))
                self.assertEqual(headers["content-type"], "application/problem+json")

    def test_schema_violations_and_unsupported_interval(self):
        for overrides in ({"interval": "1m"}, {"start_date": "01.01.2026"}, {"budget": "1e3"}):
            with self.subTest(overrides=overrides):
                status, body, _ = self.run_backtest(**overrides)
                self.assertEqual((status, body["code"]), (422, "REQUEST_VALIDATION_FAILED"))

    def test_venue_outage_is_a_bounded_502(self):
        self.fail = True
        status, body, _ = self.run_backtest()
        self.assertEqual((status, body["code"]), (502, "PUBLIC_UPSTREAM_UNAVAILABLE"))


class RealAppBacktestContractTests(unittest.TestCase):
    def test_backtest_route_is_typed_and_bounded(self):
        schema = api_module.app.openapi()
        operation = schema["paths"]["/api/v2/backtests"]["post"]
        self.assertIn("$ref", json.dumps(operation["responses"]["200"]))
        self.assertIn("/api/v2/backtests", api_module.ROUTE_BODY_LIMITS)


if __name__ == "__main__":
    unittest.main()
