"""Read-only boundary between the Futures DCA journal and CORE01."""

from dataclasses import dataclass
from pathlib import Path

from .futures_dca_journal_schema import (
    FuturesDcaJournalSchemaError,
    load_economic_postings,
    load_journal_events,
)


@dataclass(frozen=True, slots=True)
class FuturesDcaCoreBindingPreflight:
    """One durable posting decision without CORE01 mutation authority."""

    event_id: str
    posting_id: str
    status: str
    missing_authority: tuple[str, ...]
    reason_code: str


def preflight_futures_dca_core_binding(
    path: Path,
) -> tuple[FuturesDcaCoreBindingPreflight, ...]:
    """Replay postings and refuse to invent the missing CORE01 order contract."""

    events = {event.event_id: event for event in load_journal_events(path)}
    decisions = []
    for posting in load_economic_postings(path):
        event = events.get(posting.source_event_id)
        if event is None:
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_CORE_BINDING_EVENT_MISSING", "Posting source event replay içinde bulunamadı."
            )
        if event.event_state != "ACCEPTED":
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_CORE_BINDING_EVENT_NOT_ACCEPTED", "CORE01 binding accepted event olmadan açılamaz."
            )
        decisions.append(
            FuturesDcaCoreBindingPreflight(
                event.event_id,
                posting.posting_id,
                "BLOCKED",
                ("side", "core_order_intent", "role", "limit_price"),
                "FUTURES_DCA_CORE_INTENT_MAPPING_MISSING",
            )
        )
    return tuple(decisions)
