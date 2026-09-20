"""Bounded, unpublished provenance target layered on a new v1 journal file."""

from dataclasses import dataclass
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Literal

from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaJournalSchemaError,
    _open_existing,
    create_futures_dca_journal_schema,
    load_profile_revisions,
)


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
_HASH = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_SOURCE_STATES = frozenset({"ACCEPTED", "UNKNOWN", "QUARANTINED"})


@dataclass(frozen=True, slots=True)
class FuturesDcaProfileSourceSnapshot:
    """Immutable provenance identity for one profile revision snapshot."""

    source_snapshot_id: str
    profile_revision_id: str
    source_kind: str
    source_row_id: str
    payload_hash: str
    source_schema_revision: str
    observed_time_us: int
    source_state: str = "ACCEPTED"


@dataclass(frozen=True, slots=True)
class FuturesDcaProvenanceValidation:
    """Read-only validation result; READY never publishes the target."""

    status: Literal["READY", "NO_GO"]
    publish_decision: Literal["READY", "NO_GO"]
    issues: tuple[str, ...]
    profile_revision_count: int
    snapshot_count: int
    accepted_snapshot_count: int


@dataclass(frozen=True, slots=True)
class FuturesDcaProvenanceMigrationMapping:
    """One immutable source-row to provenance-target-row mapping."""

    source_kind: str
    source_row_id: str
    target_row_id: str
    profile_revision_id: str
    payload_hash: str
    source_schema_revision: str
    observed_time_us: int
    source_state: str = "ACCEPTED"


@dataclass(frozen=True, slots=True)
class FuturesDcaProvenanceMigrationManifest:
    """Hash-bound mapping list; it never grants migration authority."""

    manifest_hash: str
    mappings: tuple[FuturesDcaProvenanceMigrationMapping, ...]
    status: Literal["READY", "NO_GO"]
    issues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FuturesDcaProvenanceManifestDecision:
    """Read-only result of comparing a manifest with one target."""

    status: Literal["READY", "NO_GO"]
    manifest_hash: str
    mapping_count: int
    issues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FuturesDcaProvenancePublishReadiness:
    """Human-review gate; a READY result still keeps publish blocked."""

    status: Literal["READY_FOR_REVIEW", "NO_GO"]
    approval_state: Literal["REQUIRED"]
    publish_action: Literal["BLOCKED"]
    manifest_hash: str
    issues: tuple[str, ...]


def create_futures_dca_provenance_target(path: Path) -> Path:
    """Create a new journal target with an unpublished provenance owner."""

    target = create_futures_dca_journal_schema(path)
    db = sqlite3.connect(target.resolve().as_uri() + "?mode=rw", uri=True, isolation_level=None)
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute(
                "CREATE TABLE profile_source_snapshots("
                "source_snapshot_id TEXT PRIMARY KEY, profile_revision_id TEXT NOT NULL, "
                "source_kind TEXT NOT NULL, source_row_id TEXT NOT NULL, payload_hash TEXT NOT NULL, "
                "source_schema_revision TEXT NOT NULL, observed_time_us INTEGER NOT NULL, "
                "source_state TEXT NOT NULL CHECK(source_state IN ('ACCEPTED','UNKNOWN','QUARANTINED')), "
                "FOREIGN KEY(profile_revision_id) REFERENCES profile_revisions(revision_id))"
            )
            db.execute(
                "CREATE UNIQUE INDEX accepted_profile_source ON profile_source_snapshots(profile_revision_id) "
                "WHERE source_state='ACCEPTED'"
            )
            db.execute(
                "INSERT INTO journal_metadata(key, value) VALUES (?, ?)",
                ("provenance_owner", "UNPUBLISHED_PROFILE_SOURCE_SNAPSHOTS"),
            )
            db.execute("COMMIT")
        except BaseException:
            db.execute("ROLLBACK")
            raise
    except (OSError, sqlite3.Error) as exc:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_PROVENANCE_TARGET_UNAVAILABLE", "Provenance target oluşturulamadı."
        ) from exc
    finally:
        db.close()
    return target


