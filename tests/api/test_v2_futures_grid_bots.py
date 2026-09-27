"""G3-c: futures grid bot endpoints + paper runner ticks over klines and funding."""

import itertools
import json
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from api.test_v2_bots import FakeMarket, call
from dcabot.application.futures_grid_runner import prepare_futures_grid_runtime
from dcabot.data_adapters.binance_futures_public_transport import (
    BinanceFuturesFundingRate,
    BinanceFuturesSymbolRules,
)
from dcabot.data_adapters.binance_public_transport import BinancePublicKline, BinancePublicTransportError
from dcabot.domain.numbers import Q
from dcabot.persistence.bot_store import BotStore
from dcabot.server import api as api_module
from dcabot.server import bot_runner, v2_bots

ROOT = Path(__file__).resolve().parents[2]
MIN = 60_000_000
T0 = 1_790_000_000 * 1_000_000 // MIN * MIN
RULES = BinanceFuturesSymbolRules(
    "BTCUSDT", "TRADING", "BTC", "USDT", "PERPETUAL", "0.1", "0.00001", "0.00001", "5"
)


class FakeFuturesMarket:
    def __init__(self):
        self.price = Q("84506.01")
        self.down = False

    def symbol_rules(self, symbol):
        if self.down:
            raise v2_bots.MarketUnavailable("PUBLIC_UPSTREAM_UNAVAILABLE", "down")
        assert symbol == "BTCUSDT"
        return RULES

    def last_price(self, symbol):
        if self.down:
            raise v2_bots.MarketUnavailable("PUBLIC_UPSTREAM_UNAVAILABLE", "down")
        return self.price


def fgrid_strategy(**overrides):
    body = {
        "symbol": "BTCUSDT",
        "direction": "LONG",
        "mode": "ARITHMETIC",
        "lower_price": "80000",
        "upper_price": "89000",
        "interval_count": 9,
        "leverage": 5,
        "fee_rate": "0.0005",
        "stop_loss_price": None,
        "take_profit_pct": None,
        "trailing_up_pct": None,
        "trailing_down_pct": None,
    }
    body.update(overrides)
    return body


class _Venue:
    def __init__(self):
        self.path: dict[int, tuple[str, str, str, str]] = {}
        self.funding: dict[int, str] = {}
        self.down = False

    def fetch_range(self, symbol, *, interval, start_us, end_us, max_bars, now_us, allowed_symbols):
        if self.down:
            raise BinancePublicTransportError("PUBLIC_UPSTREAM_UNAVAILABLE", "down")
        bars = []
        t = start_us
        while t < end_us and t + MIN - 1 < now_us:
            o, h, low, c = self.path.get(t, ("84506.01", "84506.01", "84506.01", "84506.01"))
            bars.append(BinancePublicKline(t, t + MIN - 1, o, h, low, c, "1"))
            t += MIN
        return tuple(bars)

    def fetch_funding(self, symbol, *, start_us, end_us, allowed_symbols):
        if self.down:
            raise BinancePublicTransportError("PUBLIC_UPSTREAM_UNAVAILABLE", "down")
        return tuple(
            BinanceFuturesFundingRate(funding_time_us=t, rate=rate)
            for t, rate in sorted(self.funding.items())
            if start_us <= t < end_us
        )


