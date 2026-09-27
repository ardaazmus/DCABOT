"""Pure isolated USD-M futures grid execution engine (one-way, LONG/SHORT).

Price-series pure like the spot engine, with three futures differences:
lots instead of averaged entries (a notional-weighted average rarely fits
the exact-decimal contract, so closes match opens FIFO and stay exact),
isolated margin tracked per open (notional / leverage locked from the
wallet), and explicit funding derived from (rate, mark) inputs per the
verified funding formula. Liquidation is ESTIMATE_ONLY: with explicit
frozen risk tiers the engine labels a per-tick estimate and halts with
DONE_LIQ_ESTIMATE on breach; without tiers no estimate exists and the
venue remains the only liquidation authority (LCR-12).
"""

from dataclasses import dataclass
from enum import StrEnum
import hashlib

from dcabot.application.futures_grid_levels import FuturesGridProfile
from dcabot.application.futures_grid_position import (
    FuturesGridFill,
    FuturesGridFillSide,
)
from dcabot.application.isolated_liquidation import IsolatedRiskTier
from dcabot.application.spot_grid_levels import (
    build_arithmetic_grid_levels,
    build_geometric_grid_levels,
)
from dcabot.domain.numbers import Q, align, bounded, exact_text, number, positive

ENGINE_REVISION = "G3a.1"
_FEE_REVISION = "futures-grid-engine-1"
_MAX_FUNDING_RATE = Q(2, 100)

_BUY = "BUY"
_SELL = "SELL"
_NONE = "NONE"


