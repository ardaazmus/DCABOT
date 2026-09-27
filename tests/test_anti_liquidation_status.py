"""Faz 17 D.1: Anti-Liquidation Cascade -- fail-closed durum makinesi.

RG-02 (2026-09-21/22) bağlayıcı düzeltmeler: `/fapi/v3/positionRisk` yanıtında
`marginRatio` alanı YOK; oran `totalMaintMargin / totalMarginBalance`'tan
(`/fapi/v3/account`) exact türetilir. `liquidationPrice == "0"` borsanın
"bu alan anlamsız" işaretidir, ASLA "risk yok" değildir. Likidasyon fiyatını
DCABOT kendi hesaplamaz (LCR-12) -- bu modül yalnız venue'nin raporladığı
ham değerleri normalize eder ve tazelik/tutarlılık durumunu değerlendirir.
"""
import unittest

from dcabot.application.anti_liquidation_status import (
    AntiLiquidationStatusError,
    LiquidationStatus,
    derive_margin_ratio,
    evaluate_liquidation_status,
    is_fast_price_move,
    select_position_row,
)
from dcabot.data_adapters.binance_futures_testnet_position_risk import (
    FuturesAccountMargin,
    FuturesPositionRisk,
)


def _position(**overrides) -> FuturesPositionRisk:
    base = dict(
        symbol="BTCUSDT",
        position_amt="1.000",
        entry_price="60000",
        mark_price="60500",
        liquidation_price="54000",
        leverage="5",
        unrealized_profit="500",
        position_side="LONG",
        update_time_ms=1_700_000_000_000,
    )
    base.update(overrides)
    return FuturesPositionRisk(**base)


def _margin(**overrides) -> FuturesAccountMargin:
    base = dict(
        total_maint_margin="120",
        total_margin_balance="10000",
        update_time_ms=1_700_000_000_000,
    )
    base.update(overrides)
    return FuturesAccountMargin(**base)


class DeriveMarginRatioTests(unittest.TestCase):
    def test_exact_ratio_from_maint_margin_and_balance(self):
        self.assertEqual(derive_margin_ratio("120", "10000"), "0.012")

    def test_zero_balance_is_rejected(self):
        with self.assertRaises(AntiLiquidationStatusError) as ctx:
            derive_margin_ratio("120", "0")
        self.assertEqual(ctx.exception.code, "ALC_MARGIN_BALANCE_NONPOSITIVE")

    def test_negative_balance_is_rejected(self):
        with self.assertRaises(AntiLiquidationStatusError):
            derive_margin_ratio("120", "-5")

    def test_non_decimal_text_is_rejected(self):
        with self.assertRaises(AntiLiquidationStatusError):
            derive_margin_ratio("abc", "10000")


class FastPriceMoveTests(unittest.TestCase):
    def test_slow_move_is_not_flagged(self):
        # 100 price units over 10 seconds = 10/s, threshold 50/s.
        self.assertFalse(
            is_fast_price_move("60000", 0, "60100", 10_000_000, threshold_per_second="50")
        )

    def test_fast_move_is_flagged(self):
        # 1000 price units over 1 second = 1000/s, threshold 50/s.
        self.assertTrue(
            is_fast_price_move("60000", 0, "61000", 1_000_000, threshold_per_second="50")
        )

    def test_boundary_rate_equal_to_threshold_is_flagged(self):
        self.assertTrue(
            is_fast_price_move("60000", 0, "60500", 1_000_000, threshold_per_second="500")
        )

    def test_non_positive_or_zero_elapsed_time_fails_closed_true(self):
        self.assertTrue(
            is_fast_price_move("60000", 1_000_000, "60100", 1_000_000, threshold_per_second="50")
        )
        self.assertTrue(
            is_fast_price_move("60000", 1_000_000, "60100", 500_000, threshold_per_second="50")
        )


