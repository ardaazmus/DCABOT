import unittest
from fractions import Fraction as F

from dcabot.domain.math import (
    Direction,
    build_plan,
    signed_pnl,
    directional_take_profit,
    directional_stop_loss,
    directional_safety_price,
    is_safety_triggered,
    is_take_profit_triggered,
)


class DirectionalMathTests(unittest.TestCase):
    """Faz 17.7 — Short/Bidirectional yön desteği, matematik çekirdeği.
    Vektörler üç bağımsız araştırma raporunun (2026-09-21) TV-1..TV-8 ve
    değişmezler (invariant) bölümlerinden alınmıştır; evidence/F17.7/SONUC.md.
    """

    # --- PnL ---

    def test_long_pnl_positive_on_price_rise(self):
        self.assertEqual(signed_pnl(Direction.LONG, F(3), F(100), F(110)), F(30))

    def test_short_pnl_positive_on_price_fall(self):
        self.assertEqual(signed_pnl(Direction.SHORT, F(3), F(100), F(90)), F(30))

    def test_pnl_symmetry_under_mirrored_price_move(self):
        long_pnl = signed_pnl(Direction.LONG, F(1), F(100), F(90))
        short_pnl = signed_pnl(Direction.SHORT, F(1), F(100), F(110))
        self.assertEqual(long_pnl, short_pnl)
        self.assertEqual(long_pnl, F(-10))

    def test_pnl_rejects_non_positive_inputs(self):
        for qty, entry, exit_price in ((F(0), F(1), F(1)), (F(1), F(0), F(1)), (F(1), F(1), F(0))):
            with self.assertRaises(ValueError):
                signed_pnl(Direction.LONG, qty, entry, exit_price)

    # --- Take-profit / stop-loss ordering ---

    def test_long_tp_above_and_sl_below_average(self):
        average = F(100)
        tp = directional_take_profit(Direction.LONG, average, F(1, 10))
        sl = directional_stop_loss(Direction.LONG, average, F(1, 20))
        self.assertTrue(sl < average < tp)
        self.assertEqual((sl, tp), (F(95), F(110)))

    def test_short_tp_below_and_sl_above_average(self):
        average = F(100)
        tp = directional_take_profit(Direction.SHORT, average, F(1, 10))
        sl = directional_stop_loss(Direction.SHORT, average, F(1, 20))
        self.assertTrue(tp < average < sl)
        self.assertEqual((tp, sl), (F(90), F(105)))

    def test_tp_rate_of_one_or_more_is_rejected(self):
        with self.assertRaises(ValueError):
            directional_take_profit(Direction.LONG, F(100), F(1))

    # --- Safety-order ladder ---

    def test_long_and_short_ladders_are_mirror_images(self):
        anchor, tick = F(100), F(1, 100)
        deviations = [F(2, 100), F(5, 100), F(19, 200)]  # 2%, 5%, 9.5%
        long_prices = [directional_safety_price(Direction.LONG, anchor, d, tick) for d in deviations]
        short_prices = [directional_safety_price(Direction.SHORT, anchor, d, tick) for d in deviations]
        self.assertEqual(long_prices, [F(98), F(95), F(1810, 20)])
        self.assertEqual(short_prices, [F(102), F(105), F(2190, 20)])
        # Long ladder strictly descends; short ladder strictly ascends.
        self.assertEqual(long_prices, sorted(long_prices, reverse=True))
        self.assertEqual(short_prices, sorted(short_prices))

    def test_safety_price_rejects_non_positive_deviation(self):
        with self.assertRaises(ValueError):
            directional_safety_price(Direction.LONG, F(100), F(0), F(1, 100))

    def test_long_safety_price_collapsing_below_zero_is_rejected(self):
        with self.assertRaises(ValueError):
            directional_safety_price(Direction.LONG, F(100), F(2), F(1, 100))

    # --- Trigger condition (the "inverted comparator" bug class) ---

    def test_long_triggers_only_when_price_falls_to_or_through_level(self):
        self.assertTrue(is_safety_triggered(Direction.LONG, F(98), F(98)))
        self.assertTrue(is_safety_triggered(Direction.LONG, F(97), F(98)))
        self.assertFalse(is_safety_triggered(Direction.LONG, F(99), F(98)))

    def test_short_triggers_only_when_price_rises_to_or_through_level(self):
        self.assertTrue(is_safety_triggered(Direction.SHORT, F(102), F(102)))
        self.assertTrue(is_safety_triggered(Direction.SHORT, F(103), F(102)))
        self.assertFalse(is_safety_triggered(Direction.SHORT, F(101), F(102)))

    def test_short_ladder_does_not_fire_immediately_at_anchor_price(self):
        # Regression for the documented sector bug: reusing the LONG `<=`
        # comparator for SHORT fires the whole ladder in the first tick.
        anchor = F(100)
        so_price = directional_safety_price(Direction.SHORT, anchor, F(2, 100), F(1, 100))
        self.assertFalse(is_safety_triggered(Direction.SHORT, anchor, so_price))

    def test_trigger_rejects_non_positive_prices(self):
        with self.assertRaises(ValueError):
            is_safety_triggered(Direction.LONG, F(0), F(1))

    # --- Faz 17 C.3: take-profit trigger (mirror of safety trigger) ---

    def test_long_take_profit_triggers_only_when_price_rises_to_or_through_target(self):
        self.assertTrue(is_take_profit_triggered(Direction.LONG, F(110), F(110)))
        self.assertTrue(is_take_profit_triggered(Direction.LONG, F(111), F(110)))
        self.assertFalse(is_take_profit_triggered(Direction.LONG, F(109), F(110)))

    def test_short_take_profit_triggers_only_when_price_falls_to_or_through_target(self):
        self.assertTrue(is_take_profit_triggered(Direction.SHORT, F(90), F(90)))
        self.assertTrue(is_take_profit_triggered(Direction.SHORT, F(89), F(90)))
        self.assertFalse(is_take_profit_triggered(Direction.SHORT, F(91), F(90)))

    def test_take_profit_trigger_rejects_non_positive_prices(self):
        with self.assertRaises(ValueError):
            is_take_profit_triggered(Direction.LONG, F(0), F(1))

    # --- Faz 17 C.2: build_plan direction support ---

    def _plan_args(self):
        return dict(
            anchor=F(100),
            safety_qty=F(1),
            count=3,
            deviation=F(2, 100),
            step_multiplier=F(1),
            volume_multiplier=F(1),
            tick=F(1, 100),
            qty_step=F(1, 100),
        )

    def test_build_plan_omitted_direction_defaults_to_long_unchanged(self):
        args = self._plan_args()
        default_call = build_plan(**args)
        explicit_long = build_plan(**args, direction=Direction.LONG)
        self.assertEqual(default_call, explicit_long)
        self.assertEqual([level.price for level in default_call], sorted(
            (level.price for level in default_call), reverse=True
        ))

    def test_build_plan_short_ladder_ascends_above_anchor(self):
        args = self._plan_args()
        plan = build_plan(**args, direction=Direction.SHORT)
        prices = [level.price for level in plan]
        self.assertEqual(prices, sorted(prices))
        self.assertTrue(all(price > args["anchor"] for price in prices))

    def test_build_plan_first_short_level_matches_directional_safety_price(self):
        args = self._plan_args()
        plan = build_plan(**args, direction=Direction.SHORT)
        expected_first = directional_safety_price(
            Direction.SHORT, args["anchor"], args["deviation"], args["tick"]
        )
        self.assertEqual(plan[0].price, expected_first)

    def test_build_plan_long_and_short_ladders_mirror(self):
        args = self._plan_args()
        long_plan = build_plan(**args, direction=Direction.LONG)
        short_plan = build_plan(**args, direction=Direction.SHORT)
        for long_level, short_level in zip(long_plan, short_plan):
            self.assertEqual(args["anchor"] - long_level.price, short_level.price - args["anchor"])


if __name__ == "__main__":
    unittest.main()
