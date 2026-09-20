import ast
from pathlib import Path
import unittest

from dcabot.application.futures_dca_fill_projection import (
    FuturesDcaFill,
    project_futures_dca_fills,
)
from dcabot.application.futures_dca_plan import project_futures_dca_plan
from dcabot.application.futures_dca_take_profit import (
    FuturesDcaTakeProfitError,
    FuturesDcaTakeProfitProjection,
    project_futures_dca_take_profit,
)


def plan(*, side="LONG", safety_amount="2"):
    return project_futures_dca_plan(
        side=side,
        anchor_price="100",
        base_amount="10",
        base_sizing="QUOTE_NOTIONAL",
        safety_amount=safety_amount,
        safety_sizing="QUOTE_NOTIONAL",
        safety_count=2,
        deviation="0.01",
        step_multiplier="2",
        volume_multiplier="2",
        price_tick="0.001",
        quantity_step="0.0001",
    )


def fills(*, side="LONG"):
    entry = "100"
    safety = "97" if side == "LONG" else "103"
    return project_futures_dca_fills(
        plan(side=side, safety_amount="2.06" if side == "SHORT" else "2"),
        (FuturesDcaFill("base", 0, "0.1", entry), FuturesDcaFill("s1", 1, "0.02", safety)),
    )


class FuturesDcaTakeProfitTests(unittest.TestCase):
    def test_long_average_entry_and_split_quantities_are_exact(self):
        result = project_futures_dca_take_profit(
            fills(), profit_rate="0.01", split_quantities=("0.06", "0.04")
        )

        self.assertEqual(
            (
                result.average_entry,
                result.profit_rate,
                result.target_price,
                result.split_quantities,
                result.allocated_quantity,
                result.remaining_quantity,
            ),
            ("99.5", "0.01", "100.495", ("0.06", "0.04"), "0.1", "0.02"),
        )
        self.assertEqual(result.order_authority, "NONE")

    def test_short_average_entry_uses_the_opposite_target_direction(self):
        result = project_futures_dca_take_profit(
            fills(side="SHORT"), profit_rate="0.01", split_quantities=("0.12",)
        )

        self.assertEqual(result.average_entry, "100.5")
        self.assertEqual(result.target_price, "99.495")
        self.assertEqual(result.remaining_quantity, "0")

    def test_split_overallocation_is_rejected_before_exit_authority(self):
        with self.assertRaisesRegex(
            FuturesDcaTakeProfitError, "EXIT_CAPACITY_EXCEEDED"
        ):
            project_futures_dca_take_profit(
                fills(), profit_rate="0.01", split_quantities=("0.13",)
            )

    def test_empty_or_invalid_position_and_split_fail_closed(self):
        empty = project_futures_dca_fills(plan(), ())
        with self.assertRaisesRegex(FuturesDcaTakeProfitError, "TP_POSITION_EMPTY"):
            project_futures_dca_take_profit(
                empty, profit_rate="0.01", split_quantities=("0.1",)
            )
        for quantities in ((), ("0",), ("bad",)):
            with self.subTest(quantities=quantities), self.assertRaisesRegex(
                FuturesDcaTakeProfitError, "TP_SPLIT_INVALID"
            ):
                project_futures_dca_take_profit(
                    fills(), profit_rate="0.01", split_quantities=quantities
                )

    def test_target_must_be_positive_and_on_tick_grid(self):
        with self.assertRaisesRegex(FuturesDcaTakeProfitError, "TP_TARGET_INVALID"):
            project_futures_dca_take_profit(
                fills(side="SHORT"), profit_rate="1", split_quantities=("0.1",)
            )
        with self.assertRaisesRegex(
            FuturesDcaTakeProfitError, "TP_TARGET_OFF_GRID"
        ):
            project_futures_dca_take_profit(
                fills(), profit_rate="0.001", split_quantities=("0.1",)
            )

    def test_projection_rejects_order_authority(self):
        with self.assertRaisesRegex(
            FuturesDcaTakeProfitError, "TP_ORDER_AUTHORITY_INVALID"
        ):
            FuturesDcaTakeProfitProjection(
                fill_projection=fills(),
                average_entry="99.5",
                profit_rate="0.01",
                target_price="100.495",
                split_quantities=("0.1",),
                allocated_quantity="0.1",
                remaining_quantity="0.02",
                order_authority="CREATE_ORDER",
            )

    def test_source_has_no_persistence_or_transport_writes(self):
        source_path = (
            Path(__file__).parents[1]
            / "src"
            / "dcabot"
            / "application"
            / "futures_dca_take_profit.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        forbidden_calls = {
            "commit",
            "execute",
            "post",
            "put",
            "delete",
            "send",
            "request",
        }
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue(calls.isdisjoint(forbidden_calls))


if __name__ == "__main__":
    unittest.main()
