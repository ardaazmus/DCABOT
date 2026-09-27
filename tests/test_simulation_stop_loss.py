"""The simulator honours stop_loss_rate (found 2026-09-24: it silently ignored
it, so every backtest with a stop loss was computed as if there were none)."""
import json
import unittest
from fractions import Fraction
from pathlib import Path

from dcabot.application.historical_simulation import simulate_historical_ohlcv
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.domain.config import Config

ROOT = Path(__file__).resolve().parents[1]
HOUR = 3_600_000_000


def _dataset(rows):
    bars = tuple(CanonicalBar(i * HOUR, (i + 1) * HOUR - 1, o, h, low, c, "1", True) for i, (o, h, low, c) in enumerate(rows))
    return HistoricalDatasetInput(HistoricalDatasetMetadata("t", "s", "BTCUSDT", "1h", "a", "b", "0" * 64, 0, "MICROSECOND", "UTC"), bars)


def _config(**overrides):
    raw = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
    raw.update(
        base_qty="1", safety_qty="1", safety_count=1, deviation="0.2", take_profit="0.02",
        stop_loss_rate="0.05", stop_loss_confirmation_bars=1, initial_equity="10000", max_entry_notional="10000",
    )
    raw.update(overrides)
    return Config.parse(raw)


class SimulationStopLossTests(unittest.TestCase):
    def test_confirmed_close_below_the_stop_exits_and_a_new_deal_starts(self):
        rows = [
            ("100", "100.5", "99.5", "100"),
            ("100", "100.2", "93.5", "94"),
            ("94", "94.5", "93.8", "94.2"),
        ]
        result = simulate_historical_ohlcv(_dataset(rows), _config(), config_hash="0" * 64)
        roles = [(a.role, a.fill_price) for a in result.actions]
        self.assertEqual(roles, [("BASE", "100"), ("STOP", "94"), ("BASE", "94")])
        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertLess(Fraction(result.summary["deal_pnls"][0]), 0)

    def test_confirmation_bars_require_consecutive_closes(self):
        rows = [
            ("100", "100.5", "99.5", "100"),
            ("100", "100.2", "93.5", "94"),
            ("94", "96.5", "93.8", "96"),
            ("96", "96.2", "93.5", "94"),
            ("94", "94.2", "93.6", "93.9"),
        ]
        result = simulate_historical_ohlcv(_dataset(rows), _config(stop_loss_confirmation_bars=2), config_hash="0" * 64)
        stops = [a for a in result.actions if a.role == "STOP"]
        self.assertEqual(len(stops), 1)
        self.assertEqual(stops[0].bar_index, 5)

    def test_without_stop_loss_the_position_is_held(self):
        rows = [("100", "100.5", "99.5", "100"), ("100", "100.2", "93.5", "94"), ("94", "94.5", "93.8", "94.2")]
        result = simulate_historical_ohlcv(
            _dataset(rows), _config(stop_loss_rate=None, stop_loss_confirmation_bars=None), config_hash="0" * 64
        )
        self.assertEqual([a.role for a in result.actions], ["BASE"])
        self.assertEqual(result.summary["position_status"], "OPEN_AT_END")



class BudgetAndGuardTests(unittest.TestCase):
    def test_budget_equal_to_required_funds_fills_every_safety_order(self):
        from dcabot.application.sector_backtest import run_sector_backtest
        from dcabot.application.sector_dca import SymbolRules, derive_deal_config, parse_sector_dca, summarize_deal_plan
        from dcabot.data_adapters.binance_public_transport import BinancePublicKline

        rules = SymbolRules("BTCUSDT", "TRADING", "BTC", "USDT", "0.01", "0.00001", "0.00001", "5")
        params = parse_sector_dca(dict(
            symbol="BTCUSDT", base_order="25", safety_order="25", max_safety_orders=6, max_active_safety_orders=None,
            price_deviation="1.5", safety_order_volume_scale="1.5", safety_order_step_scale="1", take_profit="2", stop_loss=None,
        ))
        template = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
        plan = summarize_deal_plan(
            derive_deal_config(params, rules=rules, reference_price=Fraction(100), budget=Fraction(10**6), template=template), Fraction(100)
        )
        budget = Fraction(plan["required_funds"])
        prices = [100 - i for i in range(0, 12)]
        bars = tuple(
            BinancePublicKline(i * HOUR, (i + 1) * HOUR - 1, f"{p}", f"{p}", f"{p - 1}", f"{p - 1}", "1")
            for i, p in enumerate(prices)
        )
        result = run_sector_backtest(params, rules=rules, budget=budget, interval="1h", interval_us=HOUR, bars=bars, template=template)
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["deals"][0]["safety_orders_filled"], 6)

    def test_drawdown_guard_closes_the_position_instead_of_failing_the_run(self):
        rows = [("100", "100.5", "99.5", "100"), ("100", "100", "94", "95"), ("95", "95", "60", "61"), ("61", "61", "55", "56")]
        config = _config(
            safety_count=3, deviation="0.05", stop_loss_rate=None, stop_loss_confirmation_bars=None,
            initial_equity="400", max_entry_notional="400", max_drawdown="0.25", minimum_equity="0",
        )
        result = simulate_historical_ohlcv(_dataset(rows), config, config_hash="0" * 64)
        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertIn("STOP", [a.role for a in result.actions])
        self.assertTrue(result.summary["halted"])


class SameBarFillAndStopTests(unittest.TestCase):
    def test_a_safety_fill_and_a_confirmed_stop_on_the_same_bar_both_apply(self):
        rows = [("100", "100.5", "99.5", "100"), ("100", "100", "85", "86")]
        config = _config(safety_count=1, deviation="0.1", stop_loss_rate="0.05", stop_loss_confirmation_bars=1)
        result = simulate_historical_ohlcv(_dataset(rows), config, config_hash="0" * 64)
        self.assertEqual([(a.role, a.bar_index) for a in result.actions], [("BASE", 1), ("SAFETY:1", 2), ("STOP", 2)])
        self.assertEqual(result.execution_status, "COMPLETED")


if __name__ == "__main__":
    unittest.main()
