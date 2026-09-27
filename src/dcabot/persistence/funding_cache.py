"""Settled funding-rate cache: immutable venue history, offline reuse.

Settled funding intervals never change, so a fetched range stays valid
forever. Unlike klines, funding has gaps that are data (a missing
interval is unknown, never zero), so coverage is tracked explicitly:
`get_range` answers only when one stored coverage row fully contains
the ask; otherwise the caller fetches the venue range and `put_range`s it.
"""

from pathlib import Path
from threading import Lock
import sqlite3

from dcabot.data_adapters.binance_futures_public_transport import BinanceFuturesFundingRate


class FundingCacheError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class FundingCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.db = sqlite3.connect(str(path), isolation_level=None, timeout=5, check_same_thread=False)
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS funding (
                    symbol TEXT NOT NULL,
                    funding_time_us INTEGER NOT NULL,
                    rate TEXT NOT NULL,
                    PRIMARY KEY (symbol, funding_time_us)
                )
                """
            )
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS funding_coverage (
                    symbol TEXT NOT NULL,
                    start_us INTEGER NOT NULL,
                    end_us INTEGER NOT NULL,
                    PRIMARY KEY (symbol, start_us, end_us)
                )
                """
            )
        except sqlite3.Error as exc:
            raise FundingCacheError("FUNDING_CACHE_UNAVAILABLE", "Funding cache açılamadı.") from exc

    def get_range(
        self, symbol: str, start_us: int, end_us: int
    ) -> tuple[BinanceFuturesFundingRate, ...] | None:
        """Records with funding time in [start_us, end_us), or None if uncovered."""
        if type(symbol) is not str or not symbol:
            raise FundingCacheError("FUNDING_CACHE_SYMBOL_INVALID", "Sembol geçersiz.")
        if (
            type(start_us) is not int
            or type(end_us) is not int
            or not 0 <= start_us < end_us
        ):
            raise FundingCacheError("FUNDING_CACHE_RANGE_INVALID", "Aralık geçersiz.")
        try:
            with self._lock:
                covered = self.db.execute(
                    """
                    SELECT 1 FROM funding_coverage
                    WHERE symbol = ? AND start_us <= ? AND end_us >= ?
                    LIMIT 1
                    """,
                    (symbol, start_us, end_us),
                ).fetchone()
                if covered is None:
                    return None
                rows = self.db.execute(
                    """
                    SELECT funding_time_us, rate FROM funding
                    WHERE symbol = ? AND funding_time_us >= ? AND funding_time_us < ?
                    ORDER BY funding_time_us
                    """,
                    (symbol, start_us, end_us),
                ).fetchall()
        except sqlite3.Error as exc:
            raise FundingCacheError("FUNDING_CACHE_UNAVAILABLE", "Funding cache okunamadı.") from exc
        return tuple(
            BinanceFuturesFundingRate(funding_time_us=time_us, rate=rate) for time_us, rate in rows
        )

    def put_range(
        self, symbol: str, records: tuple[BinanceFuturesFundingRate, ...], *, start_us: int, end_us: int
    ) -> None:
        """Store one venue fetch plus its coverage; out-of-range records rejected."""
        if type(symbol) is not str or not symbol:
            raise FundingCacheError("FUNDING_CACHE_SYMBOL_INVALID", "Sembol geçersiz.")
        if (
            type(start_us) is not int
            or type(end_us) is not int
            or not 0 <= start_us < end_us
        ):
            raise FundingCacheError("FUNDING_CACHE_RANGE_INVALID", "Aralık geçersiz.")
        if not isinstance(records, tuple):
            raise FundingCacheError("FUNDING_CACHE_RECORDS_INVALID", "Kayıtlar tuple olmalıdır.")
        for record in records:
            if not isinstance(record, BinanceFuturesFundingRate):
                raise FundingCacheError("FUNDING_CACHE_RECORDS_INVALID", "Kayıt türü geçersiz.")
            if not start_us <= record.funding_time_us < end_us:
                raise FundingCacheError(
                    "FUNDING_CACHE_RECORDS_INVALID", "Kayıt aralık dışında; yazılmadı."
                )
        try:
            with self._lock:
                self.db.execute("BEGIN IMMEDIATE")
                try:
                    self.db.executemany(
                        "INSERT OR REPLACE INTO funding VALUES (?,?,?)",
                        [(symbol, record.funding_time_us, record.rate) for record in records],
                    )
                    self.db.execute(
                        "INSERT OR REPLACE INTO funding_coverage VALUES (?,?,?)",
                        (symbol, start_us, end_us),
                    )
                    self.db.execute("COMMIT")
                except sqlite3.Error:
                    self.db.execute("ROLLBACK")
                    raise
        except sqlite3.Error as exc:
            raise FundingCacheError("FUNDING_CACHE_UNAVAILABLE", "Funding cache yazılamadı.") from exc

    def close(self) -> None:
        with self._lock:
            self.db.close()
