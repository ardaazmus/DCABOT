"""AA.5a-önkoşul: GET /api/config/paper -- read-only exposure of the
canonical paper.json base config, so a client can overlay its own chosen
fields instead of fabricating defaults (forbidden). Chosen design: (a)
from TASK.md's two options -- a dedicated read endpoint, not
partial+server-defaults merging inside the mutation endpoints."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest

from dcabot.domain.config import Config
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


class ConfigPaperApiTests(unittest.TestCase):
    def test_returns_a_full_config_parse_valid_dict(self):
        status, body = _asgi("/api/config/paper")
        self.assertEqual(status, 200)
        Config.parse(body["data"])  # must not raise

    def test_matches_the_on_disk_paper_json(self):
        _status, body = _asgi("/api/config/paper")
        on_disk = json.loads(api_module.CONFIG_PATH.read_text(encoding="utf-8"))
        self.assertEqual(body["data"], on_disk)

    def test_is_usable_directly_as_a_session_create_payload(self):
        _status, config_body = _asgi("/api/config/paper")
        with tempfile.TemporaryDirectory() as directory:
            original_store = api_module.TESTNET_DCA_SESSION_STORE
            api_module.TESTNET_DCA_SESSION_STORE = api_module.TestnetDcaSessionStore(
                Path(directory) / "dca-sessions.sqlite3"
            )
            try:
                payload = json.dumps(
                    {"session_id": "cfg-paper-1", "symbol": "BTCUSDT", "config": config_body["data"]}
                ).encode()
                status, body = _asgi("/api/testnet/dca-sessions", method="POST", body=payload)
                self.assertEqual(status, 200, body)
            finally:
                api_module.TESTNET_DCA_SESSION_STORE.close()
                api_module.TESTNET_DCA_SESSION_STORE = original_store


if __name__ == "__main__":
    unittest.main()
