"""B: bot historical run — a fresh STOPPED bot replays closed 1m history.

Same bar rule, config derivation and combo evaluation as the live
runner; runtime, deals and events persist in one guarded write.
"""

import itertools
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from api.test_combo_runner import combo_strategy
from api.test_v2_bots import call, strategy
from api.test_v2_futures_grid_bots import FakeFuturesMarket, fgrid_strategy
from api.test_v2_grid_bots import grid_strategy
from api.test_v2_multi_pair import FakeMultiMarket, MultiVenue, multi_strategy
from dcabot.application.sector_dca import max_deal_quote_cost, parse_sector_dca
from dcabot.data_adapters.binance_futures_public_transport import BinanceFuturesFundingRate
from dcabot.data_adapters.binance_public_transport import BinancePublicKline, BinancePublicTransportError
from dcabot.domain.numbers import Q, exact_text
from dcabot.persistence.bot_store import BotRecord, BotStore
from dcabot.server import api as api_module
from dcabot.server import bot_runner, v2_bots

ROOT = Path(__file__).resolve().parents[2]
MIN = 60_000_000
DAY = 86_400_000_000


def _day_start_us(value: str) -> int:
    parsed = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(parsed.timestamp()) * 1_000_000


START = "2026-09-20"
END = "2026-09-22"
START_US = _day_start_us(START)
END_US = _day_start_us(END)


class ReplayApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BotStore(Path(self.tmp.name) / "bots.sqlite3")
        self.now = END_US + DAY + 3_600_000_000
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
            on_replay=self.runner.run_replay,
            record_event=lambda kind, ref, summary, time_us: self.landmarks.append((kind, ref, summary)),
        )
        self.app = FastAPI()
        self.app.router.route_class = api_module.BoundedAPIRoute
        self.app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_bots.register_routes(self.app, deps)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def _create(self, body, budget="2000", mode="PAPER"):
        status, created, _ = call(
            self.app, "POST", "/api/v2/bots", {"name": "replay", "mode": mode, "budget": budget, "strategy": body}
        )
        self.assertEqual(status, 201, created)
        return created["data"]["bot_id"]

    def _multi_budget(self, body):
        params = parse_sector_dca(body)
        template = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
        cap = max_deal_quote_cost(params, fee_rate=Q(1, 1000), fee_quantum=Q(1, 10**8))
        return exact_text(cap * params.max_active_deals)

    def _replay(self, bot_id, start=START, end=END):
        return call(self.app, "POST", f"/api/v2/bots/{bot_id}/replay", {"start_date": start, "end_date": end})

    def _rows(self, bot_id):
        return [(d.deal_sequence, d.symbol, d.close_reason) for d in self.store.list_deals(bot_id)]

    def test_fresh_single_replay_persists_runtime_deals_and_summary(self):
        bot_id = self._create(strategy(stop_loss=None))
        status, body, _ = self._replay(bot_id)
        self.assertEqual(status, 200, body)
        data = body["data"]
        self.assertEqual(
            (data["bars"], data["first_bar_open_us"], data["last_bar_open_us"], data["symbols"], data["stopped"]),
            (4320, START_US, END_US + DAY - MIN, ["BTCUSDT"], None),
        )
        self.assertGreaterEqual(data["deals_opened"], 1)
        self.assertEqual(len(self.store.list_deals(bot_id)), data["deals_opened"])
        runtime = self.store.get_runtime(bot_id)
        self.assertIsNotNone(runtime)
        assert runtime is not None
        self.assertEqual(runtime.last_bar_open_us, END_US + DAY - MIN)
        self.assertEqual(self.store.get(bot_id).status, "STOPPED")
        self.assertIn("BOT_REPLAYED", [entry[0] for entry in self.landmarks])

    def test_second_replay_is_409_and_store_is_untouched(self):
        bot_id = self._create(strategy(stop_loss=None))
        self.assertEqual(self._replay(bot_id)[0], 200)
        before = [d for d in self.store.list_deals(bot_id)]
        status, body, _ = self._replay(bot_id)
        self.assertEqual((status, body["code"]), (409, "REPLAY_STATE_EXISTS"))
        self.assertEqual([d.deal_sequence for d in self.store.list_deals(bot_id)], [d.deal_sequence for d in before])

    def test_replay_refused_unless_fresh_stopped(self):
        running = self._create(strategy(stop_loss=None))
        record = self.store.get(running)
        status, _, _ = call(self.app, "POST", f"/api/v2/bots/{running}/start", {"revision": record.revision})
        self.assertEqual(status, 200)
        status, body, _ = self._replay(running)
        self.assertEqual((status, body["code"]), (409, "REPLAY_STATUS_INVALID"))
        archived = self._create(strategy(stop_loss=None))
        record = self.store.get(archived)
        status, _, _ = call(self.app, "POST", f"/api/v2/bots/{archived}/archive", {"revision": record.revision})
        self.assertEqual(status, 200)
        status, body, _ = self._replay(archived)
        self.assertEqual((status, body["code"]), (409, "REPLAY_STATUS_INVALID"))

    def test_testnet_mode_replay_is_409(self):
        bot_id = self._create(strategy(stop_loss=None), mode="TESTNET")
        status, body, _ = self._replay(bot_id)
        self.assertEqual((status, body["code"]), (409, "TESTNET_REPLAY_NOT_ENABLED"))
        self.assertIsNone(self.store.get_runtime(bot_id))

    def test_range_errors_are_problem_details(self):
        bot_id = self._create(strategy(stop_loss=None))
        cases = [
            ({"start_date": "2026-09-22", "end_date": "2026-09-20"}, "REPLAY_RANGE_INVALID", "end_date"),
            ({"start_date": "2026-02-30", "end_date": "2026-09-22"}, "REPLAY_DATE_INVALID", "start_date"),
            ({"start_date": "2026-09-01", "end_date": "2026-09-20"}, "REPLAY_RANGE_TOO_LONG", "start_date"),
            ({"start_date": "2026-09-25", "end_date": "2026-09-26"}, "REPLAY_NO_BARS", "start_date"),
        ]
        for overrides, code, field in cases:
            with self.subTest(overrides=overrides):
                status, body, headers = call(
                    self.app, "POST", f"/api/v2/bots/{bot_id}/replay", {"start_date": START, "end_date": END, **overrides}
                )
                self.assertEqual((status, body["code"], body["errors"][0]["field"]), (422, code, field))
                self.assertEqual(headers["content-type"], "application/problem+json")
        self.assertIsNone(self.store.get_runtime(bot_id))
        status, body, _ = call(
            self.app, "POST", f"/api/v2/bots/{bot_id}/replay", {"start_date": "01.01.2026", "end_date": END}
        )
        self.assertEqual((status, body["code"]), (422, "REQUEST_VALIDATION_FAILED"))

    def test_multi_replay_covers_all_symbols_with_shared_sequence(self):
        body = multi_strategy()
        bot_id = self._create(body, budget=self._multi_budget(body))
        status, data, _ = self._replay(bot_id)
        self.assertEqual(status, 200, data)
        rows = self._rows(bot_id)
        self.assertEqual({row[1] for row in rows}, {"BTCUSDT", "ETHUSDT"})
        self.assertEqual([row[0] for row in rows], sorted(row[0] for row in rows))
        self.assertEqual(len({row[0] for row in rows}), len(rows))
        self.assertEqual([r.symbol for r in self.store.get_pair_runtimes(bot_id)], ["BTCUSDT", "ETHUSDT"])

    def test_multi_combo_replay_closes_both_at_combined_target(self):
        body = combo_strategy()
        bot_id = self._create(body, budget=self._multi_budget(body))
        close_at = START_US + 100 * MIN
        self.venue.paths["BTCUSDT"] = {close_at: ("84506.01", "85773.60", "84506.01", "85773.60")}
        self.venue.paths["ETHUSDT"] = {close_at: ("3000", "3045", "3000", "3045")}
        status, data, _ = self._replay(bot_id)
        self.assertEqual(status, 200, data)
        rows = self._rows(bot_id)
        self.assertEqual(rows[:2], [(1, "BTCUSDT", "TAKE_PROFIT"), (2, "ETHUSDT", "TAKE_PROFIT")])
        first_two = self.store.list_deals(bot_id)[:2]
        self.assertTrue(all(d.profit is not None and Q(d.profit) > 0 for d in first_two))
        self.assertTrue(all(d.closed_at_us == close_at + MIN for d in first_two))

    def test_single_combo_replay_closes(self):
        body = strategy(stop_loss=None)
        body["combined_take_profit"] = "1"
        bot_id = self._create(body)
        close_at = START_US + 100 * MIN
        self.venue.paths["BTCUSDT"] = {close_at: ("84506.01", "85773.60", "84506.01", "85773.60")}
        status, data, _ = self._replay(bot_id)
        self.assertEqual(status, 200, data)
        self.assertEqual(self._rows(bot_id)[0], (1, "BTCUSDT", "TAKE_PROFIT"))

    def test_grid_replay_records_fills(self):
        status, created, _ = call(
            self.app, "POST", "/api/v2/grid-bots", {"name": "grid", "mode": "PAPER", "budget": "900", "strategy": grid_strategy()}
        )
        self.assertEqual(status, 201, created)
        bot_id = created["data"]["bot_id"]
        path = {}
        for index in range(1440):
            price = "83500" if (index // 30) % 2 == 0 else "85500"
            path[START_US + index * MIN] = (price, price, price, price)
        self.venue.paths["BTCUSDT"] = path
        status, body, _ = call(
            self.app, "POST", f"/api/v2/bots/{bot_id}/replay", {"start_date": START, "end_date": "2026-09-21"}
        )
        self.assertEqual(status, 200, body)
        data = body["data"]
        self.assertEqual(data["bars"], 2880)
        self.assertGreaterEqual(data["fills"], 4)
        self.assertIsNone(data["stopped"])
        self.assertIsNotNone(self.store.get_grid_runtime(bot_id))
        self.assertEqual(self.store.get(bot_id).status, "STOPPED")

    def test_market_down_is_502_and_persists_nothing(self):
        bot_id = self._create(strategy(stop_loss=None))
        self.venue.down = True
        status, body, _ = self._replay(bot_id)
        self.assertEqual((status, body["code"]), (502, "PUBLIC_UPSTREAM_UNAVAILABLE"))
        self.assertIsNone(self.store.get_runtime(bot_id))
        self.assertEqual(self.store.list_deals(bot_id), ())

    def test_replay_is_deterministic(self):
        first = self._create(strategy(stop_loss=None))
        second = self._create(strategy(stop_loss=None))
        self.assertEqual(self._replay(first)[0], 200)
        self.assertEqual(self._replay(second)[0], 200)

        def shape(bot_id):
            return [
                (d.deal_sequence, d.symbol, d.started_at_us, d.closed_at_us, d.safety_orders_filled, d.profit, d.close_reason)
                for d in self.store.list_deals(bot_id)
            ]

        self.assertEqual(shape(first), shape(second))
        self.assertEqual(self.store.get_runtime(first).state, self.store.get_runtime(second).state)

    def test_replay_then_start_continues_live_without_duplicates(self):
        bot_id = self._create(strategy(stop_loss=None))
        status, body, _ = self._replay(bot_id)
        self.assertEqual(status, 200, body)
        record = self.store.get(bot_id)
        status, _, _ = call(self.app, "POST", f"/api/v2/bots/{bot_id}/start", {"revision": record.revision})
        self.assertEqual(status, 200)
        self.now = END_US + DAY + 12 * MIN + 1
        self.runner.tick()
        runtime = self.store.get_runtime(bot_id)
        assert runtime is not None
        self.assertGreater(runtime.last_bar_open_us, END_US + DAY - MIN)
        seqs = [d.deal_sequence for d in self.store.list_deals(bot_id)]
        self.assertEqual(len(set(seqs)), len(seqs))

    def test_no_runner_is_409(self):
        template = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
        deps = v2_bots.V2BotDeps(
            store=self.store,
            market=FakeMultiMarket(),
            template_loader=lambda: template,
            clock_us=lambda: self.now,
            runner_available=lambda: False,
            problem=api_module._problem,
        )
        app = FastAPI()
        app.router.route_class = api_module.BoundedAPIRoute
        app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_bots.register_routes(app, deps)
        bot_id = self._create(strategy(stop_loss=None))
        status, body, _ = call(app, "POST", f"/api/v2/bots/{bot_id}/replay", {"start_date": START, "end_date": END})
        self.assertEqual((status, body["code"]), (409, "BOT_RUNNER_UNAVAILABLE"))


class FuturesVenue:
    def __init__(self):
        self.path: dict[int, tuple[str, str, str, str]] = {}
        self.funding: dict[int, str] = {}

    def fetch_range(self, symbol, *, interval, start_us, end_us, max_bars, now_us, allowed_symbols):
        bars = []
        t = start_us
        while t < end_us and t + MIN - 1 < now_us:
            o, h, low, c = self.path.get(t, ("84506.01", "84506.01", "84506.01", "84506.01"))
            bars.append(BinancePublicKline(t, t + MIN - 1, o, h, low, c, "1"))
            t += MIN
        return tuple(bars)

    def fetch_funding(self, symbol, *, start_us, end_us, allowed_symbols):
        return tuple(
            BinanceFuturesFundingRate(funding_time_us=t, rate=rate)
            for t, rate in sorted(self.funding.items())
            if start_us <= t < end_us
        )


class FuturesReplayApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BotStore(Path(self.tmp.name) / "bots.sqlite3")
        self.now = END_US + DAY + 3_600_000_000
        self.venue = FuturesVenue()
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
                futures_market=FakeFuturesMarket(),
                fetch_futures_range=self.venue.fetch_range,
                fetch_funding=self.venue.fetch_funding,
            )
        )
        deps = v2_bots.V2BotDeps(
            store=self.store,
            market=FakeMultiMarket(),
            template_loader=lambda: template,
            clock_us=lambda: self.now,
            runner_available=lambda: True,
            problem=api_module._problem,
            on_start=self.runner.prepare_start,
            on_replay=self.runner.run_replay,
            futures_market=FakeFuturesMarket(),
        )
        self.app = FastAPI()
        self.app.router.route_class = api_module.BoundedAPIRoute
        self.app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_bots.register_routes(self.app, deps)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_futures_grid_replay_records_fills(self):
        status, created, _ = call(
            self.app,
            "POST",
            "/api/v2/futures-grid-bots",
            {"name": "fgrid", "mode": "PAPER", "budget": "900", "strategy": fgrid_strategy()},
        )
        self.assertEqual(status, 201, created)
        bot_id = created["data"]["bot_id"]
        for index in range(2880):
            price = "83500" if (index // 30) % 2 == 0 else "85500"
            self.venue.path[START_US + index * MIN] = (price, price, price, price)
        self.venue.funding[START_US + 8 * 3_600_000_000] = "0.0001"
        status, body, _ = call(
            self.app, "POST", f"/api/v2/bots/{bot_id}/replay", {"start_date": START, "end_date": "2026-09-21"}
        )
        self.assertEqual(status, 200, body)
        self.assertEqual(body["data"]["bars"], 2880)
        self.assertGreaterEqual(body["data"]["fills"], 4)
        self.assertIsNotNone(self.store.get_grid_runtime(bot_id))
        self.assertEqual(self.store.get(bot_id).status, "STOPPED")

    def test_futures_replay_without_futures_data_is_409(self):
        record = BotRecord(
            bot_id="bot_futures_no_data",
            name="fgrid",
            strategy_type="FUTURES_GRID",
            mode="PAPER",
            symbol="BTCUSDT",
            strategy=fgrid_strategy(),
            budget="900",
            status="STOPPED",
            status_reason=None,
            revision=1,
            created_at_us=self.now,
            updated_at_us=self.now,
            archived_at_us=None,
        )
        self.store.create(record)
        runner = bot_runner.PaperBotRunner(
            bot_runner.RunnerDeps(
                store=self.store,
                market=FakeMultiMarket(),
                fetch_range=self.venue.fetch_range,
                transport_error=BinancePublicTransportError,
                template_loader=lambda: {},
                clock_us=lambda: self.now,
                kill_switch_engaged=lambda: False,
            )
        )
        with self.assertRaises(bot_runner.ReplayError) as ctx:
            runner.run_replay(record.bot_id, START_US, START_US + DAY)
        self.assertEqual((ctx.exception.code, ctx.exception.status), ("FUTURES_REPLAY_UNAVAILABLE", 409))
        self.assertIsNone(self.store.get_grid_runtime(record.bot_id))


class RealAppReplayContractTests(unittest.TestCase):
    def test_route_is_typed_and_bounded(self):
        import json

        schema = api_module.app.openapi()
        operation = schema["paths"]["/api/v2/bots/{bot_id}/replay"]["post"]
        self.assertIn("$ref", json.dumps(operation["responses"]["200"]))
        self.assertIn("/api/v2/bots/{bot_id}/replay", api_module.ROUTE_BODY_LIMITS)


if __name__ == "__main__":
    unittest.main()
