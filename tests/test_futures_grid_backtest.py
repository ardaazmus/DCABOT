"""G3-b: futures grid backtest — exact equity, funding, exits, guards."""

import unittest

from dcabot.application.futures_grid_backtest import (
    FuturesGridBacktestError,
    parse_futures_grid_backtest,
    run_futures_grid_backtest,
)
from dcabot.data_adapters.binance_futures_public_transport import (
    BinanceFuturesFundingRate,
    BinanceFuturesSymbolRules,
)
from dcabot.data_adapters.binance_public_transport import BinancePublicKline

HOUR = 3_600_000_000
RULES = BinanceFuturesSymbolRules(
    "BTCUSDT", "TRADING", "BTC", "USDT", "PERPETUAL", "0.1", "0.001", "0.001", "5"
)


def _bar(index: int, o: str, h: str, low: str, c: str, start_us: int = 0) -> BinancePublicKline:
    return BinancePublicKline(
        start_us + index * HOUR, start_us + (index + 1) * HOUR - 1, o, h, low, c, "10"
    )


def _params(**overrides: object) -> dict:
    raw: dict[str, object] = {
        "symbol": "BTCUSDT",
        "direction": "LONG",
        "mode": "ARITHMETIC",
        "lower_price": "90",
        "upper_price": "110",
        "interval_count": 2,
        "investment": "1000",
        "leverage": 1,
        "fee_rate": "0",
        "stop_loss_price": None,
        "take_profit_pct": None,
        "trailing_up_pct": None,
        "trailing_down_pct": None,
    }
    raw.update(overrides)
    return raw


class FuturesGridBacktestParseTest(unittest.TestCase):
    def test_defaults(self) -> None:
        params = parse_futures_grid_backtest(_params())
        self.assertEqual(params.direction.value, "LONG")
        self.assertEqual(params.leverage, 1)
        self.assertEqual(params.fee_rate, "0")
        short = parse_futures_grid_backtest(_params(direction="SHORT"))
        self.assertEqual(short.direction.value, "SHORT")

    def test_rejects_bad_shape(self) -> None:
        with self.assertRaises(FuturesGridBacktestError) as ctx:
            parse_futures_grid_backtest(_params(direction="BOTH"))
        self.assertEqual(ctx.exception.code, "FGRID_DIRECTION_INVALID")
        with self.assertRaises(FuturesGridBacktestError) as ctx:
            parse_futures_grid_backtest(_params(leverage=11))
        self.assertEqual(ctx.exception.code, "FGRID_LEVERAGE_INVALID")
        with self.assertRaises(FuturesGridBacktestError) as ctx:
            parse_futures_grid_backtest(_params(leverage=True))
        self.assertEqual(ctx.exception.code, "FGRID_LEVERAGE_INVALID")
        with self.assertRaises(FuturesGridBacktestError) as ctx:
            parse_futures_grid_backtest(_params(interval_count=0))
        self.assertEqual(ctx.exception.code, "FGRID_INTERVAL_INVALID")
        with self.assertRaises(FuturesGridBacktestError) as ctx:
            parse_futures_grid_backtest(_params(lower_price="-1"))
        self.assertEqual(ctx.exception.code, "FGRID_PRICE_INVALID")


