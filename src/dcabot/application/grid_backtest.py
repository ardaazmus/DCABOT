"""Grid backtest: spot-grid engine over closed venue klines.

Each closed bar feeds the engine the intrabar path open → high → low →
close; fills happen at level prices per the engine contract. Venue
quantization (qty step, price tick) and the minimum notional come from
current symbol rules and are recorded in the assumptions.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from time import monotonic

from dcabot.application.equity_curve_scores import annualized_sharpe_ratio
from dcabot.application.historical_simulation import MAX_SECTOR_BACKTEST_BARS
from dcabot.application.sector_backtest import BACKTEST_TIMEOUT_SECONDS
from dcabot.application.sector_dca import SymbolRules
from dcabot.application.spot_grid_cycle_accounting import SpotGridFeeProfile
from dcabot.application.spot_grid_engine import (
    SpotGridConfig,
    SpotGridEngineError,
    SpotGridMode,
    SpotGridStatus,
    apply_tick,
    create_grid,
    grid_equity_quote,
)
from dcabot.data_adapters.binance_public_transport import BinancePublicKline
from dcabot.domain.numbers import exact_text, number, text

MAX_GRID_BACKTEST_BARS = MAX_SECTOR_BACKTEST_BARS

PERCENT_PLACES = 4
_FEE_REVISION = "grid-backtest-1"
_YEAR_US = 365 * 24 * 3_600_000_000


class GridBacktestError(ValueError):
    """Raised when grid backtest input or venue state is unsafe."""

    def __init__(self, code: str, message: str, field: str | None = None) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.field = field


@dataclass(frozen=True, slots=True)
class GridBacktestParams:
    """Validated grid backtest request (venue grounding happens at run)."""

    symbol: str
    mode: SpotGridMode
    lower_price: str
    upper_price: str
    interval_count: int
    investment_quote: str
    fee_rate: str
    stop_loss_price: str | None
    take_profit_pct: str | None
    trailing_up_pct: str | None
    trailing_down_pct: str | None


def _decimal(raw: object, field: str, code: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise GridBacktestError(code, "Decimal string olmalıdır.", field=field)
    try:
        value = number(raw)
    except ValueError as error:
        raise GridBacktestError(code, "Decimal string olmalıdır.", field=field) from error
    if value < 0:
        raise GridBacktestError(code, "Negatif olamaz.", field=field)
    return raw


def _optional_decimal(raw: object, field: str, code: str) -> str | None:
    if raw is None:
        return None
    return _decimal(raw, field, code)


def parse_grid_backtest(raw: dict) -> GridBacktestParams:
    """Validate the grid backtest body shape; engine checks run later."""
    if not isinstance(raw, dict):
        raise GridBacktestError("GRID_BODY_INVALID", "Gövde geçersiz.", field="strategy")
    symbol = raw.get("symbol")
    if not isinstance(symbol, str) or not symbol or len(symbol) > 20:
        raise GridBacktestError("GRID_SYMBOL_INVALID", "Sembol geçersiz.", field="strategy.symbol")
    mode_raw = raw.get("mode", "ARITHMETIC")
    try:
        mode = SpotGridMode(str(mode_raw))
    except ValueError as error:
        raise GridBacktestError("GRID_MODE_INVALID", "Mod geçersiz.", field="strategy.mode") from error
    count = raw.get("interval_count")
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 1000:
        raise GridBacktestError(
            "GRID_INTERVAL_INVALID", "Aralık sayısı 1-1000 olmalıdır.", field="strategy.interval_count"
        )
    return GridBacktestParams(
        symbol=symbol,
        mode=mode,
        lower_price=_decimal(raw.get("lower_price"), "strategy.lower_price", "GRID_PRICE_INVALID"),
        upper_price=_decimal(raw.get("upper_price"), "strategy.upper_price", "GRID_PRICE_INVALID"),
        interval_count=count,
        investment_quote=_decimal(raw.get("investment"), "investment", "GRID_INVESTMENT_INVALID"),
        fee_rate=_decimal(raw.get("fee_rate", "0.001"), "strategy.fee_rate", "GRID_FEE_INVALID"),
        stop_loss_price=_optional_decimal(raw.get("stop_loss_price"), "strategy.stop_loss_price", "GRID_SL_INVALID"),
        take_profit_pct=_optional_decimal(
            raw.get("take_profit_pct"), "strategy.take_profit_pct", "GRID_TP_INVALID"
        ),
        trailing_up_pct=_optional_decimal(
            raw.get("trailing_up_pct"), "strategy.trailing_up_pct", "GRID_TRAIL_INVALID"
        ),
        trailing_down_pct=_optional_decimal(
            raw.get("trailing_down_pct"), "strategy.trailing_down_pct", "GRID_TRAIL_INVALID"
        ),
    )


def _percent(value: Fraction) -> str:
    return text(value * 100, PERCENT_PLACES)


def _month(time_us: int) -> str:
    return datetime.fromtimestamp(time_us / 1_000_000, tz=timezone.utc).strftime("%Y-%m")


def _is_month_start(time_us: int) -> bool:
    moment = datetime.fromtimestamp(time_us / 1_000_000, tz=timezone.utc)
    return (moment.day, moment.hour, moment.minute, moment.second, moment.microsecond) == (1, 0, 0, 0, 0)


def run_grid_backtest(
    params: GridBacktestParams,
    *,
    rules: SymbolRules,
    interval: str,
    interval_us: int,
    bars: tuple[BinancePublicKline, ...],
) -> dict:
    """Run the grid engine over closed bars; pure except the timeout clock."""
    if not 2 <= len(bars) <= MAX_GRID_BACKTEST_BARS:
        raise GridBacktestError("BACKTEST_BARS_INVALID", "Backtest en az 2, en fazla 20.000 mum ister.")
    if rules.status != "TRADING":
        raise GridBacktestError("GRID_SYMBOL_HALTED", "Sembol işlemde değil.", field="strategy.symbol")
    try:
        fee_rate = number(params.fee_rate)
        if not 0 <= fee_rate < 1:
            raise GridBacktestError("GRID_FEE_INVALID", "Fee 0-1 aralığında olmalıdır.", field="strategy.fee_rate")
        profile = SpotGridFeeProfile(
            fee_asset=rules.quote_asset,
            fee_rate=params.fee_rate,
            fee_quantum="0",
            profile_revision=_FEE_REVISION,
        )
        config = SpotGridConfig(
            base_asset=rules.base_asset,
            quote_asset=rules.quote_asset,
            mode=params.mode,
            lower_price=params.lower_price,
            upper_price=params.upper_price,
            interval_count=params.interval_count,
            investment_quote=params.investment_quote,
            base_step_size=rules.qty_step,
            fee_profile=profile,
            price_tick=rules.tick if params.mode is SpotGridMode.GEOMETRIC else None,
            tick_origin="0" if params.mode is SpotGridMode.GEOMETRIC else None,
            stop_loss_price=params.stop_loss_price,
            take_profit_pct=params.take_profit_pct,
            trailing_up_pct=params.trailing_up_pct,
            trailing_down_pct=params.trailing_down_pct,
        )
    except SpotGridEngineError as error:
        raise GridBacktestError(error.code, str(error).split(": ", 1)[-1], field="strategy") from error
    if number(config.quote_per_grid) < number(rules.min_notional):
        raise GridBacktestError(
            "GRID_MIN_NOTIONAL_TOO_SMALL",
            f"Grid başına ({config.quote_per_grid}) min notional ({rules.min_notional}) altında.",
            field="strategy",
        )

    investment = number(config.investment_quote)
    state = create_grid(config)
    equity: list[Fraction] = []
    equity_times: list[int] = []
    processed = 0
    stopped_at_us: int | None = None
    deadline = monotonic() + BACKTEST_TIMEOUT_SECONDS
    for bar in bars:
        if monotonic() > deadline:
            raise GridBacktestError("BACKTEST_TIMEOUT", "Backtest zaman aşımına uğradı.")
        for tick in (bar.open, bar.high, bar.low, bar.close):
            result = apply_tick(state, config, price=tick)
            state = result.state
            if state.status in (SpotGridStatus.DONE_SL, SpotGridStatus.DONE_TP):
                break
        processed += 1
        equity.append(number(grid_equity_quote(state, mark_price=bar.close)))
        equity_times.append(bar.close_time_us)
        if state.status in (SpotGridStatus.DONE_SL, SpotGridStatus.DONE_TP):
            stopped_at_us = bar.close_time_us
            break

    if state.status is SpotGridStatus.DONE_SL:
        status = "STOPPED_SL"
    elif state.status is SpotGridStatus.DONE_TP:
        status = "STOPPED_TP"
    elif state.status is SpotGridStatus.WAIT:
        status = "NEVER_ENTERED"
        # Capital never entered the grid; it rests as undeployed cash.
        equity = [investment for _ in equity]
    else:
        status = "COMPLETED"
    net_profit = equity[-1] - investment
    period_us = bars[-1].close_time_us - bars[0].open_time_us
    peak = equity[0]
    drawdown_curve = []
    max_drawdown = Fraction(0)
    for time_us, value in zip(equity_times, equity):
        peak = max(peak, value)
        drawdown = (peak - value) / peak if peak > 0 else Fraction(0)
        max_drawdown = max(max_drawdown, drawdown)
        drawdown_curve.append({"time_us": time_us, "drawdown_percent": _percent(drawdown)})
    monthly = []
    month_start_equity = investment
    month_start = bars[0].open_time_us
    for index, (time_us, value) in enumerate(zip(equity_times, equity)):
        last = index == len(equity) - 1
        boundary = last or _is_month_start(equity_times[index + 1] + 1)
        if boundary:
            complete = _is_month_start(month_start) and (last or _is_month_start(time_us + 1))
            monthly.append(
                {
                    "month": _month(month_start),
                    "return_percent": _percent((value - month_start_equity) / month_start_equity),
                    "complete": bool(complete),
                }
            )
            if not last:
                month_start_equity = value
                month_start = time_us + 1
    return {
        "symbol": params.symbol,
        "interval": interval,
        "period_start_us": bars[0].open_time_us,
        "period_end_us": bars[-1].close_time_us,
        "bar_count": len(bars),
        "processed_bar_count": processed,
        "status": status,
        "stopped_at_us": stopped_at_us,
        "investment": exact_text(investment),
        "summary": {
            "net_profit": exact_text(net_profit),
            "roi_percent": _percent(net_profit / investment),
            "annualized_roi_percent": _percent(net_profit / investment * _YEAR_US / period_us)
            if period_us > 0
            else "0",
            "final_equity": exact_text(equity[-1]),
            "cycles_closed": state.cycles_closed,
            "fills_count": len(state.inventory.fills),
            "max_drawdown_percent": _percent(max_drawdown),
            "total_fees": exact_text(number(state.fees_paid_quote)),
            "grid_status": state.status.value,
            "entry_price": state.entry_price,
            "sharpe_ratio_annualized": annualized_sharpe_ratio(
                tuple(exact_text(value) for value in equity), bars_per_year=_YEAR_US // interval_us
            ),
        },
        "levels": list(state.levels),
        "equity_curve": [{"time_us": t, "equity": exact_text(v)} for t, v in zip(equity_times, equity)],
        "drawdown_curve": drawdown_curve,
        "monthly_returns": monthly,
        "assumptions": [
            "CURRENT_VENUE_RULES",
            "OHLC_INTRABAR_PATH",
            "LEVEL_PRICE_FILLS",
            "QUOTE_FEES_EXACT",
            "FUNDING_NOT_MODELED",
        ],
    }
