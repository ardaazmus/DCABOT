"""Durable atomic release transitions for the greenfield Futures DCA journal."""

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3

from dcabot.application.futures_dca_core_mapping import FuturesDcaCoreReplayReceipt
from .futures_dca_journal_schema import (
    FuturesDcaEconomicPosting,
    FuturesDcaEventEnvelope,
    FuturesDcaJournalSchemaError,
    FuturesDcaReservationProjection,
    _append_event_unlocked,
    _append_posting_unlocked,
    _digest,
    _normalize_event,
    _normalize_posting,
    _normalize_reservation,
    _open_existing,
)
from .futures_dca_core_replay_store import _append_core_replay_receipt_unlocked
from dcabot.domain.numbers import number
from .futures_dca_release_transition import (
    FuturesDcaReleaseTransition,
    apply_futures_dca_release_transition,
)


@dataclass(frozen=True, slots=True)
class FuturesDcaReleaseRecord:
    """Immutable durable release transition and its resulting state."""

    transition: FuturesDcaReleaseTransition
    target_state: str


def append_futures_dca_release_transition(
    path: Path,
    transition: FuturesDcaReleaseTransition,
) -> str:
    """Persist one release transition with its reservation projection atomically."""

    db = _open_existing(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        try:
            current = _load_reservation_unlocked(db, transition.reservation_id)
            _require_release_history_aligned(db, current)
            _require_transition_event(db, transition)
            candidate, outcome = apply_futures_dca_release_transition(current, transition)
            if outcome == "DUPLICATE":
                _verify_duplicate_record(db, transition, candidate.terminal_state)
                db.execute("COMMIT")
                return outcome
            _persist_release_unlocked(db, current, transition, candidate)
            db.execute("COMMIT")
            return outcome
        except BaseException:
            db.execute("ROLLBACK")
            raise
    finally:
        db.close()


def append_futures_dca_fill_release_and_posting_atomic(
    path: Path,
    event: FuturesDcaEventEnvelope,
    transition: FuturesDcaReleaseTransition,
    posting: FuturesDcaEconomicPosting,
) -> str:
    """Atomically bind an accepted fill event, release, reservation, and posting."""

    normalized_event = _normalize_event(event)
    normalized_posting = _normalize_posting(posting)
    _validate_fill_release_posting_binding(normalized_event, transition, normalized_posting)

    db = _open_existing(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        try:
            result = _append_futures_dca_fill_release_and_posting_unlocked(
                db, normalized_event, transition, normalized_posting
            )
            db.execute("COMMIT")
            return result[0]
        except BaseException:
            db.execute("ROLLBACK")
            raise
    finally:
        db.close()


def append_futures_dca_core_replay_receipt_atomic(
    path: Path,
    event: FuturesDcaEventEnvelope,
    transition: FuturesDcaReleaseTransition,
    posting: FuturesDcaEconomicPosting,
    receipt: FuturesDcaCoreReplayReceipt,
) -> str:
    """Atomically bind one fill, release, posting and CORE01 replay receipt."""

    normalized_event = _normalize_event(event)
    normalized_posting = _normalize_posting(posting)
    _validate_fill_release_posting_binding(normalized_event, transition, normalized_posting)
    if not isinstance(receipt, FuturesDcaCoreReplayReceipt):
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_CORE_REPLAY_RECEIPT_INVALID",
            "Replay receipt güvenli tipte değil.",
        )
    if (
        receipt.event_id != normalized_event.event_id
        or receipt.posting_id != normalized_posting.posting_id
        or receipt.transition_event_id != transition.transition_event_id
        or receipt.release_identity != transition.release_identity
        or receipt.release_cursor != transition.release_cursor
    ):
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_CORE_REPLAY_RECEIPT_SCOPE_CONFLICT",
            "Replay receipt event, posting ve release scope ile eşleşmelidir.",
        )

    db = _open_existing(path)
    db.execute("PRAGMA foreign_keys=ON")
    try:
        db.execute("BEGIN IMMEDIATE")
        try:
            results = _append_futures_dca_fill_release_and_posting_unlocked(
                db, normalized_event, transition, normalized_posting
            )
            receipt_result = _append_core_replay_receipt_unlocked(db, receipt)
            all_results = (*results, receipt_result)
            if len(set(all_results)) != 1:
                raise FuturesDcaJournalSchemaError(
                    "FUTURES_DCA_CORE_REPLAY_ATOMIC_STATE_CONFLICT",
                    "Event, release, posting ve receipt kısmi duplicate durumunda birlikte kabul edilemez.",
                )
            db.execute("COMMIT")
            return all_results[0]
        except BaseException:
            db.execute("ROLLBACK")
            raise
    finally:
        db.close()


