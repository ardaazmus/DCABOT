"""Faz W-B1/W-B3/W-B7: /api/v2/bots — sector-vocabulary bots, durable store,
typed OpenAPI contract, Problem Details errors."""
import asyncio
import itertools
import json
import tempfile
import unittest
from fractions import Fraction as Q
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from dcabot.application.sector_dca import SymbolRules
from dcabot.persistence.bot_store import BOT_ACTIONS, BOT_STATUSES, BotStore, BotStoreError, next_status
from dcabot.server import api as api_module
from dcabot.server import v2_bots

ROOT = Path(__file__).resolve().parents[2]
BTC = SymbolRules("BTCUSDT", "TRADING", "BTC", "USDT", "0.01", "0.00001", "0.00001", "5")
BTC_USDC = SymbolRules("BTCUSDC", "TRADING", "BTC", "USDC", "0.01", "0.00001", "0.00001", "5")


class FakeMarket:
    def __init__(self):
        self.rules = {"BTCUSDT": BTC, "BTCUSDC": BTC_USDC}
        self.price = Q("84506.01")
        self.down = False

    def symbol_rules(self, symbol):
        if self.down:
            raise v2_bots.MarketUnavailable("PUBLIC_UPSTREAM_UNAVAILABLE", "Public market-data alınamadı.")
        return self.rules[symbol]

    def last_price(self, symbol):
        return self.price


def strategy(**overrides):
    body = {
        "symbol": "BTCUSDT",
        "base_order": "100",
        "safety_order": "100",
        "max_safety_orders": 5,
        "max_active_safety_orders": None,
        "price_deviation": "1.5",
        "safety_order_volume_scale": "1.5",
        "safety_order_step_scale": "1",
        "take_profit": "2",
        "stop_loss": "10",
    }
    body.update(overrides)
    return body


