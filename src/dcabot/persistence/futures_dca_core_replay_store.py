"""Read-only gate for the future durable CORE01 replay receipt owner."""

from dataclasses import dataclass
from pathlib import Path
import sqlite3

from dcabot.application.futures_dca_core_mapping import FuturesDcaCoreReplayReceipt
from .futures_dca_journal_schema import (
    SCHEMA_VERSION,
    FuturesDcaJournalSchemaError,
    _open_existing,
)


_RECEIPT_COLUMNS = frozenset(
    {
        "mapping_id",
        "event_id",
        "posting_id",
        "transition_event_id",
        "release_identity",
        "release_cursor",
        "fingerprint",
    }
)
_RECEIPT_SCOPE = frozenset(
    {
        "mapping_id",
        "event_id",
        "posting_id",
        "transition_event_id",
        "release_identity",
        "release_cursor",
    }
)


def append_futures_dca_core_replay_receipt(
    path: Path,
    receipt: FuturesDcaCoreReplayReceipt,
) -> str:
    """Persist one verified replay receipt, or return an exact duplicate."""

    if not isinstance(receipt, FuturesDcaCoreReplayReceipt):
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_CORE_REPLAY_RECEIPT_INVALID",
            "Replay receipt güvenli tipte değil.",
        )
    values = (
        receipt.mapping_id,
        receipt.event_id,
        receipt.posting_id,
        receipt.transition_event_id,
        receipt.release_identity,
        receipt.release_cursor,
        receipt.fingerprint,
    )
    db = _open_existing(path)
    db.execute("PRAGMA foreign_keys=ON")
    try:
        db.execute("BEGIN IMMEDIATE")
        try:
            result = _append_core_replay_receipt_unlocked(db, receipt)
            db.execute("COMMIT")
            return result
        except BaseException:
            db.execute("ROLLBACK")
            raise
    finally:
        db.close()


def _append_core_replay_receipt_unlocked(
    db: sqlite3.Connection,
    receipt: FuturesDcaCoreReplayReceipt,
) -> str:
    _verify_receipt_links_unlocked(db, receipt)
    values = (
        receipt.mapping_id,
        receipt.event_id,
        receipt.posting_id,
        receipt.transition_event_id,
        receipt.release_identity,
        receipt.release_cursor,
        receipt.fingerprint,
    )
    prior = db.execute(
        "SELECT mapping_id, event_id, posting_id, transition_event_id, release_identity, "
        "release_cursor, fingerprint FROM core_replay_receipts WHERE fingerprint=?",
        (receipt.fingerprint,),
    ).fetchone()
    if prior is not None:
        if prior != values:
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_CORE_REPLAY_RECEIPT_CONFLICT",
                "Replay receipt fingerprint farklı durable scope ile kullanılamaz.",
            )
        return "DUPLICATE"
    prior = db.execute(
        "SELECT mapping_id, event_id, posting_id, transition_event_id, release_identity, "
        "release_cursor, fingerprint FROM core_replay_receipts "
        "WHERE mapping_id=? OR event_id=? OR posting_id=? OR transition_event_id=? "
        "OR release_identity=?",
        values[:5],
    ).fetchone()
    if prior is not None:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_CORE_REPLAY_RECEIPT_CONFLICT",
            "Replay receipt identity başka durable receipt’e bağlanamaz.",
        )
    db.execute(
        "INSERT INTO core_replay_receipts("
        "mapping_id, event_id, posting_id, transition_event_id, release_identity, "
        "release_cursor, fingerprint) VALUES (?, ?, ?, ?, ?, ?, ?)",
        values,
    )
    return "ACCEPTED"


def load_futures_dca_core_replay_receipts(
    path: Path,
) -> tuple[FuturesDcaCoreReplayReceipt, ...]:
    """Replay durable receipts and verify every event, posting and release link."""

    db = _open_existing(path)
    try:
        db.execute("PRAGMA query_only=ON")
        rows = db.execute(
            "SELECT mapping_id, event_id, posting_id, transition_event_id, release_identity, "
            "release_cursor, fingerprint FROM core_replay_receipts "
            "ORDER BY release_cursor, event_id, fingerprint"
        ).fetchall()
        result = []
        for row in rows:
            try:
                receipt = FuturesDcaCoreReplayReceipt(*row)
            except (TypeError, ValueError) as exc:
                raise FuturesDcaJournalSchemaError(
                    "FUTURES_DCA_CORE_REPLAY_RECEIPT_CORRUPT",
                    "Replay receipt payload doğrulanamadı.",
                ) from exc
            _verify_receipt_links_unlocked(db, receipt)
            result.append(receipt)
        return tuple(result)
    except FuturesDcaJournalSchemaError:
        raise
    except (TypeError, ValueError, sqlite3.Error) as exc:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_CORE_REPLAY_RECEIPT_CORRUPT",
            "Replay receipt replay edilemedi.",
        ) from exc
    finally:
        db.close()


