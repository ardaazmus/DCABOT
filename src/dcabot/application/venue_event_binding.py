"""Explicit, non-economic contract for matching venue events to lookups."""

from dataclasses import dataclass
from enum import StrEnum
import re

from dcabot.application.reconciliation import (
    LookupKind,
    OrderLookup,
    ReconciliationError,
    UserDataEvent,
)


class VenueEventEvidenceOutcome(StrEnum):
    """Classification of one venue event against one lookup result."""

    MATCHED = "MATCHED"
    UNRESOLVED = "UNRESOLVED"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class VenueEventLookupEvidence:
    """Redacted identity evidence; it carries no lifecycle or economic facts."""

    event_id: str
    event_venue_order_id: int
    lookup_kind: LookupKind
    lookup_venue_order_id: int | None
    outcome: VenueEventEvidenceOutcome

    def __post_init__(self) -> None:
        if _IDENTIFIER.fullmatch(self.event_id) is None:
            raise ReconciliationError(
                "VENUE_EVIDENCE_EVENT_ID_INVALID", "Venue evidence event ID geçersiz."
            )
        if type(self.event_venue_order_id) is not int or self.event_venue_order_id < 0:
            raise ReconciliationError(
                "VENUE_EVIDENCE_EVENT_ORDER_ID_INVALID",
                "Venue evidence event order ID negatif olamaz.",
            )
        try:
            lookup_kind = LookupKind(self.lookup_kind)
            outcome = VenueEventEvidenceOutcome(self.outcome)
        except (TypeError, ValueError) as exc:
            raise ReconciliationError(
                "VENUE_EVIDENCE_OUTCOME_INVALID", "Venue evidence sınıfı geçersiz."
            ) from exc
        object.__setattr__(self, "lookup_kind", lookup_kind)
        object.__setattr__(self, "outcome", outcome)
        if self.lookup_venue_order_id is not None and (
            type(self.lookup_venue_order_id) is not int or self.lookup_venue_order_id < 0
        ):
            raise ReconciliationError(
                "VENUE_EVIDENCE_LOOKUP_ORDER_ID_INVALID",
                "Venue evidence lookup order ID negatif olamaz.",
            )
        if outcome is VenueEventEvidenceOutcome.MATCHED and (
            lookup_kind is not LookupKind.FOUND
            or self.lookup_venue_order_id != self.event_venue_order_id
        ):
            raise ReconciliationError(
                "VENUE_EVIDENCE_MATCH_INVALID", "MATCHED yalnız birebir FOUND kimliği taşıyabilir."
            )
        if outcome is VenueEventEvidenceOutcome.CONFLICT and lookup_kind is not LookupKind.FOUND:
            raise ReconciliationError(
                "VENUE_EVIDENCE_CONFLICT_INVALID", "CONFLICT yalnız FOUND kimlik uyuşmazlığında üretilebilir."
            )
        if outcome is VenueEventEvidenceOutcome.UNRESOLVED and lookup_kind is LookupKind.FOUND:
            raise ReconciliationError(
                "VENUE_EVIDENCE_UNRESOLVED_INVALID", "FOUND sonucu UNRESOLVED olarak sınıflandırılamaz."
            )


def evaluate_venue_event_lookup(
    event: UserDataEvent, lookup: OrderLookup
) -> VenueEventLookupEvidence:
    """Classify an exact venue identity match without promoting it to a fill."""

    if not isinstance(event, UserDataEvent):
        raise ReconciliationError("VENUE_EVENT_INVALID", "Venue event güvenli tipte değil.")
    if not isinstance(lookup, OrderLookup):
        raise ReconciliationError("LOOKUP_RESULT_INVALID", "REST lookup sonucu güvenli tipte değil.")
    if lookup.kind is LookupKind.FOUND:
        outcome = (
            VenueEventEvidenceOutcome.MATCHED
            if lookup.venue_order_id == event.venue_order_id
            else VenueEventEvidenceOutcome.CONFLICT
        )
    else:
        outcome = VenueEventEvidenceOutcome.UNRESOLVED
    return VenueEventLookupEvidence(
        event.event_id,
        event.venue_order_id,
        lookup.kind,
        lookup.venue_order_id,
        outcome,
    )


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,128}\Z", re.ASCII)
