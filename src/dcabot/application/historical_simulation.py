"""Bounded closed-bar historical simulation over the existing pure reducer."""

from dataclasses import dataclass
from time import monotonic

from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput
from dcabot.application.historical_features import (
    HistoricalFeatureError,
    HistoricalFeatureRunBinding,
    validate_historical_feature_binding,
)
from dcabot.application.historical_fixed_slice import (
    HistoricalFixedSliceAction,
    HistoricalFixedSliceResult,
    apply_fixed_slice_fill,
    fixed_slice_result,
)
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply, decision, report, target
from dcabot.domain.numbers import Q, align, exact_text, number, round_quantum, text


MAX_HISTORICAL_SIMULATION_BARS = 1_000
MAX_HISTORICAL_SIMULATION_SECONDS = 5.0
# Faz W v2 backtests fetch venue klines on demand; measured ~5,000 bars/s,
# so the cap keeps a run near 4 s. Stored/legacy runs keep the 1,000 cap.
MAX_SECTOR_BACKTEST_BARS = 20_000
EXPECTED_INTERVAL_US = {
    "1m": 60_000_000,
    "5m": 300_000_000,
    "15m": 900_000_000,
    "30m": 1_800_000_000,
    "1h": 3_600_000_000,
    "4h": 14_400_000_000,
    "1d": 86_400_000_000,
}
AVERAGE_PRICE_PLACES = 12


