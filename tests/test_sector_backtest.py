"""Faz W v2 backtest: paged venue klines, local kline cache, and the sector
backtest statistics (checked as invariants over seeded random walks)."""
import json
import random
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dcabot.application.sector_backtest import run_sector_backtest
from dcabot.application.sector_dca import SymbolRules, parse_sector_dca
from dcabot.data_adapters.binance_public_transport import (
    BinancePublicKline,
    BinancePublicTransportError,
    fetch_binance_public_klines_range,
)
from dcabot.domain.numbers import number
from dcabot.persistence.kline_cache import KlineCache

ROOT = Path(__file__).resolve().parents[1]
HOUR = 3_600_000_000
RULES = SymbolRules("BTCUSDT", "TRADING", "BTC", "USDT", "0.01", "0.00001", "0.00001", "5")
TEMPLATE = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))


def _walk(count: int, seed: int, start_us: int = 0) -> tuple[BinancePublicKline, ...]:
    rng = random.Random(seed)
    price = 100.0
    bars = []
    for i in range(count):
        open_ = price
        price = max(20.0, price * (1 + rng.uniform(-0.012, 0.012)))
        high = max(open_, price) * (1 + rng.uniform(0, 0.003))
        low = min(open_, price) * (1 - rng.uniform(0, 0.003))
        bars.append(
            BinancePublicKline(start_us + i * HOUR, start_us + (i + 1) * HOUR - 1, f"{open_:.2f}", f"{high:.2f}", f"{low:.2f}", f"{price:.2f}", "10")
        )
    return tuple(bars)


def _params(**overrides):
    raw = dict(
        symbol="BTCUSDT", base_order="25", safety_order="25", max_safety_orders=6, max_active_safety_orders=2,
        price_deviation="1.5", safety_order_volume_scale="1.5", safety_order_step_scale="1.2", take_profit="2", stop_loss=None,
    )
    raw.update(overrides)
    return parse_sector_dca(raw)


class _PagedOpener:
    """Serves 1h klines for any startTime/endTime window, 1000 per page."""

    def __init__(self, last_open_ms: int):
        self.last_open_ms = last_open_ms
        self.calls = []

    def open(self, request, timeout):
        query = {k: v[0] for k, v in parse_qs(urlparse(request.full_url).query).items()}
        self.calls.append(query)
        start, end, limit = int(query["startTime"]), int(query["endTime"]), int(query["limit"])
        rows = []
        t = start - start % 3_600_000
        while t <= min(end, self.last_open_ms) and len(rows) < limit:
            rows.append([t, "100", "101", "99", "100.5", "1", t + 3_599_999, "0", 1, "0", "0", "0"])
            t += 3_600_000
        return _Resp(rows)


class _Resp:
    def __init__(self, rows):
        self.status = 200
        self._body = json.dumps(rows).encode()
        self.headers = {}

    def read(self, size=-1):
        data, self._body = self._body[:size], self._body[size:]
        return data

    def close(self):
        pass


class KlineRangeFetchTests(unittest.TestCase):
    def test_pages_until_the_range_is_covered_and_drops_forming_bars(self):
        opener = _PagedOpener(last_open_ms=2_500 * 3_600_000)
        now_us = 2_500 * HOUR + 10
        bars = fetch_binance_public_klines_range(
            "BTCUSDT", interval="1h", start_us=0, end_us=2_501 * HOUR, max_bars=5000, now_us=now_us,
            allowed_symbols=frozenset({"BTCUSDT"}), opener=opener,
        )
        self.assertEqual(len(opener.calls), 3)
        self.assertEqual(len(bars), 2_500)
        self.assertEqual(bars[-1].open_time_us, 2_499 * HOUR)
        self.assertTrue(all(b.open_time_us - a.open_time_us == HOUR for a, b in zip(bars, bars[1:])))

    def test_oversized_range_fails_before_any_request(self):
        opener = _PagedOpener(last_open_ms=10**9)
        with self.assertRaises(BinancePublicTransportError) as ctx:
            fetch_binance_public_klines_range(
                "BTCUSDT", interval="1h", start_us=0, end_us=20_001 * HOUR, max_bars=20_000, now_us=10**18,
                allowed_symbols=frozenset({"BTCUSDT"}), opener=opener,
            )
        self.assertEqual(ctx.exception.code, "PUBLIC_RANGE_TOO_LARGE")
        self.assertEqual(opener.calls, [])

    def test_unsupported_interval_is_rejected(self):
        with self.assertRaises(BinancePublicTransportError):
            fetch_binance_public_klines_range(
                "BTCUSDT", interval="3m", start_us=0, end_us=HOUR, max_bars=10, now_us=10**18,
                allowed_symbols=frozenset({"BTCUSDT"}), opener=_PagedOpener(0),
            )


class KlineCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = KlineCache(Path(self.tmp.name) / "k.sqlite3")

    def tearDown(self):
        self.cache.close()
        self.tmp.cleanup()

    def test_full_range_round_trips_exactly_and_partial_range_is_a_miss(self):
        bars = _walk(50, 1)
        self.cache.put("BTCUSDT", "1h", bars, now_us=10**18)
        self.assertEqual(self.cache.get_range("BTCUSDT", "1h", 0, 50 * HOUR, HOUR), bars)
        self.assertEqual(self.cache.get_range("BTCUSDT", "1h", 10 * HOUR, 20 * HOUR, HOUR), bars[10:20])
        self.assertIsNone(self.cache.get_range("BTCUSDT", "1h", 0, 51 * HOUR, HOUR))
        self.assertIsNone(self.cache.get_range("ETHUSDT", "1h", 0, 10 * HOUR, HOUR))

    def test_forming_bars_are_never_stored(self):
        bars = _walk(5, 2)
        self.cache.put("BTCUSDT", "1h", bars, now_us=4 * HOUR + 5)
        self.assertIsNone(self.cache.get_range("BTCUSDT", "1h", 0, 5 * HOUR, HOUR))
        self.assertEqual(len(self.cache.get_range("BTCUSDT", "1h", 0, 4 * HOUR, HOUR)), 4)


