"""G2-c: grid bot endpoints — create, preview, live grid state."""

import itertools
import json
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from dcabot.application.grid_runner import prepare_grid_runtime
from dcabot.persistence.bot_store import BotStore
from dcabot.server import api as api_module
from dcabot.server import v2_bots
from api.test_v2_bots import FakeMarket, call, strategy

ROOT = Path(__file__).resolve().parents[2]


def grid_strategy(**overrides):
    body = {
        "symbol": "BTCUSDT",
        "mode": "ARITHMETIC",
        "lower_price": "80000",
        "upper_price": "89000",
        "interval_count": 9,
        "fee_rate": "0.001",
        "stop_loss_price": None,
        "take_profit_pct": None,
        "trailing_up_pct": None,
        "trailing_down_pct": None,
    }
    body.update(overrides)
    return body


class V2GridBotApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BotStore(Path(self.tmp.name) / "bots.sqlite3")
        self.market = FakeMarket()
        self.clock = itertools.count(10_000_000, 1_000)
        template = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))

        def on_start(record):
            runtime = prepare_grid_runtime(
                record.bot_id, record.strategy, self.market.symbol_rules(record.symbol),
                investment=record.budget, now_us=next(self.clock),
            )
            self.store.save_grid_runtime(runtime)

        deps = v2_bots.V2BotDeps(
            store=self.store,
            market=self.market,
            template_loader=lambda: template,
            clock_us=lambda: next(self.clock),
            runner_available=lambda: True,
            problem=api_module._problem,
            on_start=on_start,
        )
        self.app = FastAPI()
        self.app.router.route_class = api_module.BoundedAPIRoute
        self.app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_bots.register_routes(self.app, deps)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def create_grid(self, **overrides):
        body = {"name": "Grid test", "mode": "PAPER", "budget": "900", "strategy": grid_strategy()}
        body.update(overrides)
        return call(self.app, "POST", "/api/v2/grid-bots", body)

    def test_preview_reports_levels_and_entry_position(self):
        status, body, _ = call(
            self.app, "POST", "/api/v2/grid-bots/preview",
            {"budget": "900", "strategy": grid_strategy()},
        )
        self.assertEqual(status, 200)
        preview = body["data"]
        self.assertEqual(preview["reference_price"], "84506.01")
        self.assertEqual(preview["entry_position"], "WITHIN")
        self.assertEqual(len(preview["levels"]), 10)
        self.assertEqual(preview["levels"][0], "80000")
        self.assertEqual(preview["quote_per_grid"], "100")
        self.assertIs(preview["within_min_notional"], True)
        status, body, _ = call(
            self.app, "POST", "/api/v2/grid-bots/preview",
            {"budget": "900", "strategy": grid_strategy(lower_price="90000", upper_price="99000")},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["entry_position"], "BELOW")

    def test_preview_flags_min_notional_without_failing(self):
        status, body, _ = call(
            self.app, "POST", "/api/v2/grid-bots/preview",
            {"budget": "40", "strategy": grid_strategy(lower_price="80000", upper_price="81000", interval_count=10)},
        )
        self.assertEqual(status, 200, body)
        self.assertEqual(body["data"]["quote_per_grid"], "4")
        self.assertIs(body["data"]["within_min_notional"], False)

    def test_create_start_and_grid_state(self):
        status, body, _ = self.create_grid()
        self.assertEqual(status, 201, body)
        bot = body["data"]
        self.assertEqual(bot["type"], "GRID")
        self.assertEqual(bot["status"], "STOPPED")
        bot_id = bot["bot_id"]
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/grid")
        self.assertEqual(status, 200, body)
        self.assertEqual(body["data"]["grid_status"], "WAIT")
        self.assertEqual(len(body["data"]["levels"]), 10)
        status, body, _ = call(self.app, "POST", f"/api/v2/bots/{bot_id}/start", {"revision": 1})
        self.assertEqual(status, 200, body)
        self.assertEqual(body["data"]["status"], "RUNNING")
        self.assertIsNotNone(self.store.get_grid_runtime(bot_id))
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/grid")
        self.assertEqual(status, 200, body)
        self.assertEqual(body["data"]["grid_status"], "WAIT")
        self.assertEqual(body["data"]["last_price"], "84506.01")
        # DCA-only surfaces stay safe: no deals, zero stats.
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/deals")
        self.assertEqual((status, body["data"]), (200, []))
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{bot_id}/stats")
        self.assertEqual(status, 200)

    def test_copy_grid_bot_keeps_grid_setup_fresh(self):
        status, body, _ = self.create_grid()
        self.assertEqual(status, 201, body)
        source = body["data"]
        status, body, _ = call(self.app, "POST", f"/api/v2/bots/{source['bot_id']}/copy", {})
        self.assertEqual(status, 201, body)
        data = body["data"]
        self.assertEqual(
            (data["type"], data["strategy"], data["budget"], data["status"]),
            ("GRID", source["strategy"], source["budget"], "STOPPED"),
        )
        self.assertIsNone(self.store.get_grid_runtime(data["bot_id"]))

    def test_grid_state_on_dca_bot_is_404(self):
        dca = {"name": "DCA", "mode": "PAPER", "budget": "2000", "strategy": strategy()}
        status, body, _ = call(self.app, "POST", "/api/v2/bots", dca)
        self.assertEqual(status, 201, body)
        status, body, _ = call(self.app, "GET", f"/api/v2/bots/{body['data']['bot_id']}/grid")
        self.assertEqual((status, body["code"]), (404, "GRID_STATE_UNAVAILABLE"))

    def test_create_errors_are_problem_details(self):
        cases = [
            ({"strategy": grid_strategy(upper_price="70000")}, "GRID_BOUNDS_INVALID"),
            ({"strategy": grid_strategy(lower_price="80000", upper_price="81000", interval_count=10), "budget": "40"},
             "GRID_MIN_NOTIONAL_TOO_SMALL"),
        ]
        for overrides, code in cases:
            with self.subTest(code=code):
                status, body, _ = self.create_grid(**overrides)
                self.assertEqual((status, body["code"]), (422, code))

    def test_market_outage_is_a_bounded_502(self):
        self.market.down = True
        status, body, _ = self.create_grid()
        self.assertEqual((status, body["code"]), (502, "PUBLIC_UPSTREAM_UNAVAILABLE"))


if __name__ == "__main__":
    unittest.main()