def build_futures_dca_provenance_migration_manifest(
    mappings: tuple[FuturesDcaProvenanceMigrationMapping, ...],
) -> FuturesDcaProvenanceMigrationManifest:
    """Build a deterministic source-to-target manifest without writing it."""

    if not isinstance(mappings, tuple):
        raise TypeError("mappings must be tuple")
    normalized = tuple(sorted((_normalize_mapping(mapping) for mapping in mappings), key=_mapping_sort_key))
    issues = set()
    source_ids = set()
    target_ids = set()
    profile_ids = set()
    for mapping in normalized:
        source_id = (mapping.source_kind, mapping.source_row_id)
        if source_id in source_ids:
            issues.add("FUTURES_DCA_MIGRATION_SOURCE_DUPLICATE")
        source_ids.add(source_id)
        if mapping.target_row_id in target_ids:
            issues.add("FUTURES_DCA_MIGRATION_TARGET_DUPLICATE")
        target_ids.add(mapping.target_row_id)
        if mapping.source_state != "ACCEPTED":
            issues.add(f"FUTURES_DCA_MIGRATION_{mapping.source_state}")
        if mapping.profile_revision_id in profile_ids:
            issues.add("FUTURES_DCA_MIGRATION_PROFILE_CONFLICT")
        profile_ids.add(mapping.profile_revision_id)
    if not normalized:
        issues.add("FUTURES_DCA_MIGRATION_NO_MAPPINGS")
    manifest_hash = _digest_manifest(normalized)
    status = "READY" if not issues else "NO_GO"
    return FuturesDcaProvenanceMigrationManifest(
        manifest_hash, normalized, status, tuple(sorted(issues))
    )


def evaluate_futures_dca_provenance_manifest(
    path: Path, manifest: FuturesDcaProvenanceMigrationManifest
) -> FuturesDcaProvenanceManifestDecision:
    """Compare a manifest with a target read-only; never migrates or publishes."""

    if not isinstance(manifest, FuturesDcaProvenanceMigrationManifest):
        raise TypeError("manifest must be FuturesDcaProvenanceMigrationManifest")
    issues = set()
    try:
        canonical = build_futures_dca_provenance_migration_manifest(manifest.mappings)
    except (TypeError, FuturesDcaJournalSchemaError):
        canonical = None
        issues.add("FUTURES_DCA_MIGRATION_MANIFEST_INVALID")
    if canonical is not None:
        issues.update(canonical.issues)
        if manifest.manifest_hash != canonical.manifest_hash:
            issues.add("FUTURES_DCA_MIGRATION_MANIFEST_HASH_MISMATCH")
        if manifest.status != canonical.status or manifest.issues != canonical.issues:
            issues.add("FUTURES_DCA_MIGRATION_MANIFEST_METADATA_MISMATCH")
    target_validation = validate_futures_dca_provenance_target(path)
    issues.update(target_validation.issues)
    if canonical is not None and target_validation.status == "READY" and canonical.status == "READY":
        actual = tuple(
            sorted(
                (
                    FuturesDcaProvenanceMigrationMapping(
                        snapshot.source_kind,
                        snapshot.source_row_id,
                        snapshot.source_snapshot_id,
                        snapshot.profile_revision_id,
                        snapshot.payload_hash,
                        snapshot.source_schema_revision,
                        snapshot.observed_time_us,
                        snapshot.source_state,
                    )
                    for snapshot in load_accepted_profile_source_snapshots(path)
                ),
                key=_mapping_sort_key,
            )
        )
        if actual != manifest.mappings:
            issues.add("FUTURES_DCA_MIGRATION_MANIFEST_TARGET_MISMATCH")
    return FuturesDcaProvenanceManifestDecision(
        "READY" if not issues else "NO_GO",
        manifest.manifest_hash,
        len(manifest.mappings),
        tuple(sorted(issues)),
    )


