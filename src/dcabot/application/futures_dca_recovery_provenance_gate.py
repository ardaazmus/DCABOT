"""Read-only recovery-to-provenance gate for Futures DCA."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaJournalSchemaError,
    load_profile_revisions,
)
from dcabot.persistence.futures_dca_provenance_target import (
    FuturesDcaProvenanceMigrationManifest,
    assess_futures_dca_provenance_publish_readiness,
    load_accepted_profile_source_snapshots,
)
from .futures_dca_recovery_snapshot import project_futures_dca_profile_recovery_snapshot


@dataclass(frozen=True, slots=True)
class FuturesDcaRecoveryProvenanceGate:
    """Immutable cross-check result; neither READY state grants publish authority."""

    status: Literal["READY_FOR_REVIEW", "NO_GO"]
    approval_state: Literal["REQUIRED"]
    publish_action: Literal["BLOCKED"]
    migration_action: Literal["BLOCKED"]
    profile_revision_id: str
    recovery_status: str
    provenance_status: str
    manifest_hash: str
    issues: tuple[str, ...]


def assess_futures_dca_recovery_provenance_gate(
    recovery_path: Path,
    provenance_path: Path,
    profile_revision_id: str,
    active_profile_revision_id: str,
    manifest: FuturesDcaProvenanceMigrationManifest,
    independent_oracle_status: Literal["PASS", "FAIL", "NOT_RUN"],
    prior_gate_status: Literal["PASS", "NO_GO", "NOT_RUN"],
) -> FuturesDcaRecoveryProvenanceGate:
    """Cross-check one recovery snapshot with immutable source provenance.

    All reads are fail-closed.  A clean cross-check only reaches human review;
    migration and publish remain blocked by construction.
    """

    snapshot = project_futures_dca_profile_recovery_snapshot(
        recovery_path, profile_revision_id, active_profile_revision_id
    )
    publish_readiness = assess_futures_dca_provenance_publish_readiness(
        provenance_path, manifest, independent_oracle_status, prior_gate_status
    )
    issues = set(publish_readiness.issues)
    if snapshot.status != "READY":
        issues.add(f"FUTURES_DCA_RECOVERY_PROVENANCE_SNAPSHOT_{snapshot.status}")

    try:
        recovery_profiles = {
            profile.revision_id: profile for profile in load_profile_revisions(recovery_path)
        }
        provenance_profiles = {
            profile.revision_id: profile for profile in load_profile_revisions(provenance_path)
        }
        if recovery_profiles.get(profile_revision_id) != provenance_profiles.get(profile_revision_id):
            issues.add("FUTURES_DCA_RECOVERY_PROVENANCE_PROFILE_MISMATCH")
        accepted_sources = tuple(
            source
            for source in load_accepted_profile_source_snapshots(provenance_path)
            if source.profile_revision_id == profile_revision_id
        )
        if len(accepted_sources) != 1:
            issues.add("FUTURES_DCA_RECOVERY_PROVENANCE_SOURCE_CARDINALITY")
    except FuturesDcaJournalSchemaError as exc:
        issues.add(f"FUTURES_DCA_RECOVERY_PROVENANCE_{exc.code}")

    return FuturesDcaRecoveryProvenanceGate(
        "READY_FOR_REVIEW" if not issues else "NO_GO",
        "REQUIRED",
        "BLOCKED",
        "BLOCKED",
        profile_revision_id,
        snapshot.status,
        publish_readiness.status,
        publish_readiness.manifest_hash,
        tuple(sorted(issues)),
    )
