"""Types and exact reducer helpers for the opt-in fixed-slice runner."""

from dataclasses import dataclass

from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply, report
from dcabot.domain.numbers import Q, exact_text, round_quantum


FIXED_SLICE_MODEL = "historical_ohlcv_partial_fixed_v1"
FIXED_SLICE_PROVENANCE = "OHLC_TOUCH_FIXED_SLICE_ASSUMPTION"


@dataclass(frozen=True, slots=True)
class HistoricalFixedSliceAction:
    """One fixed-slice execution with its post-execution order projection."""

    event_sequence: int
    bar_index: int
    open_time_us: int
    action_type: str
    role: str
    order_id: str
    execution_id: str
    raw_reference: str
    fill_price: str
    quantity: str
    fee: str
    fee_asset: str
    order_status_after: str
    original_qty: str
    cumulative_filled_qty: str
    leaves_qty: str
    canceled_qty: str
    fill_provenance: str


@dataclass(frozen=True, slots=True)
class HistoricalFixedSliceResult:
    """Bounded result for the opt-in fixed-slice application runner."""

    execution_status: str
    application_code: str | None
    processed_bar_count: int
    first_ambiguous_bar_index: int | None
    position_status: str
    synthetic_cancel_applied: bool
    actions: tuple[HistoricalFixedSliceAction, ...]
    summary: dict[str, object]


def apply_fixed_slice_fill(
    state: State,
    config: Config,
    bar: CanonicalBar,
    bar_index: int,
    order_id: str,
    fixed_qty: Q,
    actions: list[HistoricalFixedSliceAction],
) -> State:
    """Apply one bounded exact fill and record its post-fill projection."""

    order = state.orders[order_id]
    fill_qty = min(fixed_qty, order.leaves)
    fill_price = order.limit
    fee = round_quantum(fill_qty * fill_price * config.fee_rate, config.fee_quantum)
    execution_id = f"historical_partial:{bar_index}:fill"
    state = apply(
        state,
        {
            "type": "FILL",
            "execution_id": execution_id,
            "order_id": order_id,
            "side": order.side,
            "qty": exact_text(fill_qty),
            "price": exact_text(fill_price),
            "fee": exact_text(fee),
            "fee_asset": config.quote_asset,
        },
        config,
    )
    if state.orders[order_id].leaves == 0:
        state = apply(
            state,
            {
                "type": "ORDER_FINAL",
                "order_id": order_id,
                "status": "FILLED",
                "filled_qty": exact_text(state.orders[order_id].filled),
                "coverage_complete": True,
            },
            config,
        )
    order = state.orders[order_id]
    actions.append(
        HistoricalFixedSliceAction(
            event_sequence=len(actions) + 1,
            bar_index=bar_index,
            open_time_us=bar.open_time_us,
            action_type="FULL_FILL" if order.status == "FILLED" else "PARTIAL_FILL",
            role=order.role,
            order_id=order_id,
            execution_id=execution_id,
            raw_reference=exact_text(fill_price),
            fill_price=exact_text(fill_price),
            quantity=exact_text(fill_qty),
            fee=exact_text(fee),
            fee_asset=config.quote_asset,
            order_status_after=order.status,
            original_qty=exact_text(order.qty),
            cumulative_filled_qty=exact_text(order.filled),
            leaves_qty=exact_text(order.leaves),
            canceled_qty=exact_text(order.canceled),
            fill_provenance=FIXED_SLICE_PROVENANCE,
        )
    )
    return state


def fixed_slice_result(
    dataset: HistoricalDatasetInput,
    config: Config,
    config_hash: str,
    state: State,
    actions: list[HistoricalFixedSliceAction],
    *,
    execution_status: str,
    application_code: str | None,
    processed_bar_count: int,
    first_ambiguous_bar_index: int | None = None,
) -> HistoricalFixedSliceResult:
    """Build a bounded fixed-slice result without synthetic cancellation."""

    summary = report(state, config)
    position_status = "OPEN_AT_END" if state.position.qty or state.unsettled else "CLOSED"
    summary.update(
        {
            "dataset_id": dataset.metadata.dataset_id,
            "artifact_sha256": dataset.metadata.artifact_sha256,
            "config_hash": config_hash,
            "model": FIXED_SLICE_MODEL,
            "processed_bar_count": processed_bar_count,
            "position_status": position_status,
            "synthetic_cancel_applied": False,
            "fill_provenance": FIXED_SLICE_PROVENANCE,
            "reserve_model": "NONE",
            "same_bar_cancel_fill_race": "NOT_MODELED",
        }
    )
    return HistoricalFixedSliceResult(
        execution_status=execution_status,
        application_code=application_code,
        processed_bar_count=processed_bar_count,
        first_ambiguous_bar_index=first_ambiguous_bar_index,
        position_status=position_status,
        synthetic_cancel_applied=False,
        actions=tuple(actions),
        summary=summary,
    )
