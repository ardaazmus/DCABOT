"""Faz 17 AA.7a-2: Sharpe ratio over an exact equity curve -- the one
allowlisted bridge into analytics/scores.py's sharpe_ratio (bar-over-bar
returns stay exact Fraction; only the final statistic crosses to float)."""
import unittest

from dcabot.application.equity_curve_scores import bar_returns, equity_curve_sharpe_ratio


class BarReturnsTests(unittest.TestCase):
    def test_computes_exact_percentage_returns(self):
        returns = bar_returns(("100", "110", "99"))
        self.assertEqual(returns, ("0.1", "-0.1"))

    def test_skips_a_zero_prior_bar_rather_than_dividing_by_zero(self):
        # prev=0 has an undefined return and is skipped; only prev=10->20 remains.
        returns = bar_returns(("0", "10", "20"))
        self.assertEqual(returns, ("1",))

    def test_single_point_yields_no_returns(self):
        self.assertEqual(bar_returns(("100",)), ())


class EquityCurveSharpeRatioTests(unittest.TestCase):
    def test_none_for_too_few_points(self):
        self.assertIsNone(equity_curve_sharpe_ratio(("100",)))
        self.assertIsNone(equity_curve_sharpe_ratio(()))

    def test_none_for_zero_volatility(self):
        # Constant equity -> all returns are 0 -> zero variance -> undefined.
        self.assertIsNone(equity_curve_sharpe_ratio(("100", "100", "100", "100")))

    def test_positive_trend_has_a_positive_sharpe(self):
        curve = ("100", "101", "102", "103", "104", "105")
        result = equity_curve_sharpe_ratio(curve)
        self.assertIsNotNone(result)
        self.assertGreater(float(result), 0)

    def test_result_is_a_plain_float_repr_not_exact_text(self):
        curve = ("100", "105", "98", "110", "101")
        result = equity_curve_sharpe_ratio(curve)
        self.assertIsNotNone(result)
        float(result)  # must parse as a plain float


if __name__ == "__main__":
    unittest.main()
