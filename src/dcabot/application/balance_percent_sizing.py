"""Exact balance-percent budget projection with explicit source ownership."""

from dataclasses import dataclass
import re

from dcabot.domain.numbers import bounded, exact_text, positive


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
_ASSET = re.compile(r"[A-Z0-9]{2,12}\Z", re.ASCII)


class BalancePercentError(ValueError):
    """Raised when tagged balance-percent sizing input is invalid."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class BalancePercentBudget:
    """Exact budget projection from one explicitly tagged balance source."""

    balance_source: str
    asset: str
    eligible_balance: str
    percent: str
    budget: str


def build_balance_percent_budget(
    *, balance_source: str, asset: str, eligible_balance: str, percent: str
) -> BalancePercentBudget:
    """Calculate ``eligible_balance * percent`` without account-side effects.

    The caller must provide the already-authorized eligible balance source.
    This function never discovers wallet, available, reserved, or credit
    balances and never creates a reserve or an economic order.
    """

    if not isinstance(balance_source, str) or _IDENTIFIER.fullmatch(balance_source) is None:
        raise BalancePercentError(
            "BALANCE_SOURCE_INVALID", "Balance source açık bir kimlik olmalıdır."
        )
    if not isinstance(asset, str) or _ASSET.fullmatch(asset) is None:
        raise BalancePercentError(
            "BALANCE_ASSET_INVALID", "Balance asset büyük harfli açık bir kod olmalıdır."
        )
    try:
        eligible = positive(eligible_balance)
    except ValueError as error:
        raise BalancePercentError(
            "ELIGIBLE_BALANCE_INVALID",
            "Eligible balance pozitif decimal string olmalıdır.",
        ) from error
    try:
        share = positive(percent)
    except ValueError as error:
        raise BalancePercentError(
            "BALANCE_PERCENT_INVALID",
            "Balance percent pozitif decimal string olmalıdır.",
        ) from error
    if share > 1:
        raise BalancePercentError(
            "BALANCE_PERCENT_INVALID", "Balance percent 1’i aşamaz."
        )
    budget = bounded(eligible * share)
    try:
        return BalancePercentBudget(
            balance_source=balance_source,
            asset=asset,
            eligible_balance=exact_text(eligible),
            percent=exact_text(share),
            budget=exact_text(budget),
        )
    except ValueError as error:
        raise BalancePercentError(
            "BALANCE_BUDGET_UNREPRESENTABLE",
            "Balance budget exact decimal sözleşmesine sığmıyor.",
        ) from error