class EvaluateLiquidationStatusTests(unittest.TestCase):
    def test_simulated_only_when_venue_does_not_support_position_risk(self):
        status = evaluate_liquidation_status(
            venue_supports_position_risk=False,
            position_risk=None,
            account_margin=None,
            observed_at_us=1_000_000,
            now_us=1_000_000,
            stale_after_us=5_000_000,
        )
        self.assertEqual(status.state, "SIMULATED_ONLY")
        self.assertIsNone(status.liquidation_price)
        self.assertIsNone(status.margin_ratio)

    def test_no_position_when_position_amt_is_zero(self):
        status = evaluate_liquidation_status(
            venue_supports_position_risk=True,
            position_risk=_position(position_amt="0"),
            account_margin=_margin(),
            observed_at_us=1_000_000,
            now_us=1_000_000,
            stale_after_us=5_000_000,
        )
        self.assertEqual(status.state, "NO_POSITION")

    def test_no_position_when_position_risk_is_none(self):
        status = evaluate_liquidation_status(
            venue_supports_position_risk=True,
            position_risk=None,
            account_margin=_margin(),
            observed_at_us=1_000_000,
            now_us=1_000_000,
            stale_after_us=5_000_000,
        )
        self.assertEqual(status.state, "NO_POSITION")

    def test_data_ok_with_fresh_consistent_data_and_no_fast_move(self):
        status = evaluate_liquidation_status(
            venue_supports_position_risk=True,
            position_risk=_position(),
            account_margin=_margin(),
            observed_at_us=1_000_000,
            now_us=1_100_000,
            stale_after_us=5_000_000,
        )
        self.assertEqual(status.state, "DATA_OK")
        self.assertEqual(status.liquidation_price, "54000")
        self.assertEqual(status.margin_ratio, "0.012")

    def test_liquidation_price_zero_is_meaningless_not_no_risk(self):
        status = evaluate_liquidation_status(
            venue_supports_position_risk=True,
            position_risk=_position(liquidation_price="0"),
            account_margin=_margin(),
            observed_at_us=1_000_000,
            now_us=1_100_000,
            stale_after_us=5_000_000,
        )
        self.assertEqual(status.state, "DATA_OK")
        self.assertIsNone(status.liquidation_price)
        self.assertEqual(status.reason, "LIQUIDATION_PRICE_NOT_MEANINGFUL")

    def test_stale_when_poll_age_exceeds_threshold(self):
        status = evaluate_liquidation_status(
            venue_supports_position_risk=True,
            position_risk=_position(),
            account_margin=_margin(),
            observed_at_us=1_000_000,
            now_us=10_000_000,
            stale_after_us=5_000_000,
        )
        self.assertEqual(status.state, "STALE")
        # Last-known values are still surfaced, just flagged stale.
        self.assertEqual(status.liquidation_price, "54000")

    def test_inconsistent_when_margin_balance_nonpositive(self):
        status = evaluate_liquidation_status(
            venue_supports_position_risk=True,
            position_risk=_position(),
            account_margin=_margin(total_margin_balance="0"),
            observed_at_us=1_000_000,
            now_us=1_100_000,
            stale_after_us=5_000_000,
        )
        self.assertEqual(status.state, "INCONSISTENT")
        self.assertIsNone(status.margin_ratio)

    def test_inconsistent_when_account_margin_missing(self):
        status = evaluate_liquidation_status(
            venue_supports_position_risk=True,
            position_risk=_position(),
            account_margin=None,
            observed_at_us=1_000_000,
            now_us=1_100_000,
            stale_after_us=5_000_000,
        )
        self.assertEqual(status.state, "INCONSISTENT")

    def test_watch_when_fast_price_move_flagged(self):
        status = evaluate_liquidation_status(
            venue_supports_position_risk=True,
            position_risk=_position(),
            account_margin=_margin(),
            observed_at_us=1_000_000,
            now_us=1_100_000,
            stale_after_us=5_000_000,
            previous_mark_price="60000",
            previous_observed_at_us=0,
            fast_move_threshold_per_second="1",
        )
        self.assertEqual(status.state, "WATCH")
        self.assertTrue(status.is_fast_move)
        # Fast-move degrades confidence but the last reported numbers still show.
        self.assertEqual(status.liquidation_price, "54000")

    def test_inconsistent_takes_priority_over_stale(self):
        status = evaluate_liquidation_status(
            venue_supports_position_risk=True,
            position_risk=_position(),
            account_margin=_margin(total_margin_balance="0"),
            observed_at_us=1_000_000,
            now_us=10_000_000,
            stale_after_us=5_000_000,
        )
        self.assertEqual(status.state, "INCONSISTENT")


class SelectPositionRowTests(unittest.TestCase):
    """D.1-followup: fapi `positionRisk` sembol başına satır listesini
    `evaluate_liquidation_status`'un tek-satır girdisine indirger."""

    def test_empty_tuple_returns_none(self):
        self.assertIsNone(select_position_row(()))

    def test_all_zero_rows_return_none(self):
        rows = (_position(position_amt="0"), _position(position_amt="0.000"))
        self.assertIsNone(select_position_row(rows))

    def test_negative_zero_is_treated_as_zero(self):
        rows = (_position(position_amt="-0"), _position(position_amt="-0.00"))
        self.assertIsNone(select_position_row(rows))

    def test_single_nonzero_row_is_returned(self):
        zero = _position(position_amt="0")
        nonzero = _position(position_amt="1.5", position_side="LONG")
        self.assertEqual(select_position_row((zero, nonzero)), nonzero)

    def test_negative_position_amt_is_nonzero_and_returned(self):
        row = _position(position_amt="-1.5", position_side="SHORT")
        self.assertEqual(select_position_row((row,)), row)

    def test_two_nonzero_rows_hedge_mode_is_rejected(self):
        long_leg = _position(position_amt="1.0", position_side="LONG")
        short_leg = _position(position_amt="-1.0", position_side="SHORT")
        with self.assertRaises(AntiLiquidationStatusError) as ctx:
            select_position_row((long_leg, short_leg))
        self.assertEqual(ctx.exception.code, "ALC_MULTI_POSITION_UNSUPPORTED")


if __name__ == "__main__":
    unittest.main()