class HistoricalSimulationError(ValueError):
    """Raised when a bounded historical simulation cannot continue safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class HistoricalSimulationAction:
    """One deterministic state-changing action and its exact simulated fill."""

    bar_index: int
    open_time_us: int
    role: str
    raw_reference: str
    fill_price: str
    quantity: str
    fee: str
    deal_sequence: int


@dataclass(frozen=True, slots=True)
class HistoricalSimulationResult:
    """In-memory result for one bounded historical OHLCV execution."""

    execution_status: str
    application_code: str | None
    processed_bar_count: int
    first_ambiguous_bar_index: int | None
    position_status: str
    fee_amount: str
    funding_status: str
    mark_status: str
    actions: tuple[HistoricalSimulationAction, ...]
    summary: dict[str, object]
    feature_binding: HistoricalFeatureRunBinding | None = None


def simulate_historical_fixed_slice(
    dataset: HistoricalDatasetInput,
    config: Config,
    *,
    slice_qty: str,
    config_hash: str,
    timeout_seconds: float = MAX_HISTORICAL_SIMULATION_SECONDS,
) -> HistoricalFixedSliceResult:
    """Run explicit fixed-slice fills without changing the legacy historical model."""

    if len(dataset.bars) > MAX_HISTORICAL_SIMULATION_BARS:
        raise HistoricalSimulationError("BAR_SCOPE_EXCEEDED", "Dataset bar kapsamı server sınırını aşıyor.")
    if config.base_sizing != "BASE" and slice_qty is not None:
        raise HistoricalSimulationError("CONFIG_INVALID", "Fixed-slice model QUOTE base sizing desteklemez.")
    if not dataset.bars:
        raise HistoricalSimulationError("BAR_SCOPE_TOO_SMALL", "Dataset içinde simüle edilecek bar yok.")
    if timeout_seconds <= 0:
        raise HistoricalSimulationError("EXECUTION_BUDGET_EXCEEDED", "Simülasyon çalışma bütçesi geçersiz.")
    try:
        fixed_qty = number(slice_qty)
    except ValueError as exc:
        raise HistoricalSimulationError("SLICE_QTY_INVALID", "Fixed slice quantity geçersiz.") from exc
    if fixed_qty <= 0:
        raise HistoricalSimulationError("SLICE_QTY_INVALID", "Fixed slice quantity pozitif olmalıdır.")
    if align(fixed_qty, config.qty_step, up=False) != fixed_qty:
        raise HistoricalSimulationError("SLICE_QTY_OFF_GRID", "Fixed slice quantity mevcut quantity grid’inde değil.")

    _validate_dataset(dataset)
    started_at = monotonic()
    state = State()
    actions: list[HistoricalFixedSliceAction] = []
    state = _start_fixed_slice_order(
        state,
        config,
        dataset.bars[0],
        1,
        "BASE",
        config.base_qty,
        fixed_qty,
        actions,
    )
    state = apply(state, {"type": "MARK", "price": dataset.bars[0].close}, config)

    for index, bar in enumerate(dataset.bars[1:], start=2):
        _check_budget(started_at, timeout_seconds)
        if state.unsettled:
            order = state.unsettled[0]
            reachable = (
                _buy_reachable(bar, order.limit)
                if order.side == "BUY"
                else _sell_reachable(bar, order.limit)
            )
            if reachable:
                state = apply_fixed_slice_fill(state, config, bar, index, order.order_id, fixed_qty, actions)
            state = apply(state, {"type": "MARK", "price": bar.close}, config)
            continue

        safety = _next_safety(state, config)
        take_profit = target(state, config) if state.position.qty else None
        short = config.direction == "SHORT"
        safety_reachable = safety is not None and (
            _sell_reachable(bar, safety.price) if short else _buy_reachable(bar, safety.price)
        )
        take_profit_reachable = take_profit is not None and (
            _buy_reachable(bar, take_profit) if short else _sell_reachable(bar, take_profit)
        )
        if safety_reachable and take_profit_reachable:
            return fixed_slice_result(
                dataset,
                config,
                config_hash,
                state,
                actions,
                execution_status="INDETERMINATE",
                application_code="AMBIGUOUS_OHLC_PATH",
                processed_bar_count=index - 1,
                first_ambiguous_bar_index=index,
            )
        if safety_reachable and safety is not None:
            if short:
                raw_reference = bar.open if number(bar.open) >= safety.price else exact_text(safety.price)
            else:
                raw_reference = bar.open if number(bar.open) <= safety.price else exact_text(safety.price)
            state = _start_fixed_slice_order(
                state,
                config,
                bar,
                index,
                f"SAFETY:{_next_safety_index(state) + 1}",
                safety.qty,
                fixed_qty,
                actions,
                raw_reference=raw_reference,
            )
        elif take_profit_reachable and take_profit is not None:
            if short:
                raw_reference = bar.open if number(bar.open) <= take_profit else exact_text(take_profit)
            else:
                raw_reference = bar.open if number(bar.open) >= take_profit else exact_text(take_profit)
            state = _start_fixed_slice_order(
                state,
                config,
                bar,
                index,
                "EXIT",
                state.position.qty,
                fixed_qty,
                actions,
                raw_reference=raw_reference,
            )
        state = apply(state, {"type": "MARK", "price": bar.close}, config)

    _check_budget(started_at, timeout_seconds)
    return fixed_slice_result(
        dataset,
        config,
        config_hash,
        state,
        actions,
        execution_status="COMPLETED",
        application_code=None,
        processed_bar_count=len(dataset.bars),
        first_ambiguous_bar_index=None,
    )


def _start_fixed_slice_order(
    state: State,
    config: Config,
    bar: CanonicalBar,
    bar_index: int,
    role: str,
    quantity: Q,
    fixed_qty: Q,
    actions: list[HistoricalFixedSliceAction],
    *,
    raw_reference: str | None = None,
) -> State:
    buy = role not in ("EXIT", "STOP")
    raw_reference = raw_reference or bar.open
    raw_price = number(raw_reference)
    fill_price = align(
        raw_price * (1 + config.slippage if buy else 1 - config.slippage),
        config.tick,
        up=buy,
    )
    order_id = f"historical_partial:{bar_index}:order"
    state = apply(state, {"type": "MARK", "price": raw_reference}, config)
    state = apply(
        state,
        {
            "type": "INTENT",
            "order_id": order_id,
            "role": role,
            "qty": exact_text(quantity),
            "limit_price": exact_text(fill_price),
        },
        config,
    )
    return apply_fixed_slice_fill(
        state,
        config,
        bar,
        bar_index,
        order_id,
        fixed_qty,
        actions,
    )


def simulate_historical_ohlcv(
    dataset: HistoricalDatasetInput,
    config: Config,
    *,
    config_hash: str,
    timeout_seconds: float = MAX_HISTORICAL_SIMULATION_SECONDS,
    feature_binding: HistoricalFeatureRunBinding | None = None,
    max_bars: int = MAX_HISTORICAL_SIMULATION_BARS,
) -> HistoricalSimulationResult:
    """Run the first closed-bar model without network, persistence, or randomness."""

    if type(max_bars) is not int or not 1 <= max_bars <= MAX_SECTOR_BACKTEST_BARS:
        raise HistoricalSimulationError("BAR_SCOPE_EXCEEDED", "Bar kapsamı sınırı geçersiz.")
    if len(dataset.bars) > max_bars:
        raise HistoricalSimulationError("BAR_SCOPE_EXCEEDED", "Dataset bar kapsamı server sınırını aşıyor.")
    if not dataset.bars:
        raise HistoricalSimulationError("BAR_SCOPE_TOO_SMALL", "Dataset içinde simüle edilecek bar yok.")
    if timeout_seconds <= 0:
        raise HistoricalSimulationError("EXECUTION_BUDGET_EXCEEDED", "Simülasyon çalışma bütçesi geçersiz.")

    _validate_dataset(dataset)
    first_bar_index = _feature_start_index(dataset, config_hash, feature_binding)
    started_at = monotonic()
    cursor = DealCursor(state=State(), deal_sequence=0, prev_net=Q(0))
    actions: list[HistoricalSimulationAction] = []
    deal_pnls: list[str] = []
    equity_points: list[str] = []

    for index, bar in enumerate(dataset.bars[first_bar_index:], start=first_bar_index + 1):
        _check_budget(started_at, timeout_seconds)
        step = step_closed_bar(cursor, config, bar, index, actions, on_ambiguous="HALT")
        if step.ambiguous:
            return _result(
                dataset,
                config,
                config_hash,
                cursor.state,
                actions,
                execution_status="INDETERMINATE",
                application_code="AMBIGUOUS_OHLC_PATH",
                processed_bar_count=index - 1,
                first_ambiguous_bar_index=index,
                feature_binding=feature_binding,
                deal_pnls=deal_pnls,
                equity_points=equity_points,
            )
        cursor = step.cursor
        if step.closed_deal_pnl is not None:
            deal_pnls.append(step.closed_deal_pnl)
        equity_points.append(exact_text(cursor.state.equity(config)))

    _check_budget(started_at, timeout_seconds)
    return _result(
        dataset,
        config,
        config_hash,
        cursor.state,
        actions,
        execution_status="COMPLETED",
        application_code=None,
        processed_bar_count=len(dataset.bars),
        first_ambiguous_bar_index=None,
        feature_binding=feature_binding,
        deal_pnls=deal_pnls,
        equity_points=equity_points,
    )


def _apply_action(
    state: State,
    config: Config,
    bar: CanonicalBar,
    bar_index: int,
    role: str,
    quantity: Q,
    raw_reference: str,
    actions: list[HistoricalSimulationAction],
    deal_sequence: int,
    id_suffix: str = "",
) -> State:
    opening = role not in ("EXIT", "STOP") and not role.startswith("EXIT:")
    buy = opening if config.direction == "LONG" else not opening
    try:
        raw_price = number(raw_reference)
        fill_price = align(
            raw_price * (1 + config.slippage if buy else 1 - config.slippage),
            config.tick,
            up=buy,
        )
        if role == "BASE":
            # Faz W: under QUOTE base sizing the quantity depends on the
            # order's own fill price; identical to config.base_qty otherwise.
            quantity = config.base_order_qty(fill_price)
        fill_text = exact_text(fill_price)
        state = apply(state, {"type": "MARK", "price": raw_reference}, config)
        # A bar-close exit can follow an intrabar fill on the same bar, so it
        # carries a suffix; every other id keeps its historical form.
        order_id = f"historical:{bar_index}{id_suffix}:order"
        state = apply(
            state,
            {
                "type": "INTENT",
                "order_id": order_id,
                "role": role,
                "qty": exact_text(quantity),
                "limit_price": fill_text,
            },
            config,
        )
        fee = round_quantum(quantity * fill_price * config.fee_rate, config.fee_quantum)
        state = apply(
            state,
            {
                "type": "FILL",
                "execution_id": f"historical:{bar_index}{id_suffix}:fill",
                "order_id": order_id,
                "side": "BUY" if buy else "SELL",
                "qty": exact_text(quantity),
                "price": fill_text,
                "fee": exact_text(fee),
                "fee_asset": config.quote_asset,
            },
            config,
        )
        state = apply(
            state,
            {
                "type": "ORDER_FINAL",
                "order_id": order_id,
                "status": "FILLED",
                "filled_qty": exact_text(quantity),
                "coverage_complete": True,
            },
            config,
        )
    except (ValueError, ZeroDivisionError) as exc:
        raise HistoricalSimulationError(
            "REDUCER_POLICY_REJECTED",
            "Historical reducer mevcut politika sınırları içinde çalışamadı.",
        ) from exc
    actions.append(
        HistoricalSimulationAction(
            bar_index=bar_index,
            open_time_us=bar.open_time_us,
            role=role,
            raw_reference=raw_reference,
            fill_price=fill_text,
            quantity=exact_text(quantity),
            fee=exact_text(fee),
            deal_sequence=deal_sequence,
        )
    )
    return state


def _start_new_deal(state: State) -> State:
    """Open a fresh deal-scoped State after a prior deal closed flat.

    Carries forward cumulative economics (realized, fees, funding, peak,
    max_dd, halted) and the already-flat position; resets deal-scoped
    tracking (orders, anchor, safety_stopped, blockers) so the core
    "one base order per deal" invariant in engine.apply() is satisfied by
    construction, without touching engine.py or core State semantics.
    """

    return State(
        position=state.position,
        realized=state.realized,
        fees=state.fees,
        funding=state.funding,
        entry_notional=Q(0),
        mark=state.mark,
        anchor=None,
        peak=state.peak,
        max_dd=state.max_dd,
        halted=state.halted,
        safety_stopped=False,
        orders={},
        blockers=[],
        last_rejection=state.last_rejection,
    )


def _average_entry_price(actions: list[HistoricalSimulationAction]) -> str | None:
    """Quantity-weighted average fill price across every BUY-side action in the run."""

    total_qty = Q(0)
    total_cost = Q(0)
    for action in actions:
        if action.role == "BASE" or action.role.startswith("SAFETY:"):
            qty = number(action.quantity)
            total_qty += qty
            total_cost += qty * number(action.fill_price)
    # A quantity-weighted average is generally non-terminating (e.g. 1/3);
    # it is a display metric, so it is rounded half-even like every other
    # ratio shown, instead of crashing exact_text on real market data.
    return text(total_cost / total_qty, AVERAGE_PRICE_PLACES) if total_qty else None


def _time_in_position_us(actions: list[HistoricalSimulationAction]) -> int:
    """Sum of entry-bar-open to exit-bar-open duration for every deal that has closed."""

    deal_start_us: dict[int, int] = {}
    total = 0
    for action in actions:
        if action.role == "BASE":
            deal_start_us[action.deal_sequence] = action.open_time_us
        elif action.role == "EXIT" and action.deal_sequence in deal_start_us:
            total += action.open_time_us - deal_start_us[action.deal_sequence]
    return total


@dataclass(frozen=True, slots=True)
class DealCursor:
    """Where a bot stands between closed bars: engine state, the current
    deal's sequence number, and the cumulative net at the last deal close."""

    state: State
    deal_sequence: int
    prev_net: Q
    # Faz G1-kalan/a: no new deal opens on a bar whose open_time_us
    # is below this exclusive bound. Set from each deal close and
    # seeded from the store by the paper runner.
    cooldown_until_us: int = 0


