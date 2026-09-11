"""Pure, long-only linear-contract math. No venue margin engine is implied."""

from dataclasses import dataclass
from fractions import Fraction as Q
from .numbers import align, bounded


@dataclass(frozen=True)
class Position:
    qty: Q = Q(0)
    cost: Q = Q(0)

    def __post_init__(self):
        if self.qty < 0 or self.cost < 0 or (self.qty == 0) != (self.cost == 0):
            raise ValueError("Invalid long position")
        bounded(self.qty)
        bounded(self.cost)

    @property
    def average(self) -> Q | None:
        return self.cost / self.qty if self.qty else None

    def buy(self, qty: Q, price: Q) -> "Position":
        if qty <= 0 or price <= 0:
            raise ValueError("Execution must have positive quantity and price")
        return Position(self.qty + qty, self.cost + qty * price)

    def sell(self, qty: Q, price: Q) -> tuple["Position", Q]:
        if qty <= 0 or price <= 0 or qty > self.qty:
            raise ValueError("Invalid reduce-only execution")
        removed = self.cost * qty / self.qty
        return Position(self.qty - qty, self.cost - removed), bounded(
            qty * price - removed
        )

    def unrealized(self, mark: Q) -> Q:
        if mark <= 0:
            raise ValueError("Mark must be positive")
        return bounded(self.qty * mark - self.cost)


@dataclass(frozen=True)
class Level:
    index: int
    price: Q
    qty: Q


def build_plan(
    anchor: Q,
    safety_qty: Q,
    count: int,
    deviation: Q,
    step_multiplier: Q,
    volume_multiplier: Q,
    tick: Q,
    qty_step: Q,
) -> tuple[Level, ...]:
    if type(count) is not int or not 0 <= count <= 50:
        raise ValueError("Safety count must be an integer between 0 and 50")
    if (
        min(
            anchor,
            safety_qty,
            deviation,
            step_multiplier,
            volume_multiplier,
            tick,
            qty_step,
        )
        <= 0
    ):
        raise ValueError("Plan parameters must be positive")
    cumulative = Q(0)
    increment = deviation
    qty = safety_qty
    previous = anchor
    levels = []
    for i in range(1, count + 1):
        cumulative = bounded(cumulative + increment)
        price = align(anchor * (1 - cumulative), tick, up=False)
        aligned_qty = align(qty, qty_step, up=False)
        if price <= 0 or price >= previous or aligned_qty <= 0:
            raise ValueError(
                "Invalid or collapsed ladder level; no clamping is allowed"
            )
        levels.append(Level(i, price, aligned_qty))
        previous = price
        increment = bounded(increment * step_multiplier)
        qty = bounded(qty * volume_multiplier)
    return tuple(levels)


def net_take_profit(
    position: Position,
    total_costs: Q,
    realized: Q,
    target_quote: Q,
    exit_fee_rate: Q,
    tick: Q,
) -> Q:
    if position.qty <= 0 or not 0 <= exit_fee_rate < 1 or target_quote < 0:
        raise ValueError("Invalid net target inputs")
    root = (position.cost + total_costs + target_quote - realized) / (
        position.qty * (1 - exit_fee_rate)
    )
    # A target already earned still requires a positive executable price.
    return max(tick, align(root, tick, up=True))


def liquidation_long(
    qty: Q,
    average: Q,
    wallet: Q,
    maintenance_rate: Q,
    deduction: Q = Q(0),
    bracket_floor: Q = Q(0),
    bracket_cap: Q | None = None,
) -> Q | None:
    if (
        min(qty, average) <= 0
        or wallet < 0
        or deduction < 0
        or not 0 <= maintenance_rate < 1
    ):
        raise ValueError("Invalid teaching-model liquidation inputs")
    root = (qty * average - wallet - deduction) / (qty * (1 - maintenance_rate))
    if root <= 0:
        return None  # No positive root in this toy model, NOT a venue safety claim.
    if qty * root < bracket_floor or (
        bracket_cap is not None and qty * root >= bracket_cap
    ):
        raise ValueError("Root does not belong to this bracket")
    return bounded(root)


def drawdown(peak: Q, equity: Q) -> Q | None:
    return None if peak <= 0 or equity <= 0 else max(Q(0), (peak - equity) / peak)
