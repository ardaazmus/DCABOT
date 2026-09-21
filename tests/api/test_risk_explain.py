"""F10.8: risk explain assembly (F39)."""
import tempfile
import unittest
from pathlib import Path

from dcabot.application.bot_registry import BotRegistry, new_bot_profile
from dcabot.application.paper_trading_gate import activate_paper_session
from dcabot.server.api import _risk_explain, _validate_risk_explain_payload


class RiskExplainApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.deals_dir = Path(self.tmp.name) / "deals"
        self.registry = BotRegistry()
        self.registry.register(new_bot_profile(
            bot_id="b1", name="B", pairs=["BTCUSDT"],
            blacklist=["LUNAUSDT"], favorites=[],
            virtual_quote_budget="10",
        ))
        self.session = activate_paper_session(
            confirmed=True, session_time_us=1000, symbols=("BTCUSDT",),
            max_staleness_us=0, starting_cash="100", credential_present=False,
        )
        self.paper_store = {"sessions": {self.session.session_id: self.session}}

    def tearDown(self):
        self.tmp.cleanup()

    def test_allowed_and_active(self):
        validated, fields = _validate_risk_explain_payload({
            "session_id": self.session.session_id,
            "bot_id": "b1",
            "symbol": "BTCUSDT",
        })
        self.assertEqual(fields, {})
        result = _risk_explain(self.paper_store, self.registry, self.deals_dir, validated)
        self.assertFalse(result["blocked"])

    def test_blocked_pair(self):
        validated, fields = _validate_risk_explain_payload({
            "bot_id": "b1", "symbol": "LUNAUSDT",
        })
        self.assertEqual(fields, {})
        result = _risk_explain(self.paper_store, self.registry, self.deals_dir, validated)
        self.assertTrue(result["blocked"])
        self.assertIn("PAIR_BLOCKED", [r["code"] for r in result["reasons"]])

    def test_unknown_session(self):
        validated, fields = _validate_risk_explain_payload({"session_id": "ghost"})
        self.assertEqual(fields, {})
        result = _risk_explain(self.paper_store, self.registry, self.deals_dir, validated)
        self.assertTrue(result["blocked"])

    def test_unknown_bot_is_unknown_verdict(self):
        validated, fields = _validate_risk_explain_payload({
            "bot_id": "ghost", "symbol": "BTCUSDT",
        })
        self.assertEqual(fields, {})
        result = _risk_explain(self.paper_store, self.registry, self.deals_dir, validated)
        self.assertTrue(result["blocked"])
        self.assertIn("PAIR_UNKNOWN", [r["code"] for r in result["reasons"]])

    def test_symbol_without_bot_rejected(self):
        validated, fields = _validate_risk_explain_payload({"symbol": "BTCUSDT"})
        self.assertIsNone(validated)
        self.assertIn("bot_id", fields)


if __name__ == "__main__":
    unittest.main()
