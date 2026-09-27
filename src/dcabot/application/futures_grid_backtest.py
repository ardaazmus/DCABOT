"""Futures grid backtest: futures-grid engine over closed venue klines.

Mirrors the spot grid backtest loop (intrabar path open → high → low →
close, fills at level prices) with two futures additions: venue funding
history is applied as explicit engine funding events, and leverage /
direction flow into the config. Liquidation is NOT estimated here:
risk tiers need credentials, so the run stays tier-free and says so in
the assumptions instead of inventing a margin schedule.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from time import monotonic

from dcabot.application.equity_curve_scores import annualized_sharpe_ratio
from dcabot.application.futures_grid_engine import (
    FuturesGridConfig,
    FuturesGridDirection,
    FuturesGridEngineError,
    FuturesGridMode,
    FuturesGridStatus,
    apply_funding,
    apply_tick,
    create_grid,
    grid_equity_quote,
)
from dcabot.application.grid_backtest import MAX_GRID_BACKTEST_BARS
from dcabot.application.sector_backtest import BACKTEST_TIMEOUT_SECONDS
from dcabot.data_adapters.binance_futures_public_transport import (
    BinanceFuturesFundingRate,
    BinanceFuturesSymbolRules,
)
from dcabot.data_adapters.binance_public_transport import BinancePublicKline
from dcabot.domain.numbers import exact_text, number, text

PERCENT_PLACES = 4
_YEAR_US = 365 * 24 * 3_600_000_000


class FuturesGridBacktestError(ValueError):
    """Raised when futures grid backtest input or venue state is unsafe."""

    def __init__(self, code: str, message: str, field: str | None = None) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.field = field


@dataclass(frozen=True, slots=True)
class FuturesGridBacktestParams:
    """Validated futures grid backtest request (venue grounding happens at run)."""

    symbol: str
    direction: FuturesGridDirection
    mode: FuturesGridMode
    lower_price: str
    upper_price: str
    interval_count: int
    investment_quote: str
    leverage: int
    fee_rate: str
    stop_loss_price: str | None
    take_profit_pct: str | None
    trailing_up_pct: str | None
    trailing_down_pct: str | None


def _decimal(raw: object, field: str, code: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise FuturesGridBacktestError(code, "Decimal string olmalıdır.", field=field)
    try:
        value = number(raw)
    except ValueError as error:
        raise FuturesGridBacktestError(code, "Decimal string olmalıdır.", field=field) from error
    if value < 0:
        raise FuturesGridBacktestError(code, "Negatif olamaz.", field=field)
    return raw


def _optional_decimal(raw: object, field: str, code: str) -> str | None:
    if raw is None:
        return None
    return _decimal(raw, field, code)


def parse_futures_grid_backtest(raw: dict) -> FuturesGridBacktestParams:
    """Validate the futures grid backtest body shape; engine checks run later."""
    if not isinstance(raw, dict):
        raise FuturesGridBacktestError("FGRID_BODY_INVALID", "Gövde geçersiz.", field="strategy")
    symbol = raw.get("symbol")
    if not isinstance(symbol, str) or not symbol or len(symbol) > 20:
        raise FuturesGridBacktestError("FGRID_SYMBOL_INVALID", "Sembol geçersiz.", field="strategy.symbol")
    direction_raw = raw.get("direction", "LONG")
    try:
        direction = FuturesGridDirection(str(direction_raw))
    except ValueError as error:
        raise FuturesGridBacktestError(
            "FGRID_DIRECTION_INVALID", "Yön geçersiz.", field="strategy.direction"
        ) from error
    mode_raw = raw.get("mode", "ARITHMETIC")
    try:
        mode = FuturesGridMode(str(mode_raw))
    except ValueError as error:
        raise FuturesGridBacktestError("FGRID_MODE_INVALID", "Mod geçersiz.", field="strategy.mode") from error
    count = raw.get("interval_count")
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 1000:
        raise FuturesGridBacktestError(
            "FGRID_INTERVAL_INVALID", "Aralık sayısı 1-1000 olmalıdır.", field="strategy.interval_count"
        )
    leverage = raw.get("leverage", 1)
    if isinstance(leverage, bool) or not isinstance(leverage, int) or not 1 <= leverage <= 10:
        raise FuturesGridBacktestError(
            "FGRID_LEVERAGE_INVALID", "Kaldıraç 1-10 tamsayı olmalıdır.", field="strategy.leverage"
        )
    return FuturesGridBacktestParams(
        symbol=symbol,
        direction=direction,
        mode=mode,
        lower_price=_decimal(raw.get("lower_price"), "strategy.lower_price", "FGRID_PRICE_INVALID"),
        upper_price=_decimal(raw.get("upper_price"), "strategy.upper_price", "FGRID_PRICE_INVALID"),
        interval_count=count,
        investment_quote=_decimal(raw.get("investment"), "investment", "FGRID_INVESTMENT_INVALID"),
        leverage=leverage,
        fee_rate=_decimal(raw.get("fee_rate", "0.0005"), "strategy.fee_rate", "FGRID_FEE_INVALID"),
        stop_loss_price=_optional_decimal(
            raw.get("stop_loss_price"), "strategy.stop_loss_price", "FGRID_SL_INVALID"
        ),
        take_profit_pct=_optional_decimal(
            raw.get("take_profit_pct"), "strategy.take_profit_pct", "FGRID_TP_INVALID"
        ),
        trailing_up_pct=_optional_decimal(
            raw.get("trailing_up_pct"), "strategy.trailing_up_pct", "FGRID_TRAIL_INVALID"
        ),
        trailing_down_pct=_optional_decimal(
            raw.get("trailing_down_pct"), "strategy.trailing_down_pct", "FGRID_TRAIL_INVALID"
        ),
    )


def _percent(value: Fraction) -> str:
    return text(value * 100, PERCENT_PLACES)


def _month(time_us: int) -> str:
    return datetime.fromtimestamp(time_us / 1_000_000, tz=timezone.utc).strftime("%Y-%m")


def _is_month_start(time_us: int) -> bool:
    moment = datetime.fromtimestamp(time_us / 1_000_000, tz=timezone.utc)
    return (moment.day, moment.hour, moment.minute, moment.second, moment.microsecond) == (1, 0, 0, 0, 0)


def _engine_error(error: FuturesGridEngineError) -> FuturesGridBacktestError:
    return FuturesGridBacktestError(error.code, str(error).split(": ", 1)[-1], field="strategy")


def run_futures_grid_backtest(
    params: FuturesGridBacktestParams,
    *,
    rules: BinanceFuturesSymbolRules,
    interval: str,
    interval_us: int,
    bars: tuple[BinancePublicKline, ...],
    funding: tuple[BinanceFuturesFundingRate, ...] = (),
) -> dict:
    """Run the futures grid engine over closed bars; pure except the timeout clock."""
    if not 2 <= len(bars) <= MAX_GRID_BACKTEST_BARS:
        raise FuturesGridBacktestError("BACKTEST_BARS_INVALID", "Backtest en az 2, en fazla 20.000 mum ister.")
    if rules.status != "TRADING":
        raise FuturesGridBacktestError("FGRID_SYMBOL_HALTED", "Sembol işlemde değil.", field="strategy.symbol")
    if rules.contract_type != "PERPETUAL":
        raise FuturesGridBacktestError(
            "FGRID_CONTRACT_UNSUPPORTED", "Yalnız USDT-M perpetual desteklenir.", field="strategy.symbol"
        )
    if rules.quote_asset != "USDT":
        raise FuturesGridBacktestError(
            "FGRID_SETTLEMENT_UNSUPPORTED", "Yalnız USDT-M profili desteklenir.", field="strategy.symbol"
        )
    try:
        config = FuturesGridConfig(
            base_asset=rules.base_asset,
            quote_asset=rules.quote_asset,
            direction=params.direction,
            mode=params.mode,
            lower_price=params.lower_price,
            upper_price=params.upper_price,
            interval_count=params.interval_count,
            investment_quote=params.investment_quote,
            leverage=params.leverage,
            base_step_size=rules.qty_step,
            fee_rate=params.fee_rate,
            price_tick=rules.tick if params.mode is FuturesGridMode.GEOMETRIC else None,
            tick_origin="0" if params.mode is FuturesGridMode.GEOMETRIC else None,
            stop_loss_price=params.stop_loss_price,
            take_profit_pct=params.take_profit_pct,
            trailing_up_pct=params.trailing_up_pct,
            trailing_down_pct=params.trailing_down_pct,
        )
    except FuturesGridEngineError as error:
        raise _engine_error(error) from error
    notional_per_grid = number(config.quote_per_grid) * params.leverage
    if notional_per_grid < number(rules.min_notional):
        raise FuturesGridBacktestError(
            "FGRID_MIN_NOTIONAL_TOO_SMALL",
            f"Grid başına notional ({exact_text(notional_per_grid)}) min notional ({rules.min_notional}) altında.",
            field="strategy",
        )

    investment = number(config.investment_quote)
    state = create_grid(config)
    equity: list[Fraction] = []
    equity_times: list[int] = []
    processed = 0
    stopped_at_us: int | None = None
    funding_index = 0
    funding_applied = 0
    deadline = monotonic() + BACKTEST_TIMEOUT_SECONDS
    terminal = (
        FuturesGridStatus.DONE_SL,
        FuturesGridStatus.DONE_TP,
        FuturesGridStatus.DONE_LIQ_ESTIMATE,
    )
    for bar in bars:
        if monotonic() > deadline:
            raise FuturesGridBacktestError("BACKTEST_TIMEOUT", "Backtest zaman aşımına uğradı.")
        span = max(bar.close_time_us - bar.open_time_us, 3)
        ticks = (
            (bar.open, bar.open_time_us),
            (bar.high, bar.open_time_us + span // 3),
            (bar.low, bar.open_time_us + 2 * span // 3),
            (bar.close, bar.close_time_us),
        )
        try:
            for price, time_us in ticks:
                result = apply_tick(state, config, price=price, time_us=time_us)
                state = result.state
                if state.status in terminal:
                    break
            while funding_index < len(funding) and funding[funding_index].funding_time_us <= bar.close_time_us:
                record = funding[funding_index]
                funding_index += 1
                if record.funding_time_us < bars[0].open_time_us:
                    continue
                # Bar-close attribution: the venue timestamp stays in the
                # event id, but the engine time is the containing bar's
                # close so tick/funding order stays monotonic.
                state = apply_funding(
                    state,
                    config,
                    rate=record.rate,
                    mark_price=bar.close,
                    time_us=bar.close_time_us,
                    event_id=f"venue:{record.funding_time_us}",
                )
                funding_applied += 1
        except FuturesGridEngineError as error:
            raise _engine_error(error) from error
        processed += 1
        equity.append(number(grid_equity_quote(state, config, mark_price=bar.close)))
        equity_times.append(bar.close_time_us)
        if state.status in terminal:
            stopped_at_us = bar.close_time_us
            break

    if state.status is FuturesGridStatus.DONE_SL:
        status = "STOPPED_SL"
    elif state.status is FuturesGridStatus.DONE_TP:
        status = "STOPPED_TP"
    elif state.status is FuturesGridStatus.DONE_LIQ_ESTIMATE:
        status = "STOPPED_LIQ_ESTIMATE"
    elif state.status is FuturesGridStatus.WAIT:
        status = "NEVER_ENTERED"
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
        "direction": params.direction.value,
        "leverage": params.leverage,
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
            "fills_count": len(state.fills),
            "max_drawdown_percent": _percent(max_drawdown),
            "total_fees": exact_text(number(state.fees_paid_quote)),
            "funding_cashflow": exact_text(number(state.funding_cashflow)),
            "funding_events_applied": funding_applied,
            "realized_gross_pnl": exact_text(number(state.realized_gross_pnl)),
            "trailing_shifts": state.trailing_shifts,
            "grid_status": state.status.value,
            "entry_price": state.entry_price,
            "liq_estimate_price": state.liq_estimate_price,
            "sharpe_ratio_annualized": annualized_sharpe_ratio(
                tuple(exact_text(value) for value in equity), bars_per_year=_YEAR_US // interval_us
            ),
        },
        "levels": list(state.levels),
        "equity_curve": [{"time_us": t, "equity": exact_text(v)} for t, v in zip(equity_times, equity)],
        "drawdown_curve": drawdown_curve,
        "monthly_returns": monthly,
        "assumptions": [
            "CURRENT_FUTURES_RULES",
            "OHLC_INTRABAR_PATH",
            "LEVEL_PRICE_FILLS",
            "FLAT_FEE_RATE",
            "FUNDING_VENUE_HISTORY",
            "FUNDING_AT_BAR_CLOSE",
            "USDT_M_ISOLATED_ONEWAY",
            "MARK_TRADE_BASIS_NOT_MODELED",
            "LIQ_ESTIMATE_DISABLED_NO_TIERS",
        ],
    }
