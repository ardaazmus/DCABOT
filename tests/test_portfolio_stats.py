"""Faz W-B5: portfoy istatistikleri -- ozet/equity/gunluk/bot/parite.

Tum para hesabi exact Fraction; oranlarin bitmeyen ondaliklari yalniz
`text()` ile gosterimde yuvarlanir. Arsivli botlar her yerden dislanir.

Kurgu (gun=3 ogle): A (RUNNING, 1000): +10.5 (gun1), -2.25 (bugun);
B (RUNNING, 500): acik deal, uPnL +10; C (STOPPED, 2000): issiz;
D (arsivli): sayilmaz. Ozsermaye 3518.25, bugun -2.25, aktif 2.
"""
import json
import tempfile
import unittest
from fractions import Fraction as Q
from pathlib import Path

from dcabot.application.sector_dca import SymbolRules, derive_deal_config, parse_sector_dca
from dcabot.domain.engine import State
from dcabot.domain.math import Position
from dcabot.persistence.bot_store import BotDeal, BotRecord, BotRuntime, BotStore

ROOT = Path(__file__).resolve().parents[1]
RULES = SymbolRules("BTCUSDT", "TRADING", "BTC", "USDT", "0.01", "0.001", "0.001", "5")
TEMPLATE = json.loads((ROOT / "config" / "paper.json").read_text(encoding="utf-8"))
DAY = 86_400_000_000
NOW = 3 * DAY + 12 * 3_600_000_000


def _record(bot_id, name, symbol, budget, status, archived=None):
    return BotRecord(bot_id, name, "DCA", "PAPER", symbol, {}, budget, status, None, 1, 0, 0, archived)


def _runtime(bot_id):
    params = parse_sector_dca(dict(
        symbol="BTCUSDT", base_order="25", safety_order="25", max_safety_orders=2,
        max_active_safety_orders=None, price_deviation="1.5", safety_order_volume_scale="1.5",
        safety_order_step_scale="1.2", take_profit="2", stop_loss=None,
    ))
    raw = derive_deal_config(params, rules=RULES, reference_price=Q(100), budget=Q(500), template=TEMPLATE)
    state = State(position=Position(Q(1), Q(100)), anchor=Q(100), mark=Q(110))
    return BotRuntime(bot_id, raw, state, 1, Q(0), NOW - 60_000_000, NOW)


def _fixture():
    records = (
        _record("a", "A", "BTCUSDT", "1000", "RUNNING"),
        _record("b", "B", "ETHUSDT", "500", "RUNNING"),
        _record("c", "C", "BTCUSDT", "2000", "STOPPED"),
        _record("d", "D", "BTCUSDT", "9999", "RUNNING", archived=1),
    )
    deals = {
        "a": (
            BotDeal("a", 1, DAY, DAY + 100, 0, "10.5", "TAKE_PROFIT"),
            BotDeal("a", 2, 3 * DAY, 3 * DAY + 100, 1, "-2.25", "STOP_LOSS"),
            BotDeal("a", 3, 3 * DAY + 200, None, 0, None, None),
        ),
        "b": (BotDeal("b", 1, 3 * DAY, None, 0, None, None),),
        "d": (BotDeal("d", 1, DAY, DAY + 50, 0, "100", "TAKE_PROFIT"),),
    }
    return records, deals, {"b": _runtime("b")}


class PortfolioEquityTests(unittest.TestCase):
    def test_equity_sums_budget_realized_and_unrealized(self):
        from dcabot.application.portfolio_stats import portfolio_equity

        records, deals, runtimes = _fixture()
        result = portfolio_equity(records, deals, runtimes)
        self.assertEqual(result, {"equity": "3518.25", "realized": "8.25", "unrealized": "10"})

    def test_archived_bots_excluded(self):
        from dcabot.application.portfolio_stats import portfolio_equity

        records, deals, runtimes = _fixture()
        result = portfolio_equity(records, deals, runtimes)
        # D'nin +100'u toplama girmemistir.
        self.assertEqual(result["realized"], "8.25")

    def test_empty_portfolio_is_zero(self):
        from dcabot.application.portfolio_stats import portfolio_equity

        self.assertEqual(
            portfolio_equity((), {}, {}), {"equity": "0", "realized": "0", "unrealized": "0"}
        )


class PortfolioSummaryTests(unittest.TestCase):
    def test_summary_fields(self):
        from dcabot.application.portfolio_stats import portfolio_summary

        records, deals, runtimes = _fixture()
        result = portfolio_summary(records, deals, runtimes, NOW)
        self.assertEqual(
            result,
            {
                "total_value": "3518.25",
                "today_profit": "-2.25",
                "active_bots": 2,
                "deployed_capital": "1500",
            },
        )


class DailyProfitTests(unittest.TestCase):
    def test_daily_buckets_zero_filled_ascending(self):
        from dcabot.application.portfolio_stats import daily_profit

        records, deals, _ = _fixture()
        all_deals = tuple(deal for bot_deals in deals.values() for deal in bot_deals if deal.bot_id != "d")
        result = daily_profit(all_deals, 3, NOW)
        self.assertEqual(
            result,
            [
                {"day_start_us": DAY, "profit": "10.5"},
                {"day_start_us": 2 * DAY, "profit": "0"},
                {"day_start_us": 3 * DAY, "profit": "-2.25"},
            ],
        )


class ProfitSplitTests(unittest.TestCase):
    def test_by_bot_created_order(self):
        from dcabot.application.portfolio_stats import profit_by_bot

        records, deals, _ = _fixture()
        result = profit_by_bot(records, deals)
        self.assertEqual(
            result,
            [
                {"bot_id": "a", "bot_name": "A", "profit": "8.25", "deals_completed": 2},
                {"bot_id": "b", "bot_name": "B", "profit": "0", "deals_completed": 0},
                {"bot_id": "c", "bot_name": "C", "profit": "0", "deals_completed": 0},
            ],
        )

    def test_by_pair_symbol_order(self):
        from dcabot.application.portfolio_stats import profit_by_pair

        records, deals, _ = _fixture()
        result = profit_by_pair(records, deals)
        self.assertEqual(
            result,
            [
                {"symbol": "BTCUSDT", "profit": "8.25", "deals_completed": 2, "bots": 2},
                {"symbol": "ETHUSDT", "profit": "0", "deals_completed": 0, "bots": 1},
            ],
        )


class SnapshotStoreTests(unittest.TestCase):
    def test_save_latest_list_and_prune(self):
        from dcabot.application.portfolio_stats import SNAPSHOT_RETENTION_US

        tmp = tempfile.TemporaryDirectory()
        try:
            store = BotStore(Path(tmp.name) / "bots.sqlite3")
            try:
                self.assertIsNone(store.latest_portfolio_snapshot_time())
                store.save_portfolio_snapshot(100, "1", "1", "0")
                store.save_portfolio_snapshot(200, "2", "2", "0")
                store.save_portfolio_snapshot(300, "3", "2", "1")
                self.assertEqual(store.latest_portfolio_snapshot_time(), 300)
                rows = store.list_portfolio_snapshots(since_us=200)
                self.assertEqual(
                    rows,
                    (
                        {"time_us": 200, "equity": "2", "realized": "2", "unrealized": "0"},
                        {"time_us": 300, "equity": "3", "realized": "2", "unrealized": "1"},
                    ),
                )
                store.prune_portfolio_snapshots(before_us=300)
                self.assertEqual([row["time_us"] for row in store.list_portfolio_snapshots()], [300])
                self.assertGreater(SNAPSHOT_RETENTION_US, 0)
            finally:
                store.close()
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
