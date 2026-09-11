"""Internal BASE-only bridge from fixed-limit observations to the core reducer."""

from dataclasses import dataclass
import hashlib
import json
import re

from dcabot.application.historical_fixed_limit import (
    FixedLimitAction,
    FixedLimitObservation,
    FixedLimitOrder,
    simulate_fixed_limit_order,
)
from dcabot.data_adapters.historical import HistoricalDatasetInput
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply, report
from dcabot.domain.numbers import Q, exact_text, number, round_quantum


BASE_LIMIT_BINDING_MODEL = "historical_ohlcv_base_fixed_limit_binding_v1"
BASE_LIMIT_BINDING_POLICY = "BASE_ONLY_CORE_REDUCER_V1"
BASE_LIMIT_RESERVE_MODEL = "NONE"
BASE_LIMIT_RESERVE_AMOUNT = "NOT_MODELED"
BASE_LIMIT_RESERVE_ASSET = "NOT_APPLICABLE"
_HASH_PATTERN = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)


class HistoricalBaseLimitBindingError(ValueError):
    """Raised when the guarded BASE-only bridge cannot safely continue."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class HistoricalBaseLimitBindingResult:
    """Internal result that keeps fixed observations and core state together."""

    model: str
    policy: str
    reserve_model: str
    reserve_amount: str
    reserve_asset: str
    production_ready: bool
    config_hash: str
    status: str
    application_code: str | None
    processed_bar_count: int
    observations: tuple[FixedLimitObservation, ...]
    actions: tuple[FixedLimitAction, ...]
    state: State
    summary: dict[str, object]


def simulate_base_fixed_limit_binding(
    dataset: HistoricalDatasetInput,
    config: Config,
    order: FixedLimitOrder,
    *,
    slice_qty: str,
    config_hash: str,
    ambiguous_bar_indices: set[int] | frozenset[int] | None = None,
) -> HistoricalBaseLimitBindingResult:
    """Apply only BASE fixed-limit candidates through the existing core reducer.

    This is an internal research bridge. It deliberately exposes no public
    profile or persistence path and declares that reserve is not modeled.
    """

    _validate_binding_inputs(dataset, config, order, config_hash)
    fixed = simulate_fixed_limit_order(
        dataset,
        config,
        order,
        slice_qty=slice_qty,
        ambiguous_bar_indices=ambiguous_bar_indices,
    )
    state = _open_base_order(dataset, config, order)
    actions_by_bar = {action.bar_index: action for action in fixed.actions}

    for observation in fixed.observations:
        bar = dataset.bars[observation.bar_index - 1]
        action = actions_by_bar.get(observation.bar_index)
        if action is not None:
            state = _commit_candidate(state, config, order, action)
        state = apply(state, {"type": "MARK", "price": bar.close}, config)

    if fixed.status == "FILLED":
        _require_complete_order(state, order)

    return HistoricalBaseLimitBindingResult(
        model=BASE_LIMIT_BINDING_MODEL,
        policy=BASE_LIMIT_BINDING_POLICY,
        reserve_model=BASE_LIMIT_RESERVE_MODEL,
        reserve_amount=BASE_LIMIT_RESERVE_AMOUNT,
        reserve_asset=BASE_LIMIT_RESERVE_ASSET,
        production_ready=False,
        config_hash=config_hash,
        status=fixed.status,
        application_code=fixed.application_code,
        processed_bar_count=fixed.processed_bar_count,
        observations=fixed.observations,
        actions=fixed.actions,
        state=state,
        summary=report(state, config),
    )


def _validate_binding_inputs(
    dataset: HistoricalDatasetInput,
    config: Config,
    order: FixedLimitOrder,
    config_hash: str,
) -> None:
    if not isinstance(dataset, HistoricalDatasetInput):
        raise HistoricalBaseLimitBindingError("DATASET_INVALID", "Historical dataset girdisi geçersiz.")
    if order.side != "BUY":
        raise HistoricalBaseLimitBindingError("BASE_SIDE_REQUIRED", "BASE binding yalnız BUY order kabul eder.")
    if number(order.original_qty) != config.base_qty:
        raise HistoricalBaseLimitBindingError(
            "BASE_QUANTITY_REQUIRED",
            "BASE binding miktarı aktif config base_qty ile eşleşmelidir.",
        )
    if order.placement_bar_index < 1:
        raise HistoricalBaseLimitBindingError(
            "PLACEMENT_BAR_REQUIRED",
            "BASE binding placement kimliği dataset içindeki bir barı göstermelidir.",
        )
    if not isinstance(config_hash, str) or _HASH_PATTERN.fullmatch(config_hash) is None:
        raise HistoricalBaseLimitBindingError("CONFIG_HASH_INVALID", "Config hash kimliği geçersiz.")


def _open_base_order(
    dataset: HistoricalDatasetInput,
    config: Config,
    order: FixedLimitOrder,
) -> State:
    placement_bar = dataset.bars[order.placement_bar_index - 1]
    state = apply(State(), {"type": "MARK", "price": placement_bar.close}, config)
    try:
        return apply(
            state,
            {
                "type": "INTENT",
                "order_id": order.order_id,
                "role": "BASE",
                "qty": order.original_qty,
                "limit_price": order.limit_price,
            },
            config,
        )
    except (ValueError, ZeroDivisionError) as exc:
        raise HistoricalBaseLimitBindingError(
            "CORE_INTENT_REJECTED",
            "BASE limit order core intent politikası tarafından reddedildi.",
        ) from exc


def _commit_candidate(
    state: State,
    config: Config,
    order: FixedLimitOrder,
    action: FixedLimitAction,
) -> State:
    quantity = number(action.quantity)
    price = number(action.fill_price)
    fee = round_quantum(quantity * price * config.fee_rate, config.fee_quantum)
    try:
        state = apply(
            state,
            {
                "type": "FILL",
                "execution_id": f"base_limit_binding:{action.bar_index}:fill",
                "order_id": order.order_id,
                "side": "BUY",
                "qty": exact_text(quantity),
                "price": exact_text(price),
                "fee": exact_text(fee),
                "fee_asset": config.quote_asset,
            },
            config,
        )
    except (ValueError, ZeroDivisionError) as exc:
        raise HistoricalBaseLimitBindingError(
            "CORE_FILL_REJECTED",
            "BASE limit fill candidate core reducer tarafından reddedildi.",
        ) from exc
    core_order = state.orders[order.order_id]
    if (
        core_order.filled != number(action.cumulative_filled_qty)
        or core_order.leaves != number(action.leaves_qty)
    ):
        raise HistoricalBaseLimitBindingError(
            "CORE_PROJECTION_MISMATCH",
            "Core order projection fixed-limit candidate ile eşleşmiyor.",
        )
    if core_order.leaves == 0:
        try:
            state = apply(
                state,
                {
                    "type": "ORDER_FINAL",
                    "order_id": order.order_id,
                    "status": "FILLED",
                    "filled_qty": exact_text(core_order.filled),
                    "coverage_complete": True,
                },
                config,
            )
        except (ValueError, ZeroDivisionError) as exc:
            raise HistoricalBaseLimitBindingError(
                "CORE_FINAL_REJECTED",
                "BASE limit final coverage core reducer tarafından reddedildi.",
            ) from exc
    return state


def _require_complete_order(state: State, order: FixedLimitOrder) -> None:
    core_order = state.orders[order.order_id]
    if not core_order.complete or core_order.status != "FILLED":
        raise HistoricalBaseLimitBindingError(
            "CORE_FINAL_MISSING",
            "Fixed-limit sonucu FILLED olduğu halde core final coverage oluşmadı.",
        )


def base_limit_binding_identity_sha256(
    *,
    dataset_id: str,
    artifact_sha256: str,
    profile_id: str,
    profile_version: str,
    config_hash: str,
    order: FixedLimitOrder,
    slice_qty: str,
) -> str:
    """Hash the immutable policy, profile, config, and BASE order binding."""

    payload = {
        "schema_version": 1,
        "model": BASE_LIMIT_BINDING_MODEL,
        "policy": BASE_LIMIT_BINDING_POLICY,
        "profile_id": profile_id,
        "profile_version": profile_version,
        "dataset_id": dataset_id,
        "artifact_sha256": artifact_sha256,
        "config_hash": config_hash,
        "order": {
            "order_id": order.order_id,
            "side": order.side,
            "limit_price": order.limit_price,
            "original_qty": order.original_qty,
            "placement_bar_index": order.placement_bar_index,
            "placement_open_time_us": order.placement_open_time_us,
        },
        "slice_qty": slice_qty,
        "reserve_model": BASE_LIMIT_RESERVE_MODEL,
    }
    canonical = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
