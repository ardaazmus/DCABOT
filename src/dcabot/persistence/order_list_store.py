"""Durable, offline SQLite replay owner for the bounded OCO projection."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3

from dcabot.application.order_list_contract import (
    MAX_ORDER_LIST_OBSERVATIONS,
    OcoOrderListIdentity,
    OrderListError,
    OrderListLegIdentity,
    OrderListObservation,
    OrderListObservationOutcome,
    OrderListSnapshot,
    admit_order_list_observation,
)


APPLICATION_ID = 0x44434F53
SCHEMA_VERSION = 1


class OrderListStoreError(ValueError):
    """Raised when the durable OCO replay owner cannot be trusted."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class OrderListStore:
    """Own one bounded OCO identity/observation journal without economic authority."""

    path: Path
    db: sqlite3.Connection

    @classmethod
    def create(
        cls,
        path: Path,
        identity: OcoOrderListIdentity,
        initial_observation: OrderListObservation,
    ) -> "OrderListStore":
        validated = _validate_path(path)
        if validated.exists():
            raise OrderListStoreError("ORDER_LIST_STORE_EXISTS", "OCO store mevcut dosyanın üzerine yazamaz.")
        _validate_identity(identity)
        _validate_observation(initial_observation)
        try:
            validated.parent.mkdir(parents=True, exist_ok=True)
            with validated.open("xb"):
                pass
            db = _connect(validated)
            store = cls(validated, db)
            store._initialize(identity, initial_observation)
            return store
        except OrderListStoreError:
            if "db" in locals():
                db.close()
            raise
        except (OSError, sqlite3.Error) as exc:
            if "db" in locals():
                db.close()
            raise OrderListStoreError("ORDER_LIST_STORE_UNAVAILABLE", "OCO store açılamadı.") from exc

    @classmethod
    def open(cls, path: Path) -> "OrderListStore":
        validated = _validate_path(path)
        if not validated.is_file():
            raise OrderListStoreError("ORDER_LIST_STORE_MISSING", "OCO store bulunamadı.")
        try:
            db = _connect(validated)
            if (
                db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
                or db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION
            ):
                raise OrderListStoreError("ORDER_LIST_STORE_UNSUPPORTED", "OCO store şeması desteklenmiyor.")
            metadata = dict(db.execute("SELECT key, value FROM metadata"))
            if metadata.get("store") != "offline-order-list-1" or metadata.get(
                "scope"
            ) != "DURABLE_OCO_ORDER_LIST_PROJECTION":
                raise OrderListStoreError("ORDER_LIST_METADATA_INVALID", "OCO store metadata geçersiz.")
            store = cls(validated, db)
            store._load_unlocked()
            return store
        except OrderListStoreError:
            if "db" in locals():
                db.close()
            raise
        except (OSError, sqlite3.Error) as exc:
            if "db" in locals():
                db.close()
            raise OrderListStoreError("ORDER_LIST_STORE_UNAVAILABLE", "OCO store açılamadı.") from exc

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "OrderListStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def append(self, observation: OrderListObservation) -> OrderListObservationOutcome:
        """Atomically append one ordered venue observation or return an exact duplicate."""

        _validate_observation(observation)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            payload = _canonical(_observation_payload(observation))
            prior = self.db.execute(
                "SELECT observation_payload, observation_hash FROM order_list_observations "
                "WHERE event_id=?",
                (observation.event_id,),
            ).fetchone()
            if prior is not None:
                if prior[1] != _digest(prior[0]) or prior[0] != payload:
                    raise OrderListStoreError(
                        "ORDER_LIST_EVENT_CONFLICT",
                        "Aynı event kimliği farklı veya bozuk kayıtla kullanılamaz.",
                    )
                self.db.execute("COMMIT")
                return OrderListObservationOutcome.DUPLICATE
            snapshot = self._load_unlocked()
            result = snapshot.apply(observation)
            sequence = len(result.snapshot.observations)
            self.db.execute(
                "INSERT INTO order_list_observations(sequence, event_id, observation_payload, "
                "observation_hash) VALUES (?, ?, ?, ?)",
                (sequence, observation.event_id, payload, _digest(payload)),
            )
            self.db.execute("COMMIT")
            return result.outcome
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def load(self) -> OrderListSnapshot:
        """Replay the complete durable OCO projection and verify every checksum."""

        self.db.execute("BEGIN")
        try:
            result = self._load_unlocked()
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _initialize(
        self,
        identity: OcoOrderListIdentity,
        initial_observation: OrderListObservation,
    ) -> None:
        try:
            _validate_observation_identity(identity, initial_observation)
            snapshot = admit_order_list_observation(identity, initial_observation)
        except OrderListError as exc:
            raise OrderListStoreError(
                "ORDER_LIST_INITIALIZATION_INVALID", "İlk OCO observation doğrulanamadı."
            ) from exc
        identity_payload = _canonical(_identity_payload(identity))
        observation_payload = _canonical(_observation_payload(initial_observation))
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute(f"PRAGMA application_id={APPLICATION_ID}")
            self.db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
            self.db.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            self.db.execute(
                "CREATE TABLE order_list_identity(identity_payload TEXT NOT NULL, identity_hash TEXT NOT NULL)"
            )
            self.db.execute(
                "CREATE TABLE order_list_observations(" 
                "sequence INTEGER PRIMARY KEY, event_id TEXT UNIQUE NOT NULL, "
                "observation_payload TEXT NOT NULL, observation_hash TEXT NOT NULL)"
            )
            self.db.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                (
                    ("store", "offline-order-list-1"),
                    ("scope", "DURABLE_OCO_ORDER_LIST_PROJECTION"),
                ),
            )
            self.db.execute(
                "INSERT INTO order_list_identity(identity_payload, identity_hash) VALUES (?, ?)",
                (identity_payload, _digest(identity_payload)),
            )
            self.db.execute(
                "INSERT INTO order_list_observations(sequence, event_id, observation_payload, observation_hash) "
                "VALUES (?, ?, ?, ?)",
                (1, initial_observation.event_id, observation_payload, _digest(observation_payload)),
            )
            if snapshot.observations != (initial_observation,):
                raise OrderListStoreError("ORDER_LIST_INITIALIZATION_INVALID", "İlk OCO observation doğrulanamadı.")
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _load_unlocked(self) -> OrderListSnapshot:
        identity_rows = self.db.execute(
            "SELECT identity_payload, identity_hash FROM order_list_identity"
        ).fetchall()
        if len(identity_rows) != 1:
            raise OrderListStoreError("ORDER_LIST_IDENTITY_RECORD_INVALID", "Tek OCO identity kaydı bekleniyordu.")
        identity_payload, identity_hash = identity_rows[0]
        identity = _decode_identity(identity_payload, identity_hash)
        rows = self.db.execute(
            "SELECT sequence, event_id, observation_payload, observation_hash "
            "FROM order_list_observations ORDER BY sequence"
        ).fetchall()
        if not rows or len(rows) > MAX_ORDER_LIST_OBSERVATIONS:
            raise OrderListStoreError("ORDER_LIST_OBSERVATION_LIMIT", "OCO observation sınırı geçersiz.")
        snapshot: OrderListSnapshot | None = None
        for expected_sequence, row in enumerate(rows, start=1):
            sequence, event_id, payload, payload_hash = row
            if (
                sequence != expected_sequence
                or not isinstance(event_id, str)
                or not isinstance(payload, str)
                or not isinstance(payload_hash, str)
                or _digest(payload) != payload_hash
            ):
                raise OrderListStoreError("ORDER_LIST_RECORD_CORRUPT", "OCO sıra veya checksum doğrulanamadı.")
            observation = _decode_observation(payload, event_id)
            try:
                snapshot = (
                    admit_order_list_observation(identity, observation)
                    if snapshot is None
                    else snapshot.apply(observation).snapshot
                )
            except OrderListError as exc:
                raise OrderListStoreError(
                    "ORDER_LIST_RECORD_CORRUPT", "OCO observation replay edilemedi."
                ) from exc
        if snapshot is None:
            raise OrderListStoreError("ORDER_LIST_OBSERVATION_MISSING", "OCO observation kaydı bulunamadı.")
        return snapshot


