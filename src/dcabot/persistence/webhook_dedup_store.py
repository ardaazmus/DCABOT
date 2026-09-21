"""Durable webhook intake store: fast-ACK receipt + dedup (Faz 13).

The endpoint records the accept row and returns 200 immediately; heavier
candidate binding happens later through an explicit bind step. The dedup
key is UNIQUE: a redelivered alert returns DUPLICATE without touching
the original receipt row.
"""
from pathlib import Path
import re
import sqlite3


APPLICATION_ID = 0x44435748
SCHEMA_VERSION = 1

_SIGNAL_ID = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
_HEX64 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)


class WebhookDedupStoreError(ValueError):
    """Raised when the webhook store cannot preserve receipt integrity."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class WebhookDedupStore:
    """Own one durable webhook intake file."""

    def __init__(self, path: Path):
        self.path = _validate_path(path)
        existed = self.path.exists()
        try:
            self.db = sqlite3.connect(
                self.path.resolve().as_uri() + "?mode=rwc",
                uri=True,
                isolation_level=None,
                timeout=5,
            )
            self.db.execute("PRAGMA foreign_keys=ON")
            if existed:
                self._validate_existing()
            else:
                self._initialize()
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
        except WebhookDedupStoreError:
            self._close_after_open_failure()
            raise
        except (OSError, sqlite3.Error) as exc:
            self._close_after_open_failure()
            raise WebhookDedupStoreError(
                "WEBHOOK_STORE_UNAVAILABLE", "Webhook store açılamadı."
            ) from exc

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "WebhookDedupStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def record_intake(
        self,
        *,
        signal_id: str,
        dedup_key: str,
        payload_hash: str,
        source: str,
        symbol: str,
        action: str,
        event_time_us: int,
        price: str | None,
        received_us: int,
    ) -> str:
        """Insert one receipt or report DUPLICATE; never rewrites history."""

        _validate_signal_id(signal_id)
        if not isinstance(dedup_key, str) or not dedup_key or len(dedup_key) > 512:
            raise WebhookDedupStoreError("WEBHOOK_DEDUP_KEY_INVALID", "Dedup key geçersiz.")
        if not isinstance(payload_hash, str) or _HEX64.fullmatch(payload_hash) is None:
            raise WebhookDedupStoreError("WEBHOOK_PAYLOAD_HASH_INVALID", "Payload hash geçersiz.")
        for name, value in (("source", source), ("symbol", symbol), ("action", action)):
            if not isinstance(value, str) or not value or len(value) > 128:
                raise WebhookDedupStoreError("WEBHOOK_INTAKE_FIELD_INVALID", f"Intake alanı geçersiz: {name}.")
        for name, value in (("event_time_us", event_time_us), ("received_us", received_us)):
            if type(value) is not int or value < 0:
                raise WebhookDedupStoreError("WEBHOOK_INTAKE_TIME_INVALID", f"Intake zamanı geçersiz: {name}.")
        if price is not None and (not isinstance(price, str) or not price or len(price) > 256):
            raise WebhookDedupStoreError("WEBHOOK_INTAKE_FIELD_INVALID", "Intake alanı geçersiz: price.")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            cursor = self.db.execute(
                "INSERT OR IGNORE INTO webhook_intakes"
                " (signal_id, dedup_key, payload_hash, source, symbol, action,"
                " event_time_us, price, received_us, status, candidate_id)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACCEPTED', NULL)",
                (signal_id, dedup_key, payload_hash, source, symbol, action,
                 event_time_us, price, received_us),
            )
            self.db.execute("COMMIT")
        except sqlite3.Error as exc:
            self.db.execute("ROLLBACK")
            raise WebhookDedupStoreError(
                "WEBHOOK_STORE_UNAVAILABLE", "Webhook intake yazılamadı."
            ) from exc
        return "ACCEPTED" if cursor.rowcount == 1 else "DUPLICATE"

    def get_intake(self, signal_id: str) -> dict[str, object] | None:
        """Return one receipt row by signal id, or None when unknown."""

        _validate_signal_id(signal_id)
        row = self.db.execute(
            "SELECT signal_id, dedup_key, payload_hash, source, symbol, action,"
            " event_time_us, price, received_us, status, candidate_id"
            " FROM webhook_intakes WHERE signal_id = ?",
            (signal_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "signal_id": row[0],
            "dedup_key": row[1],
            "payload_hash": row[2],
            "source": row[3],
            "symbol": row[4],
            "action": row[5],
            "event_time_us": row[6],
            "price": row[7],
            "received_us": row[8],
            "status": row[9],
            "candidate_id": row[10],
        }

    def list_intakes(self, *, limit: int = 50) -> list[dict[str, object]]:
        """Return receipt rows newest-first, bounded to 1-100 rows."""

        if type(limit) is not int or not 1 <= limit <= 100:
            raise WebhookDedupStoreError("WEBHOOK_LIST_LIMIT_INVALID", "Liste limiti 1-100 olmalıdır.")
        rows = self.db.execute(
            "SELECT signal_id, dedup_key, payload_hash, source, symbol, action,"
            " event_time_us, price, received_us, status, candidate_id"
            " FROM webhook_intakes ORDER BY received_us DESC, rowid DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {
                "signal_id": row[0],
                "dedup_key": row[1],
                "payload_hash": row[2],
                "source": row[3],
                "symbol": row[4],
                "action": row[5],
                "event_time_us": row[6],
                "price": row[7],
                "received_us": row[8],
                "status": row[9],
                "candidate_id": row[10],
            }
            for row in rows
        ]

    def mark_bound(self, signal_id: str, candidate_id: str) -> None:
        """Record the candidate bound to one accepted intake."""

        _validate_signal_id(signal_id)
        if not isinstance(candidate_id, str) or not candidate_id or len(candidate_id) > 128:
            raise WebhookDedupStoreError("WEBHOOK_CANDIDATE_ID_INVALID", "Candidate kimliği geçersiz.")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            cursor = self.db.execute(
                "UPDATE webhook_intakes SET status = 'BOUND', candidate_id = ?"
                " WHERE signal_id = ? AND status = 'ACCEPTED'",
                (candidate_id, signal_id),
            )
            self.db.execute("COMMIT")
        except sqlite3.Error as exc:
            self.db.execute("ROLLBACK")
            raise WebhookDedupStoreError(
                "WEBHOOK_STORE_UNAVAILABLE", "Webhook bind işareti yazılamadı."
            ) from exc
        if cursor.rowcount != 1:
            raise WebhookDedupStoreError("WEBHOOK_INTAKE_NOT_ACCEPTED", "Yalnız ACCEPTED intake bağlanabilir.")

    def _initialize(self) -> None:
        self.db.execute(f"PRAGMA application_id={APPLICATION_ID}")
        self.db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        self.db.execute(
            "CREATE TABLE webhook_intakes ("
            " signal_id TEXT PRIMARY KEY,"
            " dedup_key TEXT NOT NULL UNIQUE,"
            " payload_hash TEXT NOT NULL,"
            " source TEXT NOT NULL,"
            " symbol TEXT NOT NULL,"
            " action TEXT NOT NULL,"
            " event_time_us INTEGER NOT NULL,"
            " price TEXT,"
            " received_us INTEGER NOT NULL,"
            " status TEXT NOT NULL,"
            " candidate_id TEXT"
            ")"
        )

    def _validate_existing(self) -> None:
        app_id = self.db.execute("PRAGMA application_id").fetchone()[0]
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if app_id != APPLICATION_ID or version != SCHEMA_VERSION:
            raise WebhookDedupStoreError(
                "WEBHOOK_STORE_SCHEMA_MISMATCH", "Webhook store şeması uyumsuz."
            )

    def _close_after_open_failure(self) -> None:
        try:
            self.db.close()
        except (AttributeError, sqlite3.Error):
            pass


def _validate_path(path: Path) -> Path:
    if not isinstance(path, Path):
        raise WebhookDedupStoreError("WEBHOOK_STORE_PATH_INVALID", "Webhook store yolu geçersiz.")
    return path


def _validate_signal_id(signal_id: str) -> None:
    if not isinstance(signal_id, str) or _SIGNAL_ID.fullmatch(signal_id) is None:
        raise WebhookDedupStoreError("WEBHOOK_SIGNAL_ID_INVALID", "Signal kimliği geçersiz.")
