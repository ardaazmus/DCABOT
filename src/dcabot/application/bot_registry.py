"""Multi-bot registry: identity, pair scope, blacklist/favorites, ownership (F05).

Pure in-memory authority. A bot owns sessions explicitly; a session has at
most one owner. Pair scope is checked before any binding — blacklist entries
must stay disjoint from pairs so no silent precedence exists.
"""
from dataclasses import dataclass, replace
import re
from typing import Final

from dcabot.domain.numbers import bounded, exact_text, number


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)
_SYMBOL = re.compile(r"[A-Z0-9]{3,20}\Z", re.ASCII)
_MAX_PAIRS: Final = 32


class BotRegistryError(ValueError):
    """Raised when bot identity, scope, or ownership is violated."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class BotProfile:
    """Immutable bot identity with explicit pair scope and virtual budget."""

    bot_id: str
    name: str
    pairs: tuple[str, ...]
    blacklist: tuple[str, ...] = ()
    favorites: tuple[str, ...] = ()
    virtual_quote_budget: str = "0"

    def __post_init__(self) -> None:
        _validate_identifier(self.bot_id, "BOT_ID_INVALID")
        if type(self.name) is not str or not 1 <= len(self.name) <= 100:
            raise BotRegistryError("BOT_NAME_INVALID", "Bot adı 1-100 karakter olmalıdır.")
        pairs = _validate_symbol_list(self.pairs, "BOT_PAIRS_INVALID", minimum=1)
        blacklist = _validate_symbol_list(self.blacklist, "BOT_BLACKLIST_INVALID", minimum=0)
        favorites = _validate_symbol_list(self.favorites, "BOT_FAVORITES_INVALID", minimum=0)
        overlap = set(pairs) & set(blacklist)
        if overlap:
            raise BotRegistryError(
                "BOT_BLACKLIST_CONFLICT",
                "Blacklist pair listesiyle kesişemez: " + ", ".join(sorted(overlap)),
            )
        outside = set(favorites) - set(pairs)
        if outside:
            raise BotRegistryError(
                "BOT_FAVORITES_INVALID",
                "Favoriler pair listesi içinde olmalıdır: " + ", ".join(sorted(outside)),
            )
        budget = _validate_budget(self.virtual_quote_budget)
        object.__setattr__(self, "pairs", pairs)
        object.__setattr__(self, "blacklist", blacklist)
        object.__setattr__(self, "favorites", favorites)
        object.__setattr__(self, "virtual_quote_budget", budget)


def new_bot_profile(
    *,
    bot_id: str,
    name: str,
    pairs: list[str] | tuple[str, ...],
    blacklist: list[str] | tuple[str, ...] = (),
    favorites: list[str] | tuple[str, ...] = (),
    virtual_quote_budget: str = "0",
) -> BotProfile:
    """Construct one validated bot profile without registering it."""
    return BotProfile(
        bot_id=bot_id,
        name=name,
        pairs=tuple(pairs),
        blacklist=tuple(blacklist),
        favorites=tuple(favorites),
        virtual_quote_budget=virtual_quote_budget,
    )


class BotRegistry:
    """Own bot profiles and session ownership; no trading authority."""

    def __init__(self) -> None:
        self._profiles: dict[str, BotProfile] = {}
        self._owners: dict[str, str] = {}
        self._sessions: dict[str, dict[str, str]] = {}

    def register(self, profile: BotProfile) -> str:
        """Store one profile; identical re-register is DUPLICATE."""
        if not isinstance(profile, BotProfile):
            raise BotRegistryError("BOT_PROFILE_INVALID", "Bot profili geçersiz.")
        prior = self._profiles.get(profile.bot_id)
        if prior is not None:
            if prior == profile:
                return "DUPLICATE"
            raise BotRegistryError(
                "BOT_ID_CONFLICT", "Aynı bot kimliği farklı profille kullanılamaz."
            )
        self._profiles[profile.bot_id] = profile
        self._sessions[profile.bot_id] = {}
        return "CREATED"

    def get(self, bot_id: str) -> BotProfile:
        """Return one stored profile or fail closed."""
        try:
            return self._profiles[bot_id]
        except (KeyError, TypeError) as error:
            raise BotRegistryError("BOT_UNKNOWN", "Bot kayıtlı değil.") from error

    def list_ids(self) -> tuple[str, ...]:
        """List registered bot ids in registration order."""
        return tuple(self._profiles)

    def update_lists(
        self,
        bot_id: str,
        *,
        blacklist: list[str] | tuple[str, ...],
        favorites: list[str] | tuple[str, ...],
    ) -> BotProfile:
        """Replace blacklist/favorites atomically; failure keeps the old profile."""
        current = self.get(bot_id)
        updated = replace(
            current, blacklist=tuple(blacklist), favorites=tuple(favorites)
        )
        BotProfile(
            bot_id=updated.bot_id,
            name=updated.name,
            pairs=updated.pairs,
            blacklist=updated.blacklist,
            favorites=updated.favorites,
            virtual_quote_budget=updated.virtual_quote_budget,
        )
        self._profiles[bot_id] = updated
        return updated

    def check_pair(self, bot_id: str, symbol: str) -> tuple[str, str]:
        """Return the pair verdict and a human reason; never trades."""
        profile = self.get(bot_id)
        if type(symbol) is not str or _SYMBOL.fullmatch(symbol) is None:
            raise BotRegistryError("BOT_SYMBOL_INVALID", "Sembol geçersiz.")
        if symbol in profile.blacklist:
            return "BLOCKED_BLACKLIST", f"{symbol} bu bot için blacklistte."
        if symbol not in profile.pairs:
            return "NOT_IN_SCOPE", f"{symbol} bu botun pair listesinde yok."
        return "ALLOWED", f"{symbol} bu bot için serbest."

    def bind_session(self, bot_id: str, session_id: str, symbol: str) -> str:
        """Bind one session to one bot after the pair check passes."""
        _validate_identifier(session_id, "BOT_SESSION_INVALID")
        verdict, reason = self.check_pair(bot_id, symbol)
        if verdict != "ALLOWED":
            raise BotRegistryError("BOT_PAIR_BLOCKED", reason)
        owner = self._owners.get(session_id)
        if owner is not None:
            if owner == bot_id and self._sessions[bot_id].get(session_id) == symbol:
                return "DUPLICATE"
            raise BotRegistryError(
                "BOT_SESSION_OWNED", "Session başka bir botun sahipliğinde."
            )
        self._owners[session_id] = bot_id
        self._sessions[bot_id][session_id] = symbol
        return "BOUND"

    def owner_of(self, session_id: str) -> str | None:
        """Return the owning bot id, or None when unbound."""
        return self._owners.get(session_id)

    def sessions_of(self, bot_id: str) -> dict[str, str]:
        """Return the session->symbol map owned by one bot."""
        self.get(bot_id)
        return dict(self._sessions[bot_id])


def _validate_identifier(value: object, code: str) -> None:
    if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
        raise BotRegistryError(code, "Kimlik değeri geçersiz.")


def _validate_symbol_list(
    values: object, code: str, *, minimum: int
) -> tuple[str, ...]:
    if not isinstance(values, tuple) or not all(
        type(item) is str and _SYMBOL.fullmatch(item) is not None for item in values
    ):
        raise BotRegistryError(code, "Sembol listesi geçersiz.")
    if not minimum <= len(values) <= _MAX_PAIRS or len(set(values)) != len(values):
        raise BotRegistryError(code, "Sembol listesi 1-32 benzersiz sembol olmalıdır.")
    return values


def _validate_budget(value: object) -> str:
    if not isinstance(value, str):
        raise BotRegistryError("BOT_BUDGET_INVALID", "Bütçe exact decimal metni olmalıdır.")
    try:
        amount = number(value)
    except ValueError as error:
        raise BotRegistryError(
            "BOT_BUDGET_INVALID", "Bütçe exact decimal metni olmalıdır."
        ) from error
    if amount < 0:
        raise BotRegistryError("BOT_BUDGET_INVALID", "Bütçe negatif olamaz.")
    try:
        return exact_text(bounded(amount))
    except ValueError as error:
        raise BotRegistryError(
            "BOT_BUDGET_INVALID", "Bütçe dış sözleşmede exact temsil edilemiyor."
        ) from error
