import sqlite3
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest


class FuturesDcaProvenanceOracleTests(unittest.TestCase):
    def test_accepted_snapshot_replays_and_exact_duplicate_is_idempotent(self):
        with TemporaryDirectory() as directory:
            path = self._initialize(Path(directory) / "provenance.sqlite")
            row = self._row()

            self.assertEqual(self._append(path, row), "ACCEPTED")
            self.assertEqual(self._append(path, row), "DUPLICATE")
            self.assertEqual(self._load(path), (row,))

    def test_same_revision_conflict_and_non_authoritative_state_fail_closed(self):
        with TemporaryDirectory() as directory:
            path = self._initialize(Path(directory) / "provenance.sqlite")
            row = self._row()
            self._append(path, row)

            conflict = (*row[:4], "schema-2", row[5], row[6], row[7])
            with self.assertRaisesRegex(ValueError, "PROVENANCE_CONFLICT"):
                self._append(path, conflict)

            unknown = ("snapshot-2", "profile-2", "BINANCE_EXCHANGE_INFO", "BTCUSDT-2", "hash-2", "schema-1", 101, "UNKNOWN")
            self.assertEqual(self._append(path, unknown), "ACCEPTED")
            self.assertEqual(self._load(path), (row,))

    def test_failure_before_commit_replays_no_partial_snapshot(self):
        with TemporaryDirectory() as directory:
            path = self._initialize(Path(directory) / "provenance.sqlite")
            db = sqlite3.connect(path, isolation_level=None)
            try:
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    "INSERT INTO profile_source_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    self._row(),
                )
                with self.assertRaisesRegex(RuntimeError, "injected provenance failure"):
                    try:
                        raise RuntimeError("injected provenance failure")
                    except RuntimeError:
                        db.execute("ROLLBACK")
                        raise
            finally:
                db.close()
            self.assertEqual(self._load(path), ())

    @staticmethod
    def _row():
        return ("snapshot-1", "profile-1", "BINANCE_EXCHANGE_INFO", "BTCUSDT", "hash-1", "schema-1", 100, "ACCEPTED")

    @staticmethod
    def _initialize(path: Path) -> Path:
        db = sqlite3.connect(path)
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("CREATE TABLE profile_revisions(revision_id TEXT PRIMARY KEY)")
            db.execute(
                "CREATE TABLE profile_source_snapshots("
                "source_snapshot_id TEXT PRIMARY KEY, profile_revision_id TEXT UNIQUE NOT NULL, "
                "source_kind TEXT NOT NULL, source_row_id TEXT NOT NULL, payload_hash TEXT NOT NULL, "
                "source_schema_revision TEXT NOT NULL, observed_time_us INTEGER NOT NULL, "
                "source_state TEXT NOT NULL CHECK(source_state IN ('ACCEPTED','UNKNOWN','QUARANTINED')), "
                "FOREIGN KEY(profile_revision_id) REFERENCES profile_revisions(revision_id))"
            )
            db.execute("INSERT INTO profile_revisions VALUES ('profile-1')")
            db.execute("INSERT INTO profile_revisions VALUES ('profile-2')")
            db.commit()
        finally:
            db.close()
        return path

    @staticmethod
    def _append(path: Path, row):
        db = sqlite3.connect(path, isolation_level=None)
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        try:
            prior = db.execute(
                "SELECT source_snapshot_id, profile_revision_id, source_kind, source_row_id, payload_hash, "
                "source_schema_revision, observed_time_us, source_state FROM profile_source_snapshots WHERE source_snapshot_id=?",
                (row[0],),
            ).fetchone()
            if prior is not None:
                if prior != row:
                    raise ValueError("PROVENANCE_CONFLICT")
                db.execute("COMMIT")
                return "DUPLICATE"
            db.execute("INSERT INTO profile_source_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?)", row)
            db.execute("COMMIT")
            return "ACCEPTED"
        except BaseException:
            db.execute("ROLLBACK")
            raise
        finally:
            db.close()

    @staticmethod
    def _load(path: Path):
        db = sqlite3.connect(path)
        try:
            return tuple(
                db.execute(
                    "SELECT source_snapshot_id, profile_revision_id, source_kind, source_row_id, payload_hash, "
                    "source_schema_revision, observed_time_us, source_state "
                    "FROM profile_source_snapshots WHERE source_state='ACCEPTED' ORDER BY source_snapshot_id"
                ).fetchall()
            )
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
