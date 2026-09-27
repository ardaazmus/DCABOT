"""G2-a: spot-grid engine contract — allocation, fills, TP/SL, trailing."""

import unittest

from dcabot.application.spot_grid_cycle_accounting import SpotGridFeeProfile
from dcabot.application.spot_grid_engine import (
    SpotGridConfig,
    SpotGridEngineError,
    SpotGridMode,
    SpotGridStatus,
    apply_tick,
    create_grid,
    describe_grid,
    grid_equity_quote,
    restore_grid,
    snapshot_grid,
)
from dcabot.domain.numbers import Q, number


def _profile() -> SpotGridFeeProfile:
    return SpotGridFeeProfile(
        fee_asset="USDT",
        fee_rate="0.001",
        fee_quantum="0",
        profile_revision="test1",
    )


def _config(**overrides: object) -> SpotGridConfig:
    params: dict[str, object] = {
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "mode": SpotGridMode.ARITHMETIC,
        "lower_price": "20000",
        "upper_price": "30000",
        "interval_count": 10,
        "investment_quote": "1000",
        "base_step_size": "0.00001",
        "fee_profile": _profile(),
    }
    params.update(overrides)
    return SpotGridConfig(**params)  # type: ignore[arg-type]


def _quote_invariant(config: SpotGridConfig, state) -> None:
    """Reserve + locked quote equals investment − buys + sells, exactly."""
    reserve = number(state.quote_reserve)
    locked = sum((number(v) for v in state.locked_quote), Q(0))
    buys = sum(
        (number(f.price) * number(f.base_quantity) for f in state.inventory.fills if f.side == "BUY"),
        Q(0),
    )
    sells = sum(
        (number(f.price) * number(f.base_quantity) for f in state.inventory.fills if f.side == "SELL"),
        Q(0),
    )
    assert reserve + locked == number(config.investment_quote) - buys + sells


class GridConfigTest(unittest.TestCase):
    def test_derives_levels_and_quote_per_grid(self) -> None:
        config = _config()
        self.assertEqual(len(config.levels), 11)
        self.assertEqual(config.levels[0], "20000")
        self.assertEqual(config.levels[-1], "30000")
        self.assertEqual(config.levels[5], "25000")
        self.assertEqual(config.quote_per_grid, "100")
        self.assertEqual(len(config.fingerprint), 16)

    def test_rejects_same_asset(self) -> None:
        with self.assertRaises(SpotGridEngineError) as ctx:
            _config(base_asset="USDT")
        self.assertEqual(ctx.exception.code, "SPOT_GRID_ASSET_INVALID")

    def test_rejects_inexact_quote_per_grid(self) -> None:
        with self.assertRaises(SpotGridEngineError) as ctx:
            _config(lower_price="21000", interval_count=3)
        self.assertEqual(ctx.exception.code, "SPOT_GRID_QUOTE_PER_GRID_UNREPRESENTABLE")

    def test_rejects_grid_below_step(self) -> None:
        with self.assertRaises(SpotGridEngineError) as ctx:
            _config(base_step_size="0.001", investment_quote="10")
        self.assertEqual(ctx.exception.code, "SPOT_GRID_QTY_TOO_SMALL")

    def test_rejects_stop_loss_inside_range(self) -> None:
        with self.assertRaises(SpotGridEngineError) as ctx:
            _config(stop_loss_price="20000")
        self.assertEqual(ctx.exception.code, "SPOT_GRID_SL_INVALID")

    def test_rejects_zero_take_profit(self) -> None:
        with self.assertRaises(SpotGridEngineError) as ctx:
            _config(take_profit_pct="0")
        self.assertEqual(ctx.exception.code, "SPOT_GRID_TP_INVALID")

    def test_geometric_config_ok(self) -> None:
        config = _config(
            mode=SpotGridMode.GEOMETRIC,
            lower_price="100",
            upper_price="121",
            interval_count=2,
            investment_quote="300",
            base_step_size="0.01",
            price_tick="1",
            tick_origin="0",
        )
        self.assertEqual(config.levels, ("100", "110", "121"))
        self.assertEqual(config.quote_per_grid, "150")

    def test_geometric_requires_ticks(self) -> None:
        with self.assertRaises(SpotGridEngineError) as ctx:
            _config(mode=SpotGridMode.GEOMETRIC, lower_price="100", upper_price="121",
                    interval_count=2, investment_quote="300", base_step_size="0.01")
        self.assertEqual(ctx.exception.code, "SPOT_GRID_TICK_INVALID")


