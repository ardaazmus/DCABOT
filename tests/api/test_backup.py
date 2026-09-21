"""F10.2: backup admin API (F36)."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from dcabot.server.api import (
    _backup_list,
    _backup_take,
    _backup_verify,
    _validate_backup_take_payload,
    _validate_backup_verify_payload,
)


def _make_db(path):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    db.commit()
    db.close()


class BackupApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.src = self.root / "live.sqlite3"
        _make_db(self.src)
        self.dest = self.root / "backups"
        self.stores = {"live": self.src}

    def tearDown(self):
        self.tmp.cleanup()

    def test_take_list_verify_roundtrip(self):
        validated, fields = _validate_backup_take_payload({"store": "live"})
        self.assertEqual(fields, {})
        taken = _backup_take(self.stores, self.dest, validated, now_us=1000)
        self.assertEqual(taken["manifest"]["store"], "live")
        listed = _backup_list(self.dest)
        self.assertEqual(len(listed["backups"]), 1)
        vvalidated, vfields = _validate_backup_verify_payload(
            {"backup_file": taken["manifest"]["backup_file"]}
        )
        self.assertEqual(vfields, {})
        verdict = _backup_verify(self.dest, vvalidated)
        self.assertEqual(verdict["verdict"], "VERIFIED")

    def test_unknown_store_rejected(self):
        validated, fields = _validate_backup_take_payload({"store": "ghost"})
        self.assertEqual(fields, {})
        with self.assertRaises(ValueError):
            _backup_take(self.stores, self.dest, validated, now_us=1000)

    def test_unknown_backup_file_rejected(self):
        with self.assertRaises(ValueError):
            _backup_verify(self.dest, {"backup_file": "ghost-1.sqlite3"})

    def test_traversal_backup_file_rejected(self):
        validated, fields = _validate_backup_verify_payload({"backup_file": "../x.sqlite3"})
        self.assertIsNone(validated)
        self.assertIn("backup_file", fields)

    def test_empty_store_is_field_error(self):
        validated, fields = _validate_backup_take_payload({"store": ""})
        self.assertIsNone(validated)
        self.assertIn("store", fields)


if __name__ == "__main__":
    unittest.main()
