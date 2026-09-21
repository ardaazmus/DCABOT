"""Fee/rounding disclosure and reserve-checked order binding for rebalance plans.

Every plan line is disclosed with gross delta, explicit fee, net delta, raw
quantity, quantized quantity, and the unrepresentable remainder — nothing is
rounded silently. Lines that cannot trade are SKIPPED with an explicit reason.
Order candidates bind only from READY disclosures with sufficient reserve;
candidates are MARKET intents, never venue orders.
"""

from dataclasses import dataclass
import hashlib
import json
import re

from dcabot.application.rebalance_projection import RebalanceProjection
from dcabot.application.rebalance_valuation import RebalancePlan
from dcabot.domain.numbers import Q, bounded, exact_text, number, positive


_ASSET = re.compile(r"[A-Za-z0-9:_-]{1,32}\Z", re.ASCII)


class RebalanceExecutionError(ValueError):
    """Raised when a plan cannot be disclosed or bound safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class ExecutionLine:
    """One disclosed plan line with fee, quantization, and explicit status."""

    asset: str
    side: str
    gross_delta: str
    fee: str
    net_delta: str
    qty: str
    quantized_qty: str
    remainder_qty: str
    notional: str
    status: str


@dataclass(frozen=True, slots=True)
class ExecutionDisclosure:
    """Immutable per-line disclosure plus one plan-level tradeability status."""

    plan_id: str
    status: str
    total_buy_gross: str
    total_fee: str
    lines: tuple[ExecutionLine, ...]


@dataclass(frozen=True, slots=True)
class RebalanceOrderCandidate:
    """One immutable MARKET-intent candidate; execution authority lives elsewhere."""

    candidate_id: str
    plan_id: str
    asset: str
    side: str
    qty: str
    order_time_us: int
    status: str


def disclose_execution(
    *,
    plan: RebalancePlan,
    projection: RebalanceProjection,
    prices: tuple[tuple[str, str], ...],
    fee_rate: str,
    qty_step: str,
    min_notional: str,
    cash_reserve: str,
) -> ExecutionDisclosure:
    """Disclose fees, quantization, and reserve against one plan+projection."""

    if not isinstance(plan, RebalancePlan) or plan.status != "DRAFT":
        raise RebalanceExecutionError(
            "REBALANCE_EXEC_PLAN_INVALID", "Plan kaydı geçersiz."
        )
    if not isinstance(projection, RebalanceProjection) or not projection.targets:
        raise RebalanceExecutionError(
            "REBALANCE_EXEC_PROJECTION_INVALID", "Projection kaydı geçersiz."
        )
    _require_gross_match(plan, projection)
    quote = _checked_prices(prices, projection)
    try:
        fee = number(fee_rate)
    except ValueError as error:
        raise RebalanceExecutionError(
            "REBALANCE_EXEC_FEE_INVALID", "Fee oranı decimal olmalıdır."
        ) from error
    if not 0 <= fee < 1:
        raise RebalanceExecutionError(
            "REBALANCE_EXEC_FEE_INVALID", "Fee oranı 0 ile 1 arasında olmalıdır."
        )
    try:
        step = positive(qty_step)
        minimum = positive(min_notional)
        reserve = number(cash_reserve)
    except ValueError as error:
        raise RebalanceExecutionError(
            "REBALANCE_EXEC_PROFILE_INVALID", "Grid/rezerv profili geçersiz."
        ) from error
    if reserve < 0:
        raise RebalanceExecutionError(
            "REBALANCE_EXEC_PROFILE_INVALID", "Nakit rezervi negatif olamaz."
        )

    try:
        lines: list[ExecutionLine] = []
        buy_gross = Q(0)
        total_fee = Q(0)
        for target in projection.targets:
            delta = number(target.trade_delta)
            if delta == 0:
                lines.append(
                    ExecutionLine(
                        asset=target.asset, side="FLAT",
                        gross_delta="0", fee="0", net_delta="0",
                        qty="0", quantized_qty="0", remainder_qty="0",
                        notional="0", status="SKIPPED_ZERO",
                    )
                )
                continue
            price = quote[target.asset]
            raw_qty = bounded(abs(delta) / price)
            line_fee = bounded(abs(delta) * fee)
            net = bounded(abs(delta) - line_fee)
            units = raw_qty // step
            quantized = bounded(units * step)
            remainder = bounded(raw_qty - quantized)
            notional = bounded(quantized * price)
            if quantized == 0:
                status = "SKIPPED_UNREPRESENTABLE"
            elif notional < minimum:
                status = "SKIPPED_BELOW_MIN"
            else:
                status = "READY"
            if delta > 0:
                buy_gross = bounded(buy_gross + delta)
            total_fee = bounded(total_fee + line_fee)
            lines.append(
                ExecutionLine(
                    asset=target.asset,
                    side="BUY" if delta > 0 else "SELL",
                    gross_delta=exact_text(delta),
                    fee=exact_text(line_fee),
                    net_delta=exact_text(net if delta > 0 else -net),
                    qty=exact_text(raw_qty),
                    quantized_qty=exact_text(quantized),
                    remainder_qty=exact_text(remainder),
                    notional=exact_text(notional),
                    status=status,
                )
            )
        required = bounded(buy_gross + total_fee)
        if required > reserve:
            plan_status = "BLOCKED_INSUFFICIENT_RESERVE"
        elif not any(line.status == "READY" for line in lines):
            plan_status = "EMPTY_NO_TRADABLE_LINE"
        else:
            plan_status = "READY"
        return ExecutionDisclosure(
            plan_id=plan.plan_id,
            status=plan_status,
            total_buy_gross=exact_text(buy_gross),
            total_fee=exact_text(total_fee),
            lines=tuple(lines),
        )
    except ValueError as error:
        raise RebalanceExecutionError(
            "REBALANCE_EXEC_UNREPRESENTABLE",
            "Disclosure exact decimal sözleşmesine sığmıyor.",
        ) from error


def bind_execution_orders(
    disclosure: ExecutionDisclosure, *, order_time_us: int
) -> tuple[RebalanceOrderCandidate, ...]:
    """Bind deterministic MARKET-intent candidates from a READY disclosure."""

    if not isinstance(disclosure, ExecutionDisclosure):
        raise RebalanceExecutionError(
            "REBALANCE_EXEC_DISCLOSURE_INVALID", "Disclosure kaydı geçersiz."
        )
    if type(order_time_us) is not int or order_time_us < 0:
        raise RebalanceExecutionError(
            "REBALANCE_EXEC_TIME_INVALID",
            "Emir zamanı sıfır veya pozitif integer olmalıdır.",
        )
    if disclosure.status == "BLOCKED_INSUFFICIENT_RESERVE":
        raise RebalanceExecutionError(
            "REBALANCE_EXEC_BLOCKED", "Bloke plan aday üretemez."
        )
    if disclosure.status != "READY":
        return ()
    candidates: list[RebalanceOrderCandidate] = []
    for line in disclosure.lines:
        if line.status != "READY":
            continue
        candidate_id = hashlib.sha256(
            json.dumps(
                {
                    "asset": line.asset,
                    "order_time_us": order_time_us,
                    "plan_id": disclosure.plan_id,
                    "qty": line.quantized_qty,
                    "schema": "rebalance-order-candidate-v1",
                    "side": line.side,
                },
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()
        candidates.append(
            RebalanceOrderCandidate(
                candidate_id=candidate_id,
                plan_id=disclosure.plan_id,
                asset=line.asset,
                side=line.side,
                qty=line.quantized_qty,
                order_time_us=order_time_us,
                status="CANDIDATE",
            )
        )
    return tuple(candidates)


def _require_gross_match(plan: RebalancePlan, projection: RebalanceProjection) -> None:
    try:
        deltas = [number(t.trade_delta) for t in projection.targets]
        buy = sum((d for d in deltas if d > 0), Q(0))
        sell = sum((-d for d in deltas if d < 0), Q(0))
        same = (
            plan.valuation_asset == projection.valuation_asset
            and plan.total_equity == projection.total_equity
            and number(plan.gross_buy) == buy
            and number(plan.gross_sell) == sell
        )
    except ValueError:
        same = False
    if not same:
        raise RebalanceExecutionError(
            "REBALANCE_EXEC_PLAN_MISMATCH",
            "Plan ve projection aynı kayda ait değil.",
        )


def _checked_prices(
    prices: tuple[tuple[str, str], ...], projection: RebalanceProjection
) -> dict[str, Q]:
    if not isinstance(prices, tuple):
        raise RebalanceExecutionError(
            "REBALANCE_EXEC_PRICES_INVALID", "Prices tuple olmalıdır."
        )
    quote: dict[str, Q] = {}
    for entry in prices:
        if (
            not isinstance(entry, tuple)
            or len(entry) != 2
            or not all(isinstance(v, str) for v in entry)
        ):
            raise RebalanceExecutionError(
                "REBALANCE_EXEC_PRICE_ENTRY_INVALID",
                "Price asset ve price string tuple olmalıdır.",
            )
        asset, raw = entry
        if _ASSET.fullmatch(asset) is None:
            raise RebalanceExecutionError(
                "REBALANCE_EXEC_PRICE_ENTRY_INVALID", "Asset kimliği geçersiz."
            )
        if asset in quote:
            raise RebalanceExecutionError(
                "REBALANCE_EXEC_PRICE_DUPLICATE",
                "Aynı asset için iki price verilemez.",
            )
        try:
            quote[asset] = positive(raw)
        except ValueError as error:
            raise RebalanceExecutionError(
                "REBALANCE_EXEC_PRICE_INVALID",
                "Price pozitif decimal olmalıdır.",
            ) from error
    needed = {
        t.asset for t in projection.targets if number(t.trade_delta) != 0
    }
    for asset in sorted(needed):
        if asset not in quote:
            raise RebalanceExecutionError(
                "REBALANCE_EXEC_PRICE_MISSING",
                "Sıfır-olmayan her delta için price gerekir.",
            )
    return quote
