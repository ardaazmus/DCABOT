"""Faz N2 telegram settings endpoints: vault-backed token, chat, test send.

`GET /api/notifications/telegram` reports non-secret status;
`POST .../configure` stores the bot token in the OS vault (never in
this repo or any response) plus the chat id in settings;
`POST .../test` sends one probe message; `POST .../enabled` toggles
fan-out; `DELETE ...` forgets the token. Registered with
`register_routes(app, deps)` directly on the app (see v2_bots for why).
"""

from dataclasses import dataclass
from threading import Lock
from typing import Annotated, Callable

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import Field

from dcabot.application.credential_boundary import CredentialMaterial
from dcabot.application.signed_request import ApiKeyType, SignedRequestError
from dcabot.application.telegram_notify import TelegramNotifyError, validate_chat_id, validate_token
from dcabot.data_adapters.telegram_transport import TelegramTransportError
from dcabot.server.v2_bots import _Strict

TELEGRAM_CREDENTIAL_ID = "dcabot.telegram-bot"
TELEGRAM_API_LABEL = "telegram-bot-token"


class TelegramConfigureRequest(_Strict):
    token: Annotated[str, Field(min_length=1, max_length=200)]
    chat_id: Annotated[str, Field(min_length=1, max_length=21, pattern=r"^-?\d+$")]
    enabled: bool = True


class TelegramEnabledRequest(_Strict):
    enabled: bool


class TelegramStatus(_Strict):
    vault: str
    configured: bool
    enabled: bool
    chat_id: str
    cursor_seq: int
    last_error: str | None


class TelegramStatusEnvelope(_Strict):
    data: TelegramStatus


class TelegramTestResult(_Strict):
    message_id: int


class TelegramTestEnvelope(_Strict):
    data: TelegramTestResult


@dataclass(frozen=True)
class V2TelegramDeps:
    settings: object
    vault: object | None
    send_message: Callable[[str, str, str], int]
    clock_us: Callable[[], int]
    problem: Callable[..., JSONResponse]


def _configured(deps: V2TelegramDeps) -> bool:
    if deps.vault is None:
        return False
    try:
        deps.vault.load(TELEGRAM_CREDENTIAL_ID)  # type: ignore[attr-defined]
    except SignedRequestError as exc:
        if exc.code == "CREDENTIAL_NOT_FOUND":
            return False
        raise
    return True


def _load_token(deps: V2TelegramDeps) -> str:
    assert deps.vault is not None
    material = deps.vault.load(TELEGRAM_CREDENTIAL_ID)  # type: ignore[attr-defined]
    return validate_token(material.secret.decode("utf-8"))


def _status_data(deps: V2TelegramDeps) -> dict:
    state = deps.settings.get_telegram()  # type: ignore[attr-defined]
    return {
        "vault": "OK" if deps.vault is not None else "UNAVAILABLE",
        "configured": _configured(deps),
        "enabled": state["enabled"],
        "chat_id": state["chat_id"],
        "cursor_seq": state["cursor_seq"],
        "last_error": state["last_error"],
    }