@dataclass(frozen=True, slots=True)
class BarStep:
    cursor: DealCursor
    closed_deal_pnl: str | None
    ambiguous: bool
    resolved_ambiguity: bool = False


def step_closed_bar(
    cursor: DealCursor,
    config: Config,
    bar: CanonicalBar,
    bar_index: int,
    actions: list[HistoricalSimulationAction],
    *,
    on_ambiguous: str,
    allow_new_deal: bool = True,
) -> BarStep:
    """Advance one closed bar under the closed-bar model -- the single rule
    shared by backtests and the paper bot runner.

    A flat, settled, unhalted cursor opens a new deal at the bar's open.
    Otherwise at most one safety order OR the take profit fills inside the
    bar; if both are reachable the intrabar order is unknown: "HALT" returns
    `ambiguous` untouched (backtests stop honestly), "SAFETY_FIRST" takes the
    conservative path (live paper keeps running). The bar's close then marks
    the position and feeds the stop-loss confirmation. A deal that ends on
    this bar reports its exact net (fees included) immediately.
    """

    if on_ambiguous not in ("HALT", "SAFETY_FIRST"):
        raise ValueError("on_ambiguous must be HALT or SAFETY_FIRST")
    state = cursor.state
    deal_sequence = cursor.deal_sequence
    resolved_ambiguity = False
    opens_deal = (
        not state.position.qty
        and not state.unsettled
        and not state.halted
        and not state.blockers
    )
    if opens_deal:
        blocked = not allow_new_deal or bar.open_time_us < cursor.cooldown_until_us
        if not blocked:
            entry_price = number(bar.open)
            blocked = (config.min_entry_price is not None and entry_price < config.min_entry_price) or (
                config.max_entry_price is not None and entry_price > config.max_entry_price
            )
        if blocked:
            return BarStep(
                DealCursor(
                    apply(state, {"type": "MARK", "price": bar.close}, config),
                    deal_sequence,
                    cursor.prev_net,
                    cursor.cooldown_until_us,
                ),
                None,
                False,
            )
        if state.orders:
            state = _start_new_deal(state)
        deal_sequence += 1
        state = _apply_action(state, config, bar, bar_index, "BASE", config.base_qty, bar.open, actions, deal_sequence)
    else:
        # A halted engine (drawdown guard) accepts no new risk, only an exit.
        safety = None if state.halted else _next_safety(state, config)
        # F09a: with trailing configured the fixed intrabar TP exit is OFF
        # (3Commas never exits at the fixed target once trailing is on);
        # the exit is a bar-close decision in _close_bar instead.
        take_profit = (
            target(state, config)
            if state.position.qty and config.trailing_take_profit_rate is None
            else None
        )
        short = config.direction == "SHORT"
        safety_reachable = safety is not None and (
            _sell_reachable(bar, safety.price) if short else _buy_reachable(bar, safety.price)
        )
        take_profit_reachable = take_profit is not None and (
            _buy_reachable(bar, take_profit) if short else _sell_reachable(bar, take_profit)
        )
        resolved_ambiguity = safety_reachable and take_profit_reachable
        if resolved_ambiguity and on_ambiguous == "HALT":
            return BarStep(cursor, None, True)
        if safety_reachable and safety is not None:
            if short:
                raw_reference = bar.open if number(bar.open) >= safety.price else exact_text(safety.price)
            else:
                raw_reference = bar.open if number(bar.open) <= safety.price else exact_text(safety.price)
            state = _apply_action(state, config, bar, bar_index, f"SAFETY:{_next_safety_index(state) + 1}", safety.qty, raw_reference, actions, deal_sequence)
        elif take_profit_reachable and take_profit is not None:
            if short:
                raw_reference = bar.open if number(bar.open) <= take_profit else exact_text(take_profit)
            else:
                raw_reference = bar.open if number(bar.open) >= take_profit else exact_text(take_profit)
            state = _apply_action(state, config, bar, bar_index, "EXIT", state.position.qty, raw_reference, actions, deal_sequence)
    state = _close_bar(state, config, bar, bar_index, actions, deal_sequence)
    prev_net = cursor.prev_net
    closed_pnl = None
    cooldown_until_us = cursor.cooldown_until_us
    was_in_deal = opens_deal or cursor.state.position.qty > 0
    if was_in_deal and not state.position.qty and not state.unsettled:
        current_net = state.realized - state.fees - state.funding
        closed_pnl = exact_text(current_net - prev_net)
        prev_net = current_net
        if config.cooldown_seconds:
            cooldown_until_us = bar.close_time_us + config.cooldown_seconds * 1_000_000
    return BarStep(DealCursor(state, deal_sequence, prev_net, cooldown_until_us), closed_pnl, False, resolved_ambiguity)