def _validate_identity(identity: object) -> None:
    if not isinstance(identity, OcoOrderListIdentity):
        raise OrderListStoreError("ORDER_LIST_IDENTITY_INVALID", "OCO identity güvenli tipte değil.")


def _validate_observation(observation: object) -> None:
    if not isinstance(observation, OrderListObservation):
        raise OrderListStoreError("ORDER_LIST_OBSERVATION_INVALID", "OCO observation güvenli tipte değil.")


def _validate_observation_identity(
    identity: OcoOrderListIdentity,
    observation: OrderListObservation,
) -> None:
    if (observation.order_list_id, observation.list_client_order_id) != (
        identity.order_list_id,
        identity.list_client_order_id,
    ):
        raise OrderListStoreError("ORDER_LIST_IDENTITY_MISMATCH", "Observation OCO identity ile eşleşmiyor.")


def _identity_payload(identity: OcoOrderListIdentity) -> dict[str, object]:
    return {
        "order_list_id": identity.order_list_id,
        "list_client_order_id": identity.list_client_order_id,
        "symbol": identity.symbol,
        "contingency_type": identity.contingency_type.value,
        "legs": [
            {
                "leg_id": leg.leg_id,
                "order_id": leg.order_id,
                "client_order_id": leg.client_order_id,
                "role": leg.role.value,
                "order_type": leg.order_type,
            }
            for leg in identity.legs
        ],
    }


