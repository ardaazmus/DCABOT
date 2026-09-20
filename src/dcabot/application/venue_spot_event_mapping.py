"""Explicit, non-economic mapping candidate for venue and Spot events."""

from dataclasses import dataclass
from enum import StrEnum
import re

from dcabot.application.spot_order_lifecycle import SpotOrderEvent
from dcabot.application.venue_event_binding import (
    VenueEventEvidenceOutcome,
    VenueEventLookupEvidence,
)
from dcabot.application.reconciliation import ReconciliationError


class VenueSpotMappingStatus(StrEnum):
    """Lifecycle status of a mapping candidate before economic admission."""

    CANDIDATE = "CANDIDATE"


@dataclass(frozen=True, slots=True)
class VenueSpotEventMappingCandidate:
    """Two-namespace identity link with no fill or accounting authority."""

    venue_event_id: str
    venue_order_id: int
    spot_event_id: str
    spot_order_id: str
    execution_id: str | None
    status: VenueSpotMappingStatus = VenueSpotMappingStatus.CANDIDATE

    def __post_init__(self) -> None:
        for value, code in (
            (self.venue_event_id, "VENUE_SPOT_MAPPING_VENUE_EVENT_ID_INVALID"),
            (self.spot_event_id, "VENUE_SPOT_MAPPING_SPOT_EVENT_ID_INVALID"),
            (self.spot_order_id, "VENUE_SPOT_MAPPING_SPOT_ORDER_ID_INVALID"),
        ):
            if _IDENTIFIER.fullmatch(value) is None:
                raise ReconciliationError(code, "Mapping kimliği güvenli biçimde saklanamaz.")
        if type(self.venue_order_id) is not int or self.venue_order_id < 0:
            raise ReconciliationError(
                "VENUE_SPOT_MAPPING_ORDER_ID_INVALID", "Mapping venue order ID negatif olamaz."
            )
        if self.execution_id is not None and _IDENTIFIER.fullmatch(self.execution_id) is None:
            raise ReconciliationError(
                "VENUE_SPOT_MAPPING_EXECUTION_ID_INVALID",
                "Mapping execution ID güvenli biçimde saklanamaz.",
            )
        try:
            status = VenueSpotMappingStatus(self.status)
        except (TypeError, ValueError) as exc:
            raise ReconciliationError(
                "VENUE_SPOT_MAPPING_STATUS_INVALID", "Mapping candidate status geçersiz."
            ) from exc
        object.__setattr__(self, "status", status)


def build_spot_event_mapping_candidate(
    evidence: VenueEventLookupEvidence, spot_event: SpotOrderEvent
) -> VenueSpotEventMappingCandidate:
    """Create an identity candidate without admitting a lifecycle transition."""

    if not isinstance(evidence, VenueEventLookupEvidence):
        raise ReconciliationError(
            "VENUE_SPOT_MAPPING_EVIDENCE_INVALID", "Venue evidence güvenli tipte değil."
        )
    if evidence.outcome is not VenueEventEvidenceOutcome.MATCHED:
        raise ReconciliationError(
            "VENUE_SPOT_MAPPING_REQUIRES_MATCH",
            "Spot event mapping yalnız exact venue identity match ile oluşturulabilir.",
        )
    if not isinstance(spot_event, SpotOrderEvent):
        raise ReconciliationError(
            "VENUE_SPOT_MAPPING_SPOT_EVENT_INVALID", "Spot event güvenli tipte değil."
        )
    return VenueSpotEventMappingCandidate(
        venue_event_id=evidence.event_id,
        venue_order_id=evidence.event_venue_order_id,
        spot_event_id=spot_event.event_id,
        spot_order_id=spot_event.order_id,
        execution_id=spot_event.execution_id,
    )


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,128}\Z", re.ASCII)
