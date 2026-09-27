"""N2: telegram settings endpoints + worker tick over a fake log."""

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from api.test_v2_bots import call
from dcabot.application.credential_boundary import CredentialMaterial, EphemeralCredentialProvider
from dcabot.application.signed_request import ApiKeyType
from dcabot.data_adapters.telegram_transport import TelegramTransportError
from dcabot.persistence.notification_settings import NotificationSettings
from dcabot.server import api as api_module
from dcabot.server import v2_notifications_telegram
from dcabot.server.telegram_worker import TelegramWorker, TelegramWorkerDeps

TOKEN = "123456:ABCDEF1234567890abcdef1234567890abc"


class _FakeLog:
    def __init__(self):
        self.entries = []

    def list_after(self, seq, limit=200):
        return [e for e in self.entries if e["seq"] > seq][:limit]


class V2TelegramApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = NotificationSettings(Path(self.tmp.name) / "n.sqlite3")
        self.vault = EphemeralCredentialProvider()
        self.sent = []
        deps = v2_notifications_telegram.V2TelegramDeps(
            settings=self.settings,
            vault=self.vault,
            send_message=lambda token, chat, text: self.sent.append((token, chat, text)) or 7,
            clock_us=lambda: 0,
            problem=api_module._problem,
        )
        self.app = FastAPI()
        self.app.router.route_class = api_module.BoundedAPIRoute
        self.app.add_exception_handler(RequestValidationError, api_module.request_validation_error)
        v2_notifications_telegram.register_routes(self.app, deps)

    def tearDown(self):
        self.settings.close()
        self.tmp.cleanup()

    def test_lifecycle_configure_test_toggle_delete(self):
        status, body, _ = call(self.app, "GET", "/api/notifications/telegram")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["configured"], False)

        status, body, _ = call(
            self.app, "POST", "/api/notifications/telegram/configure",
            {"token": TOKEN, "chat_id": "987654321", "enabled": True},
        )
        self.assertEqual(status, 200, body)
        self.assertEqual(
            (body["data"]["configured"], body["data"]["enabled"], body["data"]["chat_id"]),
            (True, True, "987654321"),
        )
        self.assertNotIn(TOKEN, str(body))

        status, body, _ = call(self.app, "POST", "/api/notifications/telegram/test", {})
        self.assertEqual(status, 200, body)
        self.assertEqual(body["data"]["message_id"], 7)
        (token, chat, text), *_ = self.sent
        self.assertEqual((token, chat), (TOKEN, "987654321"))
        self.assertIn("test", text)

        status, body, _ = call(
            self.app, "POST", "/api/notifications/telegram/enabled", {"enabled": False}
        )
        self.assertEqual((status, body["data"]["enabled"]), (200, False))

        status, body, _ = call(self.app, "DELETE", "/api/notifications/telegram")
        self.assertEqual((status, body["data"]["configured"], body["data"]["enabled"]), (200, False, False))
        self.assertEqual(body["data"]["chat_id"], "987654321")

    def test_bad_token_and_test_without_config(self):
        status, body, _ = call(
            self.app, "POST", "/api/notifications/telegram/configure",
            {"token": "nope", "chat_id": "987654321"},
        )
        self.assertEqual((status, body["code"]), (422, "TELEGRAM_TOKEN_INVALID"))
        status, body, _ = call(self.app, "POST", "/api/notifications/telegram/test", {})
        self.assertEqual((status, body["code"]), (409, "TELEGRAM_NOT_CONFIGURED"))

    def test_transport_failure_is_bounded_502(self):
        def failing(token, chat, text):
            raise TelegramTransportError("TELEGRAM_UPSTREAM_UNAVAILABLE", "down")

        deps = v2_notifications_telegram.V2TelegramDeps(
            settings=self.settings,
            vault=self.vault,
            send_message=failing,
            clock_us=lambda: 0,
            problem=api_module._problem,
        )
        app = FastAPI()
        app.router.route_class = api_module.BoundedAPIRoute
        v2_notifications_telegram.register_routes(app, deps)
        call(app, "POST", "/api/notifications/telegram/configure", {"token": TOKEN, "chat_id": "1"})
        status, body, _ = call(app, "POST", "/api/notifications/telegram/test", {})
        self.assertEqual((status, body["code"]), (502, "TELEGRAM_UPSTREAM_UNAVAILABLE"))


class TelegramWorkerTests(unittest.TestCase):
    def test_tick_fans_out_and_survives_outage(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = NotificationSettings(Path(tmp) / "n.sqlite3")
            vault = EphemeralCredentialProvider()
            vault.put(
                CredentialMaterial(
                    credential_id=v2_notifications_telegram.TELEGRAM_CREDENTIAL_ID,
                    api_key=v2_notifications_telegram.TELEGRAM_API_LABEL,
                    key_type=ApiKeyType.HMAC,
                    secret=TOKEN.encode("utf-8"),
                )
            )
            settings.set_telegram_config(chat_id="987654321", enabled=True)
            log = _FakeLog()
            log.entries.append({"seq": 1, "kind": "BOT_STARTED", "ref": "bot_1", "summary": "Bot başladı.", "time_us": 0})
            sent = []
            worker = TelegramWorker(
                TelegramWorkerDeps(
                    settings=settings, vault=vault,
                    send_message=lambda token, chat, text: sent.append(text) or 1,
                    log=log, interval_seconds=3600,
                )
            )
            worker.tick()
            self.assertEqual(len(sent), 1)
            self.assertIn("Bot başladı.", sent[0])
            self.assertEqual(settings.get_telegram()["cursor_seq"], 1)
            log.entries.append({"seq": 2, "kind": "BOT_STOPPED", "ref": "bot_1", "summary": "Bot durdu.", "time_us": 0})

            def failing(token, chat, text):
                raise TelegramTransportError("TELEGRAM_UPSTREAM_UNAVAILABLE", "down")

            worker = TelegramWorker(
                TelegramWorkerDeps(
                    settings=settings, vault=vault, send_message=failing, log=log, interval_seconds=3600
                )
            )
            worker.tick()
            self.assertEqual(settings.get_telegram()["cursor_seq"], 1)
            self.assertEqual(settings.get_telegram()["last_error"], "TELEGRAM_UPSTREAM_UNAVAILABLE")
            settings.close()


class RealAppTelegramContractTests(unittest.TestCase):
    def test_routes_are_typed_and_bounded(self):
        import json

        schema = api_module.app.openapi()
        self.assertIn("$ref", json.dumps(schema["paths"]["/api/notifications/telegram"]["get"]["responses"]["200"]))
        for path in (
            "/api/notifications/telegram/configure",
            "/api/notifications/telegram/test",
            "/api/notifications/telegram/enabled",
        ):
            self.assertIn(path, api_module.ROUTE_BODY_LIMITS)


if __name__ == "__main__":
    unittest.main()