class FuturesGridBacktestRunTest(unittest.TestCase):
    def _run(self, bars, **overrides):
        return run_futures_grid_backtest(
            parse_futures_grid_backtest(_params(**overrides)),
            rules=RULES,
            interval="1h",
            interval_us=HOUR,
            bars=bars,
        )

    def test_three_bar_walk_matches_hand_computation(self) -> None:
        bars = (
            _bar(0, "100", "100", "100", "100"),
            _bar(1, "100", "110", "100", "110"),
            _bar(2, "110", "110", "90", "90"),
        )
        result = self._run(bars)
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["direction"], "LONG")
        self.assertEqual(result["leverage"], 1)
        self.assertEqual(result["processed_bar_count"], 3)
        summary = result["summary"]
        self.assertEqual(summary["final_equity"], "1050")
        self.assertEqual(summary["net_profit"], "50")
        self.assertEqual(summary["cycles_closed"], 2)
        self.assertEqual(summary["fills_count"], 6)
        self.assertEqual(summary["total_fees"], "0")
        self.assertEqual(summary["funding_cashflow"], "0")
        self.assertEqual(summary["grid_status"], "ACTIVE")
        self.assertEqual(summary["entry_price"], "100")
        self.assertIsNone(summary["liq_estimate_price"])
        curve = [point["equity"] for point in result["equity_curve"]]
        self.assertEqual(curve, ["1000", "1100", "1050"])
        self.assertIn("FUNDING_VENUE_HISTORY", result["assumptions"])
        self.assertIn("LIQ_ESTIMATE_DISABLED_NO_TIERS", result["assumptions"])
        self.assertIn("MARK_TRADE_BASIS_NOT_MODELED", result["assumptions"])

    def test_funding_applied_at_bar_close_exact(self) -> None:
        bars = (
            _bar(0, "100", "100", "100", "100"),
            _bar(1, "100", "110", "100", "110"),
            _bar(2, "110", "110", "90", "90"),
        )
        funding = (
            BinanceFuturesFundingRate(funding_time_us=2 * HOUR + 1000, rate="0.0001"),
        )
        result = run_futures_grid_backtest(
            parse_futures_grid_backtest(_params()),
            rules=RULES,
            interval="1h",
            interval_us=HOUR,
            bars=bars,
            funding=funding,
        )
        summary = result["summary"]
        # Open lots at bar-2 close: 5 @100 and 5.555 @90; long pays.
        self.assertEqual(summary["funding_cashflow"], "-0.094995")
        self.assertEqual(summary["funding_events_applied"], 1)
        self.assertEqual(summary["final_equity"], "1049.905005")

    def test_funding_before_period_skipped(self) -> None:
        bars = (
            _bar(0, "100", "100", "100", "100"),
            _bar(1, "100", "110", "100", "110"),
        )
        funding = (BinanceFuturesFundingRate(funding_time_us=-1, rate="0.0001"),)
        result = run_futures_grid_backtest(
            parse_futures_grid_backtest(_params()),
            rules=RULES,
            interval="1h",
            interval_us=HOUR,
            bars=bars,
            funding=funding,
        )
        self.assertEqual(result["summary"]["funding_events_applied"], 0)

    def test_short_direction_completes(self) -> None:
        bars = (
            _bar(0, "100", "100", "100", "100"),
            _bar(1, "100", "100", "90", "90"),
        )
        result = self._run(bars, direction="SHORT")
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["direction"], "SHORT")
        self.assertGreater(len(result["equity_curve"]), 0)

    def test_stop_loss_flattens(self) -> None:
        bars = (
            _bar(0, "100", "100", "100", "100"),
            _bar(1, "100", "100", "80", "80"),
        )
        result = self._run(bars, stop_loss_price="85")
        self.assertEqual(result["status"], "STOPPED_SL")
        self.assertEqual(result["processed_bar_count"], 2)
        self.assertIsNotNone(result["stopped_at_us"])

    def test_never_entered_keeps_capital(self) -> None:
        bars = (
            _bar(0, "150", "151", "149", "150"),
            _bar(1, "150", "151", "149", "150"),
        )
        result = self._run(bars)
        self.assertEqual(result["status"], "NEVER_ENTERED")
        self.assertEqual(result["summary"]["final_equity"], "1000")
        self.assertEqual(result["summary"]["fills_count"], 0)

    def test_guards(self) -> None:
        bars = (
            _bar(0, "100", "100", "100", "100"),
            _bar(1, "100", "100", "100", "100"),
        )
        halted = BinanceFuturesSymbolRules(
            "BTCUSDT", "HALT", "BTC", "USDT", "PERPETUAL", "0.1", "0.001", "0.001", "5"
        )
        with self.assertRaises(FuturesGridBacktestError) as ctx:
            run_futures_grid_backtest(
                parse_futures_grid_backtest(_params()),
                rules=halted,
                interval="1h",
                interval_us=HOUR,
                bars=bars,
            )
        self.assertEqual(ctx.exception.code, "FGRID_SYMBOL_HALTED")
        quarterly = BinanceFuturesSymbolRules(
            "BTCUSDT", "TRADING", "BTC", "USDT", "CURRENT_QUARTER", "0.1", "0.001", "0.001", "5"
        )
        with self.assertRaises(FuturesGridBacktestError) as ctx:
            run_futures_grid_backtest(
                parse_futures_grid_backtest(_params()),
                rules=quarterly,
                interval="1h",
                interval_us=HOUR,
                bars=bars,
            )
        self.assertEqual(ctx.exception.code, "FGRID_CONTRACT_UNSUPPORTED")
        tiny = BinanceFuturesSymbolRules(
            "BTCUSDT", "TRADING", "BTC", "USDT", "PERPETUAL", "0.1", "0.001", "0.001", "50000"
        )
        with self.assertRaises(FuturesGridBacktestError) as ctx:
            run_futures_grid_backtest(
                parse_futures_grid_backtest(_params()),
                rules=tiny,
                interval="1h",
                interval_us=HOUR,
                bars=bars,
            )
        self.assertEqual(ctx.exception.code, "FGRID_MIN_NOTIONAL_TOO_SMALL")
        with self.assertRaises(FuturesGridBacktestError) as ctx:
            run_futures_grid_backtest(
                parse_futures_grid_backtest(_params()),
                rules=RULES,
                interval="1h",
                interval_us=HOUR,
                bars=bars[:1],
            )
        self.assertEqual(ctx.exception.code, "BACKTEST_BARS_INVALID")


if __name__ == "__main__":
    unittest.main()
