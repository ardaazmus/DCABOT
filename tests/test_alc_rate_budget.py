"""Faz 17 D.1: Anti-Liquidation Cascade'in KENDİ düşük-frekans rate bütçesi
-- §8.2'nin paylaşımlı Lab bütçesi DEĞİL (ALC ana motorda, sabit ve küçük bir
poll aralığı ister; Lab'ın borsa-yoran, çok-kaynaklı paylaşımlı bütçesinden
kasıtlı olarak ayrı)."""
import unittest

from dcabot.application.alc_rate_budget import AlcPollBudget, AlcRateBudgetError


class AlcPollBudgetTests(unittest.TestCase):
    def test_first_poll_for_a_key_is_always_allowed(self):
        budget = AlcPollBudget(min_interval_us=5_000_000)
        self.assertTrue(budget.allow("binance_futures", "BTCUSDT", now_us=1_000_000))

    def test_poll_before_interval_elapses_is_denied(self):
        budget = AlcPollBudget(min_interval_us=5_000_000)
        budget.allow("binance_futures", "BTCUSDT", now_us=1_000_000)
        self.assertFalse(budget.allow("binance_futures", "BTCUSDT", now_us=3_000_000))

    def test_poll_after_interval_elapses_is_allowed(self):
        budget = AlcPollBudget(min_interval_us=5_000_000)
        budget.allow("binance_futures", "BTCUSDT", now_us=1_000_000)
        self.assertTrue(budget.allow("binance_futures", "BTCUSDT", now_us=6_000_001))

    def test_boundary_exact_interval_is_allowed(self):
        budget = AlcPollBudget(min_interval_us=5_000_000)
        budget.allow("binance_futures", "BTCUSDT", now_us=1_000_000)
        self.assertTrue(budget.allow("binance_futures", "BTCUSDT", now_us=6_000_000))

    def test_denied_poll_does_not_reset_the_window(self):
        budget = AlcPollBudget(min_interval_us=5_000_000)
        budget.allow("binance_futures", "BTCUSDT", now_us=1_000_000)
        self.assertFalse(budget.allow("binance_futures", "BTCUSDT", now_us=3_000_000))
        # Still measured from the original 1_000_000 timestamp, not 3_000_000.
        self.assertFalse(budget.allow("binance_futures", "BTCUSDT", now_us=5_500_000))
        self.assertTrue(budget.allow("binance_futures", "BTCUSDT", now_us=6_000_000))

    def test_different_symbols_have_independent_budgets(self):
        budget = AlcPollBudget(min_interval_us=5_000_000)
        budget.allow("binance_futures", "BTCUSDT", now_us=1_000_000)
        self.assertTrue(budget.allow("binance_futures", "ETHUSDT", now_us=1_000_001))

    def test_non_positive_interval_is_rejected_at_construction(self):
        with self.assertRaises(AlcRateBudgetError):
            AlcPollBudget(min_interval_us=0)
        with self.assertRaises(AlcRateBudgetError):
            AlcPollBudget(min_interval_us=-1)

    def test_backwards_clock_is_rejected_not_silently_allowed(self):
        budget = AlcPollBudget(min_interval_us=5_000_000)
        budget.allow("binance_futures", "BTCUSDT", now_us=10_000_000)
        with self.assertRaises(AlcRateBudgetError):
            budget.allow("binance_futures", "BTCUSDT", now_us=1_000_000)


if __name__ == "__main__":
    unittest.main()
