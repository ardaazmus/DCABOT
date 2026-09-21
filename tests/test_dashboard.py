"""F10.3: read-only dashboard aggregation (F28)."""
import unittest

from dcabot.application.dashboard import DashboardError, build_dashboard


class DashboardTests(unittest.TestCase):
    def test_empty_inputs_yield_zeros(self):
        result = build_dashboard(paper=[], bots=[], deals=[], backups=[])
        self.assertEqual(result["paper"]["sessions"], 0)
        self.assertEqual(result["paper"]["total_cash"], "0")
        self.assertEqual(result["bots"]["bots"], 0)
        self.assertEqual(result["deals"]["deals"], 0)
        self.assertEqual(result["backups"]["backups"], 0)

    def test_paper_cash_sums_exactly(self):
        result = build_dashboard(
            paper=[
                {"session_id": "s1", "cash": "9918.18654", "positions": [{"symbol": "BTCUSDT", "qty": "0.001"}], "orders": []},
                {"session_id": "s2", "cash": "81.81346", "positions": [], "orders": [{"status": "OPEN"}, {"status": "FILLED"}]},
            ],
            bots=[],
            deals=[],
            backups=[],
        )
        self.assertEqual(result["paper"]["sessions"], 2)
        self.assertEqual(result["paper"]["total_cash"], "10000")
        self.assertEqual(result["paper"]["positions"], 1)
        self.assertEqual(result["paper"]["open_orders"], 1)

    def test_bots_deals_backups_counted(self):
        result = build_dashboard(
            paper=[],
            bots=[
                {"bot_id": "b1", "sessions": {"s1": "BTCUSDT"}},
                {"bot_id": "b2", "sessions": {}},
            ],
            deals=[
                {"deal_id": "d1", "status": "RUNNING"},
                {"deal_id": "d2", "status": "PAUSED"},
                {"deal_id": "d3", "status": "RUNNING"},
            ],
            backups=[{"backup_file": "a.sqlite3"}, {"backup_file": "b.sqlite3"}],
        )
        self.assertEqual(result["bots"], {"bots": 2, "bound_sessions": 1})
        self.assertEqual(result["deals"], {"deals": 3, "by_status": {"RUNNING": 2, "PAUSED": 1}})
        self.assertEqual(result["backups"], {"backups": 2})

    def test_bad_cash_rejected(self):
        with self.assertRaises(DashboardError) as ctx:
            build_dashboard(
                paper=[{"session_id": "s1", "cash": "lots", "positions": [], "orders": []}],
                bots=[], deals=[], backups=[],
            )
        self.assertEqual(ctx.exception.code, "DASHBOARD_CASH_INVALID")

    def test_wrong_types_rejected(self):
        with self.assertRaises(DashboardError):
            build_dashboard(paper={}, bots=[], deals=[], backups=[])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
