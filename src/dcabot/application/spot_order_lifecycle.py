"""Offline Spot order lifecycle facts before venue/economic posting."""

from dataclasses import dataclass, replace
from enum import StrEnum
import hashlib
import json
import re

from dcabot.application.instrument_filters import (
    InstrumentFilterError,
    InstrumentFilterProfile,
    validate_order_candidate,
)
from dcabot.domain.numbers import align, exact_text, number, positive


class SpotOrderType(StrEnum):
    """The first offline Spot order-type subset."""

    LIMIT = "LIMIT"
    MARKET = "MARKET"


class SpotSide(StrEnum):
    """Spot order side preserved as a venue fact."""

    BUY = "BUY"
    SELL = "SELL"


class SpotOrderStatus(StrEnum):
    """Venue order statuses admitted by the first lifecycle slice."""

    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    EXPIRED_IN_MATCH = "EXPIRED_IN_MATCH"


class EventOutcome(StrEnum):
    """Result of admitting one immutable venue lifecycle observation."""

    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    CONFLICT = "CONFLICT"
    QUARANTINED = "QUARANTINED"


class SpotOrderLifecycleError(ValueError):
    """Raised when an offline Spot order or event violates its contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class SpotOrder:
    """One order projection; it contains no balance, fee, PnL, or fill value."""

    order_id: str
    client_order_id: str
    symbol: str
    side: SpotSide
    order_type: SpotOrderType
    requested_quantity: str | None
    quote_order_quantity: str | None
    price: str | None
    status: SpotOrderStatus = SpotOrderStatus.NEW
    filled_quantity: str = "0"
    leaves_quantity: str | None = "0"
    last_event_time_ms: int | None = None

    def __post_init__(self) -> None:
        _validate_ascii_identifier(self.order_id, "ORDER_ID_INVALID")
        _validate_ascii_identifier(self.client_order_id, "CLIENT_ORDER_ID_INVALID")
        _validate_symbol(self.symbol)
        try:
            side = SpotSide(self.side)
            order_type = SpotOrderType(self.order_type)
            status = SpotOrderStatus(self.status)
        except (TypeError, ValueError) as exc:
            raise SpotOrderLifecycleError("ORDER_ENUM_INVALID", "Order enum değeri geçersiz.") from exc
        object.__setattr__(self, "side", side)
        object.__setattr__(self, "order_type", order_type)
        object.__setattr__(self, "status", status)
        if (self.requested_quantity is None) == (self.quote_order_quantity is None):
            raise SpotOrderLifecycleError(
                "ORDER_QUANTITY_MODEL_INVALID",
                "Order quantity veya quoteOrderQty alanlarından yalnız biri bulunmalıdır.",
            )
        if order_type is SpotOrderType.LIMIT and self.price is None:
            raise SpotOrderLifecycleError("LIMIT_PRICE_REQUIRED", "LIMIT order price taşımalıdır.")
        if order_type is SpotOrderType.MARKET and self.price is not None:
            raise SpotOrderLifecycleError("MARKET_PRICE_UNEXPECTED", "MARKET order price taşımaz.")
        for value, code in (
            (self.requested_quantity, "ORDER_QUANTITY_INVALID"),
            (self.quote_order_quantity, "ORDER_QUOTE_QUANTITY_INVALID"),
            (self.price, "ORDER_PRICE_INVALID"),
        ):
            if value is not None:
                try:
                    positive(value)
                except ValueError as exc:
                    raise SpotOrderLifecycleError(code, "Pozitif decimal string bekleniyordu.") from exc
        try:
            filled = number(self.filled_quantity)
        except ValueError as exc:
            raise SpotOrderLifecycleError(
                "ORDER_FILLED_QUANTITY_INVALID", "Filled quantity decimal string olmalıdır."
            ) from exc
        if filled < 0:
            raise SpotOrderLifecycleError(
                "ORDER_FILLED_QUANTITY_INVALID", "Filled quantity negatif olamaz."
            )
        if self.requested_quantity is not None and filled > number(self.requested_quantity):
            raise SpotOrderLifecycleError("ORDER_OVERFILLED", "Filled quantity istenen quantity’yi aşamaz.")
        if self.leaves_quantity is not None:
            try:
                leaves = number(self.leaves_quantity)
            except ValueError as exc:
                raise SpotOrderLifecycleError(
                    "ORDER_LEAVES_QUANTITY_INVALID", "Leaves quantity decimal string olmalıdır."
                ) from exc
            if leaves < 0:
                raise SpotOrderLifecycleError(
                    "ORDER_LEAVES_QUANTITY_INVALID", "Leaves quantity negatif olamaz."
                )
        if self.last_event_time_ms is not None and (
            type(self.last_event_time_ms) is not int or self.last_event_time_ms < 0
        ):
            raise SpotOrderLifecycleError("ORDER_EVENT_TIME_INVALID", "Event zamanı negatif olmayan integer olmalıdır.")


@dataclass(frozen=True, slots=True)
class SpotOrderEvent:
    """A redacted execution/status observation from a fake or future venue."""

    order_id: str
    event_id: str
    execution_id: str | None
    event_time_ms: int
    status: SpotOrderStatus
    last_filled_qty: str
    cumulative_filled_qty: str
    last_price: str | None

    def __post_init__(self) -> None:
        _validate_ascii_identifier(self.order_id, "EVENT_ORDER_ID_INVALID")
        _validate_ascii_identifier(self.event_id, "EVENT_ID_INVALID")
        if self.execution_id is not None:
            _validate_ascii_identifier(self.execution_id, "EXECUTION_ID_INVALID")
        if type(self.event_time_ms) is not int or self.event_time_ms < 0:
            raise SpotOrderLifecycleError("EVENT_TIME_INVALID", "Event zamanı negatif olmayan integer olmalıdır.")
        try:
            status = SpotOrderStatus(self.status)
        except (TypeError, ValueError) as exc:
            raise SpotOrderLifecycleError("EVENT_STATUS_INVALID", "Event status değeri geçersiz.") from exc
        object.__setattr__(self, "status", status)
        for value, code in (
            (self.last_filled_qty, "EVENT_LAST_FILL_INVALID"),
            (self.cumulative_filled_qty, "EVENT_CUMULATIVE_FILL_INVALID"),
        ):
            try:
                parsed = number(value)
            except ValueError as exc:
                raise SpotOrderLifecycleError(code, "Event quantity decimal string olmalıdır.") from exc
            if parsed < 0:
                raise SpotOrderLifecycleError(code, "Event quantity negatif olamaz.")
        if self.last_price is not None:
            try:
                positive(self.last_price)
            except ValueError as exc:
                raise SpotOrderLifecycleError(
                    "EVENT_LAST_PRICE_INVALID", "Event fiyatı pozitif decimal string olmalıdır."
                ) from exc


@dataclass(frozen=True, slots=True)
class LifecycleApplyResult:
    """State plus admission outcome; conflicts never rewrite order facts."""

    lifecycle: "SpotOrderLifecycle"
    outcome: EventOutcome


@dataclass(frozen=True, slots=True)
class SpotOrderLifecycle:
    """Immutable offline lifecycle with exact quantity conservation."""

    order: SpotOrder
    seen_events: tuple[tuple[str, str], ...] = ()
    seen_executions: tuple[tuple[str, str], ...] = ()
    reconciliation_required: bool = False

    def event(
        self,
        *,
        event_id: str,
        execution_id: str | None,
        event_time_ms: int,
        status: str,
        last_filled_qty: str,
        cumulative_filled_qty: str,
        last_price: str | None,
    ) -> SpotOrderEvent:
        """Construct a validated event for this lifecycle boundary."""

        return SpotOrderEvent(
            order_id=self.order.order_id,
            event_id=event_id,
            execution_id=execution_id,
            event_time_ms=event_time_ms,
            status=status,
            last_filled_qty=last_filled_qty,
            cumulative_filled_qty=cumulative_filled_qty,
            last_price=last_price,
        )

    def apply(self, event: SpotOrderEvent) -> LifecycleApplyResult:
        """Admit a venue event without posting economics or silently repairing gaps."""

        if not isinstance(event, SpotOrderEvent):
            raise SpotOrderLifecycleError("EVENT_INVALID", "Spot order event güvenli tipte değil.")
        if event.order_id != self.order.order_id:
            return LifecycleApplyResult(
                replace(self, reconciliation_required=True), EventOutcome.CONFLICT
            )
        fingerprint = _fingerprint(event)
        prior_event = dict(self.seen_events).get(event.event_id)
        if prior_event is not None:
            if prior_event == fingerprint:
                return LifecycleApplyResult(self, EventOutcome.DUPLICATE)
            return LifecycleApplyResult(
                replace(self, reconciliation_required=True), EventOutcome.CONFLICT
            )
        if event.execution_id is not None:
            prior_execution = dict(self.seen_executions).get(event.execution_id)
            if prior_execution is not None:
                if prior_execution == fingerprint:
                    return LifecycleApplyResult(self, EventOutcome.DUPLICATE)
                return LifecycleApplyResult(
                    replace(self, reconciliation_required=True), EventOutcome.CONFLICT
                )
        if self.reconciliation_required:
            return LifecycleApplyResult(self, EventOutcome.QUARANTINED)
        if (
            self.order.last_event_time_ms is not None
            and event.event_time_ms < self.order.last_event_time_ms
        ):
            return LifecycleApplyResult(
                replace(self, reconciliation_required=True), EventOutcome.OUT_OF_ORDER
            )
        try:
            next_order = _apply_to_order(self.order, event)
        except SpotOrderLifecycleError:
            return LifecycleApplyResult(
                replace(self, reconciliation_required=True), EventOutcome.CONFLICT
            )
        events = (*self.seen_events, (event.event_id, fingerprint))
        executions = self.seen_executions
        if event.execution_id is not None:
            executions = (*executions, (event.execution_id, fingerprint))
        return LifecycleApplyResult(
            replace(self, order=next_order, seen_events=events, seen_executions=executions),
            EventOutcome.ACCEPTED,
        )


def create_limit_order(
    profile: InstrumentFilterProfile,
    *,
    order_id: str,
    client_order_id: str,
    symbol: str,
    side: SpotSide,
    quantity: str,
    price: str,
) -> SpotOrder:
    """Create a LIMIT order after exact profile validation."""

    try:
        candidate = validate_order_candidate(profile, quantity=quantity, price=price)
    except InstrumentFilterError as exc:
        raise SpotOrderLifecycleError(exc.code, str(exc).split(": ", 1)[-1]) from exc
    _validate_side(side)
    return SpotOrder(
        order_id=order_id,
        client_order_id=client_order_id,
        symbol=symbol,
        side=side,
        order_type=SpotOrderType.LIMIT,
        requested_quantity=candidate.quantity,
        quote_order_quantity=None,
        price=candidate.price,
        leaves_quantity=candidate.quantity,
    )


def create_market_order(
    profile: InstrumentFilterProfile,
    *,
    order_id: str,
    client_order_id: str,
    symbol: str,
    side: SpotSide,
    quantity: str | None = None,
    quote_order_quantity: str | None = None,
) -> SpotOrder:
    """Create a MARKET order without deriving base quantity from quote quantity."""

    if (quantity is None) == (quote_order_quantity is None):
        raise SpotOrderLifecycleError(
            "MARKET_QUANTITY_MODEL_INVALID",
            "MARKET order quantity veya quoteOrderQty alanlarından biri gerekir.",
        )
    _validate_side(side)
    if quantity is not None:
        try:
            parsed = positive(quantity)
            step = positive(profile.qty_step)
            minimum = positive(profile.min_qty)
        except (AttributeError, ValueError) as exc:
            raise SpotOrderLifecycleError(
                "ORDER_QUANTITY_INVALID", "MARKET quantity decimal string olmalıdır."
            ) from exc
        if align(parsed, step, up=False) != parsed:
            raise SpotOrderLifecycleError("ORDER_QUANTITY_OFF_GRID", "MARKET quantity step grid’inde değil.")
        if parsed < minimum:
            raise SpotOrderLifecycleError("ORDER_QUANTITY_BELOW_MINIMUM", "MARKET quantity minimumunun altında.")
        requested_quantity = exact_text(parsed)
        quote_quantity = None
    else:
        try:
            parsed_quote = positive(quote_order_quantity)
            minimum = positive(profile.min_notional)
        except (AttributeError, ValueError) as exc:
            raise SpotOrderLifecycleError(
                "ORDER_QUOTE_QUANTITY_INVALID", "MARKET quoteOrderQty decimal string olmalıdır."
            ) from exc
        if parsed_quote < minimum:
            raise SpotOrderLifecycleError(
                "ORDER_NOTIONAL_BELOW_MINIMUM", "MARKET quoteOrderQty minimum notional’ın altında."
            )
        requested_quantity = None
        quote_quantity = exact_text(parsed_quote)
    return SpotOrder(
        order_id=order_id,
        client_order_id=client_order_id,
        symbol=symbol,
        side=side,
        order_type=SpotOrderType.MARKET,
        requested_quantity=requested_quantity,
        quote_order_quantity=quote_quantity,
        price=None,
        leaves_quantity=exact_text(positive(requested_quantity)) if requested_quantity else None,
    )


def new_lifecycle(order: SpotOrder) -> SpotOrderLifecycle:
    """Create an empty immutable lifecycle for one order."""

    if not isinstance(order, SpotOrder):
        raise SpotOrderLifecycleError("ORDER_INVALID", "Spot order güvenli tipte değil.")
    return SpotOrderLifecycle(order)


def report(lifecycle: SpotOrderLifecycle) -> dict[str, object]:
    """Return a display-safe projection without economic calculations."""

    if not isinstance(lifecycle, SpotOrderLifecycle):
        raise SpotOrderLifecycleError("LIFECYCLE_INVALID", "Lifecycle güvenli tipte değil.")
    order = lifecycle.order
    return {
        "order_id": order.order_id,
        "client_order_id": order.client_order_id,
        "symbol": order.symbol,
        "side": order.side.value,
        "order_type": order.order_type.value,
        "status": order.status.value,
        "requested_quantity": order.requested_quantity,
        "filled_quantity": order.filled_quantity,
        "leaves_quantity": order.leaves_quantity,
        "quote_order_quantity": order.quote_order_quantity,
        "reconciliation_required": lifecycle.reconciliation_required,
    }


def _apply_to_order(order: SpotOrder, event: SpotOrderEvent) -> SpotOrder:
    if order.status in {
        SpotOrderStatus.FILLED,
        SpotOrderStatus.CANCELED,
        SpotOrderStatus.REJECTED,
        SpotOrderStatus.EXPIRED,
        SpotOrderStatus.EXPIRED_IN_MATCH,
    }:
        raise SpotOrderLifecycleError("TERMINAL_ORDER_EVENT", "Terminal order yeni event alamaz.")
    current_filled = number(order.filled_quantity)
    last_filled = number(event.last_filled_qty)
    cumulative = number(event.cumulative_filled_qty)
    if cumulative != current_filled + last_filled:
        raise SpotOrderLifecycleError(
            "CUMULATIVE_FILL_MISMATCH", "Cumulative fill önceki miktar ile conservation sağlamıyor."
        )
    if order.requested_quantity is not None and cumulative > number(order.requested_quantity):
        raise SpotOrderLifecycleError("ORDER_OVERFILLED", "Cumulative fill istenen quantity’yi aşamaz.")
    if last_filled and event.last_price is None:
        raise SpotOrderLifecycleError("EVENT_LAST_PRICE_REQUIRED", "Fill event fiyat taşımalıdır.")
    if not last_filled and event.last_price is not None:
        raise SpotOrderLifecycleError("EVENT_LAST_PRICE_UNEXPECTED", "Boş fill event fiyat taşıyamaz.")
    if event.status is SpotOrderStatus.NEW and cumulative != 0:
        raise SpotOrderLifecycleError("NEW_WITH_FILL", "NEW status filled quantity taşıyamaz.")
    if event.status is SpotOrderStatus.REJECTED and cumulative != 0:
        raise SpotOrderLifecycleError("REJECTED_WITH_FILL", "REJECTED status fill taşıyamaz.")
    if event.status is SpotOrderStatus.PARTIALLY_FILLED:
        if cumulative == 0 or (
            order.requested_quantity is not None and cumulative >= number(order.requested_quantity)
        ):
            raise SpotOrderLifecycleError("PARTIAL_STATUS_INVALID", "PARTIALLY_FILLED ara miktar taşımalıdır.")
    if event.status is SpotOrderStatus.FILLED and cumulative == 0:
        raise SpotOrderLifecycleError("FILLED_WITHOUT_EXECUTION", "FILLED status execution taşımalıdır.")
    if event.status is SpotOrderStatus.FILLED and (
        order.requested_quantity is not None and cumulative != number(order.requested_quantity)
    ):
        raise SpotOrderLifecycleError("FILLED_COVERAGE_INVALID", "FILLED status istenen miktarı kapatmalıdır.")
    if event.status is SpotOrderStatus.FILLED and order.requested_quantity is None and cumulative == 0:
        raise SpotOrderLifecycleError("FILLED_WITHOUT_EXECUTION", "FILLED status execution taşımalıdır.")
    leaves = (
        exact_text(number(order.requested_quantity) - cumulative)
        if order.requested_quantity is not None
        else None
    )
    return replace(
        order,
        status=event.status,
        filled_quantity=exact_text(cumulative),
        leaves_quantity=leaves,
        last_event_time_ms=event.event_time_ms,
    )


def _fingerprint(event: SpotOrderEvent) -> str:
    payload = {
        "order_id": event.order_id,
        "event_id": event.event_id,
        "execution_id": event.execution_id,
        "event_time_ms": event.event_time_ms,
        "status": event.status.value,
        "last_filled_qty": event.last_filled_qty,
        "cumulative_filled_qty": event.cumulative_filled_qty,
        "last_price": event.last_price,
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)


def _validate_ascii_identifier(value: object, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise SpotOrderLifecycleError(code, "Kimlik geçersiz.")


def _validate_symbol(value: object) -> None:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 32
        or value != value.strip()
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
    ):
        raise SpotOrderLifecycleError("SYMBOL_INVALID", "Symbol bounded UTF-8 metin olmalıdır.")


def _validate_side(value: object) -> None:
    try:
        SpotSide(value)
    except (TypeError, ValueError) as exc:
        raise SpotOrderLifecycleError("ORDER_SIDE_INVALID", "Order side geçersiz.") from exc
