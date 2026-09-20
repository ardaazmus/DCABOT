"""Persist the bounded greenfield journal for Futures DCA binding."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from dcabot.domain.numbers import exact_text, number, positive


APPLICATION_ID = 0x4446444A
SCHEMA_VERSION = 4
_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)


class FuturesDcaJournalSchemaError(ValueError):
    """Raised when the reserved Futures DCA journal schema cannot be created safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FuturesDcaProfileRevision:
    """Immutable venue/profile scope required before journal event binding."""

    revision_id: str
    venue: str
    product: str
    symbol: str
    settlement_asset: str
    margin_mode: str
    position_mode: str
    effective_time_us: int
    contract_size: str
    fee_policy_revision: str
    slippage_policy_revision: str
    rounding_policy_revision: str


@dataclass(frozen=True, slots=True)
class FuturesDcaEventEnvelope:
    """Immutable event envelope bound to one stored profile revision."""

    event_id: str
    sequence_no: int
    execution_id: str
    order_id: str
    event_kind: str
    profile_revision_id: str
    observed_time_us: int
    execution_time_us: int
    fill_quantity: str
    effective_price: str
    gross_commitment: str
    fee_amount: str
    fee_asset: str
    slippage_reference: str
    rounding_policy_revision: str
    payload: str
    event_state: str = "ACCEPTED"


@dataclass(frozen=True, slots=True)
class FuturesDcaReservationProjection:
    """Exact reservation projection referenced by an optional journal event."""

    reservation_id: str
    owner_scope: str
    asset: str
    reserved_amount: str
    consumed_amount: str
    releasable_amount: str
    release_identity: str | None
    terminal_state: str
    version: int
    source_event_id: str | None
    release_cursor: int = 0


@dataclass(frozen=True, slots=True)
class FuturesDcaEconomicPosting:
    """Exact economic posting cursor bound to one accepted journal event."""

    posting_id: str
    source_event_id: str
    posting_cursor: int
    commitment: str
    fee_amount: str
    funding_amount: str
    posting_state: str


_EVENT_STATES = frozenset({"ACCEPTED", "LATE", "UNKNOWN", "CONFLICT", "QUARANTINED"})


