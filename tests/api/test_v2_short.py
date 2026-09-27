"""Faz G1: SHORT botlar -- API kabul, onizleme tersligi, uPnL isareti."""
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
from dcabot.domain.engine import State, apply
from dcabot.persistence.bot_store import BotDeal, BotEvent, BotRecord, BotRuntime, BotStore
from dcabot.server import api as api_module
from dcabot.server import v2_bots

ROOT = Path(__file__).resolve().parents[2]
BTC = SymbolRules("BTCUSDT", "TRADING", "BTC", "USDT", "0.01", "0.00001", "0.00001", "5")


class FakeMarket:
    def __init__(self):
        self.rules = {"BTCUSDT": BTC}
        self.price = Q("84506.01")

    def symbol_rules(self, symbol):
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
        "direction": "SHORT",
    }
    body.update(overrides)
    return body


def call(app, method, path, body=None):
    payload = json.dumps(body).encode() if body is not None else b""
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
    return start["status"], json.loads(data.decode()) if data else None


def short_base_fill():
    """SHORT BASE 1@100 (satis): qty 1, cost 100, yan SELL."""
    raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
    raw["direction"] = "SHORT"
    from dcabot.domain.config import Config

    config = Config.parse(raw)
    state = apply(State(), {"type": "MARK", "price": "100"}, config)
    state = apply(
        state,
        {"type": "INTENT", "order_id": "base", "role": "BASE", "qty": "1", "limit_price": "100"},
        config,
    )
    assert state.orders["base"].side == "SELL"
    state = apply(
        state,
        {
            "type": "FILL", "execution_id": "base-fill", "order_id": "base", "side": "SELL",
            "qty": "1", "price": "100", "fee": "0", "fee_asset": "USDT",
        },
        config,
    )
    state = apply(
        state,
        {"type": "ORDER_FINAL", "order_id": "base", "status": "FILLED", "filled_qty": "1", "coverage_complete": True},
        config,
    )
    return state, raw


class V2ShortApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BotStore(Path(self.tmp.name) / "bots.sqlite3")
        self.market = FakeMarket()
        template = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
        self.clock = itertools.count(1_000_000, 1_000)
        deps = v2_bots.V2BotDeps(
            store=self.store,
            market=self.market,
            template_loader=lambda: template,
            clock_us=lambda: next(self.clock),
            runner_available=lambda: True,
            problem=api_module._problem,
        )
        self.app = FastAPI()
        self.app.router.route_class = api_module.BoundedAPIRoute
        self.app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_bots.register_routes(self.app, deps)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_create_short_bot(self):
        status, body = call(
            self.app, "POST", "/api/v2/bots",
            {"name": "Kisa", "mode": "PAPER", "budget": "2000", "strategy": strategy()},
        )
        self.assertEqual(status, 201)
        self.assertEqual(body["data"]["strategy"]["direction"], "SHORT")

    def test_create_defaults_to_long(self):
        raw = strategy()
        del raw["direction"]
        status, body = call(
            self.app, "POST", "/api/v2/bots",
            {"name": "Uzun", "mode": "PAPER", "budget": "2000", "strategy": raw},
        )
        self.assertEqual(status, 201)
        self.assertEqual(body["data"]["strategy"]["direction"], "LONG")

    def test_preview_short_inverts_levels(self):
        status, body = call(
            self.app, "POST", "/api/v2/bots/preview",
            {"budget": "2000", "strategy": strategy()},
        )
        self.assertEqual(status, 200)
        plan = body["data"]
        base = Q(plan["base_order"]["price"])
        self.assertLess(Q(plan["take_profit_price"]), base)
        self.assertGreater(Q(plan["safety_orders"][0]["price"]), base)
        self.assertGreater(Q(plan["stop_loss_price_initial"]), base)

    def test_start_short_paper(self):
        status, created = call(
            self.app, "POST", "/api/v2/bots",
            {"name": "Kisa", "mode": "PAPER", "budget": "2000", "strategy": strategy()},
        )
        status, body = call(
            self.app, "POST", f"/api/v2/bots/{created['data']['bot_id']}/start",
            {"revision": created["data"]["revision"]},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["status"], "RUNNING")

    def test_short_open_deal_flips_unrealized(self):
        status, created = call(
            self.app, "POST", "/api/v2/bots",
            {"name": "Kisa", "mode": "PAPER", "budget": "2000", "strategy": strategy()},
        )
        bot_id = created["data"]["bot_id"]
        state, raw = short_base_fill()
        from dcabot.domain.config import Config

        state = apply(state, {"type": "MARK", "price": "90"}, Config.parse(raw))
        self.store.save_runtime(
            BotRuntime(bot_id, raw, state, 1, Q(0), 60_000_000, 2_000_000),
            deals=(BotDeal(bot_id, 1, 1000, None, 0, None, None, 0, "BTCUSDT"),),
            events=(BotEvent(bot_id, 1000, "DEAL_STARTED", {"deal": 1, "price": "100", "qty": "1", "fee": "0"}),),
        )
        status, body = call(self.app, "GET", f"/api/v2/bots/{bot_id}/deals/1")
        self.assertEqual(status, 200)
        # Short 1@100, piyasa 90: maliyet - tutar = 10 kâr.
        self.assertEqual(body["data"]["unrealized_profit"], "10")
        self.assertEqual(body["data"]["unrealized_percent"], "10")
        self.assertEqual(body["data"]["direction"], "SHORT")
        status, body = call(self.app, "GET", "/api/v2/deals?status=active")
        self.assertEqual(body["data"][0]["direction"], "SHORT")

    def test_legacy_strategy_reads_as_long(self):
        legacy = strategy()
        del legacy["direction"]
        record = self.store.create(
            BotRecord(
                "bot_legacy0001", "Eski", "DCA", "PAPER", "BTCUSDT", legacy, "2000",
                "STOPPED", None, 1, 1_000_000, 1_000_000, None,
            )
        )
        status, body = call(self.app, "GET", f"/api/v2/bots/{record.bot_id}")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["strategy"]["direction"], "LONG")
        status, body = call(
            self.app, "POST", f"/api/v2/bots/{record.bot_id}/start", {"revision": record.revision}
        )
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
