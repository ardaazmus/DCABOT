"""Faz W-B6: v2 bot/deal landmarks for the SSE channel."""
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
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply
from dcabot.persistence.bot_store import BotDeal, BotRuntime, BotStore
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


def base_fill(price="100", fee="0"):
    config = Config.parse(json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8")))
    state = apply(State(), {"type": "MARK", "price": price}, config)
    state = apply(
        state,
        {"type": "INTENT", "order_id": "base", "role": "BASE", "qty": "1", "limit_price": price},
        config,
    )
    state = apply(
        state,
        {
            "type": "FILL", "execution_id": "base-fill", "order_id": "base", "side": "BUY",
            "qty": "1", "price": price, "fee": fee, "fee_asset": "USDT",
        },
        config,
    )
    return apply(
        state,
        {"type": "ORDER_FINAL", "order_id": "base", "status": "FILLED", "filled_qty": "1", "coverage_complete": True},
        config,
    )


class LifecycleEventTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BotStore(Path(self.tmp.name) / "bots.sqlite3")
        self.market = FakeMarket()
        self.landmarks = []
        template = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
        self.clock = itertools.count(1_000_000, 1_000)
        deps = v2_bots.V2BotDeps(
            store=self.store,
            market=self.market,
            template_loader=lambda: template,
            clock_us=lambda: next(self.clock),
            runner_available=lambda: True,
            problem=api_module._problem,
            record_event=lambda kind, ref, summary, time_us: self.landmarks.append((kind, ref, summary, time_us)),
        )
        self.app = FastAPI()
        self.app.router.route_class = api_module.BoundedAPIRoute
        self.app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_bots.register_routes(self.app, deps)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def create(self, name="Akis botu"):
        body = {"name": name, "mode": "PAPER", "budget": "2000", "strategy": strategy()}
        return call(self.app, "POST", "/api/v2/bots", body)

    def seed_open_deal(self, bot_id):
        raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
        self.store.save_runtime(
            BotRuntime(bot_id, raw, base_fill(), 1, Q(0), 60_000_000, 2_000_000),
            deals=(BotDeal(bot_id, 1, 1000, None, 0, None, None, 0, "BTCUSDT"),),
        )

    def test_create_emits_bot_created(self):
        status, created = self.create()
        self.assertEqual(status, 201)
        bot_id = created["data"]["bot_id"]
        self.assertEqual(
            self.landmarks,
            [("BOT_CREATED", bot_id, "Bot oluşturuldu (Akis botu).", 1_000_000)],
        )

    def test_lifecycle_actions_emit_in_order(self):
        _, created = self.create()
        bot_id = created["data"]["bot_id"]
        revision = created["data"]["revision"]
        for action, kind in (
            ("start", "BOT_STARTED"), ("pause", "BOT_PAUSED"), ("resume", "BOT_RESUMED"),
            ("stop", "BOT_STOPPED"), ("archive", "BOT_ARCHIVED"),
        ):
            with self.subTest(action=action):
                status, body = call(self.app, "POST", f"/api/v2/bots/{bot_id}/{action}", {"revision": revision})
                self.assertEqual(status, 200)
                revision = body["data"]["revision"]
        self.assertEqual(
            [entry[0] for entry in self.landmarks],
            ["BOT_CREATED", "BOT_STARTED", "BOT_PAUSED", "BOT_RESUMED", "BOT_STOPPED", "BOT_ARCHIVED"],
        )
        self.assertTrue(all(entry[1] == bot_id for entry in self.landmarks))

    def test_failed_action_emits_nothing(self):
        _, created = self.create()
        bot_id = created["data"]["bot_id"]
        status, _ = call(self.app, "POST", f"/api/v2/bots/{bot_id}/pause", {"revision": 999})
        self.assertEqual(status, 409)
        self.assertEqual([entry[0] for entry in self.landmarks], ["BOT_CREATED"])

    def test_deal_actions_emit(self):
        cases = (
            ("close", {"revision": None}, "DEAL_CLOSED"),
            ("cancel", {"revision": None}, "DEAL_CANCELLED"),
            ("add-funds", {"revision": None, "amount": "50"}, "DEAL_FUNDS_ADDED"),
        )
        self.market.price = Q(110)
        for action, extra, kind in cases:
            with self.subTest(action=action):
                _, created = self.create(f"Deal {action}")
                bot_id = created["data"]["bot_id"]
                self.seed_open_deal(bot_id)
                body = dict(extra, revision=created["data"]["revision"])
                status, _ = call(self.app, "POST", f"/api/v2/bots/{bot_id}/deals/1/{action}", body)
                self.assertEqual(status, 200)
                self.assertIn((kind, f"{bot_id}:1"), [(entry[0], entry[1]) for entry in self.landmarks])


if __name__ == "__main__":
    unittest.main()