def assess_futures_dca_provenance_publish_readiness(
    path: Path,
    manifest: FuturesDcaProvenanceMigrationManifest,
    independent_oracle_status: Literal["PASS", "FAIL", "NOT_RUN"],
    prior_gate_status: Literal["PASS", "NO_GO", "NOT_RUN"],
) -> FuturesDcaProvenancePublishReadiness:
    """Combine local gates for human review without enabling publish."""

    if independent_oracle_status not in {"PASS", "FAIL", "NOT_RUN"}:
        raise ValueError("independent_oracle_status geçersiz")
    if prior_gate_status not in {"PASS", "NO_GO", "NOT_RUN"}:
        raise ValueError("prior_gate_status geçersiz")
    decision = evaluate_futures_dca_provenance_manifest(path, manifest)
    issues = set(decision.issues)
    if independent_oracle_status != "PASS":
        issues.add(f"FUTURES_DCA_PUBLISH_ORACLE_{independent_oracle_status}")
    if prior_gate_status != "PASS":
        issues.add(f"FUTURES_DCA_PUBLISH_PRIOR_GATE_{prior_gate_status}")
    status = "READY_FOR_REVIEW" if not issues else "NO_GO"
    return FuturesDcaProvenancePublishReadiness(
        status,
        "REQUIRED",
        "BLOCKED",
        manifest.manifest_hash,
        tuple(sorted(issues)),
    )


def validate_futures_dca_provenance_target(path: Path) -> FuturesDcaProvenanceValidation:
    """Validate target contents without writing, migrating, or publishing."""

    try:
        profiles = load_profile_revisions(path)
        db = _open_provenance_target(path)
    except FuturesDcaJournalSchemaError as exc:
        return FuturesDcaProvenanceValidation("NO_GO", "NO_GO", (exc.code,), 0, 0, 0)
    try:
        rows = db.execute(
            "SELECT source_snapshot_id, profile_revision_id, source_kind, source_row_id, payload_hash, "
            "source_schema_revision, observed_time_us, source_state FROM profile_source_snapshots "
            "ORDER BY source_snapshot_id"
        ).fetchall()
        profile_ids = {profile.revision_id for profile in profiles}
        issues = set()
        accepted_by_profile = {}
        for row in rows:
            try:
                snapshot = _normalize_snapshot(FuturesDcaProfileSourceSnapshot(*row))
            except FuturesDcaJournalSchemaError as exc:
                issues.add(exc.code)
                continue
            if snapshot.profile_revision_id not in profile_ids:
                issues.add("FUTURES_DCA_PROVENANCE_PROFILE_MISSING")
            if snapshot.source_state == "ACCEPTED":
                accepted_by_profile[snapshot.profile_revision_id] = (
                    accepted_by_profile.get(snapshot.profile_revision_id, 0) + 1
                )
            else:
                issues.add(f"FUTURES_DCA_PROVENANCE_{snapshot.source_state}")
        if not profiles:
            issues.add("FUTURES_DCA_PROVENANCE_NO_PROFILES")
        if not rows:
            issues.add("FUTURES_DCA_PROVENANCE_NO_SNAPSHOTS")
        if set(accepted_by_profile) != profile_ids:
            issues.add("FUTURES_DCA_PROVENANCE_PROFILE_WITHOUT_ACCEPTED_SOURCE")
        if any(count != 1 for count in accepted_by_profile.values()):
            issues.add("FUTURES_DCA_PROVENANCE_ACCEPTED_PROFILE_CONFLICT")
        status = "READY" if not issues else "NO_GO"
        return FuturesDcaProvenanceValidation(
            status,
            status,
            tuple(sorted(issues)),
            len(profiles),
            len(rows),
            sum(accepted_by_profile.values()),
        )
    except sqlite3.Error:
        return FuturesDcaProvenanceValidation(
            "NO_GO", "NO_GO", ("FUTURES_DCA_PROVENANCE_CORRUPT",), len(profiles), 0, 0
        )
    finally:
        db.close()


