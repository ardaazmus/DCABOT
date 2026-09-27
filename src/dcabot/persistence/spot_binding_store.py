"""Durable offline journal for guarded Spot lifecycle/core bindings."""

from dataclasses import dataclass
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import sqlite3

from dcabot.application.spot_lifecycle_core_binding import (
    CoreBindingOutcome,
    CoreBindingResult,
    bind_spot_event_to_core,
)
from dcabot.application.spot_order_lifecycle import (
    SpotOrder,
    SpotOrderEvent,
    SpotOrderLifecycle,
)
from dcabot.domain.config import Config
from dcabot.domain.engine import Order, State, identifier
from dcabot.domain.math import Position
from dcabot.domain.numbers import bounded, exact_text, number, ratio
from dcabot.application.reconciliation import EventDecision
from dcabot.application.venue_spot_event_mapping import VenueSpotEventMappingCandidate
from dcabot.persistence.reconciliation_journal import (
    DurableReconciliationObservation,
    MappingRecordOutcome,
    RECONCILIATION_TABLE_SQL,
    ReconciliationRecordOutcome,
    load_mappings_unlocked,
    load_unlocked as load_reconciliation_unlocked,
    record_mapping_unlocked,
    record_mapping_with_evidence_unlocked,
    record_unlocked as record_reconciliation_unlocked,
    validate_reconciliation_schema,
)


APPLICATION_ID = 0x44434253
SCHEMA_VERSION = 1
MAX_EVENTS = 1_000


