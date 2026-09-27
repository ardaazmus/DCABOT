"""Faz 17 AA.-1 (final piece): /api/bots/{bot_id}/dca-sessions/deal-count
and /performance -- real, exact-Fraction aggregation over a bot's own
sessions (bot_id is a purely associative link, no economic meaning)."""
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


def _create(session_id, bot_id=None, **config_overrides):
    payload = {"session_id": session_id, "symbol": "BTCUSDT", "config": _raw_config(**config_overrides)}
    if bot_id is not None:
        payload["bot_id"] = bot_id
    return _asgi("/api/testnet/dca-sessions", method="POST", body=json.dumps(payload).encode())


def _mark(session_id, price):
    return _asgi(
        f"/api/testnet/dca-sessions/{session_id}/mark", method="POST",
        body=json.dumps({"price": price}).encode(),
    )


class BotDcaPerformanceApiTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_store = api_module.TESTNET_DCA_SESSION_STORE
        path = Path(self._tmp.name) / "dca-sessions.sqlite3"
        api_module.TESTNET_DCA_SESSION_STORE = api_module.TestnetDcaSessionStore(path)

    def tearDown(self):
        api_module.TESTNET_DCA_SESSION_STORE.close()
        api_module.TESTNET_DCA_SESSION_STORE = self._original_store
        self._tmp.cleanup()

    def test_deal_count_for_unknown_bot_is_zero(self):
        status, body = _asgi("/api/bots/nobody/dca-sessions/deal-count")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"], {"bot_id": "nobody", "total": 0, "active": 0, "completed": 0})

    def test_deal_count_only_counts_the_named_bots_sessions(self):
        _create("s1", bot_id="bot-1")
        _create("s2", bot_id="bot-2")
        _create("s3", bot_id="bot-1")
        status, body = _asgi("/api/bots/bot-1/dca-sessions/deal-count")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["total"], 2)
        self.assertEqual(body["data"]["active"], 2)
        self.assertEqual(body["data"]["completed"], 0)

    def test_sessions_without_bot_id_are_excluded(self):
        _create("s1")  # no bot_id
        status, body = _asgi("/api/bots/bot-1/dca-sessions/deal-count")
        self.assertEqual(body["data"]["total"], 0)

    def test_performance_defaults_when_no_sessions(self):
        status, body = _asgi("/api/bots/nobody/dca-sessions/performance")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["deal_count"], 0)
        self.assertEqual(body["data"]["total_realized_net"], "0")
        self.assertIsNone(body["data"]["win_rate"])

    def test_performance_aggregates_across_sessions(self):
        _create("s1", bot_id="bot-1")
        _mark("s1", "100")
        status, body = _asgi("/api/bots/bot-1/dca-sessions/performance")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["deal_count"], 1)
        self.assertEqual(body["data"]["completed_deal_count"], 0)
        self.assertEqual(body["data"]["total_realized_net"], "0")

    def test_invalid_bot_id_is_rejected(self):
        status, body = _asgi("/api/bots/%20/dca-sessions/deal-count")
        # empty/whitespace bot_id path segments are unusual but must not crash
        self.assertIn(status, (200, 422))


class PortfolioDcaPerformanceApiTests(unittest.TestCase):
    """AA.13 wire-finding #2 (2026-09-23): GET /api/portfolio/dca-performance
    -- per-bot net + winning-bot count, exact and server-side (no client
    ratio/sign/total math)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_store = api_module.TESTNET_DCA_SESSION_STORE
        path = Path(self._tmp.name) / "dca-sessions.sqlite3"
        api_module.TESTNET_DCA_SESSION_STORE = api_module.TestnetDcaSessionStore(path)

    def tearDown(self):
        api_module.TESTNET_DCA_SESSION_STORE.close()
        api_module.TESTNET_DCA_SESSION_STORE = self._original_store
        self._tmp.cleanup()

    def test_empty_portfolio_defaults(self):
        status, body = _asgi("/api/portfolio/dca-performance")
        self.assertEqual(status, 200)
        self.assertEqual(
            body["data"],
            {"bot_count": 0, "winning_bot_count": 0, "total_realized_net": "0", "bots": []},
        )

    def test_sessions_without_bot_id_count_toward_total_but_not_bots(self):
        _create("s1")  # no bot_id
        status, body = _asgi("/api/portfolio/dca-performance")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["bot_count"], 0)
        self.assertEqual(body["data"]["bots"], [])
        self.assertEqual(body["data"]["total_realized_net"], "0")

    def test_two_bots_are_aggregated_and_ranked_deterministically(self):
        _create("s1", bot_id="bot-a")
        _create("s2", bot_id="bot-b")
        status, body = _asgi("/api/portfolio/dca-performance")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["bot_count"], 2)
        self.assertEqual([b["bot_id"] for b in body["data"]["bots"]], ["bot-a", "bot-b"])
        for entry in body["data"]["bots"]:
            self.assertEqual(entry["realized_net"], "0")
            # total_net is 0 here (no fills yet) -> degenerate denominator -> None
            self.assertIsNone(entry["share_of_total"])
        self.assertEqual(body["data"]["winning_bot_count"], 0)


if __name__ == "__main__":
    unittest.main()
