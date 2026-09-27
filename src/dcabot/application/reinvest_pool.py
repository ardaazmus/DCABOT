"""Faz 17 H.1 (RG-10): reinvest profit pool -- deliberately OUTSIDE
`domain/config.py`/`engine.py`. Research finding (konu 10/12): the pool must
be fed ONLY at deal closure (after full fill/fee/funding reconciliation),
never from intermediate ladder realizations, so an open position's risk is
never stacked with an already-enlarged next deal's risk. `base_initial_equity`
(the bot/template's own static config) is immutable; `effective_initial_equity`
is a runtime-derived value a caller passes into the NEXT deal's
`Config.initial_equity` when materializing it -- `Config` itself is never
touched or reinterpreted by this module.

Only profit is ever reinvested: a realized loss leaves the pool unchanged,
never reduces it (reinvest is profit-sharing, not loss-amplification).
"""

from dataclasses import dataclass
from fractions import Fraction as Q

from dcabot.domain.numbers import bounded


class ReinvestPoolError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class ReinvestPool:
    base_initial_equity: Q
    accumulated: Q = Q(0)

    @property
    def effective_initial_equity(self) -> Q:
        return bounded(self.base_initial_equity + self.accumulated)


def create_pool(base_initial_equity: Q) -> ReinvestPool:
    if base_initial_equity <= 0:
        raise ReinvestPoolError("REINVEST_BASE_EQUITY_INVALID", "base_initial_equity pozitif olmalıdır.")
    return ReinvestPool(base_initial_equity=base_initial_equity)


def apply_deal_closed(pool: ReinvestPool, *, realized_profit: Q, reinvest_percent: Q) -> ReinvestPool:
    """Feed the pool from ONE deal's final, fully-reconciled net profit.
    `realized_profit` is the deal's net result (realized - fees - funding,
    i.e. `report()`'s `realized_net_after_all_costs`) -- a loss (<=0)
    contributes nothing and never shrinks the pool."""

    if not 0 <= reinvest_percent <= 1:
        raise ReinvestPoolError("REINVEST_PERCENT_INVALID", "reinvest_percent 0..1 aralığında olmalıdır.")
    if realized_profit <= 0:
        return pool
    contribution = bounded(realized_profit * reinvest_percent)
    return ReinvestPool(
        base_initial_equity=pool.base_initial_equity,
        accumulated=bounded(pool.accumulated + contribution),
    )
