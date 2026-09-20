from decimal import Decimal
import unittest

from dcabot.application.futures_dca_fill_projection import (
    FuturesDcaFill,
    project_futures_dca_fills,
)
from dcabot.application.futures_dca_plan import project_futures_dca_plan
from dcabot.application.linear_futures_math import LinearFuturesPosition


def decimal_text(value: Decimal) -> str:
    result = format(value, "f").rstrip("0").rstrip(".")
    return result or "0"


class FuturesDcaContractSizeGateTests(unittest.TestCase):
    def test_dca_notional_waits_for_explicit_multiplier_binding(self):
        plan = project_futures_dca_plan(
            side="LONG",
            anchor_price="100",
            base_amount="100",
            base_sizing="BASE_QTY",
            safety_amount="100",
            safety_sizing="BASE_QTY",
            safety_count=1,
            deviation="0.01",
            step_multiplier="1",
            volume_multiplier="1",
            price_tick="0.01",
            quantity_step="0.1",
        )
        result = project_futures_dca_fills(
            plan,
            (
                FuturesDcaFill("base", 0, "100", "100"),
                FuturesDcaFill("safety-1", 1, "100", "99"),
            ),
        )

        multiplier = Decimal("0.001")
        expected_effective_quantity = Decimal("200") * multiplier
        expected_effective_notional = (
            Decimal("100") * Decimal("100")
            + Decimal("100") * Decimal("99")
        ) * multiplier
        position = LinearFuturesPosition(
            side="LONG",
            quantity=result.position_quantity,
            contract_size=str(multiplier),
            entry_price=result.average_entry or "0",
            mark_price="99",
            settlement_asset="USDT",
        )

        self.assertEqual(
            (result.position_quantity, result.position_notional),
            ("200", "19900"),
        )
        self.assertEqual(
            (position.effective_quantity, position.position_value),
            (
                decimal_text(expected_effective_quantity),
                decimal_text(Decimal("99") * expected_effective_quantity),
            ),
        )
        self.assertNotEqual(result.position_notional, decimal_text(expected_effective_notional))


if __name__ == "__main__":
    unittest.main()