class GridInitTest(unittest.TestCase):
    def test_wait_outside_then_init_inside(self) -> None:
        config = _config()
        state = create_grid(config)
        self.assertEqual(state.status, SpotGridStatus.WAIT)
        waiting = apply_tick(state, config, price="15000")
        self.assertEqual(waiting.state.status, SpotGridStatus.WAIT)
        self.assertEqual(waiting.events, ("GRID_WAIT",))
        init = apply_tick(waiting.state, config, price="25000")
        self.assertEqual(init.state.status, SpotGridStatus.ACTIVE)
        self.assertEqual(init.events, ("GRID_INIT",))
        self.assertEqual(init.state.entry_price, "25000")
        # 5 buy intervals below, 5 sell intervals above.
        self.assertEqual(init.state.pending[:5], ("BUY",) * 5)
        self.assertEqual(init.state.pending[5:], ("SELL",) * 5)
        self.assertEqual(len(init.fills), 5)
        self.assertTrue(all(fill.side == "BUY" for fill in init.fills))
        # 5 x 0.004 base bought at 25000; reserve fully deployed.
        self.assertEqual(init.state.quote_reserve, "0")
        self.assertEqual(sum(number(v) for v in init.state.locked_base), Q(2, 100))
        _quote_invariant(config, init.state)

    def test_entry_inclusive_at_bounds(self) -> None:
        config = _config()
        low = apply_tick(create_grid(config), config, price="20000")
        self.assertEqual(low.state.status, SpotGridStatus.ACTIVE)
        self.assertEqual(low.state.pending, ("SELL",) * 10)
        high = apply_tick(create_grid(config), config, price="30000")
        self.assertEqual(high.state.status, SpotGridStatus.ACTIVE)
        self.assertEqual(high.state.pending, ("BUY",) * 10)

    def test_equity_equals_investment_at_entry(self) -> None:
        config = _config()
        init = apply_tick(create_grid(config), config, price="25000")
        self.assertEqual(grid_equity_quote(init.state, mark_price="25000"), "1000")


