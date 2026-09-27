"""Futures grid paper runner core (Faz G3-c): advance one bot over closed bars.

Pure and deterministic like the spot grid runner: given the persisted
grid runtime, the venue's newly closed 1m klines, and settled funding
intervals, it returns the next runtime plus the bot events to persist.
Each bar feeds the engine the O,H,L,C intrabar path with interpolated
bar times; funding due at or before a bar's close is applied right
after that bar's close tick (same bar-close attribution as backtests).
"""

from dataclasses import dataclass

from dcabot.application.futures_grid_engine import (
    FuturesGridConfig,
    FuturesGridDirection,
    FuturesGridEngineError,
    FuturesGridMode,
    FuturesGridStatus,
    apply_funding,
    apply_tick,
    create_grid,
    restore_grid,
    snapshot_grid,
)
from dcabot.application.paper_bot_runner import RUNNER_INTERVAL_US
from dcabot.data_adapters.binance_futures_public_transport import BinanceFuturesFundingRate
from dcabot.data_adapters.binance_public_transport import BinancePublicKline
from dcabot.domain.numbers import exact_text, number
from dcabot.persistence.bot_store import BotEvent, GridRuntime

_TERMINAL = (
    FuturesGridStatus.DONE_SL,
    FuturesGridStatus.DONE_TP,
    FuturesGridStatus.DONE_LIQ_ESTIMATE,
)
_LANDMARK_EVENTS = (
    "GRID_INIT",
    "GRID_STOP_LOSS",
    "GRID_TAKE_PROFIT",
    "GRID_LIQ_ESTIMATE_HIT",
    "GRID_TRAIL_UP",
    "GRID_TRAIL_DOWN",
)


@dataclass(frozen=True, slots=True)
class FuturesGridAdvance:
    runtime: GridRuntime
    events: tuple[BotEvent, ...]
    stopped_reason: str | None


def build_futures_grid_config(
    strategy: dict, rules, *, investment: str, enforce_min_notional: bool = True
) -> FuturesGridConfig:
    """Rebuild the tradable engine config from the bot strategy + venue rules."""

    if not isinstance(strategy, dict):
        raise FuturesGridEngineError("FUTURES_GRID_CONFIG_INVALID", "Grid stratejisi geçersiz.")
    try:
        direction = FuturesGridDirection(str(strategy.get("direction", "LONG")))
    except ValueError as error:
        raise FuturesGridEngineError("FUTURES_GRID_DIRECTION_INVALID", "Grid yönü geçersiz.") from error
    try:
        mode = FuturesGridMode(str(strategy.get("mode", "ARITHMETIC")))
    except ValueError as error:
        raise FuturesGridEngineError("FUTURES_GRID_MODE_INVALID", "Grid modu geçersiz.") from error
    leverage = strategy.get("leverage", 1)
    if isinstance(leverage, bool) or not isinstance(leverage, int):
        raise FuturesGridEngineError("FUTURES_GRID_LEVERAGE_INVALID", "Kaldıraç tamsayı olmalıdır.")
    config = FuturesGridConfig(
        base_asset=rules.base_asset,
        quote_asset=rules.quote_asset,
        direction=direction,
        mode=mode,
        lower_price=str(strategy["lower_price"]),
        upper_price=str(strategy["upper_price"]),
        interval_count=int(strategy["interval_count"]),
        investment_quote=investment,
        leverage=leverage,
        base_step_size=rules.qty_step,
        fee_rate=str(strategy.get("fee_rate", "0.0005")),
        price_tick=rules.tick if mode is FuturesGridMode.GEOMETRIC else None,
        tick_origin="0" if mode is FuturesGridMode.GEOMETRIC else None,
        stop_loss_price=strategy.get("stop_loss_price"),
        take_profit_pct=strategy.get("take_profit_pct"),
        trailing_up_pct=strategy.get("trailing_up_pct"),
        trailing_down_pct=strategy.get("trailing_down_pct"),
    )
    if enforce_min_notional and number(config.quote_per_grid) * leverage < number(rules.min_notional):
        raise FuturesGridEngineError(
            "FGRID_MIN_NOTIONAL_TOO_SMALL",
            f"Grid başına notional min notional ({rules.min_notional}) altında.",
        )
    return config


def futures_config_to_dict(config: FuturesGridConfig) -> dict:
    """Freeze the engine config into the runtime row (rebuilt on advance)."""

    return {
        "market": "FUTURES",
        "base_asset": config.base_asset,
        "quote_asset": config.quote_asset,
        "direction": config.direction.value,
        "mode": config.mode.value,
        "lower_price": config.lower_price,
        "upper_price": config.upper_price,
        "interval_count": config.interval_count,
        "investment_quote": config.investment_quote,
        "leverage": config.leverage,
        "base_step_size": config.base_step_size,
        "fee_rate": config.fee_rate,
        "price_tick": config.price_tick,
        "tick_origin": config.tick_origin,
        "stop_loss_price": config.stop_loss_price,
        "take_profit_pct": config.take_profit_pct,
        "trailing_up_pct": config.trailing_up_pct,
        "trailing_down_pct": config.trailing_down_pct,
        "fingerprint": config.fingerprint,
    }


