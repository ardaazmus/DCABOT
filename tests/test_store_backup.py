"""F10.2: consistent sqlite backup + manifest + verify (F36)."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from dcabot.application.store_backup import (
    StoreBackupError,
    backup_sqlite_file,
    list_backup_manifests,
    verify_backup,
)


def _make_db(path):
    db = sqlite3.connect(path)
    db.execute("PRAGMA application_id=12345")
    db.execute("PRAGMA user_version=2")
    db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
    db.execute("INSERT INTO t (v) VALUES ('hello')")
    db.commit()
    db.close()


class StoreBackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.src = self.root / "live.sqlite3"
        _make_db(self.src)
        self.dest = self.root / "backups"

    def tearDown(self):
        self.tmp.cleanup()

    def test_backup_roundtrip_verifies(self):
        manifest = backup_sqlite_file(
            self.src, self.dest, store="live", now_us=1700000000000000
        )
        self.assertEqual(manifest["store"], "live")
        self.assertEqual(manifest["created_us"], 1700000000000000)
        self.assertEqual(len(manifest["sha256"]), 64)
        backup_path = self.dest / manifest["backup_file"]
        self.assertTrue(backup_path.exists())
        self.assertTrue((self.dest / manifest["manifest_file"]).exists())
        verdict = verify_backup(backup_path, manifest)
        self.assertEqual(verdict["verdict"], "VERIFIED")
        self.assertEqual(verdict["application_id"], 12345)
        self.assertEqual(verdict["user_version"], 2)

    def test_manifest_is_stable_json(self):
        manifest = backup_sqlite_file(
            self.src, self.dest, store="live", now_us=1700000000000000
        )
        stored = json.loads((self.dest / manifest["manifest_file"]).read_text(encoding="utf-8"))
        self.assertEqual(stored, manifest)

    def test_list_manifests_sorted(self):
        first = backup_sqlite_file(self.src, self.dest, store="live", now_us=1000)
        second = backup_sqlite_file(self.src, self.dest, store="live", now_us=2000)
        listed = list_backup_manifests(self.dest)
        self.assertEqual([m["backup_file"] for m in listed],
                          [first["backup_file"], second["backup_file"]])

    def test_tampered_backup_detected(self):
        manifest = backup_sqlite_file(
            self.src, self.dest, store="live", now_us=1700000000000000
        )
        backup_path = self.dest / manifest["backup_file"]
        with backup_path.open("r+b") as handle:
            handle.seek(100)
            handle.write(b"XX")
        verdict = verify_backup(backup_path, manifest)
        self.assertEqual(verdict["verdict"], "CORRUPT")

    def test_missing_source_rejected(self):
        with self.assertRaises(StoreBackupError) as ctx:
            backup_sqlite_file(self.root / "ghost.db", self.dest, store="x", now_us=1)
        self.assertEqual(ctx.exception.code, "BACKUP_SOURCE_MISSING")

    def test_non_sqlite_source_rejected(self):
        junk = self.root / "junk.db"
        junk.write_text("not a database", encoding="utf-8")
        with self.assertRaises(StoreBackupError) as ctx:
            backup_sqlite_file(junk, self.dest, store="x", now_us=1)
        self.assertEqual(ctx.exception.code, "BACKUP_SOURCE_INVALID")

    def test_bad_store_name_rejected(self):
        with self.assertRaises(StoreBackupError) as ctx:
            backup_sqlite_file(self.src, self.dest, store="../evil", now_us=1)
        self.assertEqual(ctx.exception.code, "BACKUP_STORE_INVALID")

    def test_verify_wrong_manifest_rejected(self):
        manifest = backup_sqlite_file(
            self.src, self.dest, store="live", now_us=1700000000000000
        )
        other = backup_sqlite_file(
            self.src, self.dest, store="live", now_us=1700000000000001
        )
        with self.assertRaises(StoreBackupError) as ctx:
            verify_backup(self.dest / manifest["backup_file"], other)
        self.assertEqual(ctx.exception.code, "BACKUP_MANIFEST_MISMATCH")


if __name__ == "__main__":
    unittest.main()
