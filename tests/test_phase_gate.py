"""Tests for tools/phase_gate.py helpers (the gate itself must be trustworthy)."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import phase_gate


class NoRawColorsTests(unittest.TestCase):
    def test_clean_css_passes(self):
        css = (
            ":root { --color-text: #000000; }\n"
            "/* === TOKEN BLOCK END === */\n"
            ".a { color: var(--color-text); background: transparent; }\n"
        )
        path = ROOT / "frontend/src/styles.css"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text("/* x */\n" + css, encoding="utf-8")
            self.assertEqual(
                phase_gate.check_no_raw_colors("frontend/src/styles.css"), []
            )
        finally:
            path.write_text(original, encoding="utf-8")

    def test_hex_outside_block_fails(self):
        css = "/* === TOKEN BLOCK END === */\n.a { color: #ff0000; }\n"
        path = ROOT / "frontend/src/styles.css"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(css, encoding="utf-8")
            errors = phase_gate.check_no_raw_colors("frontend/src/styles.css")
            self.assertEqual(len(errors), 1)
            self.assertIn("#ff0000", errors[0])
        finally:
            path.write_text(original, encoding="utf-8")

    def test_missing_marker_fails(self):
        path = ROOT / "frontend/src/styles.css"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(".a { color: red; }\n", encoding="utf-8")
            errors = phase_gate.check_no_raw_colors("frontend/src/styles.css")
            self.assertEqual(len(errors), 1)
            self.assertIn("marker", errors[0])
        finally:
            path.write_text(original, encoding="utf-8")

    def test_undefined_token_fails(self):
        css = (
            "/* === TOKEN BLOCK END === */\n"
            ".a { color: var(--color-nope); }\n"
        )
        path = ROOT / "frontend/src/styles.css"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(":root { --color-ok: red; }\n" + css, encoding="utf-8")
            errors = phase_gate.check_no_raw_colors("frontend/src/styles.css")
            self.assertEqual(len(errors), 1)
            self.assertIn("--color-nope", errors[0])
        finally:
            path.write_text(original, encoding="utf-8")

    def test_real_stylesheet_passes(self):
        self.assertEqual(
            phase_gate.check_no_raw_colors("frontend/src/styles.css"), []
        )


class EvidenceTests(unittest.TestCase):
    def test_missing_evidence_fails(self):
        errors = phase_gate.check_evidence("evidence/NOPE/SONUC.md")
        self.assertTrue(any("Missing" in e for e in errors))

    def test_evidence_without_counts_fails(self):
        path = ROOT / "evidence/F11/SONUC.md"
        existed = path.is_file()
        original = path.read_text(encoding="utf-8") if existed else ""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("done, trust me\n", encoding="utf-8")
            errors = phase_gate.check_evidence("evidence/F11/SONUC.md")
            self.assertTrue(any("N/M PASS" in e for e in errors))
        finally:
            if existed:
                path.write_text(original, encoding="utf-8")
            elif path.is_file():
                path.unlink()

    def test_unknown_phase_fails(self):
        errors = phase_gate.gate("NOPE")
        self.assertEqual(len(errors), 1)
        self.assertIn("Unknown phase", errors[0])


if __name__ == "__main__":
    unittest.main()
