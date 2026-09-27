"""Paper mode (2026-09-23 design decision, docs/KARARLAR.md): the real
engine + real market data, no real order API. POST .../{id}/paper-fill --
no credential, no kill-switch, no confirmed field (no real money moves)."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest

import dcabot.server.api as api


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
    asyncio.run(api.app(scope, receive, send))
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    payload = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return status, json.loads(payload.decode())


def _raw_config(**overrides) -> dict:
    raw = json.loads((Path(__file__).resolve().parents[2] / "config/paper.json").read_text(encoding="utf-8"))
    raw.update(overrides)
    return raw


class PaperFillApiTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_store = api.TESTNET_DCA_SESSION_STORE
        path = Path(self._tmp.name) / "dca-sessions.sqlite3"
        api.TESTNET_DCA_SESSION_STORE = api.TestnetDcaSessionStore(path)
        _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps(
                {
                    "session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config(),
                    "starting_balance": "1000", "mode": "PAPER",
                }
            ).encode(),
        )
        _asgi("/api/testnet/dca-sessions/s1/mark", method="POST", body=json.dumps({"price": "100"}).encode())

    def tearDown(self):
        api.TESTNET_DCA_SESSION_STORE.close()
        api.TESTNET_DCA_SESSION_STORE = self._original_store
        self._tmp.cleanup()

    def test_paper_fill_needs_no_credential_and_no_confirmed_field(self):
        status, body = _asgi(
            "/api/testnet/dca-sessions/s1/paper-fill", method="POST",
            body=json.dumps({"role": "BASE", "qty": "1"}).encode(),
        )
        self.assertEqual(status, 200, body)
        self.assertEqual(len(body["data"]["unsettled_orders"]), 0)  # paper fills complete instantly
        self.assertEqual(body["data"]["qty"], "1")

    def test_paper_fill_updates_the_virtual_balance(self):
        status, _body = _asgi(
            "/api/testnet/dca-sessions/s1/paper-fill", method="POST",
            body=json.dumps({"role": "BASE", "qty": "1"}).encode(),
        )
        self.assertEqual(status, 200)
        status, body = _asgi("/api/testnet/dca-sessions/s1")
        self.assertEqual(status, 200)
        # Fees paid, no exit yet -> net is slightly negative -> virtual
        # balance is starting_balance + net (both exact, server-computed).
        from fractions import Fraction

        self.assertEqual(
            Fraction(body["data"]["virtual_balance"]),
            Fraction("1000") + Fraction(body["data"]["realized_net_after_all_costs"]),
        )

    def test_mismatched_role_is_409(self):
        status, body = _asgi(
            "/api/testnet/dca-sessions/s1/paper-fill", method="POST",
            body=json.dumps({"role": "SAFETY:1", "qty": "1"}).encode(),
        )
        self.assertEqual(status, 409)

    def test_missing_qty_is_422(self):
        status, body = _asgi(
            "/api/testnet/dca-sessions/s1/paper-fill", method="POST",
            body=json.dumps({"role": "BASE"}).encode(),
        )
        self.assertEqual(status, 422)
        self.assertIn("qty", body["error"]["fields"]["body"])

    def test_testnet_mode_session_rejects_paper_fill(self):
        _asgi(
            "/api/testnet/dca-sessions", method="POST",
            body=json.dumps({"session_id": "s-testnet", "symbol": "BTCUSDT", "config": _raw_config()}).encode(),
        )
        _asgi("/api/testnet/dca-sessions/s-testnet/mark", method="POST", body=json.dumps({"price": "100"}).encode())
        status, body = _asgi(
            "/api/testnet/dca-sessions/s-testnet/paper-fill", method="POST",
            body=json.dumps({"role": "BASE", "qty": "1"}).encode(),
        )
        self.assertEqual(status, 409)
        self.assertEqual(body["code"], "DCA_SESSION_MODE_MISMATCH")

    def test_unknown_session_is_404(self):
        status, body = _asgi(
            "/api/testnet/dca-sessions/ghost/paper-fill", method="POST",
            body=json.dumps({"role": "BASE", "qty": "1"}).encode(),
        )
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
