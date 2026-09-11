"""Dedicated SQLite boundary for non-economic lifecycle event records."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sqlite3

from dcabot.application.config_revision import ConfigRevision, ConfigRevisionError
from dcabot.application.deal_lifecycle import DealLifecycle, new_deal_lifecycle
from dcabot.application.lifecycle_event_contract import (
    LifecycleEvent,
    LifecycleEventContractError,
    accept_lifecycle_event,
)
from dcabot.application.lifecycle_event_transition import apply_lifecycle_event


APPLICATION_ID = 0x44434C53
SCHEMA_VERSION = 2


class LifecycleStoreError(ValueError):
    """Raised when a lifecycle store cannot be safely opened or replayed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class LifecycleReplay:
    """Validated lifecycle projection reconstructed from stored events."""

    lifecycle: DealLifecycle | None
    history: tuple[LifecycleEvent, ...]


class LifecycleStore:
    """Own a separate versioned SQLite store for lifecycle events only."""

    def __init__(self, path: Path, db: sqlite3.Connection) -> None:
        self.path = path
        self.db = db

    @classmethod
    def create(cls, path: Path) -> "LifecycleStore":
        """Create a new store and reject an existing path."""

        validated = _validate_store_path(path)
        if validated.exists():
            raise LifecycleStoreError(
                "LIFECYCLE_STORE_EXISTS", "Lifecycle store mevcut dosyanın üzerine yazamaz."
            )
        validated.parent.mkdir(parents=True, exist_ok=True)
        db = _connect(validated, mode="rwc")
        try:
            db.executescript(
                f"""
                BEGIN IMMEDIATE;
                PRAGMA application_id={APPLICATION_ID};
                PRAGMA user_version={SCHEMA_VERSION};
                CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE config_revisions(
                    revision_id TEXT PRIMARY KEY,
                    snapshot_json TEXT NOT NULL,
                    snapshot_sha256 TEXT NOT NULL
                );
                CREATE TABLE lifecycle_events(
                    event_id TEXT PRIMARY KEY,
                    deal_id TEXT NOT NULL,
                    config_revision_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_sequence INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    UNIQUE(deal_id, event_sequence)
                );
                INSERT INTO metadata(key, value) VALUES
                    ('store', 'offline-lifecycle-1'),
                    ('scope', 'NON_ECONOMIC_LIFECYCLE_ONLY');
                COMMIT;
                """
            )
            return cls(validated, db)
        except BaseException:
            db.close()
            raise

    @classmethod
    def open(cls, path: Path) -> "LifecycleStore":
        """Open an existing store without migration or schema rewriting."""

        validated = _validate_store_path(path)
        if not validated.is_file():
            raise LifecycleStoreError(
                "LIFECYCLE_STORE_MISSING", "Lifecycle store bulunamadı."
            )
        db = _connect(validated, mode="rw")
        try:
            if (
                db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
                or db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION
            ):
                raise LifecycleStoreError(
                    "LIFECYCLE_STORE_UNSUPPORTED", "Lifecycle store şeması desteklenmiyor."
                )
            metadata = dict(db.execute("SELECT key, value FROM metadata"))
            if metadata != {
                "store": "offline-lifecycle-1",
                "scope": "NON_ECONOMIC_LIFECYCLE_ONLY",
            }:
                raise LifecycleStoreError(
                    "LIFECYCLE_STORE_METADATA_INVALID", "Lifecycle store metadata geçersiz."
                )
            return cls(validated, db)
        except BaseException:
            db.close()
            raise

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "LifecycleStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def append(self, event: LifecycleEvent, *, config_revision: ConfigRevision) -> str:
        """Atomically append one event or return an exact duplicate outcome."""

        if not isinstance(event, LifecycleEvent):
            raise LifecycleEventContractError(
                "LIFECYCLE_EVENT_INVALID", "Lifecycle event kaydı geçersiz."
            )
        if not isinstance(config_revision, ConfigRevision):
            raise ConfigRevisionError(
                "CONFIG_REVISION_INVALID", "Config revision kaydı geçersiz."
            )
        if event.config_revision_id != config_revision.revision_id:
            raise LifecycleEventContractError(
                "LIFECYCLE_EVENT_REVISION_CONFLICT",
                "Event config revision kimliği snapshot ile eşleşmiyor.",
            )
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT event_id, deal_id, config_revision_id, event_type, event_sequence, payload "
                "FROM lifecycle_events WHERE event_id=?",
                (event.event_id,),
            ).fetchone()
            if row is not None:
                prior = _decode_row(row)
                if prior == event:
                    self.db.execute("COMMIT")
                    return "DUPLICATE"
                raise LifecycleEventContractError(
                    "LIFECYCLE_EVENT_CONFLICT",
                    "Aynı lifecycle event kimliği farklı kayıtla kullanılamaz.",
                )

            replay = self._load_unlocked()
            revision_row = self.db.execute(
                "SELECT revision_id, snapshot_json, snapshot_sha256 FROM config_revisions "
                "WHERE revision_id=?",
                (config_revision.revision_id,),
            ).fetchone()
            if revision_row is not None and _decode_revision(revision_row) != config_revision:
                raise LifecycleEventContractError(
                    "CONFIG_REVISION_CONFLICT",
                    "Aynı config revision farklı snapshot ile kullanılamaz.",
                )
            lifecycle = replay.lifecycle or new_deal_lifecycle(
                event.deal_id, event.config_revision_id
            )
            _, _, outcome = apply_lifecycle_event(lifecycle, replay.history, event)
            payload = _canonical_event(event)
            if revision_row is None:
                self.db.execute(
                    "INSERT INTO config_revisions(revision_id, snapshot_json, snapshot_sha256) "
                    "VALUES (?, ?, ?)",
                    (
                        config_revision.revision_id,
                        config_revision.snapshot_json,
                        config_revision.snapshot_sha256,
                    ),
                )
            self.db.execute(
                "INSERT INTO lifecycle_events(event_id, deal_id, config_revision_id, event_type, "
                "event_sequence, payload) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    event.event_id,
                    event.deal_id,
                    event.config_revision_id,
                    event.event,
                    event.event_sequence,
                    payload,
                ),
            )
            self.db.execute("COMMIT")
            return outcome
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def load(self) -> LifecycleReplay:
        """Replay all records and return the validated lifecycle projection."""

        self.db.execute("BEGIN")
        try:
            result = self._load_unlocked()
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _load_unlocked(self) -> LifecycleReplay:
        revisions = {
            row[0]: _decode_revision(row)
            for row in self.db.execute(
                "SELECT revision_id, snapshot_json, snapshot_sha256 FROM config_revisions"
            )
        }
        rows = self.db.execute(
            "SELECT event_id, deal_id, config_revision_id, event_type, event_sequence, payload "
            "FROM lifecycle_events ORDER BY event_sequence"
        ).fetchall()
        lifecycle: DealLifecycle | None = None
        history: tuple[LifecycleEvent, ...] = ()
        try:
            for row in rows:
                event = _decode_row(row)
                if event.config_revision_id not in revisions:
                    raise LifecycleStoreError(
                        "LIFECYCLE_RECORD_CORRUPT", "Lifecycle event revision snapshot bulunamadı."
                    )
                lifecycle = lifecycle or new_deal_lifecycle(
                    event.deal_id, event.config_revision_id
                )
                lifecycle, history, outcome = apply_lifecycle_event(
                    lifecycle, history, event
                )
                if outcome != "ACCEPTED":
                    raise LifecycleStoreError(
                        "LIFECYCLE_STORE_CORRUPT", "Stored lifecycle event duplicate."
                    )
        except LifecycleStoreError:
            raise
        except (LifecycleEventContractError, ValueError) as exc:
            raise LifecycleStoreError(
                "LIFECYCLE_STORE_CORRUPT", "Stored lifecycle event replay edilemedi."
            ) from exc
        return LifecycleReplay(lifecycle=lifecycle, history=history)


