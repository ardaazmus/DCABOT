"""Pure spot-grid execution engine: allocation, level-cross fills, TP/SL, trailing.

The engine is price-sequence pure: no clock, no network, no persistence. Money
moves only through accepted ``SpotFill`` records applied to a
``SpotInventoryState``; fees follow the explicit quote-asset profile. Orders
live per price *interval* (``N`` intervals over ``N + 1`` levels): a below-entry
interval holds a BUY at its lower level, an above-entry interval holds a SELL
at its upper level. A fill flips its interval to the opposite side, so every
level maps to at most one pending order and no placement ever collides.

Intra-tick semantics are conservative limit semantics: a level crossed between
the previous tick and the current tick fills at the LEVEL price, falling ticks
processing crossed BUY intervals top-down, rising ticks crossed SELL intervals
bottom-up. Stop-loss liquidates after level fills at the tick price; take-profit
compares post-fill equity against the compounded target. Trailing shifts the
whole range and re-plans from current holdings without fresh investment.
"""

from dataclasses import dataclass
from enum import StrEnum
import hashlib

from dcabot.application.spot_grid_cycle_accounting import (
    SpotGridCycleError,
    SpotGridFeeProfile,
)
from dcabot.application.spot_grid_levels import (
    build_arithmetic_grid_levels,
    build_geometric_grid_levels,
)
from dcabot.application.spot_inventory_projection import (
    SpotFill,
    SpotFillSide,
    SpotInventoryState,
    apply_accepted_spot_fill,
)
from dcabot.domain.numbers import Q, align, bounded, exact_text, number, positive

ENGINE_REVISION = "G2a.1"

_BUY = "BUY"
_SELL = "SELL"
_NONE = "NONE"