def _close_bar(
    state: State,
    config: Config,
    bar: CanonicalBar,
    bar_index: int,
    actions: list[HistoricalSimulationAction],
    deal_sequence: int,
) -> State:
    """Mark the bar's close and, when a stop loss is configured, feed the
    engine's bar-close confirmation; a confirmed stop exits the whole
    position at that close. Without this the simulator silently ignored
    `stop_loss_rate`."""

    state = apply(state, {"type": "MARK", "price": bar.close}, config)
    if state.halted and state.position.qty and not state.unsettled:
        # The engine's own rule when its drawdown guard trips: close out.
        state = _apply_action(state, config, bar, bar_index, "STOP", state.position.qty, bar.close, actions, deal_sequence, ":close")
        return apply(state, {"type": "MARK", "price": bar.close}, config)
    if not state.position.qty:
        return state
    if config.stop_loss_rate is not None or config.trailing_take_profit_rate is not None:
        state = apply(state, {"type": "BAR_CLOSE", "close": bar.close}, config)
    else:
        return state
    if (
        config.stop_loss_rate is not None
        and state.sl_breach_streak >= config.stop_loss_confirmation_bars
        and not state.unsettled
    ):
        state = _apply_action(state, config, bar, bar_index, "STOP", state.position.qty, bar.close, actions, deal_sequence, ":close")
        state = apply(state, {"type": "MARK", "price": bar.close}, config)
        return state
    # F09a: trailing take-profit exit at the close. Division-free trigger
    # (water*(1-trail) / water*(1+trail), Fraction-exact): LONG exits
    # below the trigger, SHORT above it. Unarmed water (None) holds.
    trail = config.trailing_take_profit_rate
    if trail is not None and state.position.qty and not state.unsettled:
        water = state.trail_water
        close = number(bar.close)
        short = config.direction == "SHORT"
        triggered = water is not None and (
            close > water * (1 + trail) if short else close < water * (1 - trail)
        )
        if triggered:
            state = _apply_action(state, config, bar, bar_index, "EXIT", state.position.qty, bar.close, actions, deal_sequence, ":close")
            state = apply(state, {"type": "MARK", "price": bar.close}, config)
    return state


