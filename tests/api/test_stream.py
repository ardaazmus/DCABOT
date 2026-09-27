"""Faz W-B6: SSE /api/stream — landmark replay + live + ping."""
import asyncio
import json
import threading
import time
import unittest

from fastapi import FastAPI

from dcabot.application.event_log import EventLog
from dcabot.server import api as api_module


def drive(coro):
    return asyncio.run(coro)


class DisconnectAfter:
    """Fake disconnect flag that trips after `frames` generator steps."""

    def __init__(self, frames):
        self.frames = frames

    async def __call__(self):
        if self.frames <= 0:
            return True
        self.frames -= 1
        return False


def get_status(app, path):
    messages = [{"type": "http.request", "body": b"", "more_body": False}]
    sent = []

    async def receive():
        return messages.pop(0) if messages else {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    path_only, _, query = path.partition("?")
    scope = {
        "type": "http", "method": "GET", "path": path_only, "raw_path": path_only.encode(),
        "query_string": query.encode(), "headers": [], "scheme": "http",
        "server": ("testserver", 80), "client": ("testclient", 1),
    }
    asyncio.run(app(scope, receive, send))
    start = next(m for m in sent if m["type"] == "http.response.start")
    data = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return start["status"], json.loads(data.decode()) if data else None


class StreamCursorTests(unittest.TestCase):
    def test_default_is_zero(self):
        self.assertEqual(api_module._parse_stream_cursor(None, None), 0)

    def test_query_param_is_used(self):
        self.assertEqual(api_module._parse_stream_cursor(None, "41"), 41)

    def test_header_wins_over_query_param(self):
        self.assertEqual(api_module._parse_stream_cursor("7", "41"), 7)

    def test_invalid_values_rejected(self):
        for header, param in (("abc", None), (None, "abc"), ("-1", None), (None, "-1"),
                              ("", None), (None, ""), ("1.5", None), (" 3", None)):
            with self.subTest(header=header, param=param):
                with self.assertRaises(ValueError):
                    api_module._parse_stream_cursor(header, param)


class StreamFrameTests(unittest.TestCase):
    def test_frame_layout(self):
        entry = {"seq": 7, "kind": "BOT_STARTED", "ref": "bot_1", "summary": "Bot başladı.", "time_us": 5}
        self.assertEqual(
            api_module._sse_frame(entry),
            'event: landmark\nid: 7\ndata: {"seq": 7, "kind": "BOT_STARTED", "ref": "bot_1", '
            '"summary": "Bot başladı.", "time_us": 5}\n\n',
        )

    def test_multiline_summary_is_split_into_data_lines(self):
        entry = {"seq": 1, "kind": "A", "ref": "r", "summary": "a\nb", "time_us": 1}
        frame = api_module._sse_frame(entry)
        self.assertTrue(frame.startswith("event: landmark\nid: 1\n"))
        self.assertIn('\\n', frame)
        for line in frame.split("\n"):
            self.assertTrue(line == "" or line.startswith(("event:", "id:", "data:")))


class StreamGeneratorTests(unittest.TestCase):
    def test_replay_then_disconnect(self):
        log = EventLog()
        log.append(kind="A", ref="r1", summary="s", time_us=1)
        log.append(kind="B", ref="r2", summary="s", time_us=2)

        async def collect():
            gen = api_module._stream_landmarks(log, 0, DisconnectAfter(1), ping_interval=60.0)
            hello = await gen.__anext__()
            frames = [await gen.__anext__(), await gen.__anext__()]
            with self.assertRaises(StopAsyncIteration):
                await gen.__anext__()
            return hello, frames

        hello, (first, second) = drive(collect())
        self.assertEqual(hello, ": connected\n\n")
        self.assertIn("\nid: 1\n", first)
        self.assertIn("\nid: 2\n", second)

    def test_live_append_is_pushed(self):
        log = EventLog()
        log.append(kind="A", ref="r1", summary="s", time_us=1)

        def _append_late():
            time.sleep(0.05)
            log.append(kind="B", ref="r2", summary="s", time_us=2)

        worker = threading.Thread(target=_append_late)
        worker.start()
        try:
            async def next_frame():
                gen = api_module._stream_landmarks(log, 1, DisconnectAfter(99), ping_interval=60.0)
                self.assertEqual(await gen.__anext__(), ": connected\n\n")
                return await asyncio.wait_for(gen.__anext__(), timeout=5.0)

            self.assertIn("\nid: 2\n", drive(next_frame()))
        finally:
            worker.join(timeout=10)

    def test_idle_connection_pings(self):
        log = EventLog()

        async def next_frame():
            gen = api_module._stream_landmarks(log, 0, DisconnectAfter(99), ping_interval=0.05)
            await gen.__anext__()
            return await asyncio.wait_for(gen.__anext__(), timeout=5.0)

        self.assertEqual(drive(next_frame()), ": ping\n\n")


class StreamRouteTests(unittest.TestCase):
    def test_bad_cursor_is_422(self):
        app = FastAPI()
        api_module.register_stream_route(app, api_module.EVENT_LOG)
        status, body = get_status(app, "/api/stream?last_event_id=abc")
        self.assertEqual(status, 422)
        self.assertEqual(body["error"]["fields"], {"last_event_id": "last_event_id negatif olmayan integer olmalıdır."})
