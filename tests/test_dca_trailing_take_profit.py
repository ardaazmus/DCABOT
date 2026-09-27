"""F09a: DCA trailing take-profit -- close-only ratchet in step_closed_bar.

Semantics (3Commas-style, honest close-only bar model, same bar as the
H.2 stop-loss confirmation):
- With trailing configured the fixed intrabar TP exit is OFF; nothing
  exits on a wick -- only closes move the ratchet.
- Activation: first close at/beyond the TP target arms the water at
  that close (not at the target).
- LONG holds while close >= water*(1-trail), exits at the close below
  it; SHORT mirrors (water = lowest close, exit above water*(1+trail)).
- Averages moving (safety fills) never reset an armed ratchet; a new
  deal starts unarmed (fresh State via _start_new_deal).
"""
import json
import unittest
from fractions import Fraction as F
from pathlib import Path

from dcabot.application.historical_simulation import simulate_historical_ohlcv
from dcabot.application.sector_dca import (
    SectorDcaError,
    SymbolRules,
    derive_deal_config,
    parse_sector_dca,
)
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.domain.config import Config

ROOT = Path(__file__).resolve().parents[1]
HOUR = 3_600_000_000
RULES = SymbolRules("BTCUSDT", "TRADING", "BTC", "USDT", "0.01", "0.001", "0.001", "5")
TEMPLATE = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))


def _sector_raw(**overrides):
    body = dict(
        symbol="BTCUSDT", base_order="100", safety_order="100", max_safety_orders=2,
        max_active_safety_orders=None, price_deviation="10", safety_order_volume_scale="1",
        safety_order_step_scale="1", take_profit="5", stop_loss=None, direction="LONG",
        cooldown_seconds=0, min_price=None, max_price=None,
    )
    body.update(overrides)
    return body


def _dataset(rows):
    bars = tuple(CanonicalBar(i * HOUR, (i + 1) * HOUR - 1, o, h, low, c, "1", True) for i, (o, h, low, c) in enumerate(rows))
    return HistoricalDatasetInput(HistoricalDatasetMetadata("t", "s", "BTCUSDT", "1h", "a", "b", "0" * 64, 0, "MICROSECOND", "UTC"), bars)


def _config(**overrides):
    raw = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
    raw.update(
        base_qty="1", safety_qty="1", safety_count=0, deviation="0.1",
        step_multiplier="1", volume_multiplier="1", take_profit="0.05",
        stop_loss_rate=None, stop_loss_confirmation_bars=None,
        trailing_take_profit_rate="0.01",
        initial_equity="10000", max_entry_notional="10000",
    )
    raw.update(overrides)
    return Config.parse(raw)


def _fills(result):
    return [(a.role, a.fill_price, a.deal_sequence, a.open_time_us) for a in result.actions]


class TrailingLongTests(unittest.TestCase):
    # BASE@100, TP %5 -> hedef 105, trail %1.
    # b1 fitili (106) ateslemez; b2 arm(105.5); b3 su 107; b4 tutar
    # (106.5 >= 105.93); b5 cikar (105.5 < 105.93); b6 yeni deal.
    ROWS = [
        ("100", "100", "100", "100"),
        ("100", "106", "100", "104"),
        ("104", "106", "104", "105.5"),
        ("105.5", "107.5", "105.5", "107"),
        ("107", "107", "106", "106.5"),
        ("106.5", "106.5", "105", "105.5"),
        ("105.5", "105.5", "105.5", "105.5"),
    ]

    def test_wick_ignored_arm_ratchet_hold_exit(self):
        result = simulate_historical_ohlcv(_dataset(self.ROWS), _config(), config_hash="0" * 64)
        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertEqual(
            _fills(result),
            [("BASE", "100", 1, 0), ("EXIT", "105.5", 1, 5 * HOUR), ("BASE", "105.5", 2, 6 * HOUR)],
        )


