"""Local event center: bounded in-memory landmark log (F33).

Records server-side landmarks (deal/backup/bot/paper milestones) for the
operator UI. External channels (mail/chat/push) are adapters and stay
PLAN — this module is the mandatory local channel.
"""
from collections import deque
import re
from typing import Final


_KIND = re.compile(r"[A-Z0-9_]{1,40}\Z", re.ASCII)
_MAX_LIMIT: Final = 200


class EventLogError(ValueError):
    """Raised when an event cannot be recorded or listed safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class EventLog:
    """Own one bounded newest-first landmark buffer."""

    def __init__(self, *, capacity: int = 500) -> None:
        if type(capacity) is not int or capacity < 1:
            raise EventLogError("EVENT_LOG_CAPACITY_INVALID", "Kapasite pozitif olmalıdır.")
        self._events: deque[dict[str, object]] = deque(maxlen=capacity)
        self._seq = 0

    def append(self, *, kind: str, ref: str, summary: str, time_us: int) -> int:
        """Record one landmark and return its sequence number."""
        if type(kind) is not str or _KIND.fullmatch(kind) is None:
            raise EventLogError("EVENT_KIND_INVALID", "Olay türü geçersiz.")
        if type(ref) is not str or not ref or len(ref) > 200:
            raise EventLogError("EVENT_REF_INVALID", "Olay referansı geçersiz.")
        if type(summary) is not str or not summary or len(summary) > 500:
            raise EventLogError("EVENT_SUMMARY_INVALID", "Olay özeti geçersiz.")
        if type(time_us) is not int or time_us < 0:
            raise EventLogError("EVENT_TIME_INVALID", "Olay zamanı geçersiz.")
        self._seq += 1
        self._events.append({
            "seq": self._seq,
            "kind": kind,
            "ref": ref,
            "summary": summary,
            "time_us": time_us,
        })
        return self._seq

    def list(self, *, limit: int = 50) -> list[dict[str, object]]:
        """Return landmarks newest-first, bounded by limit."""
        if type(limit) is not int or not 1 <= limit <= _MAX_LIMIT:
            raise EventLogError("EVENT_LIMIT_INVALID", "Limit 1-200 arası olmalıdır.")
        return list(reversed(list(self._events)[-limit:]))
