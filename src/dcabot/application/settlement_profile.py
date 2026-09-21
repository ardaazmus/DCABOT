"""Single settlement-asset authority (F35).

Only USDT is supported: every other asset needs timed rates, inventory
impact, and an INCOMPLETE-net policy that does not exist yet. New
settlement paths must call require_settlement_asset instead of
re-implementing the lock.
"""
from typing import Final


SUPPORTED_SETTLEMENT_ASSETS: Final = ("USDT",)


class SettlementProfileError(ValueError):
    """Raised when a settlement asset is outside the supported set."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def require_settlement_asset(asset: object) -> str:
    """Return the asset when supported; fail closed otherwise."""
    if asset in SUPPORTED_SETTLEMENT_ASSETS:
        assert isinstance(asset, str)
        return asset
    raise SettlementProfileError(
        "SETTLEMENT_ASSET_UNSUPPORTED",
        "Yalnız USDT settlement desteklenir; başka varlık zamanlı kur ve "
        "envanter modeli ister (F35 DEFERRED).",
    )
