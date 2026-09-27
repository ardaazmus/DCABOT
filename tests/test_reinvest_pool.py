"""Faz 17 H.1 (RG-10): reinvest pool -- fed only by realized deal profit at
closure, never by a loss; `base_initial_equity` stays immutable, only
`effective_initial_equity` grows."""
import unittest
from fractions import Fraction as F

from dcabot.application.reinvest_pool import (
    ReinvestPoolError,
    apply_deal_closed,
    create_pool,
)


class CreatePoolTests(unittest.TestCase):
    def test_starts_with_zero_accumulated(self):
        pool = create_pool(F(1000))
        self.assertEqual(pool.accumulated, F(0))
        self.assertEqual(pool.effective_initial_equity, F(1000))

    def test_non_positive_base_is_rejected(self):
        with self.assertRaises(ReinvestPoolError):
            create_pool(F(0))
        with self.assertRaises(ReinvestPoolError):
            create_pool(F(-10))


class ApplyDealClosedTests(unittest.TestCase):
    def test_profit_contributes_the_configured_percent(self):
        pool = create_pool(F(1000))
        pool = apply_deal_closed(pool, realized_profit=F(100), reinvest_percent=F(1, 2))
        self.assertEqual(pool.accumulated, F(50))
        self.assertEqual(pool.effective_initial_equity, F(1050))

    def test_full_reinvest_percent_adds_the_whole_profit(self):
        pool = create_pool(F(1000))
        pool = apply_deal_closed(pool, realized_profit=F(200), reinvest_percent=F(1))
        self.assertEqual(pool.accumulated, F(200))

    def test_zero_reinvest_percent_adds_nothing(self):
        pool = create_pool(F(1000))
        pool = apply_deal_closed(pool, realized_profit=F(200), reinvest_percent=F(0))
        self.assertEqual(pool.accumulated, F(0))

    def test_loss_never_reduces_the_pool(self):
        pool = create_pool(F(1000))
        pool = apply_deal_closed(pool, realized_profit=F(100), reinvest_percent=F(1))
        pool = apply_deal_closed(pool, realized_profit=F(-500), reinvest_percent=F(1))
        self.assertEqual(pool.accumulated, F(100))

    def test_zero_profit_adds_nothing(self):
        pool = create_pool(F(1000))
        pool = apply_deal_closed(pool, realized_profit=F(0), reinvest_percent=F(1))
        self.assertEqual(pool.accumulated, F(0))

    def test_pool_compounds_across_multiple_deals(self):
        pool = create_pool(F(1000))
        pool = apply_deal_closed(pool, realized_profit=F(100), reinvest_percent=F(1))
        pool = apply_deal_closed(pool, realized_profit=F(50), reinvest_percent=F(1))
        self.assertEqual(pool.accumulated, F(150))
        self.assertEqual(pool.effective_initial_equity, F(1150))

    def test_base_initial_equity_is_never_mutated(self):
        pool = create_pool(F(1000))
        pool = apply_deal_closed(pool, realized_profit=F(9999), reinvest_percent=F(1))
        self.assertEqual(pool.base_initial_equity, F(1000))

    def test_out_of_range_percent_is_rejected(self):
        pool = create_pool(F(1000))
        with self.assertRaises(ReinvestPoolError):
            apply_deal_closed(pool, realized_profit=F(100), reinvest_percent=F(-1))
        with self.assertRaises(ReinvestPoolError):
            apply_deal_closed(pool, realized_profit=F(100), reinvest_percent=F(2))


if __name__ == "__main__":
    unittest.main()
