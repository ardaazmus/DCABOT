"""Q2: POST /api/v2/risk/correlation-matrix -- aligned venue closes,
exact breach verdicts, display coefficients. Read-only."""
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from dcabot.application.sector_dca import SymbolRules
from dcabot.data_adapters.binance_public_transport import BinancePublicTransportError
from dcabot.persistence.kline_cache import KlineCache
from dcabot.server import api as api_module
from dcabot.server import v2_risk
from api.test_v2_bots import call
from test_sector_backtest import HOUR, _walk

DAY_US = 86_400_000_000
START_US = 1_767_225_600_000_000  # 2026-01-01T00:00:00Z
NOW_US = START_US + 400 * DAY_US


class _Market:
    def __init__(self):
        self.status = {}

    def symbol_rules(self, symbol):
        return SymbolRules(symbol, self.status.get(symbol, "TRADING"), symbol[:-4], "USDT", "0.01", "0.00001", "0.00001", "5")

    def last_price(self, symbol):
        raise AssertionError("matrix must not need a live price")


class V2CorrelationMatrixApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = KlineCache(Path(self.tmp.name) / "k.sqlite3")
        self.market = _Market()
        self.fetches = []
        self.fail = False
        self.short = set()

        def fetch_range(symbol, *, interval, start_us, end_us, max_bars, now_us, allowed_symbols):
            self.fetches.append(symbol)
            if self.fail:
                raise BinancePublicTransportError("PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı.")
            count = (end_us - start_us) // HOUR
            if symbol in self.short:
                count = 3
            seed = 11 if symbol in ("BTCUSDT", "ETHUSDT") else 77
            return _walk(count, seed, start_us=start_us)

        deps = v2_risk.V2RiskDeps(
            market=self.market,
            fetch_range=fetch_range,
            cache=self.cache,
            clock_us=lambda: NOW_US,
            problem=api_module._problem,
            transport_error=BinancePublicTransportError,
        )
        self.app = FastAPI()
        self.app.router.route_class = api_module.BoundedAPIRoute
        self.app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_risk.register_routes(self.app, deps)

    def tearDown(self):
        self.cache.close()
        self.tmp.cleanup()

    def run_matrix(self, **overrides):
        body = {"symbols": ["BTCUSDT", "ETHUSDT", "XRPUSDT"], "interval": "1h", "window": 30, "threshold": "0.7"}
        body.update(overrides)
        return call(self.app, "POST", "/api/v2/risk/correlation-matrix", body)

    def test_identical_walks_breach_and_divergent_do_not(self):
        status, body, _ = self.run_matrix()
        self.assertEqual(status, 200, body)
        data = body["data"]
        self.assertEqual(data["data_source"], "VENUE")
        self.assertEqual(data["overlap_bars"], 63)
        cells = {(c["x"], c["y"]): c for c in data["cells"]}
        self.assertEqual(set(cells), {("BTCUSDT", "ETHUSDT"), ("BTCUSDT", "XRPUSDT"), ("ETHUSDT", "XRPUSDT")})
        self.assertEqual(cells[("BTCUSDT", "ETHUSDT")]["verdict"], "BREACH")
        self.assertEqual(cells[("BTCUSDT", "ETHUSDT")]["coefficient"], "1.0000")
        self.assertEqual(cells[("BTCUSDT", "XRPUSDT")]["verdict"], "OK")

    def test_second_run_is_served_from_cache(self):
        self.run_matrix()
        fetches = len(self.fetches)
        status, body, _ = self.run_matrix()
        self.assertEqual((status, body["data"]["data_source"]), (200, "CACHE"))
        self.assertEqual(len(self.fetches), fetches)

    def test_short_symbol_history_is_insufficient_not_ok(self):
        self.short.add("XRPUSDT")
        status, body, _ = self.run_matrix()
        self.assertEqual(status, 200, body)
        for cell in body["data"]["cells"]:
            if "XRPUSDT" in (cell["x"], cell["y"]):
                self.assertEqual(cell["verdict"], "INSUFFICIENT")

    def test_validation_errors_are_problem_details(self):
        cases = [
            ({"symbols": ["BTCUSDT"]}, "REQUEST_VALIDATION_FAILED", "symbols"),
            ({"symbols": ["BTCUSDT"] * 11}, "REQUEST_VALIDATION_FAILED", "symbols"),
            ({"symbols": ["BTCUSDT", "BTCUSDT"]}, "CORRELATION_SYMBOLS_INVALID", "symbols"),
            ({"symbols": ["BTCUSDT", "btcusdt"]}, "REQUEST_VALIDATION_FAILED", "symbols"),
            ({"window": 1}, "REQUEST_VALIDATION_FAILED", "window"),
            ({"window": 201}, "REQUEST_VALIDATION_FAILED", "window"),
            ({"threshold": "0"}, "CORRELATION_THRESHOLD_INVALID", "threshold"),
            ({"threshold": "1.5"}, "CORRELATION_THRESHOLD_INVALID", "threshold"),
            ({"threshold": "abc"}, "REQUEST_VALIDATION_FAILED", "threshold"),
            ({"interval": "1m"}, "REQUEST_VALIDATION_FAILED", "interval"),
        ]
        for overrides, code, field in cases:
            with self.subTest(overrides=overrides):
                status, body, headers = self.run_matrix(**overrides)
                self.assertEqual(status, 422, body)
                self.assertEqual(body["code"], code)
                self.assertIn(field, body["errors"][0]["field"])
                self.assertEqual(headers["content-type"], "application/problem+json")

    def test_halted_symbol_rejected_and_outage_is_502(self):
        self.market.status["XRPUSDT"] = "BREAK"
        status, body, _ = self.run_matrix()
        self.assertEqual((status, body["code"]), (422, "CORRELATION_SYMBOL_HALTED"))
        self.market.status.clear()
        self.fail = True
        status, body, _ = self.run_matrix()
        self.assertEqual((status, body["code"]), (502, "PUBLIC_UPSTREAM_UNAVAILABLE"))


if __name__ == "__main__":
    unittest.main()
