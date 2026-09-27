"""Faz 17 G.1-motor (RG-06, konu 2/5 entegrasyonu): CROSS margin mode
composes D.1's account margin-ratio status with F.2's correlation gate
before a new deal is admitted. ISOLATED is untouched (no-op)."""
import unittest

from dcabot.application.anti_liquidation_status import LiquidationStatus
from dcabot.application.margin_mode_cross_admission import (
    MarginModeCrossAdmissionError,
    evaluate_cross_admission,
)


def _status(state: str) -> LiquidationStatus:
    return LiquidationStatus(
        state=state,
        liquidation_price=None,
        margin_ratio="0.1",
        is_fast_move=False,
        reason=None,
        observed_at_us=1,
    )


class IsolatedIsNoOpTests(unittest.TestCase):
    def test_isolated_never_raises_regardless_of_inputs(self):
        evaluate_cross_admission(
            margin_mode="ISOLATED",
            liquidation_status=None,
            correlation_decision="DENY",
            correlation_reason="CORRELATION_BREACH",
        )  # must not raise


class CrossRequiresReliableAccountStatusTests(unittest.TestCase):
    def test_missing_liquidation_status_denies(self):
        with self.assertRaises(MarginModeCrossAdmissionError) as ctx:
            evaluate_cross_admission(
                margin_mode="CROSS",
                liquidation_status=None,
                correlation_decision="ALLOW",
                correlation_reason="OK",
            )
        self.assertEqual(ctx.exception.code, "MARGIN_MODE_CROSS_ACCOUNT_STATUS_UNRELIABLE")

    def test_inconsistent_status_denies(self):
        with self.assertRaises(MarginModeCrossAdmissionError) as ctx:
            evaluate_cross_admission(
                margin_mode="CROSS",
                liquidation_status=_status("INCONSISTENT"),
                correlation_decision="ALLOW",
                correlation_reason="OK",
            )
        self.assertEqual(ctx.exception.code, "MARGIN_MODE_CROSS_ACCOUNT_STATUS_UNRELIABLE")

    def test_stale_status_denies(self):
        with self.assertRaises(MarginModeCrossAdmissionError):
            evaluate_cross_admission(
                margin_mode="CROSS",
                liquidation_status=_status("STALE"),
                correlation_decision="ALLOW",
                correlation_reason="OK",
            )

    def test_data_ok_status_passes_this_check(self):
        evaluate_cross_admission(
            margin_mode="CROSS",
            liquidation_status=_status("DATA_OK"),
            correlation_decision="ALLOW",
            correlation_reason="OK",
        )  # must not raise

    def test_no_position_status_passes_this_check(self):
        evaluate_cross_admission(
            margin_mode="CROSS",
            liquidation_status=_status("NO_POSITION"),
            correlation_decision="ALLOW",
            correlation_reason="OK",
        )  # must not raise


class CrossRequiresCorrelationAllowTests(unittest.TestCase):
    def test_correlation_deny_denies_the_deal(self):
        with self.assertRaises(MarginModeCrossAdmissionError) as ctx:
            evaluate_cross_admission(
                margin_mode="CROSS",
                liquidation_status=_status("DATA_OK"),
                correlation_decision="DENY",
                correlation_reason="CORRELATION_BREACH",
            )
        self.assertEqual(ctx.exception.code, "MARGIN_MODE_CROSS_CORRELATION_DENY")

    def test_account_status_is_checked_before_correlation(self):
        # Both would fail; the account-status reason must surface first
        # (matches evaluate_cross_admission's declared check order).
        with self.assertRaises(MarginModeCrossAdmissionError) as ctx:
            evaluate_cross_admission(
                margin_mode="CROSS",
                liquidation_status=None,
                correlation_decision="DENY",
                correlation_reason="CORRELATION_BREACH",
            )
        self.assertEqual(ctx.exception.code, "MARGIN_MODE_CROSS_ACCOUNT_STATUS_UNRELIABLE")


if __name__ == "__main__":
    unittest.main()
