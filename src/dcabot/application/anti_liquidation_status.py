"""Faz 17 D.1: Anti-Liquidation Cascade -- fail-closed status derivation.

DCABOT never computes its own liquidation price (LCR-12, unchanged). This
module only (a) derives the margin ratio the venue does not hand back
ready-made (RG-02 correction: `/fapi/v3/positionRisk` has no `marginRatio`
field; the ratio is `totalMaintMargin / totalMarginBalance` from
`/fapi/v3/account`), (b) flags stale/inconsistent venue data instead of
displaying numbers that may no longer be true, and (c) flags a fast recent
price move (Arda's requirement, 2026-09-22: "hızlı çöküş/pump anlarında bu
veri daha az güvenilir olabilir") so the UI (D.2) can warn about reduced
confidence without inventing a new number.

State priority when a real futures venue is in play (highest first):
NO_POSITION > INCONSISTENT > STALE > WATCH > DATA_OK. INCONSISTENT outranks
STALE because a broken ratio is a harder failure than an old-but-valid one.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

from dcabot.data_adapters.binance_futures_testnet_position_risk import (
    FuturesAccountMargin,
    FuturesPositionRisk,
)
from dcabot.domain.numbers import number, text

LiquidationState = Literal[
    "NO_POSITION", "DATA_OK", "WATCH", "STALE", "INCONSISTENT", "SIMULATED_ONLY"
]

_MEANINGLESS_LIQUIDATION_PRICE = "0"


class AntiLiquidationStatusError(ValueError):
    """Raised when margin-ratio/fast-move inputs cannot be evaluated honestly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class LiquidationStatus:
    """One evaluated snapshot; UI-facing, no local liquidation estimate."""

    state: LiquidationState
    liquidation_price: str | None
    margin_ratio: str | None
    is_fast_move: bool
    reason: str | None
    observed_at_us: int


def derive_margin_ratio(total_maint_margin: str, total_margin_balance: str) -> str:
    """Exact `totalMaintMargin / totalMarginBalance` (RG-02: the venue does
    not report this ratio itself). A non-positive balance cannot honestly
    produce a ratio -- fail closed rather than divide or report nonsense."""

    try:
        maint = number(total_maint_margin)
        balance = number(total_margin_balance)
    except ValueError as exc:
        raise AntiLiquidationStatusError(
            "ALC_MARGIN_VALUE_INVALID", "Margin tutarları exact decimal olmalıdır."
        ) from exc
    if balance <= 0:
        raise AntiLiquidationStatusError(
            "ALC_MARGIN_BALANCE_NONPOSITIVE", "totalMarginBalance pozitif olmalıdır."
        )
    if maint < 0:
        raise AntiLiquidationStatusError(
            "ALC_MARGIN_MAINT_NEGATIVE", "totalMaintMargin negatif olamaz."
        )
    shown = text(Fraction(maint) / Fraction(balance), 12)
    assert shown is not None
    return shown


def is_fast_price_move(
    previous_price: str,
    previous_at_us: int,
    current_price: str,
    current_at_us: int,
    *,
    threshold_per_second: str,
) -> bool:
    """Exact |Δprice/Δt| in price-units-per-second vs. threshold. A
    non-positive elapsed time cannot prove the move was slow -- fail closed
    to True (flag it) rather than silently treat it as calm."""

    try:
        previous = number(previous_price)
        current = number(current_price)
        threshold = number(threshold_per_second)
    except ValueError as exc:
        raise AntiLiquidationStatusError(
            "ALC_FAST_MOVE_VALUE_INVALID", "Fiyat/eşik exact decimal olmalıdır."
        ) from exc
    if threshold < 0:
        raise AntiLiquidationStatusError(
            "ALC_FAST_MOVE_THRESHOLD_NEGATIVE", "Eşik negatif olamaz."
        )
    elapsed_us = current_at_us - previous_at_us
    if elapsed_us <= 0:
        return True
    delta = abs(current - previous)
    rate_per_second = Fraction(delta) * 1_000_000 / Fraction(elapsed_us)
    return rate_per_second >= threshold


