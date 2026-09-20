"""Offline evidence binding for OCO venue events and cancel-replace identities.

This module records venue identity only.  It does not create orders, infer
fills, or promote a partial cancel-replace response into economic state.
"""

from dataclasses import dataclass
from enum import StrEnum

from dcabot.application.order_list_contract import (
    OcoOrderListIdentity,
    OrderListError,
    OrderListLegStatus,
    OrderListStatus,
)


class OrderListEventOutcome(StrEnum):
    """Evidence classification for one venue event against one OCO identity."""

    MATCHED = "MATCHED"
    CONFLICT = "CONFLICT"


class CancelReplaceDisposition(StrEnum):
    """Fail-closed classification of the two result fields."""

    CONFIRMED = "CONFIRMED"
    CANCEL_CONFIRMED_NEW_REJECTED = "CANCEL_CONFIRMED_NEW_REJECTED"
    CANCEL_REJECTED_NEW_CONFIRMED = "CANCEL_REJECTED_NEW_CONFIRMED"
    BOTH_REJECTED = "BOTH_REJECTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class OrderListVenueEvent:
    """Redacted order-list event identity; it carries no price or fill data."""

    event_id: str
    event_time_ms: int
    order_list_id: int
    list_client_order_id: str
    order_id: int
    client_order_id: str
    list_status: OrderListStatus
    list_order_status: OrderListStatus
    leg_status: OrderListLegStatus

    def __post_init__(self) -> None:
        _identifier(self.event_id, "ORDER_LIST_EVENT_ID_INVALID")
        _non_negative_int(self.event_time_ms, "ORDER_LIST_EVENT_TIME_INVALID")
        _positive_int(self.order_list_id, "ORDER_LIST_ID_INVALID")
        _identifier(self.list_client_order_id, "ORDER_LIST_CLIENT_ID_INVALID")
        _positive_int(self.order_id, "ORDER_LIST_ORDER_ID_INVALID")
        _identifier(self.client_order_id, "ORDER_LIST_CLIENT_ORDER_ID_INVALID")
        try:
            object.__setattr__(self, "list_status", OrderListStatus(self.list_status))
            object.__setattr__(self, "list_order_status", OrderListStatus(self.list_order_status))
            object.__setattr__(self, "leg_status", OrderListLegStatus(self.leg_status))
        except (TypeError, ValueError) as exc:
            raise OrderListError(
                "ORDER_LIST_EVENT_STATUS_INVALID", "Venue order-list status değeri geçersiz."
            ) from exc


@dataclass(frozen=True, slots=True)
class OrderListEventEvidence:
    """Redacted result of comparing one event with the immutable OCO identity."""

    event_id: str
    order_list_id: int
    order_id: int
    outcome: OrderListEventOutcome
    matched_leg_id: str | None

    def __post_init__(self) -> None:
        _identifier(self.event_id, "ORDER_LIST_EVENT_ID_INVALID")
        _positive_int(self.order_list_id, "ORDER_LIST_ID_INVALID")
        _positive_int(self.order_id, "ORDER_LIST_ORDER_ID_INVALID")
        try:
            object.__setattr__(self, "outcome", OrderListEventOutcome(self.outcome))
        except (TypeError, ValueError) as exc:
            raise OrderListError(
                "ORDER_LIST_EVENT_OUTCOME_INVALID", "Venue event sonucu geçersiz."
            ) from exc
        if self.matched_leg_id is not None:
            _identifier(self.matched_leg_id, "ORDER_LIST_LEG_ID_INVALID")
        if self.outcome is OrderListEventOutcome.MATCHED and self.matched_leg_id is None:
            raise OrderListError(
                "ORDER_LIST_EVENT_MATCH_INVALID", "MATCHED kanıtı leg kimliği taşımalıdır."
            )
        if self.outcome is OrderListEventOutcome.CONFLICT and self.matched_leg_id is not None:
            raise OrderListError(
                "ORDER_LIST_EVENT_CONFLICT_INVALID", "CONFLICT kanıtı eşleşmiş leg taşıyamaz."
            )


