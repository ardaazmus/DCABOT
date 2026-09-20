"""Durable offline replay for the conditional trigger/execution projection."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3

from dcabot.application.conditional_execution import (
    ConditionalExecution,
    ConditionalExecutionOutcome,
    ConditionalStatus,
)


APPLICATION_ID = 0x44434553
SCHEMA_VERSION = 1


class ConditionalExecutionStoreError(ValueError):
    """Raised when the durable conditional projection cannot be trusted."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class ConditionalExecutionStore:
    """Own one bounded conditional projection without economic authority."""

    path: Path
    db: sqlite3.Connection

    @classmethod
    def create(cls, path: Path, execution: ConditionalExecution) -> "ConditionalExecutionStore":
        validated = _validate_path(path)
        if validated.exists():
            raise ConditionalExecutionStoreError("CONDITIONAL_STORE_EXISTS", "Conditional store üzerine yazılamaz.")
        _validate_execution(execution)
        try:
            with validated.open("xb"):
                pass
            db = _connect(validated)
            store = cls(validated, db)
            store._initialize(execution)
            return store
        except ConditionalExecutionStoreError:
            if "db" in locals():
                db.close()
            raise
        except (OSError, sqlite3.Error) as exc:
            if "db" in locals():
                db.close()
            raise ConditionalExecutionStoreError("CONDITIONAL_STORE_UNAVAILABLE", "Conditional store açılamadı.") from exc

    @classmethod
    def open(cls, path: Path) -> "ConditionalExecutionStore":
        validated = _validate_path(path)
        if not validated.is_file():
            raise ConditionalExecutionStoreError("CONDITIONAL_STORE_MISSING", "Conditional store bulunamadı.")
        try:
            db = _connect(validated)
            if (
                db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
                or db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION
            ):
                raise ConditionalExecutionStoreError("CONDITIONAL_STORE_UNSUPPORTED", "Conditional store şeması desteklenmiyor.")
            metadata = dict(db.execute("SELECT key, value FROM metadata"))
            if metadata.get("store") != "offline-conditional-execution-1" or metadata.get(
                "scope"
            ) != "DURABLE_CONDITIONAL_TRIGGER_EXECUTION":
                raise ConditionalExecutionStoreError("CONDITIONAL_STORE_METADATA_INVALID", "Conditional store metadata geçersiz.")
            store = cls(validated, db)
            store._load_unlocked()
            return store
        except ConditionalExecutionStoreError:
            if "db" in locals():
                db.close()
            raise
        except (OSError, sqlite3.Error) as exc:
            if "db" in locals():
                db.close()
            raise ConditionalExecutionStoreError("CONDITIONAL_STORE_UNAVAILABLE", "Conditional store açılamadı.") from exc

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "ConditionalExecutionStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def save(self, execution: ConditionalExecution) -> ConditionalExecutionOutcome:
        """Atomically save one valid conditional successor or return duplicate."""

        _validate_execution(execution)
        payload = _canonical(_execution_payload(execution))
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT state_payload, state_hash FROM conditional_execution_state WHERE conditional_order_id=?",
                (execution.conditional_order_id,),
            ).fetchone()
            if row is None:
                raise ConditionalExecutionStoreError("CONDITIONAL_STORE_STATE_MISSING", "Conditional başlangıç state’i bulunamadı.")
            prior = _decode_checked(row[0], row[1])
            _validate_successor(prior, execution)
            if prior == execution:
                self.db.execute("COMMIT")
                return ConditionalExecutionOutcome.DUPLICATE
            self.db.execute(
                "UPDATE conditional_execution_state SET state_payload=?, state_hash=? WHERE conditional_order_id=?",
                (payload, _digest(payload), execution.conditional_order_id),
            )
            self.db.execute("COMMIT")
            return ConditionalExecutionOutcome.ACCEPTED
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def load(self) -> ConditionalExecution:
        """Replay the conditional projection without creating an economic event."""

        self.db.execute("BEGIN")
        try:
            result = self._load_unlocked()
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _initialize(self, execution: ConditionalExecution) -> None:
        payload = _canonical(_execution_payload(execution))
        self.db.executescript(
            f"""
            BEGIN IMMEDIATE;
            PRAGMA application_id={APPLICATION_ID};
            PRAGMA user_version={SCHEMA_VERSION};
            CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE conditional_execution_state(
                conditional_order_id TEXT PRIMARY KEY,
                state_payload TEXT NOT NULL,
                state_hash TEXT NOT NULL
            );
            INSERT INTO metadata(key, value) VALUES
                ('store', 'offline-conditional-execution-1'),
                ('scope', 'DURABLE_CONDITIONAL_TRIGGER_EXECUTION');
            INSERT INTO conditional_execution_state VALUES
                ('{_sql_text(execution.conditional_order_id)}', '{_sql_text(payload)}', '{_digest(payload)}');
            COMMIT;
            """
        )

    def _load_unlocked(self) -> ConditionalExecution:
        rows = self.db.execute(
            "SELECT state_payload, state_hash FROM conditional_execution_state"
        ).fetchall()
        if len(rows) != 1:
            raise ConditionalExecutionStoreError("CONDITIONAL_STORE_STATE_INVALID", "Tek conditional state kaydı bekleniyordu.")
        return _decode_checked(rows[0][0], rows[0][1])


