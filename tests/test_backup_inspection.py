"""Source inspection is explicit, non-executing and leaves bytes unchanged."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from inspect_backup import inspect


class BackupInspectionTests(unittest.TestCase):
    def test_selected_source_is_hashed_without_execution_or_modification(self):
        with tempfile.TemporaryDirectory() as td:
            backup = Path(td)
            source = backup / "src/candidate.py"
            source.parent.mkdir()
            content = b"raise RuntimeError('must never execute')\n"
            source.write_bytes(content)
            result = inspect("src/candidate.py", backup)
            self.assertEqual(result["sha256"], hashlib.sha256(content).hexdigest())
            self.assertEqual(result["status"], "CANDIDATE_ONLY")
            self.assertEqual(source.read_bytes(), content)

    def test_paths_outside_selected_source_types_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            for path in (
                "../src/x.py",
                "/tmp/x.py",
                "",
                ".env",
                "session.db",
                "src/session.db",
                ".git/config",
                "tools/setup.py",
            ):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    inspect(path, Path(td))

    def test_missing_candidate_is_not_reported_as_verified(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                inspect("src/missing.py", Path(td))
