"""Redacted durable observations for the offline reconciliation boundary."""

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import re
import sqlite3

from dcabot.application.reconciliation import (
    ConnectionState,
    EventDecision,
    UserDataEvent,
)


MAX_RECONCILIATION_EVENTS = 1_000
_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,128}\Z", re.ASCII)


class ReconciliationJournalError(ValueError):
    """Raised when a redacted reconciliation journal cannot be trusted."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class ReconciliationRecordOutcome(StrEnum):
    """Result of recording one immutable reconciliation observation."""

    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True, slots=True)
class DurableReconciliationObservation:
    """Redacted coordinator fact, optionally linked to one Spot binding event."""

    event: UserDataEvent
    decision: EventDecision
    state: ConnectionState
    binding_event_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.event, UserDataEvent):
            raise ReconciliationJournalError(
                "SPOT_RECONCILIATION_EVENT_INVALID", "Reconciliation event güvenli tipte değil."
            )
        try:
            decision = EventDecision(self.decision)
            state = ConnectionState(self.state)
        except (TypeError, ValueError) as exc:
            raise ReconciliationJournalError(
                "SPOT_RECONCILIATION_STATE_INVALID", "Reconciliation karar/state değeri geçersiz."
            ) from exc
        object.__setattr__(self, "decision", decision)
        object.__setattr__(self, "state", state)
        if self.binding_event_id is not None and _IDENTIFIER.fullmatch(self.binding_event_id) is None:
            raise ReconciliationJournalError(
                "SPOT_RECONCILIATION_BINDING_ID_INVALID", "Binding event kimliği güvenli biçimde saklanamaz."
            )


RECONCILIATION_TABLE_SQL = """
CREATE TABLE reconciliation_events(
    sequence INTEGER PRIMARY KEY,
    event_id TEXT UNIQUE NOT NULL,
    binding_event_id TEXT,
    observation_payload TEXT NOT NULL,
    observation_hash TEXT NOT NULL
);
""".strip()


def validate_reconciliation_schema(db: sqlite3.Connection) -> None:
    columns = {
        row[1]
        for row in db.execute("PRAGMA table_info(reconciliation_events)")
    }
    if columns != {
        "sequence",
        "event_id",
        "binding_event_id",
        "observation_payload",
        "observation_hash",
    }:
        raise ReconciliationJournalError(
            "SPOT_RECONCILIATION_SCHEMA_INVALID", "Reconciliation journal şeması geçersiz."
        )


def record_unlocked(
    db: sqlite3.Connection,
    observation: DurableReconciliationObservation,
) -> ReconciliationRecordOutcome:
    _validate_observation(observation)
    payload = _canonical(_observation_payload(observation))
    prior = db.execute(
        "SELECT observation_payload FROM reconciliation_events WHERE event_id=?",
        (observation.event.event_id,),
    ).fetchone()
    if prior is not None:
        if prior[0] != payload:
            raise ReconciliationJournalError(
                "SPOT_RECONCILIATION_EVENT_CONFLICT",
                "Aynı reconciliation event kimliği farklı gözlemle kullanılamaz.",
            )
        return ReconciliationRecordOutcome.DUPLICATE
    count = db.execute("SELECT COUNT(*) FROM reconciliation_events").fetchone()[0]
    if count >= MAX_RECONCILIATION_EVENTS:
        raise ReconciliationJournalError(
            "SPOT_RECONCILIATION_EVENT_LIMIT", "Reconciliation journal bounded event sınırına ulaştı."
        )
    db.execute(
        "INSERT INTO reconciliation_events(sequence, event_id, binding_event_id, "
        "observation_payload, observation_hash) VALUES (?, ?, ?, ?, ?)",
        (
            count + 1,
            observation.event.event_id,
            observation.binding_event_id,
            payload,
            _digest(payload),
        ),
    )
    return ReconciliationRecordOutcome.ACCEPTED


def load_unlocked(db: sqlite3.Connection) -> tuple[DurableReconciliationObservation, ...]:
    validate_reconciliation_schema(db)
    rows = db.execute(
        "SELECT sequence, event_id, binding_event_id, observation_payload, observation_hash "
        "FROM reconciliation_events ORDER BY sequence"
    ).fetchall()
    result = []
    for expected_sequence, row in enumerate(rows, start=1):
        sequence, event_id, binding_event_id, payload, payload_hash = row
        if (
            sequence != expected_sequence
            or not isinstance(payload, str)
            or not isinstance(payload_hash, str)
            or _digest(payload) != payload_hash
        ):
            raise ReconciliationJournalError(
                "SPOT_RECONCILIATION_RECORD_CORRUPT",
                "Reconciliation journal sırası/checksum doğrulanamadı.",
            )
        observation = _decode_observation(payload)
        if observation.event.event_id != event_id or observation.binding_event_id != binding_event_id:
            raise ReconciliationJournalError(
                "SPOT_RECONCILIATION_RECORD_CORRUPT",
                "Reconciliation event kimliği payload ile eşleşmiyor.",
            )
        result.append(observation)
    return tuple(result)


def _validate_observation(observation: object) -> None:
    if not isinstance(observation, DurableReconciliationObservation):
        raise ReconciliationJournalError(
            "SPOT_RECONCILIATION_OBSERVATION_INVALID", "Reconciliation gözlemi güvenli tipte değil."
        )


def _observation_payload(observation: DurableReconciliationObservation) -> dict[str, object]:
    event = observation.event
    return {
        "binding_event_id": observation.binding_event_id,
        "decision": observation.decision.value,
        "event": {
            "event_id": event.event_id,
            "event_time_ms": event.event_time_ms,
            "event_type": event.event_type,
            "payload_fingerprint": event.payload_fingerprint,
            "venue_order_id": event.venue_order_id,
        },
        "state": observation.state.value,
    }


def _decode_observation(payload: str) -> DurableReconciliationObservation:
    try:
        raw = json.loads(payload)
        if not isinstance(raw, dict) or set(raw) != {
            "binding_event_id",
            "decision",
            "event",
            "state",
        }:
            raise ValueError("Unexpected reconciliation fields")
        event = raw["event"]
        if not isinstance(event, dict) or set(event) != {
            "event_id",
            "event_time_ms",
            "event_type",
            "payload_fingerprint",
            "venue_order_id",
        }:
            raise ValueError("Unexpected reconciliation event fields")
        return DurableReconciliationObservation(
            UserDataEvent(**event),
            EventDecision(raw["decision"]),
            ConnectionState(raw["state"]),
            raw["binding_event_id"],
        )
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ReconciliationJournalError(
            "SPOT_RECONCILIATION_RECORD_CORRUPT", "Reconciliation payload doğrulanamadı."
        ) from exc


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
