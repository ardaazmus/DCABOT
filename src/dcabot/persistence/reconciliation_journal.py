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
    LookupKind,
    OrderLookup,
    UserDataEvent,
)
from dcabot.application.venue_spot_event_mapping import (
    VenueSpotEventMappingCandidate,
)
from dcabot.application.venue_event_binding import (
    VenueEventEvidenceOutcome,
    evaluate_venue_event_lookup,
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


class MappingRecordOutcome(StrEnum):
    """Result of recording one immutable identity mapping candidate."""

    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True, slots=True)
class DurableReconciliationObservation:
    """Redacted coordinator fact, optionally linked to one Spot binding event."""

    event: UserDataEvent
    decision: EventDecision
    state: ConnectionState
    binding_event_id: str | None = None
    lookup: OrderLookup | None = None

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
        if self.lookup is not None and not isinstance(self.lookup, OrderLookup):
            raise ReconciliationJournalError(
                "SPOT_RECONCILIATION_LOOKUP_INVALID", "Lookup sonucu güvenli tipte değil."
            )


RECONCILIATION_TABLE_SQL = """
CREATE TABLE reconciliation_events(
    sequence INTEGER PRIMARY KEY,
    event_id TEXT UNIQUE NOT NULL,
    binding_event_id TEXT,
    observation_payload TEXT NOT NULL,
    observation_hash TEXT NOT NULL
);

CREATE TABLE reconciliation_mappings(
    sequence INTEGER PRIMARY KEY,
    venue_event_id TEXT UNIQUE NOT NULL,
    spot_event_id TEXT UNIQUE NOT NULL,
    mapping_payload TEXT NOT NULL,
    mapping_hash TEXT NOT NULL
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


def record_mapping_unlocked(
    db: sqlite3.Connection,
    candidate: VenueSpotEventMappingCandidate,
) -> MappingRecordOutcome:
    _validate_mapping(candidate)
    validate_mapping_schema(db)
    payload = _canonical(_mapping_payload(candidate))
    prior = db.execute(
        "SELECT mapping_payload FROM reconciliation_mappings WHERE venue_event_id=?",
        (candidate.venue_event_id,),
    ).fetchone()
    if prior is not None:
        if prior[0] != payload:
            raise ReconciliationJournalError(
                "SPOT_RECONCILIATION_MAPPING_CONFLICT",
                "Aynı venue event kimliği farklı mapping ile kullanılamaz.",
            )
        return MappingRecordOutcome.DUPLICATE
    if db.execute(
        "SELECT 1 FROM reconciliation_mappings WHERE spot_event_id=?",
        (candidate.spot_event_id,),
    ).fetchone() is not None:
        raise ReconciliationJournalError(
            "SPOT_RECONCILIATION_MAPPING_CONFLICT",
            "Aynı Spot event kimliği farklı mapping ile kullanılamaz.",
        )
    count = db.execute("SELECT COUNT(*) FROM reconciliation_mappings").fetchone()[0]
    if count >= MAX_RECONCILIATION_EVENTS:
        raise ReconciliationJournalError(
            "SPOT_RECONCILIATION_MAPPING_LIMIT", "Mapping journal bounded sınırına ulaştı."
        )
    db.execute(
        "INSERT INTO reconciliation_mappings(sequence, venue_event_id, spot_event_id, "
        "mapping_payload, mapping_hash) VALUES (?, ?, ?, ?, ?)",
        (
            count + 1,
            candidate.venue_event_id,
            candidate.spot_event_id,
            payload,
            _digest(payload),
        ),
    )
    return MappingRecordOutcome.ACCEPTED


def record_mapping_with_evidence_unlocked(
    db: sqlite3.Connection,
    candidate: VenueSpotEventMappingCandidate,
    observation: DurableReconciliationObservation,
) -> MappingRecordOutcome:
    """Atomically persist matched redacted evidence and its non-economic mapping."""

    _validate_mapping(candidate)
    _validate_observation(observation)
    if (
        observation.binding_event_id is not None
        or observation.event.event_id != candidate.venue_event_id
        or observation.event.venue_order_id != candidate.venue_order_id
        or observation.lookup is None
        or evaluate_venue_event_lookup(observation.event, observation.lookup).outcome
        is not VenueEventEvidenceOutcome.MATCHED
    ):
        raise ReconciliationJournalError(
            "SPOT_RECONCILIATION_MAPPING_LINK_INVALID",
            "Mapping yalnız eşleşen redacted evidence ile bağlanabilir.",
        )
    record_unlocked(db, observation)
    return record_mapping_unlocked(db, candidate)


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


def load_mappings_unlocked(
    db: sqlite3.Connection,
) -> tuple[VenueSpotEventMappingCandidate, ...]:
    validate_mapping_schema(db)
    rows = db.execute(
        "SELECT sequence, venue_event_id, spot_event_id, mapping_payload, mapping_hash "
        "FROM reconciliation_mappings ORDER BY sequence"
    ).fetchall()
    result = []
    for expected_sequence, row in enumerate(rows, start=1):
        sequence, venue_event_id, spot_event_id, payload, payload_hash = row
        if (
            sequence != expected_sequence
            or not isinstance(payload, str)
            or not isinstance(payload_hash, str)
            or _digest(payload) != payload_hash
        ):
            raise ReconciliationJournalError(
                "SPOT_RECONCILIATION_MAPPING_CORRUPT",
                "Mapping journal sırası/checksum doğrulanamadı.",
            )
        candidate = _decode_mapping(payload)
        if (
            candidate.venue_event_id != venue_event_id
            or candidate.spot_event_id != spot_event_id
        ):
            raise ReconciliationJournalError(
                "SPOT_RECONCILIATION_MAPPING_CORRUPT",
                "Mapping kimlikleri payload ile eşleşmiyor.",
            )
        result.append(candidate)
    return tuple(result)


def validate_mapping_schema(db: sqlite3.Connection) -> None:
    columns = {
        row[1]
        for row in db.execute("PRAGMA table_info(reconciliation_mappings)")
    }
    if columns != {
        "sequence",
        "venue_event_id",
        "spot_event_id",
        "mapping_payload",
        "mapping_hash",
    }:
        raise ReconciliationJournalError(
            "SPOT_RECONCILIATION_MAPPING_SCHEMA_INVALID", "Mapping journal şeması geçersiz."
        )


def _validate_observation(observation: object) -> None:
    if not isinstance(observation, DurableReconciliationObservation):
        raise ReconciliationJournalError(
            "SPOT_RECONCILIATION_OBSERVATION_INVALID", "Reconciliation gözlemi güvenli tipte değil."
        )


def _validate_mapping(candidate: object) -> None:
    if not isinstance(candidate, VenueSpotEventMappingCandidate):
        raise ReconciliationJournalError(
            "SPOT_RECONCILIATION_MAPPING_INVALID", "Mapping candidate güvenli tipte değil."
        )


def _observation_payload(observation: DurableReconciliationObservation) -> dict[str, object]:
    event = observation.event
    payload: dict[str, object] = {
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
    if observation.lookup is not None:
        payload["lookup"] = {
            "kind": observation.lookup.kind.value,
            "venue_order_id": observation.lookup.venue_order_id,
        }
    return payload


def _mapping_payload(candidate: VenueSpotEventMappingCandidate) -> dict[str, object]:
    return {
        "execution_id": candidate.execution_id,
        "spot_event_id": candidate.spot_event_id,
        "spot_order_id": candidate.spot_order_id,
        "status": candidate.status.value,
        "venue_event_id": candidate.venue_event_id,
        "venue_order_id": candidate.venue_order_id,
    }


def _decode_observation(payload: str) -> DurableReconciliationObservation:
    try:
        raw = json.loads(payload)
        if not isinstance(raw, dict) or set(raw) not in ({
            "binding_event_id",
            "decision",
            "event",
            "state",
        }, {
            "binding_event_id",
            "decision",
            "event",
            "lookup",
            "state",
        }):
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
        lookup = None if "lookup" not in raw else _decode_lookup(raw["lookup"])
        return DurableReconciliationObservation(
            UserDataEvent(**event),
            EventDecision(raw["decision"]),
            ConnectionState(raw["state"]),
            raw["binding_event_id"],
            lookup,
        )
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ReconciliationJournalError(
            "SPOT_RECONCILIATION_RECORD_CORRUPT", "Reconciliation payload doğrulanamadı."
        ) from exc


def _decode_lookup(payload: object) -> OrderLookup | None:
    if payload is None:
        return None
    if not isinstance(payload, dict) or set(payload) != {"kind", "venue_order_id"}:
        raise ValueError("Unexpected lookup fields")
    return OrderLookup(LookupKind(payload["kind"]), payload["venue_order_id"])


def _decode_mapping(payload: str) -> VenueSpotEventMappingCandidate:
    try:
        raw = json.loads(payload)
        if not isinstance(raw, dict) or set(raw) != {
            "execution_id",
            "spot_event_id",
            "spot_order_id",
            "status",
            "venue_event_id",
            "venue_order_id",
        }:
            raise ValueError("Unexpected mapping fields")
        return VenueSpotEventMappingCandidate(**raw)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ReconciliationJournalError(
            "SPOT_RECONCILIATION_MAPPING_CORRUPT", "Mapping payload doğrulanamadı."
        ) from exc


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
