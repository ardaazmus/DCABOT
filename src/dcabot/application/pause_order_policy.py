"""Pure, non-economic policy contract for paused lifecycle orders."""

from dataclasses import dataclass
from typing import Final


_POLICIES: Final = frozenset({"KEEP_OPEN", "CANCEL_REQUESTED", "BLOCKED"})


class PauseOrderPolicyError(ValueError):
    """Raised when a paused-order policy is outside the explicit contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class PausedOrderDecision:
    """Describes pause handling without applying an order-side effect."""

    pending_order_action: str
    new_intent_action: str
    cancellation_state: str


def evaluate_paused_orders(policy: str) -> PausedOrderDecision:
    """Return the explicit paused-order decision for ``policy``.

    A paused lifecycle never accepts a new economic intent. ``CANCEL_REQUESTED``
    records only a request; it does not claim that cancellation or any fill has
    occurred. Applying either action remains the responsibility of a future
    order adapter with its own event and execution-identity contract.
    """

    if not isinstance(policy, str) or policy not in _POLICIES:
        raise PauseOrderPolicyError(
            "PAUSE_ORDER_POLICY_INVALID",
            "PAUSED order policy explicit bir profilden seçilmelidir.",
        )
    cancellation_state = (
        "REQUESTED_NOT_CONFIRMED" if policy == "CANCEL_REQUESTED" else "NOT_REQUESTED"
    )
    return PausedOrderDecision(
        pending_order_action=policy,
        new_intent_action="BLOCKED",
        cancellation_state=cancellation_state,
    )
