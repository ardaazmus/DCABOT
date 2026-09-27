"""Faz W-B5: portfolio stats API -- summary/equity/daily/by-bot/by-pair."""
import tempfile
import unittest
from fractions import Fraction as Q
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from api.test_v2_bots import call
from dcabot.domain.engine import State
from dcabot.persistence.bot_store import BotDeal, BotRecord, BotRuntime, BotStore
from dcabot.server import api as api_module
from dcabot.server import v2_stats

DAY = 86_400_000_000
NOW = 10 * DAY + 3_600_000_000


def _record(bot_id, name, symbol, budget, status="STOPPED"):
    return BotRecord(bot_id, name, "DCA", "PAPER", symbol, {}, budget, status, None, 1, 0, 0, None)


class PortfolioStatsApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BotStore(Path(self.tmp.name) / "bots.sqlite3")
        self.app = FastAPI()
        self.app.router.route_class = api_module.BoundedAPIRoute
        self.app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_stats.register_routes(
            self.app,
            v2_stats.V2StatsDeps(store=self.store, clock_us=lambda: NOW, problem=api_module._problem),
        )
        self.store.create(_record("a", "A", "BTCUSDT", "1000"))
        self.store.create(_record("b", "B", "ETHUSDT", "500"))
        self.store.apply_action("a", "start", expected_revision=1, now_us=NOW)
        runtime = BotRuntime("a", {}, State(), 0, Q(0), 0, NOW)
        self.store.save_runtime(
            runtime,
            deals=(
                BotDeal("a", 1, 8 * DAY, 8 * DAY + 1, 0, "10.5", "TAKE_PROFIT", 0, "BTCUSDT"),
                BotDeal("a", 2, 10 * DAY, 10 * DAY + 1, 0, "-2.25", "STOP_LOSS", 0, "BTCUSDT"),
            ),
        )
        self.store.save_portfolio_snapshot(9 * DAY, "1500", "10.5", "0")
        self.store.save_portfolio_snapshot(10 * DAY, "1508.25", "8.25", "0")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_summary(self):
        status, body, _ = call(self.app, "GET", "/api/v2/stats/portfolio/summary")
        self.assertEqual(status, 200)
        self.assertEqual(
            body["data"],
            {"total_value": "1508.25", "today_profit": "-2.25", "active_bots": 1, "deployed_capital": "1000"},
        )

    def test_equity_range_filters(self):
        status, body, _ = call(self.app, "GET", "/api/v2/stats/portfolio/equity?range=all")
        self.assertEqual(status, 200)
        self.assertEqual([row["time_us"] for row in body["data"]], [9 * DAY, 10 * DAY])
        status, body, _ = call(self.app, "GET", "/api/v2/stats/portfolio/equity?range=7d")
        self.assertEqual([row["time_us"] for row in body["data"]], [9 * DAY, 10 * DAY])
        status, body, _ = call(self.app, "GET", "/api/v2/stats/portfolio/equity?range=bogus")
        self.assertEqual(status, 422)

    def test_daily_profit(self):
        status, body, _ = call(self.app, "GET", "/api/v2/stats/portfolio/daily-profit?days=3")
        self.assertEqual(status, 200)
        self.assertEqual(
            body["data"],
            [
                {"day_start_us": 8 * DAY, "profit": "10.5"},
                {"day_start_us": 9 * DAY, "profit": "0"},
                {"day_start_us": 10 * DAY, "profit": "-2.25"},
            ],
        )
        status, _, _ = call(self.app, "GET", "/api/v2/stats/portfolio/daily-profit?days=91")
        self.assertEqual(status, 422)

    def test_by_bot_and_by_pair(self):
        status, body, _ = call(self.app, "GET", "/api/v2/stats/portfolio/by-bot")
        self.assertEqual(status, 200)
        self.assertEqual(
            body["data"],
            [
                {"bot_id": "a", "bot_name": "A", "profit": "8.25", "deals_completed": 2},
                {"bot_id": "b", "bot_name": "B", "profit": "0", "deals_completed": 0},
            ],
        )
        status, body, _ = call(self.app, "GET", "/api/v2/stats/portfolio/by-pair")
        self.assertEqual(status, 200)
        self.assertEqual(
            body["data"],
            [
                {"symbol": "BTCUSDT", "profit": "8.25", "deals_completed": 2, "bots": 1},
                {"symbol": "ETHUSDT", "profit": "0", "deals_completed": 0, "bots": 1},
            ],
        )


if __name__ == "__main__":
    unittest.main()
