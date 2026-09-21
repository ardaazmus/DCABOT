"""F10.3: dashboard route assembly (F28)."""
import tempfile
import unittest
from pathlib import Path

from dcabot.application.bot_registry import BotRegistry, new_bot_profile
from dcabot.application.paper_trading_gate import activate_paper_session
from dcabot.server.api import _dashboard_data


class DashboardApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.deals_dir = self.root / "deals"
        self.backups_dir = self.root / "backups"

    def tearDown(self):
        self.tmp.cleanup()

    def test_empty_dashboard(self):
        data = _dashboard_data(
            {"sessions": {}}, BotRegistry(), self.deals_dir, self.backups_dir
        )
        self.assertEqual(data["paper"]["sessions"], 0)
        self.assertEqual(data["paper"]["total_cash"], "0")
        self.assertEqual(data["bots"]["bots"], 0)

    def test_paper_and_bot_aggregated(self):
        session = activate_paper_session(
            confirmed=True,
            session_time_us=1000,
            symbols=("BTCUSDT",),
            max_staleness_us=0,
            starting_cash="100",
            credential_present=False,
        )
        registry = BotRegistry()
        registry.register(new_bot_profile(
            bot_id="b1", name="B", pairs=["BTCUSDT"],
            blacklist=[], favorites=[], virtual_quote_budget="10",
        ))
        registry.bind_session("b1", session.session_id, "BTCUSDT")
        data = _dashboard_data(
            {"sessions": {session.session_id: session}},
            registry, self.deals_dir, self.backups_dir,
        )
        self.assertEqual(data["paper"]["sessions"], 1)
        self.assertEqual(data["paper"]["total_cash"], "100")
        self.assertEqual(data["bots"], {"bots": 1, "bound_sessions": 1})


if __name__ == "__main__":
    unittest.main()
