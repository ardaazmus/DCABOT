"""Pure event reducer. Order intentions and executions are separate facts."""

from dataclasses import dataclass, field
from copy import deepcopy
from fractions import Fraction as Q
import re
from .config import Config
from .math import Position, drawdown, net_take_profit
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


def apply(state: State, event: dict, c: Config) -> State:
    if not isinstance(event, dict) or not isinstance(event.get("type"), str):
        raise ValueError("Expected typed event object")
    s = deepcopy(state)
    kind = event["type"]
    if kind == "MARK":
        _fields(event, {"price"})
        s.mark = positive(event["price"])
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
        if oid in s.orders or s.mark is None or s.unsettled:
            raise ValueError(
                "Order already exists, mark missing, or unresolved prior order"
            )
        c.check_order(qty, price)
        if role in ("EXIT", "STOP"):
            if qty > s.position.qty:
                raise ValueError("Exit cannot reverse the position")
            side = "SELL"
        else:
            if s.halted or s.blockers:
                raise ValueError("New risk is blocked")
            side = "BUY"
            if role == "BASE":
                if s.orders or qty != c.base_qty:
                    raise ValueError(
                        "One base order per deal, with configured quantity"
                    )
                # Validate the proposed plan before exposing any synthetic position.
                c.plan(price)
            elif isinstance(role, str) and re.fullmatch(r"SAFETY:[1-9][0-9]*", role):
                done = sum(
                    o.role.startswith("SAFETY:") and o.complete and o.filled == o.qty
                    for o in s.orders.values()
                )
                if s.anchor is None or s.safety_stopped or not s.position.qty:
                    raise ValueError("Safety plan is not active")
                plan = c.plan(s.anchor)
                if (
                    done >= len(plan)
                    or role != f"SAFETY:{done + 1}"
                    or qty != plan[done].qty
                    or s.mark > plan[done].price
                ):
                    raise ValueError(
                        "Only the next triggered safety level can be accepted"
                    )
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
        s.orders[oid] = Order(oid, role, side, qty, price, intent_id=intent_id)
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
        if o.complete:
            # Keep the economics of a valid late fill, but invalidate earlier coverage.
            o.complete = False
            o.status = "UNKNOWN"
            s.blockers.append("LATE_FILL_AFTER_FINAL")
        if o.side == "BUY":
            s.position = s.position.buy(qty, price)
            s.entry_notional += qty * price
        else:
            s.position, g = s.position.sell(qty, price)
            s.realized += g
        s.fees += fee
        o.filled += qty
        o.notional += qty * price
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
    if not s.position.qty:
        return None
    if c.target_mode == "NET_QUOTE":
        return net_take_profit(
            s.position,
            s.fees + s.funding + c.fee_quantum / 2,
            s.realized,
            c.target_quote,
            c.fee_rate,
            c.tick,
        )
    return align(s.position.average * (1 + c.take_profit), c.tick, up=True)


def decision(s: State, c: Config) -> tuple[str, Q] | None:
    if s.mark is None or s.unsettled:
        return None
    if s.position.qty:
        if s.halted:
            return ("STOP", s.position.qty)
        if s.mark >= target(s, c):
            return ("EXIT", s.position.qty)
        if s.blockers or s.safety_stopped or s.anchor is None:
            return None
        done = sum(
            o.role.startswith("SAFETY:") and o.complete and o.filled == o.qty
            for o in s.orders.values()
        )
        plan = c.plan(s.anchor)
        if done < len(plan) and s.mark <= plan[done].price:
            return (f"SAFETY:{done + 1}", plan[done].qty)
    elif not s.orders and not s.halted and not s.blockers:
        return ("BASE", c.base_qty)
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
