"""AA.12 (2026-09-23): GET /api/system/status -- real, local-process-only
health probe (data-dir existence, disk free/total, real backup count/
latest). No docker-compose/service-card fiction, no client-side CPU/RAM
measurement -- only what this process can actually observe about itself."""
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


class SystemStatusApiTests(unittest.TestCase):
    def test_returns_real_disk_and_data_dir_fields(self):
        status, body = _asgi("/api/system/status")
        self.assertEqual(status, 200)
        data = body["data"]
        self.assertEqual(data["status"], "ok")
        self.assertIsInstance(data["data_dir"]["exists"], bool)
        self.assertGreater(data["disk"]["total_bytes"], 0)
        self.assertGreaterEqual(data["disk"]["free_bytes"], 0)
        self.assertIsInstance(data["backups"]["count"], int)


if __name__ == "__main__":
    unittest.main()