def _next_safety(state: State, config: Config):
    if not state.position.qty or state.anchor is None or state.safety_stopped or state.blockers:
        return None
    plan = config.plan(state.anchor)
    index = _next_safety_index(state)
    return plan[index] if index < len(plan) else None


def _next_safety_index(state: State) -> int:
    return sum(
        order.role.startswith("SAFETY:") and order.complete and order.filled == order.qty
        for order in state.orders.values()
    )


def _buy_reachable(bar: CanonicalBar, threshold: Q) -> bool:
    return number(bar.open) <= threshold or number(bar.low) <= threshold


def _sell_reachable(bar: CanonicalBar, threshold: Q) -> bool:
    return number(bar.open) >= threshold or number(bar.high) >= threshold


def _validate_dataset(dataset: HistoricalDatasetInput) -> None:
    expected_interval_us = EXPECTED_INTERVAL_US.get(dataset.metadata.interval)
    if expected_interval_us is None:
        raise HistoricalSimulationError(
            "INTERVAL_UNKNOWN",
            "Historical simulation için dataset interval sözleşmesi tanımlı değil.",
        )
    _validate_bar(dataset.bars[0], None)
    for previous, bar in zip(dataset.bars, dataset.bars[1:]):
        _validate_bar(bar, previous)
        if bar.open_time_us - previous.open_time_us != expected_interval_us:
            raise HistoricalSimulationError(
                "DATASET_NOT_CONTIGUOUS",
                "Historical dataset beklenen zaman grid'inde kesintiye sahip.",
            )


