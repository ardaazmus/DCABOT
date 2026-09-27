"""AA.8b (2026-09-23): GET /api/indicators/registry -- salt-okunur görünüm
over `indicator_registry.py` (Faz 17 G.4). Registry computes nothing; this
only exposes the same name list `/api/indicators/*` already dispatches
against."""
import asyncio
import json
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


class IndicatorRegistryApiTests(unittest.TestCase):
    def test_returns_the_known_indicator_names(self):
        status, body = _asgi("/api/indicators/registry")
        self.assertEqual(status, 200)
        self.assertEqual(
            set(body["data"]["indicators"]),
            {"SMA", "EMA", "MACD", "STOCH_RSI", "BOLLINGER"},
        )


if __name__ == "__main__":
    unittest.main()
