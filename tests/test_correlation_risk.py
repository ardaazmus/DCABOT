"""Faz 17 F.2: integer-only correlation breach kernel (t^2*Bx*By <= A^2,
sqrt-free) + multi-window/floor evaluation + account_reservation admission
gate. Float-analytics (log-return covariance) is a DANÇIŞMAN only -- the
decision boundary itself is integer arithmetic."""
import unittest

from dcabot.application.account_reservation import (
    AccountCapacity,
    project_reservation,
)
from dcabot.application.correlation_risk import (
    CorrelationRiskError,
    correlation_admission_gate,
    evaluate_correlation_gate,
    is_correlation_breach,
    scale_to_integer,
)
from dcabot.application.shared_account_identity import new_shared_account_identity


class ScaleToIntegerTests(unittest.TestCase):
    def test_scales_and_rounds_deterministically(self):
        self.assertEqual(scale_to_integer(1.23456, scale=1000), 1235)

    def test_negative_values_round_correctly(self):
        self.assertEqual(scale_to_integer(-0.005, scale=1000), -5)


class IsCorrelationBreachTests(unittest.TestCase):
    def test_high_covariance_relative_to_variances_breaches(self):
        # corr ~= cov/sqrt(varx*vary); here cov=90, varx=vary=100 -> corr=0.9
        # threshold 0.8 -> should breach.
        self.assertTrue(
            is_correlation_breach(
                covariance_scaled=90, variance_x_scaled=100, variance_y_scaled=100,
                threshold_numerator=8, threshold_denominator=10,
            )
        )

    def test_low_covariance_does_not_breach(self):
        self.assertFalse(
            is_correlation_breach(
                covariance_scaled=10, variance_x_scaled=100, variance_y_scaled=100,
                threshold_numerator=8, threshold_denominator=10,
            )
        )

    def test_sign_of_covariance_does_not_matter(self):
        self.assertTrue(
            is_correlation_breach(
                covariance_scaled=-90, variance_x_scaled=100, variance_y_scaled=100,
                threshold_numerator=8, threshold_denominator=10,
            )
        )

    def test_boundary_is_inclusive(self):
        # corr exactly 0.8: cov=80, varx=vary=100 -> cov^2=6400, t^2*Bx*By=0.64*10000=6400
        self.assertTrue(
            is_correlation_breach(
                covariance_scaled=80, variance_x_scaled=100, variance_y_scaled=100,
                threshold_numerator=8, threshold_denominator=10,
            )
        )

    def test_rejects_negative_variance(self):
        with self.assertRaises(CorrelationRiskError):
            is_correlation_breach(
                covariance_scaled=1, variance_x_scaled=-1, variance_y_scaled=1,
                threshold_numerator=8, threshold_denominator=10,
            )


class EvaluateCorrelationGateTests(unittest.TestCase):
    def _trending_together(self, n, start=100.0, step=1.0):
        return [start + i * step for i in range(n)]

    def test_insufficient_history_in_floor_window_denies(self):
        prices_x = self._trending_together(5)
        prices_y = self._trending_together(5)
        result = evaluate_correlation_gate(
            prices_x, prices_y, windows=(10, 20), threshold_numerator=8,
            threshold_denominator=10, scale=1_000_000,
        )
        self.assertEqual(result.decision, "DENY")
        self.assertEqual(result.reason, "INSUFFICIENT_HISTORY")

    def test_highly_correlated_series_deny_with_low_threshold(self):
        prices_x = self._trending_together(40, step=1.0)
        prices_y = self._trending_together(40, step=1.0)
        result = evaluate_correlation_gate(
            prices_x, prices_y, windows=(10, 20), threshold_numerator=1,
            threshold_denominator=100, scale=10**12,
        )
        self.assertEqual(result.decision, "DENY")
        self.assertEqual(result.reason, "CORRELATION_BREACH")

    def test_uncorrelated_series_allow_with_high_threshold(self):
        prices_x = self._trending_together(42, step=1.0)
        prices_y = [100.0, 99.0, 101.0, 98.5, 102.0, 97.0] * 7
        # A large scale keeps the tiny log-return variances of a smooth,
        # linear price ramp from rounding to zero (see the dedicated
        # underflow test below for what happens when scale is too coarse).
        result = evaluate_correlation_gate(
            prices_x, prices_y, windows=(10, 20), threshold_numerator=99,
            threshold_denominator=100, scale=10**12,
        )
        self.assertEqual(result.decision, "ALLOW")

    def test_too_coarse_a_scale_denies_as_insufficient_precision(self):
        # Same series as the ALLOW case above, but scale=1 is far too coarse
        # for these tiny log-return variances -- they round to zero, which
        # must fail closed (DENY), never silently pass or silently breach.
        prices_x = self._trending_together(42, step=1.0)
        prices_y = [100.0, 99.0, 101.0, 98.5, 102.0, 97.0] * 7
        result = evaluate_correlation_gate(
            prices_x, prices_y, windows=(10, 20), threshold_numerator=99,
            threshold_denominator=100, scale=1,
        )
        self.assertEqual(result.decision, "DENY")
        self.assertEqual(result.reason, "INSUFFICIENT_PRECISION")

    def test_mismatched_price_lengths_rejected(self):
        with self.assertRaises(CorrelationRiskError):
            evaluate_correlation_gate(
                [1.0] * 20, [1.0] * 10, windows=(5,), threshold_numerator=8,
                threshold_denominator=10, scale=1000,
            )


class CorrelationAdmissionGateTests(unittest.TestCase):
    def _capacity(self):
        return AccountCapacity(account_id="acct-1", asset="USDT", amount="1000", version=0)

    def _owner(self):
        return new_shared_account_identity("acct-1", "dca", "ONE_WAY", "deal-1", None)

    def test_correlation_breach_denies_before_touching_reservation_capacity(self):
        prices_x = [100.0 + i for i in range(40)]
        prices_y = [100.0 + i for i in range(40)]
        with self.assertRaises(CorrelationRiskError) as ctx:
            correlation_admission_gate(
                capacity=self._capacity(),
                active_reservations=(),
                reservation_id="res-1",
                amount="50",
                expected_version=0,
                owner=self._owner(),
                prices_x=prices_x,
                prices_y=prices_y,
                windows=(10, 20),
                threshold_numerator=1,
                threshold_denominator=100,
                scale=10**12,
            )
        self.assertEqual(ctx.exception.code, "CORRELATION_BREACH")

    def test_allowed_correlation_still_runs_the_real_capacity_projection(self):
        prices_x = [100.0 + i for i in range(42)]
        prices_y = [100.0, 99.0, 101.0, 98.5, 102.0, 97.0] * 7
        projection = correlation_admission_gate(
            capacity=self._capacity(),
            active_reservations=(),
            reservation_id="res-1",
            amount="50",
            expected_version=0,
            owner=self._owner(),
            prices_x=prices_x,
            prices_y=prices_y,
            windows=(10, 20),
            threshold_numerator=99,
            threshold_denominator=100,
            scale=10**12,
        )
        self.assertEqual(projection.requested, "50")
        self.assertEqual(projection.available_after, "950")


if __name__ == "__main__":
    unittest.main()
