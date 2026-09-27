"""Pure event reducer. Order intentions and executions are separate facts."""

from dataclasses import dataclass, field
from copy import deepcopy
from fractions import Fraction as Q
import re
from .config import Config
from .math import (
    Direction,
    Position,
    directional_stop_loss,
    directional_take_profit,
    drawdown,
    is_safety_triggered,
    is_take_profit_triggered,
    net_take_profit,
    signed_pnl,
)
from .numbers import number, positive, align, bounded, text, ratio


@dataclass
class Order:
    order_id: str
    role: str
    side: str
    qty: Q
    limit: Q
    intent_id: str | None = None
    filled: Q = Q(0)
    notional: Q = Q(0)
    status: str = "OPEN"
    complete: bool = False
    order_type: str = "LIMIT"
    # Faz 17 G.2 (RG-07): the planning-layer reference price captured at
    # INTENT time -- `limit` itself for LIMIT (structurally protected: a
    # fill can never cross it), `mark` at intent time for MARKET (the only
    # supported `slippage_reference` today). `realized_slippage` is a
    # post-fact, fill-only accounting output -- never an input to planning.
    reference_price: Q | None = None
    realized_slippage: Q | None = None

    @property
    def leaves(self) -> Q:
        """Return the quantity still executable under the current order state."""

        return Q(0) if self.complete and self.status == "CANCELED" else self.qty - self.filled

    @property
    def canceled(self) -> Q:
        """Return the terminal remainder closed by an explicit cancellation."""

        return self.qty - self.filled if self.complete and self.status == "CANCELED" else Q(0)


@dataclass
class State:
    position: Position = field(default_factory=Position)
    realized: Q = Q(0)
    fees: Q = Q(0)
    funding: Q = Q(0)
    entry_notional: Q = Q(0)
    mark: Q | None = None
    anchor: Q | None = None
    peak: Q = Q(0)
    max_dd: Q = Q(0)
    halted: bool = False
    safety_stopped: bool = False
    ladder_start_qty: Q | None = None
    # Faz 17 H.2 (RG-11): all time is explicit DATA carried on a "CLOCK"
    # event, never read from a wall clock inside the reducer -- a caller's
    # ReplayClock (derived from bar timestamps) and LiveClock (real time)
    # are indistinguishable to this module by design, which is what makes
    # replay deterministic.
    now_us: int | None = None
    deal_started_at_us: int | None = None
    deal_duration_expired: bool = False
    sl_breach_streak: int = 0
    # F09a: trailing take-profit water -- None until the TP target is
    # first reached on a close (activation), then the best close since
    # (highest LONG, lowest SHORT). The exit itself is a bar-close
    # decision in historical_simulation, next to the stop-loss
    # confirmation; decision() is untouched (testnet/service path).
    trail_water: Q | None = None
    # Faz 17 I.1 (RG-12): set once the cost-recovery-only EXIT (base-asset
    # profit mode) is FILLED/finalized; `retained_profit_base` accumulates
    # the base quantity later withdrawn (unsold, held) as profit via the
    # explicit WITHDRAW_PROFIT event.
    profit_cost_recovered: bool = False
    retained_profit_base: Q = Q(0)
    orders: dict[str, Order] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    last_rejection: str | None = None

    def equity(self, config: Config) -> Q:
        u = self.position.unrealized(self.mark) if self.mark is not None else Q(0)
        return bounded(
            config.initial_equity + self.realized - self.fees - self.funding + u
        )

    @property
    def unsettled(self):
        return [o for o in self.orders.values() if not o.complete]


