"""Pure, fail-closed release transitions for one Futures DCA reservation."""

from dataclasses import dataclass, replace

from dcabot.domain.numbers import exact_text, number

from .futures_dca_journal_schema import (
    FuturesDcaJournalSchemaError,
    FuturesDcaReservationProjection,
    _IDENTIFIER,
    _normalize_reservation,
)


_TRANSITION_KINDS = frozenset({"PARTIAL_FILL", "FULL_FILL", "CANCEL", "LATE_FILL", "UNKNOWN"})
_ALLOWED_STATES = frozenset({"OPEN", "PARTIAL", "RELEASED", "CANCELED", "QUARANTINED"})


class FuturesDcaReleaseTransitionError(FuturesDcaJournalSchemaError):
    """Raised when a reservation release transition is not admissible."""


@dataclass(frozen=True, slots=True)
class FuturesDcaReleaseTransition:
    """Caller-identified, exact transition request without persistence authority."""

    reservation_id: str
    transition_event_id: str
    release_identity: str
    release_cursor: int
    expected_version: int
    transition_kind: str
    consumed_amount: str
    releasable_amount: str


def apply_futures_dca_release_transition(
    reservation: FuturesDcaReservationProjection,
    transition: FuturesDcaReleaseTransition,
) -> tuple[FuturesDcaReservationProjection, str]:
    """Return a new reservation projection and ``ACCEPTED``/``DUPLICATE``.

    Partial/full fills and cancellation conserve the original reservation.
    Late or UNKNOWN observations quarantine the reservation without inventing
    consumed or released economic amounts. This function is intentionally
    non-persistent; the bounded journal remains the later ownership boundary.
    """

    current = _normalize_reservation(reservation)
    _validate_transition(transition)
    if current.reservation_id != transition.reservation_id:
        raise FuturesDcaReleaseTransitionError(
            "FUTURES_DCA_RELEASE_SCOPE_CONFLICT", "Transition başka reservation’a ait."
        )
    if _is_duplicate(current, transition):
        return current, "DUPLICATE"
    if current.release_identity == transition.release_identity and current.release_cursor == transition.release_cursor:
        raise FuturesDcaReleaseTransitionError(
            "FUTURES_DCA_RELEASE_CONFLICT", "Release identity farklı transition payload ile kullanılamaz."
        )
    if transition.release_cursor != current.release_cursor + 1:
        raise FuturesDcaReleaseTransitionError(
            "FUTURES_DCA_RELEASE_CURSOR_INVALID", "Release cursor ardışık olmalıdır."
        )
    if transition.expected_version != current.version:
        raise FuturesDcaReleaseTransitionError(
            "FUTURES_DCA_RELEASE_VERSION_CONFLICT", "Reservation version transition öncesiyle eşleşmiyor."
        )
    target_state = _target_state(current.terminal_state, transition.transition_kind)
    consumed_amount, releasable_amount = _transition_amounts(current, transition)
    return replace(
        current,
        consumed_amount=consumed_amount,
        releasable_amount=releasable_amount,
        release_identity=transition.release_identity,
        terminal_state=target_state,
        version=current.version + 1,
        release_cursor=transition.release_cursor,
    ), "ACCEPTED"


def _is_duplicate(
    current: FuturesDcaReservationProjection,
    transition: FuturesDcaReleaseTransition,
) -> bool:
    if (current.release_identity, current.release_cursor) != (
        transition.release_identity,
        transition.release_cursor,
    ):
        return False
    if transition.expected_version + 1 != current.version:
        return False
    if (transition.consumed_amount, transition.releasable_amount) != (
        current.consumed_amount,
        current.releasable_amount,
    ):
        return False
    allowed_kinds = {
        "PARTIAL": {"PARTIAL_FILL"},
        "RELEASED": {"FULL_FILL"},
        "CANCELED": {"CANCEL"},
        "QUARANTINED": {"LATE_FILL", "UNKNOWN"},
    }.get(current.terminal_state, set())
    return transition.transition_kind in allowed_kinds


def _candidate(
    current: FuturesDcaReservationProjection,
    transition: FuturesDcaReleaseTransition,
) -> FuturesDcaReservationProjection:
    target_state = _target_state(current.terminal_state, transition.transition_kind)
    consumed_amount, releasable_amount = _transition_amounts(current, transition)
    return replace(
        current,
        consumed_amount=consumed_amount,
        releasable_amount=releasable_amount,
        release_identity=transition.release_identity,
        terminal_state=target_state,
        version=current.version + 1,
        release_cursor=transition.release_cursor,
    )