class SpotBindingStoreError(ValueError):
    """Raised when the durable Spot binding journal cannot be trusted."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class SpotBindingReplay:
    """Validated lifecycle and core projections reconstructed from one journal."""

    lifecycle: SpotOrderLifecycle
    core_state: State
    accepted_event_count: int


class SpotBindingStore:
    """Own one atomic, replayable journal for offline Spot/core projections."""

    def __init__(self, path: Path, db: sqlite3.Connection, config: Config) -> None:
        self.path = path
        self.db = db
        self.config = config

    @classmethod
    def create(
        cls,
        path: Path,
        *,
        config: Config,
        lifecycle: SpotOrderLifecycle,
        core_state: State,
    ) -> "SpotBindingStore":
        validated = _validate_path(path)
        if validated.exists():
            raise SpotBindingStoreError(
                "SPOT_BINDING_STORE_EXISTS", "Spot binding store mevcut dosyanın üzerine yazamaz."
            )
        if not isinstance(config, Config):
            raise SpotBindingStoreError("SPOT_BINDING_CONFIG_INVALID", "Config geçerli core tipi olmalıdır.")
        _validate_projection_types(lifecycle, core_state)
        try:
            validated.parent.mkdir(parents=True, exist_ok=True)
            with validated.open("xb"):
                pass
            db = _connect(validated, mode="rw")
            store = cls(validated, db, config)
            store._initialize(lifecycle, core_state)
            return store
        except SpotBindingStoreError:
            if "db" in locals():
                db.close()
            raise
        except (OSError, sqlite3.Error) as exc:
            if "db" in locals():
                db.close()
            raise SpotBindingStoreError(
                "SPOT_BINDING_STORE_UNAVAILABLE", "Spot binding store açılamadı."
            ) from exc

    @classmethod
    def open(cls, path: Path, *, config: Config) -> "SpotBindingStore":
        validated = _validate_path(path)
        if not validated.is_file():
            raise SpotBindingStoreError(
                "SPOT_BINDING_STORE_MISSING", "Spot binding store bulunamadı."
            )
        if not isinstance(config, Config):
            raise SpotBindingStoreError("SPOT_BINDING_CONFIG_INVALID", "Config geçerli core tipi olmalıdır.")
        try:
            db = _connect(validated, mode="rw")
            if (
                db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
                or db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION
            ):
                raise SpotBindingStoreError(
                    "SPOT_BINDING_STORE_UNSUPPORTED", "Spot binding store şeması desteklenmiyor."
                )
            metadata = dict(db.execute("SELECT key, value FROM metadata"))
            expected_config = _config_payload(config)
            if metadata.get("store") != "offline-spot-binding-1":
                raise SpotBindingStoreError(
                    "SPOT_BINDING_METADATA_INVALID", "Spot binding store metadata geçersiz."
                )
            if metadata.get("scope") != "DURABLE_SPOT_LIFECYCLE_CORE_BINDING":
                raise SpotBindingStoreError(
                    "SPOT_BINDING_METADATA_INVALID", "Spot binding store kapsamı geçersiz."
                )
            if metadata.get("config") != _canonical(expected_config) or metadata.get(
                "config_hash"
            ) != _digest(metadata.get("config", "")):
                raise SpotBindingStoreError(
                    "SPOT_BINDING_CONFIG_MISMATCH", "Store config snapshot doğrulanamadı."
                )
            if metadata.get("config") != _canonical(expected_config):
                raise SpotBindingStoreError(
                    "SPOT_BINDING_CONFIG_MISMATCH", "Store config aktif config ile eşleşmiyor."
                )
            store = cls(validated, db, config)
            store._validate_base_rows()
            return store
        except SpotBindingStoreError:
            if "db" in locals():
                db.close()
            raise
        except (OSError, sqlite3.Error) as exc:
            if "db" in locals():
                db.close()
            raise SpotBindingStoreError(
                "SPOT_BINDING_STORE_UNAVAILABLE", "Spot binding store açılamadı."
            ) from exc

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "SpotBindingStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def append(
        self,
        event: SpotOrderEvent,
        *,
        fee: str | None = None,
        fee_asset: str | None = None,
        core_role: str | None = None,
        reconciliation: DurableReconciliationObservation | None = None,
    ) -> CoreBindingResult:
        """Bind and atomically append one accepted event, or return a duplicate."""

        if not isinstance(event, SpotOrderEvent):
            raise SpotBindingStoreError("SPOT_BINDING_EVENT_INVALID", "Spot event güvenli tipte değil.")
        if reconciliation is not None and (
            not isinstance(reconciliation, DurableReconciliationObservation)
            or reconciliation.binding_event_id != event.event_id
        ):
            raise SpotBindingStoreError(
                "SPOT_BINDING_RECONCILIATION_LINK_INVALID",
                "Reconciliation gözlemi aynı Spot event kimliğine bağlanmalıdır.",
            )
        envelope = _binding_envelope(event, fee=fee, fee_asset=fee_asset, core_role=core_role)
        event_payload = _canonical(envelope)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            prior = self.db.execute(
                "SELECT event_payload FROM binding_events WHERE event_id=?",
                (event.event_id,),
            ).fetchone()
            if prior is not None:
                if prior[0] != event_payload:
                    raise SpotBindingStoreError(
                        "SPOT_BINDING_EVENT_CONFLICT",
                        "Aynı event kimliği farklı binding kaydıyla kullanılamaz.",
                    )
                replay = self._load_unlocked()
                if reconciliation is not None:
                    record_reconciliation_unlocked(self.db, reconciliation)
                self.db.execute("COMMIT")
                return CoreBindingResult(
                    replay.lifecycle,
                    replay.core_state,
                    (),
                    CoreBindingOutcome.DUPLICATE,
                )
            replay = self._load_unlocked()
            if replay.accepted_event_count >= MAX_EVENTS:
                raise SpotBindingStoreError(
                    "SPOT_BINDING_EVENT_LIMIT", "Spot binding journal bounded event sınırına ulaştı."
                )
            result = bind_spot_event_to_core(
                replay.core_state,
                self.config,
                replay.lifecycle,
                event,
                fee=fee,
                fee_asset=fee_asset,
                core_role=core_role,
            )
            if result.outcome is not CoreBindingOutcome.ACCEPTED:
                if reconciliation is not None:
                    raise SpotBindingStoreError(
                        "SPOT_BINDING_RECONCILIATION_REQUIRES_ACCEPTED",
                        "Reconciliation ilişkisi yalnız kabul edilmiş binding ile yazılabilir.",
                    )
                self.db.execute("COMMIT")
                return result
            core_payload = _canonical(list(result.core_events))
            sequence = replay.accepted_event_count + 1
            self.db.execute(
                "INSERT INTO binding_events(sequence, event_id, event_payload, event_hash, "
                "core_payload, core_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    sequence,
                    event.event_id,
                    event_payload,
                    _digest(event_payload),
                    core_payload,
                    _digest(core_payload),
                ),
            )
            if reconciliation is not None:
                record_reconciliation_unlocked(self.db, reconciliation)
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def load(self) -> SpotBindingReplay:
        """Replay every stored binding and verify both projections together."""

        self.db.execute("BEGIN")
        try:
            result = self._load_unlocked()
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def record_reconciliation(
        self, observation: DurableReconciliationObservation
    ) -> ReconciliationRecordOutcome:
        """Persist one redacted coordinator observation with idempotent identity."""

        self.db.execute("BEGIN IMMEDIATE")
        try:
            result = record_reconciliation_unlocked(self.db, observation)
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def load_reconciliation(self) -> tuple[DurableReconciliationObservation, ...]:
        """Reload reconciliation observations without promoting any state."""

        self.db.execute("BEGIN")
        try:
            result = load_reconciliation_unlocked(self.db)
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def record_mapping(
        self, candidate: VenueSpotEventMappingCandidate
    ) -> MappingRecordOutcome:
        """Persist one non-economic mapping candidate without changing projections."""

        self.db.execute("BEGIN IMMEDIATE")
        try:
            result = record_mapping_unlocked(self.db, candidate)
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def record_mapping_with_evidence(
        self,
        candidate: VenueSpotEventMappingCandidate,
        observation: DurableReconciliationObservation,
    ) -> MappingRecordOutcome:
        """Atomically persist matched evidence and a non-economic mapping candidate."""

        self.db.execute("BEGIN IMMEDIATE")
        try:
            result = record_mapping_with_evidence_unlocked(self.db, candidate, observation)
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def load_mappings(self) -> tuple[VenueSpotEventMappingCandidate, ...]:
        """Replay identity candidates without promoting lifecycle or core state."""

        self.db.execute("BEGIN")
        try:
            result = load_mappings_unlocked(self.db)
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def append_verified_mapping(
        self,
        candidate: VenueSpotEventMappingCandidate,
        observation: DurableReconciliationObservation,
        event: SpotOrderEvent,
        *,
        fee: str | None = None,
        fee_asset: str | None = None,
        core_role: str | None = None,
    ) -> CoreBindingResult:
        """Admit one durably matched Spot event through the existing guarded binder."""

        if not isinstance(candidate, VenueSpotEventMappingCandidate):
            raise SpotBindingStoreError(
                "SPOT_RECONCILIATION_MAPPING_INVALID", "Mapping candidate güvenli tipte değil."
            )
        if not isinstance(observation, DurableReconciliationObservation):
            raise SpotBindingStoreError(
                "SPOT_RECONCILIATION_MAPPING_LINK_INVALID", "Reconciliation evidence güvenli tipte değil."
            )
        if not isinstance(event, SpotOrderEvent):
            raise SpotBindingStoreError(
                "SPOT_BINDING_EVENT_INVALID", "Spot event güvenli tipte değil."
            )
        if observation.decision not in {EventDecision.ACCEPTED, EventDecision.DUPLICATE}:
            raise SpotBindingStoreError(
                "SPOT_RECONCILIATION_MAPPING_ADMISSION_INVALID",
                "Ekonomik admission yalnız kabul edilmiş stream kararıyla yapılabilir.",
            )
        if (
            candidate.spot_event_id != event.event_id
            or candidate.spot_order_id != event.order_id
            or candidate.execution_id != event.execution_id
        ):
            raise SpotBindingStoreError(
                "SPOT_RECONCILIATION_MAPPING_LINK_INVALID",
                "Mapping candidate Spot event kimliğiyle eşleşmiyor.",
            )
        self.db.execute("BEGIN IMMEDIATE")
        try:
            observations = load_reconciliation_unlocked(self.db)
            mappings = load_mappings_unlocked(self.db)
            if observation not in observations or candidate not in mappings:
                raise SpotBindingStoreError(
                    "SPOT_RECONCILIATION_MAPPING_NOT_DURABLE",
                    "Mapping ve matched evidence önce durable olarak yazılmalıdır.",
                )
            record_mapping_with_evidence_unlocked(self.db, candidate, observation)
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        return self.append(
            event,
            fee=fee,
            fee_asset=fee_asset,
            core_role=core_role,
        )

    def _initialize(
        self, lifecycle: SpotOrderLifecycle, core_state: State
    ) -> None:
        config_payload = _canonical(_config_payload(self.config))
        lifecycle_payload = _canonical(_lifecycle_payload(lifecycle))
        core_payload = _canonical(_state_payload(core_state))
        self.db.executescript(
            f"""
            BEGIN IMMEDIATE;
            PRAGMA application_id={APPLICATION_ID};
            PRAGMA user_version={SCHEMA_VERSION};
            CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE base_projection(
                kind TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                payload_hash TEXT NOT NULL
            );
            CREATE TABLE binding_events(
                sequence INTEGER PRIMARY KEY,
                event_id TEXT UNIQUE NOT NULL,
                event_payload TEXT NOT NULL,
                event_hash TEXT NOT NULL,
                core_payload TEXT NOT NULL,
                core_hash TEXT NOT NULL
            );
            {RECONCILIATION_TABLE_SQL}
            INSERT INTO metadata(key, value) VALUES
                ('store', 'offline-spot-binding-1'),
                ('scope', 'DURABLE_SPOT_LIFECYCLE_CORE_BINDING'),
                ('config', '{_sql_text(config_payload)}'),
                ('config_hash', '{_digest(config_payload)}');
            INSERT INTO base_projection VALUES
                ('LIFECYCLE', '{_sql_text(lifecycle_payload)}', '{_digest(lifecycle_payload)}'),
                ('CORE_STATE', '{_sql_text(core_payload)}', '{_digest(core_payload)}');
            COMMIT;
            """
        )

    def _validate_base_rows(self) -> None:
        validate_reconciliation_schema(self.db)
        rows = {
            row[0]: (row[1], row[2])
            for row in self.db.execute(
                "SELECT kind, payload, payload_hash FROM base_projection"
            )
        }
        if set(rows) != {"LIFECYCLE", "CORE_STATE"}:
            raise SpotBindingStoreError(
                "SPOT_BINDING_BASE_INVALID", "Spot binding başlangıç projection’ları eksik."
            )
        for kind, (payload, payload_hash) in rows.items():
            if _digest(payload) != payload_hash:
                raise SpotBindingStoreError(
                    "SPOT_BINDING_RECORD_CORRUPT", f"{kind} projection checksum doğrulanamadı."
                )
        _decode_lifecycle(json.loads(rows["LIFECYCLE"][0]))
        _decode_state(json.loads(rows["CORE_STATE"][0]))

    def _load_unlocked(self) -> SpotBindingReplay:
        self._validate_base_rows()
        base = {
            row[0]: row[1]
            for row in self.db.execute("SELECT kind, payload FROM base_projection")
        }
        lifecycle = _decode_lifecycle(json.loads(base["LIFECYCLE"]))
        core_state = _decode_state(json.loads(base["CORE_STATE"]))
        rows = self.db.execute(
            "SELECT sequence, event_id, event_payload, event_hash, core_payload, core_hash "
            "FROM binding_events ORDER BY sequence"
        ).fetchall()
        for expected_sequence, row in enumerate(rows, start=1):
            sequence, event_id, event_payload, event_hash, core_payload, core_hash = row
            if sequence != expected_sequence or _digest(event_payload) != event_hash:
                raise SpotBindingStoreError(
                    "SPOT_BINDING_RECORD_CORRUPT", "Spot event journal sırası/checksum doğrulanamadı."
                )
            if _digest(core_payload) != core_hash:
                raise SpotBindingStoreError(
                    "SPOT_BINDING_RECORD_CORRUPT", "Core event journal checksum doğrulanamadı."
                )
            envelope = _decode_envelope(event_payload)
            if envelope["event"].event_id != event_id:
                raise SpotBindingStoreError(
                    "SPOT_BINDING_RECORD_CORRUPT", "Event journal kimliği payload ile eşleşmiyor."
                )
            result = bind_spot_event_to_core(
                core_state,
                self.config,
                lifecycle,
                envelope["event"],
                fee=envelope["fee"],
                fee_asset=envelope["fee_asset"],
                core_role=envelope["core_role"],
            )
            if result.outcome is not CoreBindingOutcome.ACCEPTED or _canonical(
                list(result.core_events)
            ) != core_payload:
                raise SpotBindingStoreError(
                    "SPOT_BINDING_RECORD_CORRUPT", "Stored binding replay sonucu değişti."
                )
            lifecycle = result.lifecycle
            core_state = result.core_state
        return SpotBindingReplay(lifecycle, core_state, len(rows))


def _binding_envelope(
    event: SpotOrderEvent,
    *,
    fee: str | None,
    fee_asset: str | None,
    core_role: str | None,
) -> dict[str, object]:
    normalized_fee = None if fee is None else exact_text(number(fee))
    if fee_asset is not None and (
        not isinstance(fee_asset, str) or not 1 <= len(fee_asset) <= 32
    ):
        raise SpotBindingStoreError("SPOT_BINDING_FEE_ASSET_INVALID", "Fee asset bounded metin olmalıdır.")
    if core_role is not None and (
        not isinstance(core_role, str) or not 1 <= len(core_role) <= 100
    ):
        raise SpotBindingStoreError("SPOT_BINDING_ROLE_INVALID", "Core role bounded metin olmalıdır.")
    return {
        "event": _event_payload(event),
        "fee": normalized_fee,
        "fee_asset": fee_asset,
        "core_role": core_role,
    }


def _decode_envelope(payload: str) -> dict[str, object]:
    try:
        raw = json.loads(payload)
        if set(raw) != {"core_role", "event", "fee", "fee_asset"}:
            raise ValueError("Unexpected binding envelope fields")
        event = _decode_event(raw["event"])
        fee = raw["fee"]
        fee_asset = raw["fee_asset"]
        core_role = raw["core_role"]
        if fee is not None:
            exact_text(number(fee))
        if fee_asset is not None and (
            not isinstance(fee_asset, str) or not 1 <= len(fee_asset) <= 32
        ):
            raise ValueError("Invalid fee asset")
        if core_role is not None and (
            not isinstance(core_role, str) or not 1 <= len(core_role) <= 100
        ):
            raise ValueError("Invalid core role")
        return {
            "event": event,
            "fee": fee,
            "fee_asset": fee_asset,
            "core_role": core_role,
        }
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SpotBindingStoreError(
            "SPOT_BINDING_RECORD_CORRUPT", "Binding envelope doğrulanamadı."
        ) from exc


def _event_payload(event: SpotOrderEvent) -> dict[str, object]:
    return {
        "order_id": event.order_id,
        "event_id": event.event_id,
        "execution_id": event.execution_id,
        "event_time_ms": event.event_time_ms,
        "status": event.status.value,
        "last_filled_qty": event.last_filled_qty,
        "cumulative_filled_qty": event.cumulative_filled_qty,
        "last_price": event.last_price,
    }


def _decode_event(payload: object) -> SpotOrderEvent:
    if not isinstance(payload, dict) or set(payload) != {
        "order_id",
        "event_id",
        "execution_id",
        "event_time_ms",
        "status",
        "last_filled_qty",
        "cumulative_filled_qty",
        "last_price",
    }:
        raise ValueError("Unexpected event fields")
    return SpotOrderEvent(**payload)


def _lifecycle_payload(lifecycle: SpotOrderLifecycle) -> dict[str, object]:
    order = lifecycle.order
    return {
        "order": {
            "order_id": order.order_id,
            "client_order_id": order.client_order_id,
            "symbol": order.symbol,
            "side": order.side.value,
            "order_type": order.order_type.value,
            "requested_quantity": order.requested_quantity,
            "quote_order_quantity": order.quote_order_quantity,
            "price": order.price,
            "status": order.status.value,
            "filled_quantity": order.filled_quantity,
            "leaves_quantity": order.leaves_quantity,
            "last_event_time_ms": order.last_event_time_ms,
        },
        "seen_events": [list(item) for item in lifecycle.seen_events],
        "seen_executions": [list(item) for item in lifecycle.seen_executions],
        "reconciliation_required": lifecycle.reconciliation_required,
    }


def _decode_lifecycle(payload: object) -> SpotOrderLifecycle:
    if not isinstance(payload, dict) or set(payload) != {
        "order",
        "seen_events",
        "seen_executions",
        "reconciliation_required",
    }:
        raise SpotBindingStoreError("SPOT_BINDING_RECORD_CORRUPT", "Lifecycle projection alanları geçersiz.")
    raw_order = payload["order"]
    if not isinstance(raw_order, dict) or set(raw_order) != {
        "order_id",
        "client_order_id",
        "symbol",
        "side",
        "order_type",
        "requested_quantity",
        "quote_order_quantity",
        "price",
        "status",
        "filled_quantity",
        "leaves_quantity",
        "last_event_time_ms",
    }:
        raise SpotBindingStoreError("SPOT_BINDING_RECORD_CORRUPT", "Spot order projection alanları geçersiz.")
    try:
        order = SpotOrder(**raw_order)
        seen_events = _decode_seen(payload["seen_events"])
        seen_executions = _decode_seen(payload["seen_executions"])
        if type(payload["reconciliation_required"]) is not bool:
            raise ValueError("Invalid reconciliation flag")
        return SpotOrderLifecycle(
            order,
            seen_events=seen_events,
            seen_executions=seen_executions,
            reconciliation_required=payload["reconciliation_required"],
        )
    except (TypeError, ValueError) as exc:
        raise SpotBindingStoreError(
            "SPOT_BINDING_RECORD_CORRUPT", "Lifecycle projection doğrulanamadı."
        ) from exc


def _decode_seen(value: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, list):
        raise ValueError("Seen event list expected")
    result = []
    for item in value:
        if (
            not isinstance(item, list)
            or len(item) != 2
            or not all(isinstance(part, str) for part in item)
        ):
            raise ValueError("Invalid seen event")
        result.append((item[0], item[1]))
    return tuple(result)


def _state_payload(state: State) -> dict[str, object]:
    return {
        "position": {
            "qty": ratio(state.position.qty),
            "cost": ratio(state.position.cost),
        },
        "realized": ratio(state.realized),
        "fees": ratio(state.fees),
        "funding": ratio(state.funding),
        "entry_notional": ratio(state.entry_notional),
        "mark": None if state.mark is None else ratio(state.mark),
        "anchor": None if state.anchor is None else ratio(state.anchor),
        "peak": ratio(state.peak),
        "max_dd": ratio(state.max_dd),
        "halted": state.halted,
        "safety_stopped": state.safety_stopped,
        # Faz 17 H.1/H.2/I.1: added well after this store's original field
        # set -- omitted here for years, which silently dropped them on
        # every save/reload round-trip (a real bug, fixed together with the
        # new testnet DCA session store that needs these to survive).
        "ladder_start_qty": None if state.ladder_start_qty is None else ratio(state.ladder_start_qty),
        "now_us": state.now_us,
        "deal_started_at_us": state.deal_started_at_us,
        "deal_duration_expired": state.deal_duration_expired,
        "sl_breach_streak": state.sl_breach_streak,
        # F09a: armed trailing water must survive save/reload, or a
        # restart would silently disarm an in-profit deal's ratchet.
        "trail_water": None if state.trail_water is None else ratio(state.trail_water),
        "profit_cost_recovered": state.profit_cost_recovered,
        "retained_profit_base": ratio(state.retained_profit_base),
        "orders": {
            key: _order_payload(order) for key, order in sorted(state.orders.items())
        },
        "blockers": list(state.blockers),
        "last_rejection": state.last_rejection,
    }


def _order_payload(order: Order) -> dict[str, object]:
    payload = {
        "order_id": order.order_id,
        "role": order.role,
        "side": order.side,
        "qty": ratio(order.qty),
        "limit": ratio(order.limit),
        "filled": ratio(order.filled),
        "notional": ratio(order.notional),
        "status": order.status,
        "complete": order.complete,
        "order_type": order.order_type,
    }
    if order.intent_id is not None:
        payload["intent_id"] = order.intent_id
    if order.reference_price is not None:
        payload["reference_price"] = ratio(order.reference_price)
    if order.realized_slippage is not None:
        payload["realized_slippage"] = ratio(order.realized_slippage)
    return payload


_STATE_REQUIRED_FIELDS = {
    "position",
    "realized",
    "fees",
    "funding",
    "entry_notional",
    "mark",
    "anchor",
    "peak",
    "max_dd",
    "halted",
    "safety_stopped",
    "orders",
    "blockers",
    "last_rejection",
}
# Faz 17 H.1/H.2/I.1: optional-on-decode so a record written before these
# fields existed still loads, defaulting exactly like a fresh State() would.
_STATE_OPTIONAL_FIELDS = {
    "ladder_start_qty",
    "now_us",
    "deal_started_at_us",
    "deal_duration_expired",
    "sl_breach_streak",
    "trail_water",
    "profit_cost_recovered",
    "retained_profit_base",
}


def _decode_state(payload: object) -> State:
    if (
        not isinstance(payload, dict)
        or not _STATE_REQUIRED_FIELDS <= set(payload)
        or not (set(payload) - _STATE_REQUIRED_FIELDS) <= _STATE_OPTIONAL_FIELDS
    ):
        raise SpotBindingStoreError("SPOT_BINDING_RECORD_CORRUPT", "Core state alanları geçersiz.")
    try:
        position = payload["position"]
        if not isinstance(position, dict) or set(position) != {"qty", "cost"}:
            raise ValueError("Invalid position")
        orders_raw = payload["orders"]
        if not isinstance(orders_raw, dict):
            raise ValueError("Invalid orders")
        orders = {key: _decode_order(value) for key, value in orders_raw.items()}
        if set(orders) != set(orders_raw) or any(
            order.order_id != key for key, order in orders.items()
        ):
            raise ValueError("Order identity mismatch")
        for name in ("halted", "safety_stopped"):
            if type(payload[name]) is not bool:
                raise ValueError("Invalid state flag")
        blockers = payload["blockers"]
        if not isinstance(blockers, list) or not all(
            isinstance(item, str) and len(item) <= 200 for item in blockers
        ):
            raise ValueError("Invalid blockers")
        if payload["last_rejection"] is not None and not isinstance(
            payload["last_rejection"], str
        ):
            raise ValueError("Invalid rejection")
        now_us = payload.get("now_us")
        if now_us is not None and type(now_us) is not int:
            raise ValueError("Invalid now_us")
        deal_started_at_us = payload.get("deal_started_at_us")
        if deal_started_at_us is not None and type(deal_started_at_us) is not int:
            raise ValueError("Invalid deal_started_at_us")
        deal_duration_expired = payload.get("deal_duration_expired", False)
        if type(deal_duration_expired) is not bool:
            raise ValueError("Invalid deal_duration_expired")
        sl_breach_streak = payload.get("sl_breach_streak", 0)
        if type(sl_breach_streak) is not int:
            raise ValueError("Invalid sl_breach_streak")
        trail_water = _optional_fraction(payload.get("trail_water"))
        profit_cost_recovered = payload.get("profit_cost_recovered", False)
        if type(profit_cost_recovered) is not bool:
            raise ValueError("Invalid profit_cost_recovered")
        retained_profit_base_raw = payload.get("retained_profit_base")
        retained_profit_base = (
            Q(0) if retained_profit_base_raw is None else _fraction(retained_profit_base_raw)
        )
        return State(
            position=Position(_fraction(position["qty"]), _fraction(position["cost"])),
            realized=_fraction(payload["realized"]),
            fees=_fraction(payload["fees"]),
            funding=_fraction(payload["funding"]),
            entry_notional=_fraction(payload["entry_notional"]),
            mark=_optional_fraction(payload["mark"]),
            anchor=_optional_fraction(payload["anchor"]),
            peak=_fraction(payload["peak"]),
            max_dd=_fraction(payload["max_dd"]),
            halted=payload["halted"],
            safety_stopped=payload["safety_stopped"],
            ladder_start_qty=_optional_fraction(payload.get("ladder_start_qty")),
            now_us=now_us,
            deal_started_at_us=deal_started_at_us,
            deal_duration_expired=deal_duration_expired,
            sl_breach_streak=sl_breach_streak,
            trail_water=trail_water,
            profit_cost_recovered=profit_cost_recovered,
            retained_profit_base=retained_profit_base,
            orders=orders,
            blockers=blockers,
            last_rejection=payload["last_rejection"],
        )
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        raise SpotBindingStoreError(
            "SPOT_BINDING_RECORD_CORRUPT", "Core state doğrulanamadı."
        ) from exc


_ORDER_REQUIRED_FIELDS = {
    "order_id",
    "role",
    "side",
    "qty",
    "limit",
    "filled",
    "notional",
    "status",
    "complete",
}
# Faz 17 G.2: `order_type`/`reference_price`/`realized_slippage` are new on
# Order and optional on decode -- a record written before this feature
# existed must still load, defaulting exactly like a fresh Order() would.
_ORDER_OPTIONAL_FIELDS = {"intent_id", "order_type", "reference_price", "realized_slippage"}


def _decode_order(payload: object) -> Order:
    payload_fields = set(payload) if isinstance(payload, dict) else None
    if (
        payload_fields is None
        or not _ORDER_REQUIRED_FIELDS <= payload_fields
        or not (payload_fields - _ORDER_REQUIRED_FIELDS) <= _ORDER_OPTIONAL_FIELDS
    ):
        raise ValueError("Invalid order fields")
    if type(payload["complete"]) is not bool:
        raise ValueError("Invalid order flag")
    intent_id = payload.get("intent_id")
    if intent_id is not None:
        intent_id = identifier(intent_id)
    order_type = payload.get("order_type", "LIMIT")
    if order_type not in ("MARKET", "LIMIT"):
        raise ValueError("Invalid order type")
    return Order(
        order_id=payload["order_id"],
        role=payload["role"],
        side=payload["side"],
        qty=_fraction(payload["qty"]),
        limit=_fraction(payload["limit"]),
        filled=_fraction(payload["filled"]),
        notional=_fraction(payload["notional"]),
        status=payload["status"],
        complete=payload["complete"],
        intent_id=intent_id,
        order_type=order_type,
        reference_price=_optional_fraction(payload.get("reference_price")),
        realized_slippage=_optional_fraction(payload.get("realized_slippage")),
    )


def _fraction(value: object) -> Q:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not all(isinstance(item, str) and item.lstrip("-").isdigit() for item in value)
        or int(value[1]) == 0
    ):
        raise ValueError("Invalid exact fraction")
    result = Q(int(value[0]), int(value[1]))
    return bounded(result)


def _optional_fraction(value: object) -> Q | None:
    return None if value is None else _fraction(value)


_CONFIG_PAYLOAD_CATEGORICAL = {
    "symbol", "base_asset", "quote_asset", "target_mode", "safety_count",
    "margin_mode", "direction", "max_active_safety_orders",
    "base_order_type", "safety_order_type", "exit_order_type", "stop_order_type",
    "slippage_reference",
    "stop_loss_confirmation_bars", "max_deal_duration_seconds", "max_deal_duration_action",
    "cooldown_seconds",
    "profit_asset",
    "safety_sizing",
    "base_sizing",
}
# Faz 17 H.2: a Q field that may be None (like max_adverse_slippage_bps) --
# exact_text() would crash on None, so it needs the same None-aware branch.
_CONFIG_PAYLOAD_OPTIONAL_EXACT = {
    "max_adverse_slippage_bps",
    "stop_loss_rate",
    # F09a: without this, _config_payload crashes on exact_text(None)
    # for every default (non-trailing) config.
    "trailing_take_profit_rate",
    # Faz G1-kalan/a: entry price band -- exact when set, null when open.
    "min_entry_price",
    "max_entry_price",
}


def _config_field_payload(config: Config, name: str) -> object:
    value = getattr(config, name)
    if name in _CONFIG_PAYLOAD_CATEGORICAL:
        return value
    if name in _CONFIG_PAYLOAD_OPTIONAL_EXACT:
        return None if value is None else exact_text(value)
    if name == "take_profit_ladder":
        # Faz 17 H.1: a tuple of TakeProfitLevel (or None) -- neither
        # categorical passthrough nor a single exact_text() value fits, so
        # each level is exploded into its own [weight, target_percent] pair.
        return (
            None
            if value is None
            else [[exact_text(level.weight), exact_text(level.target_percent)] for level in value]
        )
    return exact_text(value)


def _config_payload(config: Config) -> dict[str, object]:
    # safety_sizing is emitted only when non-default so every pre-Faz-W
    # persisted payload (and its identity hash) stays byte-identical.
    return {
        "mode": "offline",
        "schema_version": 1,
        **{
            name: _config_field_payload(config, name)
            for name in config.__dataclass_fields__
            if not (name in ("safety_sizing", "base_sizing") and getattr(config, name) == "BASE")
        },
    }


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sql_text(value: str) -> str:
    return value.replace("'", "''")


def _validate_projection_types(lifecycle: object, core_state: object) -> None:
    if not isinstance(lifecycle, SpotOrderLifecycle) or not isinstance(core_state, State):
        raise SpotBindingStoreError(
            "SPOT_BINDING_PROJECTION_INVALID", "Başlangıç projection’ları geçerli tipte olmalıdır."
        )


def _validate_path(path: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve()
    if "YEDEK_ESKI_PROJE" in resolved.parts or any(
        item.is_symlink() or bool(getattr(item, "is_junction", lambda: False)())
        for item in (candidate, *candidate.parents)
    ):
        raise SpotBindingStoreError("SPOT_BINDING_PATH_UNSAFE", "Store backup/linked path üzerinde olamaz.")
    if candidate.exists() and not candidate.is_file():
        raise SpotBindingStoreError("SPOT_BINDING_PATH_INVALID", "Store yolu dosya olmalıdır.")
    if not resolved.parent.is_dir():
        raise SpotBindingStoreError("SPOT_BINDING_PATH_INVALID", "Store parent yolu bulunmalıdır.")
    return candidate


def _connect(path: Path, *, mode: str) -> sqlite3.Connection:
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