class SectorBacktestInvariantTests(unittest.TestCase):
    def test_statistics_are_mutually_consistent_over_random_walks(self):
        completed_runs = 0
        for seed in range(12):
            bars = _walk(1500, 100 + seed)
            result = run_sector_backtest(
                _params(), rules=RULES, budget=Fraction(1000), interval="1h", interval_us=HOUR, bars=bars, template=TEMPLATE
            )
            summary = result["summary"]
            closed = [deal for deal in result["deals"] if deal["closed_at_us"] is not None]
            with self.subTest(seed=seed, status=result["status"]):
                self.assertEqual(len(result["equity_curve"]), result["processed_bar_count"])
                self.assertEqual(summary["deals_completed"], len(closed))
                self.assertEqual(sum(row["deals"] for row in result["safety_order_usage"]), len(closed))
                self.assertEqual(number(summary["net_profit"]), sum((number(d["profit"]) for d in closed), Fraction(0)))
                self.assertEqual(summary["winning_deals"], sum(1 for d in closed if number(d["profit"]) > 0))
                self.assertTrue(all(number(p["drawdown_percent"]) >= 0 for p in result["drawdown_curve"]))
                self.assertTrue(all(d["safety_orders_filled"] <= 6 for d in result["deals"]))
                if result["open_deal"] is None and result["status"] == "COMPLETED":
                    self.assertEqual(number(summary["final_equity"]), Fraction(1000) + number(summary["net_profit"]))
                growth = Fraction(1)
                for month in result["monthly_returns"]:
                    growth *= 1 + number(month["return_percent"]) / 100
                self.assertAlmostEqual(float(growth), float(number(summary["final_equity"]) / 1000), places=3)
            completed_runs += result["status"] == "COMPLETED"
        self.assertGreater(completed_runs, 0)

    def test_budget_too_small_for_the_venue_minimum_is_a_sector_error(self):
        from dcabot.application.sector_dca import SectorDcaError

        with self.assertRaises(SectorDcaError):
            run_sector_backtest(
                _params(base_order="3"), rules=RULES, budget=Fraction(1000), interval="1h", interval_us=HOUR, bars=_walk(10, 3), template=TEMPLATE
            )


class BacktestTradeAnalyticsTests(unittest.TestCase):
    # Q1 (Qwen): fiyat+islem-isareti grafigi ve Profit Factor icin
    # backend alanlari -- PF legacy sozlesmeyle ayni formul
    # (brut-kar/brut-zarar, zararsizsa None); giris/cikis fiyatlari
    # fill passthrough; fiyat egrisi kosulan barlarin kapanislari.
    def test_profit_factor_matches_gross_ratio_or_none(self):
        seen_none = False
        for seed in range(12):
            result = run_sector_backtest(
                _params(), rules=RULES, budget=Fraction(1000), interval="1h", interval_us=HOUR,
                bars=_walk(1500, 100 + seed), template=TEMPLATE,
            )
            closed = [deal for deal in result["deals"] if deal["closed_at_us"] is not None]
            pf = result["summary"]["profit_factor"]
            gross_win = sum((number(d["profit"]) for d in closed if number(d["profit"]) > 0), Fraction(0))
            gross_loss = sum((-number(d["profit"]) for d in closed if number(d["profit"]) < 0), Fraction(0))
            with self.subTest(seed=seed):
                if gross_loss > 0:
                    self.assertEqual(number(pf), gross_win / gross_loss)
                else:
                    seen_none = True
                    self.assertIsNone(pf)
        self.assertTrue(seen_none)

    def test_entry_exit_prices_present_and_positive(self):
        for seed in range(12):
            result = run_sector_backtest(
                _params(), rules=RULES, budget=Fraction(1000), interval="1h", interval_us=HOUR,
                bars=_walk(1500, 100 + seed), template=TEMPLATE,
            )
            with self.subTest(seed=seed):
                for deal in result["deals"]:
                    self.assertGreater(number(deal["entry_price"]), 0)
                    if deal["closed_at_us"] is not None:
                        self.assertGreater(number(deal["exit_price"]), 0)
                    else:
                        self.assertIsNone(deal["exit_price"])

    def test_price_curve_covers_processed_bars_with_venue_closes(self):
        for seed in range(12):
            bars = _walk(1500, 100 + seed)
            result = run_sector_backtest(
                _params(), rules=RULES, budget=Fraction(1000), interval="1h", interval_us=HOUR,
                bars=bars, template=TEMPLATE,
            )
            curve = result["price_curve"]
            with self.subTest(seed=seed):
                self.assertEqual(len(curve), result["processed_bar_count"])
                for point, bar in zip(curve, bars):
                    self.assertEqual(point["time_us"], bar.open_time_us)
                    self.assertEqual(point["close"], bar.close)

if __name__ == "__main__":
    unittest.main()