def _validate_transition(transition: FuturesDcaReleaseTransition) -> None:
    if not isinstance(transition, FuturesDcaReleaseTransition):
        raise FuturesDcaReleaseTransitionError(
            "FUTURES_DCA_RELEASE_INVALID", "Release transition güvenli tipte değil."
        )
    for value in (
        transition.reservation_id,
        transition.transition_event_id,
        transition.release_identity,
    ):
        if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
            raise FuturesDcaReleaseTransitionError(
                "FUTURES_DCA_RELEASE_INVALID", "Release transition identity geçersiz."
            )
    if transition.transition_kind not in _TRANSITION_KINDS:
        raise FuturesDcaReleaseTransitionError(
            "FUTURES_DCA_RELEASE_INVALID", "Release transition türü geçersiz."
        )
    if type(transition.release_cursor) is not int or transition.release_cursor < 1:
        raise FuturesDcaReleaseTransitionError(
            "FUTURES_DCA_RELEASE_INVALID", "Release cursor pozitif olmalıdır."
        )
    if type(transition.expected_version) is not int or transition.expected_version < 0:
        raise FuturesDcaReleaseTransitionError(
            "FUTURES_DCA_RELEASE_INVALID", "Beklenen reservation version geçersiz."
        )
    for value in (transition.consumed_amount, transition.releasable_amount):
        try:
            parsed = number(value)
            if parsed < 0 or exact_text(parsed) != value:
                raise ValueError
        except (TypeError, ValueError) as exc:
            raise FuturesDcaReleaseTransitionError(
                "FUTURES_DCA_RELEASE_INVALID", "Release miktarları exact ve negatif olmayan değerler olmalıdır."
            ) from exc


def _target_state(current_state: str, transition_kind: str) -> str:
    if current_state not in _ALLOWED_STATES:
        raise FuturesDcaReleaseTransitionError(
            "FUTURES_DCA_RELEASE_STATE_INVALID", "Reservation state release transition için geçersiz."
        )
    target = {
        "PARTIAL_FILL": "PARTIAL",
        "FULL_FILL": "RELEASED",
        "CANCEL": "CANCELED",
        "LATE_FILL": "QUARANTINED",
        "UNKNOWN": "QUARANTINED",
    }[transition_kind]
    if transition_kind in {"LATE_FILL", "UNKNOWN"}:
        allowed = current_state in {"OPEN", "PARTIAL"} or (
            transition_kind == "LATE_FILL" and current_state in {"RELEASED", "CANCELED"}
        )
    else:
        allowed = current_state in {"OPEN", "PARTIAL"}
    if not allowed:
        raise FuturesDcaReleaseTransitionError(
            "FUTURES_DCA_RELEASE_TRANSITION_INVALID", "Reservation state için transition sırası geçersiz."
        )
    return target


def _transition_amounts(
    current: FuturesDcaReservationProjection,
    transition: FuturesDcaReleaseTransition,
) -> tuple[str, str]:
    reserved = number(current.reserved_amount)
    prior_consumed = number(current.consumed_amount)
    consumed = number(transition.consumed_amount)
    releasable = number(transition.releasable_amount)
    if consumed + releasable != reserved or consumed < prior_consumed:
        raise FuturesDcaReleaseTransitionError(
            "FUTURES_DCA_RELEASE_CONSERVATION", "Reserved miktar consumed + releasable olarak korunmalıdır."
        )
    if transition.transition_kind == "PARTIAL_FILL":
        if not prior_consumed < consumed < reserved or releasable <= 0:
            raise FuturesDcaReleaseTransitionError(
                "FUTURES_DCA_PARTIAL_INVALID", "Partial fill kalan reservation’ı ve pozitif tüketimi taşımalıdır."
            )
    elif transition.transition_kind == "FULL_FILL":
        if consumed != reserved or releasable != 0:
            raise FuturesDcaReleaseTransitionError(
                "FUTURES_DCA_FULL_FILL_INVALID", "Full fill tüm reservation’ı tüketmelidir."
            )
    elif transition.transition_kind == "CANCEL":
        if consumed != prior_consumed:
            raise FuturesDcaReleaseTransitionError(
                "FUTURES_DCA_CANCEL_MANUFACTURES_FILL", "Cancel yeni consumed miktar üretemez."
            )
    elif transition.transition_kind in {"LATE_FILL", "UNKNOWN"}:
        if consumed != prior_consumed or releasable != number(current.releasable_amount):
            raise FuturesDcaReleaseTransitionError(
                "FUTURES_DCA_QUARANTINE_MUTATES_ECONOMICS", "Late/UNKNOWN ekonomik miktarları değiştiremez."
            )
    return exact_text(consumed), exact_text(releasable)