def select_position_row(
    rows: tuple[FuturesPositionRisk, ...],
) -> FuturesPositionRisk | None:
    """Faz 17 D.1-followup: reduce one symbol's `positionRisk` rows to the
    single row `evaluate_liquidation_status` expects. Exact zero-filter
    (mirrors the same `position_amt` check `evaluate_liquidation_status`
    itself uses) so "0"/"0.000"/"-0" variants all count as no exposure.
    Two or more nonzero rows means hedge-mode (separate LONG+SHORT legs on
    one symbol) -- unsupported here, consistent with the closed C.5
    bidirectional-concurrency decision, so this fails closed rather than
    silently picking one leg."""

    nonzero = [row for row in rows if number(row.position_amt.removeprefix("-")) != 0]
    if not nonzero:
        return None
    if len(nonzero) > 1:
        raise AntiLiquidationStatusError(
            "ALC_MULTI_POSITION_UNSUPPORTED",
            "Hedge modunda birden fazla açık pozisyon bacağı desteklenmiyor.",
        )
    return nonzero[0]


def evaluate_liquidation_status(
    *,
    venue_supports_position_risk: bool,
    position_risk: FuturesPositionRisk | None,
    account_margin: FuturesAccountMargin | None,
    observed_at_us: int,
    now_us: int,
    stale_after_us: int,
    previous_mark_price: str | None = None,
    previous_observed_at_us: int | None = None,
    fast_move_threshold_per_second: str = "0",
) -> LiquidationStatus:
    """Combine one position-risk row + account margin totals into one
    honest, fail-closed status. Never estimates a liquidation price locally.
    """

    if not venue_supports_position_risk:
        return LiquidationStatus(
            state="SIMULATED_ONLY",
            liquidation_price=None,
            margin_ratio=None,
            is_fast_move=False,
            reason="VENUE_HAS_NO_POSITION_RISK_DATA",
            observed_at_us=observed_at_us,
        )
    if position_risk is None or number(position_risk.position_amt.removeprefix("-")) == 0:
        return LiquidationStatus(
            state="NO_POSITION",
            liquidation_price=None,
            margin_ratio=None,
            is_fast_move=False,
            reason=None,
            observed_at_us=observed_at_us,
        )

    liquidation_price: str | None = position_risk.liquidation_price
    reason: str | None = None
    if liquidation_price == _MEANINGLESS_LIQUIDATION_PRICE:
        liquidation_price = None
        reason = "LIQUIDATION_PRICE_NOT_MEANINGFUL"

    margin_ratio: str | None = None
    inconsistent = account_margin is None
    if account_margin is not None:
        try:
            margin_ratio = derive_margin_ratio(
                account_margin.total_maint_margin, account_margin.total_margin_balance
            )
        except AntiLiquidationStatusError:
            inconsistent = True

    if inconsistent:
        return LiquidationStatus(
            state="INCONSISTENT",
            liquidation_price=liquidation_price,
            margin_ratio=None,
            is_fast_move=False,
            reason=reason or "ACCOUNT_MARGIN_UNAVAILABLE",
            observed_at_us=observed_at_us,
        )

    if now_us - observed_at_us > stale_after_us:
        return LiquidationStatus(
            state="STALE",
            liquidation_price=liquidation_price,
            margin_ratio=margin_ratio,
            is_fast_move=False,
            reason=reason,
            observed_at_us=observed_at_us,
        )

    fast_move = False
    if previous_mark_price is not None and previous_observed_at_us is not None:
        fast_move = is_fast_price_move(
            previous_mark_price,
            previous_observed_at_us,
            position_risk.mark_price,
            observed_at_us,
            threshold_per_second=fast_move_threshold_per_second,
        )

    return LiquidationStatus(
        state="WATCH" if fast_move else "DATA_OK",
        liquidation_price=liquidation_price,
        margin_ratio=margin_ratio,
        is_fast_move=fast_move,
        reason=reason,
        observed_at_us=observed_at_us,
    )
