"""Faz 17 G.1 (RG-06): per-symbol margin-mode ownership lock.

Binance's marginType is symbol-global venue state, not per-bot -- research
(konu 6/12) documented that on a shared account, "the last order-opening
bot's setting wins on the venue, even a failed order attempt can change it."
This registry is the LOCAL guard against two independent owners (bots/deals)
fighting over the same symbol's margin mode. In-memory only; no live venue
call (see `margin_mode_preflight.py` for that fake-seamed state machine).
"""

from dataclasses import dataclass, field

from .margin_mode_preflight import MARGIN_MODES


class MarginModeRegistryError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass
class MarginModeSymbolRegistry:
    _owners: dict[str, tuple[str, str]] = field(default_factory=dict)

    def acquire(self, symbol: str, owner_id: str, mode: str) -> None:
        if mode not in MARGIN_MODES:
            raise MarginModeRegistryError(
                "MARGIN_MODE_INVALID", "mode ISOLATED veya CROSS olmalıdır."
            )
        current = self._owners.get(symbol)
        if current is not None and current[0] != owner_id:
            raise MarginModeRegistryError(
                "MARGIN_MODE_SYMBOL_LOCKED",
                f"{symbol}, başka bir sahip ({current[0]}) tarafından {current[1]} modunda kilitli.",
            )
        if current is not None and current[1] != mode:
            raise MarginModeRegistryError(
                "MARGIN_MODE_OWNER_MODE_CONFLICT",
                f"{owner_id} zaten {symbol} için {current[1]} modunu tutuyor, {mode} istendi.",
            )
        self._owners[symbol] = (owner_id, mode)

    def release(self, symbol: str, owner_id: str) -> None:
        current = self._owners.get(symbol)
        if current is None or current[0] != owner_id:
            raise MarginModeRegistryError(
                "MARGIN_MODE_RELEASE_NOT_OWNER", f"{owner_id}, {symbol} kilidine sahip değil."
            )
        del self._owners[symbol]

    def owner_of(self, symbol: str) -> tuple[str, str] | None:
        return self._owners.get(symbol)
