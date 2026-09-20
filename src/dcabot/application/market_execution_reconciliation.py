"""Offline identity binding for exact MARKET fills and redacted venue evidence."""

from dataclasses import dataclass

from dcabot.application.market_base_quantity import (
    MarketBaseExecution,
    MarketFill,
)
from dcabot.application.reconciliation import (
    ConnectionState,
    EventDecision,
    LookupKind,
    OrderLookup,
    ReconciliationError,
    UserDataEvent,
)
from dcabot.application.venue_event_binding import (
    VenueEventEvidenceOutcome,
    evaluate_venue_event_lookup,
)
from dcabot.application.venue_spot_event_mapping import VenueSpotEventMappingCandidate


@dataclass(frozen=True, slots=True)
class MarketExecutionReconciliationBinding:
    """Immutable identity link; it has no core-event or persistence authority."""

    venue_event_id: str
    venue_order_id: int
    spot_event_id: str
    spot_order_id: str
    market_order_id: str
    execution_id: str
    fill: MarketFill


def bind_market_fill_to_reconciliation(
    candidate: VenueSpotEventMappingCandidate,
    observation: tuple[UserDataEvent, EventDecision, ConnectionState],
    lookup: OrderLookup,
    execution: MarketBaseExecution,
    fill: MarketFill,
) -> MarketExecutionReconciliationBinding:
    """Bind a MARKET fill only after exact accepted-stream/REST identity proof."""

    if not isinstance(candidate, VenueSpotEventMappingCandidate):
        raise ReconciliationError(
            "MARKET_RECONCILIATION_CANDIDATE_INVALID", "MARKET mapping candidate geçersiz."
        )
    if not isinstance(execution, MarketBaseExecution) or not isinstance(fill, MarketFill):
        raise ReconciliationError(
            "MARKET_RECONCILIATION_EXECUTION_INVALID", "MARKET execution/fill tipi geçersiz."
        )
    if fill not in execution.fills or candidate.execution_id != fill.execution_id:
        raise ReconciliationError(
            "MARKET_RECONCILIATION_EXECUTION_INVALID",
            "MARKET execution kimliği fill ve mapping ile eşleşmiyor.",
        )
    if candidate.spot_order_id != execution.order_id:
        raise ReconciliationError(
            "MARKET_RECONCILIATION_ORDER_INVALID", "MARKET order kimliği mapping ile eşleşmiyor."
        )
    if not isinstance(lookup, OrderLookup) or lookup.kind is not LookupKind.FOUND:
        raise ReconciliationError(
            "MARKET_RECONCILIATION_LOOKUP_INVALID", "MARKET binding exact FOUND lookup gerektirir."
        )
    if lookup.venue_order_id != candidate.venue_order_id:
        raise ReconciliationError(
            "MARKET_RECONCILIATION_LOOKUP_INVALID", "MARKET lookup order kimliği eşleşmiyor."
        )
    if not isinstance(observation, tuple) or len(observation) != 3:
        raise ReconciliationError(
            "MARKET_RECONCILIATION_OBSERVATION_INVALID", "MARKET observation üçlü tuple olmalıdır."
        )
    event, decision, state = observation
    if not isinstance(event, UserDataEvent):
        raise ReconciliationError(
            "MARKET_RECONCILIATION_OBSERVATION_INVALID", "MARKET venue event geçersiz."
        )
    try:
        decision = EventDecision(decision)
        state = ConnectionState(state)
    except (TypeError, ValueError) as exc:
        raise ReconciliationError(
            "MARKET_RECONCILIATION_OBSERVATION_INVALID", "MARKET observation state geçersiz."
        ) from exc
    if decision not in {EventDecision.ACCEPTED, EventDecision.DUPLICATE} or state not in {
        ConnectionState.CONNECTED_READ_ONLY,
        ConnectionState.SYNCED,
    }:
        raise ReconciliationError(
            "MARKET_RECONCILIATION_DECISION_INVALID",
            "MARKET binding yalnız kabul edilmiş ve quarantine edilmemiş evidence gerektirir.",
        )
    if event.event_id != candidate.venue_event_id or event.venue_order_id != candidate.venue_order_id:
        raise ReconciliationError(
            "MARKET_RECONCILIATION_EVENT_INVALID", "MARKET venue event kimliği mapping ile eşleşmiyor."
        )
    if evaluate_venue_event_lookup(event, lookup).outcome is not VenueEventEvidenceOutcome.MATCHED:
        raise ReconciliationError(
            "MARKET_RECONCILIATION_LOOKUP_INVALID", "MARKET evidence birebir FOUND eşleşmesi değil."
        )
    return MarketExecutionReconciliationBinding(
        venue_event_id=candidate.venue_event_id,
        venue_order_id=candidate.venue_order_id,
        spot_event_id=candidate.spot_event_id,
        spot_order_id=candidate.spot_order_id,
        market_order_id=execution.order_id,
        execution_id=fill.execution_id,
        fill=fill,
    )