def create_futures_dca_journal_schema(path: Path) -> Path:
    """Create an empty greenfield schema without binding rows."""

    target = _validate_path(path)
    if target.exists():
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_JOURNAL_EXISTS", "Journal mevcut dosyanın üzerine yazamaz.")
    try:
        with target.open("xb"):
            pass
        db = sqlite3.connect(target.resolve().as_uri() + "?mode=rw", uri=True, isolation_level=None)
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute(f"PRAGMA application_id={APPLICATION_ID}")
            db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
            db.execute("CREATE TABLE journal_metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.executemany(
                "INSERT INTO journal_metadata(key, value) VALUES (?, ?)",
                (
                    ("store", "offline-futures-dca-journal-1"),
                    ("scope", "DURABLE_FUTURES_DCA_ATOMIC_BINDING"),
                    ("activation", "INERT_UNBOUND"),
                ),
            )
            db.execute(
                "CREATE TABLE profile_revisions("
                "revision_id TEXT PRIMARY KEY, venue TEXT NOT NULL, product TEXT NOT NULL, "
                "symbol TEXT NOT NULL, settlement_asset TEXT NOT NULL, margin_mode TEXT NOT NULL, "
                "position_mode TEXT NOT NULL, effective_time_us INTEGER NOT NULL, contract_size TEXT NOT NULL, "
                "fee_policy_revision TEXT NOT NULL, slippage_policy_revision TEXT NOT NULL, "
                "rounding_policy_revision TEXT NOT NULL, profile_hash TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE journal_events("
                "event_id TEXT PRIMARY KEY, sequence_no INTEGER UNIQUE NOT NULL, execution_id TEXT NOT NULL, "
                "order_id TEXT NOT NULL, event_kind TEXT NOT NULL, profile_revision_id TEXT NOT NULL, "
                "observed_time_us INTEGER NOT NULL, execution_time_us INTEGER NOT NULL, fill_quantity TEXT NOT NULL, "
                "effective_price TEXT NOT NULL, gross_commitment TEXT NOT NULL, fee_amount TEXT NOT NULL, "
                "fee_asset TEXT NOT NULL, slippage_reference TEXT NOT NULL, rounding_policy_revision TEXT NOT NULL, "
                "payload TEXT NOT NULL, payload_hash TEXT NOT NULL, event_state TEXT NOT NULL, "
                "FOREIGN KEY(profile_revision_id) REFERENCES profile_revisions(revision_id), "
                "CHECK(event_state IN ('ACCEPTED','LATE','UNKNOWN','CONFLICT','QUARANTINED')))"
            )
            db.execute(
                "CREATE TABLE reservations("
                "reservation_id TEXT PRIMARY KEY, owner_scope TEXT NOT NULL, asset TEXT NOT NULL, "
                "reserved_amount TEXT NOT NULL, consumed_amount TEXT NOT NULL, releasable_amount TEXT NOT NULL, "
                "release_identity TEXT, terminal_state TEXT NOT NULL, version INTEGER NOT NULL, "
                "source_event_id TEXT, release_cursor INTEGER NOT NULL, "
                "FOREIGN KEY(source_event_id) REFERENCES journal_events(event_id))"
            )
            db.execute(
                "CREATE TABLE reservation_releases("
                "release_identity TEXT PRIMARY KEY, reservation_id TEXT NOT NULL, "
                "transition_event_id TEXT NOT NULL, release_cursor INTEGER NOT NULL, "
                "expected_version INTEGER NOT NULL, transition_kind TEXT NOT NULL, "
                "consumed_amount TEXT NOT NULL, releasable_amount TEXT NOT NULL, "
                "target_state TEXT NOT NULL, payload TEXT NOT NULL, payload_hash TEXT NOT NULL, "
                "FOREIGN KEY(reservation_id) REFERENCES reservations(reservation_id), "
                "UNIQUE(reservation_id, release_cursor))"
            )
            db.execute(
                "CREATE TABLE economic_postings("
                "posting_id TEXT PRIMARY KEY, source_event_id TEXT UNIQUE NOT NULL, posting_cursor INTEGER NOT NULL, "
                "commitment TEXT NOT NULL, fee_amount TEXT NOT NULL, funding_amount TEXT NOT NULL, "
                "posting_state TEXT NOT NULL, checksum TEXT NOT NULL, "
                "FOREIGN KEY(source_event_id) REFERENCES journal_events(event_id))"
            )
            db.execute(
                "CREATE TABLE core_replay_receipts("
                "mapping_id TEXT NOT NULL, event_id TEXT NOT NULL, posting_id TEXT NOT NULL, "
                "transition_event_id TEXT NOT NULL, release_identity TEXT NOT NULL, "
                "release_cursor INTEGER NOT NULL CHECK(release_cursor > 0), "
                "fingerprint TEXT PRIMARY KEY CHECK(length(fingerprint)=64), "
                "UNIQUE(mapping_id, event_id, posting_id, transition_event_id, release_identity, release_cursor), "
                "FOREIGN KEY(event_id) REFERENCES journal_events(event_id), "
                "FOREIGN KEY(posting_id) REFERENCES economic_postings(posting_id), "
                "FOREIGN KEY(transition_event_id) REFERENCES journal_events(event_id), "
                "FOREIGN KEY(release_identity) REFERENCES reservation_releases(release_identity))"
            )
            db.execute("COMMIT")
        except BaseException:
            db.execute("ROLLBACK")
            raise
        db.close()
        return target
    except FuturesDcaJournalSchemaError:
        raise
    except (OSError, sqlite3.Error) as exc:
        if "db" in locals():
            db.close()
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_JOURNAL_UNAVAILABLE", "Journal schema oluşturulamadı.") from exc


