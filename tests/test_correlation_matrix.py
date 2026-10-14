"""Q2: pairwise correlation matrix -- display coefficients (float, 4dp)
plus exact integer breach verdicts from the tested Faz 17 F.2 core.
No new math here: composition + per-cell fail-closed mapping only."""
import re
import unittest

from dcabot.application.correlation_matrix import correlation_matrix_cells


def _linear(n, start=100.0, step=1.0):
    return [start + i * step for i in range(n)]


def _oscillating(n):
    return [100.0 + (i % 2) for i in range(n)]


class CorrelationMatrixTests(unittest.TestCase):
    KW = {"window": 10, "threshold_numerator": 7, "threshold_denominator": 10, "scale": 10**12}

    def test_identical_series_breach_with_unit_coefficient(self):
        series = {"AAA": _linear(40), "BBB": _linear(40)}
        (cell,) = correlation_matrix_cells(series, **self.KW)
        self.assertEqual((cell.x, cell.y), ("AAA", "BBB"))
        self.assertEqual(cell.verdict, "BREACH")
        self.assertEqual(cell.coefficient, "1.0000")
        self.assertEqual(cell.samples, 40)

    def test_uncorrelated_pair_is_ok_with_small_coefficient(self):
        series = {"AAA": _linear(40), "BBB": _oscillating(40)}
        (cell,) = correlation_matrix_cells(series, **self.KW)
        self.assertEqual(cell.verdict, "OK")
        assert cell.coefficient is not None
        self.assertTrue(re.fullmatch(r"-?\d\.\d{4}", cell.coefficient))
        self.assertLess(abs(float(cell.coefficient)), 0.7)

    def test_short_history_is_insufficient_not_ok(self):
        series = {"AAA": _linear(5), "BBB": _linear(5)}
        (cell,) = correlation_matrix_cells(series, **self.KW)
        self.assertEqual(cell.verdict, "INSUFFICIENT")
        self.assertEqual(cell.detail, "INSUFFICIENT_HISTORY")
        self.assertIsNone(cell.coefficient)
        self.assertEqual(cell.samples, 5)

    def test_flat_series_is_insufficient_precision(self):
        series = {"AAA": [100.0] * 40, "BBB": _linear(40)}
        (cell,) = correlation_matrix_cells(series, **self.KW)
        self.assertEqual(cell.verdict, "INSUFFICIENT")
        self.assertEqual(cell.detail, "INSUFFICIENT_PRECISION")

    def test_only_upper_triangle_pairs_sorted(self):
        series = {"CCC": _linear(40), "AAA": _linear(40), "BBB": _linear(40)}
        cells = correlation_matrix_cells(series, **self.KW)
        self.assertEqual([(c.x, c.y) for c in cells], [("AAA", "BBB"), ("AAA", "CCC"), ("BBB", "CCC")])

    def test_length_mismatch_is_insufficient(self):
        series = {"AAA": _linear(40), "BBB": _linear(30)}
        (cell,) = correlation_matrix_cells(series, **self.KW)
        self.assertEqual(cell.verdict, "INSUFFICIENT")
        self.assertEqual(cell.detail, "INSUFFICIENT_HISTORY")

    def test_invalid_parameters_rejected(self):
        series = {"AAA": _linear(40), "BBB": _linear(40)}
        for bad in (
            {"window": 1},
            {"threshold_denominator": 0},
            {"threshold_numerator": -1},
            {"scale": 0},
        ):
            kwargs = dict(self.KW)
            kwargs.update(bad)
            with self.assertRaises(ValueError, msg=bad):
                correlation_matrix_cells(series, **kwargs)


if __name__ == "__main__":
    unittest.main()
