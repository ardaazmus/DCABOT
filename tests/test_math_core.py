import unittest
from fractions import Fraction as F
from decimal import getcontext
from dcabot.domain.numbers import number, text, align
from dcabot.domain.math import (
    Position,
    net_take_profit,
    liquidation_long,
    drawdown,
)


class MathTests(unittest.TestCase):
    def test_notional_and_bad_numeric_inputs(self):
        self.assertEqual(number("100.25") * number("0.04"), F(401, 100))
        for value in (
            True,
            1,
            0.1,
            "NaN",
            "Infinity",
            "1e999999",
            "1_000",
            " 1",
            "9" * 1000,
        ):
            with self.subTest(value=str(value)[:30]), self.assertRaises(ValueError):
                number(value)

    def test_tick_grid_not_decimal_places(self):
        self.assertEqual(align(number("100.13"), number("0.25"), up=False), F(100))
        self.assertEqual(align(number("100.13"), number("0.25"), up=True), F(401, 4))

    def test_partial_exit_preserves_average_and_equity_bridge(self):
        p = Position().buy(F(1), F(100)).buy(F(1), F(90))
        q, g = p.sell(F(1, 2), F(110))
        self.assertEqual(
            (q.qty, q.cost, q.average, g), (F(3, 2), F(285, 2), F(95), F(15, 2))
        )
        self.assertEqual(g + q.unrealized(F(100)), p.unrealized(F(100)) + F(5))
        flat, g2 = q.sell(F(3, 2), F(100))
        self.assertEqual(
            (flat.qty, flat.cost, flat.average, g + g2), (F(0), F(0), None, F(15))
        )

    def test_repeating_cost_allocation_has_no_residual(self):
        p = Position().buy(F(2), F(1)).buy(F(1), F(2))
        gains = F(0)
        for _ in range(3):
            p, g = p.sell(F(1), F(2))
            gains += g
        self.assertEqual((p.cost, gains), (0, 2))

    def test_net_target_and_liquidation_roots(self):
        target = net_take_profit(
            Position(F(2), F(190)), F(19, 100), F(0), F(19, 10), F(1, 1000), F(1, 100)
        )
        self.assertEqual(target, F(1923, 20))
        self.assertEqual(
            F(2) * (target - F(95)) - F(19, 100) - F(1, 1000) * F(2) * target,
            F(19177, 10000),
        )
        self.assertEqual(
            liquidation_long(F(1), F(100), F(10), F(5, 1000)), F(18000, 199)
        )

    def test_peak_drawdown_not_initial_loss(self):
        self.assertEqual(drawdown(F(120), F(100)), F(1, 6))
        self.assertIsNone(drawdown(F(120), F(0)))

    def test_global_decimal_context_does_not_change_economics(self):
        before = getcontext().prec
        try:
            getcontext().prec = 2
            self.assertEqual(number("100.25") * number("0.04"), F(401, 100))
            self.assertEqual(text(F(401, 100)), "4.01")
        finally:
            getcontext().prec = before