def append_profile_revision(path: Path, revision: FuturesDcaProfileRevision) -> str:
    """Persist one immutable profile revision, or return an exact duplicate."""

    normalized = _normalize_profile(revision)
    db = _open_existing(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        try:
            payload = _profile_payload(normalized)
            profile_hash = _digest(payload)
            prior = db.execute(
                "SELECT revision_id, venue, product, symbol, settlement_asset, margin_mode, position_mode, "
                "effective_time_us, contract_size, fee_policy_revision, slippage_policy_revision, "
                "rounding_policy_revision, profile_hash FROM profile_revisions WHERE revision_id=?",
                (normalized.revision_id,),
            ).fetchone()
            values = (*_profile_values(normalized), profile_hash)
            if prior is not None:
                if prior != values:
                    raise FuturesDcaJournalSchemaError("FUTURES_DCA_PROFILE_CONFLICT", "Profile revision farklı payload ile kullanılamaz.")
                db.execute("COMMIT")
                return "DUPLICATE"
            db.execute(
                "INSERT INTO profile_revisions(" 
                "revision_id, venue, product, symbol, settlement_asset, margin_mode, position_mode, "
                "effective_time_us, contract_size, fee_policy_revision, slippage_policy_revision, "
                "rounding_policy_revision, profile_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                values,
            )
            db.execute("COMMIT")
            return "ACCEPTED"
        except BaseException:
            db.execute("ROLLBACK")
            raise
    finally:
        db.close()


def load_profile_revisions(path: Path) -> tuple[FuturesDcaProfileRevision, ...]:
    """Replay and verify all immutable profile revisions in the journal."""

    db = _open_existing(path)
    try:
        rows = db.execute(
            "SELECT revision_id, venue, product, symbol, settlement_asset, margin_mode, position_mode, "
            "effective_time_us, contract_size, fee_policy_revision, slippage_policy_revision, "
            "rounding_policy_revision, profile_hash FROM profile_revisions ORDER BY effective_time_us, revision_id"
        ).fetchall()
        result = []
        for row in rows:
            revision = _normalize_profile(FuturesDcaProfileRevision(*row[:-1]))
            if _digest(_profile_payload(revision)) != row[-1]:
                raise FuturesDcaJournalSchemaError("FUTURES_DCA_PROFILE_CORRUPT", "Profile revision checksum doğrulanamadı.")
            result.append(revision)
        return tuple(result)
    except FuturesDcaJournalSchemaError:
        raise
    except (TypeError, ValueError, sqlite3.Error) as exc:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_PROFILE_CORRUPT", "Profile revision replay edilemedi.") from exc
    finally:
        db.close()


def append_journal_event(path: Path, event: FuturesDcaEventEnvelope) -> str:
    """Persist one profile-bound event without touching reservations or postings."""

    normalized = _normalize_event(event)
    db = _open_existing(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        try:
            result = _append_event_unlocked(db, normalized)
            db.execute("COMMIT")
            return result
        except BaseException:
            db.execute("ROLLBACK")
            raise
    finally:
        db.close()


def load_journal_events(path: Path) -> tuple[FuturesDcaEventEnvelope, ...]:
    """Replay profile-bound events and verify sequence, identity and checksum."""

    db = _open_existing(path)
    try:
        rows = db.execute(
            "SELECT event_id, sequence_no, execution_id, order_id, event_kind, profile_revision_id, "
            "observed_time_us, execution_time_us, fill_quantity, effective_price, gross_commitment, fee_amount, "
            "fee_asset, slippage_reference, rounding_policy_revision, payload, payload_hash, event_state "
            "FROM journal_events ORDER BY sequence_no"
        ).fetchall()
        result = []
        seen_execution = set()
        for expected_sequence, row in enumerate(rows, start=1):
            event = _normalize_event(FuturesDcaEventEnvelope(*row[:16], event_state=row[17]))
            if event.sequence_no != expected_sequence or event.execution_id in seen_execution:
                raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_CORRUPT", "Event sequence veya execution identity bozulmuş.")
            if _digest(event.payload) != row[16]:
                raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_CORRUPT", "Event checksum doğrulanamadı.")
            if db.execute("SELECT 1 FROM profile_revisions WHERE revision_id=?", (event.profile_revision_id,)).fetchone() is None:
                raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_CORRUPT", "Event profile revision bulunamadı.")
            seen_execution.add(event.execution_id)
            result.append(event)
        return tuple(result)
    except FuturesDcaJournalSchemaError:
        raise
    except (TypeError, ValueError, sqlite3.Error) as exc:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_CORRUPT", "Event replay edilemedi.") from exc
    finally:
        db.close()


def append_reservation_projection(path: Path, reservation: FuturesDcaReservationProjection) -> str:
    """Persist one exact reservation projection without release or posting decisions."""

    normalized = _normalize_reservation(reservation)
    db = _open_existing(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        try:
            result = _append_reservation_unlocked(db, normalized)
            db.execute("COMMIT")
            return result
        except BaseException:
            db.execute("ROLLBACK")
            raise
    finally:
        db.close()


def append_event_and_reservation_atomic(
    path: Path,
    event: FuturesDcaEventEnvelope,
    reservation: FuturesDcaReservationProjection,
) -> str:
    """Append one linked event and reservation in one bounded journal transaction."""

    normalized_event = _normalize_event(event)
    normalized_reservation = _normalize_reservation(reservation)
    if normalized_reservation.source_event_id != normalized_event.event_id:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_ATOMIC_SOURCE_MISMATCH", "Reservation source event atomic event ile eşleşmelidir."
        )
    db = _open_existing(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        try:
            event_result = _append_event_unlocked(db, normalized_event)
            reservation_result = _append_reservation_unlocked(db, normalized_reservation)
            db.execute("COMMIT")
            return "DUPLICATE" if event_result == reservation_result == "DUPLICATE" else "ACCEPTED"
        except BaseException:
            db.execute("ROLLBACK")
            raise
    finally:
        db.close()


def append_event_reservation_and_posting_atomic(
    path: Path,
    event: FuturesDcaEventEnvelope,
    reservation: FuturesDcaReservationProjection,
    posting: FuturesDcaEconomicPosting,
) -> str:
    """Append one accepted event, release projection, and posting cursor atomically."""

    normalized_event = _normalize_event(event)
    normalized_reservation = _normalize_reservation(reservation)
    normalized_posting = _normalize_posting(posting)
    if normalized_event.event_state != "ACCEPTED":
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_POSTING_EVENT_NOT_ACCEPTED", "Economic posting yalnız ACCEPTED event’e bağlanabilir."
        )
    if normalized_reservation.source_event_id != normalized_event.event_id:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_ATOMIC_SOURCE_MISMATCH", "Reservation source event atomic event ile eşleşmelidir."
        )
    if normalized_posting.source_event_id != normalized_event.event_id:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_POSTING_SOURCE_MISMATCH", "Posting source event atomic event ile eşleşmelidir."
        )
    if normalized_posting.commitment != normalized_event.gross_commitment:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_POSTING_COMMITMENT_MISMATCH", "Posting commitment event gross commitment ile eşleşmelidir."
        )
    if normalized_posting.fee_amount != normalized_event.fee_amount:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_POSTING_FEE_MISMATCH", "Posting fee event fee amount ile eşleşmelidir."
        )
    db = _open_existing(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        try:
            event_result = _append_event_unlocked(db, normalized_event)
            reservation_result = _append_reservation_unlocked(db, normalized_reservation)
            posting_result = _append_posting_unlocked(db, normalized_posting)
            db.execute("COMMIT")
            return "DUPLICATE" if event_result == reservation_result == posting_result == "DUPLICATE" else "ACCEPTED"
        except BaseException:
            db.execute("ROLLBACK")
            raise
    finally:
        db.close()


def _append_event_unlocked(db: sqlite3.Connection, event: FuturesDcaEventEnvelope) -> str:
    if db.execute("SELECT 1 FROM profile_revisions WHERE revision_id=?", (event.profile_revision_id,)).fetchone() is None:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_PROFILE_MISSING", "Event profile revision bulunamadı.")
    payload_hash = _digest(event.payload)
    prior = db.execute(
        "SELECT event_id, sequence_no, execution_id, order_id, event_kind, profile_revision_id, "
        "observed_time_us, execution_time_us, fill_quantity, effective_price, gross_commitment, fee_amount, "
        "fee_asset, slippage_reference, rounding_policy_revision, payload, payload_hash, event_state "
        "FROM journal_events WHERE event_id=?",
        (event.event_id,),
    ).fetchone()
    values = _event_row(event, payload_hash)
    if prior is not None:
        if prior != values:
            raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_CONFLICT", "Event identity farklı payload ile kullanılamaz.")
        return "DUPLICATE"
    if db.execute("SELECT 1 FROM journal_events WHERE execution_id=?", (event.execution_id,)).fetchone() is not None:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_EXECUTION_CONFLICT", "Execution identity ikinci event’e bağlanamaz.")
    next_sequence = db.execute("SELECT COALESCE(MAX(sequence_no), 0) + 1 FROM journal_events").fetchone()[0]
    if event.sequence_no != next_sequence:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_SEQUENCE_INVALID", "Event sırası ardışık olmalıdır.")
    db.execute(
        "INSERT INTO journal_events(" 
        "event_id, sequence_no, execution_id, order_id, event_kind, profile_revision_id, observed_time_us, "
        "execution_time_us, fill_quantity, effective_price, gross_commitment, fee_amount, fee_asset, "
        "slippage_reference, rounding_policy_revision, payload, payload_hash, event_state) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        values,
    )
    return "ACCEPTED"


def _append_reservation_unlocked(db: sqlite3.Connection, reservation: FuturesDcaReservationProjection) -> str:
    if reservation.source_event_id is not None and db.execute(
        "SELECT 1 FROM journal_events WHERE event_id=?", (reservation.source_event_id,)
    ).fetchone() is None:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RESERVATION_EVENT_MISSING", "Reservation source event bulunamadı."
        )
    prior = db.execute(
        "SELECT reservation_id, owner_scope, asset, reserved_amount, consumed_amount, "
        "releasable_amount, release_identity, terminal_state, version, source_event_id, release_cursor "
        "FROM reservations WHERE reservation_id=?",
        (reservation.reservation_id,),
    ).fetchone()
    values = _reservation_values(reservation)
    if prior is not None:
        if prior != values:
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_RESERVATION_CONFLICT", "Reservation identity farklı payload ile kullanılamaz."
            )
        return "DUPLICATE"
    db.execute(
        "INSERT INTO reservations(" 
        "reservation_id, owner_scope, asset, reserved_amount, consumed_amount, releasable_amount, "
        "release_identity, terminal_state, version, source_event_id, release_cursor) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        values,
    )
    return "ACCEPTED"