def identifier(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch("[A-Za-z0-9_.:-]{1,100}", value):
        raise ValueError("Invalid local identifier")
    return value


def _fields(event: dict, fields: set[str]):
    if set(event) != fields | {"type"}:
        raise ValueError("Unexpected or missing event field")


def observe_risk(s: State, c: Config):
    equity = s.equity(c)
    s.peak = max(s.peak, c.initial_equity, equity)
    dd = drawdown(s.peak, equity)
    if dd is not None:
        s.max_dd = max(s.max_dd, dd)
    if equity <= c.minimum_equity or dd is None or dd >= c.max_drawdown:
        s.halted = True


def _cost_recovery_qty(s: State, c: Config, price: Q) -> Q:
    """Faz 17 I.1 (RG-12): the smallest on-grid quantity whose proceeds at
    `price` are >= the position's cost basis -- rounded UP (research's
    documented rounding-direction rule: rounding DOWN here would recover
    less than cost, silently financing "base profit" out of principal).
    Capped at the actual remaining quantity for the degenerate case where
    grid rounding would otherwise ask for more than exists."""

    raw_qty = s.position.cost / price
    return min(align(raw_qty, c.qty_step, up=True), s.position.qty)


def apply(state: State, event: dict, c: Config) -> State:
    if not isinstance(event, dict) or not isinstance(event.get("type"), str):
        raise ValueError("Expected typed event object")
    s = deepcopy(state)
    kind = event["type"]
    if kind == "MARK":
        _fields(event, {"price"})
        s.mark = positive(event["price"])
    elif kind == "CLOCK":
        # Faz 17 H.2 (RG-11): deal start is the first ECONOMIC EXPOSURE
        # (position.qty going 0 -> nonzero), not order-submission time --
        # consistent with the fill-based accounting principle (konu #7).
        # The caller must emit a CLOCK event promptly after any FILL that
        # could open the position for this to be captured accurately.
        _fields(event, {"now_us"})
        now_us = event["now_us"]
        if type(now_us) is not int or now_us < 0:
            raise ValueError("now_us must be a non-negative integer microsecond timestamp")
        if s.now_us is not None and now_us < s.now_us:
            raise ValueError("Clock cannot move backward")
        s.now_us = now_us
        if s.position.qty and s.deal_started_at_us is None:
            s.deal_started_at_us = now_us
        if (
            c.max_deal_duration_seconds is not None
            and s.deal_started_at_us is not None
            and not s.deal_duration_expired
            and now_us - s.deal_started_at_us >= c.max_deal_duration_seconds * 1_000_000
        ):
            s.deal_duration_expired = True
            if c.max_deal_duration_action in ("FORCE_CLOSE", "STOP_NEW_SAFETY_ORDERS"):
                s.blockers.append("MAX_DEAL_DURATION_EXPIRED")
    elif kind == "BAR_CLOSE":
        # Faz 17 H.2 (RG-11): stop-loss confirmation is bar-count based ONLY
        # (never seconds) -- a seconds-based dwell cannot be honestly
        # simulated against OHLC bar data (konu 11/12's data-resolution
        # warning), so this is the ONLY confirmation primitive offered.
        _fields(event, {"close"})
        close = positive(event["close"])
        if c.stop_loss_rate is not None and s.position.qty:
            trigger = directional_stop_loss(c.direction_enum, s.position.average, c.stop_loss_rate)
            breached = close <= trigger if c.direction_enum is Direction.LONG else close >= trigger
            s.sl_breach_streak = s.sl_breach_streak + 1 if breached else 0
        else:
            s.sl_breach_streak = 0
        # F09a: trailing ratchet on closes only, never intrabar wicks
        # (the same honesty rule as the bar-count stop-loss). A moving
        # average (safety fills) never resets an armed ratchet; a flat
        # book clears it, and every new deal starts from a fresh State.
        if c.trailing_take_profit_rate is not None and s.position.qty:
            tp_target = target(s, c)
            if tp_target is None:
                s.trail_water = None
            elif c.direction_enum is Direction.LONG:
                if s.trail_water is None:
                    if close >= tp_target:
                        s.trail_water = close
                elif close > s.trail_water:
                    s.trail_water = close
            elif s.trail_water is None:
                if close <= tp_target:
                    s.trail_water = close
            elif close < s.trail_water:
                s.trail_water = close
        else:
            s.trail_water = None
    elif kind == "WITHDRAW_PROFIT":
        # Faz 17 I.1 (RG-12): base-asset profit retention is a NON-CASH
        # write-down, never a fabricated sale -- the cost-recovery portion
        # was already sold for real quote proceeds via a normal EXIT/FILL;
        # this event only removes the remaining, deliberately-unsold base
        # quantity from the tracked position. Requires the ENTIRE remainder
        # in one call (no partial withdrawal) to keep the model simple.
        _fields(event, {"qty"})
        qty = positive(event["qty"])
        if c.effective_profit_asset != c.base_asset:
            raise ValueError("WITHDRAW_PROFIT is only valid when profit_asset is base_asset")
        if not s.profit_cost_recovered:
            raise ValueError("WITHDRAW_PROFIT requires the cost-recovery EXIT to be finalized first")
        if s.unsettled:
            raise ValueError("WITHDRAW_PROFIT requires no unsettled orders")
        if qty != s.position.qty:
            raise ValueError("WITHDRAW_PROFIT must withdraw the entire remaining position at once")
        s.retained_profit_base = bounded(s.retained_profit_base + qty)
        s.position = Position()
    elif kind == "INTENT":
        fields = {"order_id", "role", "qty", "limit_price"}
        event_fields = set(event)
        if event_fields != fields | {"type"} and event_fields != fields | {"type", "intent_id"}:
            raise ValueError("Unexpected or missing event field")
        oid = identifier(event["order_id"])
        intent_id = event.get("intent_id")
        if intent_id is not None:
            intent_id = identifier(intent_id)
        role = event["role"]
        qty = positive(event["qty"])
        price = positive(event["limit_price"])
        if oid in s.orders or s.mark is None:
            raise ValueError("Order already exists or mark missing")
        if c.max_deal_duration_action == "FREEZE" and s.deal_duration_expired:
            # Mirrors decision()'s unconditional freeze -- a caller must not
            # be able to bypass it by submitting an INTENT directly.
            raise ValueError("New intents are blocked: max_deal_duration FREEZE is active")
        is_safety_role = isinstance(role, str) and re.fullmatch(r"SAFETY:[1-9][0-9]*", role)
        is_manual_role = isinstance(role, str) and re.fullmatch(r"MANUAL:[1-9][0-9]*", role)
        is_ladder_exit_role = isinstance(role, str) and re.fullmatch(r"EXIT:[1-9][0-9]*", role)
        # Faz 17 G.3: up to `effective_max_active_safety_orders` safety
        # orders may be open (unsettled) at once -- a real, sector-validated
        # feature (3Commas/Bitsgap), not a qwen-only idea. BASE/EXIT/STOP
        # keep the original strict single-open-order-at-a-time gate; only a
        # SAFETY intent may be accepted while other *safety* orders are
        # still open.
        if s.unsettled and not (
            is_safety_role and all(o.role.startswith("SAFETY:") for o in s.unsettled)
        ):
            raise ValueError("Unresolved prior order blocks this intent")
        c.check_order(qty, price)
        # Faz 17 C.3: side flips with direction (SHORT opens by selling and
        # closes by buying back); LONG keeps the original BUY-open/SELL-close
        # mapping exactly.
        closing_side = "BUY" if c.direction == "SHORT" else "SELL"
        opening_side = "SELL" if c.direction == "SHORT" else "BUY"
        if role in ("EXIT", "STOP") or is_ladder_exit_role:
            # Faz 17 H.1 (RG-10): a ladder, once configured, is the ONLY
            # accepted exit path -- mixing plain "EXIT" with "EXIT:N" would
            # let a caller bypass the ladder's own remainder/weight rules.
            if role == "EXIT" and c.take_profit_ladder is not None:
                raise ValueError("Plain EXIT is not accepted while a take_profit_ladder is configured")
            if is_ladder_exit_role and c.take_profit_ladder is None:
                raise ValueError("EXIT:N is not accepted without a configured take_profit_ladder")
            if is_ladder_exit_role:
                ladder = c.take_profit_ladder
                created = {
                    int(o.role.split(":", 1)[1])
                    for o in s.orders.values()
                    if o.role.startswith("EXIT:")
                }
                next_index = len(created) + 1
                if next_index > len(ladder) or role != f"EXIT:{next_index}":
                    raise ValueError("Only the next take_profit_ladder level can be accepted")
                level = ladder[next_index - 1]
                start_qty = s.ladder_start_qty if s.ladder_start_qty is not None else s.position.qty
                expected_qty = (
                    s.position.qty
                    if next_index == len(ladder)
                    else align(level.weight * start_qty, c.qty_step, up=False)
                )
                if qty != expected_qty:
                    raise ValueError("take_profit_ladder level quantity does not match the expected amount")
                level_target = directional_take_profit(c.direction_enum, s.position.average, level.target_percent)
                if not is_take_profit_triggered(c.direction_enum, s.mark, level_target):
                    raise ValueError("take_profit_ladder level has not triggered yet")
            if role == "EXIT" and c.effective_profit_asset == c.base_asset:
                # Faz 17 I.1 (RG-12): only the cost-recovery portion is
                # actually SOLD -- the rest stays in base, withdrawn later
                # via WITHDRAW_PROFIT, never bundled into this sale.
                expected_qty = _cost_recovery_qty(s, c, price)
                if qty != expected_qty:
                    raise ValueError("EXIT quantity must equal the base-asset cost-recovery amount")
            if qty > s.position.qty:
                raise ValueError("Exit cannot reverse the position")
            side = closing_side
        else:
            if s.halted or s.blockers:
                raise ValueError("New risk is blocked")
            side = opening_side
            if role == "BASE":
                if s.orders or qty != c.base_order_qty(price):
                    raise ValueError(
                        "One base order per deal, with configured quantity"
                    )
                # Validate the proposed plan before exposing any synthetic position.
                c.plan(price)
            elif is_safety_role:
                # Next index is by creation order (any SAFETY order ever
                # opened, complete or not), not completion count -- under
                # concurrency a completed-count basis would collide with an
                # already-open-but-unsettled order at the same index.
                created = {
                    int(o.role.split(":", 1)[1])
                    for o in s.orders.values()
                    if o.role.startswith("SAFETY:")
                }
                next_index = len(created) + 1
                open_safety = sum(
                    1 for o in s.unsettled if o.role.startswith("SAFETY:")
                )
                if s.anchor is None or s.safety_stopped or not s.position.qty:
                    raise ValueError("Safety plan is not active")
                if open_safety >= c.effective_max_active_safety_orders:
                    raise ValueError("Active safety order window is full")
                plan = c.plan(s.anchor)
                if (
                    next_index > len(plan)
                    or role != f"SAFETY:{next_index}"
                    or qty != plan[next_index - 1].qty
                    or not is_safety_triggered(
                        c.direction_enum, s.mark, plan[next_index - 1].price
                    )
                ):
                    raise ValueError(
                        "Only the next triggered safety level can be accepted"
                    )
            elif is_manual_role:
                # Faz W-B4: explicit user top-up ("Add funds") into an open
                # deal. It averages like a safety fill but consumes no plan
                # index and needs no trigger -- the click is the trigger.
                # Halted/blocker, grid/minimum, entry-cap and margin gates
                # above still apply; plan exhaustion does not block it.
                created = {
                    int(o.role.split(":", 1)[1])
                    for o in s.orders.values()
                    if o.role.startswith("MANUAL:")
                }
                next_index = len(created) + 1
                if s.anchor is None or not s.position.qty:
                    raise ValueError("Manual orders require an open deal")
                if role != f"MANUAL:{next_index}":
                    raise ValueError("Only the next manual order index can be accepted")
            else:
                raise ValueError("Unknown order role")
            if s.entry_notional + qty * price > c.max_entry_notional:
                raise ValueError("Gross entry notional cap exceeded")
            # Deliberately a local IM estimate, not a venue/bracket collateral model.
            if (
                s.position.qty * s.mark + qty * price
            ) / c.leverage + qty * price * c.fee_rate > s.equity(c):
                raise ValueError(
                    "Insufficient equity for local initial-margin estimate"
                )
        order_type = c.order_type_for_role(role)
        reference_price = price if order_type == "LIMIT" else s.mark
        if order_type == "MARKET":
            # Faz 17 G.2 (RG-07): MARKET's true fill price is unknown before
            # submission -- the declared `limit_price` is reinterpreted as a
            # worst-case planning bound, and that bound must itself respect
            # the live policy cap (off `slippage_reference`=MARK, the only
            # reference the engine has). This is the single enforcement
            # point; the pre-existing per-order `o.limit` check at FILL time
            # (unchanged) then guarantees no execution can cross a bound that
            # is already policy-conformant by construction.
            bound_fraction = c.max_adverse_slippage_bps / Q(10000)
            worst_case = (
                s.mark * (1 + bound_fraction)
                if side == "BUY"
                else s.mark * (1 - bound_fraction)
            )
            if (side == "BUY" and price > worst_case) or (
                side == "SELL" and price < worst_case
            ):
                raise ValueError(
                    "MARKET order's worst-case bound exceeds max_adverse_slippage_bps"
                )
        if is_ladder_exit_role and s.ladder_start_qty is None:
            # Snapshot BEFORE any sell happens (INTENT time, position still
            # untouched) -- every later level's weight*start_qty is computed
            # against this single fixed reference, never the shrinking
            # remaining quantity (RG-10's documented bug class).
            s.ladder_start_qty = s.position.qty
        s.orders[oid] = Order(
            oid,
            role,
            side,
            qty,
            price,
            intent_id=intent_id,
            order_type=order_type,
            reference_price=reference_price,
        )
    elif kind == "FILL":
        _fields(
            event,
            {"execution_id", "order_id", "side", "qty", "price", "fee", "fee_asset"},
        )
        identifier(event["execution_id"])
        oid = identifier(event["order_id"])
        if oid not in s.orders:
            raise ValueError("Execution has no known local order")
        o = s.orders[oid]
        qty = positive(event["qty"])
        price = positive(event["price"])
        fee = number(event["fee"])
        if event["fee_asset"] != c.quote_asset or event["side"] != o.side:
            raise ValueError("Execution asset/side mismatch")
        if o.filled + qty > o.qty:
            raise ValueError(
                "Synthetic overfill: quarantine; live overfill recovery is not implemented"
            )
        if (
            align(qty, c.qty_step, up=False) != qty
            or align(price, c.tick, up=False) != price
        ):
            raise ValueError("Execution is off-grid")
        if (o.side == "BUY" and price > o.limit) or (
            o.side == "SELL" and price < o.limit
        ):
            raise ValueError("Execution violates its declared limit")
        # Faz 17 G.2 (RG-07): `realized_slippage` is a pure post-fact
        # accounting output -- never an input to any decision. Positive =
        # adverse (paid more on a BUY / received less on a SELL) relative to
        # the reference price captured at INTENT time. For LIMIT orders this
        # is always <= 0 by construction (the check above already forbids a
        # fill crossing the limit == reference price).
        if o.reference_price is not None:
            o.realized_slippage = (
                (price - o.reference_price) / o.reference_price
                if o.side == "BUY"
                else (o.reference_price - price) / o.reference_price
            )
        if o.complete:
            # Keep the economics of a valid late fill, but invalidate earlier coverage.
            o.complete = False
            o.status = "UNKNOWN"
            s.blockers.append("LATE_FILL_AFTER_FINAL")
        # Faz 17 C.3: dispatch on role (open vs close), not literal side --
        # Position.buy()/sell() track magnitude/cost, agnostic to which venue
        # side opens or closes. `sell()`'s returned gain assumes a LONG
        # bought-low basis; for SHORT it is the negative of the true PnL, so
        # `signed_pnl` (already exact/tested since Faz 17.7) recomputes the
        # correctly-signed realized amount from the same entry/exit prices
        # instead. For LONG this is algebraically identical to `sell()`'s own
        # gain (regression-zero, pinned by test_engine_direction.py).
        if o.role in ("EXIT", "STOP") or o.role.startswith("EXIT:"):
            entry_price = s.position.average
            s.position, _ = s.position.sell(qty, price)
            s.realized += signed_pnl(c.direction_enum, qty, entry_price, price)
        else:
            s.position = s.position.buy(qty, price)
            s.entry_notional += qty * price
        s.fees += fee
        o.filled += qty
        o.notional += qty * price
        if o.role.startswith("SAFETY:") or o.role.startswith("MANUAL:"):
            # F09a: an averaging fill moves the TP target, so the trailing
            # ratchet re-arms from the new average -- 3Commas replaces the
            # TP order on every safety fill. A stale peak must never force
            # an exit calibrated to the old average (e.g. a loss exit after
            # a crash-fill). Exits never reset: average is unchanged by
            # closes, and a flat book clears the water at BAR_CLOSE.
            s.trail_water = None
        if o.filled < o.qty and o.status != "UNKNOWN":
            o.status = "PARTIALLY_FILLED"
        # Quantity reaching the requested total is not final coverage proof.
    elif kind == "ORDER_FINAL":
        _fields(event, {"order_id", "status", "filled_qty", "coverage_complete"})
        oid = identifier(event["order_id"])
        if (
            oid not in s.orders
            or event["status"] not in ("FILLED", "CANCELED")
            or type(event["coverage_complete"]) is not bool
        ):
            raise ValueError("Invalid final observation")
        o = s.orders[oid]
        observed = number(event["filled_qty"])
        if observed < 0 or observed > o.qty:
            raise ValueError("Invalid cumulative quantity")
        if observed != o.filled or not event["coverage_complete"]:
            o.status = "UNKNOWN"
            o.complete = False
        elif event["status"] == "FILLED" and o.filled != o.qty:
            raise ValueError("FILLED status cannot manufacture an execution")
        else:
            if o.complete and o.status != event["status"]:
                raise ValueError("Conflicting terminal observation")
            o.status = event["status"]
            o.complete = True
            if o.role == "BASE" and o.filled and s.anchor is None:
                s.anchor = o.notional / o.filled
                try:
                    c.plan(s.anchor)
                except ValueError:
                    s.blockers.append("FINAL_ANCHOR_PLAN_INVALID")
                    s.safety_stopped = True
            if o.role.startswith("SAFETY:") and o.filled < o.qty:
                s.safety_stopped = (
                    True  # Explicitly abort further safety, no silent skip/retry.
                )
            if (
                o.role == "EXIT"
                and c.effective_profit_asset == c.base_asset
                and o.filled == o.qty
            ):
                # Faz 17 I.1: cost-recovery sale finalized -- the remainder
                # (if any) can now be withdrawn via WITHDRAW_PROFIT.
                s.profit_cost_recovered = True
    elif kind == "UNKNOWN":
        _fields(event, {"order_id"})
        oid = identifier(event["order_id"])
        if oid not in s.orders:
            raise ValueError("Unknown local order")
        s.orders[oid].status = "UNKNOWN"
        s.orders[oid].complete = False
    elif kind == "POLICY_REJECTION":
        _fields(event, {"reason"})
        if not isinstance(event["reason"], str) or len(event["reason"]) > 200:
            raise ValueError("Invalid rejection reason")
        s.last_rejection = event["reason"]
    elif kind == "FUNDING":
        _fields(event, {"amount", "asset"})
        if event["asset"] != c.quote_asset:
            raise ValueError("Funding asset mismatch")
        s.funding += number(event["amount"])
    else:
        raise ValueError("Unsupported event type")
    for value in (s.realized, s.fees, s.funding, s.entry_notional, s.peak, s.max_dd):
        bounded(value)
    observe_risk(s, c)
    return s


def target(s: State, c: Config) -> Q | None:
    if c.take_profit is None:
        return None
    if not s.position.qty:
        return None
    if c.target_mode == "NET_QUOTE":
        # NET_QUOTE's cost-recovery formula is LONG-only (Faz 17 C.3 scope
        # note): SHORT+NET_QUOTE is rejected at Config.parse, so this branch
        # is unreachable for SHORT and its LONG behavior is unchanged.
        return net_take_profit(
            s.position,
            s.fees + s.funding + c.fee_quantum / 2,
            s.realized,
            c.target_quote,
            c.fee_rate,
            c.tick,
        )
    direction = c.direction_enum
    raw = directional_take_profit(direction, s.position.average, c.take_profit)
    return align(raw, c.tick, up=(direction is Direction.LONG))


def decision(s: State, c: Config) -> tuple[str, Q] | None:
    """Propose the next action for a single-deal State.

    The BASE branch fires only on a fresh State (no orders yet); after a
    deal completes the same State never reopens risk -- multi-deal
    orchestration must start a new State (CORE01 single-deal invariant).
    """

    if s.mark is None:
        return None
    unsettled = s.unsettled
    # Faz 17 G.3: while orders are open, only a further SAFETY proposal is
    # ever possible (never BASE/EXIT/STOP) -- and only if every currently
    # open order is itself a safety order (a non-safety unsettled order,
    # e.g. an in-flight EXIT, blocks everything, matching pre-G.3 behavior).
    if unsettled and any(not o.role.startswith("SAFETY:") for o in unsettled):
        return None
    if s.position.qty:
        if s.halted:
            if unsettled:
                return None
            return ("STOP", s.position.qty)
        # Faz 17 H.2 (RG-11): a CONFIRMED stop-loss (bar-count dwell) takes
        # priority over everything below it -- it is a deliberate risk exit,
        # not a mere policy freeze/timeout.
        if c.stop_loss_rate is not None and s.sl_breach_streak >= c.stop_loss_confirmation_bars:
            return None if unsettled else ("STOP", s.position.qty)
        # FREEZE stops ALL further automated proposals (including TP/ladder)
        # once the deal's max duration has expired -- the most conservative
        # of the four actions (konu 11/12: no single universal behavior
        # exists, so this engine picks the safest interpretation for it).
        if c.max_deal_duration_action == "FREEZE" and s.deal_duration_expired:
            return None
        if c.max_deal_duration_action == "FORCE_CLOSE" and s.deal_duration_expired:
            return None if unsettled else ("STOP", s.position.qty)
        if c.effective_profit_asset == c.base_asset and s.profit_cost_recovered:
            # Faz 17 I.1: the cost-recovery sale is done -- the only
            # remaining action for this deal is withdrawing the retained
            # base remainder (never another EXIT/TP proposal; average cost
            # is unchanged but there is nothing left to sell for quote).
            return None if unsettled else ("WITHDRAW_PROFIT", s.position.qty)
        if not unsettled:
            # Faz 17 H.1 (RG-10): a configured ladder is orthogonal to
            # safety orders -- it only replaces the single plain "EXIT"
            # proposal, so falling through here (ladder not yet triggered,
            # or already exhausted) must still let a SAFETY proposal below
            # fire normally. Levels execute strictly one at a time (like
            # pre-G.3 SAFETY); average cost is unaffected by a partial sell
            # (proven algebraically in the research), reused unchanged.
            if c.take_profit_ladder is not None:
                ladder = c.take_profit_ladder
                created = {
                    int(o.role.split(":", 1)[1])
                    for o in s.orders.values()
                    if o.role.startswith("EXIT:")
                }
                next_index = len(created) + 1
                if next_index <= len(ladder):
                    level = ladder[next_index - 1]
                    level_target = directional_take_profit(
                        c.direction_enum, s.position.average, level.target_percent
                    )
                    if is_take_profit_triggered(c.direction_enum, s.mark, level_target):
                        start_qty = s.ladder_start_qty if s.ladder_start_qty is not None else s.position.qty
                        qty = (
                            s.position.qty
                            if next_index == len(ladder)
                            else align(level.weight * start_qty, c.qty_step, up=False)
                        )
                        return (f"EXIT:{next_index}", qty)
            elif c.take_profit is not None and is_take_profit_triggered(c.direction_enum, s.mark, target(s, c)):
                exit_price = target(s, c)
                exit_qty = (
                    _cost_recovery_qty(s, c, exit_price)
                    if c.effective_profit_asset == c.base_asset
                    else s.position.qty
                )
                return ("EXIT", exit_qty)
        if s.blockers or s.safety_stopped or s.anchor is None:
            return None
        created = {
            int(o.role.split(":", 1)[1])
            for o in s.orders.values()
            if o.role.startswith("SAFETY:")
        }
        next_index = len(created) + 1
        if len(unsettled) >= c.effective_max_active_safety_orders:
            return None
        plan = c.plan(s.anchor)
        if next_index <= len(plan) and is_safety_triggered(
            c.direction_enum, s.mark, plan[next_index - 1].price
        ):
            return (f"SAFETY:{next_index}", plan[next_index - 1].qty)
    elif not s.orders and not s.halted and not s.blockers:
        return ("BASE", c.base_order_qty(s.mark))
    return None


def report(s: State, c: Config) -> dict:
    unsettled = [o.order_id for o in s.unsettled]
    exact = {
        "qty": s.position.qty,
        "cost": s.position.cost,
        "realized": s.realized,
        "fees": s.fees,
        "funding": s.funding,
        "equity": s.equity(c),
    }
    return {
        "stage": "OFFLINE_CORE",
        "mode": "offline",
        "trading_enabled": False,
        "symbol": c.symbol,
        "qty": text(s.position.qty),
        "cost": text(s.position.cost),
        "average": text(s.position.average),
        "realized_gross": text(s.realized),
        "fees": text(s.fees),
        "funding": text(s.funding),
        "realized_net_after_all_costs": text(s.realized - s.fees - s.funding),
        "unrealized": text(
            s.position.unrealized(s.mark) if s.mark is not None else Q(0)
        ),
        "equity": text(s.equity(c)),
        "peak_equity": text(s.peak),
        "max_drawdown": text(s.max_dd),
        "current_drawdown": text(drawdown(s.peak, s.equity(c))),
        "anchor": text(s.anchor),
        "take_profit_price": text(target(s, c)),
        "entry_notional": text(s.entry_notional),
        "halted": s.halted,
        "safety_stopped": s.safety_stopped,
        "deal_started_at_us": s.deal_started_at_us,
        "deal_duration_expired": s.deal_duration_expired,
        "sl_breach_streak": s.sl_breach_streak,
        "profit_cost_recovered": s.profit_cost_recovered,
        "retained_profit_base": text(s.retained_profit_base),
        "unsettled_orders": unsettled,
        "blockers": list(s.blockers),
        "last_policy_rejection": s.last_rejection,
        "global_new_risk_gate_open": not (
            s.halted or s.blockers or unsettled or (s.orders and not s.position.qty)
        ),
        "deal_complete": bool(s.orders and not s.position.qty and not unsettled),
        "exact_ratios": {k: ratio(v) for k, v in exact.items()},
        "model": "LINEAR_LONG_SINGLE_DEAL; no external cashflows; no venue liquidation engine",
    }
