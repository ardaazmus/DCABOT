"""Faz G1: simulator SHORT deal -- ters yonde ayni kapalilik kurallari.

BASE sizing ile (miktar 1): BASE 1@100 satis, SO1 1@110 satis,
TP 102.9'dan 2 geri alim. Kâr = 210 - 205.8 = 4.2; ucretler
0.1 + 0.11 + 0.2058; net "3.7842".
"""
import json
import unittest
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
        direction="SHORT", base_qty="1", safety_qty="1", safety_count=2, deviation="0.1",
        step_multiplier="1", volume_multiplier="1", take_profit="0.02",
        stop_loss_rate=None, stop_loss_confirmation_bars=None,
        initial_equity="10000", max_entry_notional="10000",
    )
    raw.update(overrides)
    return Config.parse(raw)


class SimulationShortTests(unittest.TestCase):
    def test_short_deal_opens_sells_and_covers_below(self):
        rows = [
            ("100", "100", "100", "100"),
            ("100", "112", "99", "105"),
            ("105", "106", "100", "101"),
        ]
        result = simulate_historical_ohlcv(_dataset(rows), _config(), config_hash="0" * 64)
        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertEqual(
            [(a.role, a.fill_price) for a in result.actions],
            [("BASE", "100"), ("SAFETY:1", "110"), ("EXIT", "102.9")],
        )
        self.assertEqual(result.summary["deal_pnls"], ["3.7842"])

    def test_short_safety_gap_up_fills_at_open(self):
        rows = [
            ("100", "100", "100", "100"),
            ("111", "112", "110.5", "111"),
            ("111", "111", "100", "101"),
        ]
        result = simulate_historical_ohlcv(_dataset(rows), _config(), config_hash="0" * 64)
        fills = [(a.role, a.fill_price) for a in result.actions]
        self.assertEqual(fills[0], ("BASE", "100"))
        self.assertEqual(fills[1], ("SAFETY:1", "111"))

    def test_short_take_profit_gap_down_fills_at_open(self):
        rows = [
            ("100", "100", "100", "100"),
            ("100", "101", "99", "100"),
            ("90", "91", "89", "90"),
        ]
        result = simulate_historical_ohlcv(_dataset(rows), _config(), config_hash="0" * 64)
        exits = [a for a in result.actions if a.role == "EXIT"]
        self.assertEqual(len(exits), 1)
        # TP 98; 90'dan acilis boslukla TP'nin altinda: acilistan kapanir.
        self.assertEqual(exits[0].fill_price, "90")

    def test_short_pays_slippage_on_the_short_side(self):
        rows = [("100", "100", "100", "100")]
        result = simulate_historical_ohlcv(_dataset(rows), _config(slippage="0.001"), config_hash="0" * 64)
        # Satis asagidan dolar: 100 * 0.999 = 99.9.
        self.assertEqual([(a.role, a.fill_price) for a in result.actions], [("BASE", "99.9")])

    def test_short_stop_loss_confirms_above(self):
        rows = [
            ("100", "100", "100", "100"),
            ("100", "105", "99", "104"),
            ("104", "104", "103", "103.5"),
        ]
        config = _config(stop_loss_rate="0.02", stop_loss_confirmation_bars=1)
        result = simulate_historical_ohlcv(_dataset(rows), config, config_hash="0" * 64)
        stops = [(a.role, a.fill_price) for a in result.actions if a.role == "STOP"]
        # SL 102; 104 kapanisi teyit: STOP 104'ten.
        self.assertEqual(stops, [("STOP", "104")])


if __name__ == "__main__":
    unittest.main()
