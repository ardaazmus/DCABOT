"""Exact shared-account reservation projection without persistence or mutation."""

from dataclasses import dataclass
import re

from dcabot.application.shared_account_identity import SharedAccountIdentity
from dcabot.domain.numbers import Q, bounded, exact_text, positive


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)


class AccountReservationError(ValueError):
    """Raised when an account reservation violates its scope or capacity."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _identifier(value: object, code: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise AccountReservationError(code, "Kimlik geçersiz.")
    return value


def _amount(value: object, code: str) -> str:
    try:
        return exact_text(positive(value))
    except ValueError as error:
        raise AccountReservationError(code, "Miktar pozitif exact decimal olmalıdır.") from error


@dataclass(frozen=True, slots=True)
class AccountCapacity:
    """One account-level positive capacity in one explicitly tagged asset."""

    account_id: str
    asset: str
    amount: str
    version: int

    def __post_init__(self) -> None:
        _identifier(self.account_id, "ACCOUNT_CAPACITY_IDENTITY_INVALID")
        _identifier(self.asset, "ACCOUNT_CAPACITY_ASSET_INVALID")
        canonical_amount = _amount(self.amount, "ACCOUNT_CAPACITY_AMOUNT_INVALID")
        if type(self.version) is not int or self.version < 0:
            raise AccountReservationError(
                "ACCOUNT_CAPACITY_VERSION_INVALID", "Account version negatif olmayan integer olmalıdır."
            )
        object.__setattr__(self, "amount", canonical_amount)


@dataclass(frozen=True, slots=True)
class AccountReservation:
    """One active account reservation attributed to an immutable owner scope."""

    reservation_id: str
    owner: SharedAccountIdentity
    asset: str
    amount: str

    def __post_init__(self) -> None:
        _identifier(self.reservation_id, "ACCOUNT_RESERVATION_ID_INVALID")
        if not isinstance(self.owner, SharedAccountIdentity):
            raise AccountReservationError(
                "ACCOUNT_RESERVATION_OWNER_INVALID", "Reservation owner identity geçersiz."
            )
        _identifier(self.asset, "ACCOUNT_RESERVATION_ASSET_INVALID")
        object.__setattr__(
            self, "amount", _amount(self.amount, "ACCOUNT_RESERVATION_AMOUNT_INVALID")
        )


@dataclass(frozen=True, slots=True)
class ReservationProjection:
    """Candidate reservation result; it is not an account commit."""

    account_id: str
    asset: str
    version_before: int
    version_after: int
    active_reserved: str
    requested: str
    available_after: str


def project_reservation(
    capacity: AccountCapacity,
    active_reservations: tuple[AccountReservation, ...],
    reservation_id: str,
    amount: str,
    expected_version: int,
) -> ReservationProjection:
    """Project one reservation under exact capacity and optimistic-version checks."""

    if not isinstance(capacity, AccountCapacity):
        raise AccountReservationError(
            "ACCOUNT_CAPACITY_INVALID", "Account capacity geçersiz."
        )
    if not isinstance(active_reservations, tuple) or any(
        not isinstance(item, AccountReservation) for item in active_reservations
    ):
        raise AccountReservationError(
            "ACCOUNT_RESERVATION_INPUT_INVALID", "Active reservations tuple olmalıdır."
        )
    if type(expected_version) is not int or expected_version < 0:
        raise AccountReservationError(
            "ACCOUNT_VERSION_CONFLICT", "Expected account version geçersiz."
        )
    if expected_version != capacity.version:
        raise AccountReservationError(
            "ACCOUNT_VERSION_CONFLICT", "Account version güncel değil; retry gerekir."
        )
    new_id = _identifier(reservation_id, "ACCOUNT_RESERVATION_ID_INVALID")
    requested = _amount(amount, "ACCOUNT_RESERVATION_AMOUNT_INVALID")
    if any(item.reservation_id == new_id for item in active_reservations):
        raise AccountReservationError(
            "ACCOUNT_RESERVATION_DUPLICATE", "Reservation kimliği zaten aktiftir."
        )
    if any(
        item.owner.account_id != capacity.account_id or item.asset != capacity.asset
        for item in active_reservations
    ):
        raise AccountReservationError(
            "ACCOUNT_RESERVATION_SCOPE_CONFLICT",
            "Reservation account veya asset kapsamı ile eşleşmiyor.",
        )
    active_total = bounded(sum((positive(item.amount) for item in active_reservations), Q(0)))
    available = bounded(positive(capacity.amount) - active_total)
    if available < 0 or positive(requested) > available:
        raise AccountReservationError(
            "ACCOUNT_CAPACITY_CONFLICT",
            "Yeni reservation account kapasitesini aşar.",
        )
    available_after = bounded(available - positive(requested))
    return ReservationProjection(
        account_id=capacity.account_id,
        asset=capacity.asset,
        version_before=capacity.version,
        version_after=capacity.version + 1,
        active_reserved=exact_text(active_total),
        requested=requested,
        available_after=exact_text(available_after),
    )