class FuturesGridEngineError(ValueError):
    """Raised when a futures grid config, tick, funding, or snapshot is unsafe."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class FuturesGridMode(StrEnum):
    """Supported level-spacing modes."""

    ARITHMETIC = "ARITHMETIC"
    GEOMETRIC = "GEOMETRIC"


class FuturesGridDirection(StrEnum):
    """One-way grid direction; flips are impossible by construction."""

    LONG = "LONG"
    SHORT = "SHORT"


class FuturesGridStatus(StrEnum):
    """Engine lifecycle: wait, active, or terminally flattened."""

    WAIT = "WAIT"
    ACTIVE = "ACTIVE"
    DONE_SL = "DONE_SL"
    DONE_TP = "DONE_TP"
    DONE_LIQ_ESTIMATE = "DONE_LIQ_ESTIMATE"


def _asset(value: str, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 24
        or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for ch in value)
    ):
        raise FuturesGridEngineError(
            "FUTURES_GRID_ASSET_INVALID", f"{field_name} büyük harfli asset kodu olmalıdır."
        )
    return value


def _ratio(value: str, field_name: str) -> Q:
    try:
        parsed = number(value)
    except ValueError as error:
        raise FuturesGridEngineError(
            "FUTURES_GRID_PCT_INVALID", f"{field_name} exact decimal oran olmalıdır."
        ) from error
    if parsed < 0:
        raise FuturesGridEngineError("FUTURES_GRID_PCT_INVALID", f"{field_name} negatif olamaz.")
    return bounded(parsed)


@dataclass(frozen=True, slots=True)
class FuturesGridLot:
    """One open parcel tagged to its interval: quantity, entry, locked margin."""

    interval: int
    quantity: str
    entry_price: str
    locked_margin: str


@dataclass(frozen=True, slots=True)
class FuturesGridConfig:
    """Validated futures grid contract; levels and per-grid notional derived."""

    base_asset: str
    quote_asset: str
    direction: FuturesGridDirection
    mode: FuturesGridMode
    lower_price: str
    upper_price: str
    interval_count: int
    investment_quote: str
    leverage: int
    base_step_size: str
    fee_rate: str
    price_tick: str | None = None
    tick_origin: str | None = None
    stop_loss_price: str | None = None
    take_profit_pct: str | None = None
    trailing_up_pct: str | None = None
    trailing_down_pct: str | None = None
    risk_tiers: tuple[IsolatedRiskTier, ...] = ()
    levels: tuple[str, ...] = ()
    quote_per_grid: str = ""
    fingerprint: str = ""

    def __post_init__(self) -> None:
        base = _asset(self.base_asset, "base_asset")
        quote = _asset(self.quote_asset, "quote_asset")
        if base == quote:
            raise FuturesGridEngineError(
                "FUTURES_GRID_ASSET_INVALID", "base_asset quote_asset ile aynı olamaz."
            )
        if quote != "USDT":
            raise FuturesGridEngineError(
                "FUTURES_GRID_SETTLEMENT_UNSUPPORTED", "Yalnız USDT-M profili desteklenir."
            )
        if not isinstance(self.direction, FuturesGridDirection):
            raise FuturesGridEngineError(
                "FUTURES_GRID_DIRECTION_INVALID", "direction LONG/SHORT olmalıdır."
            )
        if not isinstance(self.mode, FuturesGridMode):
            raise FuturesGridEngineError(
                "FUTURES_GRID_MODE_INVALID", "mode ARITHMETIC/GEOMETRIC olmalıdır."
            )
        if isinstance(self.leverage, bool) or not isinstance(self.leverage, int):
            raise FuturesGridEngineError(
                "FUTURES_GRID_LEVERAGE_INVALID", "leverage 1-10 tamsayı olmalıdır."
            )
        if not 1 <= self.leverage <= 10:
            raise FuturesGridEngineError(
                "FUTURES_GRID_LEVERAGE_INVALID", "leverage 1-10 aralığında olmalıdır."
            )
        try:
            investment = positive(self.investment_quote)
            step = positive(self.base_step_size)
            fee = number(self.fee_rate)
        except ValueError as error:
            raise FuturesGridEngineError(
                "FUTURES_GRID_AMOUNT_INVALID", "investment/step/fee decimal olmalıdır."
            ) from error
        if not 0 <= fee < 1:
            raise FuturesGridEngineError(
                "FUTURES_GRID_FEE_INVALID", "fee_rate 0-1 aralığında olmalıdır."
            )
        try:
            profile = FuturesGridProfile(leverage=str(self.leverage))
        except ValueError as error:
            raise FuturesGridEngineError("FUTURES_GRID_PROFILE_INVALID", str(error)) from error
        _ = profile
        try:
            if self.mode is FuturesGridMode.ARITHMETIC:
                rendered = build_arithmetic_grid_levels(
                    lower_price=self.lower_price,
                    upper_price=self.upper_price,
                    interval_count=self.interval_count,
                ).levels
            else:
                if self.price_tick is None or self.tick_origin is None:
                    raise FuturesGridEngineError(
                        "FUTURES_GRID_TICK_INVALID",
                        "Geometric mod price_tick ve tick_origin ister.",
                    )
                rendered = build_geometric_grid_levels(
                    lower_price=self.lower_price,
                    upper_price=self.upper_price,
                    interval_count=self.interval_count,
                    price_tick=self.price_tick,
                    tick_origin=self.tick_origin,
                ).levels
        except FuturesGridEngineError:
            raise
        except ValueError as error:
            code = getattr(error, "code", "FUTURES_GRID_LEVELS_INVALID")
            raise FuturesGridEngineError(code, str(error)) from error
        per_grid = bounded(investment / self.interval_count)
        try:
            quote_per_grid = exact_text(per_grid)
        except ValueError as error:
            raise FuturesGridEngineError(
                "FUTURES_GRID_QUOTE_PER_GRID_UNREPRESENTABLE",
                "investment_quote interval sayısına exact bölünmelidir.",
            ) from error
        try:
            exact_text(bounded(per_grid / self.leverage))
        except ValueError as error:
            raise FuturesGridEngineError(
                "FUTURES_GRID_MARGIN_PER_GRID_UNREPRESENTABLE",
                "Grid başına marjin kaldıraca exact bölünmelidir.",
            ) from error
        bound = positive(rendered[-1] if self.direction is FuturesGridDirection.LONG else rendered[0])
        worst_qty = align(bounded(per_grid / bound), step, up=False)
        if worst_qty <= 0:
            raise FuturesGridEngineError(
                "FUTURES_GRID_QTY_TOO_SMALL",
                "En uç seviyede bir grid base_step_size altında kalıyor.",
            )
        stop = None
        if self.stop_loss_price is not None:
            try:
                stop = positive(self.stop_loss_price)
            except ValueError as error:
                raise FuturesGridEngineError(
                    "FUTURES_GRID_SL_INVALID", "stop_loss_price pozitif decimal olmalıdır."
                ) from error
            lower = positive(rendered[0])
            upper = positive(rendered[-1])
            if self.direction is FuturesGridDirection.LONG and stop >= lower:
                raise FuturesGridEngineError(
                    "FUTURES_GRID_SL_INVALID", "LONG stop_loss_price alt sınırın altında olmalıdır."
                )
            if self.direction is FuturesGridDirection.SHORT and stop <= upper:
                raise FuturesGridEngineError(
                    "FUTURES_GRID_SL_INVALID", "SHORT stop_loss_price üst sınırın üstünde olmalıdır."
                )
        take_profit = None
        if self.take_profit_pct is not None:
            take_profit = _ratio(self.take_profit_pct, "take_profit_pct")
            if take_profit == 0:
                raise FuturesGridEngineError(
                    "FUTURES_GRID_TP_INVALID", "take_profit_pct sıfırdan büyük olmalıdır."
                )
        trailing_up = None
        if self.trailing_up_pct is not None:
            trailing_up = _ratio(self.trailing_up_pct, "trailing_up_pct")
            if trailing_up == 0:
                raise FuturesGridEngineError(
                    "FUTURES_GRID_TRAIL_INVALID", "trailing_up_pct sıfırdan büyük olmalıdır."
                )
        trailing_down = None
        if self.trailing_down_pct is not None:
            trailing_down = _ratio(self.trailing_down_pct, "trailing_down_pct")
            if trailing_down == 0:
                raise FuturesGridEngineError(
                    "FUTURES_GRID_TRAIL_INVALID", "trailing_down_pct sıfırdan büyük olmalıdır."
                )
        tiers = self.risk_tiers
        if not isinstance(tiers, tuple) or any(not isinstance(tier, IsolatedRiskTier) for tier in tiers):
            raise FuturesGridEngineError(
                "FUTURES_GRID_TIER_INVALID", "risk_tiers IsolatedRiskTier tuple olmalıdır."
            )
        canonical = "|".join(
            [
                ENGINE_REVISION,
                base,
                quote,
                self.direction.value,
                self.mode.value,
                exact_text(positive(rendered[0])),
                exact_text(positive(rendered[-1])),
                str(self.interval_count),
                exact_text(investment),
                str(self.leverage),
                exact_text(step),
                exact_text(fee),
                exact_text(stop) if stop is not None else "",
                exact_text(take_profit) if take_profit is not None else "",
                exact_text(trailing_up) if trailing_up is not None else "",
                exact_text(trailing_down) if trailing_down is not None else "",
                ",".join(tier.tier_id for tier in tiers),
            ]
        )
        fingerprint = hashlib.sha256(canonical.encode("ascii")).hexdigest()[:16]
        object.__setattr__(self, "base_asset", base)
        object.__setattr__(self, "quote_asset", quote)
        object.__setattr__(self, "lower_price", exact_text(positive(rendered[0])))
        object.__setattr__(self, "upper_price", exact_text(positive(rendered[-1])))
        object.__setattr__(self, "investment_quote", exact_text(investment))
        object.__setattr__(self, "base_step_size", exact_text(step))
        object.__setattr__(self, "fee_rate", exact_text(fee))
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
class FuturesGridState:
    """Exact futures grid holdings; strings are canonical decimal text."""

    status: FuturesGridStatus
    config_fingerprint: str
    levels: tuple[str, ...]
    pending: tuple[str, ...]
    locked_margin: tuple[str, ...]
    open_lots: tuple[FuturesGridLot, ...]
    wallet_free: str
    last_price: str | None
    entry_price: str | None
    fills: tuple[FuturesGridFill, ...]
    funding_events: tuple[str, ...]
    realized_gross_pnl: str
    fees_paid_quote: str
    funding_cashflow: str
    cycles_closed: int
    trailing_shifts: int
    next_fill_seq: int
    liq_estimate_price: str | None
    liq_estimate_tier: str | None
    last_time_us: int | None


@dataclass(frozen=True, slots=True)
class FuturesGridTickResult:
    """One tick outcome: resulting state plus accepted fills and coarse events."""

    state: FuturesGridState
    fills: tuple[FuturesGridFill, ...]
    events: tuple[str, ...]


def _direction_sign(config: FuturesGridConfig) -> Q:
    return Q(1) if config.direction is FuturesGridDirection.LONG else Q(-1)


def _open_side(config: FuturesGridConfig) -> str:
    return _BUY if config.direction is FuturesGridDirection.LONG else _SELL


def _close_side(config: FuturesGridConfig) -> str:
    return _SELL if config.direction is FuturesGridDirection.LONG else _BUY


def create_grid(config: FuturesGridConfig) -> FuturesGridState:
    """Create an uninitialized grid waiting for the first in-range price."""
    if not isinstance(config, FuturesGridConfig):
        raise FuturesGridEngineError("FUTURES_GRID_CONFIG_INVALID", "Grid config geçersiz.")
    count = config.interval_count
    return FuturesGridState(
        status=FuturesGridStatus.WAIT,
        config_fingerprint=config.fingerprint,
        levels=config.levels,
        pending=tuple(_NONE for _ in range(count)),
        locked_margin=tuple("0" for _ in range(count)),
        open_lots=(),
        wallet_free="0",
        last_price=None,
        entry_price=None,
        fills=(),
        funding_events=(),
        realized_gross_pnl="0",
        fees_paid_quote="0",
        funding_cashflow="0",
        cycles_closed=0,
        trailing_shifts=0,
        next_fill_seq=1,
        liq_estimate_price=None,
        liq_estimate_tier=None,
        last_time_us=None,
    )


def _levels_below(levels: tuple[Q, ...], price: Q) -> int:
    index = 0
    while index < len(levels) - 1 and not price < levels[index + 1]:
        index += 1
    return index


def _mutable(state: FuturesGridState) -> dict[str, object]:
    return {
        "pending": list(state.pending),
        "locked_margin": [number(value) for value in state.locked_margin],
        "lots": [
            {
                "interval": lot.interval,
                "quantity": number(lot.quantity),
                "entry": number(lot.entry_price),
                "margin": number(lot.locked_margin),
            }
            for lot in state.open_lots
        ],
        "wallet": number(state.wallet_free),
        "fills": list(state.fills),
        "funding": list(state.funding_events),
        "realized": number(state.realized_gross_pnl),
        "fees": number(state.fees_paid_quote),
        "funding_cash": number(state.funding_cashflow),
        "cycles": state.cycles_closed,
        "seq": state.next_fill_seq,
        "last_time": state.last_time_us,
    }


def _accept_fill(
    work: dict[str, object],
    config: FuturesGridConfig,
    *,
    side: FuturesGridFillSide,
    price: Q,
    quantity: Q,
    time_us: int,
) -> FuturesGridFill:
    seq = int(work["seq"])
    fill = FuturesGridFill(
        fill_id=f"fgrid:{seq}",
        side=side,
        price=exact_text(price),
        quantity=exact_text(quantity),
        effective_time_us=time_us,
    )
    fills = work["fills"]
    assert isinstance(fills, list)
    fills.append(fill)
    notional = bounded(price * quantity)
    fee = bounded(notional * number(config.fee_rate))
    work["fees"] = bounded(work["fees"] + fee)  # type: ignore[operator]
    work["wallet"] = bounded(work["wallet"] - fee)  # type: ignore[operator]
    work["seq"] = seq + 1
    work["last_time"] = time_us
    return fill


def _open_lot(
    work: dict[str, object],
    config: FuturesGridConfig,
    *,
    interval: int,
    price: Q,
    quantity: Q,
    time_us: int,
    fills: list[FuturesGridFill],
    from_locked: Q | None = None,
) -> None:
    """Open a lot; margin comes from free wallet unless `from_locked` moves a lock."""
    margin = bounded(price * quantity / config.leverage)
    wallet = work["wallet"]
    assert isinstance(wallet, Q)
    if from_locked is None:
        if margin > wallet:
            raise FuturesGridEngineError(
                "FUTURES_GRID_MARGIN_INSUFFICIENT", "Açılış için serbest marjin yetersiz."
            )
        work["wallet"] = bounded(wallet - margin)
    else:
        if margin > from_locked:
            raise FuturesGridEngineError(
                "FUTURES_GRID_MARGIN_INSUFFICIENT", "Kilitli marjin açılışa yetmiyor."
            )
        work["wallet"] = bounded(wallet + from_locked - margin)
    lots = work["lots"]
    assert isinstance(lots, list)
    lots.append({"interval": interval, "quantity": quantity, "entry": price, "margin": margin})
    side = FuturesGridFillSide.BUY if _open_side(config) == _BUY else FuturesGridFillSide.SELL
    fills.append(_accept_fill(work, config, side=side, price=price, quantity=quantity, time_us=time_us))


def _close_interval_parcels(
    work: dict[str, object],
    config: FuturesGridConfig,
    *,
    interval: int,
    price: Q,
    time_us: int,
    fills: list[FuturesGridFill],
) -> Q:
    """Close every lot tagged to `interval` FIFO; returns closed quantity."""
    lots = work["lots"]
    assert isinstance(lots, list)
    tagged = [lot for lot in lots if lot["interval"] == interval]
    if not tagged:
        return Q(0)
    closed = sum((lot["quantity"] for lot in tagged), Q(0))
    sign = _direction_sign(config)
    for lot in tagged:
        take = lot["quantity"]
        pnl = bounded(sign * (price - lot["entry"]) * take)
        work["realized"] = bounded(work["realized"] + pnl)  # type: ignore[operator]
        work["wallet"] = bounded(work["wallet"] + lot["margin"] + pnl)  # type: ignore[operator]
        lots.remove(lot)
    side = FuturesGridFillSide.BUY if _close_side(config) == _BUY else FuturesGridFillSide.SELL
    fills.append(_accept_fill(work, config, side=side, price=price, quantity=closed, time_us=time_us))
    work["cycles"] = int(work["cycles"]) + 1
    return bounded(closed)


def _close_all_parcels(
    work: dict[str, object],
    config: FuturesGridConfig,
    *,
    price: Q,
    time_us: int,
    fills: list[FuturesGridFill],
) -> None:
    lots = work["lots"]
    assert isinstance(lots, list)
    for interval in sorted({lot["interval"] for lot in lots}):
        _close_interval_parcels(work, config, interval=interval, price=price, time_us=time_us, fills=fills)




def _position_totals(work: dict[str, object]) -> tuple[Q, Q]:
    lots = work["lots"]
    assert isinstance(lots, list)
    qty = sum((lot["quantity"] for lot in lots), Q(0))
    cost = sum((lot["quantity"] * lot["entry"] for lot in lots), Q(0))
    return bounded(qty), bounded(cost)


def _align_margin_qty(price: Q, qty: Q, leverage: int, step: Q) -> Q:
    """Largest step-aligned qty at or below `qty` whose margin is exactly renderable.

    margin = price*qty/leverage must survive `exact_text` at freeze time;
    stepping down one step at a time finds an exact qty within `leverage`
    steps (a multiple of leverage/gcd always lands in any run of
    `leverage` consecutive step counts). Returns 0 when the walk would
    empty the parcel, letting callers reuse their abandon path.
    """
    candidate = qty
    for _ in range(leverage + 1):
        if candidate <= 0:
            return Q(0)
        try:
            exact_text(bounded(price * candidate / leverage))
            return candidate
        except ValueError:
            candidate = bounded(candidate - step)
    return Q(0)


def _plan_from_wallet(
    work: dict[str, object],
    config: FuturesGridConfig,
    levels: tuple[Q, ...],
    *,
    price: Q,
    time_us: int,
    fills: list[FuturesGridFill],
) -> None:
    """Place OPEN pendings on the far side and market-open the near side.

    LONG mirrors spot: below-entry intervals hold BUY opens (margin
    locked), above-entry intervals are market-opened at entry then hold
    SELL closes. SHORT mirrors vertically: above-entry SELL opens,
    below-entry market-opened shorts with BUY closes. Shortfalls leave
    intervals NONE instead of rounding silently.
    """

    step = number(config.base_step_size)
    per_grid = number(config.quote_per_grid)
    margin_per_grid = bounded(per_grid / config.leverage)
    entry_index = _levels_below(levels, price)
    pending = work["pending"]
    locked_margin = work["locked_margin"]
    assert isinstance(pending, list)
    assert isinstance(locked_margin, list)
    wallet = work["wallet"]
    assert isinstance(wallet, Q)
    long = config.direction is FuturesGridDirection.LONG
    open_ranges = (
        [range(entry_index - 1, -1, -1), range(entry_index, config.interval_count)]
        if long
        else [range(entry_index, config.interval_count), range(entry_index - 1, -1, -1)]
    )
    open_side = _open_side(config)
    for interval in range(config.interval_count):
        pending[interval] = _NONE
        locked_margin[interval] = Q(0)
    for interval in open_ranges[0]:
        if wallet < margin_per_grid:
            break
        wallet = bounded(wallet - margin_per_grid)
        pending[interval] = open_side
        locked_margin[interval] = margin_per_grid
    work["wallet"] = wallet
    base_unit = _align_margin_qty(price, align(bounded(per_grid / price), step, up=False), config.leverage, step)
    for interval in open_ranges[1]:
        wallet = work["wallet"]
        assert isinstance(wallet, Q)
        if base_unit <= 0:
            break
        if wallet < bounded(base_unit * price / config.leverage):
            break
        _open_lot(work, config, interval=interval, price=price, quantity=base_unit, time_us=time_us, fills=fills)
        pending[interval] = _close_side(config)


def _release_opens(work: dict[str, object], config: FuturesGridConfig) -> None:
    """Release OPEN-side margin locks; parcels stay with their intervals."""
    pending = work["pending"]
    locked_margin = work["locked_margin"]
    assert isinstance(pending, list)
    assert isinstance(locked_margin, list)
    open_side = _open_side(config)
    for interval in range(config.interval_count):
        if pending[interval] == open_side:
            work["wallet"] = bounded(work["wallet"] + locked_margin[interval])  # type: ignore[operator]
            pending[interval] = _NONE
            locked_margin[interval] = Q(0)


def _unrealized(work: dict[str, object], config: FuturesGridConfig, *, mark: Q) -> Q:
    lots = work["lots"]
    assert isinstance(lots, list)
    sign = _direction_sign(config)
    return bounded(sum((sign * (mark - lot["entry"]) * lot["quantity"] for lot in lots), Q(0)))


def grid_equity_quote(state: FuturesGridState, config: FuturesGridConfig, *, mark_price: str) -> str:
    """Quote equity at an explicit mark: wallet + locked + unrealized."""
    if not isinstance(state, FuturesGridState) or not isinstance(config, FuturesGridConfig):
        raise FuturesGridEngineError("FUTURES_GRID_INPUT_INVALID", "State veya config geçersiz.")
    if state.config_fingerprint != config.fingerprint:
        raise FuturesGridEngineError("FUTURES_GRID_CONFIG_MISMATCH", "State bu config ile açılmadı.")
    try:
        mark = positive(mark_price)
    except ValueError as error:
        raise FuturesGridEngineError(
            "FUTURES_GRID_MARK_INVALID", "mark_price pozitif decimal olmalıdır."
        ) from error
    wallet = number(state.wallet_free)
    locked = sum((number(value) for value in state.locked_margin), Q(0))
    parcel_margin = sum((number(lot.locked_margin) for lot in state.open_lots), Q(0))
    sign = _direction_sign(config)
    lots_value = sum(
        (sign * (mark - number(lot.entry_price)) * number(lot.quantity) for lot in state.open_lots),
        Q(0),
    )
    return exact_text(bounded(wallet + locked + parcel_margin + lots_value))


def _estimate_liquidation(
    config: FuturesGridConfig, work: dict[str, object], *, mark: Q, wallet_total: Q
) -> tuple[str, str] | None:
    """Totals-form isolated root; None when unprovable (never guessed).

    Same mathematics as the verified fixed-tier estimate, fed with
    position totals instead of an averaged entry so multi-lot grids
    stay exact. Tier selection follows mark notional; the root must
    land inside the tier and render as exact decimal.
    """

    if not config.risk_tiers:
        return None
    qty, cost = _position_totals(work)
    if qty <= 0:
        return None
    mark_notional = bounded(qty * mark)
    tier = None
    for candidate in config.risk_tiers:
        floor = number(candidate.notional_floor)
        cap = None if candidate.notional_cap is None else number(candidate.notional_cap)
        if floor <= mark_notional and (cap is None or mark_notional < cap):
            tier = candidate
            break
    if tier is None:
        return None
    rate = number(tier.maintenance_rate)
    maintenance = number(tier.maintenance_amount)
    if config.direction is FuturesGridDirection.LONG:
        denominator = bounded(qty * (1 - rate))
        if denominator <= 0:
            return None
        root = bounded((cost - wallet_total - maintenance) / denominator)
    else:
        denominator = bounded(qty * (1 + rate))
        root = bounded((wallet_total + cost + maintenance) / denominator)
    if root <= 0:
        return None
    root_notional = bounded(qty * root)
    floor = number(tier.notional_floor)
    cap = None if tier.notional_cap is None else number(tier.notional_cap)
    if not floor <= root_notional or (cap is not None and not root_notional < cap):
        return None
    try:
        return exact_text(root), tier.tier_id
    except ValueError:
        return None


def _freeze(
    config: FuturesGridConfig,
    work: dict[str, object],
    *,
    status: FuturesGridStatus,
    levels: tuple[str, ...],
    last_price: Q,
    entry_price: Q | None,
    trailing_shifts: int,
    liq_price: str | None,
    liq_tier: str | None,
) -> FuturesGridState:
    pending = work["pending"]
    locked_margin = work["locked_margin"]
    lots = work["lots"]
    fills = work["fills"]
    funding = work["funding"]
    assert isinstance(pending, list)
    assert isinstance(locked_margin, list)
    assert isinstance(lots, list)
    assert isinstance(fills, list)
    assert isinstance(funding, list)
    return FuturesGridState(
        status=status,
        config_fingerprint=config.fingerprint,
        levels=levels,
        pending=tuple(str(side) for side in pending),
        locked_margin=tuple(exact_text(margin) for margin in locked_margin),
        open_lots=tuple(
            FuturesGridLot(
                interval=int(lot["interval"]),
                quantity=exact_text(lot["quantity"]),
                entry_price=exact_text(lot["entry"]),
                locked_margin=exact_text(lot["margin"]),
            )
            for lot in lots
        ),
        wallet_free=exact_text(work["wallet"]),  # type: ignore[arg-type]
        last_price=exact_text(last_price),
        entry_price=exact_text(entry_price) if entry_price is not None else None,
        fills=tuple(fills),
        funding_events=tuple(str(item) for item in funding),
        realized_gross_pnl=exact_text(work["realized"]),  # type: ignore[arg-type]
        fees_paid_quote=exact_text(work["fees"]),  # type: ignore[arg-type]
        funding_cashflow=exact_text(work["funding_cash"]),  # type: ignore[arg-type]
        cycles_closed=int(work["cycles"]),
        trailing_shifts=trailing_shifts,
        next_fill_seq=int(work["seq"]),
        liq_estimate_price=liq_price,
        liq_estimate_tier=liq_tier,
        last_time_us=work["last_time"],  # type: ignore[arg-type]
    )


def _refresh_liq(
    config: FuturesGridConfig, work: dict[str, object], *, mark: Q
) -> tuple[str | None, str | None]:
    wallet = work["wallet"]
    locked = work["locked_margin"]
    lots = work["lots"]
    assert isinstance(wallet, Q)
    assert isinstance(locked, list)
    assert isinstance(lots, list)
    total = bounded(wallet + sum(locked, Q(0)) + sum((lot["margin"] for lot in lots), Q(0)))
    estimate = _estimate_liquidation(config, work, mark=mark, wallet_total=total)
    if estimate is None:
        return None, None
    return estimate


def _flatten(
    work: dict[str, object],
    config: FuturesGridConfig,
    *,
    price: Q,
    time_us: int,
    fills: list[FuturesGridFill],
) -> None:
    pending = work["pending"]
    locked = work["locked_margin"]
    assert isinstance(pending, list)
    assert isinstance(locked, list)
    for interval in range(config.interval_count):
        work["wallet"] = bounded(work["wallet"] + locked[interval])  # type: ignore[operator]
        pending[interval] = _NONE
        locked[interval] = Q(0)
    _close_all_parcels(work, config, price=price, time_us=time_us, fills=fills)


def _shift_levels(
    config: FuturesGridConfig, levels: tuple[Q, ...], *, price: Q, bound: Q
) -> tuple[str, ...] | None:
    if config.mode is FuturesGridMode.ARITHMETIC:
        shifted = tuple(bounded(level + (price - bound)) for level in levels)
    else:
        factor = bounded(price / bound)
        shifted = tuple(bounded(level * factor) for level in levels)
    if shifted[0] <= 0:
        return None
    if config.mode is FuturesGridMode.GEOMETRIC:
        assert config.price_tick is not None and config.tick_origin is not None
        tick = number(config.price_tick)
        origin = number(config.tick_origin)
        if any(align(level, tick, up=False, origin=origin) != level for level in shifted):
            return None
    try:
        return tuple(exact_text(level) for level in shifted)
    except ValueError:
        return None


def _check_time(work: dict[str, object], time_us: int) -> None:
    if type(time_us) is not int or time_us < 0:
        raise FuturesGridEngineError("FUTURES_GRID_TIME_INVALID", "Tick zamanı geçersiz.")
    last_time = work["last_time"]
    if last_time is not None and time_us < last_time:
        raise FuturesGridEngineError("FUTURES_GRID_TIME_ORDER", "Tick zamanı geriye gidemez.")


def apply_tick(
    state: FuturesGridState, config: FuturesGridConfig, *, price: str, time_us: int
) -> FuturesGridTickResult:
    """Advance the grid by one timestamped price tick.

    Order per tick: level-cross fills, then stop-loss flatten, then
    trailing re-anchor, then liquidation-estimate breach, then
    take-profit flatten. Terminal states are returned unchanged.
    """

    if not isinstance(state, FuturesGridState) or not isinstance(config, FuturesGridConfig):
        raise FuturesGridEngineError("FUTURES_GRID_INPUT_INVALID", "State veya config geçersiz.")
    if state.config_fingerprint != config.fingerprint:
        raise FuturesGridEngineError("FUTURES_GRID_CONFIG_MISMATCH", "State bu config ile açılmadı.")
    try:
        tick = positive(price)
    except ValueError as error:
        raise FuturesGridEngineError(
            "FUTURES_GRID_TICK_INVALID", "tick fiyatı pozitif decimal olmalıdır."
        ) from error
    if state.status in (
        FuturesGridStatus.DONE_SL,
        FuturesGridStatus.DONE_TP,
        FuturesGridStatus.DONE_LIQ_ESTIMATE,
    ):
        return FuturesGridTickResult(state=state, fills=(), events=())

    fills: list[FuturesGridFill] = []
    events: list[str] = []
    levels = tuple(number(value) for value in state.levels)
    step = number(config.base_step_size)
    work = _mutable(state)
    _check_time(work, time_us)
    pending = work["pending"]
    locked_margin = work["locked_margin"]
    assert isinstance(pending, list)
    assert isinstance(locked_margin, list)
    long = config.direction is FuturesGridDirection.LONG
    open_side = _open_side(config)
    close_side = _close_side(config)

    if state.status is FuturesGridStatus.WAIT:
        if levels[0] <= tick <= levels[-1]:
            work["wallet"] = number(config.investment_quote)
            _plan_from_wallet(work, config, levels, price=tick, time_us=time_us, fills=fills)
            if all(side == _NONE for side in pending):
                raise FuturesGridEngineError(
                    "FUTURES_GRID_ALLOCATION_EMPTY",
                    "Giriş fiyatı tüm aralıkları boş bıraktı; yatırım aralığa göre küçük.",
                )
            events.append("GRID_INIT")
            liq_price, liq_tier = _refresh_liq(config, work, mark=tick)
            frozen = _freeze(
                config, work, status=FuturesGridStatus.ACTIVE, levels=state.levels,
                last_price=tick, entry_price=tick, trailing_shifts=state.trailing_shifts,
                liq_price=liq_price, liq_tier=liq_tier,
            )
            return FuturesGridTickResult(state=frozen, fills=tuple(fills), events=tuple(events))
        work["last_time"] = time_us
        frozen = _freeze(
            config, work, status=FuturesGridStatus.WAIT, levels=state.levels,
            last_price=tick, entry_price=None, trailing_shifts=state.trailing_shifts,
            liq_price=None, liq_tier=None,
        )
        return FuturesGridTickResult(state=frozen, fills=(), events=("GRID_WAIT",))

    last = number(state.last_price) if state.last_price is not None else tick
    if tick < last:
        if long:
            crossed = [
                interval
                for interval in range(config.interval_count - 1, -1, -1)
                if pending[interval] == _BUY and tick <= levels[interval] < last
            ]
            for interval in crossed:
                level_price = levels[interval]
                budget = locked_margin[interval]
                qty = _align_margin_qty(level_price, align(bounded(budget * config.leverage / level_price), step, up=False), config.leverage, step)
                pending[interval] = _NONE
                locked_margin[interval] = Q(0)
                if qty <= 0:
                    work["wallet"] = bounded(work["wallet"] + budget)  # type: ignore[operator]
                    events.append("GRID_LEVEL_ABANDONED")
                    continue
                _open_lot(work, config, interval=interval, price=level_price, quantity=qty, time_us=time_us,
                            fills=fills, from_locked=budget)
                pending[interval] = close_side
        else:
            crossed = [
                interval
                for interval in range(config.interval_count - 1, -1, -1)
                if pending[interval] == _BUY and tick <= levels[interval] < last
            ]
            for interval in crossed:
                closed = _close_interval_parcels(work, config, interval=interval, price=levels[interval], time_us=time_us, fills=fills)
                if closed == 0:
                    events.append("GRID_CLOSE_SKIPPED_EMPTY")
                    continue
                pending[interval] = _NONE
                _replace_open(work, config, interval=interval, events=events)
    elif tick > last:
        if long:
            crossed = [
                interval
                for interval in range(config.interval_count)
                if pending[interval] == _SELL and last < levels[interval + 1] <= tick
            ]
            for interval in crossed:
                closed = _close_interval_parcels(work, config, interval=interval, price=levels[interval + 1], time_us=time_us, fills=fills)
                if closed == 0:
                    events.append("GRID_CLOSE_SKIPPED_EMPTY")
                    continue
                pending[interval] = _NONE
                _replace_open(work, config, interval=interval, events=events)
        else:
            crossed = [
                interval
                for interval in range(config.interval_count)
                if pending[interval] == _SELL and last < levels[interval + 1] <= tick
            ]
            for interval in crossed:
                level_price = levels[interval + 1]
                budget = locked_margin[interval]
                qty = _align_margin_qty(level_price, align(bounded(budget * config.leverage / level_price), step, up=False), config.leverage, step)
                pending[interval] = _NONE
                locked_margin[interval] = Q(0)
                if qty <= 0:
                    work["wallet"] = bounded(work["wallet"] + budget)  # type: ignore[operator]
                    events.append("GRID_LEVEL_ABANDONED")
                    continue
                _open_lot(work, config, interval=interval, price=level_price, quantity=qty, time_us=time_us,
                            fills=fills, from_locked=budget)
                pending[interval] = close_side
    work["last_time"] = time_us if work["last_time"] is None else max(work["last_time"], time_us)  # type: ignore[operator]

    stop = number(config.stop_loss_price) if config.stop_loss_price is not None else None
    stop_hit = stop is not None and (tick <= stop if long else tick >= stop)
    if stop_hit:
        _flatten(work, config, price=tick, time_us=time_us, fills=fills)
        events.append("GRID_STOP_LOSS")
        frozen = _freeze(
            config, work, status=FuturesGridStatus.DONE_SL, levels=state.levels,
            last_price=tick, entry_price=number(state.entry_price) if state.entry_price is not None else None,
            trailing_shifts=state.trailing_shifts, liq_price=None, liq_tier=None,
        )
        return FuturesGridTickResult(state=frozen, fills=tuple(fills), events=tuple(events))

    current_levels = state.levels
    if config.trailing_up_pct is not None and tick > levels[-1] * (1 + number(config.trailing_up_pct)):
        shifted = _shift_levels(config, levels, price=tick, bound=levels[-1])
        if shifted is None:
            events.append("GRID_TRAIL_SKIPPED")
        else:
            _release_opens(work, config)
            _plan_from_wallet(work, config, tuple(number(value) for value in shifted), price=tick, time_us=time_us, fills=fills)
            current_levels = shifted
            events.append("GRID_TRAIL_UP")
    elif config.trailing_down_pct is not None and tick < levels[0] * (1 - number(config.trailing_down_pct)):
        shifted = _shift_levels(config, levels, price=tick, bound=levels[0])
        if shifted is None:
            events.append("GRID_TRAIL_SKIPPED")
        else:
            _release_opens(work, config)
            _plan_from_wallet(work, config, tuple(number(value) for value in shifted), price=tick, time_us=time_us, fills=fills)
            current_levels = shifted
            events.append("GRID_TRAIL_DOWN")

    liq_price, liq_tier = _refresh_liq(config, work, mark=tick)
    breached = liq_price is not None and (
        tick <= number(liq_price) if long else tick >= number(liq_price)
    )
    if breached:
        _flatten(work, config, price=tick, time_us=time_us, fills=fills)
        events.append("GRID_LIQ_ESTIMATE_HIT")
        frozen = _freeze(
            config, work, status=FuturesGridStatus.DONE_LIQ_ESTIMATE, levels=current_levels,
            last_price=tick, entry_price=number(state.entry_price) if state.entry_price is not None else None,
            trailing_shifts=state.trailing_shifts + sum(1 for event in events if event in ("GRID_TRAIL_UP", "GRID_TRAIL_DOWN")),
            liq_price=liq_price, liq_tier=liq_tier,
        )
        return FuturesGridTickResult(state=frozen, fills=tuple(fills), events=tuple(events))

    if config.take_profit_pct is not None:
        equity = number(
            grid_equity_quote(
                _freeze(
                    config, work, status=FuturesGridStatus.ACTIVE, levels=current_levels,
                    last_price=tick,
                    entry_price=number(state.entry_price) if state.entry_price is not None else None,
                    trailing_shifts=state.trailing_shifts, liq_price=liq_price, liq_tier=liq_tier,
                ),
                config, mark_price=exact_text(tick),
            )
        )
        target = bounded(number(config.investment_quote) * (1 + number(config.take_profit_pct)))
        if equity >= target:
            _flatten(work, config, price=tick, time_us=time_us, fills=fills)
            events.append("GRID_TAKE_PROFIT")
            frozen = _freeze(
                config, work, status=FuturesGridStatus.DONE_TP, levels=current_levels,
                last_price=tick, entry_price=number(state.entry_price) if state.entry_price is not None else None,
                trailing_shifts=state.trailing_shifts + sum(1 for event in events if event in ("GRID_TRAIL_UP", "GRID_TRAIL_DOWN")),
                liq_price=None, liq_tier=None,
            )
            return FuturesGridTickResult(state=frozen, fills=tuple(fills), events=tuple(events))

    frozen = _freeze(
        config, work, status=FuturesGridStatus.ACTIVE, levels=current_levels,
        last_price=tick, entry_price=number(state.entry_price) if state.entry_price is not None else None,
        trailing_shifts=state.trailing_shifts + sum(1 for event in events if event in ("GRID_TRAIL_UP", "GRID_TRAIL_DOWN")),
        liq_price=liq_price, liq_tier=liq_tier,
    )
    return FuturesGridTickResult(state=frozen, fills=tuple(fills), events=tuple(events))


def _replace_open(
    work: dict[str, object], config: FuturesGridConfig, *, interval: int, events: list[str]
) -> None:
    """Place a fresh OPEN on a closed interval, or leave it NONE when broke."""
    margin_per_grid = bounded(number(config.quote_per_grid) / config.leverage)
    wallet = work["wallet"]
    assert isinstance(wallet, Q)
    pending = work["pending"]
    locked = work["locked_margin"]
    assert isinstance(pending, list)
    assert isinstance(locked, list)
    if wallet < margin_per_grid:
        events.append("GRID_LEVEL_UNFUNDED")
        return
    work["wallet"] = bounded(wallet - margin_per_grid)
    pending[interval] = _open_side(config)
    locked[interval] = margin_per_grid


def apply_funding(
    state: FuturesGridState,
    config: FuturesGridConfig,
    *,
    rate: str,
    mark_price: str,
    time_us: int,
    event_id: str,
) -> FuturesGridState:
    """Accrue one explicit funding cashflow derived from (rate, mark).

    Longs pay when the rate is positive, shorts receive; the cashflow is
    derived inside the engine from position totals, never trusted from
    the caller. Flat or terminal states pass through unchanged.
    """

    if not isinstance(state, FuturesGridState) or not isinstance(config, FuturesGridConfig):
        raise FuturesGridEngineError("FUTURES_GRID_INPUT_INVALID", "State veya config geçersiz.")
    if state.config_fingerprint != config.fingerprint:
        raise FuturesGridEngineError("FUTURES_GRID_CONFIG_MISMATCH", "State bu config ile açılmadı.")
    if (
        not isinstance(event_id, str)
        or not event_id
        or len(event_id) > 128
        or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789:_-" for ch in event_id)
    ):
        raise FuturesGridEngineError("FUTURES_GRID_FUNDING_ID_INVALID", "Funding event kimliği geçersiz.")
    if type(time_us) is not int or time_us < 0:
        raise FuturesGridEngineError("FUTURES_GRID_TIME_INVALID", "Funding zamanı geçersiz.")
    if state.last_time_us is not None and time_us < state.last_time_us:
        raise FuturesGridEngineError("FUTURES_GRID_TIME_ORDER", "Funding zamanı geriye gidemez.")
    try:
        parsed_rate = number(rate)
        mark = positive(mark_price)
    except ValueError as error:
        raise FuturesGridEngineError(
            "FUTURES_GRID_FUNDING_INVALID", "Funding oranı/mark exact decimal olmalıdır."
        ) from error
    if abs(parsed_rate) > _MAX_FUNDING_RATE:
        raise FuturesGridEngineError(
            "FUTURES_GRID_FUNDING_INVALID", "Funding oranı ±%2 bandı dışında; veri hatası sayılır."
        )
    if any(item.split("=", 1)[0] == event_id for item in state.funding_events):
        raise FuturesGridEngineError("FUTURES_GRID_FUNDING_DUPLICATE", "Funding event tekrarlandı.")
    if state.status is not FuturesGridStatus.ACTIVE:
        return state
    work = _mutable(state)
    qty, _ = _position_totals(work)
    if qty == 0:
        return state
    cashflow = bounded(-parsed_rate * qty * mark * _direction_sign(config))
    work["wallet"] = bounded(work["wallet"] + cashflow)  # type: ignore[operator]
    work["funding_cash"] = bounded(work["funding_cash"] + cashflow)  # type: ignore[operator]
    funding = work["funding"]
    assert isinstance(funding, list)
    funding.append(f"{event_id}={exact_text(cashflow)}")
    work["last_time"] = time_us
    last = number(state.last_price) if state.last_price is not None else mark
    liq_price, liq_tier = _refresh_liq(config, work, mark=last)
    return _freeze(
        config, work, status=state.status, levels=state.levels,
        last_price=last, entry_price=number(state.entry_price) if state.entry_price is not None else None,
        trailing_shifts=state.trailing_shifts, liq_price=liq_price, liq_tier=liq_tier,
    )


def snapshot_grid(state: FuturesGridState) -> dict[str, object]:
    """Render a JSON-safe snapshot for persistence (G3-c runtime)."""
    if not isinstance(state, FuturesGridState):
        raise FuturesGridEngineError("FUTURES_GRID_INPUT_INVALID", "State geçersiz.")
    return {
        "engine_revision": ENGINE_REVISION,
        "config_fingerprint": state.config_fingerprint,
        "status": state.status.value,
        "levels": list(state.levels),
        "pending": list(state.pending),
        "locked_margin": list(state.locked_margin),
        "open_lots": [
            {
                "interval": lot.interval,
                "quantity": lot.quantity,
                "entry_price": lot.entry_price,
                "locked_margin": lot.locked_margin,
            }
            for lot in state.open_lots
        ],
        "wallet_free": state.wallet_free,
        "last_price": state.last_price,
        "entry_price": state.entry_price,
        "fills": [
            {
                "fill_id": fill.fill_id,
                "side": fill.side.value,
                "price": fill.price,
                "quantity": fill.quantity,
                "effective_time_us": fill.effective_time_us,
            }
            for fill in state.fills
        ],
        "funding_events": list(state.funding_events),
        "realized_gross_pnl": state.realized_gross_pnl,
        "fees_paid_quote": state.fees_paid_quote,
        "funding_cashflow": state.funding_cashflow,
        "cycles_closed": state.cycles_closed,
        "trailing_shifts": state.trailing_shifts,
        "next_fill_seq": state.next_fill_seq,
        "liq_estimate_price": state.liq_estimate_price,
        "liq_estimate_tier": state.liq_estimate_tier,
        "last_time_us": state.last_time_us,
    }


def restore_grid(snapshot: dict[str, object], config: FuturesGridConfig) -> FuturesGridState:
    """Rebuild grid state; rejects foreign revisions, configs, and shapes."""
    if not isinstance(snapshot, dict) or not isinstance(config, FuturesGridConfig):
        raise FuturesGridEngineError("FUTURES_GRID_SNAPSHOT_INVALID", "Snapshot veya config geçersiz.")
    if snapshot.get("engine_revision") != ENGINE_REVISION:
        raise FuturesGridEngineError(
            "FUTURES_GRID_SNAPSHOT_REVISION_INVALID", "Snapshot motor revizyonu uyuşmuyor."
        )
    if snapshot.get("config_fingerprint") != config.fingerprint:
        raise FuturesGridEngineError("FUTURES_GRID_CONFIG_MISMATCH", "Snapshot bu config ile açılmadı.")
    try:
        status = FuturesGridStatus(str(snapshot["status"]))
        levels = tuple(str(value) for value in snapshot["levels"])  # type: ignore[index]
        pending = tuple(str(value) for value in snapshot["pending"])  # type: ignore[index]
        locked_margin = tuple(str(value) for value in snapshot["locked_margin"])  # type: ignore[index]
        raw_lots = snapshot["open_lots"]
        assert isinstance(raw_lots, list)
        lots: list[FuturesGridLot] = []
        for raw in raw_lots:
            assert isinstance(raw, dict)
            interval = raw["interval"]
            assert type(interval) is int and 0 <= interval < config.interval_count
            quantity = positive(str(raw["quantity"]))
            entry = positive(str(raw["entry_price"]))
            margin = number(str(raw["locked_margin"]))
            assert margin >= 0
            lots.append(
                FuturesGridLot(
                    interval=interval,
                    quantity=exact_text(quantity),
                    entry_price=exact_text(entry),
                    locked_margin=exact_text(margin),
                )
            )
        raw_fills = snapshot["fills"]
        assert isinstance(raw_fills, list)
        fills: list[FuturesGridFill] = []
        for raw in raw_fills:
            assert isinstance(raw, dict)
            time_us = raw["effective_time_us"]
            assert type(time_us) is int and time_us >= 0
            fills.append(
                FuturesGridFill(
                    fill_id=str(raw["fill_id"]),
                    side=FuturesGridFillSide(str(raw["side"])),
                    price=str(raw["price"]),
                    quantity=str(raw["quantity"]),
                    effective_time_us=time_us,
                )
            )
        for first, second in zip(fills, fills[1:]):
            assert first.effective_time_us <= second.effective_time_us
            assert first.fill_id != second.fill_id
        funding_events = tuple(str(value) for value in snapshot["funding_events"])  # type: ignore[index]
        for item in funding_events:
            head, _, cashflow = item.partition("=")
            assert head and cashflow
            number(cashflow)
        last_price = snapshot["last_price"]
        entry_price = snapshot["entry_price"]
        liq_price = snapshot["liq_estimate_price"]
        last_time = snapshot["last_time_us"]
        for value in (
            levels + locked_margin + (str(snapshot["wallet_free"]),)
            + (() if last_price is None else (str(last_price),))
            + (() if entry_price is None else (str(entry_price),))
            + (str(snapshot["realized_gross_pnl"]), str(snapshot["fees_paid_quote"]), str(snapshot["funding_cashflow"]))
            + (() if liq_price is None else (str(liq_price),))
        ):
            number(value)
        liq_tier = snapshot["liq_estimate_tier"]
        assert liq_tier is None or isinstance(liq_tier, str)
        assert (liq_price is None) == (liq_tier is None)
        assert last_time is None or (type(last_time) is int and last_time >= 0)
        cycles = snapshot["cycles_closed"]
        shifts = snapshot["trailing_shifts"]
        seq = snapshot["next_fill_seq"]
        assert isinstance(cycles, int) and isinstance(shifts, int) and isinstance(seq, int)
        assert not isinstance(cycles, bool) and cycles >= 0 and shifts >= 0 and seq >= 1
        assert len(levels) == config.interval_count + 1
        assert len(pending) == len(locked_margin) == config.interval_count
        assert all(side in (_BUY, _SELL, _NONE) for side in pending)
        assert all(number(value) >= 0 for value in locked_margin)
        return FuturesGridState(
            status=status,
            config_fingerprint=config.fingerprint,
            levels=levels,
            pending=pending,
            locked_margin=locked_margin,
            open_lots=tuple(lots),
            wallet_free=str(snapshot["wallet_free"]),
            last_price=None if last_price is None else str(last_price),
            entry_price=None if entry_price is None else str(entry_price),
            fills=tuple(fills),
            funding_events=funding_events,
            realized_gross_pnl=str(snapshot["realized_gross_pnl"]),
            fees_paid_quote=str(snapshot["fees_paid_quote"]),
            funding_cashflow=str(snapshot["funding_cashflow"]),
            cycles_closed=cycles,
            trailing_shifts=shifts,
            next_fill_seq=seq,
            liq_estimate_price=None if liq_price is None else str(liq_price),
            liq_estimate_tier=None if liq_tier is None else str(liq_tier),
            last_time_us=last_time,  # type: ignore[arg-type]
        )
    except FuturesGridEngineError:
        raise
    except (AssertionError, KeyError, TypeError, ValueError) as error:
        raise FuturesGridEngineError(
            "FUTURES_GRID_SNAPSHOT_INVALID", "Snapshot şekli veya miktarları geçersiz."
        ) from error


def describe_grid(config: FuturesGridConfig) -> dict[str, object]:
    """Static grid summary for API/UI previews (no market data)."""
    if not isinstance(config, FuturesGridConfig):
        raise FuturesGridEngineError("FUTURES_GRID_CONFIG_INVALID", "Grid config geçersiz.")
    return {
        "engine_revision": ENGINE_REVISION,
        "direction": config.direction.value,
        "mode": config.mode.value,
        "levels": list(config.levels),
        "interval_count": config.interval_count,
        "investment_quote": config.investment_quote,
        "leverage": config.leverage,
        "quote_per_grid": config.quote_per_grid,
        "base_step_size": config.base_step_size,
        "fee_rate": config.fee_rate,
        "stop_loss_price": config.stop_loss_price,
        "take_profit_pct": config.take_profit_pct,
        "trailing_up_pct": config.trailing_up_pct,
        "trailing_down_pct": config.trailing_down_pct,
        "risk_tier_count": len(config.risk_tiers),
        "fingerprint": config.fingerprint,
    }
