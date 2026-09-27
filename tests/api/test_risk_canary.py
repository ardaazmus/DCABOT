"""B.3: canary status assembly + kill-switch endpoints (16.9/17.8 binding)."""
import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dcabot.application.canary_policy import CanarySpec
from dcabot.application.canary_status import canary_status, load_canary_spec, paper_fill_count
from dcabot.application.paper_trading_gate import activate_paper_session
from dcabot.server import api as api_module


def _asgi(path, method="GET", body=None):
    messages = [{"type": "http.request", "body": body or b"", "more_body": False}]
    sent = []

    async def receive():
        return messages.pop(0)

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http", "method": method, "path": path, "raw_path": path.encode(),
        "query_string": b"", "headers": [(b"content-type", b"application/json")],
        "scheme": "http", "server": ("testserver", 80), "client": ("testclient", 1),
    }
    asyncio.run(api_module.app(scope, receive, send))
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    payload = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return status, json.loads(payload.decode())


def _spec_payload(**overrides):
    base = {
        "status": "ACTIVE",
        "amount_cap_quote": "100",
        "daily_loss_limit_quote": "10",
        "starts_at": "2026-01-01T00:00:00+00:00",
        "ends_at": "2027-01-01T00:00:00+00:00",
        "min_trades": 5,
    }
    base.update(overrides)
    return base


class CanaryStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.spec_path = self.root / "canary_spec.json"
        self.kill_path = self.root / "kill_switch.json"
        self.approval_path = self.root / "canary_approval.json"
        self.session = activate_paper_session(
            confirmed=True, session_time_us=1000, symbols=("BTCUSDT",),
            max_staleness_us=0, starting_cash="100", credential_present=False,
        )
        self.paper_store = {"sessions": {self.session.session_id: self.session}}

    def tearDown(self):
        self.tmp.cleanup()

    def _status(self, now="2026-06-01T00:00:00+00:00"):
        return canary_status(
            spec_path=self.spec_path,
            kill_switch_path=self.kill_path,
            approval_path=self.approval_path,
            paper_store=self.paper_store,
            now_iso=now,
        )

    def test_paper_fill_count_empty(self):
        self.assertEqual(paper_fill_count(self.paper_store), 0)
        self.assertEqual(paper_fill_count({}), 0)

    def test_no_spec_no_approval_is_honest_nogo(self):
        result = self._status()
        self.assertEqual(result["verdict"], "CANARY_NOGO")
        self.assertIn("SPEC_NOT_ACTIVE", result["reasons"])
        self.assertIn("CANARY_APPROVAL_MISSING", result["reasons"])
        self.assertEqual(result["spec_status"], "MISSING")
        self.assertFalse(result["kill_switch_engaged"])

    def test_corrupt_spec_is_invalid_not_active(self):
        self.spec_path.write_text("{bozuk", encoding="utf-8")
        self.assertIsNone(load_canary_spec(self.spec_path))
        self.assertEqual(self._status()["spec_status"], "INVALID")

    def test_kill_switch_file_is_real_trigger(self):
        self.kill_path.write_text(json.dumps({"engaged": True, "reason": "test"}), encoding="utf-8")
        result = self._status()
        self.assertTrue(result["kill_switch_engaged"])
        self.assertIn("KILL_SWITCH_ENGAGED", result["reasons"])

    def test_active_spec_empty_paper_runs_real_evaluation(self):
        self.spec_path.write_text(json.dumps(_spec_payload()), encoding="utf-8")
        self.assertIsInstance(load_canary_spec(self.spec_path), CanarySpec)
        result = self._status()
        self.assertEqual(result["spec_status"], "ACTIVE")
        self.assertIn("BELOW_MINIMUM_TRADES", result["reasons"])

    def test_draft_spec_never_evaluates(self):
        self.spec_path.write_text(json.dumps(_spec_payload(status="DRAFT")), encoding="utf-8")
        result = self._status()
        self.assertEqual(result["spec_status"], "DRAFT")
        self.assertIn("SPEC_NOT_ACTIVE", result["reasons"])
        self.assertNotIn("BELOW_MINIMUM_TRADES", result["reasons"])


class CanaryEndpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.patches = [
            patch.object(api_module, "KILL_SWITCH_PATH", self.root / "kill_switch.json"),
            patch.object(api_module, "CANARY_APPROVAL_PATH", self.root / "canary_approval.json"),
            patch.object(api_module, "CANARY_SPEC_PATH", self.root / "canary_spec.json"),
        ]
        for entered in self.patches:
            entered.start()

    def tearDown(self):
        for entered in self.patches:
            entered.stop()
        self.tmp.cleanup()

    def test_get_status_contract(self):
        status, body = _asgi("/api/risk/canary")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["verdict"], "CANARY_NOGO")
        self.assertIn("SPEC_NOT_ACTIVE", body["data"]["reasons"])

    def test_kill_switch_roundtrip(self):
        engage = json.dumps({"engaged": True, "reason": "b3-test"}).encode()
        status, body = _asgi("/api/risk/kill-switch", "POST", engage)
        self.assertEqual(status, 200)
        self.assertTrue(body["data"]["engaged"])
        _, status_body = _asgi("/api/risk/canary")
        self.assertTrue(status_body["data"]["kill_switch_engaged"])
        disengage = json.dumps({"engaged": False}).encode()
        status, body = _asgi("/api/risk/kill-switch", "POST", disengage)
        self.assertEqual(status, 200)
        self.assertFalse(body["data"]["engaged"])

    def test_kill_switch_engage_requires_reason(self):
        status, _ = _asgi("/api/risk/kill-switch", "POST", json.dumps({"engaged": True}).encode())
        self.assertEqual(status, 422)
        status, _ = _asgi("/api/risk/kill-switch", "POST", json.dumps({"engaged": "yes"}).encode())
        self.assertEqual(status, 422)


if __name__ == "__main__":
    unittest.main()