def _validate_fill_release_posting_binding(
    normalized_event: FuturesDcaEventEnvelope,
    transition: FuturesDcaReleaseTransition,
    normalized_posting: FuturesDcaEconomicPosting,
) -> None:
    if not isinstance(transition, FuturesDcaReleaseTransition):
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RELEASE_POSTING_TRANSITION_INVALID", "Release transition güvenli tipte değil."
        )
    if normalized_event.event_state != "ACCEPTED":
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RELEASE_POSTING_EVENT_NOT_ACCEPTED", "Economic fill posting yalnız ACCEPTED event’e bağlanabilir."
        )
    if transition.transition_event_id != normalized_event.event_id:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RELEASE_POSTING_EVENT_MISMATCH", "Release transition event’i fill event’iyle eşleşmelidir."
        )
    if transition.transition_kind not in {"PARTIAL_FILL", "FULL_FILL"}:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RELEASE_POSTING_TRANSITION_INVALID", "Economic posting yalnız fill transition’a bağlanabilir."
        )
    if normalized_posting.source_event_id != normalized_event.event_id:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_POSTING_SOURCE_MISMATCH", "Posting source event fill event’iyle eşleşmelidir."
        )
    if normalized_posting.commitment != normalized_event.gross_commitment:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_POSTING_COMMITMENT_MISMATCH", "Posting commitment fill event gross commitment ile eşleşmelidir."
        )
    if normalized_posting.fee_amount != normalized_event.fee_amount:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_POSTING_FEE_MISMATCH", "Posting fee fill event fee amount ile eşleşmelidir."
        )


def _append_futures_dca_fill_release_and_posting_unlocked(
    db: sqlite3.Connection,
    normalized_event: FuturesDcaEventEnvelope,
    transition: FuturesDcaReleaseTransition,
    normalized_posting: FuturesDcaEconomicPosting,
) -> tuple[str, str, str]:
    current = _load_reservation_unlocked(db, transition.reservation_id)
    _require_release_history_aligned(db, current)
    candidate, release_result = apply_futures_dca_release_transition(current, transition)
    if release_result != "DUPLICATE" and number(candidate.consumed_amount) - number(
        current.consumed_amount
    ) != number(normalized_event.gross_commitment):
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RELEASE_POSTING_AMOUNT_MISMATCH",
            "Fill event gross commitment reservation consumed delta ile eşleşmelidir.",
        )
    event_result = _append_event_unlocked(db, normalized_event)
    if release_result == "DUPLICATE":
        _verify_duplicate_record(db, transition, candidate.terminal_state)
    else:
        _persist_release_unlocked(db, current, transition, candidate)
    posting_result = _append_posting_unlocked(db, normalized_posting)
    results = (event_result, release_result, posting_result)
    if len(set(results)) != 1:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RELEASE_POSTING_STATE_CONFLICT",
            "Event, release ve posting kısmi duplicate durumunda birlikte kabul edilemez.",
        )
    return results


def load_futures_dca_release_transitions(path: Path) -> tuple[FuturesDcaReleaseRecord, ...]:
    """Replay release history, checksums, cursors and final reservation projections."""

    db = _open_existing(path)
    try:
        rows = db.execute(
            "SELECT release_identity, reservation_id, transition_event_id, release_cursor, expected_version, "
            "transition_kind, consumed_amount, releasable_amount, target_state, payload, payload_hash "
            "FROM reservation_releases ORDER BY reservation_id, release_cursor"
        ).fetchall()
        result = []
        by_reservation: dict[str, list[tuple[object, ...]]] = {}
        for row in rows:
            transition = FuturesDcaReleaseTransition(
                row[1], row[2], row[0], row[3], row[4], row[5], row[6], row[7]
            )
            payload = _release_payload(transition, row[8])
            if payload != row[9] or _digest(payload) != row[10]:
                raise FuturesDcaJournalSchemaError(
                    "FUTURES_DCA_RELEASE_CORRUPT", "Release transition checksum doğrulanamadı."
                )
            by_reservation.setdefault(transition.reservation_id, []).append(row)
            result.append(FuturesDcaReleaseRecord(transition, row[8]))
        for reservation_id, history in by_reservation.items():
            reservation = _load_reservation_unlocked(db, reservation_id)
            if not history or history[0][3] != 1:
                raise FuturesDcaJournalSchemaError(
                    "FUTURES_DCA_RELEASE_CORRUPT", "Release cursor geçmişi 1’den başlamıyor."
                )
            for expected_cursor, row in enumerate(history, start=1):
                if row[3] != expected_cursor or row[4] != row[3] - 1:
                    raise FuturesDcaJournalSchemaError(
                        "FUTURES_DCA_RELEASE_CORRUPT", "Release cursor veya version geçmişi ardışık değil."
                    )
            last = history[-1]
            if (
                reservation.release_identity,
                reservation.release_cursor,
                reservation.version,
                reservation.terminal_state,
                reservation.consumed_amount,
                reservation.releasable_amount,
            ) != (last[0], last[3], last[4] + 1, last[8], last[6], last[7]):
                raise FuturesDcaJournalSchemaError(
                    "FUTURES_DCA_RELEASE_CORRUPT", "Reservation son projection ile release history eşleşmiyor."
                )
        return tuple(result)
    except FuturesDcaJournalSchemaError:
        raise
    except (TypeError, ValueError, sqlite3.Error) as exc:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RELEASE_CORRUPT", "Release transition replay edilemedi."
        ) from exc
    finally:
        db.close()


