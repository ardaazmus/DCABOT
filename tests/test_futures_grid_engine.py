"""G3-a: futures grid engine — lots, margin, funding, liq estimate, exits."""

import unittest

from dcabot.application.futures_grid_engine import (
    FuturesGridConfig,
    FuturesGridDirection,
    FuturesGridEngineError,
    FuturesGridMode,
    FuturesGridStatus,
    apply_funding,
    apply_tick,
    create_grid,
    describe_grid,
    grid_equity_quote,
    restore_grid,
    snapshot_grid,
)
from dcabot.application.isolated_liquidation import (
    IsolatedMarginSnapshot,
    IsolatedRiskTier,
    project_isolated_liquidation,
)
from dcabot.domain.numbers import Q, exact_text, number

TIER = IsolatedRiskTier(
    tier_id="t0",
    notional_floor="0",
    notional_cap=None,
    maintenance_rate="0.004",
    maintenance_amount="0",
    effective_time_us=0,
)
TIER_ZERO = IsolatedRiskTier(
    tier_id="tzero",
    notional_floor="0",
    notional_cap=None,
    maintenance_rate="0",
    maintenance_amount="0",
    effective_time_us=0,
)


def _config(**overrides: object) -> FuturesGridConfig:
    params: dict[str, object] = {
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "direction": FuturesGridDirection.LONG,
        "mode": FuturesGridMode.ARITHMETIC,
        "lower_price": "20000",
        "upper_price": "30000",
        "interval_count": 10,
        "investment_quote": "1000",
        "leverage": 5,
        "base_step_size": "0.00001",
        "fee_rate": "0.0005",
    }
    params.update(overrides)
    return FuturesGridConfig(**params)  # type: ignore[arg-type]


def _margin_invariant(config: FuturesGridConfig, state) -> None:
    """Wallet + locked + parcels equals investment + pnl - fees + funding."""
    wallet = number(state.wallet_free)
    locked = sum((number(v) for v in state.locked_margin), Q(0))
    parcels = sum((number(lot.locked_margin) for lot in state.open_lots), Q(0))
    expected = (
        number(config.investment_quote)
        + number(state.realized_gross_pnl)
        - number(state.fees_paid_quote)
        + number(state.funding_cashflow)
    )
    assert wallet + locked + parcels == expected, (wallet + locked + parcels, expected)


class FuturesGridConfigTest(unittest.TestCase):
    def test_derives_levels_and_margin_per_grid(self) -> None:
        config = _config()
        self.assertEqual(len(config.levels), 11)
        self.assertEqual(config.quote_per_grid, "100")
        self.assertEqual(len(config.fingerprint), 16)

    def test_rejects_bad_direction_and_leverage(self) -> None:
        with self.assertRaises(FuturesGridEngineError) as ctx:
            _config(direction="HEDGE")
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_DIRECTION_INVALID")
        with self.assertRaises(FuturesGridEngineError) as ctx:
            _config(leverage=11)
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_LEVERAGE_INVALID")
        with self.assertRaises(FuturesGridEngineError) as ctx:
            _config(leverage=0)
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_LEVERAGE_INVALID")

    def test_rejects_non_usdt_settlement(self) -> None:
        with self.assertRaises(FuturesGridEngineError) as ctx:
            _config(quote_asset="USDC")
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_SETTLEMENT_UNSUPPORTED")

    def test_rejects_misplaced_stop(self) -> None:
        with self.assertRaises(FuturesGridEngineError) as ctx:
            _config(stop_loss_price="20000")
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_SL_INVALID")
        with self.assertRaises(FuturesGridEngineError) as ctx:
            _config(direction=FuturesGridDirection.SHORT, stop_loss_price="30000")
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_SL_INVALID")
        short = _config(direction=FuturesGridDirection.SHORT, stop_loss_price="31000")
        self.assertEqual(short.stop_loss_price, "31000")

    def test_rejects_inexact_quote_per_grid(self) -> None:
        with self.assertRaises(FuturesGridEngineError) as ctx:
            _config(lower_price="21000", interval_count=3)
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_QUOTE_PER_GRID_UNREPRESENTABLE")

    def test_rejects_inexact_margin_per_grid(self) -> None:
        with self.assertRaises(FuturesGridEngineError) as ctx:
            _config(leverage=3)
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_MARGIN_PER_GRID_UNREPRESENTABLE")


