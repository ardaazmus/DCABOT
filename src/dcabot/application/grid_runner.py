"""Grid paper runner core (Faz G2-c): advance one grid bot over closed bars.

Pure and deterministic: given the bot's persisted grid runtime and the
venue's newly closed 1m klines, it returns the next runtime plus the bot
events to persist. Every bar feeds the engine the same O,H,L,C intrabar
path as grid backtests. A terminal engine (stop-loss/take-profit) reports
a stop reason so the service halts the bot; a paused bot still fills its
standing grid orders.
"""

from dataclasses import dataclass

from dcabot.application.paper_bot_runner import RUNNER_INTERVAL_US
from dcabot.application.spot_grid_cycle_accounting import SpotGridFeeProfile
from dcabot.application.spot_grid_engine import (
    SpotGridConfig,
    SpotGridEngineError,
    SpotGridMode,
    SpotGridStatus,
    apply_tick,
    create_grid,
    restore_grid,
    snapshot_grid,
)
from dcabot.data_adapters.binance_public_transport import BinancePublicKline
from dcabot.domain.numbers import number
from dcabot.persistence.bot_store import BotEvent, GridRuntime

_FEE_REVISION = "grid-paper-1"


@dataclass(frozen=True, slots=True)
class GridAdvance:
    runtime: GridRuntime
    events: tuple[BotEvent, ...]
    stopped_reason: str | None


def build_grid_config(
    strategy: dict, rules, *, investment: str, enforce_min_notional: bool = True
) -> SpotGridConfig:
    """Rebuild the tradable engine config from the bot strategy + venue rules."""

    if not isinstance(strategy, dict):
        raise SpotGridEngineError("SPOT_GRID_CONFIG_INVALID", "Grid stratejisi geçersiz.")
    try:
        mode = SpotGridMode(str(strategy.get("mode", "ARITHMETIC")))
    except ValueError as error:
        raise SpotGridEngineError("SPOT_GRID_MODE_INVALID", "Grid modu geçersiz.") from error
    profile = SpotGridFeeProfile(
        fee_asset=rules.quote_asset,
        fee_rate=str(strategy.get("fee_rate", "0.001")),
        fee_quantum="0",
        profile_revision=_FEE_REVISION,
    )
    config = SpotGridConfig(
        base_asset=rules.base_asset,
        quote_asset=rules.quote_asset,
        mode=mode,
        lower_price=str(strategy["lower_price"]),
        upper_price=str(strategy["upper_price"]),
        interval_count=int(strategy["interval_count"]),
        investment_quote=investment,
        base_step_size=rules.qty_step,
        fee_profile=profile,
        price_tick=rules.tick if mode is SpotGridMode.GEOMETRIC else None,
        tick_origin="0" if mode is SpotGridMode.GEOMETRIC else None,
        stop_loss_price=strategy.get("stop_loss_price"),
        take_profit_pct=strategy.get("take_profit_pct"),
        trailing_up_pct=strategy.get("trailing_up_pct"),
        trailing_down_pct=strategy.get("trailing_down_pct"),
    )
    if enforce_min_notional and number(config.quote_per_grid) < number(rules.min_notional):
        raise SpotGridEngineError(
            "GRID_MIN_NOTIONAL_TOO_SMALL",
            f"Grid başına ({config.quote_per_grid}) min notional ({rules.min_notional}) altında.",
        )
    return config


def config_to_dict(config: SpotGridConfig) -> dict:
    """Freeze the engine config into the runtime row (rebuilt on advance)."""

    return {
        "base_asset": config.base_asset,
        "quote_asset": config.quote_asset,
        "mode": config.mode.value,
        "lower_price": config.lower_price,
        "upper_price": config.upper_price,
        "interval_count": config.interval_count,
        "investment_quote": config.investment_quote,
        "base_step_size": config.base_step_size,
        "fee_rate": config.fee_profile.fee_rate,
        "fee_revision": config.fee_profile.profile_revision,
        "price_tick": config.price_tick,
        "tick_origin": config.tick_origin,
        "stop_loss_price": config.stop_loss_price,
        "take_profit_pct": config.take_profit_pct,
        "trailing_up_pct": config.trailing_up_pct,
        "trailing_down_pct": config.trailing_down_pct,
        "fingerprint": config.fingerprint,
    }