class SpotGridEngineError(ValueError):
    """Raised when a spot-grid config, tick, or snapshot is unsafe."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class SpotGridMode(StrEnum):
    """Supported level-spacing modes."""

    ARITHMETIC = "ARITHMETIC"
    GEOMETRIC = "GEOMETRIC"


class SpotGridStatus(StrEnum):
    """Engine lifecycle: wait, active, or terminally liquidated."""

    WAIT = "WAIT"
    ACTIVE = "ACTIVE"
    DONE_SL = "DONE_SL"
    DONE_TP = "DONE_TP"


def _asset(value: str, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 24
        or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for ch in value)
    ):
        raise SpotGridEngineError(
            "SPOT_GRID_ASSET_INVALID", f"{field_name} büyük harfli asset kodu olmalıdır."
        )
    return value


def _ratio(value: str, field_name: str) -> Q:
    try:
        parsed = number(value)
    except ValueError as error:
        raise SpotGridEngineError(
            "SPOT_GRID_PCT_INVALID", f"{field_name} exact decimal oran olmalıdır."
        ) from error
    if parsed < 0:
        raise SpotGridEngineError(
            "SPOT_GRID_PCT_INVALID", f"{field_name} negatif olamaz."
        )
    return bounded(parsed)


@dataclass(frozen=True, slots=True)
class SpotGridConfig:
    """Validated grid contract; levels and per-grid quote derived eagerly."""

    base_asset: str
    quote_asset: str
    mode: SpotGridMode
    lower_price: str
    upper_price: str
    interval_count: int
    investment_quote: str
    base_step_size: str
    fee_profile: SpotGridFeeProfile
    price_tick: str | None = None
    tick_origin: str | None = None
    stop_loss_price: str | None = None
    take_profit_pct: str | None = None
    trailing_up_pct: str | None = None
    trailing_down_pct: str | None = None
    levels: tuple[str, ...] = ()
    quote_per_grid: str = ""
    fingerprint: str = ""

    def __post_init__(self) -> None:
        base = _asset(self.base_asset, "base_asset")
        quote = _asset(self.quote_asset, "quote_asset")
        if base == quote:
            raise SpotGridEngineError(
                "SPOT_GRID_ASSET_INVALID", "base_asset quote_asset ile aynı olamaz."
            )
        if not isinstance(self.mode, SpotGridMode):
            raise SpotGridEngineError("SPOT_GRID_MODE_INVALID", "mode ARITHMETIC/GEOMETRIC olmalıdır.")
        try:
            investment = positive(self.investment_quote)
            step = positive(self.base_step_size)
        except ValueError as error:
            raise SpotGridEngineError(
                "SPOT_GRID_AMOUNT_INVALID",
                "investment_quote ve base_step_size pozitif decimal olmalıdır.",
            ) from error
        if not isinstance(self.fee_profile, SpotGridFeeProfile):
            raise SpotGridEngineError("SPOT_GRID_FEE_PROFILE_INVALID", "fee profili geçersiz.")
        if self.fee_profile.fee_asset != quote:
            raise SpotGridEngineError(
                "SPOT_GRID_FEE_ASSET_UNSUPPORTED",
                "Fee asset quote asset ile aynı olmalıdır.",
            )
        try:
            if self.mode is SpotGridMode.ARITHMETIC:
                built = build_arithmetic_grid_levels(
                    lower_price=self.lower_price,
                    upper_price=self.upper_price,
                    interval_count=self.interval_count,
                )
                rendered = built.levels
            else:
                if self.price_tick is None or self.tick_origin is None:
                    raise SpotGridEngineError(
                        "SPOT_GRID_TICK_INVALID",
                        "Geometric mod price_tick ve tick_origin ister.",
                    )
                built = build_geometric_grid_levels(
                    lower_price=self.lower_price,
                    upper_price=self.upper_price,
                    interval_count=self.interval_count,
                    price_tick=self.price_tick,
                    tick_origin=self.tick_origin,
                )
                rendered = built.levels
        except SpotGridEngineError:
            raise
        except ValueError as error:
            code = getattr(error, "code", "SPOT_GRID_LEVELS_INVALID")
            raise SpotGridEngineError(code, str(error)) from error
        count = self.interval_count
        per_grid = bounded(investment / count)
        try:
            quote_per_grid = exact_text(per_grid)
        except ValueError as error:
            raise SpotGridEngineError(
                "SPOT_GRID_QUOTE_PER_GRID_UNREPRESENTABLE",
                "investment_quote interval sayısına exact bölünmelidir.",
            ) from error
        upper = positive(rendered[-1])
        worst_base = align(bounded(per_grid / upper), step, up=False)
        if worst_base <= 0:
            raise SpotGridEngineError(
                "SPOT_GRID_QTY_TOO_SMALL",
                "En üst seviyede bir grid base_step_size altında kalıyor.",
            )
        stop = None
        if self.stop_loss_price is not None:
            try:
                stop = positive(self.stop_loss_price)
            except ValueError as error:
                raise SpotGridEngineError(
                    "SPOT_GRID_SL_INVALID", "stop_loss_price pozitif decimal olmalıdır."
                ) from error
            if stop >= positive(rendered[0]):
                raise SpotGridEngineError(
                    "SPOT_GRID_SL_INVALID", "stop_loss_price alt sınırın altında olmalıdır."
                )
        take_profit = None
        if self.take_profit_pct is not None:
            take_profit = _ratio(self.take_profit_pct, "take_profit_pct")
            if take_profit == 0:
                raise SpotGridEngineError(
                    "SPOT_GRID_TP_INVALID", "take_profit_pct sıfırdan büyük olmalıdır."
                )
        trailing_up = None
        if self.trailing_up_pct is not None:
            trailing_up = _ratio(self.trailing_up_pct, "trailing_up_pct")
            if trailing_up == 0:
                raise SpotGridEngineError(
                    "SPOT_GRID_TRAIL_INVALID", "trailing_up_pct sıfırdan büyük olmalıdır."
                )
        trailing_down = None
        if self.trailing_down_pct is not None:
            trailing_down = _ratio(self.trailing_down_pct, "trailing_down_pct")
            if trailing_down == 0:
                raise SpotGridEngineError(
                    "SPOT_GRID_TRAIL_INVALID", "trailing_down_pct sıfırdan büyük olmalıdır."
                )
        canonical = "|".join(
            [
                ENGINE_REVISION,
                base,
                quote,
                self.mode.value,
                exact_text(positive(rendered[0])),
                exact_text(upper),
                str(count),
                exact_text(investment),
                exact_text(step),
                self.fee_profile.fee_rate,
                self.fee_profile.profile_revision,
                exact_text(stop) if stop is not None else "",
                exact_text(take_profit) if take_profit is not None else "",
                exact_text(trailing_up) if trailing_up is not None else "",
                exact_text(trailing_down) if trailing_down is not None else "",
            ]
        )
        fingerprint = hashlib.sha256(canonical.encode("ascii")).hexdigest()[:16]
        object.__setattr__(self, "base_asset", base)
        object.__setattr__(self, "quote_asset", quote)
        object.__setattr__(self, "lower_price", exact_text(positive(rendered[0])))
        object.__setattr__(self, "upper_price", exact_text(upper))
        object.__setattr__(self, "investment_quote", exact_text(investment))
        object.__setattr__(self, "base_step_size", exact_text(step))
        object.__setattr__(self, "stop_loss_price", exact_text(stop) if stop is not None else None)
        object.__setattr__(
            self, "take_profit_pct", exact_text(take_profit) if take_profit is not None else None
        )
        object.__setattr__(
            self, "trailing_up_pct", exact_text(trailing_up) if trailing_up is not None else None
        )
        object.__setattr__(
            self,
            "trailing_down_pct",
            exact_text(trailing_down) if trailing_down is not None else None,
        )
        object.__setattr__(self, "levels", rendered)
        object.__setattr__(self, "quote_per_grid", quote_per_grid)
        object.__setattr__(self, "fingerprint", fingerprint)


@dataclass(frozen=True, slots=True)
class SpotGridState:
    """Exact grid holdings; every string field is canonical decimal text."""

    status: SpotGridStatus
    config_fingerprint: str
    levels: tuple[str, ...]
    pending: tuple[str, ...]
    locked_quote: tuple[str, ...]
    locked_base: tuple[str, ...]
    quote_reserve: str
    base_free: str
    last_price: str | None
    entry_price: str | None
    inventory: SpotInventoryState
    realized_profit_quote: str
    fees_paid_quote: str
    cycles_closed: int
    trailing_shifts: int
    next_fill_seq: int


@dataclass(frozen=True, slots=True)
class SpotGridTickResult:
    """One tick outcome: resulting state plus accepted fills and coarse events."""

    state: SpotGridState
    fills: tuple[SpotFill, ...]
    events: tuple[str, ...]


def _empty_inventory(config: SpotGridConfig) -> SpotInventoryState:
    return SpotInventoryState(
        base_asset=config.base_asset,
        quote_asset=config.quote_asset,
        base_quantity="0",
        quote_cashflow="0",
        fills=(),
    )


def create_grid(config: SpotGridConfig) -> SpotGridState:
    """Create an uninitialized grid waiting for the first in-range price."""
    if not isinstance(config, SpotGridConfig):
        raise SpotGridEngineError("SPOT_GRID_CONFIG_INVALID", "Grid config geçersiz.")
    count = config.interval_count
    return SpotGridState(
        status=SpotGridStatus.WAIT,
        config_fingerprint=config.fingerprint,
        levels=config.levels,
        pending=tuple(_NONE for _ in range(count)),
        locked_quote=tuple("0" for _ in range(count)),
        locked_base=tuple("0" for _ in range(count)),
        quote_reserve="0",
        base_free="0",
        last_price=None,
        entry_price=None,
        inventory=_empty_inventory(config),
        realized_profit_quote="0",
        fees_paid_quote="0",
        cycles_closed=0,
        trailing_shifts=0,
        next_fill_seq=1,
    )


def _levels_below(levels: tuple[Q, ...], price: Q) -> int:
    """Count intervals strictly below ``price`` (entry interval index)."""
    index = 0
    while index < len(levels) - 1 and not price < levels[index + 1]:
        index += 1
    return index


def _mutable(state: SpotGridState) -> dict[str, object]:
    return {
        "pending": list(state.pending),
        "locked_quote": [number(value) for value in state.locked_quote],
        "locked_base": [number(value) for value in state.locked_base],
        "reserve": number(state.quote_reserve),
        "base_free": number(state.base_free),
        "inventory": state.inventory,
        "realized": number(state.realized_profit_quote),
        "fees": number(state.fees_paid_quote),
        "cycles": state.cycles_closed,
        "seq": state.next_fill_seq,
    }


def _accept_fill(
    work: dict[str, object],
    config: SpotGridConfig,
    *,
    side: SpotFillSide,
    price: Q,
    base_quantity: Q,
) -> SpotFill:
    seq = int(work["seq"])
    fill = SpotFill(
        fill_id=f"grid:{seq}",
        side=side,
        price=exact_text(price),
        base_quantity=exact_text(base_quantity),
    )
    work["inventory"] = apply_accepted_spot_fill(work["inventory"], fill)  # type: ignore[arg-type]
    notional = bounded(price * base_quantity)
    fee = bounded(notional * number(config.fee_profile.fee_rate))
    work["fees"] = bounded(work["fees"] + fee)  # type: ignore[operator]
    if side is SpotFillSide.BUY:
        work["realized"] = bounded(work["realized"] - notional)  # type: ignore[operator]
    else:
        work["realized"] = bounded(work["realized"] + notional)  # type: ignore[operator]
        work["cycles"] = int(work["cycles"]) + 1
    work["seq"] = seq + 1
    return fill


def _plan_from_holdings(
    work: dict[str, object],
    config: SpotGridConfig,
    levels: tuple[Q, ...],
    *,
    price: Q,
    fresh_quote: Q,
) -> None:
    """Place BUY intervals below ``price`` and SELL intervals above it.

    ``fresh_quote`` funds BUY locks and the entry market-buy; quote already
    resting in ``reserve`` is spent first so trailing re-plans never print
    money. Shortfalls leave intervals NONE instead of rounding silently.
    """

    step = number(config.base_step_size)
    per_grid = number(config.quote_per_grid)
    entry_index = _levels_below(levels, price)
    pending = work["pending"]
    locked_quote = work["locked_quote"]
    locked_base = work["locked_base"]
    assert isinstance(pending, list)
    assert isinstance(locked_quote, list)
    assert isinstance(locked_base, list)
    for interval in range(config.interval_count):
        pending[interval] = _NONE
        locked_quote[interval] = Q(0)
        locked_base[interval] = Q(0)
    available = bounded(work["reserve"] + fresh_quote)  # type: ignore[operator]
    for interval in range(entry_index - 1, -1, -1):
        if available < per_grid:
            break
        available = bounded(available - per_grid)
        pending[interval] = _BUY
        locked_quote[interval] = per_grid
    fills: list[SpotFill] = []
    base_unit = align(bounded(per_grid / price), step, up=False)
    if base_unit > 0:
        for interval in range(entry_index, config.interval_count):
            if work["base_free"] >= base_unit:  # type: ignore[operator]
                work["base_free"] = bounded(work["base_free"] - base_unit)  # type: ignore[operator]
            else:
                cost = bounded(base_unit * price)
                if available < cost:
                    break
                available = bounded(available - cost)
                fills.append(
                    _accept_fill(
                        work, config, side=SpotFillSide.BUY, price=price, base_quantity=base_unit
                    )
                )
            pending[interval] = _SELL
            locked_base[interval] = base_unit
    work["reserve"] = available
    work["plan_fills"] = fills


def _release_all(work: dict[str, object], config: SpotGridConfig) -> None:
    pending = work["pending"]
    locked_quote = work["locked_quote"]
    locked_base = work["locked_base"]
    assert isinstance(pending, list)
    assert isinstance(locked_quote, list)
    assert isinstance(locked_base, list)
    for interval in range(config.interval_count):
        work["reserve"] = bounded(work["reserve"] + locked_quote[interval])  # type: ignore[operator]
        work["base_free"] = bounded(work["base_free"] + locked_base[interval])  # type: ignore[operator]
        pending[interval] = _NONE
        locked_quote[interval] = Q(0)
        locked_base[interval] = Q(0)


def grid_equity_quote(state: SpotGridState, *, mark_price: str) -> str:
    """Quote equity at an explicit mark: reserve + locks + base at mark."""
    try:
        mark = positive(mark_price)
    except ValueError as error:
        raise SpotGridEngineError(
            "SPOT_GRID_MARK_INVALID", "mark_price pozitif decimal olmalıdır."
        ) from error
    reserve = number(state.quote_reserve)
    locked_quote = sum((number(value) for value in state.locked_quote), Q(0))
    locked_base = sum((number(value) for value in state.locked_base), Q(0))
    base_total = bounded(locked_base + number(state.base_free))
    return exact_text(bounded(reserve + locked_quote + base_total * mark))


def _freeze(
    config: SpotGridConfig,
    work: dict[str, object],
    *,
    status: SpotGridStatus,
    levels: tuple[str, ...],
    last_price: Q,
    entry_price: Q | None,
    trailing_shifts: int,
) -> SpotGridState:
    pending = work["pending"]
    locked_quote = work["locked_quote"]
    locked_base = work["locked_base"]
    assert isinstance(pending, list)
    assert isinstance(locked_quote, list)
    assert isinstance(locked_base, list)
    inventory = work["inventory"]
    assert isinstance(inventory, SpotInventoryState)
    return SpotGridState(
        status=status,
        config_fingerprint=config.fingerprint,
        levels=levels,
        pending=tuple(str(side) for side in pending),
        locked_quote=tuple(exact_text(qty) for qty in locked_quote),
        locked_base=tuple(exact_text(qty) for qty in locked_base),
        quote_reserve=exact_text(work["reserve"]),  # type: ignore[arg-type]
        base_free=exact_text(work["base_free"]),  # type: ignore[arg-type]
        last_price=exact_text(last_price),
        entry_price=exact_text(entry_price) if entry_price is not None else None,
        inventory=inventory,
        realized_profit_quote=exact_text(work["realized"]),  # type: ignore[arg-type]
        fees_paid_quote=exact_text(work["fees"]),  # type: ignore[arg-type]
        cycles_closed=int(work["cycles"]),
        trailing_shifts=trailing_shifts,
        next_fill_seq=int(work["seq"]),
    )


def _liquidate(
    work: dict[str, object],
    config: SpotGridConfig,
    *,
    price: Q,
    fills: list[SpotFill],
) -> None:
    _release_all(work, config)
    step = number(config.base_step_size)
    base_free = work["base_free"]
    assert isinstance(base_free, Q)
    sell_qty = align(base_free, step, up=False)
    if sell_qty > 0:
        fills.append(
            _accept_fill(work, config, side=SpotFillSide.SELL, price=price, base_quantity=sell_qty)
        )
        work["base_free"] = bounded(base_free - sell_qty)
        work["reserve"] = bounded(work["reserve"] + bounded(sell_qty * price))  # type: ignore[operator]
    # Sub-step dust stays visible in base_free; it is never rounded away.


def _shift_levels(
    config: SpotGridConfig, levels: tuple[Q, ...], *, price: Q, bound: Q
) -> tuple[str, ...] | None:
    if config.mode is SpotGridMode.ARITHMETIC:
        shifted = tuple(bounded(level + (price - bound)) for level in levels)
    else:
        factor = bounded(price / bound)
        shifted = tuple(bounded(level * factor) for level in levels)
    if shifted[0] <= 0:
        return None
    if config.mode is SpotGridMode.ARITHMETIC:
        try:
            return tuple(exact_text(level) for level in shifted)
        except ValueError:
            return None
    assert config.price_tick is not None and config.tick_origin is not None
    tick = number(config.price_tick)
    origin = number(config.tick_origin)
    if any(align(level, tick, up=False, origin=origin) != level for level in shifted):
        return None
    try:
        return tuple(exact_text(level) for level in shifted)
    except ValueError:
        return None


def apply_tick(state: SpotGridState, config: SpotGridConfig, *, price: str) -> SpotGridTickResult:
    """Advance the grid by one price tick.

    Order per tick: level-cross fills, then stop-loss liquidation, then
    trailing re-anchor, then take-profit liquidation. Terminal states are
    returned unchanged.
    """

    if not isinstance(state, SpotGridState) or not isinstance(config, SpotGridConfig):
        raise SpotGridEngineError("SPOT_GRID_INPUT_INVALID", "State veya config geçersiz.")
    if state.config_fingerprint != config.fingerprint:
        raise SpotGridEngineError(
            "SPOT_GRID_CONFIG_MISMATCH", "State bu config ile açılmadı."
        )
    try:
        tick = positive(price)
    except ValueError as error:
        raise SpotGridEngineError(
            "SPOT_GRID_TICK_INVALID", "tick fiyatı pozitif decimal olmalıdır."
        ) from error
    if state.status in (SpotGridStatus.DONE_SL, SpotGridStatus.DONE_TP):
        return SpotGridTickResult(state=state, fills=(), events=())

    fills: list[SpotFill] = []
    events: list[str] = []
    levels = tuple(number(value) for value in state.levels)
    step = number(config.base_step_size)
    work = _mutable(state)
    pending = work["pending"]
    locked_quote = work["locked_quote"]
    locked_base = work["locked_base"]
    assert isinstance(pending, list)
    assert isinstance(locked_quote, list)
    assert isinstance(locked_base, list)

    if state.status is SpotGridStatus.WAIT:
        if levels[0] <= tick <= levels[-1]:
            _plan_from_holdings(
                work, config, levels, price=tick, fresh_quote=number(config.investment_quote)
            )
            fills.extend(work.get("plan_fills", []))  # type: ignore[arg-type]
            if all(side == _NONE for side in pending):
                raise SpotGridEngineError(
                    "SPOT_GRID_ALLOCATION_EMPTY",
                    "Giriş fiyatı tüm aralıkları boş bıraktı; yatırım aralığa göre küçük.",
                )
            events.append("GRID_INIT")
            frozen = _freeze(
                config,
                work,
                status=SpotGridStatus.ACTIVE,
                levels=state.levels,
                last_price=tick,
                entry_price=tick,
                trailing_shifts=state.trailing_shifts,
            )
            return SpotGridTickResult(state=frozen, fills=tuple(fills), events=tuple(events))
        frozen = _freeze(
            config,
            work,
            status=SpotGridStatus.WAIT,
            levels=state.levels,
            last_price=tick,
            entry_price=None,
            trailing_shifts=state.trailing_shifts,
        )
        return SpotGridTickResult(state=frozen, fills=(), events=("GRID_WAIT",))

    last = number(state.last_price) if state.last_price is not None else tick
    if tick < last:
        crossed = [
            interval
            for interval in range(config.interval_count - 1, -1, -1)
            if pending[interval] == _BUY and tick <= levels[interval] < last
        ]
        for interval in crossed:
            level_price = levels[interval]
            qty = align(bounded(locked_quote[interval] / level_price), step, up=False)
            locked = locked_quote[interval]
            pending[interval] = _NONE
            locked_quote[interval] = Q(0)
            if qty <= 0:
                work["reserve"] = bounded(work["reserve"] + locked)  # type: ignore[operator]
                events.append("GRID_LEVEL_ABANDONED")
                continue
            cost = bounded(qty * level_price)
            work["reserve"] = bounded(work["reserve"] + bounded(locked - cost))  # type: ignore[operator]
            fills.append(
                _accept_fill(work, config, side=SpotFillSide.BUY, price=level_price, base_quantity=qty)
            )
            pending[interval] = _SELL
            locked_base[interval] = qty
    elif tick > last:
        crossed = [
            interval
            for interval in range(config.interval_count)
            if pending[interval] == _SELL and last < levels[interval + 1] <= tick
        ]
        for interval in crossed:
            level_price = levels[interval + 1]
            qty = locked_base[interval]
            pending[interval] = _NONE
            locked_base[interval] = Q(0)
            fills.append(
                _accept_fill(
                    work, config, side=SpotFillSide.SELL, price=level_price, base_quantity=qty
                )
            )
            proceeds = bounded(qty * level_price)
            pending[interval] = _BUY
            locked_quote[interval] = proceeds

    if config.stop_loss_price is not None and tick <= number(config.stop_loss_price):
        _liquidate(work, config, price=tick, fills=fills)
        events.append("GRID_STOP_LOSS")
        frozen = _freeze(
            config,
            work,
            status=SpotGridStatus.DONE_SL,
            levels=state.levels,
            last_price=tick,
            entry_price=number(state.entry_price) if state.entry_price is not None else None,
            trailing_shifts=state.trailing_shifts,
        )
        return SpotGridTickResult(state=frozen, fills=tuple(fills), events=tuple(events))

    current_levels = state.levels
    if config.trailing_up_pct is not None and tick > levels[-1] * (
        1 + number(config.trailing_up_pct)
    ):
        shifted = _shift_levels(config, levels, price=tick, bound=levels[-1])
        if shifted is None:
            events.append("GRID_TRAIL_SKIPPED")
        else:
            _release_all(work, config)
            new_levels = tuple(number(value) for value in shifted)
            _plan_from_holdings(work, config, new_levels, price=tick, fresh_quote=Q(0))
            fills.extend(work.get("plan_fills", []))  # type: ignore[arg-type]
            current_levels = shifted
            events.append("GRID_TRAIL_UP")
    elif config.trailing_down_pct is not None and tick < levels[0] * (
        1 - number(config.trailing_down_pct)
    ):
        shifted = _shift_levels(config, levels, price=tick, bound=levels[0])
        if shifted is None:
            events.append("GRID_TRAIL_SKIPPED")
        else:
            _release_all(work, config)
            new_levels = tuple(number(value) for value in shifted)
            _plan_from_holdings(work, config, new_levels, price=tick, fresh_quote=Q(0))
            fills.extend(work.get("plan_fills", []))  # type: ignore[arg-type]
            current_levels = shifted
            events.append("GRID_TRAIL_DOWN")

    if config.take_profit_pct is not None:
        equity = number(
            grid_equity_quote(
                _freeze(
                    config,
                    work,
                    status=SpotGridStatus.ACTIVE,
                    levels=current_levels,
                    last_price=tick,
                    entry_price=number(state.entry_price) if state.entry_price is not None else None,
                    trailing_shifts=state.trailing_shifts,
                ),
                mark_price=exact_text(tick),
            )
        )
        target = bounded(number(config.investment_quote) * (1 + number(config.take_profit_pct)))
        if equity >= target:
            _liquidate(work, config, price=tick, fills=fills)
            events.append("GRID_TAKE_PROFIT")
            frozen = _freeze(
                config,
                work,
                status=SpotGridStatus.DONE_TP,
                levels=current_levels,
                last_price=tick,
                entry_price=number(state.entry_price) if state.entry_price is not None else None,
                trailing_shifts=state.trailing_shifts + sum(
                    1 for event in events if event in ("GRID_TRAIL_UP", "GRID_TRAIL_DOWN")
                ),
            )
            return SpotGridTickResult(state=frozen, fills=tuple(fills), events=tuple(events))

    frozen = _freeze(
        config,
        work,
        status=SpotGridStatus.ACTIVE,
        levels=current_levels,
        last_price=tick,
        entry_price=number(state.entry_price) if state.entry_price is not None else None,
        trailing_shifts=state.trailing_shifts
        + sum(1 for event in events if event in ("GRID_TRAIL_UP", "GRID_TRAIL_DOWN")),
    )
    return SpotGridTickResult(state=frozen, fills=tuple(fills), events=tuple(events))


def snapshot_grid(state: SpotGridState) -> dict[str, object]:
    """Render a JSON-safe snapshot for persistence (G2-c runtime)."""
    if not isinstance(state, SpotGridState):
        raise SpotGridEngineError("SPOT_GRID_INPUT_INVALID", "State geçersiz.")
    return {
        "engine_revision": ENGINE_REVISION,
        "config_fingerprint": state.config_fingerprint,
        "status": state.status.value,
        "levels": list(state.levels),
        "pending": list(state.pending),
        "locked_quote": list(state.locked_quote),
        "locked_base": list(state.locked_base),
        "quote_reserve": state.quote_reserve,
        "base_free": state.base_free,
        "last_price": state.last_price,
        "entry_price": state.entry_price,
        "fills": [
            {
                "fill_id": fill.fill_id,
                "side": fill.side.value,
                "price": fill.price,
                "base_quantity": fill.base_quantity,
            }
            for fill in state.inventory.fills
        ],
        "realized_profit_quote": state.realized_profit_quote,
        "fees_paid_quote": state.fees_paid_quote,
        "cycles_closed": state.cycles_closed,
        "trailing_shifts": state.trailing_shifts,
        "next_fill_seq": state.next_fill_seq,
    }


def restore_grid(snapshot: dict[str, object], config: SpotGridConfig) -> SpotGridState:
    """Rebuild grid state; rejects foreign revisions, configs, and shapes."""
    if not isinstance(snapshot, dict) or not isinstance(config, SpotGridConfig):
        raise SpotGridEngineError("SPOT_GRID_SNAPSHOT_INVALID", "Snapshot veya config geçersiz.")
    if snapshot.get("engine_revision") != ENGINE_REVISION:
        raise SpotGridEngineError(
            "SPOT_GRID_SNAPSHOT_REVISION_INVALID", "Snapshot motor revizyonu uyuşmuyor."
        )
    if snapshot.get("config_fingerprint") != config.fingerprint:
        raise SpotGridEngineError(
            "SPOT_GRID_CONFIG_MISMATCH", "Snapshot bu config ile açılmadı."
        )
    try:
        status = SpotGridStatus(str(snapshot["status"]))
        levels = tuple(str(value) for value in snapshot["levels"])  # type: ignore[index]
        pending = tuple(str(value) for value in snapshot["pending"])  # type: ignore[index]
        locked_quote = tuple(str(value) for value in snapshot["locked_quote"])  # type: ignore[index]
        locked_base = tuple(str(value) for value in snapshot["locked_base"])  # type: ignore[index]
        raw_fills = snapshot["fills"]
        assert isinstance(raw_fills, list)
        fills: list[SpotFill] = []
        for raw in raw_fills:
            assert isinstance(raw, dict)
            fills.append(
                SpotFill(
                    fill_id=str(raw["fill_id"]),
                    side=SpotFillSide(str(raw["side"])),
                    price=str(raw["price"]),
                    base_quantity=str(raw["base_quantity"]),
                )
            )
        last_price = snapshot["last_price"]
        entry_price = snapshot["entry_price"]
        inventory = _empty_inventory(config)
        for fill in fills:
            inventory = apply_accepted_spot_fill(inventory, fill)
        for value in (
            levels + locked_quote + locked_base + (str(snapshot["quote_reserve"]),)
            + (str(snapshot["base_free"]),)
            + (() if last_price is None else (str(last_price),))
            + (() if entry_price is None else (str(entry_price),))
            + (str(snapshot["realized_profit_quote"]), str(snapshot["fees_paid_quote"]))
        ):
            number(value)
        cycles = snapshot["cycles_closed"]
        shifts = snapshot["trailing_shifts"]
        seq = snapshot["next_fill_seq"]
        assert isinstance(cycles, int) and isinstance(shifts, int) and isinstance(seq, int)
        assert not isinstance(cycles, bool) and cycles >= 0 and shifts >= 0 and seq >= 1
        assert len(levels) == config.interval_count + 1
        assert len(pending) == len(locked_quote) == len(locked_base) == config.interval_count
        assert all(side in (_BUY, _SELL, _NONE) for side in pending)
        assert all(number(value) >= 0 for value in locked_quote + locked_base)
        return SpotGridState(
            status=status,
            config_fingerprint=config.fingerprint,
            levels=levels,
            pending=pending,
            locked_quote=locked_quote,
            locked_base=locked_base,
            quote_reserve=str(snapshot["quote_reserve"]),
            base_free=str(snapshot["base_free"]),
            last_price=None if last_price is None else str(last_price),
            entry_price=None if entry_price is None else str(entry_price),
            inventory=inventory,
            realized_profit_quote=str(snapshot["realized_profit_quote"]),
            fees_paid_quote=str(snapshot["fees_paid_quote"]),
            cycles_closed=cycles,
            trailing_shifts=shifts,
            next_fill_seq=seq,
        )
    except SpotGridEngineError:
        raise
    except (AssertionError, KeyError, TypeError, ValueError) as error:
        raise SpotGridEngineError(
            "SPOT_GRID_SNAPSHOT_INVALID", "Snapshot şekli veya miktarları geçersiz."
        ) from error


def describe_grid(config: SpotGridConfig) -> dict[str, object]:
    """Static grid summary for API/UI previews (no market data)."""
    if not isinstance(config, SpotGridConfig):
        raise SpotGridEngineError("SPOT_GRID_CONFIG_INVALID", "Grid config geçersiz.")
    return {
        "engine_revision": ENGINE_REVISION,
        "mode": config.mode.value,
        "levels": list(config.levels),
        "interval_count": config.interval_count,
        "investment_quote": config.investment_quote,
        "quote_per_grid": config.quote_per_grid,
        "base_step_size": config.base_step_size,
        "fee_rate": config.fee_profile.fee_rate,
        "stop_loss_price": config.stop_loss_price,
        "take_profit_pct": config.take_profit_pct,
        "trailing_up_pct": config.trailing_up_pct,
        "trailing_down_pct": config.trailing_down_pct,
        "fingerprint": config.fingerprint,
    }


try:
    SpotGridCycleError  # Re-exported for callers catching grid failures jointly.
except NameError:  # pragma: no cover - import guard, never fires at runtime.
    raise