def _load_reservation_unlocked(
    db: sqlite3.Connection,
    reservation_id: str,
) -> FuturesDcaReservationProjection:
    row = db.execute(
        "SELECT reservation_id, owner_scope, asset, reserved_amount, consumed_amount, "
        "releasable_amount, release_identity, terminal_state, version, source_event_id, release_cursor "
        "FROM reservations WHERE reservation_id=?",
        (reservation_id,),
    ).fetchone()
    if row is None:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RELEASE_RESERVATION_MISSING", "Release reservation bulunamadı."
        )
    return _normalize_reservation(FuturesDcaReservationProjection(*row))


def _require_release_history_aligned(
    db: sqlite3.Connection,
    reservation: FuturesDcaReservationProjection,
) -> None:
    row = db.execute(
        "SELECT COALESCE(MAX(release_cursor), 0), COUNT(*) FROM reservation_releases "
        "WHERE reservation_id=?",
        (reservation.reservation_id,),
    ).fetchone()
    if row != (reservation.release_cursor, reservation.release_cursor):
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RELEASE_HISTORY_MISSING", "Reservation release cursor geçmişiyle uyumsuz."
        )


def _require_transition_event(
    db: sqlite3.Connection,
    transition: FuturesDcaReleaseTransition,
) -> None:
    if db.execute(
        "SELECT 1 FROM journal_events WHERE event_id=?", (transition.transition_event_id,)
    ).fetchone() is None:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RELEASE_EVENT_MISSING", "Release transition event bulunamadı."
        )


def _verify_duplicate_record(
    db: sqlite3.Connection,
    transition: FuturesDcaReleaseTransition,
    target_state: str,
) -> None:
    row = db.execute(
        "SELECT release_identity, reservation_id, transition_event_id, release_cursor, expected_version, "
        "transition_kind, consumed_amount, releasable_amount, target_state, payload, payload_hash "
        "FROM reservation_releases WHERE release_identity=?",
        (transition.release_identity,),
    ).fetchone()
    if row is None or row[:9] != _release_values_without_payload(transition, target_state):
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RELEASE_CONFLICT", "Release identity farklı durable payload ile kullanılamaz."
        )
    payload = _release_payload(transition, target_state)
    if row[9] != payload or row[10] != _digest(payload):
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RELEASE_CORRUPT", "Duplicate release checksum doğrulanamadı."
        )


def _persist_release_unlocked(
    db: sqlite3.Connection,
    current: FuturesDcaReservationProjection,
    transition: FuturesDcaReleaseTransition,
    candidate: FuturesDcaReservationProjection,
) -> None:
    payload = _release_payload(transition, candidate.terminal_state)
    db.execute(
        "INSERT INTO reservation_releases("
        "release_identity, reservation_id, transition_event_id, release_cursor, expected_version, "
        "transition_kind, consumed_amount, releasable_amount, target_state, payload, payload_hash) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        _release_values(transition, candidate.terminal_state, payload),
    )
    updated = db.execute(
        "UPDATE reservations SET consumed_amount=?, releasable_amount=?, release_identity=?, "
        "terminal_state=?, version=?, release_cursor=? WHERE reservation_id=? AND version=? "
        "AND release_cursor=?",
        (
            candidate.consumed_amount,
            candidate.releasable_amount,
            candidate.release_identity,
            candidate.terminal_state,
            candidate.version,
            candidate.release_cursor,
            candidate.reservation_id,
            current.version,
            current.release_cursor,
        ),
    ).rowcount
    if updated != 1:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RELEASE_VERSION_CONFLICT", "Reservation atomic update uygulanamadı."
        )


def _release_payload(transition: FuturesDcaReleaseTransition, target_state: str) -> str:
    return json.dumps(
        {
            "reservation_id": transition.reservation_id,
            "transition_event_id": transition.transition_event_id,
            "release_identity": transition.release_identity,
            "release_cursor": transition.release_cursor,
            "expected_version": transition.expected_version,
            "transition_kind": transition.transition_kind,
            "consumed_amount": transition.consumed_amount,
            "releasable_amount": transition.releasable_amount,
            "target_state": target_state,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _release_values(
    transition: FuturesDcaReleaseTransition,
    target_state: str,
    payload: str,
) -> tuple[object, ...]:
    return (*_release_values_without_payload(transition, target_state), payload, _digest(payload))


def _release_values_without_payload(
    transition: FuturesDcaReleaseTransition,
    target_state: str,
) -> tuple[object, ...]:
    return (
        transition.release_identity,
        transition.reservation_id,
        transition.transition_event_id,
        transition.release_cursor,
        transition.expected_version,
        transition.transition_kind,
        transition.consumed_amount,
        transition.releasable_amount,
        target_state,
    )
