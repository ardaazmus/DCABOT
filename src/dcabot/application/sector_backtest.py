"""Sector-style DCA backtest over venue klines (Faz W, v2).

Runs the existing closed-bar simulator (`simulate_historical_ohlcv`, the same
engine the bots use) on a sector-parameter config and reports the result in
3Commas/Bitsgap/Pionex vocabulary. Every statistic is derived here with
exact Fraction arithmetic from the simulator's own actions, per-deal net
results and per-bar equity; only the Sharpe ratio (a statistic needing a
square root) crosses the float boundary through `equity_curve_scores`.
"""

import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction

from dcabot.application.equity_curve_scores import annualized_sharpe_ratio
from dcabot.application.historical_simulation import (
    MAX_SECTOR_BACKTEST_BARS,
    HistoricalSimulationError,
    simulate_historical_ohlcv,
)
from dcabot.application.sector_dca import SectorDcaError, SectorDcaParams, SymbolRules, derive_deal_config, summarize_deal_plan
from dcabot.data_adapters.binance_public_transport import BinancePublicKline
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.domain.config import Config
from dcabot.domain.numbers import exact_text, number, text

PERCENT_PLACES = 4
BACKTEST_TIMEOUT_SECONDS = 30.0
_YEAR_US = 365 * 24 * 3_600_000_000
_CLOSING_ROLES = ("EXIT", "STOP")


class SectorBacktestError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _percent(value: Fraction) -> str:
    return text(value * 100, PERCENT_PLACES)


def _month(time_us: int) -> str:
    return datetime.fromtimestamp(time_us / 1_000_000, tz=timezone.utc).strftime("%Y-%m")


def _is_month_start(time_us: int) -> bool:
    moment = datetime.fromtimestamp(time_us / 1_000_000, tz=timezone.utc)
    return (moment.day, moment.hour, moment.minute, moment.second, moment.microsecond) == (1, 0, 0, 0, 0)