def register_routes(app: FastAPI, deps: V2TelegramDeps) -> None:
    lock = Lock()

    def notify_invalid(exc: TelegramNotifyError) -> JSONResponse:
        field = "token" if exc.code == "TELEGRAM_TOKEN_INVALID" else "chat_id"
        return deps.problem(422, exc.code, "Telegram ayarları geçersiz", str(exc).split(": ", 1)[-1], errors=[{"field": field, "code": exc.code}])

    @app.get("/api/notifications/telegram", tags=["v2-notifications"], response_model=TelegramStatusEnvelope)
    def telegram_status():
        """Non-secret fan-out status; the token is never exposed."""
        try:
            with lock:
                return {"data": _status_data(deps)}
        except SignedRequestError as exc:
            return deps.problem(502, exc.code, "Kasa okunamadı", str(exc).split(": ", 1)[-1])

    @app.post("/api/notifications/telegram/configure", tags=["v2-notifications"], response_model=TelegramStatusEnvelope)
    def telegram_configure(body: TelegramConfigureRequest):
        """Store the token in the OS vault and the chat id in settings."""
        if deps.vault is None:
            return deps.problem(503, "TELEGRAM_VAULT_UNAVAILABLE", "Kasa yok", "Bu platformda OS kasası kullanılamıyor.")
        try:
            token = validate_token(body.token)
            chat_id = validate_chat_id(body.chat_id)
        except TelegramNotifyError as exc:
            return notify_invalid(exc)
        try:
            with lock:
                deps.vault.put(  # type: ignore[attr-defined]
                    CredentialMaterial(
                        credential_id=TELEGRAM_CREDENTIAL_ID,
                        api_key=TELEGRAM_API_LABEL,
                        key_type=ApiKeyType.HMAC,
                        secret=token.encode("utf-8"),
                    )
                )
                deps.settings.set_telegram_config(chat_id=chat_id, enabled=body.enabled)  # type: ignore[attr-defined]
                return {"data": _status_data(deps)}
        except SignedRequestError as exc:
            return deps.problem(502, exc.code, "Kasa yazılamadı", str(exc).split(": ", 1)[-1])

    @app.post("/api/notifications/telegram/test", tags=["v2-notifications"], response_model=TelegramTestEnvelope)
    def telegram_test():
        """Send one probe message with the stored configuration."""
        if deps.vault is None:
            return deps.problem(503, "TELEGRAM_VAULT_UNAVAILABLE", "Kasa yok", "Bu platformda OS kasası kullanılamıyor.")
        try:
            with lock:
                state = deps.settings.get_telegram()  # type: ignore[attr-defined]
                if not state["chat_id"]:
                    return deps.problem(409, "TELEGRAM_NOT_CONFIGURED", "Telegram hazır değil", "Önce chat kimliği kaydedilmelidir.")
                chat_id = validate_chat_id(state["chat_id"])
                token = _load_token(deps)
        except TelegramNotifyError as exc:
            return notify_invalid(exc)
        except SignedRequestError as exc:
            code = "TELEGRAM_NOT_CONFIGURED" if exc.code == "CREDENTIAL_NOT_FOUND" else exc.code
            status = 409 if code == "TELEGRAM_NOT_CONFIGURED" else 502
            return deps.problem(status, code, "Telegram hazır değil", str(exc).split(": ", 1)[-1])
        try:
            message_id = deps.send_message(token, chat_id, "DCABOT test bildirimi: Telegram bağlı. ✓")
        except TelegramTransportError as exc:
            return deps.problem(502, exc.code, "Telegram gönderilemedi", str(exc).split(": ", 1)[-1])
        return {"data": {"message_id": message_id}}

    @app.post("/api/notifications/telegram/enabled", tags=["v2-notifications"], response_model=TelegramStatusEnvelope)
    def telegram_enabled(body: TelegramEnabledRequest):
        """Toggle fan-out without touching the stored token."""
        try:
            with lock:
                deps.settings.set_telegram_enabled(body.enabled)  # type: ignore[attr-defined]
                return {"data": _status_data(deps)}
        except SignedRequestError as exc:
            return deps.problem(502, exc.code, "Kasa okunamadı", str(exc).split(": ", 1)[-1])

    @app.delete("/api/notifications/telegram", tags=["v2-notifications"], response_model=TelegramStatusEnvelope)
    def telegram_delete():
        """Forget the token and stop fan-out; the chat id stays for reuse."""
        if deps.vault is None:
            return deps.problem(503, "TELEGRAM_VAULT_UNAVAILABLE", "Kasa yok", "Bu platformda OS kasası kullanılamıyor.")
        try:
            with lock:
                try:
                    deps.vault.delete(TELEGRAM_CREDENTIAL_ID)  # type: ignore[attr-defined]
                except SignedRequestError as exc:
                    if exc.code != "CREDENTIAL_NOT_FOUND":
                        raise
                deps.settings.set_telegram_enabled(False)  # type: ignore[attr-defined]
                return {"data": _status_data(deps)}
        except SignedRequestError as exc:
            return deps.problem(502, exc.code, "Kasa yazılamadı", str(exc).split(": ", 1)[-1])