def futures_config_from_dict(raw: dict) -> FuturesGridConfig:
    """Thaw a runtime row back into the validated engine config."""

    if not isinstance(raw, dict) or raw.get("market") != "FUTURES":
        raise FuturesGridEngineError("FUTURES_GRID_CONFIG_INVALID", "Grid config satırı geçersiz.")
    try:
        config = FuturesGridConfig(
            base_asset=str(raw["base_asset"]),
            quote_asset=str(raw["quote_asset"]),
            direction=FuturesGridDirection(str(raw["direction"])),
            mode=FuturesGridMode(str(raw["mode"])),
            lower_price=str(raw["lower_price"]),
            upper_price=str(raw["upper_price"]),
            interval_count=int(raw["interval_count"]),
            investment_quote=str(raw["investment_quote"]),
            leverage=int(raw["leverage"]),
            base_step_size=str(raw["base_step_size"]),
            fee_rate=str(raw["fee_rate"]),
            price_tick=raw.get("price_tick"),
            tick_origin=raw.get("tick_origin"),
            stop_loss_price=raw.get("stop_loss_price"),
            take_profit_pct=raw.get("take_profit_pct"),
            trailing_up_pct=raw.get("trailing_up_pct"),
            trailing_down_pct=raw.get("trailing_down_pct"),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise FuturesGridEngineError("FUTURES_GRID_CONFIG_INVALID", "Grid config satırı geçersiz.") from error
    if config.fingerprint != raw.get("fingerprint"):
        raise FuturesGridEngineError("FUTURES_GRID_CONFIG_MISMATCH", "Grid config parmak izi uyuşmuyor.")
    return config


def prepare_futures_grid_runtime(
    bot_id: str,
    strategy: dict,
    rules,
    *,
    investment: str,
    now_us: int,
) -> GridRuntime:
    """Create the first grid runtime: validated config plus WAIT snapshot."""

    config = build_futures_grid_config(strategy, rules, investment=investment)
    current_bar_open = now_us // RUNNER_INTERVAL_US * RUNNER_INTERVAL_US
    return GridRuntime(
        bot_id=bot_id,
        config=futures_config_to_dict(config),
        snapshot=snapshot_grid(create_grid(config)),
        last_bar_open_us=current_bar_open,
        updated_at_us=now_us,
    )


def advance_futures_grid(
    runtime: GridRuntime,
    klines: tuple[BinancePublicKline, ...],
    funding: tuple[BinanceFuturesFundingRate, ...],
    *,
    now_us: int,
) -> FuturesGridAdvance:
    """Apply every kline newer than `runtime.last_bar_open_us`, oldest first."""

    config = futures_config_from_dict(runtime.config)
    state = restore_grid(runtime.snapshot, config)
    last_open = runtime.last_bar_open_us
    events: list[BotEvent] = []
    funding_index = 0
    for kline in klines:
        if kline.open_time_us <= last_open:
            continue
        span = max(kline.close_time_us - kline.open_time_us, 3)
        ticks = (
            (kline.open, kline.open_time_us),
            (kline.high, kline.open_time_us + span // 3),
            (kline.low, kline.open_time_us + 2 * span // 3),
            (kline.close, kline.close_time_us),
        )
        for price, time_us in ticks:
            result = apply_tick(state, config, price=price, time_us=time_us)
            state = result.state
            for fill in result.fills:
                events.append(
                    BotEvent(
                        runtime.bot_id,
                        kline.open_time_us,
                        "GRID_FILL",
                        {
                            "fill_id": fill.fill_id,
                            "side": fill.side.value,
                            "price": fill.price,
                            "qty": fill.quantity,
                        },
                    )
                )
            for name in result.events:
                if name in _LANDMARK_EVENTS:
                    events.append(BotEvent(runtime.bot_id, kline.open_time_us, name, {}))
            if state.status in _TERMINAL:
                break
        while funding_index < len(funding) and funding[funding_index].funding_time_us <= kline.close_time_us:
            record = funding[funding_index]
            funding_index += 1
            if record.funding_time_us <= last_open:
                continue
            before = number(state.funding_cashflow)
            state = apply_funding(
                state,
                config,
                rate=record.rate,
                mark_price=kline.close,
                time_us=kline.close_time_us,
                event_id=f"venue:{record.funding_time_us}",
            )
            events.append(
                BotEvent(
                    runtime.bot_id,
                    kline.open_time_us,
                    "GRID_FUNDING",
                    {
                        "funding_time_us": record.funding_time_us,
                        "rate": record.rate,
                        "cashflow": exact_text(number(state.funding_cashflow) - before),
                    },
                )
            )
        last_open = kline.open_time_us
        if state.status in _TERMINAL:
            break
    if state.status is FuturesGridStatus.DONE_SL:
        stopped_reason: str | None = "GRID_DONE_SL"
    elif state.status is FuturesGridStatus.DONE_TP:
        stopped_reason = "GRID_DONE_TP"
    elif state.status is FuturesGridStatus.DONE_LIQ_ESTIMATE:
        stopped_reason = "GRID_DONE_LIQ_ESTIMATE"
    else:
        stopped_reason = None
    next_runtime = GridRuntime(
        bot_id=runtime.bot_id,
        config=runtime.config,
        snapshot=snapshot_grid(state),
        last_bar_open_us=last_open,
        updated_at_us=now_us,
    )
    return FuturesGridAdvance(next_runtime, tuple(events), stopped_reason)
