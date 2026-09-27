"""Faz W-B2 runner core: a paper bot fed live bars in arbitrary chunks, with its
runtime persisted and reloaded between chunks, must trade exactly like a
backtest of the same settings over the same bars."""
import json
import random
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from dcabot.application.historical_simulation import simulate_historical_ohlcv
from dcabot.application.paper_bot_runner import RUNNER_INTERVAL_US, advance_bot
from dcabot.application.sector_dca import SymbolRules, derive_deal_config, parse_sector_dca
from dcabot.data_adapters.binance_public_transport import BinancePublicKline
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.domain.config import Config
from dcabot.domain.engine import State
from dcabot.persistence.bot_store import BotRecord, BotRuntime, BotStore

ROOT = Path(__file__).resolve().parents[1]
RULES = SymbolRules("BTCUSDT", "TRADING", "BTC", "USDT", "0.01", "0.00001", "0.00001", "5")
TEMPLATE = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
START_US = 1_790_000_000 * 1_000_000 // RUNNER_INTERVAL_US * RUNNER_INTERVAL_US


def _walk(count: int, seed: int) -> tuple[BinancePublicKline, ...]:
    rng = random.Random(seed)
    price = 100.0
    bars = []
    for i in range(count):
        open_ = price
        price = max(20.0, price * (1 + rng.uniform(-0.006, 0.006)))
        high = max(open_, price) * (1 + rng.uniform(0, 0.0015))
        low = min(open_, price) * (1 - rng.uniform(0, 0.0015))
        t = START_US + i * RUNNER_INTERVAL_US
        bars.append(BinancePublicKline(t, t + RUNNER_INTERVAL_US - 1, f"{open_:.2f}", f"{high:.2f}", f"{low:.2f}", f"{price:.2f}", "1"))
    return tuple(bars)


def _raw_config(stop_loss=None):
    params = parse_sector_dca(dict(
        symbol="BTCUSDT", base_order="25", safety_order="25", max_safety_orders=5, max_active_safety_orders=None,
        price_deviation="0.8", safety_order_volume_scale="1.5", safety_order_step_scale="1.2", take_profit="1", stop_loss=stop_loss,
    ))
    return derive_deal_config(params, rules=RULES, reference_price=Fraction(100), budget=Fraction(2000), template=TEMPLATE)


def _fresh_runtime(raw: dict) -> BotRuntime:
    return BotRuntime("bot_test", raw, State(), 0, Fraction(0), START_US - RUNNER_INTERVAL_US, 0)


class PaperRunnerEquivalenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BotStore(Path(self.tmp.name) / "bots.sqlite3")
        self.store.create(BotRecord("bot_test", "t", "DCA", "PAPER", "BTCUSDT", {}, "2000", "STOPPED", None, 1, 0, 0, None))

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_chunked_persisted_runner_equals_backtest(self):
        compared = 0
        for seed in range(10):
            raw = _raw_config(stop_loss="3" if seed % 2 else None)
            bars = _walk(900, seed)
            dataset = HistoricalDatasetInput(
                HistoricalDatasetMetadata("t", "s", "BTCUSDT", "1m", "a", "b", "0" * 64, 0, "MICROSECOND", "UTC"),
                tuple(CanonicalBar(b.open_time_us, b.close_time_us, b.open, b.high, b.low, b.close, b.base_volume, True) for b in bars),
            )
            backtest = simulate_historical_ohlcv(dataset, Config.parse(raw), config_hash="0" * 64, max_bars=20_000)
            if backtest.execution_status != "COMPLETED":
                continue
            rng = random.Random(1000 + seed)
            runtime = _fresh_runtime(raw)
            open_deal = None
            self.store.save_runtime(runtime)
            position = 0
            while position < len(bars):
                size = rng.randint(1, 120)
                runtime = self.store.get_runtime("bot_test")
                deals = self.store.list_deals("bot_test")
                open_deal = next((d for d in deals if d.closed_at_us is None), None)
                result = advance_bot(runtime, bars[position:position + size], open_deal=open_deal, allow_new_deal=True, now_us=1, symbol="BTCUSDT")
                self.store.save_runtime(result.runtime, deals=result.deals, events=result.events)
                position += size
            deals = self.store.list_deals("bot_test")
            with self.subTest(seed=seed):
                self.assertEqual([d.profit for d in deals if d.closed_at_us is not None], backtest.summary["deal_pnls"])
                closes = [a for a in backtest.actions if a.role in ("EXIT", "STOP")]
                self.assertEqual(
                    [(d.closed_at_us, d.close_reason) for d in deals if d.closed_at_us is not None],
                    [(a.open_time_us, "TAKE_PROFIT" if a.role == "EXIT" else "STOP_LOSS") for a in closes],
                )
                final = self.store.get_runtime("bot_test")
                exact = backtest.summary["exact_ratios"]
                self.assertEqual(final.state.position.qty, Fraction(int(exact["qty"][0]), int(exact["qty"][1])))
                self.assertEqual(final.state.position.cost, Fraction(int(exact["cost"][0]), int(exact["cost"][1])))
                self.assertEqual(final.last_bar_open_us, bars[-1].open_time_us)
            compared += 1
            self.store.db.execute("DELETE FROM bot_deals")
            self.store.db.execute("DELETE FROM bot_events")
        self.assertGreaterEqual(compared, 5)

    def test_paused_bot_finishes_its_deal_but_opens_no_new_one(self):
        raw = _raw_config()
        bars = _walk(600, 3)
        result = advance_bot(_fresh_runtime(raw), bars, open_deal=None, allow_new_deal=False, now_us=1)
        self.assertEqual(result.deals, ())
        self.assertEqual(result.runtime.deal_sequence, 0)
        running = advance_bot(_fresh_runtime(raw), bars, open_deal=None, allow_new_deal=True, now_us=1)
        self.assertGreater(len(running.deals), 1)
        self.assertEqual(running.events[0].kind, "DEAL_STARTED")

    def test_already_processed_bars_are_skipped(self):
        raw = _raw_config()
        bars = _walk(200, 4)
        first = advance_bot(_fresh_runtime(raw), bars, open_deal=None, allow_new_deal=True, now_us=1)
        again = advance_bot(first.runtime, bars, open_deal=None, allow_new_deal=True, now_us=2)
        self.assertEqual((again.deals, again.events), ((), ()))
        self.assertEqual(again.runtime.state, first.runtime.state)


if __name__ == "__main__":
    unittest.main()
