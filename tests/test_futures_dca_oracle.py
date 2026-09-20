from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import unittest

from dcabot.application.futures_dca_plan import project_futures_dca_plan


def floor_step(value: Decimal, step: Decimal) -> Decimal:
    return (value / step).to_integral_value(rounding=ROUND_FLOOR) * step


def ceil_step(value: Decimal, step: Decimal) -> Decimal:
    return (value / step).to_integral_value(rounding=ROUND_CEILING) * step


def decimal_text(value: Decimal) -> str:
    result = format(value, "f").rstrip("0").rstrip(".")
    return result or "0"


class FuturesDcaOracleTests(unittest.TestCase):
    def test_long_projection_matches_independent_decimal_oracle(self):
        result = project_futures_dca_plan(
            side="LONG", anchor_price="100", base_amount="10", base_sizing="QUOTE_NOTIONAL",
            safety_amount="2", safety_sizing="QUOTE_NOTIONAL", safety_count=2,
            deviation="0.01", step_multiplier="2", volume_multiplier="2",
            price_tick="0.01", quantity_step="0.0001",
        )
        anchor = Decimal("100")
        step = Decimal("0.01")
        qty_step = Decimal("0.0001")
        cumulative = Decimal("0")
        increment = Decimal("0.01")
        amount = Decimal("2")
        expected = []
        for index in range(2):
            cumulative += increment
            price = floor_step(anchor * (Decimal("1") - cumulative), step)
            quantity = floor_step(amount / price, qty_step)
            expected.append((decimal_text(price), decimal_text(quantity * price)))
            increment *= Decimal("2")
            amount *= Decimal("2")
        self.assertEqual(tuple((level.price, level.quote_allocation) for level in result.levels), tuple(expected))

    def test_short_projection_matches_independent_decimal_oracle(self):
        result = project_futures_dca_plan(
            side="SHORT", anchor_price="100", base_amount="1", base_sizing="BASE_QTY",
            safety_amount="0.1", safety_sizing="BASE_QTY", safety_count=2,
            deviation="0.01", step_multiplier="1", volume_multiplier="1",
            price_tick="0.5", quantity_step="0.1",
        )
        anchor = Decimal("100")
        cumulative = Decimal("0")
        expected_prices = []
        for _ in range(2):
            cumulative += Decimal("0.01")
            expected_prices.append(decimal_text(ceil_step(anchor * (Decimal("1") + cumulative), Decimal("0.5"))))
        self.assertEqual(tuple(level.price for level in result.levels), tuple(expected_prices))


if __name__ == "__main__":
    unittest.main()