def _observation_payload(observation: OrderListObservation) -> dict[str, object]:
    return {
        "event_id": observation.event_id,
        "order_list_id": observation.order_list_id,
        "list_client_order_id": observation.list_client_order_id,
        "list_status": observation.list_status.value,
        "list_order_status": observation.list_order_status.value,
        "leg_statuses": [status.value for status in observation.leg_statuses],
        "observed_at_ms": observation.observed_at_ms,
    }


def _decode_identity(payload: object, payload_hash: object) -> OcoOrderListIdentity:
    if not isinstance(payload, str) or not isinstance(payload_hash, str) or _digest(payload) != payload_hash:
        raise OrderListStoreError("ORDER_LIST_IDENTITY_CORRUPT", "OCO identity checksum doğrulanamadı.")
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
        raise OrderListStoreError("ORDER_LIST_IDENTITY_CORRUPT", "OCO identity payload geçersiz.") from exc


def _decode_observation(payload: object, event_id: object) -> OrderListObservation:
    if not isinstance(payload, str):
        raise OrderListStoreError("ORDER_LIST_RECORD_CORRUPT", "OCO observation payload metin değil.")
    try:
        data = json.loads(payload)
        if isinstance(data, dict) and isinstance(data.get("leg_statuses"), list):
            data["leg_statuses"] = tuple(data["leg_statuses"])
        observation = OrderListObservation(**data)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, OrderListError) as exc:
        raise OrderListStoreError("ORDER_LIST_RECORD_CORRUPT", "OCO observation payload geçersiz.") from exc
    if observation.event_id != event_id:
        raise OrderListStoreError("ORDER_LIST_RECORD_CORRUPT", "OCO event kimliği payload ile eşleşmiyor.")
    return observation


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_path(path: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve()
    if "YEDEK_ESKI_PROJE" in resolved.parts or any(
        item.is_symlink() or bool(getattr(item, "is_junction", lambda: False)())
        for item in (candidate, *candidate.parents)
    ):
        raise OrderListStoreError("ORDER_LIST_STORE_PATH_UNSAFE", "OCO store backup/linked path üzerinde olamaz.")
    if candidate.exists() and not candidate.is_file():
        raise OrderListStoreError("ORDER_LIST_STORE_PATH_INVALID", "OCO store yolu dosya olmalıdır.")
    if not resolved.parent.is_dir():
        raise OrderListStoreError("ORDER_LIST_STORE_PATH_INVALID", "OCO store parent yolu bulunmalıdır.")
    return candidate


def _connect(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=rw", uri=True, isolation_level=None, timeout=5)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    return db
