"""Faz 17 AA.-1 (testnet-session dilimi, adım 2): read-only DCA session HTTP
surface. Order placement/fill-sync are deliberately NOT wired here yet
(docs/KARARLAR.md, 2026-09-23) -- only create/list/get/mark/decision."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest

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


def _raw_config(**overrides) -> dict:
    raw = json.loads((Path(__file__).resolve().parents[2] / "config/paper.json").read_text(encoding="utf-8"))
    raw.update(overrides)
    return raw


class TestnetDcaSessionApiTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_path = api_module.TESTNET_DCA_SESSIONS_PATH
        self._original_store = api_module.TESTNET_DCA_SESSION_STORE
        path = Path(self._tmp.name) / "dca-sessions.sqlite3"
        api_module.TESTNET_DCA_SESSIONS_PATH = path
        api_module.TESTNET_DCA_SESSION_STORE = api_module.TestnetDcaSessionStore(path)

    def tearDown(self):
        api_module.TESTNET_DCA_SESSION_STORE.close()
        api_module.TESTNET_DCA_SESSION_STORE = self._original_store
        api_module.TESTNET_DCA_SESSIONS_PATH = self._original_path
        self._tmp.cleanup()

    def test_create_then_get_round_trips(self):
        status, body = _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps(
                {"session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config()}
            ).encode(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["session_id"], "s1")
        self.assertEqual(body["data"]["symbol"], "BTCUSDT")

        status, body = _asgi("/api/testnet/dca-sessions/s1")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["session_id"], "s1")

    def test_mode_defaults_to_testnet_and_round_trips_explicit_paper(self):
        status, body = _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps({"session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config()}).encode(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["mode"], "TESTNET")

        status, body = _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps(
                {"session_id": "s2", "symbol": "BTCUSDT", "config": _raw_config(), "mode": "PAPER"}
            ).encode(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["mode"], "PAPER")
        status, body = _asgi("/api/testnet/dca-sessions/s2")
        self.assertEqual(body["data"]["mode"], "PAPER")

    def test_unknown_mode_is_422(self):
        status, body = _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps(
                {"session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config(), "mode": "LIVE"}
            ).encode(),
        )
        self.assertEqual(status, 422)
        self.assertIn("mode", body["error"]["fields"])

    def test_starting_balance_round_trips_and_virtual_balance_starts_equal(self):
        status, body = _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps(
                {"session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config(), "starting_balance": "1000"}
            ).encode(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["starting_balance"], "1000")
        # No fills yet -> net is 0 -> virtual balance equals the starting anchor.
        self.assertEqual(body["data"]["virtual_balance"], "1000")

        status, body = _asgi("/api/testnet/dca-sessions/s1")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["starting_balance"], "1000")

    def test_omitted_starting_balance_is_null_everywhere(self):
        _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps({"session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config()}).encode(),
        )
        status, body = _asgi("/api/testnet/dca-sessions/s1")
        self.assertEqual(status, 200)
        self.assertIsNone(body["data"]["starting_balance"])
        self.assertIsNone(body["data"]["virtual_balance"])

    def test_non_positive_starting_balance_is_422(self):
        status, body = _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps(
                {"session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config(), "starting_balance": "0"}
            ).encode(),
        )
        self.assertEqual(status, 422)
        self.assertIn("starting_balance", body["error"]["fields"])

    def test_duplicate_create_is_409(self):
        payload = json.dumps(
            {"session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config()}
        ).encode()
        _asgi("/api/testnet/dca-sessions", method="POST", body=payload)
        status, body = _asgi("/api/testnet/dca-sessions", method="POST", body=payload)
        self.assertEqual(status, 409)
        self.assertIn("DCA_SESSION_ALREADY_EXISTS", body["error"]["fields"]["session"])

    def test_get_unknown_session_is_404(self):
        status, body = _asgi("/api/testnet/dca-sessions/ghost")
        self.assertEqual(status, 404)
        self.assertIn("DCA_SESSION_NOT_FOUND", body["error"]["fields"]["session"])

    def test_list_returns_created_sessions(self):
        _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps({"session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config()}).encode(),
        )
        _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps({"session_id": "s2", "symbol": "ETHUSDT", "config": _raw_config(symbol="ETHUSDT", base_asset="ETH")}).encode(),
        )
        status, body = _asgi("/api/testnet/dca-sessions")
        self.assertEqual(status, 200)
        self.assertEqual([row["session_id"] for row in body["data"]], ["s1", "s2"])

    def test_mark_updates_and_persists(self):
        _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps({"session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config()}).encode(),
        )
        status, body = _asgi(
            "/api/testnet/dca-sessions/s1/mark", method="POST",
            body=json.dumps({"price": "100"}).encode(),
        )
        self.assertEqual(status, 200)
        # report() text-encodes mark implicitly via unrealized/equity fields;
        # re-fetch to confirm durability across a fresh load.
        status, body = _asgi("/api/testnet/dca-sessions/s1")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["equity"], "1000")

    def test_decision_proposes_base_after_mark(self):
        _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps({"session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config()}).encode(),
        )
        _asgi(
            "/api/testnet/dca-sessions/s1/mark", method="POST",
            body=json.dumps({"price": "100"}).encode(),
        )
        status, body = _asgi("/api/testnet/dca-sessions/s1/decision")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["role"], "BASE")

    def test_decision_includes_preview_limit_price_and_notional_for_base(self):
        _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps({"session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config()}).encode(),
        )
        _asgi(
            "/api/testnet/dca-sessions/s1/mark", method="POST",
            body=json.dumps({"price": "100"}).encode(),
        )
        status, body = _asgi("/api/testnet/dca-sessions/s1/decision")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["role"], "BASE")
        # BASE prices at the current mark; notional = qty * mark.
        self.assertEqual(body["data"]["limit_price"], "100")
        from fractions import Fraction

        self.assertEqual(
            Fraction(body["data"]["notional"]), Fraction(body["data"]["qty"]) * Fraction(100)
        )

    def test_decision_is_none_before_any_mark(self):
        _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps({"session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config()}).encode(),
        )
        status, body = _asgi("/api/testnet/dca-sessions/s1/decision")
        self.assertEqual(status, 200)
        self.assertIsNone(body["data"])

    def test_invalid_config_on_create_is_422(self):
        bad = _raw_config()
        bad["margin_mode"] = "BAD"
        status, body = _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps({"session_id": "s1", "symbol": "BTCUSDT", "config": bad}).encode(),
        )
        self.assertEqual(status, 422)


if __name__ == "__main__":
    unittest.main()
