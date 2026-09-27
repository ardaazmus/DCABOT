"""Telegram Bot API transport: sendMessage only, fail-closed.

One HTTPS POST per message; the token travels only in the request URL
(the Bot API's own convention) and never appears in errors, logs, or
responses — every failure carries a code plus a token-free detail.
"""

from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener
import json

TELEGRAM_API_BASE_URL = "https://api.telegram.org"
DEFAULT_TIMEOUT_SECONDS = 10
MAX_RESPONSE_BYTES = 8 * 1024
MAX_TEXT_CHARS = 4000


class TelegramTransportError(RuntimeError):
    """Raised when a Telegram message cannot be sent or confirmed."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


def send_telegram_message(
    token: str,
    chat_id: str,
    text: str,
    *,
    opener=None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> int:
    """Send one text message; returns the venue message id or raises."""

    if type(token) is not str or not token or any(ch.isspace() for ch in token):
        raise TelegramTransportError("TELEGRAM_TOKEN_INVALID", "Bot token geçersiz.")
    if type(chat_id) is not str or not chat_id:
        raise TelegramTransportError("TELEGRAM_CHAT_INVALID", "Chat kimliği geçersiz.")
    if type(text) is not str or not text or len(text) > MAX_TEXT_CHARS:
        raise TelegramTransportError("TELEGRAM_TEXT_INVALID", "Mesaj metni geçersiz.")
    if type(timeout_seconds) is not int or not 0 < timeout_seconds <= 60:
        raise TelegramTransportError("TELEGRAM_TIMEOUT_INVALID", "Timeout değeri geçersiz.")
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    request = Request(
        f"{TELEGRAM_API_BASE_URL}/bot{token}/sendMessage",
        data=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    active_opener = opener or build_opener()
    response = None
    try:
        response = active_opener.open(request, timeout=timeout_seconds)
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise TelegramTransportError(
            "TELEGRAM_UPSTREAM_UNAVAILABLE", "Telegram'a ulaşılamadı."
        ) from exc
    finally:
        if response is not None:
            response.close()
    if not isinstance(raw, bytes) or len(raw) > MAX_RESPONSE_BYTES:
        raise TelegramTransportError(
            "TELEGRAM_RESPONSE_INVALID", "Telegram yanıtı okunamadı."
        )
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TelegramTransportError(
            "TELEGRAM_RESPONSE_INVALID", "Telegram yanıtı JSON değil."
        ) from exc
    if not isinstance(decoded, dict) or decoded.get("ok") is not True:
        detail = decoded.get("description") if isinstance(decoded, dict) else None
        detail_text = str(detail)[:160] if isinstance(detail, str) and detail else "Telegram gönderimi reddetti."
        raise TelegramTransportError("TELEGRAM_API_REJECTED", detail_text)
    result = decoded.get("result")
    message_id = result.get("message_id") if isinstance(result, dict) else None
    if type(message_id) is not int:
        raise TelegramTransportError(
            "TELEGRAM_RESPONSE_INVALID", "Telegram message_id dönmedi."
        )
    return message_id
