"""G3-c: futures grid runner core over closed bars + funding."""

import tempfile
import unittest
from pathlib import Path

from dcabot.application.futures_grid_engine import FuturesGridEngineError
from dcabot.application.futures_grid_runner import (
    advance_futures_grid,
    build_futures_grid_config,
    futures_config_from_dict,
    futures_config_to_dict,
    prepare_futures_grid_runtime,
)
from dcabot.data_adapters.binance_futures_public_transport import (
    BinanceFuturesFundingRate,
    BinanceFuturesSymbolRules,
)
from dcabot.data_adapters.binance_public_transport import BinancePublicKline
from dcabot.persistence.bot_store import BotStore

RULES = BinanceFuturesSymbolRules(
    "BTCUSDT", "TRADING", "BTC", "USDT", "PERPETUAL", "0.1", "0.001", "0.001", "5"
)
MINUTE = 60_000_000


def _strategy(**overrides: object) -> dict:
    body: dict[str, object] = {
        "symbol": "BTCUSDT",
        "direction": "LONG",
        "mode": "ARITHMETIC",
        "lower_price": "90",
        "upper_price": "110",
        "interval_count": 2,
        "leverage": 1,
        "fee_rate": "0",
        "stop_loss_price": None,
        "take_profit_pct": None,
        "trailing_up_pct": None,
        "trailing_down_pct": None,
    }
    body.update(overrides)
    return body


def _bar(index: int, o: str, h: str, low: str, c: str, start_us: int) -> BinancePublicKline:
    return BinancePublicKline(
        start_us + index * MINUTE, start_us + (index + 1) * MINUTE - 1, o, h, low, c, "10"
    )


class FuturesGridRunnerPrepareTest(unittest.TestCase):
    def test_prepare_builds_wait_snapshot(self) -> None:
        runtime = prepare_futures_grid_runtime("bot_1", _strategy(), RULES, investment="1000", now_us=MINUTE * 100)
        self.assertEqual(runtime.bot_id, "bot_1")
        self.assertEqual(runtime.config["market"], "FUTURES")
        self.assertEqual(runtime.snapshot["status"], "WAIT")
        self.assertEqual(runtime.config["fingerprint"], runtime.snapshot["config_fingerprint"])
        self.assertEqual(len(runtime.snapshot["levels"]), 3)
        self.assertEqual(runtime.last_bar_open_us, MINUTE * 100)

    def test_prepare_rejects_bad_strategy(self) -> None:
        with self.assertRaises(FuturesGridEngineError) as ctx:
            prepare_futures_grid_runtime("bot_1", _strategy(upper_price="80"), RULES, investment="1000", now_us=0)
        self.assertEqual(ctx.exception.code, "GRID_BOUNDS_INVALID")
        with self.assertRaises(FuturesGridEngineError) as ctx:
            prepare_futures_grid_runtime("bot_1", _strategy(leverage=11), RULES, investment="1000", now_us=0)
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_LEVERAGE_INVALID")

    def test_config_round_trip_and_guards(self) -> None:
        config = build_futures_grid_config(_strategy(), RULES, investment="1000")
        thawed = futures_config_from_dict(futures_config_to_dict(config))
        self.assertEqual(thawed.fingerprint, config.fingerprint)
        tampered = futures_config_to_dict(config)
        tampered["fingerprint"] = "0" * 16
        with self.assertRaises(FuturesGridEngineError) as ctx:
            futures_config_from_dict(tampered)
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_CONFIG_MISMATCH")
        spot_row = {k: v for k, v in futures_config_to_dict(config).items() if k != "market"}
        with self.assertRaises(FuturesGridEngineError) as ctx:
            futures_config_from_dict(spot_row)
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_CONFIG_INVALID")


class FuturesGridRunnerAdvanceTest(unittest.TestCase):
    def test_entry_cycle_and_funding_over_bars(self) -> None:
        start = MINUTE * 100
        runtime = prepare_futures_grid_runtime("bot_1", _strategy(), RULES, investment="1000", now_us=start)
        bars = (
            _bar(1, "100", "100", "100", "100", start),
            _bar(2, "100", "110", "100", "110", start),
            _bar(3, "110", "110", "90", "90", start),
        )
        funding = (
            BinanceFuturesFundingRate(funding_time_us=start + 3 * MINUTE + 1000, rate="0.0001"),
        )
        result = advance_futures_grid(runtime, bars, funding, now_us=start + 4 * MINUTE)
        state = result.runtime.snapshot
        self.assertIsNone(result.stopped_reason)
        self.assertEqual(state["status"], "ACTIVE")
        self.assertEqual(state["entry_price"], "100")
        self.assertEqual(state["cycles_closed"], 2)
        self.assertEqual(len(state["fills"]), 6)
        self.assertEqual(state["funding_cashflow"], "-0.094995")
        kinds = [event.kind for event in result.events]
        self.assertEqual(
            kinds,
            ["GRID_FILL", "GRID_INIT", "GRID_FILL", "GRID_FILL", "GRID_FILL", "GRID_FILL", "GRID_FILL", "GRID_FUNDING"],
        )
        funding_event = result.events[-1]
        self.assertEqual(funding_event.detail["rate"], "0.0001")
        self.assertEqual(funding_event.detail["cashflow"], "-0.094995")
        self.assertEqual(result.runtime.last_bar_open_us, start + 3 * MINUTE)

    def test_old_bars_and_funding_skipped(self) -> None:
        start = MINUTE * 100
        runtime = prepare_futures_grid_runtime("bot_1", _strategy(), RULES, investment="1000", now_us=start)
        bars = (_bar(0, "100", "100", "100", "100", start),)
        funding = (BinanceFuturesFundingRate(funding_time_us=start - 1000, rate="0.0001"),)
        result = advance_futures_grid(runtime, bars, funding, now_us=start + MINUTE)
        self.assertEqual(result.events, ())
        self.assertEqual(result.runtime.snapshot["status"], "WAIT")

    def test_stop_loss_reports_stop_reason(self) -> None:
        start = MINUTE * 100
        runtime = prepare_futures_grid_runtime(
            "bot_1", _strategy(stop_loss_price="85"), RULES, investment="1000", now_us=start
        )
        bars = (
            _bar(1, "100", "100", "100", "100", start),
            _bar(2, "100", "100", "80", "80", start),
        )
        result = advance_futures_grid(runtime, bars, (), now_us=start + 3 * MINUTE)
        self.assertEqual(result.stopped_reason, "GRID_DONE_SL")
        self.assertEqual(result.runtime.snapshot["status"], "DONE_SL")
        self.assertIn("GRID_STOP_LOSS", [event.kind for event in result.events])


class FuturesGridRuntimeStoreTest(unittest.TestCase):
    def test_save_and_get_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = BotStore(Path(tmp) / "bots.sqlite3")
            runtime = prepare_futures_grid_runtime("bot_1", _strategy(), RULES, investment="1000", now_us=7)
            self.assertIsNone(store.get_grid_runtime("bot_1"))
            store.save_grid_runtime(runtime)
            loaded = store.get_grid_runtime("bot_1")
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.snapshot, runtime.snapshot)
            self.assertEqual(loaded.config["market"], "FUTURES")
            store.close()


if __name__ == "__main__":
    unittest.main()
