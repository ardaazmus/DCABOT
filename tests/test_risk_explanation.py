"""F10.8: read-only why-no-trade explanation (F39)."""
import unittest

from dcabot.application.risk_explanation import explain_risk


class RiskExplanationTests(unittest.TestCase):
    def test_all_clear(self):
        result = explain_risk(
            pair_verdict=("ALLOWED", "serbest"),
            paper={"session_id": "s1", "status": "ACTIVE", "cash": "100"},
            deal={"deal_id": "d1", "status": "RUNNING"},
        )
        self.assertFalse(result["blocked"])
        self.assertTrue(all(r["severity"] == "INFO" for r in result["reasons"]))

    def test_blocked_pair_is_blocker(self):
        result = explain_risk(pair_verdict=("BLOCKED_BLACKLIST", "blacklistte"))
        self.assertTrue(result["blocked"])
        codes = [r["code"] for r in result["reasons"]]
        self.assertIn("PAIR_BLOCKED", codes)

    def test_out_of_scope_is_blocker(self):
        result = explain_risk(pair_verdict=("NOT_IN_SCOPE", "kapsam dışı"))
        self.assertTrue(result["blocked"])
        self.assertIn("PAIR_OUT_OF_SCOPE", [r["code"] for r in result["reasons"]])

    def test_unknown_session_is_blocker(self):
        result = explain_risk(paper=None, paper_requested=True)
        self.assertTrue(result["blocked"])
        self.assertIn("SESSION_UNKNOWN", [r["code"] for r in result["reasons"]])

    def test_terminal_deal_warns(self):
        result = explain_risk(deal={"deal_id": "d1", "status": "COMPLETED"})
        self.assertFalse(result["blocked"])
        codes = [r["code"] for r in result["reasons"]]
        self.assertIn("DEAL_TERMINAL", codes)

    def test_empty_request_yields_guidance(self):
        result = explain_risk()
        self.assertFalse(result["blocked"])
        self.assertEqual(result["reasons"][0]["code"], "NO_INPUT")

    def test_reasons_carry_human_messages(self):
        result = explain_risk(pair_verdict=("BLOCKED_BLACKLIST", "blacklistte"))
        for reason in result["reasons"]:
            self.assertTrue(reason["message"])
            self.assertIn(reason["severity"], ("INFO", "WARNING", "BLOCKER"))


if __name__ == "__main__":
    unittest.main()