def _validate_bar(bar: CanonicalBar, previous: CanonicalBar | None) -> None:
    try:
        open_price = number(bar.open)
        high = number(bar.high)
        low = number(bar.low)
        close = number(bar.close)
        volume = number(bar.base_volume)
    except ValueError as exc:
        raise HistoricalSimulationError("BAR_DATA_INVALID", "Historical bar verisi geçersiz.") from exc
    if (
        bar.open_time_us >= bar.close_time_us
        or (previous is not None and bar.open_time_us <= previous.open_time_us)
        or open_price <= 0
        or high < open_price
        or high < close
        or low > open_price
        or low > close
        or high < low
        or volume < 0
        or not bar.is_closed
    ):
        raise HistoricalSimulationError("BAR_DATA_INVALID", "Historical bar verisi geçersiz.")


def _check_budget(started_at: float, timeout_seconds: float) -> None:
    if monotonic() - started_at > timeout_seconds:
        raise HistoricalSimulationError("EXECUTION_BUDGET_EXCEEDED", "Simülasyon çalışma bütçesini aştı.")


def _result(
    dataset: HistoricalDatasetInput,
    config: Config,
    config_hash: str,
    state: State,
    actions: list[HistoricalSimulationAction],
    *,
    execution_status: str,
    application_code: str | None,
    processed_bar_count: int,
    first_ambiguous_bar_index: int | None,
    feature_binding: HistoricalFeatureRunBinding | None = None,
    deal_pnls: list[str] = (),
    equity_points: list[str] = (),
) -> HistoricalSimulationResult:
    summary = report(state, config)
    position_status = "OPEN_AT_END" if state.position.qty else "CLOSED"
    summary.update(
        {
            "dataset_id": dataset.metadata.dataset_id,
            "artifact_sha256": dataset.metadata.artifact_sha256,
            "config_hash": config_hash,
            "processed_bar_count": processed_bar_count,
            "position_status": position_status,
            "funding_status": "NOT_MODELED",
            "mark_status": "NOT_AVAILABLE",
            "action_count": len(actions),
            "average_entry_price": _average_entry_price(actions),
            "time_in_position_us": _time_in_position_us(actions),
            "deal_pnls": list(deal_pnls),
            "equity_curve": list(equity_points),
        }
    )
    return HistoricalSimulationResult(
        execution_status=execution_status,
        application_code=application_code,
        processed_bar_count=processed_bar_count,
        first_ambiguous_bar_index=first_ambiguous_bar_index,
        position_status=position_status,
        fee_amount=summary["fees"],
        funding_status="NOT_MODELED",
        mark_status="NOT_AVAILABLE",
        actions=tuple(actions),
        summary=summary,
        feature_binding=feature_binding,
    )


def _feature_start_index(
    dataset: HistoricalDatasetInput,
    config_hash: str,
    feature_binding: HistoricalFeatureRunBinding | None,
) -> int:
    if feature_binding is None:
        return 0
    try:
        validate_historical_feature_binding(dataset, feature_binding, config_hash=config_hash)
    except HistoricalFeatureError as exc:
        raise HistoricalSimulationError(exc.code, str(exc)) from exc
    return feature_binding.first_eligible_bar_index - 1
