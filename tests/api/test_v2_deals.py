"""Faz W-B4: /api/v2/deals -- botlar arasi birlesik deal listesi/detayi ve
deal aksiyonlari (close at market, cancel, add funds)."""
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


def engine_config():
    return Config.parse(json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8")))


def base_fill(price="100", fee="0"):
    config = engine_config()
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
    ), config


class V2DealsApiTests(unittest.TestCase):
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

    def create(self, name="BTC dengeli"):
        body = {"name": name, "mode": "PAPER", "budget": "2000", "strategy": strategy()}
        return call(self.app, "POST", "/api/v2/bots", body)

    def seed_runtime(self, bot_id, state, deals=(), events=(), prev_net=Q(0), seq=1):
        raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
        self.store.save_runtime(
            BotRuntime(bot_id, raw, state, seq, prev_net, 60_000_000, 2_000_000),
            deals=deals, events=events,
        )

    def test_deals_empty(self):
        status, body, _ = call(self.app, "GET", "/api/v2/deals")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"data": []})

    def test_deals_unified_newest_first_with_status_filter(self):
        _, first, _ = self.create("Birinci")
        _, second, _ = self.create("Ikinci")
        open_state, _ = base_fill()
        self.seed_runtime(
            first["data"]["bot_id"], open_state,
            deals=(BotDeal(first["data"]["bot_id"], 1, 1000, None, 0, None, None, 0, "BTCUSDT"),),
        )
        closed_state, _ = base_fill()
        self.seed_runtime(
            second["data"]["bot_id"], closed_state,
            deals=(BotDeal(second["data"]["bot_id"], 1, 2000, 3000, 2, "5", "TAKE_PROFIT", 0, "BTCUSDT"),),
        )
        status, body, _ = call(self.app, "GET", "/api/v2/deals")
        self.assertEqual(status, 200)
        self.assertEqual([row["bot_name"] for row in body["data"]], ["Ikinci", "Birinci"])
        self.assertEqual(body["data"][0]["symbol"], "BTCUSDT")
        self.assertEqual(body["data"][0]["manual_orders_filled"], 0)
        status, body, _ = call(self.app, "GET", "/api/v2/deals?status=active")
        self.assertEqual([row["bot_name"] for row in body["data"]], ["Birinci"])
        status, body, _ = call(self.app, "GET", "/api/v2/deals?status=closed")
        self.assertEqual([row["bot_name"] for row in body["data"]], ["Ikinci"])
        status, body, _ = call(self.app, "GET", "/api/v2/deals?limit=1&offset=1")
        self.assertEqual([row["bot_name"] for row in body["data"]], ["Birinci"])

    def test_deals_rejects_bad_query(self):
        status, _, _ = call(self.app, "GET", "/api/v2/deals?status=yanlis")
        self.assertEqual(status, 422)
        status, _, _ = call(self.app, "GET", "/api/v2/deals?limit=0")
        self.assertEqual(status, 422)

    def test_deal_detail_open_shows_live_economics(self):
        _, created, _ = self.create()
        bot_id = created["data"]["bot_id"]
        state, config = base_fill()
        state = apply(state, {"type": "MARK", "price": "110"}, config)
        deal = BotDeal(bot_id, 1, 1000, None, 0, None, None, 0, "BTCUSDT")
        events = (BotEvent(bot_id, 1000, "DEAL_STARTED", {"deal": 1, "price": "100", "qty": "1", "fee": "0"}),)
        self.seed_runtime(bot_id, state, deals=(deal,), events=events)
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/deals/1")
        self.assertEqual(status, 200)
        data = body["data"]
        self.assertEqual(data["bot_name"], "BTC dengeli")
        self.assertEqual(data["qty"], "1")
        self.assertEqual(data["cost"], "100")
        self.assertEqual(data["average_price"], "100")
        self.assertEqual(data["mark_price"], "110")
        self.assertEqual(data["unrealized_profit"], "10")
        self.assertEqual(data["unrealized_percent"], "10")
        self.assertEqual(data["take_profit_price"], "102")
        self.assertEqual(data["next_safety_order_price"], "90")
        self.assertIsNone(data["profit"])
        self.assertEqual([e["kind"] for e in data["events"]], ["DEAL_STARTED"])

    def test_deal_detail_closed_replays_fills(self):
        _, created, _ = self.create()
        bot_id = created["data"]["bot_id"]
        state, _ = base_fill()
        deal = BotDeal(bot_id, 1, 1000, 2000, 1, "9.61", "MANUAL_CLOSE", 0, "BTCUSDT")
        events = (
            BotEvent(bot_id, 1000, "DEAL_STARTED", {"deal": 1, "price": "100", "qty": "1", "fee": "0"}),
            BotEvent(bot_id, 1500, "SAFETY_ORDER_FILLED", {"deal": 1, "index": 1, "price": "90", "qty": "1", "fee": "0"}),
            BotEvent(bot_id, 2000, "DEAL_CLOSED", {"deal": 1, "reason": "MANUAL_CLOSE", "price": "100", "qty": "2", "fee": "0.2", "profit": "9.61"}),
        )
        self.seed_runtime(bot_id, state, deals=(deal,), events=events)
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/deals/1")
        self.assertEqual(status, 200)
        data = body["data"]
        self.assertEqual(data["qty"], "2")
        self.assertEqual(data["cost"], "190")
        self.assertEqual(data["average_price"], "95")
        self.assertEqual(data["duration_us"], 1000)
        self.assertEqual(data["cumulative_profit"], "9.61")
        self.assertIsNone(data["mark_price"])
        self.assertEqual(len(data["events"]), 3)

    def test_deal_detail_closed_reports_gross_net_fees(self):
        _, created, _ = self.create()
        bot_id = created["data"]["bot_id"]
        state, _ = base_fill()
        deal = BotDeal(bot_id, 1, 1000, 2000, 1, "9.61", "MANUAL_CLOSE", 0, "BTCUSDT")
        events = (
            BotEvent(bot_id, 1000, "DEAL_STARTED", {"deal": 1, "price": "100", "qty": "1", "fee": "0.1"}),
            BotEvent(bot_id, 1500, "SAFETY_ORDER_FILLED", {"deal": 1, "index": 1, "price": "90", "qty": "1", "fee": "0.09"}),
            BotEvent(bot_id, 2000, "DEAL_CLOSED", {"deal": 1, "reason": "MANUAL_CLOSE", "price": "100", "qty": "2", "fee": "0.2", "profit": "9.61"}),
        )
        self.seed_runtime(bot_id, state, deals=(deal,), events=events)
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/deals/1")
        self.assertEqual(status, 200)
        data = body["data"]
        self.assertEqual((data["profit"], data["fees"], data["gross_profit"]), ("9.61", "0.39", "10"))

    def test_deal_detail_open_reports_fees_so_far_gross_none(self):
        _, created, _ = self.create()
        bot_id = created["data"]["bot_id"]
        state, config = base_fill()
        state = apply(state, {"type": "MARK", "price": "110"}, config)
        deal = BotDeal(bot_id, 1, 1000, None, 1, None, None, 0, "BTCUSDT")
        events = (
            BotEvent(bot_id, 1000, "DEAL_STARTED", {"deal": 1, "price": "100", "qty": "1", "fee": "0.1"}),
            BotEvent(bot_id, 1500, "SAFETY_ORDER_FILLED", {"deal": 1, "index": 1, "price": "90", "qty": "1", "fee": "0.09"}),
        )
        self.seed_runtime(bot_id, state, deals=(deal,), events=events)
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/deals/1")
        self.assertEqual(status, 200)
        data = body["data"]
        self.assertEqual((data["profit"], data["fees"], data["gross_profit"]), (None, "0.19", None))

    def test_deal_detail_malformed_fee_fails_fees_to_none(self):
        _, created, _ = self.create()
        bot_id = created["data"]["bot_id"]
        state, _ = base_fill()
        deal = BotDeal(bot_id, 1, 1000, 2000, 0, "5", "TAKE_PROFIT", 0, "BTCUSDT")
        events = (
            BotEvent(bot_id, 1000, "DEAL_STARTED", {"deal": 1, "price": "100", "qty": "1", "fee": "0.1"}),
            BotEvent(bot_id, 2000, "DEAL_CLOSED", {"deal": 1, "reason": "TAKE_PROFIT", "price": "105", "qty": "1", "fee": "abc", "profit": "5"}),
        )
        self.seed_runtime(bot_id, state, deals=(deal,), events=events)
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/deals/1")
        self.assertEqual(status, 200)
        data = body["data"]
        self.assertEqual((data["fees"], data["gross_profit"]), (None, None))
        self.assertEqual((data["qty"], data["cost"]), ("1", "100"))

    def test_deal_detail_cancelled_reports_sunk_fees_gross_none(self):
        _, created, _ = self.create()
        bot_id = created["data"]["bot_id"]
        state, _ = base_fill()
        deal = BotDeal(bot_id, 1, 1000, 2000, 0, "0", "CANCELLED", 0, "BTCUSDT")
        events = (
            BotEvent(bot_id, 1000, "DEAL_STARTED", {"deal": 1, "price": "100", "qty": "1", "fee": "0.1"}),
            BotEvent(bot_id, 2000, "DEAL_CLOSED", {"deal": 1, "reason": "CANCELLED", "profit": "0"}),
        )
        self.seed_runtime(bot_id, state, deals=(deal,), events=events)
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/deals/1")
        self.assertEqual(status, 200)
        data = body["data"]
        self.assertEqual((data["profit"], data["fees"], data["gross_profit"]), ("0", "0.1", None))

    def test_deal_detail_missing_close_fee_is_none_unless_cancelled(self):
        _, created, _ = self.create()
        bot_id = created["data"]["bot_id"]
        state, _ = base_fill()
        deal = BotDeal(bot_id, 1, 1000, 2000, 0, "5", "TAKE_PROFIT", 0, "BTCUSDT")
        events = (
            BotEvent(bot_id, 1000, "DEAL_STARTED", {"deal": 1, "price": "100", "qty": "1", "fee": "0.1"}),
            BotEvent(bot_id, 2000, "DEAL_CLOSED", {"deal": 1, "reason": "TAKE_PROFIT", "profit": "5"}),
        )
        self.seed_runtime(bot_id, state, deals=(deal,), events=events)
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/deals/1")
        self.assertEqual(status, 200)
        data = body["data"]
        self.assertEqual((data["fees"], data["gross_profit"]), (None, None))

    def test_deal_detail_unknown(self):
        _, created, _ = self.create()
        bot_id = created["data"]["bot_id"]
        state, _ = base_fill()
        self.seed_runtime(bot_id, state)
        status, _, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/deals/9")
        self.assertEqual(status, 404)
        status, _, _ = call(self.app, "GET", "/api/v2/bots/bot_yok/deals/1")
        self.assertEqual(status, 404)

    def test_close_at_market(self):
        _, created, _ = self.create()
        bot_id = created["data"]["bot_id"]
        revision = created["data"]["revision"]
        state, _ = base_fill()
        self.seed_runtime(bot_id, state, deals=(BotDeal(bot_id, 1, 1000, None, 0, None, None, 0, "BTCUSDT"),))
        self.market.price = Q(110)
        status, body, _ = call(self.app, "POST", f"/api/v2/bots/{bot_id}/deals/1/close", {"revision": revision})
        self.assertEqual(status, 200)
        # 1@110 satis, maliyet 100 -> 10 kazanc, ucret 0.11.
        self.assertEqual(body["data"]["profit"], "9.89")
        self.assertEqual(body["data"]["close_reason"], "MANUAL_CLOSE")
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}")
        self.assertEqual(body["data"]["revision"], revision + 1)
        status, body, _ = call(
            self.app, "POST", f"/api/v2/bots/{bot_id}/deals/1/close", {"revision": revision + 1}
        )
        self.assertEqual(status, 409)

    def test_close_rejects_stale_revision(self):
        _, created, _ = self.create()
        bot_id = created["data"]["bot_id"]
        state, _ = base_fill()
        self.seed_runtime(bot_id, state, deals=(BotDeal(bot_id, 1, 1000, None, 0, None, None, 0, "BTCUSDT"),))
        status, _, _ = call(self.app, "POST", f"/api/v2/bots/{bot_id}/deals/1/close", {"revision": 99})
        self.assertEqual(status, 409)

    def test_cancel_books_zero(self):
        _, created, _ = self.create()
        bot_id = created["data"]["bot_id"]
        revision = created["data"]["revision"]
        state, _ = base_fill()
        self.seed_runtime(bot_id, state, deals=(BotDeal(bot_id, 1, 1000, None, 0, None, None, 0, "BTCUSDT"),))
        status, body, _ = call(self.app, "POST", f"/api/v2/bots/{bot_id}/deals/1/cancel", {"revision": revision})
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["profit"], "0")
        self.assertEqual(body["data"]["close_reason"], "CANCELLED")

    def test_add_funds(self):
        _, created, _ = self.create()
        bot_id = created["data"]["bot_id"]
        revision = created["data"]["revision"]
        state, _ = base_fill()
        self.seed_runtime(bot_id, state, deals=(BotDeal(bot_id, 1, 1000, None, 0, None, None, 0, "BTCUSDT"),))
        self.market.price = Q(110)
        status, body, _ = call(
            self.app, "POST", f"/api/v2/bots/{bot_id}/deals/1/add-funds", {"revision": revision, "amount": "100"}
        )
        self.assertEqual(status, 200)
        # 100/110 asagi yuvarlanir: 0.909 BTC; ucret 0.09999.
        self.assertEqual(body["data"]["qty"], "1.909")
        self.assertIsNone(body["data"]["closed_at_us"])
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/deals")
        self.assertEqual(body["data"][0]["manual_orders_filled"], 1)
        status, body, _ = call(
            self.app, "POST", f"/api/v2/bots/{bot_id}/deals/1/add-funds", {"revision": revision + 1, "amount": "0.001"}
        )
        self.assertEqual(status, 409)

    def test_error_bot_close_allowed_add_blocked(self):
        _, created, _ = self.create()
        bot_id = created["data"]["bot_id"]
        state, _ = base_fill()
        self.seed_runtime(bot_id, state, deals=(BotDeal(bot_id, 1, 1000, None, 0, None, None, 0, "BTCUSDT"),))
        record = self.store.set_runner_status(bot_id, "ERROR", "RUNNER_ERROR: x", now_us=9_000_000)
        self.market.price = Q(110)
        status, _, _ = call(
            self.app, "POST", f"/api/v2/bots/{bot_id}/deals/1/add-funds", {"revision": record.revision, "amount": "100"}
        )
        self.assertEqual(status, 409)
        status, body, _ = call(
            self.app, "POST", f"/api/v2/bots/{bot_id}/deals/1/close", {"revision": record.revision}
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["close_reason"], "MANUAL_CLOSE")

    def test_archived_bot_action_refused(self):
        _, created, _ = self.create()
        bot_id = created["data"]["bot_id"]
        state, _ = base_fill()
        self.seed_runtime(bot_id, state, deals=(BotDeal(bot_id, 1, 1000, None, 0, None, None, 0, "BTCUSDT"),))
        record = self.store.archive(bot_id, expected_revision=created["data"]["revision"], now_us=9_000_000)
        status, _, _ = call(
            self.app, "POST", f"/api/v2/bots/{bot_id}/deals/1/cancel", {"revision": record.revision}
        )
        self.assertEqual(status, 409)


if __name__ == "__main__":
    unittest.main()
