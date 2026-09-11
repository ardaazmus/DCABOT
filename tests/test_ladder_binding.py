import unittest

from dcabot.application.ladder_binding import (
    LadderBindingError,
    LadderBinding,
    LadderLevelCandidate,
    build_ladder_binding,
)
from dcabot.application.ladder_conservation import LadderConservation


class LadderBindingTests(unittest.TestCase):
    def test_domain_levels_bind_to_exact_base_conservation(self):
        result = build_ladder_binding(
            anchor_price="100",
            safety_qty="0.1",
            safety_count=2,
            deviation="0.1",
            step_multiplier="1",
            volume_multiplier="1",
            price_tick="0.5",
            qty_step="0.1",
            allocation_unit="BASE_QTY",
            budget="0.3",
        )

        self.assertEqual(
            result,
            LadderBinding(
                levels=(
                    LadderLevelCandidate(index=1, price="90", quantity="0.1", allocation="0.1"),
                    LadderLevelCandidate(index=2, price="80", quantity="0.1", allocation="0.1"),
                ),
                conservation=LadderConservation(
                    allocation_unit="BASE_QTY",
                    total_allocated="0.2",
                    budget="0.3",
                    remaining_budget="0.1",
                ),
            ),
        )

    def test_quote_allocation_uses_exact_level_notional(self):
        result = build_ladder_binding(
            anchor_price="100",
            safety_qty="0.1",
            safety_count=2,
            deviation="0.1",
            step_multiplier="1",
            volume_multiplier="1",
            price_tick="0.5",
            qty_step="0.1",
            allocation_unit="QUOTE_NOTIONAL",
            budget="20",
        )

        self.assertEqual(
            tuple(level.allocation for level in result.levels), ("9", "8")
        )
        self.assertEqual(result.conservation.total_allocated, "17")

    def test_binding_rejects_budget_overrun_or_invalid_generation(self):
        with self.assertRaisesRegex(LadderBindingError, "LADDER_BUDGET_EXCEEDED"):
            build_ladder_binding(
                anchor_price="100",
                safety_qty="0.1",
                safety_count=2,
                deviation="0.1",
                step_multiplier="1",
                volume_multiplier="1",
                price_tick="0.5",
                qty_step="0.1",
                allocation_unit="QUOTE_NOTIONAL",
                budget="16",
            )
        with self.assertRaisesRegex(LadderBindingError, "LADDER_GENERATION_INVALID"):
            build_ladder_binding(
                anchor_price="100",
                safety_qty="0.1",
                safety_count=2,
                deviation="1",
                step_multiplier="1",
                volume_multiplier="1",
                price_tick="0.5",
                qty_step="0.1",
                allocation_unit="BASE_QTY",
                budget="1",
            )


if __name__ == "__main__":
    unittest.main()
