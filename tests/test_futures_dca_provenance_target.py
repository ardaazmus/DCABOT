import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaProfileRevision,
    append_profile_revision,
)
from dcabot.persistence.futures_dca_provenance_target import (
    FuturesDcaProfileSourceSnapshot,
    FuturesDcaProvenanceMigrationMapping,
    append_profile_source_snapshot,
    build_futures_dca_provenance_migration_manifest,
    create_futures_dca_provenance_target,
    evaluate_futures_dca_provenance_manifest,
    load_accepted_profile_source_snapshots,
    validate_futures_dca_provenance_target,
)


class FuturesDcaProvenanceTargetTests(unittest.TestCase):
    def profile(self, revision_id="profile-1"):
        return FuturesDcaProfileRevision(
            revision_id, "BINANCE", "USD_M_PERPETUAL", "BTCUSDT", "USDT", "ISOLATED", "ONE_WAY", 100,
            "0.001", "fee-1", "slippage-1", "rounding-1",
        )

    def snapshot(self, snapshot_id="snapshot-1", revision_id="profile-1", state="ACCEPTED"):
        return FuturesDcaProfileSourceSnapshot(
            snapshot_id, revision_id, "BINANCE_EXCHANGE_INFO", "BTCUSDT", "a" * 64, "schema-1", 100, state
        )

    def setup_target(self, directory):
        path = create_futures_dca_provenance_target(Path(directory) / "target.sqlite")
        append_profile_revision(path, self.profile())
        return path

    def test_new_target_binds_profile_snapshot_and_replays_only_accepted(self):
        with TemporaryDirectory() as directory:
            path = self.setup_target(directory)
            accepted = self.snapshot()
            unknown = self.snapshot("snapshot-2", state="UNKNOWN")

            self.assertEqual(append_profile_source_snapshot(path, accepted), "ACCEPTED")
            self.assertEqual(append_profile_source_snapshot(path, accepted), "DUPLICATE")
            self.assertEqual(append_profile_source_snapshot(path, unknown), "ACCEPTED")
            self.assertEqual(load_accepted_profile_source_snapshots(path), (accepted,))

    def test_conflict_missing_profile_and_second_accepted_snapshot_fail_closed(self):
        with TemporaryDirectory() as directory:
            path = self.setup_target(directory)
            append_profile_source_snapshot(path, self.snapshot())

            conflict = self.snapshot()
            conflict = FuturesDcaProfileSourceSnapshot(
                conflict.source_snapshot_id, conflict.profile_revision_id, conflict.source_kind,
                conflict.source_row_id, "b" * 64, conflict.source_schema_revision,
                conflict.observed_time_us, conflict.source_state,
            )
            with self.assertRaisesRegex(ValueError, "FUTURES_DCA_PROVENANCE_CONFLICT"):
                append_profile_source_snapshot(path, conflict)
            with self.assertRaisesRegex(ValueError, "FUTURES_DCA_PROVENANCE_PROFILE_CONFLICT"):
                append_profile_source_snapshot(path, self.snapshot("snapshot-2"))
            with self.assertRaisesRegex(ValueError, "FUTURES_DCA_PROVENANCE_PROFILE_MISSING"):
                append_profile_source_snapshot(path, self.snapshot("snapshot-3", "missing"))

    def test_insert_failure_rolls_back_snapshot_on_new_target(self):
        with TemporaryDirectory() as directory:
            path = self.setup_target(directory)
            db = sqlite3.connect(path)
            try:
                db.execute(
                    "CREATE TRIGGER reject_snapshot BEFORE INSERT ON profile_source_snapshots "
                    "BEGIN SELECT RAISE(ABORT, 'injected snapshot failure'); END"
                )
            finally:
                db.close()

            with self.assertRaisesRegex(sqlite3.IntegrityError, "injected snapshot failure"):
                append_profile_source_snapshot(path, self.snapshot())
            self.assertEqual(load_accepted_profile_source_snapshots(path), ())

    def test_read_only_validation_returns_ready_without_publishing(self):
        with TemporaryDirectory() as directory:
            path = self.setup_target(directory)
            append_profile_source_snapshot(path, self.snapshot())

            result = validate_futures_dca_provenance_target(path)

            self.assertEqual(
                result,
                type(result)("READY", "READY", (), 1, 1, 1),
            )

    def test_read_only_validation_rejects_unknown_and_missing_profile(self):
        with TemporaryDirectory() as directory:
            path = self.setup_target(directory)
            append_profile_revision(path, self.profile("profile-2"))
            append_profile_source_snapshot(path, self.snapshot(state="UNKNOWN"))
            db = sqlite3.connect(path)
            try:
                db.execute("PRAGMA foreign_keys=OFF")
                db.execute(
                    "INSERT INTO profile_source_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    ("snapshot-missing", "missing", "BINANCE_EXCHANGE_INFO", "BTCUSDT", "b" * 64, "schema-1", 101, "ACCEPTED"),
                )
                db.commit()
            finally:
                db.close()

            result = validate_futures_dca_provenance_target(path)

            self.assertEqual(result.status, "NO_GO")
            self.assertEqual(result.publish_decision, "NO_GO")
            self.assertIn("FUTURES_DCA_PROVENANCE_UNKNOWN", result.issues)
            self.assertIn("FUTURES_DCA_PROVENANCE_PROFILE_MISSING", result.issues)
            self.assertIn("FUTURES_DCA_PROVENANCE_PROFILE_WITHOUT_ACCEPTED_SOURCE", result.issues)

    def mapping(self, payload_hash="a" * 64, target_row_id="snapshot-1"):
        return FuturesDcaProvenanceMigrationMapping(
            "BINANCE_EXCHANGE_INFO", "BTCUSDT", target_row_id, "profile-1", payload_hash, "schema-1", 100
        )

    def test_manifest_is_deterministic_and_matches_target_read_only(self):
        with TemporaryDirectory() as directory:
            path = self.setup_target(directory)
            append_profile_source_snapshot(path, self.snapshot())
            first = build_futures_dca_provenance_migration_manifest((self.mapping(),))
            second = build_futures_dca_provenance_migration_manifest((self.mapping(),))

            self.assertEqual(first, second)
            self.assertEqual(first.status, "READY")
            self.assertEqual(evaluate_futures_dca_provenance_manifest(path, first).status, "READY")

    def test_manifest_rejects_unknown_duplicate_and_target_mismatch(self):
        with TemporaryDirectory() as directory:
            path = self.setup_target(directory)
            append_profile_source_snapshot(path, self.snapshot())
            unknown = self.mapping()
            unknown = FuturesDcaProvenanceMigrationMapping(
                unknown.source_kind, unknown.source_row_id, unknown.target_row_id, unknown.profile_revision_id,
                unknown.payload_hash, unknown.source_schema_revision, unknown.observed_time_us, "UNKNOWN",
            )
            blocked = build_futures_dca_provenance_migration_manifest((unknown, unknown))
            self.assertEqual(blocked.status, "NO_GO")
            self.assertIn("FUTURES_DCA_MIGRATION_UNKNOWN", blocked.issues)
            self.assertIn("FUTURES_DCA_MIGRATION_SOURCE_DUPLICATE", blocked.issues)
            mismatch = build_futures_dca_provenance_migration_manifest((self.mapping("b" * 64),))
            decision = evaluate_futures_dca_provenance_manifest(path, mismatch)
            self.assertEqual(decision.status, "NO_GO")
            self.assertIn("FUTURES_DCA_MIGRATION_MANIFEST_TARGET_MISMATCH", decision.issues)

    def test_empty_manifest_is_no_go_without_writing(self):
        with TemporaryDirectory() as directory:
            path = self.setup_target(directory)
            manifest = build_futures_dca_provenance_migration_manifest(())

            self.assertEqual(manifest.status, "NO_GO")
            self.assertIn("FUTURES_DCA_MIGRATION_NO_MAPPINGS", manifest.issues)
            self.assertEqual(load_accepted_profile_source_snapshots(path), ())


if __name__ == "__main__":
    unittest.main()
