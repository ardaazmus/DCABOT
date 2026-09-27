"""N2: telegram fan-out — format, validation, cursor discipline."""

import tempfile
import unittest
from pathlib import Path

from dcabot.application.telegram_notify import (
    TelegramNotifier,
    TelegramNotifyError,
    format_landmark,
    validate_chat_id,
    validate_token,
)
from dcabot.persistence.notification_settings import NotificationSettings

TOKEN = "123456:ABCDEF1234567890abcdef1234567890abc"


class _FakeLog:
    def __init__(self, entries):
        self.entries = entries

    def list_after(self, seq, limit=200):
        return [e for e in self.entries if e["seq"] > seq][:limit]


def _entry(seq, kind="DEAL_CLOSED", summary="Deal 1 kapandı (TAKE_PROFIT)."):
    return {"seq": seq, "kind": kind, "ref": "bot_1:1", "summary": summary, "time_us": 1_767_225_600_000_000}


class ValidateTests(unittest.TestCase):
    def test_token_shape(self):
        self.assertEqual(validate_token(TOKEN), TOKEN)
        for bad in ("", "no-colon", "12:short", "abc:def", None, 123):
            with self.assertRaises(TelegramNotifyError, msg=bad):
                validate_token(bad)

    def test_chat_shape(self):
        self.assertEqual(validate_chat_id("987654321"), "987654321")
        self.assertEqual(validate_chat_id("-100123"), "-100123")
        for bad in ("", "abc", "12.5", None):
            with self.assertRaises(TelegramNotifyError, msg=bad):
                validate_chat_id(bad)

    def test_format_landmark(self):
        text = format_landmark("DEAL_CLOSED", "bot_1:1", "Deal kapandı.", 1_767_225_600_000_000)
        self.assertIn("DCABOT", text)
        self.assertIn("Deal kapandı.", text)
        self.assertIn("bot_1:1", text)
        self.assertIn("2026-01-01", text)
        long = format_landmark("BOT_STATUS", "b", "x" * 600, 0)
        self.assertTrue(long.endswith("…") or len(long) < 600 + 100)


class NotifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = NotificationSettings(Path(self.tmp.name) / "n.sqlite3")
        self.sent = []

    def tearDown(self):
        self.settings.close()
        self.tmp.cleanup()

    def _notifier(self, log):
        return TelegramNotifier(
            send_message=lambda token, chat, text: self.sent.append((token, chat, text)),
            load_token=lambda: TOKEN,
            settings=self.settings,
            log=log,
        )

    def test_disabled_sends_nothing(self):
        result = self._notifier(_FakeLog([_entry(1)])).poll_once()
        self.assertEqual((result.sent, self.sent), (0, []))

    def test_poll_sends_and_advances_cursor(self):
        self.settings.set_telegram_config(chat_id="987654321", enabled=True)
        result = self._notifier(_FakeLog([_entry(1), _entry(2)])).poll_once()
        self.assertEqual((result.sent, result.last_seq), (2, 2))
        self.assertEqual(len(self.sent), 2)
        self.assertEqual(self.settings.get_telegram()["cursor_seq"], 2)
        again = self._notifier(_FakeLog([_entry(1), _entry(2)])).poll_once()
        self.assertEqual(again.sent, 0)

    def test_failure_keeps_cursor_and_records_code(self):
        self.settings.set_telegram_config(chat_id="987654321", enabled=True)
        calls = []

        def flaky(token, chat, text):
            calls.append(text)
            if len(calls) == 2:
                raise RuntimeError("boom")

        notifier = TelegramNotifier(
            send_message=flaky, load_token=lambda: TOKEN, settings=self.settings,
            log=_FakeLog([_entry(1), _entry(2)]),
        )
        result = notifier.poll_once()
        self.assertEqual((result.sent, result.last_seq), (1, 1))
        self.assertEqual(self.settings.get_telegram()["cursor_seq"], 1)
        self.assertEqual(self.settings.get_telegram()["last_error"], "RuntimeError")

    def test_settings_round_trip(self):
        state = self.settings.get_telegram()
        self.assertEqual(state, {"enabled": False, "chat_id": "", "cursor_seq": 0, "last_error": None})
        self.settings.set_telegram_config(chat_id="1", enabled=True)
        self.settings.set_telegram_cursor(7)
        self.settings.set_telegram_error("TELEGRAM_UPSTREAM_UNAVAILABLE")
        state = self.settings.get_telegram()
        self.assertEqual(state["cursor_seq"], 7)
        self.assertEqual(state["last_error"], "TELEGRAM_UPSTREAM_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