def _append_posting_unlocked(db: sqlite3.Connection, posting: FuturesDcaEconomicPosting) -> str:
    if db.execute("SELECT 1 FROM journal_events WHERE event_id=?", (posting.source_event_id,)).fetchone() is None:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_POSTING_EVENT_MISSING", "Posting source event bulunamadı."
        )
    payload = _posting_payload(posting)
    checksum = _digest(payload)
    prior = db.execute(
        "SELECT posting_id, source_event_id, posting_cursor, commitment, fee_amount, funding_amount, "
        "posting_state, checksum FROM economic_postings WHERE posting_id=?",
        (posting.posting_id,),
    ).fetchone()
    values = (*_posting_values(posting), checksum)
    if prior is not None:
        if prior != values:
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_POSTING_CONFLICT", "Posting identity farklı payload ile kullanılamaz."
            )
        return "DUPLICATE"
    if db.execute(
        "SELECT 1 FROM economic_postings WHERE source_event_id=?", (posting.source_event_id,)
    ).fetchone() is not None:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_POSTING_SOURCE_CONFLICT", "Event ikinci economic posting’e bağlanamaz."
        )
    next_cursor = db.execute("SELECT COALESCE(MAX(posting_cursor), 0) + 1 FROM economic_postings").fetchone()[0]
    if posting.posting_cursor != next_cursor:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_POSTING_CURSOR_INVALID", "Posting cursor ardışık olmalıdır."
        )
    db.execute(
        "INSERT INTO economic_postings(" 
        "posting_id, source_event_id, posting_cursor, commitment, fee_amount, funding_amount, posting_state, checksum) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        values,
    )
    return "ACCEPTED"


