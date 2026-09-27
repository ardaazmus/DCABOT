"""N2: telegram transport — bounded sendMessage, token never in errors."""

import json
import unittest
import urllib.error

from dcabot.data_adapters.telegram_transport import (
    TelegramTransportError,
    send_telegram_message,
)


class _FakeResponse:
    def __init__(self, body, headers=None):
        self._body = body
        self.headers = headers or {}
        self.closed = False

    def read(self, size=-1):
        data = self._body[:size] if size is not None and size >= 0 else self._body
        self._body = self._body[len(data):]
        return data

    def close(self):
        self.closed = True


class _FakeOpener:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.requests = []

    def open(self, request, timeout):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.response


TOKEN = "123456:ABCDEF1234567890abcdef1234567890abc"
CHAT = "987654321"


def _opener(payload, status=200):
    return _FakeOpener(_FakeResponse(json.dumps(payload).encode("utf-8")))


class SendTelegramMessageTests(unittest.TestCase):
    def test_ok_returns_message_id_and_posts_shape(self):
        opener = _opener({"ok": True, "result": {"message_id": 42}})
        message_id = send_telegram_message(TOKEN, CHAT, "hello", opener=opener)
        self.assertEqual(message_id, 42)
        (request,) = opener.requests
        self.assertEqual(request.full_url, f"https://api.telegram.org/bot{TOKEN}/sendMessage")
        self.assertEqual(json.loads(request.data.decode("utf-8")), {"chat_id": CHAT, "text": "hello"})
        self.assertEqual(request.get_method(), "POST")

    def test_api_rejection_is_bounded_and_token_free(self):
        opener = _opener({"ok": False, "description": "Forbidden: bot was blocked"})
        with self.assertRaises(TelegramTransportError) as ctx:
            send_telegram_message(TOKEN, CHAT, "hello", opener=opener)
        self.assertEqual(ctx.exception.code, "TELEGRAM_API_REJECTED")
        self.assertNotIn(TOKEN, str(ctx.exception))
        self.assertIn("blocked", str(ctx.exception))

    def test_network_failure_maps_unavailable(self):
        opener = _FakeOpener(error=urllib.error.URLError("down"))
        with self.assertRaises(TelegramTransportError) as ctx:
            send_telegram_message(TOKEN, CHAT, "hello", opener=opener)
        self.assertEqual(ctx.exception.code, "TELEGRAM_UPSTREAM_UNAVAILABLE")
        self.assertNotIn(TOKEN, str(ctx.exception))

    def test_bad_inputs_rejected_before_request(self):
        opener = _FakeOpener()
        for token, chat, text, code in (
            ("", CHAT, "hi", "TELEGRAM_TOKEN_INVALID"),
            ("has space:abc", CHAT, "hi", "TELEGRAM_TOKEN_INVALID"),
            (TOKEN, "", "hi", "TELEGRAM_CHAT_INVALID"),
            (TOKEN, CHAT, "", "TELEGRAM_TEXT_INVALID"),
            (TOKEN, CHAT, "x" * 4001, "TELEGRAM_TEXT_INVALID"),
        ):
            with self.subTest(code=code):
                with self.assertRaises(TelegramTransportError) as ctx:
                    send_telegram_message(token, chat, text, opener=opener)
                self.assertEqual(ctx.exception.code, code)
        self.assertEqual(opener.requests, [])


if __name__ == "__main__":
    unittest.main()
