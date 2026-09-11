"""Safe offline binding from accepted Spot lifecycle facts to core events."""

from dataclasses import dataclass
from enum import StrEnum

from dcabot.application.spot_order_lifecycle import (
    EventOutcome,
    SpotOrderLifecycle,
    SpotOrderStatus,
    SpotOrderType,
    SpotOrderEvent,
)
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply
from dcabot.domain.numbers import exact_text, number


class CoreBindingOutcome(StrEnum):
    """Outcome of one guarded Spot-to-core event binding attempt."""

    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    CORE_ORDER_TYPE_UNSUPPORTED = "CORE_ORDER_TYPE_UNSUPPORTED"
    CORE_STATUS_UNSUPPORTED = "CORE_STATUS_UNSUPPORTED"
    CORE_ROLE_REQUIRED = "CORE_ROLE_REQUIRED"
    CORE_SCOPE_CONFLICT = "CORE_SCOPE_CONFLICT"
    CORE_BINDING_REJECTED = "CORE_BINDING_REJECTED"


@dataclass(frozen=True, slots=True)
class CoreBindingResult:
    """Atomic candidate result; callers publish both projections together."""

    lifecycle: SpotOrderLifecycle
    core_state: State
    core_events: tuple[dict[str, object], ...]
    outcome: CoreBindingOutcome


def bind_spot_event_to_core(
    core_state: State,
    config: Config,
    lifecycle: SpotOrderLifecycle,
    event: SpotOrderEvent,
    *,
    fee: str | None = None,
    fee_asset: str | None = None,
    core_role: str | None = None,
) -> CoreBindingResult:
    """Bind one accepted LIMIT event without inventing venue or strategy facts.

    The Spot lifecycle remains the admission gate. Only LIMIT orders and the
    core-supported NEW/PARTIALLY_FILLED/FILLED/CANCELED statuses can cross the
    boundary. A strategy role and fee are explicit caller inputs because the
    venue event does not own either fact. Any rejected, duplicate, conflicting,
    or unsupported input leaves both projections unchanged.
    """

    if not isinstance(core_state, State) or not isinstance(config, Config):
        raise TypeError("core_state ve config geçerli core tipleri olmalıdır")
    if not isinstance(lifecycle, SpotOrderLifecycle) or not isinstance(
        event, SpotOrderEvent
    ):
        raise TypeError("lifecycle ve event geçerli Spot tipleri olmalıdır")

    order = lifecycle.order
    if order.order_type is not SpotOrderType.LIMIT:
        return _unchanged(
            lifecycle, core_state, CoreBindingOutcome.CORE_ORDER_TYPE_UNSUPPORTED
        )
    if event.status in {
        SpotOrderStatus.REJECTED,
        SpotOrderStatus.EXPIRED,
        SpotOrderStatus.EXPIRED_IN_MATCH,
    }:
        return _unchanged(lifecycle, core_state, CoreBindingOutcome.CORE_STATUS_UNSUPPORTED)

    try:
        last_filled = number(event.last_filled_qty)
    except ValueError:
        return _unchanged(lifecycle, core_state, CoreBindingOutcome.CORE_BINDING_REJECTED)
    if last_filled:
        if event.execution_id is None or fee is None or fee_asset != config.quote_asset:
            return _unchanged(lifecycle, core_state, CoreBindingOutcome.CORE_BINDING_REJECTED)
        try:
            parsed_fee = number(fee)
        except ValueError:
            return _unchanged(lifecycle, core_state, CoreBindingOutcome.CORE_BINDING_REJECTED)
        if parsed_fee < 0:
            return _unchanged(lifecycle, core_state, CoreBindingOutcome.CORE_BINDING_REJECTED)
        canonical_fee = exact_text(parsed_fee)
    else:
        if fee is not None:
            try:
                if number(fee) != 0:
                    return _unchanged(
                        lifecycle, core_state, CoreBindingOutcome.CORE_BINDING_REJECTED
                    )
            except ValueError:
                return _unchanged(
                    lifecycle, core_state, CoreBindingOutcome.CORE_BINDING_REJECTED
                )
        canonical_fee = "0"

    core_order = core_state.orders.get(order.order_id)
    if core_order is None and core_role is None:
        return _unchanged(lifecycle, core_state, CoreBindingOutcome.CORE_ROLE_REQUIRED)
    if core_order is not None and not _core_order_matches(core_order, order):
        return _unchanged(lifecycle, core_state, CoreBindingOutcome.CORE_SCOPE_CONFLICT)

    admission = lifecycle.apply(event)
    if admission.outcome is EventOutcome.DUPLICATE:
        return _unchanged(lifecycle, core_state, CoreBindingOutcome.DUPLICATE)
    if admission.outcome is not EventOutcome.ACCEPTED:
        return _unchanged(
            admission.lifecycle,
            core_state,
            CoreBindingOutcome.RECONCILIATION_REQUIRED,
        )

    core_events: list[dict[str, object]] = []
    if core_order is None:
        core_events.append(
            {
                "type": "INTENT",
                "order_id": order.order_id,
                "role": core_role,
                "qty": order.requested_quantity,
                "limit_price": order.price,
            }
        )
    if last_filled:
        core_events.append(
            {
                "type": "FILL",
                "execution_id": event.execution_id,
                "order_id": order.order_id,
                "side": order.side.value,
                "qty": event.last_filled_qty,
                "price": event.last_price,
                "fee": canonical_fee,
                "fee_asset": config.quote_asset,
            }
        )
    if event.status in {SpotOrderStatus.FILLED, SpotOrderStatus.CANCELED}:
        core_events.append(
            {
                "type": "ORDER_FINAL",
                "order_id": order.order_id,
                "status": event.status.value,
                "filled_qty": event.cumulative_filled_qty,
                "coverage_complete": True,
            }
        )

    candidate = core_state
    try:
        for core_event in core_events:
            candidate = apply(candidate, core_event, config)
    except (TypeError, ValueError):
        return _unchanged(
            lifecycle, core_state, CoreBindingOutcome.CORE_BINDING_REJECTED
        )
    return CoreBindingResult(
        lifecycle=admission.lifecycle,
        core_state=candidate,
        core_events=tuple(core_events),
        outcome=CoreBindingOutcome.ACCEPTED,
    )


def _core_order_matches(core_order, spot_order) -> bool:
    """Check identity and executable order facts without calculating economics."""

    if spot_order.requested_quantity is None or spot_order.price is None:
        return False
    try:
        return (
            core_order.side == spot_order.side.value
            and core_order.qty == number(spot_order.requested_quantity)
            and core_order.limit == number(spot_order.price)
        )
    except ValueError:
        return False


def _unchanged(
    lifecycle: SpotOrderLifecycle,
    core_state: State,
    outcome: CoreBindingOutcome,
) -> CoreBindingResult:
    return CoreBindingResult(
        lifecycle=lifecycle,
        core_state=core_state,
        core_events=(),
        outcome=outcome,
    )
