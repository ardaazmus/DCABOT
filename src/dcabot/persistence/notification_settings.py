"""Notification settings store: Telegram chat + cursor, never the token.

The bot token lives only in the OS credential vault; this SQLite table
holds the non-secret half (enabled flag, chat id, fan-out cursor, last
error code) so status stays readable without touching the vault.
"""

from pathlib import Path
from threading import RLock
import functools
import sqlite3


class NotificationSettingsError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _locked(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)

    return wrapper


_DEFAULTS = {
    "telegram_enabled": "0",
    "telegram_chat_id": "",
    "telegram_cursor_seq": "0",
    "telegram_last_error": "",
}


class NotificationSettings:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = RLock()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.db = sqlite3.connect(str(path), isolation_level=None, timeout=5, check_same_thread=False)
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            self.db.executemany(
                "INSERT OR IGNORE INTO settings VALUES (?,?)", list(_DEFAULTS.items())
            )
        except sqlite3.Error as exc:
            raise NotificationSettingsError("NOTIFICATION_SETTINGS_UNAVAILABLE", "Bildirim ayarları açılamadı.") from exc

    def close(self) -> None:
        self.db.close()

    @_locked
    def _get(self, key: str) -> str:
        try:
            row = self.db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        except sqlite3.Error as exc:
            raise NotificationSettingsError("NOTIFICATION_SETTINGS_UNAVAILABLE", "Bildirim ayarları okunamadı.") from exc
        if row is None:
            raise NotificationSettingsError("NOTIFICATION_SETTING_UNKNOWN", "Ayar bulunamadı.")
        return row[0]

    @_locked
    def _put(self, key: str, value: str) -> None:
        if key not in _DEFAULTS or type(value) is not str:
            raise NotificationSettingsError("NOTIFICATION_SETTING_INVALID", "Ayar geçersiz.")
        try:
            self.db.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, value))
        except sqlite3.Error as exc:
            raise NotificationSettingsError("NOTIFICATION_SETTINGS_UNAVAILABLE", "Bildirim ayarları yazılamadı.") from exc

    def get_telegram(self) -> dict[str, object]:
        """Non-secret Telegram state; cursor is an int, error None when clear."""
        enabled = self._get("telegram_enabled") == "1"
        try:
            cursor = int(self._get("telegram_cursor_seq"))
        except ValueError as exc:
            raise NotificationSettingsError("NOTIFICATION_SETTING_INVALID", "Cursor geçersiz.") from exc
        if cursor < 0:
            raise NotificationSettingsError("NOTIFICATION_SETTING_INVALID", "Cursor geçersiz.")
        error = self._get("telegram_last_error") or None
        return {
            "enabled": enabled,
            "chat_id": self._get("telegram_chat_id"),
            "cursor_seq": cursor,
            "last_error": error,
        }

    def set_telegram_config(self, *, chat_id: str, enabled: bool) -> None:
        if type(chat_id) is not str or type(enabled) is not bool:
            raise NotificationSettingsError("NOTIFICATION_SETTING_INVALID", "Ayar geçersiz.")
        self._put("telegram_chat_id", chat_id)
        self._put("telegram_enabled", "1" if enabled else "0")
        self._put("telegram_last_error", "")

    def set_telegram_enabled(self, enabled: bool) -> None:
        if type(enabled) is not bool:
            raise NotificationSettingsError("NOTIFICATION_SETTING_INVALID", "Ayar geçersiz.")
        self._put("telegram_enabled", "1" if enabled else "0")

    def set_telegram_cursor(self, seq: int) -> None:
        if type(seq) is not int or seq < 0:
            raise NotificationSettingsError("NOTIFICATION_SETTING_INVALID", "Cursor geçersiz.")
        self._put("telegram_cursor_seq", str(seq))

    def set_telegram_error(self, code: str | None) -> None:
        if code is not None and (type(code) is not str or not code or len(code) > 64):
            raise NotificationSettingsError("NOTIFICATION_SETTING_INVALID", "Hata kodu geçersiz.")
        self._put("telegram_last_error", code or "")
