"""Pure, long-only linear-contract math. No venue margin engine is implied."""

from dataclasses import dataclass
from enum import IntEnum
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
    direction: "Direction | None" = None,
    sizing: str = "BASE",
) -> tuple[Level, ...]:
    # Faz 17 C.2: direction defaults to LONG (below-anchor descending ladder,
    # byte-for-byte the pre-existing behavior) via directional_safety_price;
    # SHORT mirrors it above anchor with an ascending ladder. No new pricing
    # formula -- this reuses the already-tested Faz 17.7 directional math.
    # Faz W: sizing="QUOTE" reads `safety_qty` as the first safety order's
    # quote amount; each level's quantity is that amount (scaled by the volume
    # multiplier) divided by the level's own price, floored to the qty grid.
    if direction is None:
        direction = Direction.LONG
    if sizing not in ("BASE", "QUOTE"):
        raise ValueError("sizing must be BASE or QUOTE")
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
        price = directional_safety_price(direction, anchor, cumulative, tick)
        level_qty = qty / price if sizing == "QUOTE" else qty
        aligned_qty = align(level_qty, qty_step, up=False)
        moved_away_from_anchor = (
            price < previous if direction is Direction.LONG else price > previous
        )
        if not moved_away_from_anchor or aligned_qty <= 0:
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


class Direction(IntEnum):
    """Deal direction, kept as a signed multiplier so LONG/SHORT share one
    formula set instead of duplicated branches (Faz 17.7 — anonim araştırma
    raporları #1a-c, 2026-09-21, M/F/B doğrulandı: evidence/F17.7/SONUC.md).
    """

    LONG = 1
    SHORT = -1


def signed_pnl(direction: Direction, qty: Q, entry: Q, exit_price: Q) -> Q:
    """LONG: qty*(exit-entry). SHORT: qty*(entry-exit). Quantities stay positive;
    only the direction sign selects which side of the spread is profit."""
    if min(qty, entry, exit_price) <= 0:
        raise ValueError("Quantity, entry and exit price must be positive")
    return bounded(direction.value * qty * (exit_price - entry))


def directional_take_profit(direction: Direction, average: Q, tp_rate: Q) -> Q:
    """LONG: average*(1+tp_rate) (above entry). SHORT: average*(1-tp_rate) (below entry)."""
    if average <= 0 or not 0 < tp_rate < 1:
        raise ValueError("Average must be positive and 0 < tp_rate < 1")
    price = average * (1 + direction.value * tp_rate)
    if price <= 0:
        raise ValueError("Take-profit rate collapses price to non-positive")
    return bounded(price)


def directional_stop_loss(direction: Direction, average: Q, sl_rate: Q) -> Q:
    """LONG: average*(1-sl_rate) (below entry). SHORT: average*(1+sl_rate) (above entry)."""
    if average <= 0 or sl_rate <= 0:
        raise ValueError("Average must be positive and sl_rate must be positive")
    price = average * (1 - direction.value * sl_rate)
    if price <= 0:
        raise ValueError("Stop-loss rate collapses price to non-positive")
    return bounded(price)


def directional_safety_price(
    direction: Direction, anchor: Q, cumulative_deviation: Q, tick: Q
) -> Q:
    """LONG safety orders sit below anchor (fires as price falls); SHORT safety
    orders sit above anchor (fires as price rises). Both round away from the
    anchor (LONG floors, SHORT ceils) so alignment never makes a level easier
    to trigger than the exact, unaligned deviation implies."""
    if anchor <= 0 or cumulative_deviation <= 0 or tick <= 0:
        raise ValueError("Anchor, cumulative deviation and tick must be positive")
    raw = anchor * (1 - direction.value * cumulative_deviation)
    if raw <= 0:
        raise ValueError("Cumulative deviation collapses safety price to non-positive")
    price = align(raw, tick, up=(direction is Direction.SHORT))
    if price <= 0:
        raise ValueError("Aligned safety price is non-positive")
    return price


def is_safety_triggered(direction: Direction, current_price: Q, so_price: Q) -> bool:
    """LONG triggers on current<=so_price (adverse move is down); SHORT triggers
    on current>=so_price (adverse move is up). Using one shared `<=` for both
    directions is the "inverted comparator" bug documented by the research
    reports (all safety orders fire instantly on SHORT bots) — this function
    exists so callers cannot make that mistake."""
    if current_price <= 0 or so_price <= 0:
        raise ValueError("Prices must be positive")
    return current_price <= so_price if direction is Direction.LONG else current_price >= so_price


def is_take_profit_triggered(direction: Direction, current_price: Q, target_price: Q) -> bool:
    """Take-profit fires on a FAVORABLE move: LONG when current>=target (price
    rose to/through target); SHORT when current<=target (price fell to/through
    target) -- the mirror of is_safety_triggered's adverse-move convention.
    Faz 17 C.3 (engine.py direction-awareness)."""
    if current_price <= 0 or target_price <= 0:
        raise ValueError("Prices must be positive")
    return current_price >= target_price if direction is Direction.LONG else current_price <= target_price
