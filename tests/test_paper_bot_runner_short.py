"""Faz G1: SHORT paper runner -- a short bot fed live bars trades exactly
like a backtest of the same settings (BASE 1@100 sell, SO1 1@110 sell,
EXIT 2@102.9 cover; net "3.7842", same as the simulator test)."""
import json
import unittest
from fractions import Fraction
from pathlib import Path

from dcabot.application.historical_simulation import simulate_historical_ohlcv
from dcabot.application.paper_bot_runner import RUNNER_INTERVAL_US, advance_bot
from dcabot.data_adapters.binance_public_transport import BinancePublicKline
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.domain.config import Config
from dcabot.domain.engine import State
from dcabot.persistence.bot_store import BotRuntime

ROOT = Path(__file__).resolve().parents[1]
START_US = 1_790_000_000 * 1_000_000 // RUNNER_INTERVAL_US * RUNNER_INTERVAL_US


def _raw():
    raw = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
    raw.update(
        direction="SHORT", base_qty="1", safety_qty="1", safety_count=2, deviation="0.1",
        step_multiplier="1", volume_multiplier="1", take_profit="0.02",
        stop_loss_rate=None, stop_loss_confirmation_bars=None,
        initial_equity="10000", max_entry_notional="10000",
    )
    return raw


def _klines(rows):
    out = []
    for i, (o, h, low, c) in enumerate(rows):
        t = START_US + i * RUNNER_INTERVAL_US
        out.append(BinancePublicKline(t, t + RUNNER_INTERVAL_US - 1, o, h, low, c, "1"))
    return tuple(out)


ROWS = (
    ("100", "100", "100", "100"),
    ("100", "112", "99", "105"),
    ("105", "106", "100", "101"),
)


class PaperRunnerShortTests(unittest.TestCase):
    def test_short_runner_closes_with_exact_profit(self):
        runtime = BotRuntime("bot_test", _raw(), State(), 0, Fraction(0), START_US - RUNNER_INTERVAL_US, 0)
        result = advance_bot(runtime, _klines(ROWS), open_deal=None, allow_new_deal=True, now_us=1)
        closed = [d for d in result.deals if d.closed_at_us is not None]
        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0].profit, "3.7842")
        self.assertEqual(closed[0].close_reason, "TAKE_PROFIT")
        kinds = [e.kind for e in result.events]
        self.assertEqual(kinds, ["DEAL_STARTED", "SAFETY_ORDER_FILLED", "DEAL_CLOSED"])
        self.assertEqual(result.runtime.last_bar_open_us, START_US + 2 * RUNNER_INTERVAL_US)

    def test_short_runner_equals_backtest(self):
        klines = _klines(ROWS)
        runtime = BotRuntime("bot_test", _raw(), State(), 0, Fraction(0), START_US - RUNNER_INTERVAL_US, 0)
        result = advance_bot(runtime, klines, open_deal=None, allow_new_deal=True, now_us=1)
        dataset = HistoricalDatasetInput(
            HistoricalDatasetMetadata("t", "s", "BTCUSDT", "1m", "a", "b", "0" * 64, 0, "MICROSECOND", "UTC"),
            tuple(CanonicalBar(b.open_time_us, b.close_time_us, b.open, b.high, b.low, b.close, b.base_volume, True) for b in klines),
        )
        backtest = simulate_historical_ohlcv(dataset, Config.parse(_raw()), config_hash="0" * 64)
        self.assertEqual(backtest.execution_status, "COMPLETED")
        self.assertEqual(
            [d.profit for d in result.deals if d.closed_at_us is not None],
            backtest.summary["deal_pnls"],
        )


if __name__ == "__main__":
    unittest.main()
