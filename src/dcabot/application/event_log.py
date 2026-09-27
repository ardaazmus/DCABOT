"""Local event center: bounded in-memory landmark log (F33).

Records server-side landmarks (deal/backup/bot/paper milestones) for the
operator UI. External channels (mail/chat/push) are adapters and stay
PLAN — this module is the mandatory local channel.

With `path`, entries are mirrored to SQLite (WAL): the deque stays the
read model, the database is the restart log. A storage failure at
append time degrades to RAM with a warning, never breaking the caller;
an unusable path fails fast at construction.
"""
from collections import deque
import logging
import re
import sqlite3
import threading
from pathlib import Path
from typing import Final


LOGGER = logging.getLogger(__name__)
_KIND = re.compile(r"[A-Z0-9_]{1,40}\Z", re.ASCII)
_MAX_LIMIT: Final = 200


class EventLogError(ValueError):
    """Raised when an event cannot be recorded or listed safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _validate_entry(kind: str, ref: str, summary: str, time_us: int) -> None:
    if type(kind) is not str or _KIND.fullmatch(kind) is None:
        raise EventLogError("EVENT_KIND_INVALID", "Olay türü geçersiz.")
    if type(ref) is not str or not ref or len(ref) > 200:
        raise EventLogError("EVENT_REF_INVALID", "Olay referansı geçersiz.")
    if type(summary) is not str or not summary or len(summary) > 500:
        raise EventLogError("EVENT_SUMMARY_INVALID", "Olay özeti geçersiz.")
    if type(time_us) is not int or time_us < 0:
        raise EventLogError("EVENT_TIME_INVALID", "Olay zamanı geçersiz.")


class EventLog:
    """Own one bounded newest-first landmark buffer."""

    def __init__(self, *, capacity: int = 500, path: Path | str | None = None) -> None:
        if type(capacity) is not int or capacity < 1:
            raise EventLogError("EVENT_LOG_CAPACITY_INVALID", "Kapasite pozitif olmalıdır.")
        self._capacity = capacity
        self._events: deque[dict[str, object]] = deque(maxlen=capacity)
        self._seq = 0
        self._last_seen = 0
        self._changed = threading.Condition()
        self._db: sqlite3.Connection | None = None
        if path is not None:
            self._open_store(path)

    def _open_store(self, path: Path | str) -> None:
        if not isinstance(path, (str, Path)):
            raise EventLogError("EVENT_LOG_STORE_INVALID", "Olay kaydı yolu geçersiz.")
        file_path = Path(path)
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            db = sqlite3.connect(str(file_path), isolation_level=None, timeout=5, check_same_thread=False)
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                "CREATE TABLE IF NOT EXISTS landmarks"
                " (seq INTEGER PRIMARY KEY, kind TEXT NOT NULL, ref TEXT NOT NULL,"
                " summary TEXT NOT NULL, time_us INTEGER NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value INTEGER NOT NULL)"
            )
            rows = db.execute(
                "SELECT seq, kind, ref, summary, time_us FROM landmarks ORDER BY seq DESC LIMIT ?",
                (self._capacity,),
            ).fetchall()
            db.execute(
                "DELETE FROM landmarks WHERE seq <= (SELECT MAX(seq) FROM landmarks) - ?",
                (self._capacity,),
            )
        except (sqlite3.Error, OSError) as exc:
            raise EventLogError("EVENT_LOG_STORE_INVALID", f"Olay kaydı açılamadı: {exc}") from exc
        for seq, kind, ref, summary, time_us in reversed(rows):
            self._events.append({
                "seq": seq, "kind": kind, "ref": ref, "summary": summary, "time_us": time_us,
            })
            self._seq = max(self._seq, int(seq))
        seen = db.execute("SELECT value FROM meta WHERE key = 'last_seen_seq'").fetchone()
        if seen is not None:
            self._last_seen = max(0, int(seen[0]))
        self._db = db

    @property
    def latest_seq(self) -> int:
        """Newest sequence ever assigned (0 when empty)."""
        with self._changed:
            return self._seq

    def get_last_seen(self) -> int:
        """Newest sequence the operator marked read (0 = nothing)."""
        with self._changed:
            return self._last_seen

    def set_last_seen(self, seq: int) -> int:
        """Mark everything up to `seq` read. Monotonic: never unsees."""
        if type(seq) is not int or seq < 0:
            raise EventLogError("EVENT_SEQ_INVALID", "Seq negatif olmayan integer olmalıdır.")
        with self._changed:
            self._last_seen = max(self._last_seen, seq)
            if self._db is not None:
                try:
                    self._db.execute(
                        "INSERT INTO meta (key, value) VALUES ('last_seen_seq', ?)"
                        " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                        (self._last_seen,),
                    )
                except sqlite3.Error as exc:
                    LOGGER.warning("last-seen kept in RAM only, storage write failed: %s", exc)
            return self._last_seen

    def unread_count(self) -> int:
        """Retained landmarks newer than the read mark."""
        with self._changed:
            return sum(1 for entry in self._events if int(entry["seq"]) > self._last_seen)

    def close(self) -> None:
        """Release the SQLite handle; a no-op for RAM logs. Idempotent."""
        db, self._db = self._db, None
        if db is not None:
            db.close()

    def append(self, *, kind: str, ref: str, summary: str, time_us: int) -> int:
        """Record one landmark and return its sequence number."""
        _validate_entry(kind, ref, summary, time_us)
        with self._changed:
            self._seq += 1
            if self._db is not None:
                try:
                    self._db.execute(
                        "INSERT INTO landmarks (seq, kind, ref, summary, time_us) VALUES (?, ?, ?, ?, ?)",
                        (self._seq, kind, ref, summary, time_us),
                    )
                    self._db.execute(
                        "DELETE FROM landmarks WHERE seq <= (SELECT MAX(seq) FROM landmarks) - ?",
                        (self._capacity,),
                    )
                except sqlite3.Error as exc:
                    LOGGER.warning("landmark kept in RAM only, storage write failed: %s", exc)
            self._events.append({
                "seq": self._seq,
                "kind": kind,
                "ref": ref,
                "summary": summary,
                "time_us": time_us,
            })
            self._changed.notify_all()
            return self._seq

    def list(self, *, limit: int = 50) -> list[dict[str, object]]:
        """Return landmarks newest-first, bounded by limit."""
        if type(limit) is not int or not 1 <= limit <= _MAX_LIMIT:
            raise EventLogError("EVENT_LIMIT_INVALID", "Limit 1-200 arası olmalıdır.")
        return list(reversed(list(self._events)[-limit:]))

    def list_after(self, seq: int, *, limit: int = _MAX_LIMIT) -> "list[dict[str, object]]":
        """Return landmarks after `seq`, oldest-first (stream replay).

        Entries evicted by capacity are silently skipped: the caller
        resumes from the newest id it received."""
        if type(seq) is not int or seq < 0:
            raise EventLogError("EVENT_SEQ_INVALID", "Seq negatif olmayan integer olmalıdır.")
        if type(limit) is not int or not 1 <= limit <= _MAX_LIMIT:
            raise EventLogError("EVENT_LIMIT_INVALID", "Limit 1-200 arası olmalıdır.")
        with self._changed:
            return [entry for entry in self._events if int(entry["seq"]) > seq][:limit]

    def wait_for(self, last_seq: int, *, timeout: float) -> int:
        """Block until an entry after `last_seq` exists, then return the
        current sequence (which may skip evicted entries). On timeout the
        returned sequence equals `last_seq`."""
        if type(last_seq) is not int or last_seq < 0:
            raise EventLogError("EVENT_SEQ_INVALID", "Seq negatif olmayan integer olmalıdır.")
        if type(timeout) not in (int, float) or not timeout > 0:
            raise EventLogError("EVENT_TIMEOUT_INVALID", "Timeout pozitif sayı olmalıdır.")
        with self._changed:
            if self._seq <= last_seq:
                self._changed.wait(timeout=float(timeout))
            return self._seq
