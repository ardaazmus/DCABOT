"""Offline OCO order-list identity and replay-boundary contract.

This module records venue facts only.  It deliberately has no fill, reserve,
price, quantity, core-event, persistence, or transport authority.
"""

from dataclasses import dataclass, replace
from enum import StrEnum
import hashlib
import json
import re


MAX_ORDER_LIST_OBSERVATIONS = 128


class OrderListError(ValueError):
    """Raised when an order-list identity or observation is untrusted."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class OrderListContingency(StrEnum):
    OCO = "OCO"


class OrderListLegRole(StrEnum):
    WORKING = "WORKING"
    PENDING = "PENDING"


class OrderListStatus(StrEnum):
    EXEC_STARTED = "EXEC_STARTED"
    EXECUTING = "EXECUTING"
    ALL_DONE = "ALL_DONE"
    REJECT = "REJECT"


class OrderListLegStatus(StrEnum):
    NEW = "NEW"
    PENDING_NEW = "PENDING_NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    EXPIRED_IN_MATCH = "EXPIRED_IN_MATCH"


class OrderListObservationOutcome(StrEnum):
    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True, slots=True)
class OrderListLegIdentity:
    """One OCO leg; it contains identity and venue type only."""

    leg_id: str
    order_id: int
    client_order_id: str
    role: OrderListLegRole
    order_type: str

    def __post_init__(self) -> None:
        _identifier(self.leg_id, "ORDER_LIST_LEG_ID_INVALID")
        if type(self.order_id) is not int or self.order_id <= 0:
            raise OrderListError("ORDER_LIST_ORDER_ID_INVALID", "orderId pozitif integer olmalıdır.")
        _identifier(self.client_order_id, "ORDER_LIST_CLIENT_ORDER_ID_INVALID")
        try:
            role = OrderListLegRole(self.role)
        except (TypeError, ValueError) as exc:
            raise OrderListError("ORDER_LIST_ROLE_INVALID", "working/pending rolü geçersiz.") from exc
        object.__setattr__(self, "role", role)
        if self.order_type not in {
            "LIMIT",
            "LIMIT_MAKER",
            "STOP_LOSS",
            "STOP_LOSS_LIMIT",
            "TAKE_PROFIT",
            "TAKE_PROFIT_LIMIT",
        }:
            raise OrderListError("ORDER_LIST_ORDER_TYPE_INVALID", "OCO order türü desteklenmiyor.")
        if role is OrderListLegRole.WORKING and self.order_type not in {"LIMIT", "LIMIT_MAKER"}:
            raise OrderListError("ORDER_LIST_WORKING_TYPE_INVALID", "Working bacak LIMIT veya LIMIT_MAKER olmalıdır.")
        if role is OrderListLegRole.PENDING and self.order_type not in {
            "STOP_LOSS",
            "STOP_LOSS_LIMIT",
            "TAKE_PROFIT",
            "TAKE_PROFIT_LIMIT",
        }:
            raise OrderListError("ORDER_LIST_PENDING_TYPE_INVALID", "Pending bacak conditional OCO türü olmalıdır.")


@dataclass(frozen=True, slots=True)
class OcoOrderListIdentity:
    """Immutable two-leg identity; no order or economic authority."""

    order_list_id: int
    list_client_order_id: str
    symbol: str
    legs: tuple[OrderListLegIdentity, OrderListLegIdentity]
    contingency_type: OrderListContingency = OrderListContingency.OCO

    def __post_init__(self) -> None:
        if type(self.order_list_id) is not int or self.order_list_id <= 0:
            raise OrderListError("ORDER_LIST_ID_INVALID", "orderListId pozitif integer olmalıdır.")
        _identifier(self.list_client_order_id, "ORDER_LIST_CLIENT_ID_INVALID")
        _symbol(self.symbol)
        try:
            contingency_type = OrderListContingency(self.contingency_type)
        except (TypeError, ValueError) as exc:
            raise OrderListError("ORDER_LIST_CONTINGENCY_INVALID", "Contingency türü desteklenmiyor.") from exc
        object.__setattr__(self, "contingency_type", contingency_type)
        if type(self.legs) is not tuple or len(self.legs) != 2 or any(
            not isinstance(leg, OrderListLegIdentity) for leg in self.legs
        ):
            raise OrderListError("ORDER_LIST_LEGS_INVALID", "OCO tam olarak iki leg identity taşımalıdır.")
        if tuple(leg.role for leg in self.legs) != (
            OrderListLegRole.WORKING,
            OrderListLegRole.PENDING,
        ):
            raise OrderListError("ORDER_LIST_LEG_ROLES_INVALID", "Leg sırası WORKING, PENDING olmalıdır.")
        if len({leg.leg_id for leg in self.legs}) != 2 or len({leg.order_id for leg in self.legs}) != 2:
            raise OrderListError("ORDER_LIST_LEG_IDENTITY_CONFLICT", "Leg ve order kimlikleri tekil olmalıdır.")
        if len({leg.client_order_id for leg in self.legs}) != 2:
            raise OrderListError("ORDER_LIST_CLIENT_ID_CONFLICT", "Leg clientOrderId değerleri tekil olmalıdır.")


@dataclass(frozen=True, slots=True)
class UserDataOrderListLeg:
    """Identity-only leg received from Binance listStatus; no role or type."""

    symbol: str
    order_id: int
    client_order_id: str

    def __post_init__(self) -> None:
        _symbol(self.symbol)
        if type(self.order_id) is not int or self.order_id <= 0:
            raise OrderListError("USER_STREAM_ORDER_LIST_ORDER_ID_INVALID", "orderId pozitif integer olmalıdır.")
        _identifier(self.client_order_id, "USER_STREAM_ORDER_LIST_CLIENT_ID_INVALID")


@dataclass(frozen=True, slots=True)
class UserDataOrderListEvent:
    """Redacted listStatus identity kept separate from leg status or economics."""

    event_id: str
    event_time_ms: int
    transaction_time_ms: int
    symbol: str
    order_list_id: int
    contingency_type: str
    list_status: OrderListStatus
    list_order_status: OrderListStatus
    list_client_order_id: str
    orders: tuple[UserDataOrderListLeg, UserDataOrderListLeg]

    def __post_init__(self) -> None:
        _identifier(self.event_id, "USER_STREAM_ORDER_LIST_EVENT_ID_INVALID")
        if type(self.event_time_ms) is not int or self.event_time_ms < 0:
            raise OrderListError("USER_STREAM_ORDER_LIST_EVENT_TIME_INVALID", "event time negatif olamaz.")
        if type(self.transaction_time_ms) is not int or self.transaction_time_ms < 0:
            raise OrderListError(
                "USER_STREAM_ORDER_LIST_TRANSACTION_TIME_INVALID",
                "transaction time negatif olamaz.",
            )
        _symbol(self.symbol)
        if type(self.order_list_id) is not int or self.order_list_id <= 0:
            raise OrderListError("USER_STREAM_ORDER_LIST_ID_INVALID", "orderListId pozitif integer olmalıdır.")
        if self.contingency_type != "OCO":
            raise OrderListError("USER_STREAM_ORDER_LIST_UNSUPPORTED", "Yalnız OCO listStatus destekleniyor.")
        _identifier(self.list_client_order_id, "USER_STREAM_ORDER_LIST_CLIENT_ID_INVALID")
        try:
            object.__setattr__(self, "list_status", OrderListStatus(self.list_status))
            object.__setattr__(self, "list_order_status", OrderListStatus(self.list_order_status))
        except (TypeError, ValueError) as exc:
            raise OrderListError("USER_STREAM_ORDER_LIST_STATUS_INVALID", "OCO liste durumu geçersiz.") from exc
        if type(self.orders) is not tuple or len(self.orders) != 2 or any(
            not isinstance(order, UserDataOrderListLeg) for order in self.orders
        ):
            raise OrderListError(
                "USER_STREAM_ORDER_LIST_ORDERS_INVALID",
                "OCO listStatus iki leg identity taşımalıdır.",
            )
        if any(order.symbol != self.symbol for order in self.orders):
            raise OrderListError(
                "USER_STREAM_ORDER_LIST_SYMBOL_MISMATCH",
                "OCO leg symbol list symbol ile eşleşmiyor.",
            )
        if len({order.order_id for order in self.orders}) != 2 or len(
            {order.client_order_id for order in self.orders}
        ) != 2:
            raise OrderListError(
                "USER_STREAM_ORDER_LIST_IDENTITY_CONFLICT",
                "OCO leg identity tekil olmalıdır.",
            )


@dataclass(frozen=True, slots=True)
class UserDataOrderListResyncAnchor:
    """Offline cursor anchor; it is not proof of venue or economic authority."""

    anchor_id: str
    observed_at_ms: int
    event: UserDataOrderListEvent

    def __post_init__(self) -> None:
        _identifier(self.anchor_id, "USER_STREAM_ORDER_LIST_ANCHOR_ID_INVALID")
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise OrderListError(
                "USER_STREAM_ORDER_LIST_ANCHOR_TIME_INVALID",
                "Resync anchor zamanı negatif olmayan integer olmalıdır.",
            )
        if not isinstance(self.event, UserDataOrderListEvent):
            raise OrderListError(
                "USER_STREAM_ORDER_LIST_ANCHOR_EVENT_INVALID",
                "Resync anchor güvenli listStatus event taşımalıdır.",
            )
        if self.observed_at_ms < max(self.event.transaction_time_ms, self.event.event_time_ms):
            raise OrderListError(
                "USER_STREAM_ORDER_LIST_ANCHOR_STALE",
                "Resync anchor gözlem zamanı cursor zamanlarından eski olamaz.",
            )


@dataclass(frozen=True, slots=True)
class OrderListObservation:
    """One bounded venue-status observation aligned with identity. No fills."""

    event_id: str
    order_list_id: int
    list_client_order_id: str
    list_status: OrderListStatus
    list_order_status: OrderListStatus
    leg_statuses: tuple[OrderListLegStatus, OrderListLegStatus]
    observed_at_ms: int

    def __post_init__(self) -> None:
        _identifier(self.event_id, "ORDER_LIST_EVENT_ID_INVALID")
        if type(self.order_list_id) is not int or self.order_list_id <= 0:
            raise OrderListError("ORDER_LIST_ID_INVALID", "orderListId pozitif integer olmalıdır.")
        _identifier(self.list_client_order_id, "ORDER_LIST_CLIENT_ID_INVALID")
        try:
            object.__setattr__(self, "list_status", OrderListStatus(self.list_status))
            object.__setattr__(self, "list_order_status", OrderListStatus(self.list_order_status))
        except (TypeError, ValueError) as exc:
            raise OrderListError("ORDER_LIST_STATUS_INVALID", "Liste durumu geçersiz.") from exc
        if type(self.leg_statuses) is not tuple or len(self.leg_statuses) != 2:
            raise OrderListError("ORDER_LIST_LEG_STATUS_INVALID", "Tam olarak iki leg status bekleniyor.")
        try:
            object.__setattr__(
                self,
                "leg_statuses",
                tuple(OrderListLegStatus(status) for status in self.leg_statuses),
            )
        except (TypeError, ValueError) as exc:
            raise OrderListError("ORDER_LIST_LEG_STATUS_INVALID", "Leg durumu geçersiz.") from exc
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise OrderListError("ORDER_LIST_TIME_INVALID", "transaction time negatif olmayan integer olmalıdır.")
        if self.list_status is OrderListStatus.ALL_DONE and self.list_order_status is not OrderListStatus.ALL_DONE:
            raise OrderListError("ORDER_LIST_TERMINAL_STATUS_INVALID", "ALL_DONE list status ALL_DONE order status gerektirir.")
        if self.list_status is OrderListStatus.REJECT and self.list_order_status is not OrderListStatus.REJECT:
            raise OrderListError("ORDER_LIST_REJECT_STATUS_INVALID", "REJECT list status REJECT order status gerektirir.")
        if self.list_status is OrderListStatus.EXEC_STARTED and self.list_order_status is not OrderListStatus.EXECUTING:
            raise OrderListError("ORDER_LIST_STARTED_STATUS_INVALID", "EXEC_STARTED list status EXECUTING order status gerektirir.")


@dataclass(frozen=True, slots=True)
class OrderListObservationResult:
    snapshot: "OrderListSnapshot"
    outcome: OrderListObservationOutcome


@dataclass(frozen=True, slots=True)
class OrderListSnapshot:
    """In-memory replay owner for venue facts, bounded to 128 observations."""

    identity: OcoOrderListIdentity
    list_status: OrderListStatus
    list_order_status: OrderListStatus
    leg_statuses: tuple[OrderListLegStatus, OrderListLegStatus]
    last_observed_at_ms: int
    observations: tuple[OrderListObservation, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.identity, OcoOrderListIdentity):
            raise OrderListError("ORDER_LIST_IDENTITY_INVALID", "OCO identity geçersiz.")
        if type(self.observations) is not tuple or len(self.observations) == 0 or len(self.observations) > MAX_ORDER_LIST_OBSERVATIONS:
            raise OrderListError("ORDER_LIST_OBSERVATION_LIMIT", "Observation geçmişi bounded olmalıdır.")
        if any(not isinstance(observation, OrderListObservation) for observation in self.observations):
            raise OrderListError("ORDER_LIST_OBSERVATION_INVALID", "Observation geçmişi güvenli tipte değil.")
        if len({observation.event_id for observation in self.observations}) != len(self.observations):
            raise OrderListError("ORDER_LIST_EVENT_CONFLICT", "Observation event kimlikleri tekil olmalıdır.")
        for index, observation in enumerate(self.observations):
            _validate_observation_identity(self.identity, observation)
            _validate_terminal_legs(observation)
            if index and observation.observed_at_ms < self.observations[index - 1].observed_at_ms:
                raise OrderListError("ORDER_LIST_EVENT_OUT_OF_ORDER", "Observation zamanı geriye gidemez.")
            if index:
                _validate_status_transition(self.observations[index - 1].list_status, observation.list_status)
        latest = self.observations[-1]
        if (self.list_status, self.list_order_status, self.leg_statuses, self.last_observed_at_ms) != (
            latest.list_status,
            latest.list_order_status,
            latest.leg_statuses,
            latest.observed_at_ms,
        ):
            raise OrderListError("ORDER_LIST_SNAPSHOT_INVALID", "Snapshot son observation ile eşleşmiyor.")
        _validate_observation_identity(self.identity, latest)

    def apply(self, observation: OrderListObservation) -> OrderListObservationResult:
        """Apply one ordered observation without producing any economic event."""

        if not isinstance(observation, OrderListObservation):
            raise OrderListError("ORDER_LIST_OBSERVATION_INVALID", "Observation güvenli tipte değil.")
        _validate_observation_identity(self.identity, observation)
        existing = next(
            (item for item in self.observations if item.event_id == observation.event_id),
            None,
        )
        if existing is not None:
            if _fingerprint(existing) == _fingerprint(observation):
                return OrderListObservationResult(self, OrderListObservationOutcome.DUPLICATE)
            raise OrderListError("ORDER_LIST_EVENT_CONFLICT", "Aynı event ID farklı payload taşıyor.")
        if observation.observed_at_ms < self.last_observed_at_ms:
            raise OrderListError("ORDER_LIST_EVENT_OUT_OF_ORDER", "Observation zamanı geriye gidemez.")
        if self.list_status in {OrderListStatus.ALL_DONE, OrderListStatus.REJECT}:
            raise OrderListError("ORDER_LIST_TERMINAL_EVENT", "Terminal order-list yeni event alamaz.")
        _validate_status_transition(self.list_status, observation.list_status)
        _validate_terminal_legs(observation)
        if len(self.observations) >= MAX_ORDER_LIST_OBSERVATIONS:
            raise OrderListError("ORDER_LIST_OBSERVATION_LIMIT", "Observation kapasitesi aşılamaz.")
        next_snapshot = replace(
            self,
            list_status=observation.list_status,
            list_order_status=observation.list_order_status,
            leg_statuses=observation.leg_statuses,
            last_observed_at_ms=observation.observed_at_ms,
            observations=self.observations + (observation,),
        )
        return OrderListObservationResult(next_snapshot, OrderListObservationOutcome.ACCEPTED)


def create_oco_identity(
    *,
    order_list_id: int,
    list_client_order_id: str,
    symbol: str,
    working: OrderListLegIdentity,
    pending: OrderListLegIdentity,
) -> OcoOrderListIdentity:
    """Create the exact two-leg identity table without order authority."""

    return OcoOrderListIdentity(
        order_list_id=order_list_id,
        list_client_order_id=list_client_order_id,
        symbol=symbol,
        legs=(working, pending),
    )


def admit_order_list_observation(
    identity: OcoOrderListIdentity,
    observation: OrderListObservation,
) -> OrderListSnapshot:
    """Admit a first observation as the bounded replay owner."""

    if not isinstance(identity, OcoOrderListIdentity):
        raise OrderListError("ORDER_LIST_IDENTITY_INVALID", "OCO identity güvenli tipte değil.")
    if not isinstance(observation, OrderListObservation):
        raise OrderListError("ORDER_LIST_OBSERVATION_INVALID", "Observation güvenli tipte değil.")
    _validate_observation_identity(identity, observation)
    _validate_terminal_legs(observation)
    return OrderListSnapshot(
        identity=identity,
        list_status=observation.list_status,
        list_order_status=observation.list_order_status,
        leg_statuses=observation.leg_statuses,
        last_observed_at_ms=observation.observed_at_ms,
        observations=(observation,),
    )


def _validate_observation_identity(identity: OcoOrderListIdentity, observation: OrderListObservation) -> None:
    if (observation.order_list_id, observation.list_client_order_id) != (
        identity.order_list_id,
        identity.list_client_order_id,
    ):
        raise OrderListError("ORDER_LIST_IDENTITY_MISMATCH", "Observation liste kimliğiyle eşleşmiyor.")


def _validate_status_transition(current: OrderListStatus, next_status: OrderListStatus) -> None:
    rank = {
        OrderListStatus.EXEC_STARTED: 0,
        OrderListStatus.EXECUTING: 1,
        OrderListStatus.ALL_DONE: 2,
        OrderListStatus.REJECT: 2,
    }
    if rank[next_status] < rank[current]:
        raise OrderListError("ORDER_LIST_STATUS_OUT_OF_ORDER", "Liste status geriye gidemez.")


def _validate_terminal_legs(observation: OrderListObservation) -> None:
    if observation.list_status is not OrderListStatus.ALL_DONE:
        return
    terminal = {
        OrderListLegStatus.FILLED,
        OrderListLegStatus.CANCELED,
        OrderListLegStatus.REJECTED,
        OrderListLegStatus.EXPIRED,
        OrderListLegStatus.EXPIRED_IN_MATCH,
    }
    if any(status not in terminal for status in observation.leg_statuses):
        raise OrderListError("ORDER_LIST_TERMINAL_LEG_INCOMPLETE", "ALL_DONE iki terminal leg status gerektirir.")
    filled_count = observation.leg_statuses.count(OrderListLegStatus.FILLED)
    if filled_count > 1:
        raise OrderListError("ORDER_LIST_OCO_COORDINATION_INVALID", "OCO listesinde iki bacak birlikte FILLED olamaz.")
    if filled_count == 1:
        other = next(status for status in observation.leg_statuses if status is not OrderListLegStatus.FILLED)
        if other not in {
            OrderListLegStatus.CANCELED,
            OrderListLegStatus.EXPIRED,
            OrderListLegStatus.EXPIRED_IN_MATCH,
        }:
            raise OrderListError("ORDER_LIST_OCO_COORDINATION_INVALID", "OCO’da doldurulmayan bacak expire/cancel olmalıdır.")


def _fingerprint(observation: OrderListObservation) -> str:
    payload = {
        "event_id": observation.event_id,
        "order_list_id": observation.order_list_id,
        "list_client_order_id": observation.list_client_order_id,
        "list_status": observation.list_status.value,
        "list_order_status": observation.list_order_status.value,
        "leg_statuses": [status.value for status in observation.leg_statuses],
        "observed_at_ms": observation.observed_at_ms,
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)


def _identifier(value: object, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise OrderListError(code, "Kimlik bounded ASCII metin olmalıdır.")


def _symbol(value: object) -> None:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 32
        or value != value.strip()
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
    ):
        raise OrderListError("ORDER_LIST_SYMBOL_INVALID", "Symbol bounded metin olmalıdır.")
