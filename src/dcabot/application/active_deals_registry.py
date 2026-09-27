"""Faz 17 I.2 (RG-12, konu 12/12): Max Active Deals -- LOCAL, in-memory
concurrency registry. Orthogonal to `domain/config.py`/`engine.py`: a single
deal's `Config`/`State` know nothing about how many OTHER deals exist
(CORE01 single-deal invariant) -- this module is the account/bot-level
orchestration primitive that decides whether a NEW deal may even start.

Sector research: 3Commas offers a bot-level `max_active_deals` plus a
same-pair sub-limit (`allowed_deals_on_same_pair`); an ACCOUNT-wide cap does
not exist even there, despite real user demand (a genuine gap this engine
closes, exceeding the combined 3Commas+Pionex+Bitsgap feature floor).
Real, support-documented failure mode this prevents: multiple bots
reserving the same funds simultaneously ("Insufficient Funds"). Over any
limit is REJECTED, never queued -- a delayed entry admitted after a stale
signal can be worse than no entry at all.
"""

from dataclasses import dataclass, field


class ActiveDealsError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass
class ActiveDealsRegistry:
    _all: set[str] = field(default_factory=set)
    _by_bot: dict[str, set[str]] = field(default_factory=dict)
    _by_symbol: dict[str, set[str]] = field(default_factory=dict)

    def count_account(self) -> int:
        return len(self._all)

    def count_for_bot(self, bot_id: str) -> int:
        return len(self._by_bot.get(bot_id, ()))

    def count_for_symbol(self, symbol: str) -> int:
        return len(self._by_symbol.get(symbol, ()))

    def try_open(
        self,
        *,
        deal_id: str,
        bot_id: str,
        symbol: str,
        max_active_deals_account: int | None,
        max_active_deals_per_bot: int | None,
        allowed_deals_on_same_pair: int | None,
    ) -> None:
        """Admit a new deal, or raise (reject, never queue). Each limit is
        `None` (unlimited) or a positive integer, checked independently --
        all three must pass."""

        for name, value in (
            ("max_active_deals_account", max_active_deals_account),
            ("max_active_deals_per_bot", max_active_deals_per_bot),
            ("allowed_deals_on_same_pair", allowed_deals_on_same_pair),
        ):
            if value is not None and (type(value) is not int or value < 1):
                raise ActiveDealsError("ACTIVE_DEALS_LIMIT_INVALID", f"{name} pozitif integer ya da null olmalıdır.")
        if deal_id in self._all:
            raise ActiveDealsError("ACTIVE_DEALS_DUPLICATE", f"{deal_id} zaten aktif.")
        if max_active_deals_account is not None and len(self._all) >= max_active_deals_account:
            raise ActiveDealsError(
                "ACTIVE_DEALS_ACCOUNT_LIMIT", "Hesap-geneli aktif deal sınırına ulaşıldı; reddedildi (kuyruğa alınmadı)."
            )
        if max_active_deals_per_bot is not None and self.count_for_bot(bot_id) >= max_active_deals_per_bot:
            raise ActiveDealsError(
                "ACTIVE_DEALS_BOT_LIMIT", f"{bot_id} için bot-seviyeli aktif deal sınırına ulaşıldı."
            )
        if allowed_deals_on_same_pair is not None and self.count_for_symbol(symbol) >= allowed_deals_on_same_pair:
            raise ActiveDealsError(
                "ACTIVE_DEALS_PAIR_LIMIT", f"{symbol} için aynı-parite deal sınırına ulaşıldı."
            )
        self._all.add(deal_id)
        self._by_bot.setdefault(bot_id, set()).add(deal_id)
        self._by_symbol.setdefault(symbol, set()).add(deal_id)

    def close(self, *, deal_id: str, bot_id: str, symbol: str) -> None:
        if deal_id not in self._all:
            raise ActiveDealsError("ACTIVE_DEALS_NOT_OPEN", f"{deal_id} aktif değil.")
        self._all.discard(deal_id)
        self._by_bot.get(bot_id, set()).discard(deal_id)
        self._by_symbol.get(symbol, set()).discard(deal_id)
