"""Durable, offline sequencing journal for OCO venue evidence."""

from dataclasses import dataclass
from enum import StrEnum
import json
from pathlib import Path
import sqlite3

from dcabot.application.order_list_contract import (
    MAX_ORDER_LIST_OBSERVATIONS,
    OcoOrderListIdentity,
    OrderListError,
    OrderListLegIdentity,
    OrderListLegStatus,
    OrderListStatus,
    UserDataOrderListEvent,
    UserDataOrderListLeg,
)
from dcabot.application.order_list_reconciliation import (
    CancelReplaceIdentity,
    OrderListEventOutcome,
    OrderListVenueEvent,
    reconcile_order_list_event,
)
from dcabot.persistence.order_list_store import (
    _canonical,
    _connect,
    _digest,
    _identity_payload,
    _validate_path,
)


JOURNAL_APPLICATION_ID = 0x44434F45
JOURNAL_SCHEMA_VERSION = 1


class OrderListEventStoreError(ValueError):
    """Raised when the OCO venue evidence journal cannot be trusted."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class OrderListJournalRecordOutcome(StrEnum):
    """Result of appending one immutable venue observation."""

    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True, slots=True)
class OrderListEventJournalSnapshot:
    """Replay result with identity and ordered, non-economic observations."""

    identity: OcoOrderListIdentity
    observations: tuple[OrderListVenueEvent | CancelReplaceIdentity | UserDataOrderListEvent, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.identity, OcoOrderListIdentity):
            raise OrderListEventStoreError(
                "ORDER_LIST_IDENTITY_INVALID", "OCO identity güvenli tipte değil."
            )
        if type(self.observations) is not tuple or len(self.observations) > MAX_ORDER_LIST_OBSERVATIONS:
            raise OrderListEventStoreError(
                "ORDER_LIST_EVENT_LIMIT", "OCO event journal bounded olmalıdır."
            )
        identifiers: set[str] = set()
        last_time: int | None = None
        last_status: OrderListStatus | None = None
        for observation in self.observations:
            if not isinstance(observation, (OrderListVenueEvent, CancelReplaceIdentity, UserDataOrderListEvent)):
                raise OrderListEventStoreError(
                    "ORDER_LIST_EVENT_INVALID", "Journal observation güvenli tipte değil."
                )
            observation_id = _observation_id(observation)
            if observation_id in identifiers:
                raise OrderListEventStoreError(
                    "ORDER_LIST_EVENT_CONFLICT", "Journal observation kimlikleri tekil olmalıdır."
                )
            identifiers.add(observation_id)
            observed_at = _observed_at(observation)
            if last_time is not None and observed_at < last_time:
                raise OrderListEventStoreError(
                    "ORDER_LIST_EVENT_OUT_OF_ORDER", "Journal zamanı geriye gidemez."
                )
            _validate_observation_identity(self.identity, observation)
            if isinstance(observation, (OrderListVenueEvent, UserDataOrderListEvent)):
                if last_status is not None:
                    _validate_status_transition(last_status, observation.list_status)
                if last_status in {OrderListStatus.ALL_DONE, OrderListStatus.REJECT}:
                    raise OrderListEventStoreError(
                        "ORDER_LIST_TERMINAL_EVENT", "Terminal OCO listesi yeni event alamaz."
                    )
                last_status = observation.list_status
            elif last_status in {OrderListStatus.ALL_DONE, OrderListStatus.REJECT}:
                raise OrderListEventStoreError(
                    "ORDER_LIST_TERMINAL_EVENT", "Terminal OCO listesi yeni observation alamaz."
                )
            last_time = observed_at


@dataclass(frozen=True, slots=True)
class OrderListEventStore:
    """Own one bounded OCO event journal without order or economic authority."""

    path: Path
    db: sqlite3.Connection

    @classmethod
    def create(cls, path: Path, identity: OcoOrderListIdentity) -> "OrderListEventStore":
        validated = _validate_path(path)
        if validated.exists():
            raise OrderListEventStoreError(
                "ORDER_LIST_EVENT_STORE_EXISTS", "OCO event store mevcut dosyanın üzerine yazamaz."
            )
        if not isinstance(identity, OcoOrderListIdentity):
            raise OrderListEventStoreError(
                "ORDER_LIST_IDENTITY_INVALID", "OCO identity güvenli tipte değil."
            )
        try:
            with validated.open("xb"):
                pass
            db = _connect(validated)
            store = cls(validated, db)
            store._initialize(identity)
            return store
        except OrderListEventStoreError:
            if "db" in locals():
                db.close()
            raise
        except (OSError, sqlite3.Error) as exc:
            if "db" in locals():
                db.close()
            raise OrderListEventStoreError(
                "ORDER_LIST_EVENT_STORE_UNAVAILABLE", "OCO event store açılamadı."
            ) from exc

    @classmethod
    def open(cls, path: Path) -> "OrderListEventStore":
        validated = _validate_path(path)
        if not validated.is_file():
            raise OrderListEventStoreError(
                "ORDER_LIST_EVENT_STORE_MISSING", "OCO event store bulunamadı."
            )
        try:
            db = _connect(validated)
            if (
                db.execute("PRAGMA application_id").fetchone()[0] != JOURNAL_APPLICATION_ID
                or db.execute("PRAGMA user_version").fetchone()[0] != JOURNAL_SCHEMA_VERSION
            ):
                raise OrderListEventStoreError(
                    "ORDER_LIST_EVENT_STORE_UNSUPPORTED", "OCO event store şeması desteklenmiyor."
                )
            metadata = dict(db.execute("SELECT key, value FROM metadata"))
            if metadata.get("store") != "offline-order-list-events-1" or metadata.get(
                "scope"
            ) != "DURABLE_OCO_VENUE_EVIDENCE_JOURNAL":
                raise OrderListEventStoreError(
                    "ORDER_LIST_EVENT_METADATA_INVALID", "OCO event store metadata geçersiz."
                )
            store = cls(validated, db)
            store.load()
            return store
        except OrderListEventStoreError:
            if "db" in locals():
                db.close()
            raise
        except (OSError, sqlite3.Error) as exc:
            if "db" in locals():
                db.close()
            raise OrderListEventStoreError(
                "ORDER_LIST_EVENT_STORE_UNAVAILABLE", "OCO event store açılamadı."
            ) from exc

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "OrderListEventStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def append_event(self, event: OrderListVenueEvent) -> OrderListJournalRecordOutcome:
        """Persist one exact-list/leg event only when its identity matches."""

        if not isinstance(event, OrderListVenueEvent):
            raise OrderListEventStoreError(
                "ORDER_LIST_EVENT_INVALID", "Venue event güvenli tipte değil."
            )
        evidence = reconcile_order_list_event(self.load().identity, event)
        if evidence.outcome is not OrderListEventOutcome.MATCHED:
            raise OrderListEventStoreError(
                "ORDER_LIST_EVENT_CONFLICT", "Venue event OCO identity ile eşleşmiyor."
            )
        return self._append(event)

    def append_cancel_replace(
        self, identity: CancelReplaceIdentity
    ) -> OrderListJournalRecordOutcome:
        """Persist cancel-replace evidence without replacing the OCO identity."""

        if not isinstance(identity, CancelReplaceIdentity):
            raise OrderListEventStoreError(
                "CANCEL_REPLACE_IDENTITY_INVALID", "Cancel-replace identity güvenli tipte değil."
            )
        return self._append(identity)

    def append_user_data_event(
        self, event: UserDataOrderListEvent
    ) -> OrderListJournalRecordOutcome:
        """Persist listStatus identity without inventing leg status or economics."""

        if not isinstance(event, UserDataOrderListEvent):
            raise OrderListEventStoreError(
                "USER_STREAM_ORDER_LIST_EVENT_INVALID",
                "User Data Stream listStatus güvenli tipte değil.",
            )
        return self._append(event)

    def load(self) -> OrderListEventJournalSnapshot:
        """Replay and validate the complete ordered journal."""

        self.db.execute("BEGIN")
        try:
            result = self._load_unlocked()
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def load_user_data_events(self) -> tuple[UserDataOrderListEvent, ...]:
        """Expose only listStatus observations for offline coordinator hydration."""

        return tuple(
            observation
            for observation in self.load().observations
            if isinstance(observation, UserDataOrderListEvent)
        )

    def _initialize(self, identity: OcoOrderListIdentity) -> None:
        identity_payload = _canonical(_identity_payload(identity))
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute(f"PRAGMA application_id={JOURNAL_APPLICATION_ID}")
            self.db.execute(f"PRAGMA user_version={JOURNAL_SCHEMA_VERSION}")
            self.db.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            self.db.execute(
                "CREATE TABLE order_list_identity(identity_payload TEXT NOT NULL, identity_hash TEXT NOT NULL)"
            )
            self.db.execute(
                "CREATE TABLE order_list_event_observations("
                "sequence INTEGER PRIMARY KEY, observation_id TEXT UNIQUE NOT NULL, "
                "observation_type TEXT NOT NULL, observed_at_ms INTEGER NOT NULL, "
                "observation_payload TEXT NOT NULL, observation_hash TEXT NOT NULL)"
            )
            self.db.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                (
                    ("store", "offline-order-list-events-1"),
                    ("scope", "DURABLE_OCO_VENUE_EVIDENCE_JOURNAL"),
                ),
            )
            self.db.execute(
                "INSERT INTO order_list_identity(identity_payload, identity_hash) VALUES (?, ?)",
                (identity_payload, _digest(identity_payload)),
            )
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _append(
        self, observation: OrderListVenueEvent | CancelReplaceIdentity | UserDataOrderListEvent
    ) -> OrderListJournalRecordOutcome:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            observation_id = _observation_id(observation)
            payload = _canonical(_observation_payload(observation))
            prior = self.db.execute(
                "SELECT observation_type, observed_at_ms, observation_payload, observation_hash "
                "FROM order_list_event_observations WHERE observation_id=?",
                (observation_id,),
            ).fetchone()
            if prior is not None:
                if prior[3] != _digest(prior[2]) or prior[0:3] != (
                    _observation_type(observation),
                    _observed_at(observation),
                    payload,
                ):
                    raise OrderListEventStoreError(
                        "ORDER_LIST_EVENT_CONFLICT",
                        "Aynı observation kimliği farklı veya bozuk kayıtla kullanılamaz.",
                    )
                self.db.execute("COMMIT")
                return OrderListJournalRecordOutcome.DUPLICATE
            snapshot = self._load_unlocked()
            next_observations = snapshot.observations + (observation,)
            OrderListEventJournalSnapshot(snapshot.identity, next_observations)
            if len(next_observations) > MAX_ORDER_LIST_OBSERVATIONS:
                raise OrderListEventStoreError(
                    "ORDER_LIST_EVENT_LIMIT", "OCO event journal kapasitesi aşılamaz."
                )
            sequence = len(next_observations)
            self.db.execute(
                "INSERT INTO order_list_event_observations("
                "sequence, observation_id, observation_type, observed_at_ms, "
                "observation_payload, observation_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    sequence,
                    observation_id,
                    _observation_type(observation),
                    _observed_at(observation),
                    payload,
                    _digest(payload),
                ),
            )
            self.db.execute("COMMIT")
            return OrderListJournalRecordOutcome.ACCEPTED
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _load_unlocked(self) -> OrderListEventJournalSnapshot:
        identity_rows = self.db.execute(
            "SELECT identity_payload, identity_hash FROM order_list_identity"
        ).fetchall()
        if len(identity_rows) != 1:
            raise OrderListEventStoreError(
                "ORDER_LIST_IDENTITY_RECORD_INVALID", "Tek OCO identity kaydı bekleniyordu."
            )
        identity_payload, identity_hash = identity_rows[0]
        identity = _decode_identity(identity_payload, identity_hash)
        rows = self.db.execute(
            "SELECT sequence, observation_id, observation_type, observed_at_ms, "
            "observation_payload, observation_hash FROM order_list_event_observations "
            "ORDER BY sequence"
        ).fetchall()
        if len(rows) > MAX_ORDER_LIST_OBSERVATIONS:
            raise OrderListEventStoreError(
                "ORDER_LIST_EVENT_LIMIT", "OCO event journal kapasitesi geçersiz."
            )
        observations = []
        for expected_sequence, row in enumerate(rows, start=1):
            sequence, observation_id, observation_type, observed_at_ms, payload, payload_hash = row
            if (
                sequence != expected_sequence
                or not isinstance(observation_id, str)
                or observation_type not in {
                    "VENUE_EVENT",
                    "CANCEL_REPLACE",
                    "USER_STREAM_LIST_STATUS",
                }
                or type(observed_at_ms) is not int
                or not isinstance(payload, str)
                or not isinstance(payload_hash, str)
                or _digest(payload) != payload_hash
            ):
                raise OrderListEventStoreError(
                    "ORDER_LIST_EVENT_RECORD_CORRUPT",
                    "OCO event journal sıra veya checksum doğrulanamadı.",
                )
            observation = _decode_observation(payload, observation_type)
            if _observation_id(observation) != observation_id or _observed_at(observation) != observed_at_ms:
                raise OrderListEventStoreError(
                    "ORDER_LIST_EVENT_RECORD_CORRUPT",
                    "OCO event journal kimliği payload ile eşleşmiyor.",
                )
            observations.append(observation)
        return OrderListEventJournalSnapshot(identity, tuple(observations))


def _validate_observation_identity(
    identity: OcoOrderListIdentity,
    observation: OrderListVenueEvent | CancelReplaceIdentity | UserDataOrderListEvent,
) -> None:
    if isinstance(observation, OrderListVenueEvent):
        evidence = reconcile_order_list_event(identity, observation)
        if evidence.outcome is not OrderListEventOutcome.MATCHED:
            raise OrderListEventStoreError(
                "ORDER_LIST_EVENT_CONFLICT", "Venue event OCO identity ile eşleşmiyor."
            )
        return
    if isinstance(observation, UserDataOrderListEvent):
        if (
            observation.order_list_id,
            observation.list_client_order_id,
            observation.symbol,
            observation.contingency_type,
        ) != (
            identity.order_list_id,
            identity.list_client_order_id,
            identity.symbol,
            identity.contingency_type.value,
        ):
            raise OrderListEventStoreError(
                "USER_STREAM_ORDER_LIST_IDENTITY_CONFLICT",
                "User Data Stream listStatus OCO identity ile eşleşmiyor.",
            )
        event_legs = {(order.order_id, order.client_order_id) for order in observation.orders}
        identity_legs = {(leg.order_id, leg.client_order_id) for leg in identity.legs}
        if event_legs != identity_legs:
            raise OrderListEventStoreError(
                "USER_STREAM_ORDER_LIST_LEG_CONFLICT",
                "User Data Stream listStatus leg identity OCO ile eşleşmiyor.",
            )
        return
    prior = (observation.prior_order_id, observation.prior_client_order_id)
    if prior not in {(leg.order_id, leg.client_order_id) for leg in identity.legs}:
        raise OrderListEventStoreError(
            "CANCEL_REPLACE_PRIOR_IDENTITY_CONFLICT",
            "Cancel-replace prior identity OCO leg’lerinden biri olmalıdır.",
        )
    if observation.replacement_order_id == observation.prior_order_id:
        raise OrderListEventStoreError(
            "CANCEL_REPLACE_REPLACEMENT_IDENTITY_CONFLICT",
            "Replacement order identity prior identity ile aynı olamaz.",
        )


def _validate_status_transition(current: OrderListStatus, next_status: OrderListStatus) -> None:
    rank = {
        OrderListStatus.EXEC_STARTED: 0,
        OrderListStatus.EXECUTING: 1,
        OrderListStatus.ALL_DONE: 2,
        OrderListStatus.REJECT: 2,
    }
    if rank[next_status] < rank[current]:
        raise OrderListEventStoreError(
            "ORDER_LIST_EVENT_STATUS_OUT_OF_ORDER", "OCO list status geriye gidemez."
        )


def _observation_type(observation: object) -> str:
    if isinstance(observation, OrderListVenueEvent):
        return "VENUE_EVENT"
    if isinstance(observation, CancelReplaceIdentity):
        return "CANCEL_REPLACE"
    if isinstance(observation, UserDataOrderListEvent):
        return "USER_STREAM_LIST_STATUS"
    raise OrderListEventStoreError("ORDER_LIST_EVENT_INVALID", "Journal observation güvenli tipte değil.")


def _observation_id(
    observation: OrderListVenueEvent | CancelReplaceIdentity | UserDataOrderListEvent,
) -> str:
    return (
        observation.event_id
        if isinstance(observation, (OrderListVenueEvent, UserDataOrderListEvent))
        else observation.operation_id
    )


def _observed_at(
    observation: OrderListVenueEvent | CancelReplaceIdentity | UserDataOrderListEvent,
) -> int:
    if isinstance(observation, UserDataOrderListEvent):
        return observation.transaction_time_ms
    return observation.event_time_ms if isinstance(observation, OrderListVenueEvent) else observation.observed_at_ms


def _observation_payload(
    observation: OrderListVenueEvent | CancelReplaceIdentity | UserDataOrderListEvent,
) -> dict[str, object]:
    if isinstance(observation, OrderListVenueEvent):
        return {
            "client_order_id": observation.client_order_id,
            "event_id": observation.event_id,
            "event_time_ms": observation.event_time_ms,
            "leg_status": observation.leg_status.value,
            "list_client_order_id": observation.list_client_order_id,
            "list_order_status": observation.list_order_status.value,
            "list_status": observation.list_status.value,
            "order_id": observation.order_id,
            "order_list_id": observation.order_list_id,
            "observation_type": "VENUE_EVENT",
        }
    if isinstance(observation, UserDataOrderListEvent):
        return {
            "contingency_type": observation.contingency_type,
            "event_id": observation.event_id,
            "event_time_ms": observation.event_time_ms,
            "list_client_order_id": observation.list_client_order_id,
            "list_order_status": observation.list_order_status.value,
            "list_status": observation.list_status.value,
            "order_list_id": observation.order_list_id,
            "orders": [
                {
                    "client_order_id": order.client_order_id,
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                }
                for order in observation.orders
            ],
            "symbol": observation.symbol,
            "transaction_time_ms": observation.transaction_time_ms,
            "observation_type": "USER_STREAM_LIST_STATUS",
        }
    return {
        "cancel_result": observation.cancel_result,
        "new_order_result": observation.new_order_result,
        "observed_at_ms": observation.observed_at_ms,
        "operation_id": observation.operation_id,
        "prior_client_order_id": observation.prior_client_order_id,
        "prior_order_id": observation.prior_order_id,
        "replacement_client_order_id": observation.replacement_client_order_id,
        "replacement_order_id": observation.replacement_order_id,
        "observation_type": "CANCEL_REPLACE",
    }


def _decode_identity(payload: object, payload_hash: object) -> OcoOrderListIdentity:
    if not isinstance(payload, str) or not isinstance(payload_hash, str) or _digest(payload) != payload_hash:
        raise OrderListEventStoreError("ORDER_LIST_IDENTITY_CORRUPT", "OCO identity checksum doğrulanamadı.")
    try:
        data = json.loads(payload)
        legs = tuple(
            OrderListLegIdentity(
                leg_id=item["leg_id"],
                order_id=item["order_id"],
                client_order_id=item["client_order_id"],
                role=item["role"],
                order_type=item["order_type"],
            )
            for item in data["legs"]
        )
        return OcoOrderListIdentity(
            order_list_id=data["order_list_id"],
            list_client_order_id=data["list_client_order_id"],
            symbol=data["symbol"],
            legs=legs,
            contingency_type=data["contingency_type"],
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, OrderListError) as exc:
        raise OrderListEventStoreError("ORDER_LIST_IDENTITY_CORRUPT", "OCO identity payload geçersiz.") from exc


def _decode_observation(
    payload: object, observation_type: object
) -> OrderListVenueEvent | CancelReplaceIdentity | UserDataOrderListEvent:
    if not isinstance(payload, str) or observation_type not in {
        "VENUE_EVENT",
        "CANCEL_REPLACE",
        "USER_STREAM_LIST_STATUS",
    }:
        raise OrderListEventStoreError("ORDER_LIST_EVENT_RECORD_CORRUPT", "OCO event payload geçersiz.")
    try:
        data = json.loads(payload)
        if not isinstance(data, dict) or data.get("observation_type") != observation_type:
            raise ValueError("Unexpected observation type")
        data.pop("observation_type")
        if observation_type == "VENUE_EVENT":
            return OrderListVenueEvent(**data)
        if observation_type == "CANCEL_REPLACE":
            return CancelReplaceIdentity(**data)
        data["orders"] = tuple(
            UserDataOrderListLeg(
                symbol=order["symbol"],
                order_id=order["order_id"],
                client_order_id=order["client_order_id"],
            )
            for order in data["orders"]
        )
        return UserDataOrderListEvent(**data)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, OrderListError) as exc:
        raise OrderListEventStoreError("ORDER_LIST_EVENT_RECORD_CORRUPT", "OCO event payload doğrulanamadı.") from exc
