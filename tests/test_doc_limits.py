"""Ajan bağlamına giren belgelerin bayt limitini doğrular."""

import tempfile
import unittest
from pathlib import Path

from check_workspace import DOC_LIMITS, ROOT, check_doc_sizes


class DocLimitTests(unittest.TestCase):
    def test_repo_docs_are_within_limits(self):
        self.assertEqual(check_doc_sizes(ROOT), [])

    def test_oversized_doc_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "STATE.md").write_text("x" * (DOC_LIMITS["STATE.md"] + 1), encoding="utf-8")
            (root / "TASK.md").write_text("ok", encoding="utf-8")
            errors = check_doc_sizes(root)
            self.assertEqual(len(errors), 1)
            self.assertIn("STATE.md", errors[0])

    def test_limit_is_measured_in_bytes_not_characters(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # "ş" UTF-8'de 2 bayttır: karakter sayısı limit altında, bayt sayısı üstünde.
            chars = DOC_LIMITS["CLAUDE.md"] // 2 + 1
            (root / "CLAUDE.md").write_text("ş" * chars, encoding="utf-8")
            self.assertEqual(len(check_doc_sizes(root)), 1)

    def test_missing_files_are_not_a_size_error(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(check_doc_sizes(Path(td)), [])


if __name__ == "__main__":
    unittest.main()
