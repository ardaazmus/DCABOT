import ast
from decimal import Decimal
from pathlib import Path
import unittest

from dcabot.application.spot_grid_cycle_accounting import (
    SpotGridCycleError,
    SpotGridCycleStatus,
    SpotGridFeeProfile,
    project_spot_grid_cycle,
)
from dcabot.application.spot_inventory_projection import (
    SpotFill,
    SpotFillSide,
    new_spot_inventory_state,
)


def state():
    return new_spot_inventory_state(
        base_asset="BTC", quote_asset="USDT", base_quantity="1"
    )


def profile(**overrides):
    values = {
        "fee_asset": "USDT",
        "fee_rate": "0.01",
        "fee_quantum": "0",
        "profile_revision": "spot-fees-v1",
    }
    values.update(overrides)
    return SpotGridFeeProfile(**values)


def cycle():
    return {
        "buy_fill": SpotFill("buy-1", SpotFillSide.BUY, "100", "0.1"),
        "sell_fill": SpotFill("sell-1", SpotFillSide.SELL, "110", "0.1"),
    }


class SpotGridCycleAccountingTests(unittest.TestCase):
    def test_matched_profit_and_total_equity_are_exactly_separate(self):
        result = project_spot_grid_cycle(
            state(), fee_profile=profile(), mark_price="105", **cycle()
        )

        buy_notional = Decimal("100") * Decimal("0.1")
        sell_notional = Decimal("110") * Decimal("0.1")
        fee = (buy_notional + sell_notional) * Decimal("0.01")
        expected_profit = sell_notional - buy_notional - fee
        expected_equity = expected_profit + Decimal("1") * Decimal("105")
        render = lambda value: format(value, "f").rstrip("0").rstrip(".")
        self.assertEqual(
            (
                result.status,
                result.matched_cycle_profit_quote,
                result.fee_quote,
                result.open_inventory_mark_quote,
                result.total_equity_quote,
            ),
            (
                SpotGridCycleStatus.READY,
                render(expected_profit),
                render(fee),
                "105",
                render(expected_equity),
            ),
        )

    def test_cycle_profit_is_mark_independent_but_total_equity_is_not(self):
        first = project_spot_grid_cycle(
            state(), fee_profile=profile(), mark_price="105", **cycle()
        )
        second = project_spot_grid_cycle(
            state(), fee_profile=profile(), mark_price="120", **cycle()
        )

        self.assertEqual(first.matched_cycle_profit_quote, second.matched_cycle_profit_quote)
        self.assertNotEqual(first.total_equity_quote, second.total_equity_quote)

    def test_non_quote_asset_and_venue_rounding_are_rejected(self):
        with self.assertRaisesRegex(SpotGridCycleError, "SPOT_GRID_FEE_ASSET_UNSUPPORTED"):
            project_spot_grid_cycle(
                state(), fee_profile=profile(fee_asset="BNB"), mark_price="105", **cycle()
            )
        with self.assertRaisesRegex(SpotGridCycleError, "SPOT_GRID_FEE_QUANTUM_UNSUPPORTED"):
            profile(fee_quantum="0.01")

    def test_replay_from_same_immutable_state_is_identical_and_duplicates_are_blocked(self):
        first = project_spot_grid_cycle(
            state(), fee_profile=profile(), mark_price="105", **cycle()
        )
        replay = project_spot_grid_cycle(
            state(), fee_profile=profile(), mark_price="105", **cycle()
        )
        self.assertEqual(first, replay)

        from dcabot.application.spot_inventory_projection import apply_accepted_spot_fill

        accepted = apply_accepted_spot_fill(state(), cycle()["buy_fill"])
        with self.assertRaisesRegex(SpotGridCycleError, "SPOT_GRID_CYCLE_DUPLICATE_UNSAFE"):
            project_spot_grid_cycle(
                accepted,
                fee_profile=profile(),
                mark_price="105",
                **cycle(),
            )

    def test_source_has_no_persistence_or_transport_writes(self):
        source_path = (
            Path(__file__).parents[1]
            / "src"
            / "dcabot"
            / "application"
            / "spot_grid_cycle_accounting.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        forbidden_calls = {"commit", "execute", "post", "put", "delete", "send", "request"}
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue(calls.isdisjoint(forbidden_calls))


if __name__ == "__main__":
    unittest.main()