def run_sector_backtest(
    params: SectorDcaParams,
    *,
    rules: SymbolRules,
    budget: Fraction,
    interval: str,
    interval_us: int,
    bars: tuple[BinancePublicKline, ...],
    template: dict,
) -> dict:
    if not 2 <= len(bars) <= MAX_SECTOR_BACKTEST_BARS:
        raise SectorBacktestError("BACKTEST_BARS_INVALID", "Backtest en az 2, en fazla 20.000 mum ister.")
    raw = derive_deal_config(
        params, rules=rules, reference_price=number(bars[0].open), budget=budget, template=template
    )
    plan = summarize_deal_plan(raw, number(bars[0].open))
    if not plan["within_budget"]:
        raise SectorDcaError(
            "SECTOR_BUDGET_TOO_LOW",
            f"Gereken sermaye ({plan['required_funds']} USDT) bütçeyi aşıyor.",
            field="budget",
        )
    config = Config.parse(raw)
    config_json = json.dumps(raw, sort_keys=True, separators=(",", ":"))
    config_hash = hashlib.sha256(config_json.encode("utf-8")).hexdigest()
    canonical = tuple(
        CanonicalBar(b.open_time_us, b.close_time_us, b.open, b.high, b.low, b.close, b.base_volume, True)
        for b in bars
    )
    data_hash = hashlib.sha256(
        json.dumps([[b.open_time_us, b.open, b.high, b.low, b.close] for b in bars], separators=(",", ":")).encode()
    ).hexdigest()
    dataset = HistoricalDatasetInput(
        HistoricalDatasetMetadata(
            dataset_id=f"binance-klines-{params.symbol.lower()}-{interval}",
            source_id="binance-spot-public-klines",
            symbol=params.symbol,
            interval=interval,
            period_start=str(bars[0].open_time_us),
            period_end=str(bars[-1].close_time_us),
            artifact_sha256=data_hash,
            artifact_bytes=0,
            timestamp_unit="MICROSECOND",
            timezone="UTC",
        ),
        canonical,
    )
    try:
        result = simulate_historical_ohlcv(
            dataset,
            config,
            config_hash=config_hash,
            timeout_seconds=BACKTEST_TIMEOUT_SECONDS,
            max_bars=MAX_SECTOR_BACKTEST_BARS,
        )
    except HistoricalSimulationError as exc:
        raise SectorBacktestError(exc.code, str(exc)) from exc

    summary = result.summary
    equity = [number(point) for point in summary["equity_curve"]]
    equity_times = [bars[i].close_time_us for i in range(len(equity))]
    deal_pnls = [number(value) for value in summary["deal_pnls"]]

    deals: dict[int, dict] = {}
    for action in result.actions:
        deal = deals.setdefault(
            action.deal_sequence,
            {
                "deal": action.deal_sequence, "started_at_us": None, "closed_at_us": None,
                "safety_orders_filled": 0, "profit": None,
                # Q1: trade-marker chart needs exact fill prices; pure
                # passthrough of the simulator's own fills, no recompute.
                "entry_price": None, "exit_price": None,
            },
        )
        if action.role == "BASE":
            deal["started_at_us"] = action.open_time_us
            deal["entry_price"] = action.fill_price
        elif action.role.startswith("SAFETY:"):
            deal["safety_orders_filled"] += 1
        elif action.role in _CLOSING_ROLES:
            deal["closed_at_us"] = action.open_time_us
            deal["exit_price"] = action.fill_price
    ordered = [deals[key] for key in sorted(deals)]
    closed = [deal for deal in ordered if deal["closed_at_us"] is not None]
    if len(closed) != len(deal_pnls):
        raise SectorBacktestError("BACKTEST_DEAL_MISMATCH", "Deal kayıtları simülatör sonucuyla eşleşmiyor.")
    for deal, pnl in zip(closed, deal_pnls):
        deal["profit"] = exact_text(pnl)

    wins = sum(1 for pnl in deal_pnls if pnl > 0)
    so_usage: dict[int, int] = {}
    for deal in closed:
        so_usage[deal["safety_orders_filled"]] = so_usage.get(deal["safety_orders_filled"], 0) + 1
    durations = [deal["closed_at_us"] - deal["started_at_us"] for deal in closed]

    peak = equity[0]
    drawdown_curve = []
    for time_us, value in zip(equity_times, equity):
        peak = max(peak, value)
        drawdown_curve.append({"time_us": time_us, "drawdown_percent": _percent((peak - value) / peak) if peak > 0 else "0"})

    # A month is "complete" only when the backtest covered it from its first
    # to its last moment; the first and last months are usually partial.
    monthly: list[dict] = []
    month_start_equity = budget
    first_month_complete = _is_month_start(bars[0].open_time_us)
    for index, (time_us, value) in enumerate(zip(equity_times, equity)):
        is_last = index == len(equity) - 1
        if is_last or _month(equity_times[index + 1]) != _month(time_us):
            complete = (first_month_complete or monthly) and (
                not is_last or (result.execution_status == "COMPLETED" and _is_month_start(time_us + 1))
            )
            monthly.append(
                {
                    "month": _month(time_us),
                    "return_percent": _percent((value - month_start_equity) / month_start_equity),
                    "complete": bool(complete),
                }
            )
            month_start_equity = value

    # Closed-deal net (fees included), the sector "net profit"; the open
    # deal's entry fees and unrealized result live in final_equity/open_deal.
    realized_net = sum(deal_pnls, Fraction(0))
    # Q1: profit factor mirrors the legacy run contract exactly
    # (gross_win/gross_loss over closed-deal nets, None when no loss).
    gross_win = sum((pnl for pnl in deal_pnls if pnl > 0), Fraction(0))
    gross_loss = sum((-pnl for pnl in deal_pnls if pnl < 0), Fraction(0))
    profit_factor = text(gross_win / gross_loss) if gross_loss > 0 else None
    open_deal = None
    if summary["position_status"] == "OPEN_AT_END":
        open_deal = {"unrealized": summary["unrealized"], "cost": summary["cost"], "qty": summary["qty"]}
    period_us = bars[-1].close_time_us + 1 - bars[0].open_time_us
    return {
        "symbol": params.symbol,
        "interval": interval,
        "period_start_us": bars[0].open_time_us,
        "period_end_us": bars[-1].close_time_us + 1,
        "bar_count": len(bars),
        "processed_bar_count": len(equity),
        "status": result.execution_status,
        "indeterminate_at_us": (
            bars[result.first_ambiguous_bar_index - 1].open_time_us
            if result.first_ambiguous_bar_index is not None
            else None
        ),
        "budget": exact_text(budget),
        "summary": {
            "net_profit": exact_text(realized_net),
            "roi_percent": _percent(realized_net / budget),
            "annualized_roi_percent": _percent(realized_net / budget * _YEAR_US / period_us),
            "final_equity": exact_text(equity[-1]),
            "deals_completed": len(closed),
            "winning_deals": wins,
            "win_rate_percent": _percent(Fraction(wins, len(closed))) if closed else None,
            "average_deal_profit": text(realized_net / len(closed), 8) if closed else None,
            "average_deal_duration_us": sum(durations) // len(durations) if durations else None,
            "max_safety_orders_used": max((d["safety_orders_filled"] for d in ordered), default=0),
            "max_drawdown_percent": _percent(number(summary["max_drawdown"])),
            "total_fees": summary["fees"],
            "profit_factor": profit_factor,
            "sharpe_ratio_annualized": annualized_sharpe_ratio(
                tuple(summary["equity_curve"]), bars_per_year=_YEAR_US // interval_us
            ),
        },
        "open_deal": open_deal,
        "deals": ordered,
        "safety_order_usage": [{"safety_orders_filled": k, "deals": so_usage[k]} for k in sorted(so_usage)],
        "equity_curve": [{"time_us": t, "equity": exact_text(v)} for t, v in zip(equity_times, equity)],
        # Q1: the trade chart's price substrate -- the very bars the run
        # consumed (venue close strings, zero recompute), over the same
        # processed window as the equity curve so markers always land.
        "price_curve": [{"time_us": bars[i].open_time_us, "close": bars[i].close} for i in range(len(equity))],
        "drawdown_curve": drawdown_curve,
        "monthly_returns": monthly,
        "assumptions": [
            "CURRENT_VENUE_RULES",
            "CLOSED_BAR_FILLS",
            "ONE_SAFETY_ORDER_PER_BAR",
            "FEES_FROM_PAPER_CONFIG",
            "FUNDING_NOT_MODELED",
        ],
    }
