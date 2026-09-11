"""Exact reinvestment projection from an explicitly eligible profit pool."""

from dataclasses import dataclass
import re

from dcabot.domain.numbers import bounded, exact_text, number


_ASSET = re.compile(r"[A-Z0-9]{2,12}\Z", re.ASCII)


class ReinvestmentBudgetError(ValueError):
    """Raised when reinvestment input is not an eligible exact projection."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class ReinvestmentBudget:
    """Exact budget projection sourced only from realized eligible profit."""

    asset: str
    pool_kind: str
    realized_profit_eligible: str
    percent: str
    budget: str


def build_reinvestment_budget(
    *, asset: str, realized_profit_eligible: str, percent: str
) -> ReinvestmentBudget:
    """Calculate a bounded reinvestment budget without changing any ledger."""

    if not isinstance(asset, str) or _ASSET.fullmatch(asset) is None:
        raise ReinvestmentBudgetError(
            "REINVESTMENT_ASSET_INVALID", "Reinvestment asset açık kod olmalıdır."
        )
    try:
        pool = number(realized_profit_eligible)
    except ValueError as error:
        raise ReinvestmentBudgetError(
            "REINVESTMENT_POOL_INVALID",
            "Realized eligible pool decimal string olmalıdır.",
        ) from error
    if pool < 0:
        raise ReinvestmentBudgetError(
            "REINVESTMENT_POOL_INVALID", "Eligible realized profit negatif olamaz."
        )
    try:
        share = number(percent)
    except ValueError as error:
        raise ReinvestmentBudgetError(
            "REINVESTMENT_PERCENT_INVALID",
            "Reinvestment percent decimal string olmalıdır.",
        ) from error
    if share < 0 or share > 1:
        raise ReinvestmentBudgetError(
            "REINVESTMENT_PERCENT_INVALID", "Reinvestment percent 0..1 aralığında olmalıdır."
        )
    budget = bounded(pool * share)
    try:
        return ReinvestmentBudget(
            asset=asset,
            pool_kind="REALIZED_PROFIT_ELIGIBLE",
            realized_profit_eligible=exact_text(pool),
            percent=exact_text(share),
            budget=exact_text(budget),
        )
    except ValueError as error:
        raise ReinvestmentBudgetError(
            "REINVESTMENT_BUDGET_UNREPRESENTABLE",
            "Reinvestment budget exact decimal sözleşmesine sığmıyor.",
        ) from error