def config_from_dict(raw: dict) -> SpotGridConfig:
    """Thaw a runtime row back into the validated engine config."""

    if not isinstance(raw, dict):
        raise SpotGridEngineError("SPOT_GRID_CONFIG_INVALID", "Grid config satırı geçersiz.")
    try:
        config = SpotGridConfig(
            base_asset=str(raw["base_asset"]),
            quote_asset=str(raw["quote_asset"]),
            mode=SpotGridMode(str(raw["mode"])),
            lower_price=str(raw["lower_price"]),
            upper_price=str(raw["upper_price"]),
            interval_count=int(raw["interval_count"]),
            investment_quote=str(raw["investment_quote"]),
            base_step_size=str(raw["base_step_size"]),
            fee_profile=SpotGridFeeProfile(
                fee_asset=str(raw["quote_asset"]),
                fee_rate=str(raw["fee_rate"]),
                fee_quantum="0",
                profile_revision=str(raw.get("fee_revision", _FEE_REVISION)),
            ),
            price_tick=raw.get("price_tick"),
            tick_origin=raw.get("tick_origin"),
            stop_loss_price=raw.get("stop_loss_price"),
            take_profit_pct=raw.get("take_profit_pct"),
            trailing_up_pct=raw.get("trailing_up_pct"),
            trailing_down_pct=raw.get("trailing_down_pct"),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise SpotGridEngineError("SPOT_GRID_CONFIG_INVALID", "Grid config satırı geçersiz.") from error
    if config.fingerprint != raw.get("fingerprint"):
        raise SpotGridEngineError("SPOT_GRID_CONFIG_MISMATCH", "Grid config parmak izi uyuşmuyor.")
    return config


def prepare_grid_runtime(
    bot_id: str,
    strategy: dict,
    rules,
    *,
    investment: str,
    now_us: int,
) -> GridRuntime:
    """Create the first grid runtime: validated config plus WAIT snapshot."""

    config = build_grid_config(strategy, rules, investment=investment)
    current_bar_open = now_us // RUNNER_INTERVAL_US * RUNNER_INTERVAL_US
    return GridRuntime(
        bot_id=bot_id,
        config=config_to_dict(config),
        snapshot=snapshot_grid(create_grid(config)),
        last_bar_open_us=current_bar_open,
        updated_at_us=now_us,
    )


def advance_grid(
    runtime: GridRuntime,
    klines: tuple[BinancePublicKline, ...],
    *,
    now_us: int,
) -> GridAdvance:
    """Apply every kline newer than `runtime.last_bar_open_us`, oldest first."""

    config = config_from_dict(runtime.config)
    state = restore_grid(runtime.snapshot, config)
    last_open = runtime.last_bar_open_us
    events: list[BotEvent] = []
    for kline in klines:
        if kline.open_time_us <= last_open:
            continue
        for tick in (kline.open, kline.high, kline.low, kline.close):
            result = apply_tick(state, config, price=tick)
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
                            "qty": fill.base_quantity,
                        },
                    )
                )
            for name in result.events:
                if name in ("GRID_INIT", "GRID_STOP_LOSS", "GRID_TAKE_PROFIT", "GRID_TRAIL_UP", "GRID_TRAIL_DOWN"):
                    events.append(BotEvent(runtime.bot_id, kline.open_time_us, name, {}))
            if state.status in (SpotGridStatus.DONE_SL, SpotGridStatus.DONE_TP):
                break
        last_open = kline.open_time_us
        if state.status in (SpotGridStatus.DONE_SL, SpotGridStatus.DONE_TP):
            break
    if state.status is SpotGridStatus.DONE_SL:
        stopped_reason: str | None = "GRID_DONE_SL"
    elif state.status is SpotGridStatus.DONE_TP:
        stopped_reason = "GRID_DONE_TP"
    else:
        stopped_reason = None
    next_runtime = GridRuntime(
        bot_id=runtime.bot_id,
        config=runtime.config,
        snapshot=snapshot_grid(state),
        last_bar_open_us=last_open,
        updated_at_us=now_us,
    )
    return GridAdvance(next_runtime, tuple(events), stopped_reason)