def load_reservation_projections(path: Path) -> tuple[FuturesDcaReservationProjection, ...]:
    """Replay exact reservation projections and verify their event references."""

    db = _open_existing(path)
    try:
        rows = db.execute(
            "SELECT reservation_id, owner_scope, asset, reserved_amount, consumed_amount, "
            "releasable_amount, release_identity, terminal_state, version, source_event_id, release_cursor "
            "FROM reservations ORDER BY reservation_id"
        ).fetchall()
        result = []
        for row in rows:
            reservation = _normalize_reservation(FuturesDcaReservationProjection(*row))
            if reservation.source_event_id is not None and db.execute(
                "SELECT 1 FROM journal_events WHERE event_id=?", (reservation.source_event_id,)
            ).fetchone() is None:
                raise FuturesDcaJournalSchemaError(
                    "FUTURES_DCA_RESERVATION_CORRUPT", "Reservation source event bulunamadı."
                )
            result.append(reservation)
        return tuple(result)
    except FuturesDcaJournalSchemaError:
        raise
    except (TypeError, ValueError, sqlite3.Error) as exc:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RESERVATION_CORRUPT", "Reservation projection replay edilemedi."
        ) from exc
    finally:
        db.close()


def load_economic_postings(path: Path) -> tuple[FuturesDcaEconomicPosting, ...]:
    """Replay posting cursors and verify source event, order, and checksums."""

    db = _open_existing(path)
    try:
        rows = db.execute(
            "SELECT posting_id, source_event_id, posting_cursor, commitment, fee_amount, funding_amount, "
            "posting_state, checksum FROM economic_postings ORDER BY posting_cursor"
        ).fetchall()
        result = []
        for expected_cursor, row in enumerate(rows, start=1):
            posting = _normalize_posting(FuturesDcaEconomicPosting(*row[:7]))
            if posting.posting_cursor != expected_cursor or _digest(_posting_payload(posting)) != row[7]:
                raise FuturesDcaJournalSchemaError(
                    "FUTURES_DCA_POSTING_CORRUPT", "Economic posting cursor veya checksum doğrulanamadı."
                )
            event = db.execute(
                "SELECT event_state, gross_commitment, fee_amount FROM journal_events WHERE event_id=?",
                (posting.source_event_id,),
            ).fetchone()
            if (
                event is None
                or event[0] != "ACCEPTED"
                or event[1] != posting.commitment
                or event[2] != posting.fee_amount
            ):
                raise FuturesDcaJournalSchemaError(
                    "FUTURES_DCA_POSTING_CORRUPT", "Posting accepted event ekonomik alanlarıyla eşleşmiyor."
                )
            result.append(posting)
        return tuple(result)
    except FuturesDcaJournalSchemaError:
        raise
    except (TypeError, ValueError, sqlite3.Error) as exc:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_POSTING_CORRUPT", "Economic posting replay edilemedi."
        ) from exc
    finally:
        db.close()


