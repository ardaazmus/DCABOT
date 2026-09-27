"""Faz 17 D.1: Anti-Liquidation Cascade's OWN low-frequency poll budget.

Deliberately separate from the Lab's shared, multi-feature rate budget
(§8.2): ALC polling is a small, fixed-purpose, main-engine concern (one
symbol's positionRisk/account-margin, on a bot card) with its own minimum
interval, not a pool other Lab features draw from. A denied poll never
resets the window -- a caller spamming `allow()` cannot shorten the
effective interval by retrying.
"""

from dataclasses import dataclass, field


class AlcRateBudgetError(ValueError):
    """Raised on an invalid budget configuration or a clock moving backwards."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(slots=True)
class AlcPollBudget:
    """Per (venue, symbol) minimum-interval gate; in-memory, single process."""

    min_interval_us: int
    _last_polled_at_us: dict[tuple[str, str], int] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if type(self.min_interval_us) is not int or self.min_interval_us <= 0:
            raise AlcRateBudgetError(
                "ALC_RATE_BUDGET_INTERVAL_INVALID", "min_interval_us pozitif integer olmalıdır."
            )

    def allow(self, venue: str, symbol: str, *, now_us: int) -> bool:
        """True and records `now_us` only if the interval has elapsed."""

        if not isinstance(venue, str) or not venue or not isinstance(symbol, str) or not symbol:
            raise AlcRateBudgetError(
                "ALC_RATE_BUDGET_KEY_INVALID", "venue/symbol boş olmayan metin olmalıdır."
            )
        key = (venue, symbol)
        last = self._last_polled_at_us.get(key)
        if last is not None and now_us < last:
            raise AlcRateBudgetError(
                "ALC_RATE_BUDGET_CLOCK_REGRESSED", "now_us önceki kayıttan geride olamaz."
            )
        if last is not None and now_us - last < self.min_interval_us:
            return False
        self._last_polled_at_us[key] = now_us
        return True
