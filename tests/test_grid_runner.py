"""G2-c: grid runner core + grid runtime persistence."""

import tempfile
import unittest
from pathlib import Path

from dcabot.application.grid_runner import (
    advance_grid,
    build_grid_config,
    config_from_dict,
    config_to_dict,
    prepare_grid_runtime,
)
from dcabot.application.sector_dca import SymbolRules
from dcabot.application.spot_grid_engine import SpotGridEngineError
from dcabot.data_adapters.binance_public_transport import BinancePublicKline
from dcabot.persistence.bot_store import BotStore

RULES = SymbolRules("BTCUSDT", "TRADING", "BTC", "USDT", "0.01", "0.00001", "0.00001", "5")
MINUTE = 60_000_000


def _strategy(**overrides: object) -> dict:
    body: dict[str, object] = {
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


def _bar(index: int, o: str, h: str, low: str, c: str, start_us: int) -> BinancePublicKline:
    return BinancePublicKline(
        start_us + index * MINUTE, start_us + (index + 1) * MINUTE - 1, o, h, low, c, "10"
    )


class GridRunnerPrepareTest(unittest.TestCase):
    def test_prepare_builds_wait_snapshot(self) -> None:
        runtime = prepare_grid_runtime("bot_1", _strategy(), RULES, investment="900", now_us=MINUTE * 100)
        self.assertEqual(runtime.bot_id, "bot_1")
        self.assertEqual(runtime.snapshot["status"], "WAIT")
        self.assertEqual(runtime.config["fingerprint"], runtime.snapshot["config_fingerprint"])
        self.assertEqual(len(runtime.snapshot["levels"]), 10)
        self.assertEqual(runtime.last_bar_open_us, MINUTE * 100)

    def test_prepare_rejects_bad_strategy(self) -> None:
        with self.assertRaises(SpotGridEngineError) as ctx:
            prepare_grid_runtime("bot_1", _strategy(upper_price="70000"), RULES, investment="900", now_us=0)
        self.assertEqual(ctx.exception.code, "GRID_BOUNDS_INVALID")

    def test_config_round_trip_and_fingerprint_guard(self) -> None:
        config = build_grid_config(_strategy(), RULES, investment="900")
        thawed = config_from_dict(config_to_dict(config))
        self.assertEqual(thawed.fingerprint, config.fingerprint)
        tampered = config_to_dict(config)
        tampered["fingerprint"] = "0" * 16
        with self.assertRaises(SpotGridEngineError) as ctx:
            config_from_dict(tampered)
        self.assertEqual(ctx.exception.code, "SPOT_GRID_CONFIG_MISMATCH")


class GridRunnerAdvanceTest(unittest.TestCase):
    def test_entry_and_cycle_over_one_bar(self) -> None:
        start = MINUTE * 100
        runtime = prepare_grid_runtime("bot_1", _strategy(), RULES, investment="900", now_us=start)
        bars = (_bar(1, "79000", "81250", "79000", "81200", start),)
        result = advance_grid(runtime, bars, now_us=start + 2 * MINUTE)
        state = result.runtime.snapshot
        self.assertIsNone(result.stopped_reason)
        self.assertEqual(state["status"], "ACTIVE")
        self.assertEqual(state["entry_price"], "81250")
        self.assertEqual(state["cycles_closed"], 1)
        self.assertEqual(len(state["fills"]), 10)
        self.assertEqual(state["realized_profit_quote"], "-798.25")
        self.assertEqual(state["quote_reserve"], "0.5")
        kinds = [event.kind for event in result.events]
        self.assertEqual(kinds, ["GRID_FILL"] * 8 + ["GRID_INIT", "GRID_FILL", "GRID_FILL"])
        self.assertEqual(result.runtime.last_bar_open_us, start + MINUTE)

    def test_old_bars_skipped(self) -> None:
        start = MINUTE * 100
        runtime = prepare_grid_runtime("bot_1", _strategy(), RULES, investment="900", now_us=start)
        bars = (_bar(0, "81250", "81300", "81200", "81250", start),)
        result = advance_grid(runtime, bars, now_us=start + MINUTE)
        self.assertEqual(result.events, ())
        self.assertEqual(result.runtime.snapshot["status"], "WAIT")

    def test_stop_loss_reports_stop_reason(self) -> None:
        start = MINUTE * 100
        runtime = prepare_grid_runtime(
            "bot_1", _strategy(stop_loss_price="78000"), RULES, investment="900", now_us=start
        )
        bars = (
            _bar(1, "81250", "81300", "81200", "81250", start),
            _bar(2, "81250", "81250", "77000", "77000", start),
        )
        result = advance_grid(runtime, bars, now_us=start + 3 * MINUTE)
        self.assertEqual(result.stopped_reason, "GRID_DONE_SL")
        self.assertEqual(result.runtime.snapshot["status"], "DONE_SL")
        self.assertIn("GRID_STOP_LOSS", [event.kind for event in result.events])


class GridRuntimeStoreTest(unittest.TestCase):
    def test_save_and_get_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = BotStore(Path(tmp) / "bots.sqlite3")
            runtime = prepare_grid_runtime("bot_1", _strategy(), RULES, investment="900", now_us=7)
            self.assertIsNone(store.get_grid_runtime("bot_1"))
            store.save_grid_runtime(runtime)
            loaded = store.get_grid_runtime("bot_1")
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.snapshot, runtime.snapshot)
            self.assertEqual(loaded.config["fingerprint"], runtime.config["fingerprint"])
            store.close()

    def test_prune_keeps_newest_events(self) -> None:
        from dcabot.persistence.bot_store import BotEvent

        with tempfile.TemporaryDirectory() as tmp:
            store = BotStore(Path(tmp) / "bots.sqlite3")
            runtime = prepare_grid_runtime("bot_1", _strategy(), RULES, investment="900", now_us=7)
            events = tuple(BotEvent("bot_1", index, "GRID_FILL", {"fill_id": f"grid:{index}"}) for index in range(105))
            store.save_grid_runtime(runtime, events=events)
            removed = store.prune_bot_events("bot_1", keep=100)
            self.assertEqual(removed, 5)
            self.assertEqual(len(store.list_events("bot_1", limit=500)), 100)
            store.close()


if __name__ == "__main__":
    unittest.main()