def _validate_execution(execution: object) -> None:
    if not isinstance(execution, ConditionalExecution):
        raise ConditionalExecutionStoreError("CONDITIONAL_STORE_EXECUTION_INVALID", "Conditional execution güvenli tipte değil.")


def _validate_successor(prior: ConditionalExecution, current: ConditionalExecution) -> None:
    if (
        prior.conditional_order_id,
        prior.symbol,
        prior.side,
        prior.trigger_kind,
        prior.trigger_price,
    ) != (
        current.conditional_order_id,
        current.symbol,
        current.side,
        current.trigger_kind,
        current.trigger_price,
    ):
        raise ConditionalExecutionStoreError("CONDITIONAL_STORE_STATE_CONFLICT", "Conditional immutable kimliği değiştirilemez.")
    if prior == current:
        return
    if (prior.status, current.status) not in {
        (ConditionalStatus.ARMED, ConditionalStatus.TRIGGERED),
        (ConditionalStatus.ARMED, ConditionalStatus.CANCELED),
        (ConditionalStatus.ARMED, ConditionalStatus.QUARANTINED),
        (ConditionalStatus.TRIGGERED, ConditionalStatus.EXECUTION_IDENTIFIED),
        (ConditionalStatus.TRIGGERED, ConditionalStatus.CANCELED),
        (ConditionalStatus.TRIGGERED, ConditionalStatus.QUARANTINED),
    }:
        raise ConditionalExecutionStoreError("CONDITIONAL_STORE_STATE_CONFLICT", "Conditional geçiş sırası değiştirilemez.")


def _execution_payload(execution: ConditionalExecution) -> dict[str, object]:
    return {
        "conditional_order_id": execution.conditional_order_id,
        "symbol": execution.symbol,
        "side": execution.side.value,
        "trigger_kind": execution.trigger_kind,
        "trigger_price": execution.trigger_price,
        "status": execution.status.value,
        "trigger_event_id": execution.trigger_event_id,
        "observed_at_ms": execution.observed_at_ms,
        "observed_price": execution.observed_price,
        "execution_order_id": execution.execution_order_id,
        "execution_order_type": execution.execution_order_type,
        "execution_event_id": execution.execution_event_id,
        "execution_observed_at_ms": execution.execution_observed_at_ms,
        "cancel_event_id": execution.cancel_event_id,
        "canceled_at_ms": execution.canceled_at_ms,
        "quarantine_event_id": execution.quarantine_event_id,
        "quarantined_at_ms": execution.quarantined_at_ms,
        "quarantine_reason": execution.quarantine_reason,
    }


def _decode_checked(payload: str, payload_hash: str) -> ConditionalExecution:
    if _digest(payload) != payload_hash:
        raise ConditionalExecutionStoreError("CONDITIONAL_STORE_RECORD_CORRUPT", "Conditional state checksum doğrulanamadı.")
    try:
        data = json.loads(payload)
        return ConditionalExecution(**data)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ConditionalExecutionStoreError("CONDITIONAL_STORE_RECORD_CORRUPT", "Conditional state payload geçersiz.") from exc


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sql_text(value: str) -> str:
    return value.replace("'", "''")


def _validate_path(path: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve()
    if "YEDEK_ESKI_PROJE" in resolved.parts or any(
        item.is_symlink() or bool(getattr(item, "is_junction", lambda: False)())
        for item in (candidate, *candidate.parents)
    ):
        raise ConditionalExecutionStoreError("CONDITIONAL_STORE_PATH_UNSAFE", "Conditional store backup/linked path üzerinde olamaz.")
    if candidate.exists() and not candidate.is_file():
        raise ConditionalExecutionStoreError("CONDITIONAL_STORE_PATH_INVALID", "Conditional store yolu dosya olmalıdır.")
    if not resolved.parent.is_dir():
        raise ConditionalExecutionStoreError("CONDITIONAL_STORE_PATH_INVALID", "Conditional store parent yolu bulunmalıdır.")
    return candidate


def _connect(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=rw", uri=True, isolation_level=None, timeout=5)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    return db