def call(app, method, path, body=None, raw=None):
    payload = raw if raw is not None else (json.dumps(body).encode() if body is not None else b"")
    messages = [{"type": "http.request", "body": payload, "more_body": False}]
    sent = []

    async def receive():
        return messages.pop(0) if messages else {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    path_only, _, query = path.partition("?")
    scope = {
        "type": "http", "method": method, "path": path_only, "raw_path": path_only.encode(),
        "query_string": query.encode(),
        "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(payload)).encode())],
        "scheme": "http", "server": ("testserver", 80), "client": ("testclient", 1),
    }
    asyncio.run(app(scope, receive, send))
    start = next(m for m in sent if m["type"] == "http.response.start")
    data = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    headers = {k.decode(): v.decode() for k, v in start["headers"]}
    return start["status"], json.loads(data.decode()) if data else None, headers


class V2BotApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BotStore(Path(self.tmp.name) / "bots.sqlite3")
        self.market = FakeMarket()
        self.runner = False
        self.clock = itertools.count(1_000_000, 1_000)
        template = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
        deps = v2_bots.V2BotDeps(
            store=self.store,
            market=self.market,
            template_loader=lambda: template,
            clock_us=lambda: next(self.clock),
            runner_available=lambda: self.runner,
            problem=api_module._problem,
        )
        self.app = FastAPI()
        self.app.router.route_class = api_module.BoundedAPIRoute
        self.app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_bots.register_routes(self.app, deps)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def create(self, **overrides):
        body = {"name": "BTC dengeli", "mode": "PAPER", "budget": "2000", "strategy": strategy()}
        body.update(overrides)
        return call(self.app, "POST", "/api/v2/bots", body)

    def test_copy_duplicates_setup_as_fresh_stopped(self):
        status, created, _ = self.create()
        self.assertEqual(status, 201)
        source_id = created["data"]["bot_id"]
        status, body, _ = call(self.app, "POST", f"/api/v2/bots/{source_id}/copy", {})
        self.assertEqual(status, 201, body)
        data = body["data"]
        self.assertNotEqual(data["bot_id"], source_id)
        self.assertEqual(data["name"], "BTC dengeli (2)")
        self.assertEqual(
            (data["type"], data["mode"], data["symbol"], data["budget"], data["strategy"]),
            ("DCA", "PAPER", "BTCUSDT", created["data"]["budget"], created["data"]["strategy"]),
        )
        self.assertEqual((data["status"], data["revision"], data["archived"]), ("STOPPED", 1, False))
        self.assertIsNone(self.store.get_runtime(data["bot_id"]))
        self.assertEqual(self.store.list_deals(data["bot_id"]), ())

    def test_copy_honors_explicit_name(self):
        status, created, _ = self.create()
        self.assertEqual(status, 201)
        status, body, _ = call(
            self.app, "POST", f"/api/v2/bots/{created['data']['bot_id']}/copy", {"name": "  Klon  "}
        )
        self.assertEqual(status, 201, body)
        self.assertEqual(body["data"]["name"], "Klon")

    def test_copy_long_name_truncates_to_fit(self):
        status, created, _ = self.create(name="x" * 64)
        self.assertEqual(status, 201)
        status, body, _ = call(self.app, "POST", f"/api/v2/bots/{created['data']['bot_id']}/copy", {})
        self.assertEqual(status, 201, body)
        self.assertLessEqual(len(body["data"]["name"]), 64)
        self.assertTrue(body["data"]["name"].endswith(" (2)"))

    def test_copy_unknown_is_404(self):
        status, body, _ = call(self.app, "POST", "/api/v2/bots/bot_yok/copy", {})
        self.assertEqual((status, body["code"]), (404, "BOT_NOT_FOUND"))

    def test_copy_archived_source_is_allowed(self):
        status, created, _ = self.create()
        self.assertEqual(status, 201)
        source_id = created["data"]["bot_id"]
        status, _, _ = call(
            self.app, "POST", f"/api/v2/bots/{source_id}/archive", {"revision": created["data"]["revision"]}
        )
        self.assertEqual(status, 200)
        status, body, _ = call(self.app, "POST", f"/api/v2/bots/{source_id}/copy", {})
        self.assertEqual(status, 201, body)
        self.assertFalse(body["data"]["archived"])

    def test_preview_speaks_sector_terms_with_exact_engine_numbers(self):
        status, body, _ = call(self.app, "POST", "/api/v2/bots/preview", {"budget": "2000", "strategy": strategy()})
        self.assertEqual(status, 200)
        plan = body["data"]
        self.assertEqual(plan["reference_price"], "84506.01")
        self.assertEqual(plan["base_order"], {"price": "84506.01", "qty": "0.00118", "amount": "99.7170918"})
        self.assertEqual([so["amount"] for so in plan["safety_orders"]], ["99.886092", "149.1868924", "224.3549794", "336.8071136", "505.7472835"])
        self.assertEqual(plan["orders_total"], "1415.6994527")
        # 0.1% per fill, each rounded to 1e-8 like the simulator's own fees
        self.assertEqual(plan["estimated_fees"], "1.41569944")
        self.assertEqual(plan["required_funds"], "1417.11515214")
        self.assertEqual(plan["price_coverage_percent"], "7.5")
        self.assertEqual(plan["take_profit_price"], "86196.14")
        self.assertEqual(plan["stop_loss_price_initial"], "76055.409")
        self.assertIs(plan["within_budget"], True)

    def test_preview_flags_budget_without_failing(self):
        status, body, _ = call(self.app, "POST", "/api/v2/bots/preview", {"budget": "1000", "strategy": strategy()})
        self.assertEqual(status, 200)
        self.assertIs(body["data"]["within_budget"], False)

    def test_create_persists_a_stopped_bot_that_survives_reopen(self):
        status, body, _ = self.create()
        self.assertEqual(status, 201)
        bot = body["data"]
        self.assertTrue(bot["bot_id"].startswith("bot_"))
        self.assertEqual((bot["status"], bot["revision"], bot["mode"], bot["type"]), ("STOPPED", 1, "PAPER", "DCA"))
        self.assertEqual(
            bot["strategy"],
            strategy(
                direction="LONG", cooldown_seconds=0, min_price=None, max_price=None,
                market_type="SPOT", leverage=1, symbols=["BTCUSDT"], max_active_deals=1,
                combined_take_profit=None, trailing_take_profit=None,
            ),
        )
        self.assertEqual(call(self.app, "GET", "/api/v2/bots")[1]["data"], [bot])
        reopened = BotStore(self.store.path)
        try:
            self.assertEqual(reopened.get(bot["bot_id"]).name, "BTC dengeli")
        finally:
            reopened.close()

    def test_create_rejects_what_the_venue_or_budget_would_reject(self):
        cases = [
            ({"budget": "1000"}, "SECTOR_BUDGET_TOO_LOW", "budget"),
            ({"strategy": strategy(base_order="3")}, "SECTOR_BASE_ORDER_TOO_SMALL", "strategy.base_order"),
            ({"strategy": strategy(symbol="BTCUSDC")}, "SECTOR_QUOTE_UNSUPPORTED", "strategy.symbol"),
            ({"strategy": strategy(safety_order="1")}, "SECTOR_CONFIG_INVALID", "strategy"),
            ({"strategy": strategy(take_profit="100")}, "SECTOR_FIELD_OUT_OF_RANGE", "strategy.take_profit"),
            (
                {"strategy": strategy(min_price="90000", max_price="80000")},
                "SECTOR_FIELD_OUT_OF_RANGE",
                "strategy.min_price",
            ),
            (
                {"strategy": strategy(leverage=3)},
                "SECTOR_FIELD_OUT_OF_RANGE",
                "strategy.leverage",
            ),
        ]
        for overrides, code, field in cases:
            with self.subTest(code=code):
                status, body, headers = self.create(**overrides)
                self.assertEqual(status, 422)
                self.assertEqual(body["code"], code)
                self.assertEqual(body["errors"][0]["field"], field)
                self.assertEqual(headers["content-type"], "application/problem+json")
        self.assertEqual(self.store.list(), ())

    def test_create_echoes_entry_gates(self):
        status, body, _ = self.create(
            strategy=strategy(cooldown_seconds=300, min_price="80000", max_price="90000")
        )
        self.assertEqual(status, 201)
        echoed = body["data"]["strategy"]
        self.assertEqual(
            (echoed["cooldown_seconds"], echoed["min_price"], echoed["max_price"]), (300, "80000", "90000")
        )

    def test_create_echoes_trailing_and_rejects_it_with_combo(self):
        status, body, _ = self.create(strategy=strategy(trailing_take_profit="1"))
        self.assertEqual(status, 201)
        self.assertEqual(body["data"]["strategy"]["trailing_take_profit"], "1")
        status, body, _ = self.create(
            strategy=strategy(trailing_take_profit="1", combined_take_profit="5")
        )
        self.assertEqual(status, 422)
        self.assertEqual(body["code"], "SECTOR_FIELD_OUT_OF_RANGE")
        self.assertEqual(body["errors"][0]["field"], "strategy.trailing_take_profit")

    def test_create_resolves_futures_leverage_default(self):
        status, body, _ = self.create(strategy=strategy(market_type="FUTURES"))
        self.assertEqual(status, 201)
        echoed = body["data"]["strategy"]
        self.assertEqual((echoed["market_type"], echoed["leverage"]), ("FUTURES", 3))

    def test_create_echoes_explicit_futures_leverage(self):
        status, body, _ = self.create(strategy=strategy(market_type="FUTURES", leverage=7))
        self.assertEqual(status, 201)
        self.assertEqual(body["data"]["strategy"]["leverage"], 7)

    def test_create_rejects_leverage_above_ten_at_the_boundary(self):
        status, body, _ = self.create(strategy=strategy(market_type="FUTURES", leverage=11))
        self.assertEqual(status, 422)
        self.assertEqual(body["code"], "REQUEST_VALIDATION_FAILED")
        self.assertEqual(body["errors"][0]["field"], "strategy.leverage")

    def test_create_rejects_negative_cooldown_at_the_boundary(self):
        status, body, _ = self.create(strategy=strategy(cooldown_seconds=-1))
        self.assertEqual(status, 422)
        self.assertEqual(body["code"], "REQUEST_VALIDATION_FAILED")
        self.assertEqual(body["errors"][0]["field"], "strategy.cooldown_seconds")

    def test_schema_violations_are_problem_details(self):
        for bad in (
            {"name": "x", "mode": "PAPER", "budget": "2000", "strategy": strategy(), "extra": 1},
            {"name": "x", "mode": "LIVE", "budget": "2000", "strategy": strategy()},
            {"name": "x", "mode": "PAPER", "budget": "1e3", "strategy": strategy()},
            {"name": "x", "mode": "PAPER", "budget": "2000", "strategy": strategy(max_safety_orders=51)},
        ):
            with self.subTest(bad=list(bad)):
                status, body, headers = call(self.app, "POST", "/api/v2/bots", bad)
                self.assertEqual(status, 422)
                self.assertEqual(body["code"], "REQUEST_VALIDATION_FAILED")
                self.assertTrue(body["errors"])

    def test_market_outage_is_a_bounded_502(self):
        self.market.down = True
        status, body, _ = self.create()
        self.assertEqual((status, body["code"]), (502, "PUBLIC_UPSTREAM_UNAVAILABLE"))

    def test_start_is_refused_while_no_runner_exists(self):
        bot = self.create()[1]["data"]
        status, body, _ = call(self.app, "POST", f"/api/v2/bots/{bot['bot_id']}/start", {"revision": 1})
        self.assertEqual((status, body["code"]), (409, "BOT_RUNNER_UNAVAILABLE"))
        self.assertEqual(self.store.get(bot["bot_id"]).status, "STOPPED")

    def test_lifecycle_with_optimistic_revision(self):
        self.runner = True
        bot_id = self.create()[1]["data"]["bot_id"]
        path = f"/api/v2/bots/{bot_id}"
        expectations = [("start", 1, "RUNNING"), ("pause", 2, "PAUSED"), ("resume", 3, "RUNNING"), ("stop", 4, "STOPPED")]
        for action, revision, expected in expectations:
            status, body, _ = call(self.app, "POST", f"{path}/{action}", {"revision": revision})
            self.assertEqual((status, body["data"]["status"], body["data"]["revision"]), (200, expected, revision + 1))
        self.assertEqual(call(self.app, "POST", f"{path}/pause", {"revision": 5})[1]["code"], "BOT_TRANSITION_INVALID")
        self.assertEqual(call(self.app, "POST", f"{path}/start", {"revision": 4})[1]["code"], "BOT_REVISION_CONFLICT")
        status, body, _ = call(self.app, "POST", f"{path}/archive", {"revision": 5})
        self.assertEqual((status, body["data"]["archived"]), (200, True))
        self.assertEqual(call(self.app, "GET", "/api/v2/bots")[1]["data"], [])
        self.assertEqual(len(call(self.app, "GET", "/api/v2/bots?include_archived=true")[1]["data"]), 1)
        self.assertEqual(call(self.app, "POST", f"{path}/stop", {"revision": 6})[1]["code"], "BOT_ARCHIVED")

    def test_unknown_bot_and_action(self):
        self.assertEqual(call(self.app, "GET", "/api/v2/bots/bot_nope")[0], 404)
        self.assertEqual(call(self.app, "POST", "/api/v2/bots/bot_nope/explode", {"revision": 1})[0], 422)


class BotLifecycleRuleTests(unittest.TestCase):
    def test_every_status_action_pair_is_either_allowed_or_refused(self):
        allowed = {
            ("STOPPED", "start"): "RUNNING",
            ("RUNNING", "pause"): "PAUSED",
            ("PAUSED", "resume"): "RUNNING",
            ("RUNNING", "stop"): "STOPPED",
            ("PAUSED", "stop"): "STOPPED",
            ("ERROR", "stop"): "STOPPED",
        }
        for status, action in itertools.product(BOT_STATUSES, BOT_ACTIONS):
            with self.subTest(status=status, action=action):
                if (status, action) in allowed:
                    self.assertEqual(next_status(status, action), allowed[(status, action)])
                else:
                    with self.assertRaises(BotStoreError):
                        next_status(status, action)


class RealAppContractTests(unittest.TestCase):
    def test_v2_routes_are_registered_typed_and_body_bounded(self):
        schema = api_module.app.openapi()
        v2 = {path: ops for path, ops in schema["paths"].items() if path.startswith("/api/v2/")}
        self.assertEqual(
            set(v2),
            {
                "/api/v2/bots", "/api/v2/bots/preview", "/api/v2/bots/{bot_id}", "/api/v2/bots/{bot_id}/{action}",
                "/api/v2/bots/{bot_id}/deals", "/api/v2/bots/{bot_id}/events", "/api/v2/bots/{bot_id}/stats",
                "/api/v2/bots/{bot_id}/replay", "/api/v2/bots/{bot_id}/copy",
                "/api/v2/backtests", "/api/v2/grid-backtests", "/api/v2/futures-grid-backtests", "/api/v2/grid-bots", "/api/v2/grid-bots/preview",
                "/api/v2/futures-grid-bots", "/api/v2/futures-grid-bots/preview",
                "/api/v2/bots/{bot_id}/grid", "/api/v2/deals", "/api/v2/bots/{bot_id}/deals/{deal_seq}",
                "/api/v2/bots/{bot_id}/deals/{deal_seq}/close", "/api/v2/bots/{bot_id}/deals/{deal_seq}/cancel",
                "/api/v2/bots/{bot_id}/deals/{deal_seq}/add-funds", "/api/v2/stats/portfolio/summary",
                "/api/v2/stats/portfolio/equity", "/api/v2/stats/portfolio/daily-profit",
                "/api/v2/stats/portfolio/by-bot", "/api/v2/stats/portfolio/by-pair",
                "/api/v2/risk/correlation-matrix",
            },
        )
        for path, ops in v2.items():
            for method, op in ops.items():
                success = next(code for code in op["responses"] if code.startswith("2"))
                self.assertIn("$ref", json.dumps(op["responses"][success]), f"{method} {path} has no typed response")
        status, body, headers = call(api_module.app, "POST", "/api/v2/bots/preview", raw=b"{" + b" " * 5000 + b"}")
        self.assertEqual((status, body["code"]), (413, "REQUEST_TOO_LARGE"))



class LiveMarketRulesCacheTests(unittest.TestCase):
    def test_rules_are_reused_within_ttl_and_refetched_after(self):
        from unittest import mock

        from dcabot.data_adapters.binance_public_transport import BinancePublicSymbolRules, BinancePublicTransportError

        calls = []

        def fetch_rules(symbol, *, allowed_symbols):
            calls.append(symbol)
            return BinancePublicSymbolRules(symbol, "TRADING", "BTC", "USDT", "0.01", "0.00001", "0.00001", "5")

        market = v2_bots.LiveBinanceMarket(
            fetch_rules=fetch_rules, fetch_trades=None, transport_error=BinancePublicTransportError, time_unit=None
        )
        self.assertEqual(market.symbol_rules("BTCUSDT"), market.symbol_rules("BTCUSDT"))
        self.assertEqual(calls, ["BTCUSDT"])
        with mock.patch.object(v2_bots.time, "monotonic", return_value=v2_bots.time.monotonic() + 601):
            market.symbol_rules("BTCUSDT")
        self.assertEqual(calls, ["BTCUSDT", "BTCUSDT"])

    def test_failures_are_not_cached(self):
        from dcabot.data_adapters.binance_public_transport import BinancePublicTransportError

        def fail(symbol, *, allowed_symbols):
            raise BinancePublicTransportError("PUBLIC_UPSTREAM_UNAVAILABLE", "down")

        market = v2_bots.LiveBinanceMarket(fetch_rules=fail, fetch_trades=None, transport_error=BinancePublicTransportError, time_unit=None)
        for _ in range(2):
            with self.assertRaises(v2_bots.MarketUnavailable):
                market.symbol_rules("BTCUSDT")


if __name__ == "__main__":
    unittest.main()
