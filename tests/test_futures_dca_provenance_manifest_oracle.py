import hashlib
import json
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
    FuturesDcaProvenanceMigrationManifest,
    assess_futures_dca_provenance_publish_readiness,
    append_profile_source_snapshot,
    build_futures_dca_provenance_migration_manifest,
    create_futures_dca_provenance_target,
    evaluate_futures_dca_provenance_manifest,
)


class FuturesDcaProvenanceManifestOracleTests(unittest.TestCase):
    def test_independent_hash_and_reopen_rows_match_manifest(self):
        with TemporaryDirectory() as directory:
            path = self._setup(Path(directory))
            mapping = self._mapping()
            manifest = build_futures_dca_provenance_migration_manifest((mapping,))

            db = sqlite3.connect(path)
            try:
                row = db.execute(
                    "SELECT source_snapshot_id, profile_revision_id, source_kind, source_row_id, "
                    "payload_hash, source_schema_revision, observed_time_us, source_state "
                    "FROM profile_source_snapshots WHERE source_state='ACCEPTED'"
                ).fetchone()
            finally:
                db.close()
            oracle_mapping = {
                "source_kind": row[2],
                "source_row_id": row[3],
                "target_row_id": row[0],
                "profile_revision_id": row[1],
                "payload_hash": row[4],
                "source_schema_revision": row[5],
                "observed_time_us": row[6],
                "source_state": row[7],
            }
            self.assertEqual(manifest.manifest_hash, self._oracle_hash((oracle_mapping,)))
            self.assertEqual(evaluate_futures_dca_provenance_manifest(path, manifest).status, "READY")

    def test_reopened_target_tamper_is_rejected_by_manifest_comparison(self):
        with TemporaryDirectory() as directory:
            path = self._setup(Path(directory))
            manifest = build_futures_dca_provenance_migration_manifest((self._mapping(),))
            db = sqlite3.connect(path)
            try:
                db.execute("UPDATE profile_source_snapshots SET payload_hash=?", ("b" * 64,))
                db.commit()
            finally:
                db.close()

            decision = evaluate_futures_dca_provenance_manifest(path, manifest)

            self.assertEqual(decision.status, "NO_GO")
            self.assertIn("FUTURES_DCA_MIGRATION_MANIFEST_TARGET_MISMATCH", decision.issues)

    def test_manifest_hash_tamper_is_rejected_without_target_write(self):
        with TemporaryDirectory() as directory:
            path = self._setup(Path(directory))
            manifest = build_futures_dca_provenance_migration_manifest((self._mapping(),))
            tampered = FuturesDcaProvenanceMigrationManifest(
                "0" * 64, manifest.mappings, manifest.status, manifest.issues
            )

            decision = evaluate_futures_dca_provenance_manifest(path, tampered)

            self.assertEqual(decision.status, "NO_GO")
            self.assertIn("FUTURES_DCA_MIGRATION_MANIFEST_HASH_MISMATCH", decision.issues)
            db = sqlite3.connect(path)
            try:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM profile_source_snapshots").fetchone(), (1,))
            finally:
                db.close()

    def test_publish_readiness_requires_human_approval_and_stays_blocked(self):
        with TemporaryDirectory() as directory:
            path = self._setup(Path(directory))
            manifest = build_futures_dca_provenance_migration_manifest((self._mapping(),))

            readiness = assess_futures_dca_provenance_publish_readiness(path, manifest, "PASS", "PASS")

            self.assertEqual(readiness.status, "READY_FOR_REVIEW")
            self.assertEqual(readiness.approval_state, "REQUIRED")
            self.assertEqual(readiness.publish_action, "BLOCKED")

    def test_publish_readiness_rejects_missing_or_failed_independent_oracle(self):
        with TemporaryDirectory() as directory:
            path = self._setup(Path(directory))
            manifest = build_futures_dca_provenance_migration_manifest((self._mapping(),))

            for oracle_status in ("NOT_RUN", "FAIL"):
                readiness = assess_futures_dca_provenance_publish_readiness(path, manifest, oracle_status, "PASS")
                self.assertEqual(readiness.status, "NO_GO")
                self.assertIn(f"FUTURES_DCA_PUBLISH_ORACLE_{oracle_status}", readiness.issues)

    def test_publish_readiness_rejects_previous_no_go_gate(self):
        with TemporaryDirectory() as directory:
            path = self._setup(Path(directory))
            manifest = build_futures_dca_provenance_migration_manifest((self._mapping(),))

            readiness = assess_futures_dca_provenance_publish_readiness(path, manifest, "PASS", "NO_GO")

            self.assertEqual(readiness.status, "NO_GO")
            self.assertIn("FUTURES_DCA_PUBLISH_PRIOR_GATE_NO_GO", readiness.issues)

    @staticmethod
    def _setup(root: Path) -> Path:
        path = create_futures_dca_provenance_target(root / "target.sqlite")
        append_profile_revision(
            path,
            FuturesDcaProfileRevision(
                "profile-1", "BINANCE", "USD_M_PERPETUAL", "BTCUSDT", "USDT", "ISOLATED", "ONE_WAY",
                100, "0.001", "fee-1", "slippage-1", "rounding-1",
            ),
        )
        append_profile_source_snapshot(
            path,
            FuturesDcaProfileSourceSnapshot(
                "snapshot-1", "profile-1", "BINANCE_EXCHANGE_INFO", "BTCUSDT", "a" * 64, "schema-1", 100,
            ),
        )
        return path

    @staticmethod
    def _mapping() -> FuturesDcaProvenanceMigrationMapping:
        return FuturesDcaProvenanceMigrationMapping(
            "BINANCE_EXCHANGE_INFO", "BTCUSDT", "snapshot-1", "profile-1", "a" * 64, "schema-1", 100
        )

    @staticmethod
    def _oracle_hash(mappings: tuple[dict[str, object], ...]) -> str:
        payload = json.dumps(
            list(mappings), ensure_ascii=False, separators=(",", ":"), sort_keys=True
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    unittest.main()
