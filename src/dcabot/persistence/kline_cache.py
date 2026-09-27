"""Local store of CLOSED venue klines (Faz W backtests, offline-first).

Only closed bars are ever written, so a cached bar never changes. A range is
served from the store only when every expected bar is present; otherwise the
caller fetches the range from the venue and upserts it. Values stay exact
decimal text exactly as the venue sent them.
"""

import sqlite3
from pathlib import Path
from threading import Lock

from dcabot.data_adapters.binance_public_transport import BinancePublicKline


class KlineCacheError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class KlineCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.db = sqlite3.connect(str(path), isolation_level=None, timeout=5, check_same_thread=False)
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS klines (
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    open_time_us INTEGER NOT NULL,
                    close_time_us INTEGER NOT NULL,
                    open TEXT NOT NULL,
                    high TEXT NOT NULL,
                    low TEXT NOT NULL,
                    close TEXT NOT NULL,
                    base_volume TEXT NOT NULL,
                    PRIMARY KEY (symbol, interval, open_time_us)
                ) WITHOUT ROWID
                """
            )
        except sqlite3.Error as exc:
            raise KlineCacheError("KLINE_CACHE_UNAVAILABLE", "Mum önbelleği açılamadı.") from exc

    def close(self) -> None:
        self.db.close()

    def get_range(
        self, symbol: str, interval: str, start_us: int, end_us: int, interval_us: int
    ) -> tuple[BinancePublicKline, ...] | None:
        """All bars with open time in [start_us, end_us), or None if any is missing."""

        expected = -(-(end_us - start_us) // interval_us)
        with self._lock:
            rows = self.db.execute(
                """
                SELECT open_time_us, close_time_us, open, high, low, close, base_volume
                FROM klines WHERE symbol = ? AND interval = ? AND open_time_us >= ? AND open_time_us < ?
                ORDER BY open_time_us
                """,
                (symbol, interval, start_us, end_us),
            ).fetchall()
        if len(rows) != expected:
            return None
        bars = tuple(BinancePublicKline(*row) for row in rows)
        for previous, current in zip(bars, bars[1:]):
            if current.open_time_us - previous.open_time_us != interval_us:
                return None
        return bars

    def put(self, symbol: str, interval: str, bars: tuple[BinancePublicKline, ...], *, now_us: int) -> None:
        closed = [bar for bar in bars if bar.close_time_us < now_us]
        with self._lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                self.db.executemany(
                    "INSERT OR REPLACE INTO klines VALUES (?,?,?,?,?,?,?,?,?)",
                    [
                        (symbol, interval, b.open_time_us, b.close_time_us, b.open, b.high, b.low, b.close, b.base_volume)
                        for b in closed
                    ],
                )
                self.db.execute("COMMIT")
            except sqlite3.Error as exc:
                self.db.execute("ROLLBACK")
                raise KlineCacheError("KLINE_CACHE_WRITE_FAILED", "Mum önbelleğine yazılamadı.") from exc