def append_profile_source_snapshot(path: Path, snapshot: FuturesDcaProfileSourceSnapshot) -> str:
    """Append one source snapshot, keeping non-accepted states non-authoritative."""

    normalized = _normalize_snapshot(snapshot)
    db = _open_provenance_target(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        try:
            if db.execute(
                "SELECT 1 FROM profile_revisions WHERE revision_id=?", (normalized.profile_revision_id,)
            ).fetchone() is None:
                raise FuturesDcaJournalSchemaError(
                    "FUTURES_DCA_PROVENANCE_PROFILE_MISSING", "Provenance profile revision bulunamadı."
                )
            prior = db.execute(
                "SELECT source_snapshot_id, profile_revision_id, source_kind, source_row_id, payload_hash, "
                "source_schema_revision, observed_time_us, source_state FROM profile_source_snapshots "
                "WHERE source_snapshot_id=?",
                (normalized.source_snapshot_id,),
            ).fetchone()
            values = _snapshot_values(normalized)
            if prior is not None:
                if prior != values:
                    raise FuturesDcaJournalSchemaError(
                        "FUTURES_DCA_PROVENANCE_CONFLICT", "Snapshot identity farklı payload ile kullanılamaz."
                    )
                db.execute("COMMIT")
                return "DUPLICATE"
            try:
                db.execute(
                    "INSERT INTO profile_source_snapshots(" 
                    "source_snapshot_id, profile_revision_id, source_kind, source_row_id, payload_hash, "
                    "source_schema_revision, observed_time_us, source_state) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    values,
                )
            except sqlite3.IntegrityError as exc:
                if "accepted_profile_source" not in str(exc) and (
                    "UNIQUE constraint failed: profile_source_snapshots.profile_revision_id" not in str(exc)
                ):
                    raise
                raise FuturesDcaJournalSchemaError(
                    "FUTURES_DCA_PROVENANCE_PROFILE_CONFLICT", "Profile revision accepted source ile çakışıyor."
                ) from exc
            db.execute("COMMIT")
            return "ACCEPTED"
        except BaseException:
            db.execute("ROLLBACK")
            raise
    finally:
        db.close()


def load_accepted_profile_source_snapshots(path: Path) -> tuple[FuturesDcaProfileSourceSnapshot, ...]:
    """Replay only accepted provenance; UNKNOWN/QUARANTINED stays non-authoritative."""

    db = _open_provenance_target(path)
    try:
        rows = db.execute(
            "SELECT source_snapshot_id, profile_revision_id, source_kind, source_row_id, payload_hash, "
            "source_schema_revision, observed_time_us, source_state FROM profile_source_snapshots "
            "WHERE source_state='ACCEPTED' ORDER BY source_snapshot_id"
        ).fetchall()
        return tuple(_normalize_snapshot(FuturesDcaProfileSourceSnapshot(*row)) for row in rows)
    except FuturesDcaJournalSchemaError:
        raise
    except (TypeError, ValueError, sqlite3.Error) as exc:
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_PROVENANCE_CORRUPT", "Accepted provenance replay edilemedi."
        ) from exc
    finally:
        db.close()


def _open_provenance_target(path: Path) -> sqlite3.Connection:
    db = _open_existing(path)
    try:
        if db.execute("SELECT 1 FROM journal_metadata WHERE key='provenance_owner' AND value=?", (
            "UNPUBLISHED_PROFILE_SOURCE_SNAPSHOTS",
        )).fetchone() is None:
            raise FuturesDcaJournalSchemaError(
                "FUTURES_DCA_PROVENANCE_TARGET_REQUIRED", "Dosya provenance target olarak ilan edilmemiş."
            )
        db.execute("SELECT 1 FROM profile_source_snapshots LIMIT 1")
        return db
    except FuturesDcaJournalSchemaError:
        db.close()
        raise
    except sqlite3.Error as exc:
        db.close()
        raise FuturesDcaJournalSchemaError(
            "FUTURES_DCA_PROVENANCE_TARGET_INVALID", "Provenance target tabloları eksik."
        ) from exc


