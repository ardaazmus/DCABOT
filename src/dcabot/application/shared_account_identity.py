"""Immutable scope identity for a future shared-account economic boundary."""

from dataclasses import dataclass
import re


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)


class SharedAccountIdentityError(ValueError):
    """Raised when a shared-account scope identity is not representable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class SharedAccountIdentity:
    """Explicit account, product and deal scope without economic behavior."""

    account_id: str
    product_id: str
    position_mode: str
    deal_id: str
    allocation_id: str | None


def new_shared_account_identity(
    account_id: str,
    product_id: str,
    position_mode: str,
    deal_id: str,
    allocation_id: str | None,
) -> SharedAccountIdentity:
    """Validate and construct one immutable shared-account scope identity."""

    for value in (account_id, product_id, position_mode, deal_id):
        if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
            raise SharedAccountIdentityError(
                "SHARED_ACCOUNT_IDENTITY_INVALID",
                "Account, product, position mode ve deal kimlikleri geçersiz.",
            )
    if allocation_id is not None and (
        not isinstance(allocation_id, str)
        or _IDENTIFIER.fullmatch(allocation_id) is None
    ):
        raise SharedAccountIdentityError(
            "SHARED_ACCOUNT_ALLOCATION_INVALID",
            "Allocation kimliği geçersiz.",
        )
    return SharedAccountIdentity(
        account_id=account_id,
        product_id=product_id,
        position_mode=position_mode,
        deal_id=deal_id,
        allocation_id=allocation_id,
    )