def _validate_path(path: Path) -> Path:
    target = Path(path)
    resolved = target.resolve()
    if "YEDEK_ESKI_PROJE" in resolved.parts or any(item.is_symlink() for item in (target, *target.parents)):
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_JOURNAL_PATH_UNSAFE", "Journal backup/linked path üzerinde olamaz.")
    if not resolved.parent.is_dir() or (target.exists() and not target.is_file()):
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_JOURNAL_PATH_INVALID", "Journal yolu geçersiz.")
    return target


def _open_existing(path: Path) -> sqlite3.Connection:
    target = _validate_path(path)
    if not target.is_file():
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_JOURNAL_MISSING", "Journal bulunamadı.")
    try:
        db = sqlite3.connect(target.resolve().as_uri() + "?mode=rw", uri=True, isolation_level=None)
        if (
            db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
            or db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION
        ):
            raise FuturesDcaJournalSchemaError("FUTURES_DCA_JOURNAL_UNSUPPORTED", "Journal schema desteklenmiyor.")
        return db
    except FuturesDcaJournalSchemaError:
        if "db" in locals():
            db.close()
        raise
    except sqlite3.Error as exc:
        if "db" in locals():
            db.close()
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_JOURNAL_UNAVAILABLE", "Journal açılamadı.") from exc


