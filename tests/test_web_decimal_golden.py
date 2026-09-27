"""The web's display rounding (web/src/lib/decimal.ts) is pinned to the
backend's `text()` through a shared golden file; this side proves the file
still matches the backend, the web side proves the formatter matches the file."""
import json
import unittest
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

from dcabot.domain.numbers import text

GOLDEN = Path(__file__).resolve().parents[1] / "web" / "tests" / "fixtures" / "decimal" / "half_even_golden.json"


class WebDecimalGoldenTests(unittest.TestCase):
    def test_golden_vectors_match_backend_text(self):
        cases = json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]
        self.assertGreaterEqual(len(cases), 1000)
        for case in cases:
            self.assertEqual(
                text(Fraction(Decimal(case["value"])), case["places"]),
                case["expected"],
                case,
            )


if __name__ == "__main__":
    unittest.main()