class FuturesGridMarginExactnessTest(unittest.TestCase):
    def test_crossing_open_steps_qty_down_to_exact_margin(self) -> None:
        config = _config(
            lower_price="85",
            upper_price="105",
            interval_count=10,
            investment_quote="105",
            leverage=3,
            base_step_size="0.001",
            fee_rate="0",
        )
        state = apply_tick(create_grid(config), config, price="100", time_us=100).state
        state = apply_tick(state, config, price="94", time_us=200).state
        lot = next(item for item in state.open_lots if item.entry_price == "95")
        # Raw qty 0.11 has margin 10.45/3 (unrepresentable); 0.108 lands 3.42.
        self.assertEqual(lot.quantity, "0.108")
        self.assertEqual(lot.locked_margin, "3.42")
        _margin_invariant(config, state)


class FuturesGridLongTest(unittest.TestCase):
    def test_init_allocates_margin_and_opens(self) -> None:
        config = _config()
        result = apply_tick(create_grid(config), config, price="25000", time_us=100)
        state = result.state
        self.assertEqual(state.status, FuturesGridStatus.ACTIVE)
        self.assertEqual(state.pending[:5], ("BUY",) * 5)
        self.assertEqual(state.pending[5:], ("SELL",) * 5)
        self.assertEqual(len(state.fills), 5)
        self.assertEqual(state.wallet_free, "799.75")
        self.assertEqual(len(state.open_lots), 5)
        self.assertEqual(grid_equity_quote(state, config, mark_price="25000"), "999.75")
        _margin_invariant(config, state)

    def test_open_then_two_closes_match_hand_computation(self) -> None:
        config = _config()
        state = apply_tick(create_grid(config), config, price="25000", time_us=100).state
        state = apply_tick(state, config, price="24000", time_us=200).state
        self.assertEqual(state.pending[4], "SELL")
        result = apply_tick(state, config, price="26000", time_us=300)
        state = result.state
        self.assertEqual([f.price for f in result.fills], ["25000", "26000"])
        self.assertEqual(state.realized_gross_pnl, "8.16")
        self.assertEqual(state.cycles_closed, 2)
        self.assertEqual(state.fees_paid_quote, "0.40392")
        self.assertEqual(state.wallet_free, "807.75608")
        self.assertEqual(grid_equity_quote(state, config, mark_price="26000"), "1023.75608")
        _margin_invariant(config, state)

    def test_wait_outside_then_time_order_guarded(self) -> None:
        config = _config()
        waiting = apply_tick(create_grid(config), config, price="15000", time_us=100)
        self.assertEqual(waiting.events, ("GRID_WAIT",))
        with self.assertRaises(FuturesGridEngineError) as ctx:
            apply_tick(waiting.state, config, price="15000", time_us=50)
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_TIME_ORDER")

    def test_stop_loss_flattens_and_halts(self) -> None:
        config = _config(stop_loss_price="19000")
        state = apply_tick(create_grid(config), config, price="25000", time_us=100).state
        done = apply_tick(state, config, price="19000", time_us=200)
        self.assertEqual(done.state.status, FuturesGridStatus.DONE_SL)
        self.assertIn("GRID_STOP_LOSS", done.events)
        self.assertEqual(done.state.open_lots, ())
        self.assertEqual(set(done.state.pending), {"NONE"})
        again = apply_tick(done.state, config, price="18000", time_us=300)
        self.assertIs(again.state, done.state)
        _margin_invariant(config, done.state)

    def test_take_profit_flattens_on_target(self) -> None:
        config = _config(take_profit_pct="0.01")
        state = apply_tick(create_grid(config), config, price="25000", time_us=100).state
        done = apply_tick(state, config, price="26000", time_us=200)
        self.assertEqual(done.state.status, FuturesGridStatus.DONE_TP)
        self.assertIn("GRID_TAKE_PROFIT", done.events)
        _margin_invariant(config, done.state)

    def test_trailing_up_closes_then_shifts(self) -> None:
        config = _config(trailing_up_pct="0.05")
        state = apply_tick(create_grid(config), config, price="25000", time_us=100).state
        result = apply_tick(state, config, price="32000", time_us=200)
        self.assertIn("GRID_TRAIL_UP", result.events)
        self.assertEqual(result.state.levels[0], "22000")
        self.assertEqual(result.state.levels[-1], "32000")
        self.assertEqual(result.state.cycles_closed, 5)
        self.assertEqual(result.state.trailing_shifts, 1)
        _margin_invariant(config, result.state)

    def test_trailing_down_keeps_parcels(self) -> None:
        config = _config(trailing_down_pct="0.05")
        state = apply_tick(create_grid(config), config, price="25000", time_us=100).state
        parcels_before = len(state.open_lots)
        result = apply_tick(state, config, price="18500", time_us=200)
        self.assertIn("GRID_TRAIL_DOWN", result.events)
        self.assertEqual(result.state.levels[0], "18500")
        self.assertGreater(len(result.state.open_lots), parcels_before)
        _margin_invariant(config, result.state)


