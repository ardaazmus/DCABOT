"""Faz 17 G.4 (RG-09): three-valued (Kleene) boolean AST for multi-signal
conditions. All/Any/Not truth tables, cross_up/cross_down UNKNOWN-on-missing
data, and the should_act (TRUE-only) action rule."""
import unittest

from dcabot.application.signal_condition_ast import (
    All,
    Any_,
    Condition,
    CrossDown,
    CrossUp,
    Not,
    SignalConditionError,
    evaluate,
    should_act,
)

T, F, U = Condition("TRUE"), Condition("FALSE"), Condition("UNKNOWN")


class AllTruthTableTests(unittest.TestCase):
    def test_all_true_is_true(self):
        self.assertEqual(evaluate(All((T, T))), "TRUE")

    def test_any_false_makes_all_false_even_with_unknown(self):
        self.assertEqual(evaluate(All((T, F, U))), "FALSE")

    def test_unknown_without_false_makes_all_unknown(self):
        self.assertEqual(evaluate(All((T, U))), "UNKNOWN")

    def test_single_child(self):
        self.assertEqual(evaluate(All((U,))), "UNKNOWN")

    def test_empty_group_is_rejected(self):
        with self.assertRaises(SignalConditionError):
            evaluate(All(()))

    def test_nested_all(self):
        self.assertEqual(evaluate(All((T, All((T, T))))), "TRUE")
        self.assertEqual(evaluate(All((T, All((T, F))))), "FALSE")


class AnyTruthTableTests(unittest.TestCase):
    def test_any_true_makes_any_true_even_with_false_and_unknown(self):
        self.assertEqual(evaluate(Any_((F, U, T))), "TRUE")

    def test_unknown_without_true_makes_any_unknown(self):
        self.assertEqual(evaluate(Any_((F, U))), "UNKNOWN")

    def test_all_false_is_false(self):
        self.assertEqual(evaluate(Any_((F, F))), "FALSE")

    def test_empty_group_is_rejected(self):
        with self.assertRaises(SignalConditionError):
            evaluate(Any_(()))

    def test_nested_any(self):
        self.assertEqual(evaluate(Any_((F, Any_((F, T))))), "TRUE")


class NotTruthTableTests(unittest.TestCase):
    def test_not_true_is_false(self):
        self.assertEqual(evaluate(Not(T)), "FALSE")

    def test_not_false_is_true(self):
        self.assertEqual(evaluate(Not(F)), "TRUE")

    def test_not_unknown_is_unknown(self):
        self.assertEqual(evaluate(Not(U)), "UNKNOWN")

    def test_double_negation(self):
        self.assertEqual(evaluate(Not(Not(T))), "TRUE")


class CrossTests(unittest.TestCase):
    def test_cross_up_detected(self):
        a = (1, 2, 5)
        b = (3, 3, 3)
        node = CrossUp(a, b, index=2)
        self.assertEqual(evaluate(node), "TRUE")

    def test_cross_up_false_when_no_cross(self):
        a = (5, 6, 7)
        b = (1, 1, 1)
        node = CrossUp(a, b, index=2)
        self.assertEqual(evaluate(node), "FALSE")

    def test_cross_down_detected(self):
        a = (5, 4, 1)
        b = (3, 3, 3)
        node = CrossDown(a, b, index=2)
        self.assertEqual(evaluate(node), "TRUE")

    def test_missing_value_is_unknown_not_false(self):
        a = (1, None, 5)
        b = (3, 3, 3)
        node = CrossUp(a, b, index=2)
        self.assertEqual(evaluate(node), "UNKNOWN")

    def test_length_mismatch_is_rejected(self):
        with self.assertRaises(SignalConditionError):
            evaluate(CrossUp((1, 2), (1, 2, 3), index=1))

    def test_index_out_of_range_is_rejected(self):
        with self.assertRaises(SignalConditionError):
            evaluate(CrossUp((1, 2, 3), (1, 2, 3), index=0))
        with self.assertRaises(SignalConditionError):
            evaluate(CrossUp((1, 2, 3), (1, 2, 3), index=3))

    def test_unknown_cross_propagates_through_all(self):
        node = All((CrossUp((1, None, 5), (3, 3, 3), index=2), T))
        self.assertEqual(evaluate(node), "UNKNOWN")


class ShouldActTests(unittest.TestCase):
    def test_true_acts(self):
        self.assertTrue(should_act(T))

    def test_false_withholds_action(self):
        self.assertFalse(should_act(F))

    def test_unknown_withholds_action(self):
        self.assertFalse(should_act(U))

    def test_and_of_true_and_unknown_withholds_action(self):
        self.assertFalse(should_act(All((T, U))))

    def test_deeply_nested_mixed_expression(self):
        # any(all(TRUE, TRUE), not(cross_down(missing data))) -> UNKNOWN overall
        # because the second Any_ branch is UNKNOWN and the first is TRUE,
        # so Any_ resolves TRUE regardless (TRUE dominates UNKNOWN in OR).
        expr = Any_((All((T, T)), Not(CrossDown((1, None), (1, 1), index=1))))
        self.assertEqual(evaluate(expr), "TRUE")
        self.assertTrue(should_act(expr))


if __name__ == "__main__":
    unittest.main()
