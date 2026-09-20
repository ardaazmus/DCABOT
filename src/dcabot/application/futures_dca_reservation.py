"""Pure shared-account reservation binding for offline Futures DCA pending work."""

from dataclasses import dataclass

from dcabot.application.account_reservation import (
    AccountCapacity,
    AccountReservation,
    AccountReservationError,
    ReservationProjection,
    project_reservation,
)
from dcabot.application.futures_dca_fill_projection import FuturesDcaFillProjection
from dcabot.application.shared_account_identity import SharedAccountIdentity
from dcabot.domain.numbers import exact_text, number, positive


class FuturesDcaReservationError(ValueError):
    """Raised when a pending Futures DCA reservation cannot be bound safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FuturesDcaReservationBinding:
    """Pending reservation candidate plus the existing account projection."""

    fill_projection: FuturesDcaFillProjection
    reservation: AccountReservation
    projection: ReservationProjection


def project_futures_dca_reservation(
    *,
    fill_projection: FuturesDcaFillProjection,
    capacity: AccountCapacity,
    active_reservations: tuple[AccountReservation, ...],
    reservation_id: str,
    owner: SharedAccountIdentity,
    expected_version: int,
) -> FuturesDcaReservationBinding:
    """Bind exact pending quote to shared-account capacity without committing it."""

    if not isinstance(fill_projection, FuturesDcaFillProjection):
        raise FuturesDcaReservationError("FUTURES_DCA_FILL_PROJECTION_INVALID", "Fill projection güvenli tipte olmalıdır.")
    if not isinstance(owner, SharedAccountIdentity):
        raise FuturesDcaReservationError("FUTURES_DCA_RESERVATION_OWNER_INVALID", "Reservation owner güvenli tipte olmalıdır.")
    expected_asset = fill_projection.plan.profile.settlement_asset
    if not isinstance(capacity, AccountCapacity) or capacity.asset != expected_asset:
        raise FuturesDcaReservationError("FUTURES_DCA_RESERVATION_ASSET_CONFLICT", "Account kapasitesi Futures settlement asset ile eşleşmiyor.")
    if owner.position_mode != fill_projection.plan.profile.position_mode:
        raise FuturesDcaReservationError("FUTURES_DCA_RESERVATION_MODE_CONFLICT", "Reservation position mode Futures profile ile eşleşmiyor.")
    try:
        pending_amount = positive(fill_projection.pending_reserved_quote)
    except ValueError as error:
        raise FuturesDcaReservationError("FUTURES_DCA_RESERVATION_AMOUNT_INVALID", "Pending reservation pozitif exact decimal olmalıdır.") from error
    try:
        reservation = AccountReservation(
            reservation_id=reservation_id,
            owner=owner,
            asset=expected_asset,
            amount=exact_text(pending_amount),
        )
        projection = project_reservation(
            capacity,
            active_reservations,
            reservation.reservation_id,
            reservation.amount,
            expected_version,
        )
    except AccountReservationError as error:
        raise FuturesDcaReservationError(error.code, str(error)) from error
    return FuturesDcaReservationBinding(fill_projection, reservation, projection)