class TrailingShortTests(unittest.TestCase):
    # SHORT aynasi: BASE@100, hedef 95, su en dusuk kapanis; tetik
    # su*(1+trail): b3 su 93 -> tetik 93.93; b4 tutar (93.5),
    # b5 cikar (94.5 > 93.93).
    ROWS = [
        ("100", "100", "100", "100"),
        ("100", "100", "94", "96"),
        ("96", "96", "94", "94.5"),
        ("94.5", "94.5", "93", "93"),
        ("93", "93.5", "93", "93.5"),
        ("93.5", "94.5", "93.5", "94.5"),
        ("94.5", "94.5", "94.5", "94.5"),
    ]

    def test_short_mirror(self):
        result = simulate_historical_ohlcv(_dataset(self.ROWS), _config(direction="SHORT"), config_hash="0" * 64)
        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertEqual(
            _fills(result),
            [("BASE", "100", 1, 0), ("EXIT", "94.5", 1, 5 * HOUR), ("BASE", "94.5", 2, 6 * HOUR)],
        )


class TrailingRearmTests(unittest.TestCase):
    # Guvenlik dolumu ortalamayi oynatir (100 -> 95, hedef 105 ->
    # 99.75); eski zirve (105.5) cop olur. Yeniden kurma olmasa b2
    # kapanisinda 91'den ZARARINA cikilirdi; dogrusu: tut, 99.75
    # uzerinde yeniden kur, iz sur, 99.2'den karda cik.
    ROWS = [
        ("100", "100", "100", "100"),
        ("100", "106", "100", "105.5"),
        ("105.5", "105.5", "89", "91"),
        ("91", "100", "91", "99.8"),
        ("99.8", "101", "99.8", "100.5"),
        ("100.5", "100.5", "99", "99.2"),
        ("99.2", "99.2", "99.2", "99.2"),
    ]

    def test_safety_fill_rearms_from_new_average(self):
        config = _config(safety_count=1, safety_qty="1", deviation="0.1")
        result = simulate_historical_ohlcv(_dataset(self.ROWS), config, config_hash="0" * 64)
        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertEqual(
            _fills(result),
            [
                ("BASE", "100", 1, 0),
                ("SAFETY:1", "90", 1, 2 * HOUR),
                ("EXIT", "99.2", 1, 5 * HOUR),
                ("BASE", "99.2", 2, 6 * HOUR),
            ],
        )


class TrailingStopLossPrecedenceTests(unittest.TestCase):
    # Ayni barda hem SL teyidi hem trailing tetiklenirse STOP
    # kazanir: b2 kapanisi 96 hem SL esiginin (97) hem trailing
    # tetikleyicinin (104.445) altindadir.
    ROWS = [
        ("100", "100", "100", "100"),
        ("100", "106", "100", "105.5"),
        ("105.5", "105.5", "95", "96"),
        ("96", "96", "96", "96"),
    ]

    def test_confirmed_stop_beats_trailing_same_bar(self):
        config = _config(stop_loss_rate="0.03", stop_loss_confirmation_bars=1)
        result = simulate_historical_ohlcv(_dataset(self.ROWS), config, config_hash="0" * 64)
        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertEqual(
            _fills(result),
            [("BASE", "100", 1, 0), ("STOP", "96", 1, 2 * HOUR), ("BASE", "96", 2, 3 * HOUR)],
        )


class TrailingSectorTests(unittest.TestCase):
    def test_absent_means_fixed_tp(self):
        params = parse_sector_dca(_sector_raw())
        self.assertIsNone(params.trailing_take_profit)
        raw = derive_deal_config(params, rules=RULES, reference_price=F(100), budget=F(10000), template=TEMPLATE)
        self.assertIsNone(Config.parse(raw).trailing_take_profit_rate)

    def test_percent_maps_to_fraction(self):
        params = parse_sector_dca(_sector_raw(trailing_take_profit="1"))
        self.assertEqual(params.trailing_take_profit, F(1))
        raw = derive_deal_config(params, rules=RULES, reference_price=F(100), budget=F(10000), template=TEMPLATE)
        self.assertEqual(Config.parse(raw).trailing_take_profit_rate, F(1, 100))

    def test_out_of_range_rejected(self):
        for bad in ("0", "100", "-1", "abc"):
            with self.assertRaises(SectorDcaError, msg=bad):
                parse_sector_dca(_sector_raw(trailing_take_profit=bad))

    def test_combo_plus_trailing_rejected_with_named_field(self):
        with self.assertRaises(SectorDcaError) as ctx:
            parse_sector_dca(_sector_raw(trailing_take_profit="1", combined_take_profit="5"))
        self.assertEqual(ctx.exception.field, "trailing_take_profit")


if __name__ == "__main__":
    unittest.main()