class FuturesGridShortTest(unittest.TestCase):
    def test_short_mirrors(self) -> None:
        config = _config(direction=FuturesGridDirection.SHORT)
        state = apply_tick(create_grid(config), config, price="25000", time_us=100).state
        self.assertEqual(state.pending[:5], ("BUY",) * 5)
        self.assertEqual(state.pending[5:], ("SELL",) * 5)
        self.assertEqual(len(state.open_lots), 5)
        # Falling closes the interval-4 short for a profit.
        result = apply_tick(state, config, price="24000", time_us=200)
        self.assertEqual(result.state.realized_gross_pnl, "4")
        self.assertEqual(result.state.cycles_closed, 1)
        # Rising opens fresh shorts, which flip to close pendings.
        result = apply_tick(result.state, config, price="26000", time_us=300)
        self.assertEqual([f.price for f in result.fills], ["25000", "26000"])
        self.assertEqual(result.state.pending[5], "BUY")
        _margin_invariant(config, result.state)

    def test_short_stop_above_range(self) -> None:
        config = _config(direction=FuturesGridDirection.SHORT, stop_loss_price="31000")
        state = apply_tick(create_grid(config), config, price="25000", time_us=100).state
        done = apply_tick(state, config, price="31000", time_us=200)
        self.assertEqual(done.state.status, FuturesGridStatus.DONE_SL)
        _margin_invariant(config, done.state)


class FuturesGridFundingTest(unittest.TestCase):
    def test_long_pays_short_receives(self) -> None:
        config = _config()
        state = apply_tick(create_grid(config), config, price="25000", time_us=100).state
        funded = apply_funding(state, config, rate="0.0001", mark_price="26000", time_us=200, event_id="f1")
        # -(0.0001) * 0.02 * 26000 = -0.052
        self.assertEqual(funded.funding_cashflow, "-0.052")
        self.assertEqual(funded.funding_events, ("f1=-0.052",))
        short = _config(direction=FuturesGridDirection.SHORT)
        state = apply_tick(create_grid(short), short, price="25000", time_us=100).state
        funded = apply_funding(state, short, rate="0.0001", mark_price="26000", time_us=200, event_id="f1")
        self.assertEqual(funded.funding_cashflow, "0.052")
        long_state = apply_tick(create_grid(config), config, price="25000", time_us=100).state
        long_funded = apply_funding(
            long_state, config, rate="0.0001", mark_price="26000", time_us=200, event_id="f1"
        )
        _margin_invariant(config, long_funded)

    def test_funding_guards(self) -> None:
        config = _config()
        state = apply_tick(create_grid(config), config, price="25000", time_us=100).state
        with self.assertRaises(FuturesGridEngineError) as ctx:
            apply_funding(state, config, rate="0.05", mark_price="26000", time_us=200, event_id="f1")
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_FUNDING_INVALID")
        funded = apply_funding(state, config, rate="0.0001", mark_price="26000", time_us=200, event_id="f1")
        with self.assertRaises(FuturesGridEngineError) as ctx:
            apply_funding(funded, config, rate="0.0001", mark_price="26000", time_us=300, event_id="f1")
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_FUNDING_DUPLICATE")
        with self.assertRaises(FuturesGridEngineError) as ctx:
            apply_funding(state, config, rate="0.0001", mark_price="26000", time_us=50, event_id="f2")
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_TIME_ORDER")