def _normalize_profile(revision: FuturesDcaProfileRevision) -> FuturesDcaProfileRevision:
    if not isinstance(revision, FuturesDcaProfileRevision):
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_PROFILE_INVALID", "Profile revision güvenli tipte değil.")
    for value in (
        revision.revision_id,
        revision.venue,
        revision.product,
        revision.symbol,
        revision.settlement_asset,
        revision.margin_mode,
        revision.position_mode,
        revision.fee_policy_revision,
        revision.slippage_policy_revision,
        revision.rounding_policy_revision,
    ):
        if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
            raise FuturesDcaJournalSchemaError("FUTURES_DCA_PROFILE_INVALID", "Profile revision identity geçersiz.")
    if type(revision.effective_time_us) is not int or revision.effective_time_us < 0:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_PROFILE_INVALID", "Profile effective time geçersiz.")
    try:
        contract_size = exact_text(positive(revision.contract_size))
    except (TypeError, ValueError) as exc:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_PROFILE_INVALID", "Contract-size exact pozitif değer olmalıdır.") from exc
    return FuturesDcaProfileRevision(
        revision.revision_id,
        revision.venue,
        revision.product,
        revision.symbol,
        revision.settlement_asset,
        revision.margin_mode,
        revision.position_mode,
        revision.effective_time_us,
        contract_size,
        revision.fee_policy_revision,
        revision.slippage_policy_revision,
        revision.rounding_policy_revision,
    )


def _profile_values(revision: FuturesDcaProfileRevision) -> tuple[object, ...]:
    return (
        revision.revision_id,
        revision.venue,
        revision.product,
        revision.symbol,
        revision.settlement_asset,
        revision.margin_mode,
        revision.position_mode,
        revision.effective_time_us,
        revision.contract_size,
        revision.fee_policy_revision,
        revision.slippage_policy_revision,
        revision.rounding_policy_revision,
    )


def _profile_payload(revision: FuturesDcaProfileRevision) -> str:
    return json.dumps(dict(zip(
        ("revision_id", "venue", "product", "symbol", "settlement_asset", "margin_mode", "position_mode", "effective_time_us", "contract_size", "fee_policy_revision", "slippage_policy_revision", "rounding_policy_revision"),
        _profile_values(revision),
    )), ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_event(event: FuturesDcaEventEnvelope) -> FuturesDcaEventEnvelope:
    if not isinstance(event, FuturesDcaEventEnvelope):
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_INVALID", "Event envelope güvenli tipte değil.")
    for value in (
        event.event_id,
        event.execution_id,
        event.order_id,
        event.event_kind,
        event.profile_revision_id,
        event.fee_asset,
        event.slippage_reference,
        event.rounding_policy_revision,
    ):
        if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
            raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_INVALID", "Event identity geçersiz.")
    if type(event.sequence_no) is not int or event.sequence_no < 1:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_INVALID", "Event sequence geçersiz.")
    if type(event.observed_time_us) is not int or event.observed_time_us < 0 or type(event.execution_time_us) is not int or event.execution_time_us < 0:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_INVALID", "Event zamanı geçersiz.")
    try:
        fill_quantity = exact_text(positive(event.fill_quantity))
        effective_price = exact_text(positive(event.effective_price))
        gross_commitment = exact_text(positive(event.gross_commitment))
        fee_amount = exact_text(_nonnegative(event.fee_amount))
    except (TypeError, ValueError) as exc:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_INVALID", "Event ekonomik alanları exact olmalıdır.") from exc
    if event.event_state not in _EVENT_STATES or not isinstance(event.payload, str):
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_INVALID", "Event state veya payload geçersiz.")
    try:
        parsed = json.loads(event.payload)
        payload = json.dumps(parsed, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_INVALID", "Event payload canonical JSON olmalıdır.") from exc
    if payload != event.payload:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_EVENT_INVALID", "Event payload canonical JSON değildir.")
    return FuturesDcaEventEnvelope(
        event.event_id,
        event.sequence_no,
        event.execution_id,
        event.order_id,
        event.event_kind,
        event.profile_revision_id,
        event.observed_time_us,
        event.execution_time_us,
        fill_quantity,
        effective_price,
        gross_commitment,
        fee_amount,
        event.fee_asset,
        event.slippage_reference,
        event.rounding_policy_revision,
        payload,
        event.event_state,
    )


def _nonnegative(value: str):
    result = number(value)
    if result < 0:
        raise ValueError("Expected non-negative value")
    return result


def _normalize_reservation(reservation: FuturesDcaReservationProjection) -> FuturesDcaReservationProjection:
    if not isinstance(reservation, FuturesDcaReservationProjection):
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_RESERVATION_INVALID", "Reservation güvenli tipte değil.")
    for value in (reservation.reservation_id, reservation.owner_scope, reservation.asset, reservation.terminal_state):
        if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
            raise FuturesDcaJournalSchemaError("FUTURES_DCA_RESERVATION_INVALID", "Reservation identity geçersiz.")
    for value in (reservation.release_identity, reservation.source_event_id):
        if value is not None and (not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None):
            raise FuturesDcaJournalSchemaError("FUTURES_DCA_RESERVATION_INVALID", "Reservation reference geçersiz.")
    if type(reservation.version) is not int or reservation.version < 0:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_RESERVATION_INVALID", "Reservation version geçersiz.")
    if type(reservation.release_cursor) is not int or reservation.release_cursor < 0:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_RESERVATION_INVALID", "Release cursor geçersiz.")
    if (reservation.release_cursor == 0) != (reservation.release_identity is None):
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RELEASE_IDENTITY_INVALID", "Release identity ve cursor birlikte ilerlemelidir."
        )
    try:
        amounts = tuple(exact_text(_nonnegative(value)) for value in (
            reservation.reserved_amount,
            reservation.consumed_amount,
            reservation.releasable_amount,
        ))
    except (TypeError, ValueError) as exc:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RESERVATION_INVALID", "Reservation ekonomik alanları exact ve negatif olmayan değerler olmalıdır."
        ) from exc
    return FuturesDcaReservationProjection(
        reservation.reservation_id,
        reservation.owner_scope,
        reservation.asset,
        *amounts,
        reservation.release_identity,
        reservation.terminal_state,
        reservation.version,
        reservation.source_event_id,
        reservation.release_cursor,
    )