def _canonical_event(event: LifecycleEvent) -> str:
    return json.dumps(
        asdict(event), ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )


def _decode_row(row: tuple[object, ...]) -> LifecycleEvent:
    event_id, deal_id, revision_id, event_type, sequence, payload = row
    try:
        raw = json.loads(payload)
        if set(raw) != {
            "config_revision_id",
            "deal_id",
            "event",
            "event_id",
            "event_sequence",
        }:
            raise ValueError("Unexpected lifecycle payload fields")
        event = LifecycleEvent(**raw)
        if (event.event_id, event.deal_id, event.config_revision_id, event.event, event.event_sequence) != (
            event_id,
            deal_id,
            revision_id,
            event_type,
            sequence,
        ):
            raise ValueError("Lifecycle row and payload differ")
        return event
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise LifecycleStoreError(
            "LIFECYCLE_RECORD_CORRUPT", "Lifecycle record doğrulanamadı."
        ) from exc


def _decode_revision(row: tuple[object, ...]) -> ConfigRevision:
    try:
        revision = ConfigRevision(
            revision_id=row[0],
            snapshot_json=row[1],
            snapshot_sha256=row[2],
        )
        return revision
    except (ConfigRevisionError, TypeError, ValueError) as exc:
        raise LifecycleStoreError(
            "LIFECYCLE_RECORD_CORRUPT", "Config revision kaydı doğrulanamadı."
        ) from exc


def _connect(path: Path, *, mode: str) -> sqlite3.Connection:
    try:
        db = sqlite3.connect(
            path.resolve().as_uri() + f"?mode={mode}",
            uri=True,
            isolation_level=None,
            timeout=5,
        )
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        return db
    except (OSError, sqlite3.Error) as exc:
        raise LifecycleStoreError(
            "LIFECYCLE_STORE_UNAVAILABLE", "Lifecycle store açılamadı."
        ) from exc


def _validate_store_path(path: Path) -> Path:
    validated = Path(path)
    resolved = validated.resolve()
    if "YEDEK_ESKI_PROJE" in resolved.parts or any(
        item.is_symlink() or item.is_junction()
        for item in (validated, *validated.parents)
    ):
        raise LifecycleStoreError(
            "LIFECYCLE_STORE_PATH_UNSAFE", "Lifecycle store güvenli olmayan yolda."
        )
    if validated.exists() and not validated.is_file():
        raise LifecycleStoreError(
            "LIFECYCLE_STORE_PATH_INVALID", "Lifecycle store yolu dosya olmalıdır."
        )
    return validated
