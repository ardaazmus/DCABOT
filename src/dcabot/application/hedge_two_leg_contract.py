"""Profile-neutral hedge identity and two-leg lifecycle boundary."""

from dataclasses import dataclass
from typing import Final
import re


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)
_POSITION_MODES: Final = ("ONE_WAY", "HEDGE")
_HEDGE_SIDES: Final = ("LONG", "SHORT")


class HedgeTwoLegError(ValueError):
    """Raised when hedge identity or two-leg state violates its contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class TwoLegState:
    """Stable lifecycle labels for a two-leg strategy boundary."""

    NONE: Final = "NONE"
    LEG_A_PENDING: Final = "LEG_A_PENDING"
    ONE_LEG_FILLED: Final = "ONE_LEG_FILLED"
    PARTIAL_HEDGE: Final = "PARTIAL_HEDGE"
    BOTH_ESTABLISHED: Final = "BOTH_ESTABLISHED"
    RECOVERY_REQUIRED: Final = "RECOVERY_REQUIRED"
    TIMEOUT: Final = "TIMEOUT"


_STATES: Final = (
    TwoLegState.NONE,
    TwoLegState.LEG_A_PENDING,
    TwoLegState.ONE_LEG_FILLED,
    TwoLegState.PARTIAL_HEDGE,
    TwoLegState.BOTH_ESTABLISHED,
    TwoLegState.RECOVERY_REQUIRED,
    TwoLegState.TIMEOUT,
)


@dataclass(frozen=True, slots=True)
class HedgePositionIdentity:
    """Immutable position scope that keeps net and hedge sides distinct."""

    account_id: str
    venue_profile: str
    product_id: str
    symbol: str
    position_mode: str
    hedge_side: str | None

    def __post_init__(self) -> None:
        for value, code in (
            (self.account_id, "HEDGE_ACCOUNT_INVALID"),
            (self.venue_profile, "HEDGE_PROFILE_INVALID"),
            (self.product_id, "HEDGE_PRODUCT_INVALID"),
            (self.symbol, "HEDGE_SYMBOL_INVALID"),
        ):
            _validate_identifier(value, code)
        if self.position_mode not in _POSITION_MODES:
            raise HedgeTwoLegError(
                "HEDGE_POSITION_MODE_INVALID",
                "position_mode ONE_WAY veya HEDGE olmalıdır.",
            )
        if self.position_mode == "ONE_WAY" and self.hedge_side is not None:
            raise HedgeTwoLegError(
                "ONE_WAY_HEDGE_SIDE",
                "ONE_WAY identity hedge side taşıyamaz.",
            )
        if self.position_mode == "HEDGE" and self.hedge_side not in _HEDGE_SIDES:
            raise HedgeTwoLegError(
                "HEDGE_SIDE_REQUIRED",
                "HEDGE identity LONG veya SHORT side taşımalıdır.",
            )


def new_hedge_position_identity(
    *,
    account_id: str,
    venue_profile: str,
    product_id: str,
    symbol: str,
    position_mode: str,
    hedge_side: str | None,
) -> HedgePositionIdentity:
    """Construct an explicit position identity without netting or accounting."""

    return HedgePositionIdentity(
        account_id=account_id,
        venue_profile=venue_profile,
        product_id=product_id,
        symbol=symbol,
        position_mode=position_mode,
        hedge_side=hedge_side,
    )


_TRANSITIONS: Final = {
    (TwoLegState.NONE, "LEG_A_SENT"): TwoLegState.LEG_A_PENDING,
    (TwoLegState.LEG_A_PENDING, "LEG_A_ACCEPTED_FILL"): TwoLegState.ONE_LEG_FILLED,
    (TwoLegState.LEG_A_PENDING, "LEG_A_PARTIAL_FILL"): TwoLegState.PARTIAL_HEDGE,
    (TwoLegState.ONE_LEG_FILLED, "BOTH_LEGS_ACCEPTED"): TwoLegState.BOTH_ESTABLISHED,
    (TwoLegState.PARTIAL_HEDGE, "BOTH_LEGS_ACCEPTED"): TwoLegState.BOTH_ESTABLISHED,
}

for _state in (
    TwoLegState.LEG_A_PENDING,
    TwoLegState.ONE_LEG_FILLED,
    TwoLegState.PARTIAL_HEDGE,
):
    _TRANSITIONS[(_state, "RECOVERY_REQUIRED")] = TwoLegState.RECOVERY_REQUIRED
    _TRANSITIONS[(_state, "TIMEOUT")] = TwoLegState.TIMEOUT


def advance_two_leg_state(state: str, event: str) -> str:
    """Advance only explicitly allowed lifecycle states; never invent a fill."""

    if state not in _STATES:
        raise HedgeTwoLegError("TWO_LEG_STATE_INVALID", "Two-leg state geçersiz.")
    if not isinstance(event, str) or not _IDENTIFIER.fullmatch(event):
        raise HedgeTwoLegError("TWO_LEG_EVENT_INVALID", "Two-leg event geçersiz.")
    try:
        return _TRANSITIONS[(state, event)]
    except KeyError as error:
        raise HedgeTwoLegError(
            "TWO_LEG_TRANSITION_INVALID",
            f"{state} durumundan {event} geçişi tanımlı değildir.",
        ) from error


def _validate_identifier(value: object, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise HedgeTwoLegError(code, "Kimlik değeri geçersiz.")
