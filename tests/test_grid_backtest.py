"""G2-b: grid backtest over closed klines — exact equity, exits, guards."""

import unittest

from dcabot.application.grid_backtest import (
    GridBacktestError,
    parse_grid_backtest,
    run_grid_backtest,
)
from dcabot.application.sector_dca import SymbolRules
from dcabot.data_adapters.binance_public_transport import BinancePublicKline

HOUR = 3_600_000_000
RULES = SymbolRules("BTCUSDT", "TRADING", "BTC", "USDT", "0.01", "0.00001", "0.00001", "5")


def _bar(index: int, o: str, h: str, low: str, c: str, start_us: int = 0) -> BinancePublicKline:
    return BinancePublicKline(
        start_us + index * HOUR, start_us + (index + 1) * HOUR - 1, o, h, low, c, "10"
    )


def _params(**overrides: object) -> dict:
    raw: dict[str, object] = {
        "symbol": "BTCUSDT",
        "mode": "ARITHMETIC",
        "lower_price": "20000",
        "upper_price": "30000",
        "interval_count": 10,
        "investment": "1000",
        "fee_rate": "0.001",
        "stop_loss_price": None,
        "take_profit_pct": None,
        "trailing_up_pct": None,
        "trailing_down_pct": None,
    }
    raw.update(overrides)
    return raw


class GridBacktestParseTest(unittest.TestCase):
    def test_defaults_and_modes(self) -> None:
        params = parse_grid_backtest(_params())
        self.assertEqual(params.symbol, "BTCUSDT")
        self.assertEqual(params.mode.value, "ARITHMETIC")
        self.assertEqual(parse_grid_backtest(_params(mode="GEOMETRIC")).mode.value, "GEOMETRIC")

    def test_rejects_bad_shape(self) -> None:
        with self.assertRaises(GridBacktestError) as ctx:
            parse_grid_backtest(_params(mode="INFINITY"))
        self.assertEqual(ctx.exception.code, "GRID_MODE_INVALID")
        with self.assertRaises(GridBacktestError) as ctx:
            parse_grid_backtest(_params(interval_count=0))
        self.assertEqual(ctx.exception.code, "GRID_INTERVAL_INVALID")
        with self.assertRaises(GridBacktestError) as ctx:
            parse_grid_backtest(_params(lower_price="-1"))
        self.assertEqual(ctx.exception.code, "GRID_PRICE_INVALID")


class GridBacktestRunTest(unittest.TestCase):
    def test_three_bar_walk_matches_hand_computation(self) -> None:
        bars = (
            _bar(0, "25000", "25100", "24900", "25000"),
            _bar(1, "25000", "26100", "25000", "26000"),
            _bar(2, "26000", "26100", "23900", "24000"),
        )
        result = run_grid_backtest(
            parse_grid_backtest(_params()), rules=RULES, interval="1h", interval_us=HOUR, bars=bars
        )
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["processed_bar_count"], 3)
        summary = result["summary"]
        self.assertEqual(summary["final_equity"], "987.84")
        self.assertEqual(summary["net_profit"], "-12.16")
        self.assertEqual(summary["cycles_closed"], 2)
        self.assertEqual(summary["fills_count"], 10)
        self.assertEqual(summary["total_fees"], "1.024")
        self.assertEqual(summary["grid_status"], "ACTIVE")
        self.assertEqual(summary["entry_price"], "25000")
        curve = [point["equity"] for point in result["equity_curve"]]
        self.assertEqual(curve, ["1000", "1024.16", "987.84"])
        self.assertEqual(len(result["levels"]), 11)
        self.assertIn("OHLC_INTRABAR_PATH", result["assumptions"])
        self.assertEqual(result["monthly_returns"][0]["month"], "1970-01")

    def test_never_entered_keeps_capital(self) -> None:
        bars = (
            _bar(0, "15000", "15100", "14900", "15000"),
            _bar(1, "15000", "15100", "14900", "15000"),
        )
        result = run_grid_backtest(
            parse_grid_backtest(_params()), rules=RULES, interval="1h", interval_us=HOUR, bars=bars
        )
        self.assertEqual(result["status"], "NEVER_ENTERED")
        self.assertEqual(result["summary"]["final_equity"], "1000")
        self.assertEqual(result["summary"]["net_profit"], "0")
        self.assertEqual(result["summary"]["fills_count"], 0)

    def test_stop_loss_stops_early(self) -> None:
        bars = (
            _bar(0, "25000", "25100", "24900", "25000"),
            _bar(1, "25000", "25000", "18900", "19000"),
            _bar(2, "19000", "19100", "18900", "19000"),
        )
        result = run_grid_backtest(
            parse_grid_backtest(_params(stop_loss_price="19000")),
            rules=RULES,
            interval="1h",
            interval_us=HOUR,
            bars=bars,
        )
        self.assertEqual(result["status"], "STOPPED_SL")
        self.assertEqual(result["processed_bar_count"], 2)
        self.assertIsNotNone(result["stopped_at_us"])
        self.assertEqual(result["summary"]["grid_status"], "DONE_SL")

    def test_rejects_below_min_notional(self) -> None:
        rules = SymbolRules("BTCUSDT", "TRADING", "BTC", "USDT", "0.01", "0.00001", "0.00001", "500")
        bars = (_bar(0, "25000", "25100", "24900", "25000"), _bar(1, "25000", "25100", "24900", "25000"))
        with self.assertRaises(GridBacktestError) as ctx:
            run_grid_backtest(
                parse_grid_backtest(_params()), rules=rules, interval="1h", interval_us=HOUR, bars=bars
            )
        self.assertEqual(ctx.exception.code, "GRID_MIN_NOTIONAL_TOO_SMALL")

    def test_rejects_halted_symbol(self) -> None:
        rules = SymbolRules("BTCUSDT", "HALT", "BTC", "USDT", "0.01", "0.00001", "0.00001", "5")
        bars = (_bar(0, "25000", "25100", "24900", "25000"), _bar(1, "25000", "25100", "24900", "25000"))
        with self.assertRaises(GridBacktestError) as ctx:
            run_grid_backtest(
                parse_grid_backtest(_params()), rules=rules, interval="1h", interval_us=HOUR, bars=bars
            )
        self.assertEqual(ctx.exception.code, "GRID_SYMBOL_HALTED")

    def test_geometric_run_uses_venue_tick(self) -> None:
        bars = (
            _bar(0, "105", "106", "104", "105"),
            _bar(1, "105", "112", "105", "111"),
            _bar(2, "111", "122", "111", "121"),
        )
        result = run_grid_backtest(
            parse_grid_backtest(
                _params(
                    mode="GEOMETRIC",
                    lower_price="100",
                    upper_price="121",
                    interval_count=2,
                    investment="300",
                )
            ),
            rules=RULES,
            interval="1h",
            interval_us=HOUR,
            bars=bars,
        )
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["levels"], ["100", "110", "121"])
        self.assertGreater(result["summary"]["fills_count"], 0)


if __name__ == "__main__":
    unittest.main()