@dataclass(frozen=True, slots=True)
class CancelReplaceIdentity:
    """Identity-only cancel-replace result; it never mutates the prior identity."""

    operation_id: str
    prior_order_id: int
    prior_client_order_id: str
    cancel_result: str | None
    new_order_result: str | None
    replacement_order_id: int | None
    replacement_client_order_id: str | None
    observed_at_ms: int

    def __post_init__(self) -> None:
        _identifier(self.operation_id, "CANCEL_REPLACE_OPERATION_ID_INVALID")
        _positive_int(self.prior_order_id, "CANCEL_REPLACE_PRIOR_ORDER_ID_INVALID")
        _identifier(self.prior_client_order_id, "CANCEL_REPLACE_PRIOR_CLIENT_ID_INVALID")
        _result_value(self.cancel_result, "CANCEL_REPLACE_CANCEL_RESULT_INVALID")
        _result_value(self.new_order_result, "CANCEL_REPLACE_NEW_RESULT_INVALID")
        if self.replacement_order_id is not None:
            _positive_int(self.replacement_order_id, "CANCEL_REPLACE_NEW_ORDER_ID_INVALID")
        if self.replacement_client_order_id is not None:
            _identifier(
                self.replacement_client_order_id,
                "CANCEL_REPLACE_NEW_CLIENT_ID_INVALID",
            )
        if (self.replacement_order_id is None) != (self.replacement_client_order_id is None):
            raise OrderListError(
                "CANCEL_REPLACE_NEW_IDENTITY_INCOMPLETE",
                "Replacement orderId ve clientOrderId birlikte verilmelidir.",
            )
        _non_negative_int(self.observed_at_ms, "CANCEL_REPLACE_TIME_INVALID")

    @property
    def disposition(self) -> CancelReplaceDisposition:
        """Classify only complete, internally consistent result combinations."""

        cancel = self.cancel_result
        new_order = self.new_order_result
        has_replacement = self.replacement_order_id is not None
        if cancel == "SUCCESS" and new_order == "SUCCESS" and has_replacement:
            return CancelReplaceDisposition.CONFIRMED
        if cancel == "SUCCESS" and new_order == "FAILURE" and not has_replacement:
            return CancelReplaceDisposition.CANCEL_CONFIRMED_NEW_REJECTED
        if cancel == "FAILURE" and new_order == "SUCCESS" and has_replacement:
            return CancelReplaceDisposition.CANCEL_REJECTED_NEW_CONFIRMED
        if cancel == "FAILURE" and new_order == "FAILURE" and not has_replacement:
            return CancelReplaceDisposition.BOTH_REJECTED
        return CancelReplaceDisposition.UNKNOWN


def reconcile_order_list_event(
    identity: OcoOrderListIdentity, event: OrderListVenueEvent
) -> OrderListEventEvidence:
    """Match exact list and leg identities without promoting status to a fill."""

    if not isinstance(identity, OcoOrderListIdentity):
        raise OrderListError("ORDER_LIST_IDENTITY_INVALID", "OCO identity güvenli tipte değil.")
    if not isinstance(event, OrderListVenueEvent):
        raise OrderListError("ORDER_LIST_EVENT_INVALID", "Venue event güvenli tipte değil.")
    if (event.order_list_id, event.list_client_order_id) != (
        identity.order_list_id,
        identity.list_client_order_id,
    ):
        return OrderListEventEvidence(
            event.event_id,
            event.order_list_id,
            event.order_id,
            OrderListEventOutcome.CONFLICT,
            None,
        )
    matching_legs = tuple(
        leg
        for leg in identity.legs
        if (leg.order_id, leg.client_order_id) == (event.order_id, event.client_order_id)
    )
    if len(matching_legs) != 1:
        return OrderListEventEvidence(
            event.event_id,
            event.order_list_id,
            event.order_id,
            OrderListEventOutcome.CONFLICT,
            None,
        )
    return OrderListEventEvidence(
        event.event_id,
        event.order_list_id,
        event.order_id,
        OrderListEventOutcome.MATCHED,
        matching_legs[0].leg_id,
    )


def _result_value(value: object, code: str) -> None:
    if value is not None and (type(value) is not str or value not in {"SUCCESS", "FAILURE"}):
        raise OrderListError(code, "Sonuç SUCCESS, FAILURE veya bilinmeyen None olmalıdır.")


def _identifier(value: object, code: str) -> None:
    if (
        type(value) is not str
        or not 1 <= len(value) <= 128
        or any(char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_:-" for char in value)
    ):
        raise OrderListError(code, "Kimlik bounded ASCII metin olmalıdır.")


def _positive_int(value: object, code: str) -> None:
    if type(value) is not int or value <= 0:
        raise OrderListError(code, "Pozitif integer bekleniyor.")


def _non_negative_int(value: object, code: str) -> None:
    if type(value) is not int or value < 0:
        raise OrderListError(code, "Negatif olmayan integer bekleniyor.")
