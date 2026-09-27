"""G4-a COMBO-lite: combined take-profit closes every open deal together.

Elde hesap (cift, hedef %1, deal-TP %2, taban 100+100):
BTC +1.5% ve ETH +1.5% -> birlesik ~%1.5 >= 1 kapanir; ikisi de
tek-basina %2'yi gormez (combo kant). BTC +2.5% / ETH -%1 ->
birlesik ~%0.75 < 1 acik kalir; BTC tek-basina %2'yi astigi halde
kapanmaz (deal-TP baskisi kant).
"""

import itertools
import json
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from api.test_v2_bots import call, strategy
from api.test_v2_multi_pair import FakeMultiMarket, MultiVenue
from dcabot.application.sector_dca import max_deal_quote_cost, parse_sector_dca
from dcabot.data_adapters.binance_public_transport import BinancePublicTransportError
from dcabot.domain.numbers import Q, exact_text
from dcabot.persistence.bot_store import BotStore
from dcabot.server import api as api_module
from dcabot.server import bot_runner, v2_bots

ROOT = Path(__file__).resolve().parents[2]
MIN = 60_000_000
T0 = 1_790_000_000 * 1_000_000 // MIN * MIN


def combo_strategy(**overrides):
    body = strategy(stop_loss=None)
    body["symbols"] = ["BTCUSDT", "ETHUSDT"]
    body["max_active_deals"] = 2
    body["combined_take_profit"] = "1"
    body.update(overrides)
    return body