class V2FuturesGridBotApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BotStore(Path(self.tmp.name) / "bots.sqlite3")
        self.market = FakeFuturesMarket()
        self.venue = _Venue()
        self.now = T0 + 5_000_000
        self.landmarks = []
        template = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
        self.runner = bot_runner.PaperBotRunner(
            bot_runner.RunnerDeps(
                store=self.store,
                market=FakeMarket(),
                fetch_range=self.venue.fetch_range,
                transport_error=BinancePublicTransportError,
                template_loader=lambda: template,
                clock_us=lambda: self.now,
                kill_switch_engaged=lambda: False,
                record_event=lambda kind, ref, summary, time_us: self.landmarks.append((kind, ref)),
                futures_market=self.market,
                fetch_futures_range=self.venue.fetch_range,
                fetch_funding=self.venue.fetch_funding,
            )
        )
        self.clock = itertools.count(10_000_000, 1_000)
        deps = v2_bots.V2BotDeps(
            store=self.store,
            market=FakeMarket(),
            template_loader=lambda: template,
            clock_us=lambda: next(self.clock),
            runner_available=lambda: True,
            problem=api_module._problem,
            on_start=self.runner.prepare_start,
            futures_market=self.market,
        )
        self.app = FastAPI()
        self.app.router.route_class = api_module.BoundedAPIRoute
        self.app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_bots.register_routes(self.app, deps)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def create_fgrid(self, **overrides):
        body = {"name": "FGrid test", "mode": "PAPER", "budget": "900", "strategy": fgrid_strategy()}
        body.update(overrides)
        return call(self.app, "POST", "/api/v2/futures-grid-bots", body)

    def test_preview_reports_direction_leverage_and_entry(self):
        status, body, _ = call(
            self.app, "POST", "/api/v2/futures-grid-bots/preview",
            {"budget": "900", "strategy": fgrid_strategy()},
        )
        self.assertEqual(status, 200, body)
        preview = body["data"]
        self.assertEqual((preview["direction"], preview["leverage"]), ("LONG", 5))
        self.assertEqual(preview["reference_price"], "84506.01")
        self.assertEqual(preview["entry_position"], "WITHIN")
        self.assertEqual(len(preview["levels"]), 10)
        self.assertEqual(preview["quote_per_grid"], "100")
        self.assertEqual(preview["notional_per_grid"], "500")
        self.assertIs(preview["within_min_notional"], True)

    def test_create_start_tick_funding_and_state(self):
        status, body, _ = self.create_fgrid()
        self.assertEqual(status, 201, body)
        bot_id = body["data"]["bot_id"]
        self.assertEqual(body["data"]["type"], "FUTURES_GRID")
        status, body, _ = call(self.app, "POST", f"/api/v2/bots/{bot_id}/start", {"revision": 1})
        self.assertEqual((status, body["data"]["status"]), (200, "RUNNING"))
        runtime = self.store.get_grid_runtime(bot_id)
        self.assertEqual(runtime.config["market"], "FUTURES")
        self.venue.funding[T0 + 2 * MIN + 1000] = "0.0001"
        self.now = T0 + 4 * MIN + 1
        self.runner.tick()
        runtime = self.store.get_grid_runtime(bot_id)
        self.assertEqual(runtime.snapshot["status"], "ACTIVE")
        self.assertGreater(len(runtime.snapshot["fills"]), 0)
        kinds = [event.kind for event in self.store.list_events(bot_id, limit=500)]
        self.assertIn("GRID_FUNDING", kinds)
        self.assertIn("GRID_INIT", kinds)
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/grid")
        self.assertEqual(status, 200, body)
        state = body["data"]
        self.assertEqual((state["direction"], state["leverage"], state["grid_status"]), ("LONG", 5, "ACTIVE"))
        self.assertGreater(len(state["open_lots"]), 0)
        self.assertIsNotNone(state["equity_at_last"])
        self.assertEqual(state["funding_events_count"], 1)
        # Events surface accepts grid kinds (no 500 on a bot with fills).
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/events?limit=50")
        self.assertEqual(status, 200, body)

    def test_stop_loss_stops_and_landmarks(self):
        status, body, _ = self.create_fgrid(strategy=fgrid_strategy(stop_loss_price="78000"))
        bot_id = body["data"]["bot_id"]
        call(self.app, "POST", f"/api/v2/bots/{bot_id}/start", {"revision": 1})
        self.venue.path[T0 + 2 * MIN] = ("84506.01", "84506.01", "77000", "77000")
        self.now = T0 + 4 * MIN + 1
        self.runner.tick()
        bot = self.store.get(bot_id)
        self.assertEqual((bot.status, bot.status_reason), ("STOPPED", "GRID_DONE_SL"))
        self.assertIn(("GRID_STOPPED", bot_id), self.landmarks)

    def test_create_errors_are_problem_details(self):
        cases = [
            ({"strategy": fgrid_strategy(upper_price="70000")}, "GRID_BOUNDS_INVALID"),
            ({"strategy": fgrid_strategy(leverage=11)}, "REQUEST_VALIDATION_FAILED"),
            (
                {"strategy": fgrid_strategy(interval_count=10, leverage=1), "budget": "40"},
                "FGRID_MIN_NOTIONAL_TOO_SMALL",
            ),
        ]
        for overrides, code in cases:
            with self.subTest(code=code):
                status, body, _ = self.create_fgrid(**overrides)
                self.assertEqual((status, body["code"]), (422, code))

    def test_market_outage_is_a_bounded_502(self):
        self.market.down = True
        status, body, _ = self.create_fgrid()
        self.assertEqual((status, body["code"]), (502, "PUBLIC_UPSTREAM_UNAVAILABLE"))


class RealAppFuturesGridBotContractTests(unittest.TestCase):
    def test_routes_are_typed_and_bounded(self):
        import json

        schema = api_module.app.openapi()
        for path, code in (("/api/v2/futures-grid-bots", "201"), ("/api/v2/futures-grid-bots/preview", "200")):
            operation = schema["paths"][path]["post"]
            self.assertIn("$ref", json.dumps(operation["responses"][code]))
            self.assertIn(path, api_module.ROUTE_BODY_LIMITS)


if __name__ == "__main__":
    unittest.main()
