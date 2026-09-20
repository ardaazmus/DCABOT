"""Durable offline replay for the bounded Futures DCA event contract."""

import hashlib
import json
from pathlib import Path
import re
import sqlite3

from dcabot.application.futures_dca_event_contract import (
    FuturesDcaEventError,
    FuturesDcaFillEvent,
    accept_futures_dca_fill_event,
)
from dcabot.application.futures_dca_fill_projection import FuturesDcaFill


APPLICATION_ID = 0x44464453
SCHEMA_VERSION = 1
MAX_EVENTS = 1_000


class FuturesDcaEventStoreError(ValueError):
    """Raised when the durable Futures DCA event journal cannot be trusted."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class FuturesDcaEventStore:
    """Own one bounded event journal without reservation or economic authority."""

    def __init__(self, path: Path, db: sqlite3.Connection):
        self.path = path
        self.db = db

    @classmethod
    def create(cls, path: Path, deal_id: str, config_revision_id: str) -> "FuturesDcaEventStore":
        validated = _validate_path(path)
        if validated.exists():
            raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_EXISTS", "Event store üzerine yazılamaz.")
        _validate_identifier(deal_id, "FUTURES_DCA_STORE_DEAL_INVALID")
        _validate_identifier(config_revision_id, "FUTURES_DCA_STORE_CONFIG_INVALID")
        try:
            with validated.open("xb"):
                pass
            db = _connect(validated)
            store = cls(validated, db)
            store._initialize(deal_id, config_revision_id)
            return store
        except FuturesDcaEventStoreError:
            if "db" in locals():
                db.close()
            raise
        except (OSError, sqlite3.Error) as exc:
            if "db" in locals():
                db.close()
            raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_UNAVAILABLE", "Futures DCA event store açılamadı.") from exc

    @classmethod
    def open(cls, path: Path) -> "FuturesDcaEventStore":
        validated = _validate_path(path)
        if not validated.is_file():
            raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_MISSING", "Futures DCA event store bulunamadı.")
        try:
            db = _connect(validated)
            if (
                db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
                or db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION
            ):
                raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_UNSUPPORTED", "Futures DCA event store şeması desteklenmiyor.")
            store = cls(validated, db)
            store.load()
            return store
        except FuturesDcaEventStoreError:
            if "db" in locals():
                db.close()
            raise
        except (OSError, sqlite3.Error) as exc:
            if "db" in locals():
                db.close()
            raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_UNAVAILABLE", "Futures DCA event store açılamadı.") from exc

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "FuturesDcaEventStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def append(self, event: FuturesDcaFillEvent) -> str:
        """Atomically append one event or return DUPLICATE without mutation."""

        if not isinstance(event, FuturesDcaFillEvent):
            raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_EVENT_INVALID", "Futures DCA event güvenli tipte değil.")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            metadata = self._metadata_unlocked()
            if (event.deal_id, event.config_revision_id) != (metadata["deal_id"], metadata["config_revision_id"]):
                raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_SCOPE_CONFLICT", "Event store scope ile eşleşmiyor.")
            history = self._history_unlocked(metadata)
            _, outcome = _accept(history, event)
            if outcome == "DUPLICATE":
                self.db.execute("COMMIT")
                return outcome
            if len(history) >= MAX_EVENTS:
                raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_EVENT_LIMIT", "Futures DCA event sınırına ulaşıldı.")
            payload = _canonical(_event_payload(event))
            self.db.execute(
                "INSERT INTO futures_dca_events(sequence_no, event_id, event_payload, event_hash) VALUES (?, ?, ?, ?)",
                (event.event_sequence, event.event_id, payload, _digest(payload)),
            )
            self.db.execute("COMMIT")
            return outcome
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def load(self) -> tuple[FuturesDcaFillEvent, ...]:
        """Replay all events and verify metadata, sequence, identity and checksums."""

        self.db.execute("BEGIN")
        try:
            metadata = self._metadata_unlocked()
            history = self._history_unlocked(metadata)
            self.db.execute("COMMIT")
            return history
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _initialize(self, deal_id: str, config_revision_id: str) -> None:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute(f"PRAGMA application_id={APPLICATION_ID}")
            self.db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
            self.db.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            self.db.execute(
                "CREATE TABLE futures_dca_events(sequence_no INTEGER PRIMARY KEY, event_id TEXT UNIQUE NOT NULL, event_payload TEXT NOT NULL, event_hash TEXT NOT NULL)"
            )
            self.db.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                (
                    ("store", "offline-futures-dca-event-1"),
                    ("scope", "DURABLE_FUTURES_DCA_EVENT_REPLAY"),
                    ("deal_id", deal_id),
                    ("config_revision_id", config_revision_id),
                ),
            )
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _metadata_unlocked(self) -> dict[str, str]:
        metadata = dict(self.db.execute("SELECT key, value FROM metadata"))
        if (
            metadata.get("store") != "offline-futures-dca-event-1"
            or metadata.get("scope") != "DURABLE_FUTURES_DCA_EVENT_REPLAY"
        ):
            raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_METADATA_INVALID", "Futures DCA event metadata geçersiz.")
        for key in ("deal_id", "config_revision_id"):
            _validate_identifier(metadata.get(key), "FUTURES_DCA_STORE_METADATA_INVALID")
        return metadata

    def _history_unlocked(self, metadata: dict[str, str]) -> tuple[FuturesDcaFillEvent, ...]:
        history: tuple[FuturesDcaFillEvent, ...] = ()
        for expected_sequence, (sequence, event_id, payload, payload_hash) in enumerate(
            self.db.execute("SELECT sequence_no, event_id, event_payload, event_hash FROM futures_dca_events ORDER BY sequence_no"),
            start=1,
        ):
            if sequence != expected_sequence:
                raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_SEQUENCE_INVALID", "Futures DCA event sıra numarası geçersiz.")
            event = _decode_checked(payload, payload_hash)
            if event.event_id != event_id or (event.deal_id, event.config_revision_id) != (metadata["deal_id"], metadata["config_revision_id"]):
                raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_RECORD_CORRUPT", "Futures DCA event identity doğrulanamadı.")
            candidate, outcome = _accept(history, event)
            if outcome != "ACCEPTED":
                raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_RECORD_CORRUPT", "Futures DCA event replay duplicate üretti.")
            history = candidate
        return history


def _accept(history: tuple[FuturesDcaFillEvent, ...], event: FuturesDcaFillEvent) -> tuple[tuple[FuturesDcaFillEvent, ...], str]:
    try:
        return accept_futures_dca_fill_event(history, event)
    except FuturesDcaEventError as exc:
        raise FuturesDcaEventStoreError(exc.code, str(exc)) from exc


def _event_payload(event: FuturesDcaFillEvent) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "deal_id": event.deal_id,
        "config_revision_id": event.config_revision_id,
        "event_sequence": event.event_sequence,
        "fill": {
            "execution_id": event.fill.execution_id,
            "level_index": event.fill.level_index,
            "quantity": event.fill.quantity,
            "price": event.fill.price,
        },
    }


def _decode_checked(payload: str, payload_hash: str) -> FuturesDcaFillEvent:
    if _digest(payload) != payload_hash:
        raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_RECORD_CORRUPT", "Futures DCA event checksum doğrulanamadı.")
    try:
        data = json.loads(payload)
        fill = data["fill"]
        return FuturesDcaFillEvent(
            data["event_id"], data["deal_id"], data["config_revision_id"], data["event_sequence"],
            FuturesDcaFill(fill["execution_id"], fill["level_index"], fill["quantity"], fill["price"]),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_RECORD_CORRUPT", "Futures DCA event payload geçersiz.") from exc


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_identifier(value: object, code: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9:_-]{1,128}", value, re.ASCII):
        raise FuturesDcaEventStoreError(code, "Futures DCA scope kimliği geçersiz.")


def _validate_path(path: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve()
    if "YEDEK_ESKI_PROJE" in resolved.parts or any(
        item.is_symlink() or bool(getattr(item, "is_junction", lambda: False)())
        for item in (candidate, *candidate.parents)
    ):
        raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_PATH_UNSAFE", "Futures DCA event store backup/linked path üzerinde olamaz.")
    if candidate.exists() and not candidate.is_file():
        raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_PATH_INVALID", "Futures DCA event store yolu dosya olmalıdır.")
    if not resolved.parent.is_dir():
        raise FuturesDcaEventStoreError("FUTURES_DCA_STORE_PATH_INVALID", "Futures DCA event store parent yolu bulunmalıdır.")
    return candidate


def _connect(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=rw", uri=True, isolation_level=None, timeout=5)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    return db