def _normalize_posting(posting: FuturesDcaEconomicPosting) -> FuturesDcaEconomicPosting:
    if not isinstance(posting, FuturesDcaEconomicPosting):
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_POSTING_INVALID", "Economic posting güvenli tipte değil.")
    for value in (posting.posting_id, posting.source_event_id, posting.posting_state):
        if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
            raise FuturesDcaJournalSchemaError("FUTURES_DCA_POSTING_INVALID", "Posting identity geçersiz.")
    if type(posting.posting_cursor) is not int or posting.posting_cursor < 1:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_POSTING_INVALID", "Posting cursor geçersiz.")
    try:
        commitment = exact_text(positive(posting.commitment))
        fee_amount = exact_text(_nonnegative(posting.fee_amount))
        funding_amount = exact_text(number(posting.funding_amount))
    except (TypeError, ValueError) as exc:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_POSTING_INVALID", "Posting ekonomik alanları exact olmalıdır."
        ) from exc
    return FuturesDcaEconomicPosting(
        posting.posting_id,
        posting.source_event_id,
        posting.posting_cursor,
        commitment,
        fee_amount,
        funding_amount,
        posting.posting_state,
    )


def _posting_payload(posting: FuturesDcaEconomicPosting) -> str:
    return json.dumps(dict(zip(
        ("posting_id", "source_event_id", "posting_cursor", "commitment", "fee_amount", "funding_amount", "posting_state"),
        _posting_values(posting),
    )), ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _posting_values(posting: FuturesDcaEconomicPosting) -> tuple[object, ...]:
    return (
        posting.posting_id,
        posting.source_event_id,
        posting.posting_cursor,
        posting.commitment,
        posting.fee_amount,
        posting.funding_amount,
        posting.posting_state,
    )


def _reservation_values(reservation: FuturesDcaReservationProjection) -> tuple[object, ...]:
    return (
        reservation.reservation_id,
        reservation.owner_scope,
        reservation.asset,
        reservation.reserved_amount,
        reservation.consumed_amount,
        reservation.releasable_amount,
        reservation.release_identity,
        reservation.terminal_state,
        reservation.version,
        reservation.source_event_id,
        reservation.release_cursor,
    )


def _event_row(event: FuturesDcaEventEnvelope, payload_hash: str) -> tuple[object, ...]:
    return (
        event.event_id,
        event.sequence_no,
        event.execution_id,
        event.order_id,
        event.event_kind,
        event.profile_revision_id,
        event.observed_time_us,
        event.execution_time_us,
        event.fill_quantity,
        event.effective_price,
        event.gross_commitment,
        event.fee_amount,
        event.fee_asset,
        event.slippage_reference,
        event.rounding_policy_revision,
        event.payload,
        payload_hash,
        event.event_state,
    )
