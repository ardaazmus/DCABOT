"""Durable offline replay for the profile-bound linear futures ledger."""

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import sqlite3

from dcabot.application.linear_futures_math import (
    LinearLedgerEvent,
    LinearLedgerState,
    LinearFuturesError,
    apply_linear_ledger_event,
    new_linear_ledger_state,
)


APPLICATION_ID = 0x444C4C47
SCHEMA_VERSION = 1
MAX_EVENTS = 1_000


class LinearLedgerStoreError(ValueError):
    """Raised when the durable linear ledger cannot be trusted."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class LinearLedgerStoreOutcome(StrEnum):
    """Result of appending one immutable ledger event."""

    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True, slots=True)
class LinearLedgerStore:
    """Own one bounded fee/funding projection without position or core authority."""

    path: Path
    db: sqlite3.Connection

    @classmethod
    def create(cls, path: Path, settlement_asset: str) -> "LinearLedgerStore":
        validated = _validate_path(path)
        if validated.exists():
            raise LinearLedgerStoreError("LINEAR_STORE_EXISTS", "Linear ledger store üzerine yazılamaz.")
        try:
            new_linear_ledger_state(settlement_asset)
            with validated.open("xb"):
                pass
            db = _connect(validated)
            store = cls(validated, db)
            store._initialize(settlement_asset)
            return store
        except LinearLedgerStoreError:
            if "db" in locals():
                db.close()
            raise
        except (OSError, sqlite3.Error, LinearFuturesError) as exc:
            if "db" in locals():
                db.close()
            raise LinearLedgerStoreError("LINEAR_STORE_UNAVAILABLE", "Linear ledger store açılamadı.") from exc

    @classmethod
    def open(cls, path: Path) -> "LinearLedgerStore":
        validated = _validate_path(path)
        if not validated.is_file():
            raise LinearLedgerStoreError("LINEAR_STORE_MISSING", "Linear ledger store bulunamadı.")
        try:
            db = _connect(validated)
            if (
                db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
                or db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION
            ):
                raise LinearLedgerStoreError("LINEAR_STORE_UNSUPPORTED", "Linear ledger store şeması desteklenmiyor.")
            metadata = dict(db.execute("SELECT key, value FROM metadata"))
            if metadata.get("store") != "offline-linear-ledger-1" or metadata.get(
                "scope"
            ) != "DURABLE_LINEAR_FEE_FUNDING_REPLAY":
                raise LinearLedgerStoreError("LINEAR_STORE_METADATA_INVALID", "Linear ledger metadata geçersiz.")
            store = cls(validated, db)
            store.load()
            return store
        except LinearLedgerStoreError:
            if "db" in locals():
                db.close()
            raise
        except (OSError, sqlite3.Error, LinearFuturesError) as exc:
            if "db" in locals():
                db.close()
            raise LinearLedgerStoreError("LINEAR_STORE_UNAVAILABLE", "Linear ledger store açılamadı.") from exc

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "LinearLedgerStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def append(self, event: LinearLedgerEvent) -> LinearLedgerStoreOutcome:
        """Atomically append one event, making an exact duplicate a no-op."""

        if not isinstance(event, LinearLedgerEvent):
            raise LinearLedgerStoreError("LINEAR_STORE_EVENT_INVALID", "Linear ledger event güvenli tipte değil.")
        state = self.load()
        if event.settlement_asset != state.settlement_asset:
            raise LinearLedgerStoreError("LINEAR_STORE_ASSET_INVALID", "Ledger event settlement asset ile eşleşmiyor.")
        payload = _canonical(_event_payload(event))
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT event_payload, event_hash FROM linear_ledger_events WHERE event_id=?",
                (event.event_id,),
            ).fetchone()
            if row is not None:
                prior = _decode_checked(row[0], row[1])
                if prior != event:
                    raise LinearLedgerStoreError(
                        "LINEAR_STORE_EVENT_CONFLICT", "Aynı ledger event kimliği farklı payload ile kullanılamaz."
                    )
                self.db.execute("COMMIT")
                return LinearLedgerStoreOutcome.DUPLICATE
            if self.db.execute("SELECT COUNT(*) FROM linear_ledger_events").fetchone()[0] >= MAX_EVENTS:
                raise LinearLedgerStoreError("LINEAR_STORE_EVENT_LIMIT", "Linear ledger event sınırına ulaşıldı.")
            try:
                apply_linear_ledger_event(state, event)
            except LinearFuturesError as exc:
                raise LinearLedgerStoreError(exc.code, str(exc)) from exc
            sequence = self.db.execute("SELECT COALESCE(MAX(sequence_no), 0) + 1 FROM linear_ledger_events").fetchone()[0]
            self.db.execute(
                "INSERT INTO linear_ledger_events(sequence_no, event_id, event_payload, event_hash) VALUES (?, ?, ?, ?)",
                (sequence, event.event_id, payload, _digest(payload)),
            )
            self.db.execute("COMMIT")
            return LinearLedgerStoreOutcome.ACCEPTED
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def load(self) -> LinearLedgerState:
        """Replay the ledger and verify every stored payload checksum."""

        self.db.execute("BEGIN")
        try:
            metadata = dict(self.db.execute("SELECT key, value FROM metadata"))
            settlement_asset = metadata.get("settlement_asset")
            if not isinstance(settlement_asset, str):
                raise LinearLedgerStoreError("LINEAR_STORE_METADATA_INVALID", "Settlement asset metadata eksik.")
            try:
                state = new_linear_ledger_state(settlement_asset)
            except LinearFuturesError as exc:
                raise LinearLedgerStoreError(exc.code, "Settlement asset metadata geçersiz.") from exc
            rows = self.db.execute(
                "SELECT sequence_no, event_id, event_payload, event_hash FROM linear_ledger_events ORDER BY sequence_no"
            ).fetchall()
            for expected_sequence, (sequence, event_id, payload, payload_hash) in enumerate(rows, start=1):
                if sequence != expected_sequence:
                    raise LinearLedgerStoreError("LINEAR_STORE_SEQUENCE_INVALID", "Linear ledger sıra numarası geçersiz.")
                try:
                    event = _decode_checked(payload, payload_hash)
                    if event.event_id != event_id:
                        raise LinearLedgerStoreError("LINEAR_STORE_RECORD_CORRUPT", "Linear ledger event kimliği doğrulanamadı.")
                    state = apply_linear_ledger_event(state, event)
                except (LinearFuturesError, LinearLedgerStoreError) as exc:
                    code = exc.code if isinstance(exc, LinearFuturesError) else exc.code
                    raise LinearLedgerStoreError(code, "Linear ledger replay edilemedi.") from exc
            self.db.execute("COMMIT")
            return state
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _initialize(self, settlement_asset: str) -> None:
        self.db.executescript(
            f"""
            BEGIN IMMEDIATE;
            PRAGMA application_id={APPLICATION_ID};
            PRAGMA user_version={SCHEMA_VERSION};
            CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE linear_ledger_events(
                sequence_no INTEGER PRIMARY KEY,
                event_id TEXT UNIQUE NOT NULL,
                event_payload TEXT NOT NULL,
                event_hash TEXT NOT NULL
            );
            INSERT INTO metadata(key, value) VALUES
                ('store', 'offline-linear-ledger-1'),
                ('scope', 'DURABLE_LINEAR_FEE_FUNDING_REPLAY'),
                ('settlement_asset', '{_sql_text(settlement_asset)}');
            COMMIT;
            """
        )


def _event_payload(event: LinearLedgerEvent) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "effective_time_us": event.effective_time_us,
        "settlement_asset": event.settlement_asset,
        "amount": event.amount,
    }


def _decode_checked(payload: str, payload_hash: str) -> LinearLedgerEvent:
    if _digest(payload) != payload_hash:
        raise LinearLedgerStoreError("LINEAR_STORE_RECORD_CORRUPT", "Linear ledger checksum doğrulanamadı.")
    try:
        data = json.loads(payload)
        return LinearLedgerEvent(**data)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise LinearLedgerStoreError("LINEAR_STORE_RECORD_CORRUPT", "Linear ledger payload geçersiz.") from exc


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
        raise LinearLedgerStoreError("LINEAR_STORE_PATH_UNSAFE", "Linear ledger store backup/linked path üzerinde olamaz.")
    if candidate.exists() and not candidate.is_file():
        raise LinearLedgerStoreError("LINEAR_STORE_PATH_INVALID", "Linear ledger store yolu dosya olmalıdır.")
    if not resolved.parent.is_dir():
        raise LinearLedgerStoreError("LINEAR_STORE_PATH_INVALID", "Linear ledger store parent yolu bulunmalıdır.")
    return candidate


def _connect(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=rw", uri=True, isolation_level=None, timeout=5)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    return db
