"""M1: multi-pair DCA — per-symbol runtimes, shared cap, sequenced deals."""

import itertools
import json
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from api.test_v2_bots import call, strategy
from dcabot.application.sector_dca import SymbolRules, max_deal_quote_cost, parse_sector_dca
from dcabot.data_adapters.binance_public_transport import BinancePublicKline, BinancePublicTransportError
from dcabot.domain.numbers import Q, exact_text
from dcabot.persistence.bot_store import BotStore
from dcabot.server import api as api_module
from dcabot.server import bot_runner, v2_bots

ROOT = Path(__file__).resolve().parents[2]
MIN = 60_000_000
T0 = 1_790_000_000 * 1_000_000 // MIN * MIN
BTC = SymbolRules("BTCUSDT", "TRADING", "BTC", "USDT", "0.01", "0.00001", "0.00001", "5")
ETH = SymbolRules("ETHUSDT", "TRADING", "ETH", "USDT", "0.01", "0.0001", "0.0001", "5")


class FakeMultiMarket:
    def __init__(self):
        self.rules = {"BTCUSDT": BTC, "ETHUSDT": ETH}
        self.prices = {"BTCUSDT": Q("84506.01"), "ETHUSDT": Q("3000")}
        self.down = False

    def symbol_rules(self, symbol):
        if self.down:
            raise v2_bots.MarketUnavailable("PUBLIC_UPSTREAM_UNAVAILABLE", "down")
        return self.rules[symbol]

    def last_price(self, symbol):
        if self.down:
            raise v2_bots.MarketUnavailable("PUBLIC_UPSTREAM_UNAVAILABLE", "down")
        return self.prices[symbol]


class MultiVenue:
    def __init__(self):
        self.paths: dict[str, dict[int, tuple[str, str, str, str]]] = {}
        self.down = False

    def fetch_range(self, symbol, *, interval, start_us, end_us, max_bars, now_us, allowed_symbols):
        if self.down:
            raise BinancePublicTransportError("PUBLIC_UPSTREAM_UNAVAILABLE", "down")
        flat = {"BTCUSDT": "84506.01", "ETHUSDT": "3000"}[symbol]
        bars = []
        t = start_us
        while t < end_us and t + MIN - 1 < now_us:
            o, h, low, c = self.paths.get(symbol, {}).get(t, (flat, flat, flat, flat))
            bars.append(BinancePublicKline(t, t + MIN - 1, o, h, low, c, "1"))
            t += MIN
        return tuple(bars)


def multi_strategy(**overrides):
    body = strategy(stop_loss=None)
    body["symbols"] = ["BTCUSDT", "ETHUSDT"]
    body["max_active_deals"] = 2
    body.update(overrides)
    return body


class MultiPairServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BotStore(Path(self.tmp.name) / "bots.sqlite3")
        self.now = T0 + 5_000_000
        self.venue = MultiVenue()
        self.landmarks = []
        template = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
        self.runner = bot_runner.PaperBotRunner(
            bot_runner.RunnerDeps(
                store=self.store,
                market=FakeMultiMarket(),
                fetch_range=self.venue.fetch_range,
                transport_error=BinancePublicTransportError,
                template_loader=lambda: template,
                clock_us=lambda: self.now,
                kill_switch_engaged=lambda: False,
                record_event=lambda kind, ref, summary, time_us: self.landmarks.append((kind, ref, summary)),
            )
        )
        ids = itertools.count(1)
        deps = v2_bots.V2BotDeps(
            store=self.store,
            market=FakeMultiMarket(),
            template_loader=lambda: template,
            clock_us=lambda: self.now + next(ids),
            runner_available=lambda: True,
            problem=api_module._problem,
            on_start=self.runner.prepare_start,
        )
        self.app = FastAPI()
        self.app.router.route_class = api_module.BoundedAPIRoute
        self.app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_bots.register_routes(self.app, deps)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def _budget_for(self, body, deals=2):
        params = parse_sector_dca(body)
        template = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
        cap = max_deal_quote_cost(params, fee_rate=Q(1, 1000), fee_quantum=Q(1, 10**8))
        return exact_text(cap * deals), exact_text(cap)

    def _create_and_start(self, **overrides):
        body = multi_strategy(**overrides)
        budget, _ = self._budget_for(body, body["max_active_deals"])
        status, created, _ = call(
            self.app, "POST", "/api/v2/bots", {"name": "multi", "mode": "PAPER", "budget": budget, "strategy": body}
        )
        self.assertEqual(status, 201, created)
        bot_id = created["data"]["bot_id"]
        status, started, _ = call(self.app, "POST", f"/api/v2/bots/{bot_id}/start", {"revision": 1})
        self.assertEqual(status, 200, started)
        return bot_id

    def test_start_creates_one_runtime_per_symbol(self):
        bot_id = self._create_and_start()
        runtimes = self.store.get_pair_runtimes(bot_id)
        self.assertEqual([r.symbol for r in runtimes], ["BTCUSDT", "ETHUSDT"])
        self.assertIsNone(self.store.get_runtime(bot_id))
        for runtime in runtimes:
            self.assertEqual(runtime.config["symbol"], runtime.symbol)

    def test_tick_opens_one_deal_per_symbol_with_shared_sequence(self):
        bot_id = self._create_and_start()
        self.now = T0 + 4 * MIN + 1
        self.runner.tick()
        deals = self.store.list_deals(bot_id)
        self.assertEqual([(d.deal_sequence, d.symbol) for d in deals], [(1, "BTCUSDT"), (2, "ETHUSDT")])
        opened = [entry for entry in self.landmarks if entry[0] == "DEAL_OPENED"]
        self.assertEqual(
            [(ref, summary) for _, ref, summary in opened],
            [(f"{bot_id}:1", "Deal 1 açıldı (BTCUSDT)."), (f"{bot_id}:2", "Deal 2 açıldı (ETHUSDT).")],
        )

    def test_max_active_deals_caps_new_opens(self):
        bot_id = self._create_and_start(max_active_deals=1)
        self.now = T0 + 4 * MIN + 1
        self.runner.tick()
        deals = self.store.list_deals(bot_id)
        self.assertEqual([(d.deal_sequence, d.symbol) for d in deals], [(1, "BTCUSDT")])

    def test_budget_gate_rejects_at_create(self):
        body = multi_strategy()
        _, cap = self._budget_for(body)
        status, created, _ = call(
            self.app, "POST", "/api/v2/bots",
            {"name": "multi", "mode": "PAPER", "budget": cap, "strategy": body},
        )
        self.assertEqual(status, 422)
        self.assertEqual((created["code"], created["errors"][0]["field"]), ("SECTOR_MULTI_BUDGET_EXCEEDED", "budget"))

    def test_preview_reports_multi_totals(self):
        body = multi_strategy()
        budget, cap = self._budget_for(body)
        status, preview, _ = call(
            self.app, "POST", "/api/v2/bots/preview", {"budget": budget, "strategy": body}
        )
        self.assertEqual(status, 200, preview)
        data = preview["data"]
        self.assertEqual(data["symbols"], ["BTCUSDT", "ETHUSDT"])
        self.assertEqual(data["total_required_funds"], exact_text(Q(cap) * 2))
        self.assertIs(data["within_total_budget"], True)

    def test_deals_carry_symbols_and_detail_routes_live_pair(self):
        bot_id = self._create_and_start()
        self.now = T0 + 4 * MIN + 1
        self.runner.tick()
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/deals")
        self.assertEqual(status, 200)
        self.assertEqual([(row["deal"], row["symbol"]) for row in body["data"]], [(1, "BTCUSDT"), (2, "ETHUSDT")])
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/deals/2")
        self.assertEqual(status, 200, body)
        self.assertEqual(body["data"]["symbol"], "ETHUSDT")
        self.assertIsNotNone(body["data"]["qty"])
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/stats")
        self.assertEqual(status, 200)
        self.assertIsNotNone(body["data"]["active_deal"])

    def test_close_action_routes_to_the_deal_pair(self):
        bot_id = self._create_and_start()
        self.now = T0 + 4 * MIN + 1
        self.runner.tick()
        record = self.store.get(bot_id)
        status, body, _ = call(
            self.app, "POST", f"/api/v2/bots/{bot_id}/deals/2/close", {"revision": record.revision}
        )
        self.assertEqual(status, 200, body)
        self.assertEqual(body["data"]["close_reason"], "MANUAL_CLOSE")
        self.assertEqual(body["data"]["symbol"], "ETHUSDT")
        deals = self.store.list_deals(bot_id)
        self.assertIsNone(next(d for d in deals if d.deal_sequence == 1).closed_at_us)
        self.assertIsNotNone(next(d for d in deals if d.deal_sequence == 2).closed_at_us)

    def test_second_symbol_rules_failure_is_a_502(self):
        market = FakeMultiMarket()
        broken = market.symbol_rules

        def failing(symbol):
            if symbol == "ETHUSDT":
                raise v2_bots.MarketUnavailable("PUBLIC_UPSTREAM_UNAVAILABLE", "down")
            return broken(symbol)

        market.symbol_rules = failing
        ids = itertools.count(1000)
        template = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
        deps = v2_bots.V2BotDeps(
            store=self.store,
            market=market,
            template_loader=lambda: template,
            clock_us=lambda: self.now + next(ids),
            runner_available=lambda: True,
            problem=api_module._problem,
            on_start=self.runner.prepare_start,
        )
        app = FastAPI()
        v2_bots.register_routes(app, deps)
        body = multi_strategy()
        budget, _ = self._budget_for(body)
        status, created, _ = call(
            app, "POST", "/api/v2/bots", {"name": "multi", "mode": "PAPER", "budget": budget, "strategy": body}
        )
        self.assertEqual((status, created["code"]), (502, "PUBLIC_UPSTREAM_UNAVAILABLE"))


if __name__ == "__main__":
    unittest.main()