class FuturesGridLiqTest(unittest.TestCase):
    def test_healthy_tick_reports_estimate_without_breach(self) -> None:
        config = _config(risk_tiers=(TIER,), leverage=10)
        state = apply_tick(create_grid(config), config, price="25000", time_us=100).state
        # Small position vs wallet: no positive root -> no estimate, still active.
        self.assertEqual(state.status, FuturesGridStatus.ACTIVE)

    def test_crash_breaches_estimate_and_halts_labeled(self) -> None:
        config = _config(risk_tiers=(TIER_ZERO,), lower_price="20000", upper_price="30000",
                         interval_count=1, investment_quote="100", leverage=2)
        state = apply_tick(create_grid(config), config, price="25000", time_us=100).state
        # (100 - 99.95) / 0.004 = 12.5 exactly.
        self.assertEqual(state.liq_estimate_price, "12.5")
        done = apply_tick(state, config, price="10", time_us=200)
        self.assertEqual(done.state.status, FuturesGridStatus.DONE_LIQ_ESTIMATE)
        self.assertIn("GRID_LIQ_ESTIMATE_HIT", done.events)
        self.assertEqual(done.state.liq_estimate_tier, "tzero")
        self.assertEqual(done.state.open_lots, ())
        _margin_invariant(config, done.state)

    def test_totals_form_matches_verified_formula(self) -> None:
        config = _config(risk_tiers=(TIER_ZERO,), lower_price="20000", upper_price="30000",
                         interval_count=1, investment_quote="100")
        state = apply_tick(create_grid(config), config, price="25000", time_us=100).state
        self.assertEqual(len(state.open_lots), 1)
        lot = state.open_lots[0]
        wallet_total = number(state.wallet_free) + sum(
            (number(v) for v in state.locked_margin), Q(0)
        ) + number(lot.locked_margin)
        venue = project_isolated_liquidation(
            "LONG", lot.quantity, "1", lot.entry_price,
            IsolatedMarginSnapshot(
                settlement_asset="USDT",
                isolated_wallet=exact_text(wallet_total),
                mark_price="25000",
                captured_at_us=100,
            ),
            TIER_ZERO,
        )
        self.assertEqual(venue.status, "ESTIMATE_ONLY")
        self.assertEqual(state.liq_estimate_price, venue.liquidation_price)
        self.assertEqual(state.liq_estimate_tier, venue.tier_id)


class FuturesGridSnapshotTest(unittest.TestCase):
    def test_round_trip_continues_identically(self) -> None:
        config = _config()
        state = apply_tick(create_grid(config), config, price="25000", time_us=100).state
        state = apply_tick(state, config, price="24000", time_us=200).state
        restored = restore_grid(snapshot_grid(state), config)
        self.assertEqual(restored, state)
        live = apply_tick(state, config, price="26000", time_us=300).state
        resumed = apply_tick(restored, config, price="26000", time_us=300).state
        self.assertEqual(resumed, live)

    def test_rejects_foreign_config_and_shape(self) -> None:
        config = _config()
        snapshot = snapshot_grid(create_grid(config))
        with self.assertRaises(FuturesGridEngineError) as ctx:
            restore_grid(snapshot, _config(investment_quote="2000"))
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_CONFIG_MISMATCH")
        snapshot["pending"] = ["BUY"]
        with self.assertRaises(FuturesGridEngineError) as ctx:
            restore_grid(snapshot, config)
        self.assertEqual(ctx.exception.code, "FUTURES_GRID_SNAPSHOT_INVALID")

    def test_describe_grid_preview(self) -> None:
        summary = describe_grid(_config())
        self.assertEqual(summary["direction"], "LONG")
        self.assertEqual(summary["leverage"], 5)
        self.assertEqual(summary["engine_revision"], "G3a.1")


if __name__ == "__main__":
    unittest.main()
