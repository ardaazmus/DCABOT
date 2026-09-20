from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dcabot.application.futures_dca_core_mapping import FuturesDcaCoreReplayReceipt
from dcabot.application.futures_dca_recovery_provenance_gate import (
    FuturesDcaRecoveryProvenanceGate,
    assess_futures_dca_recovery_provenance_gate,
)
from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaEconomicPosting,
    FuturesDcaEventEnvelope,
    FuturesDcaProfileRevision,
    FuturesDcaReservationProjection,
    append_journal_event,
    append_profile_revision,
    append_reservation_projection,
    create_futures_dca_journal_schema,
)
from dcabot.persistence.futures_dca_provenance_target import (
    FuturesDcaProfileSourceSnapshot,
    FuturesDcaProvenanceMigrationMapping,
    append_profile_source_snapshot,
    build_futures_dca_provenance_migration_manifest,
    create_futures_dca_provenance_target,
)
from dcabot.persistence.futures_dca_release_store import (
    append_futures_dca_core_replay_receipt_atomic,
)
from dcabot.persistence.futures_dca_release_transition import FuturesDcaReleaseTransition


class FuturesDcaRecoveryProvenanceGateTests(unittest.TestCase):
    @staticmethod
    def profile(revision_id="profile-1", fee_policy_revision="fee-1"):
        return FuturesDcaProfileRevision(
            revision_id, "BINANCE", "USD_M_PERPETUAL", "BTCUSDT", "USDT", "ISOLATED", "ONE_WAY", 100,
            "0.001", fee_policy_revision, "slippage-1", "rounding-1",
        )

    def prepare(self):
        directory = TemporaryDirectory()
        recovery = create_futures_dca_journal_schema(Path(directory.name) / "recovery.sqlite")
        append_profile_revision(recovery, self.profile())
        append_journal_event(recovery, FuturesDcaEventEnvelope(
            "event-1", 1, "execution-1", "order-1", "FILL", "profile-1", 100, 101,
            "1", "100", "100", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}',
        ))
        append_reservation_projection(recovery, FuturesDcaReservationProjection(
            "reservation-1", "deal-1", "USDT", "100", "0", "100", None, "OPEN", 0, "event-1",
        ))
        event = FuturesDcaEventEnvelope(
            "event-2", 2, "execution-2", "order-1", "FILL", "profile-1", 100, 101,
            "0.4", "100", "40", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}',
        )
        transition = FuturesDcaReleaseTransition(
            "reservation-1", "event-2", "release-1", 1, 0, "PARTIAL_FILL", "40", "60",
        )
        posting = FuturesDcaEconomicPosting("posting-1", "event-2", 1, "40", "0", "0", "PROJECTED")
        append_futures_dca_core_replay_receipt_atomic(
            recovery, event, transition, posting,
            FuturesDcaCoreReplayReceipt("mapping-1", "event-2", "posting-1", "event-2", "release-1", 1, "a" * 64),
        )
        provenance = create_futures_dca_provenance_target(Path(directory.name) / "provenance.sqlite")
        append_profile_revision(provenance, self.profile())
        source = FuturesDcaProfileSourceSnapshot(
            "snapshot-1", "profile-1", "BINANCE_EXCHANGE_INFO", "BTCUSDT", "b" * 64, "schema-1", 100,
        )
        append_profile_source_snapshot(provenance, source)
        manifest = build_futures_dca_provenance_migration_manifest((
            FuturesDcaProvenanceMigrationMapping(
                source.source_kind, source.source_row_id, source.source_snapshot_id,
                source.profile_revision_id, source.payload_hash, source.source_schema_revision,
                source.observed_time_us, source.source_state,
            ),
        ))
        return directory, recovery, provenance, manifest

    def test_matching_snapshot_is_ready_for_review_but_never_authorizes_write(self):
        directory, recovery, provenance, manifest = self.prepare()
        try:
            before_recovery = recovery.read_bytes()
            before_provenance = provenance.read_bytes()
            result = assess_futures_dca_recovery_provenance_gate(
                recovery, provenance, "profile-1", "profile-1", manifest, "PASS", "PASS"
            )
            self.assertEqual(result, FuturesDcaRecoveryProvenanceGate(
                "READY_FOR_REVIEW", "REQUIRED", "BLOCKED", "BLOCKED", "profile-1",
                "READY", "READY_FOR_REVIEW", manifest.manifest_hash, (),
            ))
            self.assertEqual(recovery.read_bytes(), before_recovery)
            self.assertEqual(provenance.read_bytes(), before_provenance)
        finally:
            directory.cleanup()

    def test_stale_recovery_is_no_go(self):
        directory, recovery, provenance, manifest = self.prepare()
        try:
            append_profile_revision(recovery, self.profile("profile-2", "fee-2"))
            result = assess_futures_dca_recovery_provenance_gate(
                recovery, provenance, "profile-1", "profile-2", manifest, "PASS", "PASS"
            )
            self.assertEqual(result.status, "NO_GO")
            self.assertIn("FUTURES_DCA_RECOVERY_PROVENANCE_SNAPSHOT_QUARANTINED", result.issues)
            self.assertEqual(result.publish_action, "BLOCKED")
        finally:
            directory.cleanup()

    def test_profile_source_mismatch_is_no_go(self):
        directory, recovery, provenance, manifest = self.prepare()
        try:
            provenance = create_futures_dca_provenance_target(Path(directory.name) / "mismatch.sqlite")
            append_profile_revision(provenance, self.profile("profile-1", "fee-2"))
            source = FuturesDcaProfileSourceSnapshot(
                "snapshot-1", "profile-1", "BINANCE_EXCHANGE_INFO", "BTCUSDT", "b" * 64, "schema-1", 100,
            )
            append_profile_source_snapshot(provenance, source)
            manifest = build_futures_dca_provenance_migration_manifest((
                FuturesDcaProvenanceMigrationMapping(
                    source.source_kind, source.source_row_id, source.source_snapshot_id,
                    source.profile_revision_id, source.payload_hash, source.source_schema_revision,
                    source.observed_time_us, source.source_state,
                ),
            ))
            result = assess_futures_dca_recovery_provenance_gate(
                recovery, provenance, "profile-1", "profile-1", manifest, "PASS", "PASS"
            )
            self.assertEqual(result.status, "NO_GO")
            self.assertIn("FUTURES_DCA_RECOVERY_PROVENANCE_PROFILE_MISMATCH", result.issues)
        finally:
            directory.cleanup()

    def test_prior_gate_or_oracle_failure_keeps_no_go(self):
        directory, recovery, provenance, manifest = self.prepare()
        try:
            result = assess_futures_dca_recovery_provenance_gate(
                recovery, provenance, "profile-1", "profile-1", manifest, "NOT_RUN", "NO_GO"
            )
            self.assertEqual(result.status, "NO_GO")
            self.assertIn("FUTURES_DCA_PUBLISH_ORACLE_NOT_RUN", result.issues)
            self.assertIn("FUTURES_DCA_PUBLISH_PRIOR_GATE_NO_GO", result.issues)
            self.assertEqual(result.migration_action, "BLOCKED")
        finally:
            directory.cleanup()


if __name__ == "__main__":
    unittest.main()
