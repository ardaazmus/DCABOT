"""Telegram notification fan-out (Faz N2): landmarks become messages.

`format_landmark` renders one event-log entry as plain human text;
`TelegramNotifier.poll_once` sends every entry after the stored cursor
and advances the cursor only past confirmed sends, so a failed send is
retried on the next poll instead of skipped. The token is loaded per
poll from the caller's loader (OS vault in production) and never
stored, logged, or echoed here.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import re

_TOKEN_PATTERN = re.compile(r"\d{1,20}:[A-Za-z0-9_-]{20,100}\Z", re.ASCII)
_CHAT_PATTERN = re.compile(r"-?\d{1,20}\Z", re.ASCII)
MAX_SUMMARY_CHARS = 500

_KIND_LABELS = {
    "BOT_CREATED": "Bot oluşturuldu",
    "BOT_STARTED": "Bot başlatıldı",
    "BOT_STOPPED": "Bot durduruldu",
    "BOT_STATUS": "Bot durumu",
    "BOT_PAUSED": "Bot duraklatıldı",
    "BOT_RESUMED": "Bot devam ettirildi",
    "BOT_ARCHIVED": "Bot arşivlendi",
    "BOT_REPLAYED": "Bot geçmişte çalıştı",
    "DEAL_OPENED": "Deal açıldı",
    "DEAL_CLOSED": "Deal kapandı",
    "DEAL_CANCELLED": "Deal iptal edildi",
    "DEAL_FUNDS_ADDED": "Deal fon eklendi",
    "SAFETY_ORDER_FILLED": "SO doldu",
    "GRID_STOPPED": "Grid durdu",
}


class TelegramNotifyError(ValueError):
    """Raised when Telegram notification input or state is unsafe."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


def validate_token(token: object) -> str:
    """Bot token shape (`<id>:<secret>`); returns it unchanged or raises."""
    if type(token) is not str or _TOKEN_PATTERN.fullmatch(token) is None:
        raise TelegramNotifyError("TELEGRAM_TOKEN_INVALID", "Bot token biçimi geçersiz.")
    return token


def validate_chat_id(chat_id: object) -> str:
    """Telegram chat id (digits, groups negative); returns it or raises."""
    if type(chat_id) is not str or _CHAT_PATTERN.fullmatch(chat_id) is None:
        raise TelegramNotifyError("TELEGRAM_CHAT_INVALID", "Chat kimliği geçersiz.")
    return chat_id


def format_landmark(kind: str, ref: str, summary: str, time_us: int) -> str:
    """Render one landmark as short plain text (no markup, no secrets)."""
    if (
        type(kind) is not str
        or not kind
        or type(ref) is not str
        or not ref
        or type(summary) is not str
        or not summary
        or type(time_us) is not int
        or time_us < 0
    ):
        raise TelegramNotifyError("TELEGRAM_LANDMARK_INVALID", "Landmark geçersiz.")
    label = _KIND_LABELS.get(kind, kind)
    moment = datetime.fromtimestamp(time_us / 1_000_000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    trimmed = summary if len(summary) <= MAX_SUMMARY_CHARS else summary[:MAX_SUMMARY_CHARS] + "…"
    return f"DCABOT · {label}\n{trimmed}\n{ref} · {moment}"


@dataclass(frozen=True)
class TelegramPollResult:
    sent: int
    last_seq: int


class TelegramNotifier:
    """Cursor-driven fan-out from an event log to one Telegram chat."""

    def __init__(self, *, send_message, load_token, settings, log) -> None:
        self._send_message = send_message
        self._load_token = load_token
        self._settings = settings
        self._log = log

    def poll_once(self, *, batch_limit: int = 20) -> TelegramPollResult:
        """Send entries after the cursor; stops (and keeps the cursor) on error."""
        if type(batch_limit) is not int or not 1 <= batch_limit <= 200:
            raise TelegramNotifyError("TELEGRAM_BATCH_INVALID", "Batch limiti 1-200 olmalıdır.")
        state = self._settings.get_telegram()
        if not state["enabled"]:
            return TelegramPollResult(sent=0, last_seq=state["cursor_seq"])
        chat_id = validate_chat_id(state["chat_id"])
        token = validate_token(self._load_token())
        cursor = state["cursor_seq"]
        sent = 0
        try:
            entries = self._log.list_after(cursor, limit=batch_limit)
        except Exception as exc:
            raise TelegramNotifyError("TELEGRAM_LOG_UNAVAILABLE", "Olay günlüğü okunamadı.") from exc
        for entry in entries:
            try:
                text = format_landmark(entry["kind"], entry["ref"], entry["summary"], entry["time_us"])
                self._send_message(token, chat_id, text)
            except Exception as exc:
                code = getattr(exc, "code", type(exc).__name__)
                self._settings.set_telegram_error(f"{code}")
                return TelegramPollResult(sent=sent, last_seq=cursor)
            cursor = int(entry["seq"])
            sent += 1
            self._settings.set_telegram_cursor(cursor)
        if sent:
            self._settings.set_telegram_error(None)
        return TelegramPollResult(sent=sent, last_seq=cursor)