class GridFillTest(unittest.TestCase):
    def _active(self, config=None):
        config = config or _config()
        return config, apply_tick(create_grid(config), config, price="25000").state

    def test_buy_cross_fills_at_level_and_flips(self) -> None:
        config, active = self._active()
        result = apply_tick(active, config, price="24000")
        self.assertEqual(len(result.fills), 1)
        fill = result.fills[0]
        self.assertEqual(fill.side, "BUY")
        self.assertEqual(fill.price, "24000")
        self.assertEqual(fill.base_quantity, "0.00416")
        self.assertEqual(result.state.pending[4], "SELL")
        self.assertEqual(result.state.locked_base[4], "0.00416")
        self.assertEqual(result.state.quote_reserve, "0.16")
        _quote_invariant(config, result.state)

    def test_falling_multi_cross_processes_top_down(self) -> None:
        config, active = self._active()
        result = apply_tick(active, config, price="22500")
        self.assertEqual([f.price for f in result.fills], ["24000", "23000"])
        self.assertEqual(result.state.pending[4], "SELL")
        self.assertEqual(result.state.pending[3], "SELL")
        _quote_invariant(config, result.state)

    def test_sell_cross_compounds_proceeds(self) -> None:
        config, active = self._active()
        bought = apply_tick(active, config, price="24000")
        sold = apply_tick(bought.state, config, price="26000")
        prices = sorted(f.price for f in sold.fills)
        self.assertEqual(prices, ["25000", "26000"])
        self.assertEqual(sold.state.pending[4], "BUY")
        self.assertEqual(sold.state.locked_quote[4], "104")
        self.assertEqual(sold.state.cycles_closed, 2)
        self.assertEqual(sold.state.realized_profit_quote, "-391.84")
        self.assertEqual(sold.state.fees_paid_quote, "0.80784")
        self.assertEqual(grid_equity_quote(sold.state, mark_price="26000"), "1024.16")
        _quote_invariant(config, sold.state)

    def test_flat_tick_no_fills(self) -> None:
        config, active = self._active()
        result = apply_tick(active, config, price="25000")
        self.assertEqual(result.fills, ())
        self.assertEqual(result.state.next_fill_seq, active.next_fill_seq)

    def test_dust_level_abandoned_explicitly(self) -> None:
        config, active = self._active()
        snapshot = snapshot_grid(active)
        locked = list(snapshot["locked_quote"])
        locked[4] = "0.000001"
        snapshot["locked_quote"] = locked
        dusted = restore_grid(snapshot, config)
        result = apply_tick(dusted, config, price="24000")
        self.assertEqual(result.fills, ())
        self.assertIn("GRID_LEVEL_ABANDONED", result.events)
        self.assertEqual(result.state.pending[4], "NONE")

    def test_invalid_tick_rejected(self) -> None:
        config, active = self._active()
        with self.assertRaises(SpotGridEngineError) as ctx:
            apply_tick(active, config, price="-5")
        self.assertEqual(ctx.exception.code, "SPOT_GRID_TICK_INVALID")

    def test_config_mismatch_rejected(self) -> None:
        _, active = self._active()
        other = _config(investment_quote="2000")
        with self.assertRaises(SpotGridEngineError) as ctx:
            apply_tick(active, other, price="25000")
        self.assertEqual(ctx.exception.code, "SPOT_GRID_CONFIG_MISMATCH")


class GridExitTest(unittest.TestCase):
    def test_stop_loss_liquidates_and_halts(self) -> None:
        config = _config(stop_loss_price="19000")
        state = apply_tick(create_grid(config), config, price="25000").state
        state = apply_tick(state, config, price="24000").state
        done = apply_tick(state, config, price="19000")
        self.assertEqual(done.state.status, SpotGridStatus.DONE_SL)
        self.assertIn("GRID_STOP_LOSS", done.events)
        self.assertEqual(set(done.state.pending), {"NONE"})
        self.assertEqual(sum(number(v) for v in done.state.locked_base), Q(0))
        # Terminal ticks return the state unchanged.
        again = apply_tick(done.state, config, price="18000")
        self.assertEqual(again.fills, ())
        self.assertIs(again.state, done.state)
        _quote_invariant(config, done.state)

    def test_take_profit_liquidates_on_target(self) -> None:
        config = _config(take_profit_pct="0.01")
        state = apply_tick(create_grid(config), config, price="25000").state
        done = apply_tick(state, config, price="26000")
        self.assertEqual(done.state.status, SpotGridStatus.DONE_TP)
        self.assertIn("GRID_TAKE_PROFIT", done.events)
        self.assertEqual(set(done.state.pending), {"NONE"})
        _quote_invariant(config, done.state)

    def test_no_take_profit_without_config(self) -> None:
        config = _config()
        state = apply_tick(create_grid(config), config, price="25000").state
        result = apply_tick(state, config, price="29000")
        self.assertEqual(result.state.status, SpotGridStatus.ACTIVE)


