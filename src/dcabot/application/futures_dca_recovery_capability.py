"""Read-only profile-bound recovery capability for the Futures DCA journal."""

from dataclasses import dataclass
from pathlib import Path

from dcabot.persistence.futures_dca_core_binding import (
    preflight_futures_dca_core_binding,
)
from dcabot.persistence.futures_dca_core_replay_store import (
    load_futures_dca_core_replay_receipts,
    preflight_futures_dca_core_replay_store,
)
from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaJournalSchemaError,
    load_economic_postings,
    load_journal_events,
    load_profile_revisions,
)
from dcabot.persistence.futures_dca_release_store import (
    load_futures_dca_release_transitions,
)


@dataclass(frozen=True, slots=True)
class FuturesDcaProfileRecoveryCapability:
    """Read-only recovery result with an explicit CORE01 boundary."""

    profile_revision_id: str
    status: str
    core_admission_status: str
    missing_authority: tuple[str, ...]
    reason_code: str
    event_count: int
    posting_count: int
    receipt_count: int

    def __post_init__(self) -> None:
        if self.status not in {"READY", "BLOCKED"}:
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_PROFILE_RECOVERY_STATUS_INVALID",
                "Profile recovery status yalnız READY veya BLOCKED olabilir.",
            )
        if self.core_admission_status != "BLOCKED":
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_PROFILE_RECOVERY_CORE_STATUS_INVALID",
                "CORE01 admission bu capability içinde fail-closed BLOCKED olmalıdır.",
            )
        if not isinstance(self.missing_authority, tuple) or any(
            not isinstance(item, str) for item in self.missing_authority
        ):
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_PROFILE_RECOVERY_AUTHORITY_INVALID",
                "Eksik authority tuple olmalıdır.",
            )
        if any(type(value) is not int or value < 0 for value in (
            self.event_count,
            self.posting_count,
            self.receipt_count,
        )):
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_PROFILE_RECOVERY_COUNT_INVALID",
                "Recovery sayımları negatif olamaz.",
            )


def assess_futures_dca_profile_recovery(
    path: Path,
    profile_revision_id: str,
) -> FuturesDcaProfileRecoveryCapability:
    """Assess one profile's durable recovery without writing or admitting CORE01."""

    if not isinstance(profile_revision_id, str) or not profile_revision_id:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_PROFILE_RECOVERY_PROFILE_INVALID",
            "Profile revision kimliği güvenli bir string olmalıdır.",
        )
    try:
        profiles = load_profile_revisions(path)
        if not any(profile.revision_id == profile_revision_id for profile in profiles):
            return _blocked(
                profile_revision_id,
                "FUTURES_DCA_PROFILE_RECOVERY_PROFILE_MISSING",
                ("profile_revision",),
            )

        events = load_journal_events(path)
        scoped_events = tuple(
            event for event in events if event.profile_revision_id == profile_revision_id
        )
        if not scoped_events:
            return _blocked(
                profile_revision_id,
                "FUTURES_DCA_PROFILE_RECOVERY_EVENT_MISSING",
                ("journal_event",),
            )
        if any(event.event_state != "ACCEPTED" for event in scoped_events):
            return _blocked(
                profile_revision_id,
                "FUTURES_DCA_PROFILE_RECOVERY_EVENT_NOT_ACCEPTED",
                ("accepted_event",),
                event_count=len(scoped_events),
            )

        scoped_event_ids = {event.event_id for event in scoped_events}
        postings = tuple(
            posting
            for posting in load_economic_postings(path)
            if posting.source_event_id in scoped_event_ids
        )
        if not postings:
            return _blocked(
                profile_revision_id,
                "FUTURES_DCA_PROFILE_RECOVERY_POSTING_MISSING",
                ("economic_posting",),
                event_count=len(scoped_events),
            )

        transitions = tuple(
            record
            for record in load_futures_dca_release_transitions(path)
            if record.transition.transition_event_id in scoped_event_ids
        )
        posting_event_ids = {posting.source_event_id for posting in postings}
        transition_event_ids = {
            record.transition.transition_event_id for record in transitions
        }
        if transition_event_ids != posting_event_ids:
            return _blocked(
                profile_revision_id,
                "FUTURES_DCA_PROFILE_RECOVERY_RELEASE_MISSING",
                ("release_transition",),
                event_count=len(scoped_events),
                posting_count=len(postings),
            )

        receipts = tuple(
            receipt
            for receipt in load_futures_dca_core_replay_receipts(path)
            if receipt.event_id in scoped_event_ids
        )
        event_by_id = {event.event_id: event for event in scoped_events}
        if any(
            event_by_id.get(receipt.transition_event_id) is None
            or event_by_id[receipt.transition_event_id].profile_revision_id
            != profile_revision_id
            for receipt in receipts
        ):
            return _blocked(
                profile_revision_id,
                "FUTURES_DCA_PROFILE_RECOVERY_SCOPE_CONFLICT",
                ("profile_scope",),
                event_count=len(scoped_events),
                posting_count=len(postings),
                receipt_count=len(receipts),
            )
        receipt_posting_ids = {receipt.posting_id for receipt in receipts}
        if receipt_posting_ids != {posting.posting_id for posting in postings}:
            return _blocked(
                profile_revision_id,
                "FUTURES_DCA_PROFILE_RECOVERY_RECEIPT_MISSING",
                ("core_replay_receipt",),
                event_count=len(scoped_events),
                posting_count=len(postings),
                receipt_count=len(receipts),
            )

        store_preflight = preflight_futures_dca_core_replay_store(path)
        if store_preflight.status != "READY":
            return _blocked(
                profile_revision_id,
                store_preflight.reason_code,
                store_preflight.missing_authority,
                event_count=len(scoped_events),
                posting_count=len(postings),
                receipt_count=len(receipts),
            )

        core_decisions = preflight_futures_dca_core_binding(path)
        scoped_decisions = tuple(
            decision for decision in core_decisions if decision.posting_id in receipt_posting_ids
        )
        if len(scoped_decisions) != len(postings) or any(
            decision.status != "BLOCKED" for decision in scoped_decisions
        ):
            return _blocked(
                profile_revision_id,
                "FUTURES_DCA_PROFILE_RECOVERY_CORE_ADMISSION_UNSAFE",
                ("core_order_intent",),
                event_count=len(scoped_events),
                posting_count=len(postings),
                receipt_count=len(receipts),
            )

        missing_authority = tuple(sorted({
            authority
            for decision in scoped_decisions
            for authority in decision.missing_authority
        }))
        return FuturesDcaProfileRecoveryCapability(
            profile_revision_id,
            "READY",
            "BLOCKED",
            missing_authority,
            "FUTURES_DCA_PROFILE_RECOVERY_READY_CORE_ADMISSION_BLOCKED",
            len(scoped_events),
            len(postings),
            len(receipts),
        )
    except FuturesDcaJournalSchemaError:
        return _blocked(
            profile_revision_id,
            "FUTURES_DCA_PROFILE_RECOVERY_DURABLE_INVALID",
            ("durable_journal",),
        )


def _blocked(
    profile_revision_id: str,
    reason_code: str,
    missing_authority: tuple[str, ...],
    *,
    event_count: int = 0,
    posting_count: int = 0,
    receipt_count: int = 0,
) -> FuturesDcaProfileRecoveryCapability:
    return FuturesDcaProfileRecoveryCapability(
        profile_revision_id,
        "BLOCKED",
        "BLOCKED",
        missing_authority,
        reason_code,
        event_count,
        posting_count,
        receipt_count,
    )
