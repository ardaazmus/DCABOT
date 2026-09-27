"""Faz N1: notification read-state endpoints."""
import asyncio
import json
import unittest

from fastapi import FastAPI

from dcabot.application.event_log import EventLog
from dcabot.server import api as api_module


def call(app, method, path, body=None):
    payload = json.dumps(body).encode() if body is not None else b""
    messages = [{"type": "http.request", "body": payload, "more_body": False}]
    sent = []

    async def receive():
        return messages.pop(0) if messages else {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    path_only, _, query = path.partition("?")
    scope = {
        "type": "http", "method": method, "path": path_only, "raw_path": path_only.encode(),
        "query_string": query.encode(),
        "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(payload)).encode())],
        "scheme": "http", "server": ("testserver", 80), "client": ("testclient", 1),
    }
    asyncio.run(app(scope, receive, send))
    start = next(m for m in sent if m["type"] == "http.response.start")
    data = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return start["status"], json.loads(data.decode()) if data else None


class NotificationRouteTests(unittest.TestCase):
    def setUp(self):
        self.log = EventLog()
        self.app = FastAPI()
        api_module.register_notification_routes(self.app, self.log)

    def seed(self, count):
        for index in range(1, count + 1):
            self.log.append(kind="A", ref=f"r{index}", summary="s", time_us=index)

    def test_get_state_empty(self):
        status, body = call(self.app, "GET", "/api/notifications/state")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"data": {"last_seen_seq": 0, "unread_count": 0}})

    def test_state_counts_unread(self):
        self.seed(2)
        status, body = call(self.app, "GET", "/api/notifications/state")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"data": {"last_seen_seq": 0, "unread_count": 2}})

    def test_read_marks_upto(self):
        self.seed(3)
        status, body = call(self.app, "POST", "/api/notifications/read", {"upto_seq": 2})
        self.assertEqual(status, 200)
        self.assertEqual(body, {"data": {"last_seen_seq": 2, "unread_count": 1}})

    def test_read_clamps_to_current_max(self):
        self.seed(1)
        status, body = call(self.app, "POST", "/api/notifications/read", {"upto_seq": 99})
        self.assertEqual(status, 200)
        self.assertEqual(body, {"data": {"last_seen_seq": 1, "unread_count": 0}})

    def test_read_is_monotonic(self):
        self.seed(3)
        call(self.app, "POST", "/api/notifications/read", {"upto_seq": 2})
        status, body = call(self.app, "POST", "/api/notifications/read", {"upto_seq": 1})
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["last_seen_seq"], 2)

    def test_read_rejects_bad_body(self):
        cases = [
            ({"upto_seq": -1}, "upto_seq"),
            ({}, "upto_seq"),
            ({"upto_seq": "2"}, "upto_seq"),
            ({"upto_seq": True}, "upto_seq"),
            ({"upto_seq": 2.0}, "upto_seq"),
            ([1], "body"),
        ]
        for payload, field in cases:
            with self.subTest(payload=payload):
                status, body = call(self.app, "POST", "/api/notifications/read", payload)
                self.assertEqual(status, 422)
                self.assertIn(field, body["error"]["fields"])


if __name__ == "__main__":
    unittest.main()