class GridTrailingTest(unittest.TestCase):
    def test_trailing_up_shifts_and_replans(self) -> None:
        config = _config(trailing_up_pct="0.05")
        state = apply_tick(create_grid(config), config, price="25000").state
        result = apply_tick(state, config, price="32000")
        self.assertEqual(result.state.status, SpotGridStatus.ACTIVE)
        self.assertIn("GRID_TRAIL_UP", result.events)
        self.assertEqual(result.state.levels[0], "22000")
        self.assertEqual(result.state.levels[-1], "32000")
        self.assertEqual(result.state.trailing_shifts, 1)
        _quote_invariant(config, result.state)

    def test_trailing_down_shifts_range(self) -> None:
        config = _config(trailing_down_pct="0.05")
        state = apply_tick(create_grid(config), config, price="25000").state
        result = apply_tick(state, config, price="18500")
        self.assertEqual(result.state.status, SpotGridStatus.ACTIVE)
        self.assertIn("GRID_TRAIL_DOWN", result.events)
        self.assertEqual(result.state.levels[0], "18500")
        self.assertEqual(result.state.levels[-1], "28500")
        _quote_invariant(config, result.state)

    def test_geometric_trail_skipped_off_tick(self) -> None:
        config = _config(
            mode=SpotGridMode.GEOMETRIC,
            lower_price="100",
            upper_price="121",
            interval_count=2,
            investment_quote="300",
            base_step_size="0.01",
            price_tick="1",
            tick_origin="0",
            trailing_up_pct="0.01",
        )
        state = apply_tick(create_grid(config), config, price="110").state
        result = apply_tick(state, config, price="123")
        self.assertIn("GRID_TRAIL_SKIPPED", result.events)
        self.assertEqual(result.state.levels, ("100", "110", "121"))
        self.assertEqual(result.state.trailing_shifts, 0)


class GridSnapshotTest(unittest.TestCase):
    def test_round_trip_continues_identically(self) -> None:
        config = _config()
        state = apply_tick(create_grid(config), config, price="25000").state
        state = apply_tick(state, config, price="24000").state
        restored = restore_grid(snapshot_grid(state), config)
        self.assertEqual(restored, state)
        live = apply_tick(state, config, price="26000").state
        resumed = apply_tick(restored, config, price="26000").state
        self.assertEqual(resumed, live)

    def test_wait_snapshot_round_trip(self) -> None:
        config = _config()
        state = create_grid(config)
        self.assertEqual(restore_grid(snapshot_grid(state), config), state)

    def test_rejects_foreign_revision(self) -> None:
        config = _config()
        snapshot = snapshot_grid(create_grid(config))
        snapshot["engine_revision"] = "G1"
        with self.assertRaises(SpotGridEngineError) as ctx:
            restore_grid(snapshot, config)
        self.assertEqual(ctx.exception.code, "SPOT_GRID_SNAPSHOT_REVISION_INVALID")

    def test_rejects_foreign_config(self) -> None:
        config = _config()
        snapshot = snapshot_grid(create_grid(config))
        with self.assertRaises(SpotGridEngineError) as ctx:
            restore_grid(snapshot, _config(investment_quote="2000"))
        self.assertEqual(ctx.exception.code, "SPOT_GRID_CONFIG_MISMATCH")

    def test_rejects_bad_shape(self) -> None:
        config = _config()
        snapshot = snapshot_grid(create_grid(config))
        snapshot["pending"] = ["BUY"]
        with self.assertRaises(SpotGridEngineError) as ctx:
            restore_grid(snapshot, config)
        self.assertEqual(ctx.exception.code, "SPOT_GRID_SNAPSHOT_INVALID")

    def test_describe_grid_preview(self) -> None:
        summary = describe_grid(_config())
        self.assertEqual(summary["quote_per_grid"], "100")
        self.assertEqual(len(summary["levels"]), 11)
        self.assertEqual(summary["engine_revision"], "G2a.1")


if __name__ == "__main__":
    unittest.main()
