"""Faz W-B2 runner service + API: start prepares a runtime, ticks trade on
closed 1m bars, kill switch and market outages are honest, stats are exact."""
import itertools
import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from api.test_v2_bots import FakeMarket, call, strategy
from dcabot.data_adapters.binance_public_transport import BinancePublicKline, BinancePublicTransportError
from dcabot.persistence.bot_store import BotStore
from dcabot.server import api as api_module
from dcabot.server import bot_runner, v2_bots

ROOT = Path(__file__).resolve().parents[2]
MIN = 60_000_000
T0 = 1_790_000_000 * 1_000_000 // MIN * MIN


class _Clock:
    def __init__(self):
        self.now = T0 + 5_000_000

    def __call__(self):
        return self.now


class _Venue:
    """1m klines: flat at the reference price, then a scripted path."""

    def __init__(self):
        self.path: dict[int, tuple[str, str, str, str]] = {}
        self.down = False
        self.calls = 0

    def fetch_range(self, symbol, *, interval, start_us, end_us, max_bars, now_us, allowed_symbols):
        self.calls += 1
        if self.down:
            raise BinancePublicTransportError("PUBLIC_UPSTREAM_UNAVAILABLE", "down")
        bars = []
        t = start_us
        while t < end_us and t + MIN - 1 < now_us:
            o, h, low, c = self.path.get(t, ("84506.01", "84506.01", "84506.01", "84506.01"))
            bars.append(BinancePublicKline(t, t + MIN - 1, o, h, low, c, "1"))
            t += MIN
        return tuple(bars)


class RunnerServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BotStore(Path(self.tmp.name) / "bots.sqlite3")
        self.clock = _Clock()
        self.venue = _Venue()
        self.kill = False
        self.landmarks = []
        template = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
        self.runner = bot_runner.PaperBotRunner(
            bot_runner.RunnerDeps(
                store=self.store,
                market=FakeMarket(),
                fetch_range=self.venue.fetch_range,
                transport_error=BinancePublicTransportError,
                template_loader=lambda: template,
                clock_us=self.clock,
                kill_switch_engaged=lambda: self.kill,
                record_event=lambda kind, ref, summary, time_us: self.landmarks.append(
                    (kind, ref, summary, time_us)
                ),
            )
        )
        ids = itertools.count(1)
        deps = v2_bots.V2BotDeps(
            store=self.store,
            market=FakeMarket(),
            template_loader=lambda: template,
            clock_us=lambda: self.clock.now + next(ids),
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

    def _create_and_start(self, mode="PAPER"):
        bot = call(self.app, "POST", "/api/v2/bots", {"name": "b", "mode": mode, "budget": "2000", "strategy": strategy(stop_loss=None)})[1]["data"]
        status, body, _ = call(self.app, "POST", f"/api/v2/bots/{bot['bot_id']}/start", {"revision": 1})
        return bot["bot_id"], status, body

    def test_start_prepares_runtime_and_ticks_open_then_close_a_deal(self):
        bot_id, status, body = self._create_and_start()
        self.assertEqual((status, body["data"]["status"]), (200, "RUNNING"))
        runtime = self.store.get_runtime(bot_id)
        self.assertEqual(runtime.last_bar_open_us, T0)
        self.assertEqual(runtime.config["base_sizing"], "QUOTE")
        self.venue.path[T0 + 2 * MIN] = ("84506.01", "86300", "84506.01", "86200")
        self.clock.now = T0 + 4 * MIN + 1
        self.runner.tick()
        deals = call(self.app, "GET", f"/api/v2/bots/{bot_id}/deals")[1]["data"]
        self.assertEqual([(d["deal"], d["close_reason"]) for d in deals], [(1, "TAKE_PROFIT"), (2, None)])
        self.assertEqual([d["cumulative_profit"] for d in deals], [deals[0]["profit"], None])
        stats = call(self.app, "GET", f"/api/v2/bots/{bot_id}/stats")[1]["data"]
        self.assertEqual(stats["deals_completed"], 1)
        self.assertEqual(Fraction(stats["total_profit"]), Fraction(deals[0]["profit"]))
        self.assertGreater(Fraction(stats["total_profit"]), 0)
        self.assertEqual(stats["active_deal"]["deal"], 2)
        kinds = [e["kind"] for e in call(self.app, "GET", f"/api/v2/bots/{bot_id}/events?limit=10")[1]["data"]]
        self.assertEqual(kinds, ["DEAL_STARTED", "DEAL_CLOSED", "DEAL_STARTED"])

    def test_paused_bot_does_not_open_a_new_deal(self):
        bot_id, _, _ = self._create_and_start()
        call(self.app, "POST", f"/api/v2/bots/{bot_id}/pause", {"revision": 2})
        self.clock.now = T0 + 5 * MIN + 1
        self.runner.tick()
        self.assertEqual(self.store.list_deals(bot_id), ())

    def test_cooldown_seeded_from_last_close_delays_reopen(self):
        bot = call(
            self.app, "POST", "/api/v2/bots",
            {"name": "b", "mode": "PAPER", "budget": "2000", "strategy": strategy(stop_loss=None, cooldown_seconds=120)},
        )[1]["data"]
        call(self.app, "POST", f"/api/v2/bots/{bot['bot_id']}/start", {"revision": 1})
        self.venue.path[T0 + 2 * MIN] = ("84506.01", "86300", "84506.01", "86200")
        self.clock.now = T0 + 4 * MIN + 1
        self.runner.tick()
        deals = call(self.app, "GET", f"/api/v2/bots/{bot['bot_id']}/deals")[1]["data"]
        self.assertEqual([(d["deal"], d["close_reason"]) for d in deals], [(1, "TAKE_PROFIT")])
        self.clock.now = T0 + 6 * MIN + 1
        self.runner.tick()
        deals = call(self.app, "GET", f"/api/v2/bots/{bot['bot_id']}/deals")[1]["data"]
        self.assertEqual([(d["deal"], d["close_reason"]) for d in deals], [(1, "TAKE_PROFIT"), (2, None)])

    def test_price_band_blocks_entries_outside(self):
        bot = call(
            self.app, "POST", "/api/v2/bots",
            {"name": "b", "mode": "PAPER", "budget": "2000", "strategy": strategy(stop_loss=None, min_price="90000")},
        )[1]["data"]
        call(self.app, "POST", f"/api/v2/bots/{bot['bot_id']}/start", {"revision": 1})
        self.clock.now = T0 + 4 * MIN + 1
        self.runner.tick()
        deals = call(self.app, "GET", f"/api/v2/bots/{bot['bot_id']}/deals")[1]["data"]
        self.assertEqual(deals, [])

    def test_futures_bot_starts_and_ticks_with_leverage(self):
        bot = call(
            self.app, "POST", "/api/v2/bots",
            {"name": "b", "mode": "PAPER", "budget": "2000",
             "strategy": strategy(stop_loss=None, market_type="FUTURES", leverage=3)},
        )[1]["data"]
        call(self.app, "POST", f"/api/v2/bots/{bot['bot_id']}/start", {"revision": 1})
        self.assertEqual(self.store.get_runtime(bot["bot_id"]).config["leverage"], "3")
        self.clock.now = T0 + 3 * MIN + 1
        self.runner.tick()
        deals = call(self.app, "GET", f"/api/v2/bots/{bot['bot_id']}/deals")[1]["data"]
        self.assertEqual([(d["deal"], d["close_reason"]) for d in deals], [(1, None)])

    def test_tick_writes_an_hourly_portfolio_snapshot(self):
        from dcabot.application.portfolio_stats import SNAPSHOT_INTERVAL_US, SNAPSHOT_RETENTION_US, portfolio_equity

        bot_id, _, _ = self._create_and_start()
        self.clock.now = T0 + 3 * MIN + 1
        self.runner.tick()
        rows = self.store.list_portfolio_snapshots()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["time_us"], T0 + 3 * MIN + 1)
        records = self.store.list()
        expected = portfolio_equity(
            records,
            {record.bot_id: self.store.list_deals(record.bot_id) for record in records},
            {bot_id: self.store.get_runtime(bot_id)},
        )
        self.assertEqual({k: rows[0][k] for k in ("equity", "realized", "unrealized")}, expected)
        self.runner.tick()
        self.assertEqual(len(self.store.list_portfolio_snapshots()), 1)
        self.clock.now += SNAPSHOT_INTERVAL_US
        self.runner.tick()
        self.assertEqual(len(self.store.list_portfolio_snapshots()), 2)
        self.store.save_portfolio_snapshot(T0 - SNAPSHOT_RETENTION_US - 1, "0", "0", "0")
        self.clock.now += SNAPSHOT_INTERVAL_US
        self.runner.tick()
        times = [row["time_us"] for row in self.store.list_portfolio_snapshots()]
        self.assertNotIn(T0 - SNAPSHOT_RETENTION_US - 1, times)

    def test_kill_switch_freezes_every_bot_and_says_why(self):
        bot_id, _, _ = self._create_and_start()
        self.kill = True
        self.clock.now = T0 + 5 * MIN + 1
        self.runner.tick()
        self.assertEqual(self.venue.calls, 0)
        bot = self.store.get(bot_id)
        self.assertEqual((bot.status, bot.status_reason), ("RUNNING", "KILL_SWITCH_ACTIVE"))
        self.kill = False
        self.runner.tick()
        self.assertEqual(self.store.get(bot_id).status_reason, None)
        self.assertEqual(len(self.store.list_deals(bot_id)), 1)

    def test_market_outage_is_retried_not_an_error(self):
        bot_id, _, _ = self._create_and_start()
        self.venue.down = True
        self.clock.now = T0 + 3 * MIN + 1
        self.runner.tick()
        bot = self.store.get(bot_id)
        self.assertEqual((bot.status, bot.status_reason), ("RUNNING", "MARKET_DATA_UNAVAILABLE"))
        self.venue.down = False
        self.runner.tick()
        self.assertEqual(len(self.store.list_deals(bot_id)), 1)

    def test_testnet_bot_cannot_be_started(self):
        _, status, body = self._create_and_start(mode="TESTNET")
        self.assertEqual((status, body["code"]), (409, "TESTNET_RUNNER_NOT_ENABLED"))

    def test_restart_keeps_the_open_deal(self):
        bot_id, _, _ = self._create_and_start()
        self.clock.now = T0 + 3 * MIN + 1
        self.runner.tick()
        call(self.app, "POST", f"/api/v2/bots/{bot_id}/stop", {"revision": 2})
        before = self.store.get_runtime(bot_id)
        call(self.app, "POST", f"/api/v2/bots/{bot_id}/start", {"revision": 3})
        self.assertEqual(self.store.get_runtime(bot_id).state, before.state)
        self.assertEqual(len(self.store.list_deals(bot_id)), 1)


    def test_tick_emits_deal_opened_and_closed_landmarks(self):
        bot_id, _, _ = self._create_and_start()
        self.venue.path[T0 + 2 * MIN] = ("84506.01", "86300", "84506.01", "86200")
        self.clock.now = T0 + 4 * MIN + 1
        self.runner.tick()
        self.assertEqual(
            [(kind, ref) for kind, ref, _, _ in self.landmarks],
            [("DEAL_OPENED", f"{bot_id}:1"), ("DEAL_CLOSED", f"{bot_id}:1"), ("DEAL_OPENED", f"{bot_id}:2")],
        )
        self.assertEqual(self.landmarks[1][2], "Deal 1 kapandı (TAKE_PROFIT).")

    def test_market_outage_emits_status_once_then_recovery(self):
        bot_id, _, _ = self._create_and_start()
        self.venue.down = True
        self.clock.now = T0 + 3 * MIN + 1
        self.runner.tick()
        self.runner.tick()
        self.assertEqual(
            [(kind, ref) for kind, ref, _, _ in self.landmarks],
            [("BOT_STATUS", bot_id)],
        )
        self.assertIn("MARKET_DATA_UNAVAILABLE", self.landmarks[0][2])
        self.venue.down = False
        self.runner.tick()
        self.assertEqual(
            [kind for kind, _, _, _ in self.landmarks],
            ["BOT_STATUS", "DEAL_OPENED", "BOT_STATUS"],
        )

    def test_kill_switch_emits_status_on_engage_only(self):
        bot_id, _, _ = self._create_and_start()
        self.kill = True
        self.clock.now = T0 + 5 * MIN + 1
        self.runner.tick()
        self.runner.tick()
        self.assertEqual([kind for kind, _, _, _ in self.landmarks], ["BOT_STATUS"])
        self.kill = False
        self.runner.tick()
        self.assertEqual(
            [kind for kind, _, _, _ in self.landmarks],
            ["BOT_STATUS", "DEAL_OPENED", "BOT_STATUS"],
        )

    def test_safety_fill_emits_landmark(self):
        bot_id, _, _ = self._create_and_start()
        self.venue.path[T0 + 2 * MIN] = ("84506.01", "84506.01", "82000", "83000")
        self.clock.now = T0 + 4 * MIN + 1
        self.runner.tick()
        kinds = [(kind, ref) for kind, ref, _, _ in self.landmarks]
        self.assertIn(("SAFETY_ORDER_FILLED", f"{bot_id}:1"), kinds)
        self.assertIsNone(self.store.list_deals(bot_id)[0].closed_at_us)


if __name__ == "__main__":
    unittest.main()