class ComboRunnerTests(unittest.TestCase):
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

    def _budget_for(self, body):
        params = parse_sector_dca(body)
        template = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
        cap = max_deal_quote_cost(params, fee_rate=Q(1, 1000), fee_quantum=Q(1, 10**8))
        return exact_text(cap * params.max_active_deals)

    def _create_and_start(self, body):
        budget = self._budget_for(body)
        status, created, _ = call(
            self.app, "POST", "/api/v2/bots", {"name": "combo", "mode": "PAPER", "budget": budget, "strategy": body}
        )
        self.assertEqual(status, 201, created)
        bot_id = created["data"]["bot_id"]
        status, started, _ = call(self.app, "POST", f"/api/v2/bots/{bot_id}/start", {"revision": 1})
        self.assertEqual(status, 200, started)
        return bot_id

    def _rows(self, bot_id):
        return [(d.deal_sequence, d.symbol, d.close_reason) for d in self.store.list_deals(bot_id)]

    def test_create_stores_combo_and_suppresses_engine_tp(self):
        bot_id = self._create_and_start(combo_strategy())
        record = self.store.get(bot_id)
        self.assertEqual(record.strategy["combined_take_profit"], "1")
        for runtime in self.store.get_pair_runtimes(bot_id):
            self.assertIsNone(runtime.config["take_profit"])

    def test_preview_with_combo_returns_null_take_profit_price(self):
        body = combo_strategy()
        budget = self._budget_for(body)
        status, preview, _ = call(
            self.app, "POST", "/api/v2/bots/preview", {"budget": budget, "strategy": body}
        )
        self.assertEqual(status, 200, preview)
        self.assertIsNone(preview["data"]["take_profit_price"])
        self.assertEqual(preview["data"]["symbols"], ["BTCUSDT", "ETHUSDT"])

    def test_tick_closes_all_deals_at_combined_target(self):
        bot_id = self._create_and_start(combo_strategy())
        self.now = T0 + 4 * MIN + 1
        self.runner.tick()
        self.assertEqual(
            self._rows(bot_id),
            [(1, "BTCUSDT", None), (2, "ETHUSDT", None)],
        )
        self.venue.paths["BTCUSDT"] = {T0 + 5 * MIN: ("84506.01", "85773.60", "84506.01", "85773.60")}
        self.venue.paths["ETHUSDT"] = {T0 + 5 * MIN: ("3000", "3045", "3000", "3045")}
        self.now = T0 + 6 * MIN + 1
        self.runner.tick()
        self.assertEqual(
            self._rows(bot_id),
            [(1, "BTCUSDT", "TAKE_PROFIT"), (2, "ETHUSDT", "TAKE_PROFIT")],
        )
        closed = [entry for entry in self.landmarks if entry[0] == "DEAL_CLOSED"]
        self.assertEqual(len(closed), 2)
        profits = [d.profit for d in self.store.list_deals(bot_id)]
        self.assertTrue(all(p is not None and Q(p) > 0 for p in profits))

    def test_per_deal_tp_suppressed_below_combined_target(self):
        bot_id = self._create_and_start(combo_strategy())
        self.now = T0 + 4 * MIN + 1
        self.runner.tick()
        self.venue.paths["BTCUSDT"] = {T0 + 5 * MIN: ("84506.01", "86618.66", "84506.01", "86618.66")}
        self.venue.paths["ETHUSDT"] = {T0 + 5 * MIN: ("3000", "3000", "2970", "2970")}
        self.now = T0 + 6 * MIN + 1
        self.runner.tick()
        self.assertEqual(
            self._rows(bot_id),
            [(1, "BTCUSDT", None), (2, "ETHUSDT", None)],
        )

    def test_paused_bot_still_combo_closes_but_opens_nothing(self):
        bot_id = self._create_and_start(combo_strategy())
        self.now = T0 + 4 * MIN + 1
        self.runner.tick()
        record = self.store.get(bot_id)
        status, _, _ = call(self.app, "POST", f"/api/v2/bots/{bot_id}/pause", {"revision": record.revision})
        self.assertEqual(status, 200)
        self.venue.paths["BTCUSDT"] = {T0 + 5 * MIN: ("84506.01", "85773.60", "84506.01", "85773.60")}
        self.venue.paths["ETHUSDT"] = {T0 + 5 * MIN: ("3000", "3045", "3000", "3045")}
        self.now = T0 + 6 * MIN + 1
        self.runner.tick()
        self.assertEqual(
            self._rows(bot_id),
            [(1, "BTCUSDT", "TAKE_PROFIT"), (2, "ETHUSDT", "TAKE_PROFIT")],
        )
        self.now = T0 + 8 * MIN + 1
        self.runner.tick()
        self.assertEqual(len(self.store.list_deals(bot_id)), 2)

    def test_single_pair_combo_closes(self):
        body = strategy(stop_loss=None)
        body["combined_take_profit"] = "1"
        bot_id = self._create_and_start(body)
        self.assertIsNotNone(self.store.get_runtime(bot_id))
        self.now = T0 + 4 * MIN + 1
        self.runner.tick()
        self.assertEqual(self._rows(bot_id), [(1, "BTCUSDT", None)])
        self.venue.paths["BTCUSDT"] = {T0 + 5 * MIN: ("84506.01", "85773.60", "84506.01", "85773.60")}
        self.now = T0 + 6 * MIN + 1
        self.runner.tick()
        self.assertEqual(self._rows(bot_id), [(1, "BTCUSDT", "TAKE_PROFIT")])

    def test_new_deals_open_after_combo_close(self):
        bot_id = self._create_and_start(combo_strategy())
        self.now = T0 + 4 * MIN + 1
        self.runner.tick()
        self.venue.paths["BTCUSDT"] = {T0 + 5 * MIN: ("84506.01", "85773.60", "84506.01", "85773.60")}
        self.venue.paths["ETHUSDT"] = {T0 + 5 * MIN: ("3000", "3045", "3000", "3045")}
        self.now = T0 + 6 * MIN + 1
        self.runner.tick()
        self.assertEqual(
            [(d.deal_sequence, d.close_reason) for d in self.store.list_deals(bot_id)],
            [(1, "TAKE_PROFIT"), (2, "TAKE_PROFIT")],
        )
        self.now = T0 + 8 * MIN + 1
        self.runner.tick()
        self.assertEqual(
            [(d.deal_sequence, d.close_reason) for d in self.store.list_deals(bot_id)],
            [(1, "TAKE_PROFIT"), (2, "TAKE_PROFIT"), (3, None), (4, None)],
        )


if __name__ == "__main__":
    unittest.main()