def _normalize_snapshot(snapshot: FuturesDcaProfileSourceSnapshot) -> FuturesDcaProfileSourceSnapshot:
    if not isinstance(snapshot, FuturesDcaProfileSourceSnapshot):
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_PROVENANCE_INVALID", "Source snapshot güvenli tipte değil.")
    for value in (
        snapshot.source_snapshot_id,
        snapshot.profile_revision_id,
        snapshot.source_kind,
        snapshot.source_row_id,
        snapshot.source_schema_revision,
    ):
        if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
            raise FuturesDcaJournalSchemaError("FUTURES_DCA_PROVENANCE_INVALID", "Source snapshot identity geçersiz.")
    if not isinstance(snapshot.payload_hash, str) or _HASH.fullmatch(snapshot.payload_hash) is None:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_PROVENANCE_INVALID", "Payload hash SHA-256 olmalıdır.")
    if type(snapshot.observed_time_us) is not int or snapshot.observed_time_us < 0:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_PROVENANCE_INVALID", "Observed time geçersiz.")
    if snapshot.source_state not in _SOURCE_STATES:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_PROVENANCE_INVALID", "Source state geçersiz.")
    return snapshot


def _snapshot_values(snapshot: FuturesDcaProfileSourceSnapshot) -> tuple[object, ...]:
    return (
        snapshot.source_snapshot_id,
        snapshot.profile_revision_id,
        snapshot.source_kind,
        snapshot.source_row_id,
        snapshot.payload_hash,
        snapshot.source_schema_revision,
        snapshot.observed_time_us,
        snapshot.source_state,
    )


def _normalize_mapping(mapping: FuturesDcaProvenanceMigrationMapping) -> FuturesDcaProvenanceMigrationMapping:
    if not isinstance(mapping, FuturesDcaProvenanceMigrationMapping):
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_MIGRATION_INVALID", "Migration mapping güvenli tipte değil.")
    for value in (
        mapping.source_kind,
        mapping.source_row_id,
        mapping.target_row_id,
        mapping.profile_revision_id,
        mapping.source_schema_revision,
    ):
        if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
            raise FuturesDcaJournalSchemaError("FUTURES_DCA_MIGRATION_INVALID", "Migration mapping identity geçersiz.")
    if not isinstance(mapping.payload_hash, str) or _HASH.fullmatch(mapping.payload_hash) is None:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_MIGRATION_INVALID", "Migration payload hash geçersiz.")
    if type(mapping.observed_time_us) is not int or mapping.observed_time_us < 0:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_MIGRATION_INVALID", "Migration observed time geçersiz.")
    if mapping.source_state not in _SOURCE_STATES:
        raise FuturesDcaJournalSchemaError("FUTURES_DCA_MIGRATION_INVALID", "Migration source state geçersiz.")
    return mapping


def _mapping_sort_key(mapping: FuturesDcaProvenanceMigrationMapping) -> tuple[str, ...]:
    return mapping.target_row_id, mapping.source_kind, mapping.source_row_id


def _digest_manifest(mappings: tuple[FuturesDcaProvenanceMigrationMapping, ...]) -> str:
    payload = json.dumps(
        [
            {
                "source_kind": mapping.source_kind,
                "source_row_id": mapping.source_row_id,
                "target_row_id": mapping.target_row_id,
                "profile_revision_id": mapping.profile_revision_id,
                "payload_hash": mapping.payload_hash,
                "source_schema_revision": mapping.source_schema_revision,
                "observed_time_us": mapping.observed_time_us,
                "source_state": mapping.source_state,
            }
            for mapping in mappings
        ],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