def _verify_receipt_links_unlocked(
    db: sqlite3.Connection,
    receipt: FuturesDcaCoreReplayReceipt,
) -> None:
    event = db.execute(
        "SELECT event_state FROM journal_events WHERE event_id=?",
        (receipt.event_id,),
    ).fetchone()
    if event is None or event[0] != "ACCEPTED":
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_CORE_REPLAY_RECEIPT_EVENT_INVALID",
            "Replay receipt yalnız accepted event’e bağlanabilir.",
        )
    transition_event = db.execute(
        "SELECT event_state FROM journal_events WHERE event_id=?",
        (receipt.transition_event_id,),
    ).fetchone()
    if transition_event is None or transition_event[0] != "ACCEPTED":
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_CORE_REPLAY_RECEIPT_TRANSITION_EVENT_MISSING",
            "Replay receipt transition event bulunamadı veya accepted değil.",
        )
    posting = db.execute(
        "SELECT source_event_id FROM economic_postings WHERE posting_id=?",
        (receipt.posting_id,),
    ).fetchone()
    if posting is None or posting[0] != receipt.event_id:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_CORE_REPLAY_RECEIPT_POSTING_INVALID",
            "Replay receipt posting’i fill event’iyle eşleşmiyor.",
        )
    release = db.execute(
        "SELECT reservation_id, transition_event_id, release_cursor "
        "FROM reservation_releases WHERE release_identity=?",
        (receipt.release_identity,),
    ).fetchone()
    if release is None or release[1:] != (receipt.transition_event_id, receipt.release_cursor):
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_CORE_REPLAY_RECEIPT_RELEASE_INVALID",
            "Replay receipt release transition ve cursor ile eşleşmiyor.",
        )
    reservation = db.execute(
        "SELECT release_identity, release_cursor FROM reservations WHERE reservation_id=?",
        (release[0],),
    ).fetchone()
    if reservation != (receipt.release_identity, receipt.release_cursor):
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_CORE_REPLAY_RECEIPT_RESERVATION_INVALID",
            "Replay receipt reservation son projection ile eşleşmiyor.",
        )


@dataclass(frozen=True, slots=True)
class FuturesDcaCoreReplayStorePreflight:
    """Read-only schema decision; READY never writes or activates a Store."""

    status: str
    missing_authority: tuple[str, ...]
    reason_code: str
    schema_version: int

    def __post_init__(self) -> None:
        if self.status not in {"READY", "BLOCKED"}:
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_CORE_REPLAY_PREFLIGHT_STATUS_INVALID",
                "Replay Store preflight yalnız READY veya BLOCKED döndürebilir.",
            )
        if not isinstance(self.missing_authority, tuple) or any(
            not isinstance(item, str) for item in self.missing_authority
        ):
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_CORE_REPLAY_PREFLIGHT_AUTHORITY_INVALID",
                "Replay Store eksik authority tuple olmalıdır.",
            )
        if type(self.schema_version) is not int or self.schema_version < 1:
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_CORE_REPLAY_PREFLIGHT_SCHEMA_INVALID",
                "Replay Store schema revision pozitif integer olmalıdır.",
            )


def preflight_futures_dca_core_replay_store(
    path: Path,
) -> FuturesDcaCoreReplayStorePreflight:
    """Inspect the current journal without creating or altering a receipt Store."""

    db = _open_existing(path)
    try:
        db.execute("PRAGMA query_only=ON")
        tables = {
            row[0]
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "core_replay_receipts" not in tables:
            return FuturesDcaCoreReplayStorePreflight(
                "BLOCKED",
                ("core_replay_receipts",),
                "FUTURES_DCA_CORE_REPLAY_RECEIPT_SCHEMA_MISSING",
                SCHEMA_VERSION,
            )
        columns = {
            row[1]
            for row in db.execute("PRAGMA table_info(core_replay_receipts)")
        }
        missing_columns = tuple(sorted(_RECEIPT_COLUMNS - columns))
        if missing_columns:
            return FuturesDcaCoreReplayStorePreflight(
                "BLOCKED",
                tuple(f"core_replay_receipts.{column}" for column in missing_columns),
                "FUTURES_DCA_CORE_REPLAY_RECEIPT_SCHEMA_INVALID",
                SCHEMA_VERSION,
            )
        unique_scopes = set()
        for index in db.execute("PRAGMA index_list(core_replay_receipts)"):
            if not index[2]:
                continue
            index_name = str(index[1]).replace('"', '""')
            unique_scopes.add(
                frozenset(row[2] for row in db.execute(f'PRAGMA index_info("{index_name}")'))
            )
        missing_constraints = tuple(
            sorted(
                scope
                for scope in (_RECEIPT_SCOPE, frozenset({"fingerprint"}))
                if scope not in unique_scopes
            )
        )
        if missing_constraints:
            return FuturesDcaCoreReplayStorePreflight(
                "BLOCKED",
                tuple("unique:" + ",".join(sorted(scope)) for scope in missing_constraints),
                "FUTURES_DCA_CORE_REPLAY_RECEIPT_CONSTRAINT_INVALID",
                SCHEMA_VERSION,
            )
        return FuturesDcaCoreReplayStorePreflight(
            "READY", (), "FUTURES_DCA_CORE_REPLAY_RECEIPT_SCHEMA_READY", SCHEMA_VERSION
        )
    except FuturesDcaJournalSchemaError:
        raise
    except sqlite3.Error as exc:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_CORE_REPLAY_PREFLIGHT_FAILED", "Replay Store schema okunamadı."
        ) from exc
    finally:
        db.close()
