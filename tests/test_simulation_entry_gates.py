"""Faz G1-kalan/a: simulator giris kapilari -- cooldown + fiyat bandi.

Kapi kurali (backtest ve paper'da ayni `step_closed_bar`):
- BASE, kapanan deal'in `close_time_us + cooldown` degerinden once acilmaz.
- BASE, bar acilisi bant disindayken acilmaz (sinirlar dahildir).
Referans fiyat, dolum referansinin ta kendisidir (bar acilisi).

Kurgu (LONG, guvenliksiz, TP %2): bar0 BASE@100, bar1 TP 102 EXIT.
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
        base_qty="1", safety_qty="1", safety_count=0, deviation="0.1",
        step_multiplier="1", volume_multiplier="1", take_profit="0.02",
        stop_loss_rate=None, stop_loss_confirmation_bars=None,
        initial_equity="10000", max_entry_notional="10000",
    )
    raw.update(overrides)
    return Config.parse(raw)


def _fills(result):
    return [(a.role, a.fill_price, a.deal_sequence, a.open_time_us) for a in result.actions]


class SimulationCooldownTests(unittest.TestCase):
    ROWS = [
        ("100", "100", "100", "100"),
        ("100", "103", "99", "101"),
        ("100", "100", "100", "100"),
        ("100", "100", "100", "100"),
    ]

    def test_cooldown_skips_exactly_one_hourly_bar(self):
        result = simulate_historical_ohlcv(_dataset(self.ROWS), _config(cooldown_seconds=3600), config_hash="0" * 64)
        self.assertEqual(result.execution_status, "COMPLETED")
        # Kapanis bar1'de (close 2H-1); +1s bekleme bar2'yi (acilis 2H)
        # atlatir, bar3 (acilis 3H) yeni deal acar.
        self.assertEqual(
            _fills(result),
            [("BASE", "100", 1, 0), ("EXIT", "102", 1, HOUR), ("BASE", "100", 2, 3 * HOUR)],
        )

    def test_zero_cooldown_reopens_immediately(self):
        result = simulate_historical_ohlcv(_dataset(self.ROWS), _config(), config_hash="0" * 64)
        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertEqual(
            _fills(result),
            [("BASE", "100", 1, 0), ("EXIT", "102", 1, HOUR), ("BASE", "100", 2, 2 * HOUR)],
        )


class SimulationPriceBandTests(unittest.TestCase):
    def test_band_skips_outside_bars_edges_included(self):
        rows = [
            ("100", "100", "100", "100"),
            ("100", "103", "99", "101"),
            ("120", "121", "119", "120"),
            ("80", "81", "79", "80"),
            ("110", "110", "110", "110"),
        ]
        config = _config(min_entry_price="90", max_entry_price="110")
        result = simulate_historical_ohlcv(_dataset(rows), config, config_hash="0" * 64)
        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertEqual(
            _fills(result),
            [("BASE", "100", 1, 0), ("EXIT", "102", 1, HOUR), ("BASE", "110", 2, 4 * HOUR)],
        )

    def test_no_band_opens_everywhere(self):
        rows = [
            ("100", "100", "100", "100"),
            ("100", "103", "99", "101"),
            ("120", "121", "119", "120"),
        ]
        result = simulate_historical_ohlcv(_dataset(rows), _config(), config_hash="0" * 64)
        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertEqual(
            _fills(result),
            [("BASE", "100", 1, 0), ("EXIT", "102", 1, HOUR), ("BASE", "120", 2, 2 * HOUR)],
        )


if __name__ == "__main__":
    unittest.main()
