"""Exact valuation and canonical plan identity for offline rebalancing."""

from dataclasses import dataclass
import hashlib
import json
import re

from dcabot.application.rebalance_projection import RebalanceProjection
from dcabot.application.rebalance_triggers import (
    ThresholdTriggerDecision,
    TimeTriggerDecision,
)
from dcabot.domain.numbers import Q, bounded, exact_text, number, positive


_ASSET = re.compile(r"[A-Za-z0-9:_-]{1,32}\Z", re.ASCII)
_SCHEMA = "rebalance-plan-v1"


class RebalanceValuationError(ValueError):
    """Raised when holdings cannot be valued or a plan cannot be identified."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class ValuedPosition:
    """One holding valued in the valuation asset with its explicit price."""

    asset: str
    qty: str
    price: str
    value: str


@dataclass(frozen=True, slots=True)
class HoldingsValuation:
    """Canonical valued holdings before projection, order, or fill authority."""

    valuation_asset: str
    total_equity: str
    positions: tuple[ValuedPosition, ...]


@dataclass(frozen=True, slots=True)
class RebalancePlan:
    """Immutable draft plan: trigger + projection + identity, never an order."""

    plan_id: str
    schema_version: str
    status: str
    plan_time_us: int
    valuation_asset: str
    total_equity: str
    gross_buy: str
    gross_sell: str
    trigger_policy: str


def value_holdings(
    *,
    valuation_asset: str,
    holdings: tuple[tuple[str, str], ...],
    prices: tuple[tuple[str, str], ...],
) -> HoldingsValuation:
    """Value exact quantities with explicit caller-supplied conversion prices.

    Every holding except ``valuation_asset`` needs exactly one price in
    ``prices``. The valuation asset itself is implicitly 1 and must not
    carry a price entry, so no conflicting self-conversion can sneak in.
    No price lookup, fee, rounding, balance, order, reserve, or fill happens.
    """

    _validate_asset(valuation_asset, "REBALANCE_VALUATION_ASSET_INVALID")
    if not isinstance(holdings, tuple) or not holdings:
        raise RebalanceValuationError(
            "REBALANCE_VALUATION_HOLDINGS_INVALID",
            "En az bir holding tuple gereklidir.",
        )
    if not isinstance(prices, tuple):
        raise RebalanceValuationError(
            "REBALANCE_VALUATION_PRICES_INVALID",
            "Prices tuple olmalıdır.",
        )

    quantities: dict[str, Q] = {}
    for holding in holdings:
        if (
            not isinstance(holding, tuple)
            or len(holding) != 2
            or not all(isinstance(value, str) for value in holding)
        ):
            raise RebalanceValuationError(
                "REBALANCE_VALUATION_HOLDING_INVALID",
                "Holding asset ve qty string tuple olmalıdır.",
            )
        asset, raw_qty = holding
        _validate_asset(asset, "REBALANCE_VALUATION_ASSET_INVALID")
        if asset in quantities:
            raise RebalanceValuationError(
                "REBALANCE_VALUATION_ASSET_DUPLICATE",
                "Aynı asset holdings içinde iki kez bulunamaz.",
            )
        try:
            qty = number(raw_qty)
        except ValueError as error:
            raise RebalanceValuationError(
                "REBALANCE_VALUATION_QTY_INVALID",
                "Qty decimal string olmalıdır.",
            ) from error
        if qty < 0:
            raise RebalanceValuationError(
                "REBALANCE_VALUATION_QTY_INVALID",
                "Qty negatif olamaz.",
            )
        quantities[asset] = qty

    quote: dict[str, Q] = {}
    for entry in prices:
        if (
            not isinstance(entry, tuple)
            or len(entry) != 2
            or not all(isinstance(value, str) for value in entry)
        ):
            raise RebalanceValuationError(
                "REBALANCE_VALUATION_PRICE_ENTRY_INVALID",
                "Price asset ve price string tuple olmalıdır.",
            )
        asset, raw_price = entry
        _validate_asset(asset, "REBALANCE_VALUATION_ASSET_INVALID")
        if asset == valuation_asset:
            raise RebalanceValuationError(
                "REBALANCE_VALUATION_SELF_PRICE_FORBIDDEN",
                "Valuation asset için price verilemez, değeri 1'dir.",
            )
        if asset in quote:
            raise RebalanceValuationError(
                "REBALANCE_VALUATION_PRICE_DUPLICATE",
                "Aynı asset için iki price verilemez.",
            )
        try:
            price = positive(raw_price)
        except ValueError as error:
            raise RebalanceValuationError(
                "REBALANCE_VALUATION_PRICE_INVALID",
                "Price pozitif decimal string olmalıdır.",
            ) from error
        quote[asset] = price

    for asset in quantities:
        if asset != valuation_asset and asset not in quote:
            raise RebalanceValuationError(
                "REBALANCE_VALUATION_PRICE_MISSING",
                "Her holding için explicit conversion price gereklidir.",
            )
    for asset in quote:
        if asset not in quantities:
            raise RebalanceValuationError(
                "REBALANCE_VALUATION_PRICE_UNEXPECTED",
                "Tutlmayan asset için price verilemez.",
            )

    try:
        positions: list[ValuedPosition] = []
        total = Q(0)
        for asset in sorted(quantities):
            qty = quantities[asset]
            price = Q(1) if asset == valuation_asset else quote[asset]
            value = bounded(qty * price)
            total = bounded(total + value)
            positions.append(
                ValuedPosition(
                    asset=asset,
                    qty=exact_text(qty),
                    price=exact_text(price),
                    value=exact_text(value),
                )
            )
        return HoldingsValuation(
            valuation_asset=valuation_asset,
            total_equity=exact_text(total),
            positions=tuple(positions),
        )
    except ValueError as error:
        raise RebalanceValuationError(
            "REBALANCE_VALUATION_UNREPRESENTABLE",
            "Valuation mevcut exact decimal sözleşmesine sığmıyor.",
        ) from error


def build_rebalance_plan(
    *,
    trigger: ThresholdTriggerDecision | TimeTriggerDecision,
    projection: RebalanceProjection,
    plan_time_us: int,
) -> RebalancePlan:
    """Bind one TRIGGERED gate result to one projection with a stable identity.

    The plan is a DRAFT record: it carries gross buy/sell totals and a
    deterministic ``plan_id`` (SHA-256 over canonical JSON), but no order,
    reserve, or fill authority. A NOT_TRIGGERED gate can never produce a plan.
    """

    if not isinstance(trigger, (ThresholdTriggerDecision, TimeTriggerDecision)):
        raise RebalanceValuationError(
            "REBALANCE_PLAN_TRIGGER_INVALID",
            "Trigger kararı geçersiz.",
        )
    if trigger.status != "TRIGGERED":
        raise RebalanceValuationError(
            "REBALANCE_PLAN_TRIGGER_NOT_TRIGGERED",
            "Tetiklenmemiş gate plan üretemez.",
        )
    if not isinstance(projection, RebalanceProjection) or not projection.targets:
        raise RebalanceValuationError(
            "REBALANCE_PLAN_PROJECTION_INVALID",
            "Projection kaydı geçersiz.",
        )
    if type(plan_time_us) is not int or plan_time_us < 0:
        raise RebalanceValuationError(
            "REBALANCE_PLAN_TIME_INVALID",
            "Plan zamanı sıfır veya pozitif integer microseconds olmalıdır.",
        )

    try:
        deltas = [number(target.trade_delta) for target in projection.targets]
        gross_buy = bounded(sum((d for d in deltas if d > 0), Q(0)))
        gross_sell = bounded(sum((-d for d in deltas if d < 0), Q(0)))
    except ValueError as error:
        raise RebalanceValuationError(
            "REBALANCE_PLAN_DELTA_INVALID",
            "Projection delta değerleri exact decimal olmalıdır.",
        ) from error

    if isinstance(trigger, ThresholdTriggerDecision):
        trigger_part: dict[str, object] = {
            "policy": trigger.policy,
            "status": trigger.status,
            "deviation": trigger.deviation,
            "threshold": trigger.threshold,
        }
    else:
        trigger_part = {
            "policy": trigger.policy,
            "status": trigger.status,
            "elapsed_us": trigger.elapsed_us,
            "interval_us": trigger.interval_us,
        }
    canonical = json.dumps(
        {
            "plan_time_us": plan_time_us,
            "projection": {
                "targets": [
                    [t.asset, t.target_weight, t.target_value, t.current_value, t.trade_delta]
                    for t in projection.targets
                ],
                "total_equity": projection.total_equity,
                "valuation_asset": projection.valuation_asset,
            },
            "schema": _SCHEMA,
            "trigger": trigger_part,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    plan_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    try:
        return RebalancePlan(
            plan_id=plan_id,
            schema_version=_SCHEMA,
            status="DRAFT",
            plan_time_us=plan_time_us,
            valuation_asset=projection.valuation_asset,
            total_equity=projection.total_equity,
            gross_buy=exact_text(gross_buy),
            gross_sell=exact_text(gross_sell),
            trigger_policy=trigger.policy,
        )
    except ValueError as error:
        raise RebalanceValuationError(
            "REBALANCE_PLAN_UNREPRESENTABLE",
            "Plan brüt toplamları exact decimal sözleşmesine sığmıyor.",
        ) from error


def _validate_asset(value: str, code: str) -> None:
    if not isinstance(value, str) or _ASSET.fullmatch(value) is None:
        raise RebalanceValuationError(code, "Asset kimliği geçersiz.")
