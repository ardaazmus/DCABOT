"""Read-only profile recovery snapshot projection for Futures DCA."""

from dataclasses import dataclass
from pathlib import Path

from dcabot.persistence.futures_dca_core_replay_store import (
    load_futures_dca_core_replay_receipts,
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
from .futures_dca_recovery_capability import assess_futures_dca_profile_recovery


@dataclass(frozen=True, slots=True)
class FuturesDcaProfileRecoverySnapshot:
    """Bounded profile lineage without CORE01 or venue economic state."""

    profile_revision_id: str
    status: str
    core_admission_status: str
    reason_code: str
    missing_authority: tuple[str, ...]
    event_ids: tuple[str, ...]
    posting_ids: tuple[str, ...]
    release_identities: tuple[str, ...]
    receipt_fingerprints: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in {"READY", "BLOCKED", "QUARANTINED"}:
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_RECOVERY_SNAPSHOT_STATUS_INVALID",
                "Recovery snapshot status geçersiz.",
            )
        if self.core_admission_status != "BLOCKED":
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_RECOVERY_SNAPSHOT_CORE_STATUS_INVALID",
                "Recovery snapshot CORE01 admission’ı fail-closed BLOCKED olmalıdır.",
            )
        if not isinstance(self.missing_authority, tuple) or any(
            not isinstance(item, str) for item in self.missing_authority
        ):
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_RECOVERY_SNAPSHOT_AUTHORITY_INVALID",
                "Recovery snapshot authority tuple olmalıdır.",
            )
        for values in (
            self.event_ids,
            self.posting_ids,
            self.release_identities,
            self.receipt_fingerprints,
        ):
            if not isinstance(values, tuple) or any(not isinstance(item, str) for item in values):
                raise FuturesDcaJournalSchemaError(
                    "FUTURES_DCA_RECOVERY_SNAPSHOT_IDENTITY_INVALID",
                    "Recovery snapshot identity listesi geçersiz.",
                )
        if self.status != "READY" and any(
            values
            for values in (
                self.event_ids,
                self.posting_ids,
                self.release_identities,
                self.receipt_fingerprints,
            )
        ):
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_RECOVERY_SNAPSHOT_STATE_UNEXPECTED",
                "Blocked veya quarantined snapshot projection taşıyamaz.",
            )


def project_futures_dca_profile_recovery_snapshot(
    path: Path,
    profile_revision_id: str,
    active_profile_revision_id: str,
) -> FuturesDcaProfileRecoverySnapshot:
    """Project one profile's durable lineage and quarantine stale selection."""

    if not all(
        isinstance(value, str) and value
        for value in (profile_revision_id, active_profile_revision_id)
    ):
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_RECOVERY_SNAPSHOT_PROFILE_INVALID",
            "Profile revision kimlikleri güvenli string olmalıdır.",
        )
    try:
        profiles = load_profile_revisions(path)
        profile_ids = {profile.revision_id for profile in profiles}
        if profile_revision_id not in profile_ids:
            return _empty_snapshot(
                profile_revision_id,
                "FUTURES_DCA_RECOVERY_SNAPSHOT_PROFILE_MISSING",
                ("profile_revision",),
            )
        if active_profile_revision_id not in profile_ids:
            return _empty_snapshot(
                profile_revision_id,
                "FUTURES_DCA_RECOVERY_SNAPSHOT_ACTIVE_PROFILE_MISSING",
                ("active_profile_revision",),
            )
        if active_profile_revision_id != profile_revision_id:
            return _empty_snapshot(
                profile_revision_id,
                "FUTURES_DCA_RECOVERY_SNAPSHOT_PROFILE_STALE",
                ("active_profile_revision",),
                status="QUARANTINED",
            )

        capability = assess_futures_dca_profile_recovery(path, profile_revision_id)
        if capability.status != "READY":
            return _empty_snapshot(
                profile_revision_id,
                capability.reason_code,
                capability.missing_authority,
            )

        events = tuple(
            event
            for event in load_journal_events(path)
            if event.profile_revision_id == profile_revision_id
        )
        event_ids = {event.event_id for event in events}
        postings = tuple(
            posting
            for posting in load_economic_postings(path)
            if posting.source_event_id in event_ids
        )
        releases = tuple(
            record
            for record in load_futures_dca_release_transitions(path)
            if record.transition.transition_event_id in event_ids
        )
        receipts = tuple(
            receipt
            for receipt in load_futures_dca_core_replay_receipts(path)
            if receipt.event_id in event_ids
        )
        return FuturesDcaProfileRecoverySnapshot(
            profile_revision_id,
            "READY",
            capability.core_admission_status,
            "FUTURES_DCA_RECOVERY_SNAPSHOT_READY_CORE_ADMISSION_BLOCKED",
            capability.missing_authority,
            tuple(event.event_id for event in events),
            tuple(posting.posting_id for posting in sorted(postings, key=lambda item: (item.posting_cursor, item.posting_id))),
            tuple(
                record.transition.release_identity
                for record in sorted(
                    releases,
                    key=lambda item: (item.transition.release_cursor, item.transition.release_identity),
                )
            ),
            tuple(sorted(receipt.fingerprint for receipt in receipts)),
        )
    except FuturesDcaJournalSchemaError:
        return _empty_snapshot(
            profile_revision_id,
            "FUTURES_DCA_RECOVERY_SNAPSHOT_DURABLE_INVALID",
            ("durable_journal",),
        )


def _empty_snapshot(
    profile_revision_id: str,
    reason_code: str,
    missing_authority: tuple[str, ...],
    *,
    status: str = "BLOCKED",
) -> FuturesDcaProfileRecoverySnapshot:
    return FuturesDcaProfileRecoverySnapshot(
        profile_revision_id,
        status,
        "BLOCKED",
        reason_code,
        missing_authority,
        (),
        (),
        (),
        (),
    )
