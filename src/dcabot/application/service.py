"""Shared offline application path; replay uses the same reducer and journal."""

from fractions import Fraction as Q
from dcabot.domain.config import Config
from dcabot.domain.engine import apply, decision, report, identifier
from dcabot.domain.numbers import positive, text, exact_text, align, round_quantum
from dcabot.ports.journal import Journal


def preview(raw: dict, anchor: str) -> dict:
    c = Config.parse(raw)
    p = positive(anchor)
    base_price = align(p, c.tick, up=True)
    c.check_order(c.base_qty, base_price)
    levels = c.plan(base_price)
    gross = c.base_qty * base_price + sum((x.qty * x.price for x in levels), Q(0))
    return {
        "symbol": c.symbol,
        "base_asset": c.base_asset,
        "quote_asset": c.quote_asset,
        "anchor": text(base_price),
        "base_notional": text(c.base_qty * base_price),
        "planned_gross_notional": text(gross),
        "estimated_initial_margin": text(gross / c.leverage),
        "policy_required_collateral": None,
        "within_gross_entry_cap": gross <= c.max_entry_notional,
        "levels": [
            {
                "index": x.index,
                "price": text(x.price),
                "qty": text(x.qty),
                "notional": text(x.price * x.qty),
            }
            for x in levels
        ],
        "assumption": "Theoretical full fills at plan prices; no venue collateral guarantee",
    }


def notional(raw: dict) -> dict:
    fields = {"symbol", "base_asset", "quote_asset", "price", "qty", "qty_asset"}
    if (
        not isinstance(raw, dict)
        or set(raw) != fields
        or raw["quote_asset"] != "USDT"
        or raw["qty_asset"] != raw["base_asset"]
        or raw["symbol"] != raw["base_asset"] + raw["quote_asset"]
    ):
        raise ValueError("Explicit, matching BASE/USDT units are required")
    p = positive(raw["price"])
    q = positive(raw["qty"])
    return {
        "symbol": raw["symbol"],
        "notional": text(p * q),
        "asset": raw["quote_asset"],
    }


def replay_tick(store: Journal, tick_id: str, price: str) -> bool:
    identifier(tick_id)
    if len(tick_id) > 70:
        raise ValueError("Tick ID supports at most 70 characters")
    positive(price)
    c = store.config

    def build(state, emit):
        state = emit({"type": "MARK", "price": price})
        action = decision(state, c)
        if action is None:
            return
        role, qty = action
        buy = role not in ("EXIT", "STOP")
        fill_price = align(
            state.mark * (1 + c.slippage if buy else 1 - c.slippage), c.tick, up=buy
        )
        oid = f"{tick_id}:order"
        intent = {
            "type": "INTENT",
            "order_id": oid,
            "role": role,
            "qty": exact_text(qty),
            "limit_price": exact_text(fill_price),
        }
        # A policy-denied action leaves the mark/risk observation durable, not a partial order.
        try:
            apply(state, intent, c)
        except ValueError as exc:
            emit({"type": "POLICY_REJECTION", "reason": str(exc)})
            return
        emit(intent)
        fee = round_quantum(qty * fill_price * c.fee_rate, c.fee_quantum)
        emit(
            {
                "type": "FILL",
                "execution_id": f"{tick_id}:trade",
                "order_id": oid,
                "side": "BUY" if buy else "SELL",
                "qty": exact_text(qty),
                "price": exact_text(fill_price),
                "fee": exact_text(fee),
                "fee_asset": c.quote_asset,
            }
        )
        emit(
            {
                "type": "ORDER_FINAL",
                "order_id": oid,
                "status": "FILLED",
                "filled_qty": exact_text(qty),
                "coverage_complete": True,
            }
        )

    # One synthetic tick and its effects are atomic; interruption cannot leave a half-applied tick.
    return store.transact(tick_id, {"type": "REPLAY_TICK", "price": price}, build)


def replay(store: Journal, ticks: list[dict]) -> dict:
    if not isinstance(ticks, list) or len(ticks) > 2500:
        raise ValueError("Replay expects at most 2500 ordered ticks")
    ids = []
    for tick in ticks:
        if not isinstance(tick, dict) or set(tick) != {"id", "price"}:
            raise ValueError("Each tick needs id and price")
        identifier(tick["id"])
        positive(tick["price"])
        ids.append(tick["id"])
    if len(set(ids)) != len(ids):
        raise ValueError("Tick IDs must be unique within the input list")
    # Input list order is the observation order. Ticks are not OHLC bars or real exchange trades.
    for tick in ticks:
        replay_tick(store, tick["id"], tick["price"])
    result = report(store.load(), store.config)
    result["audit"] = store.audit()
    result["simulation"] = (
        "SYNTHETIC_TICKS_IMMEDIATE_FULL_FILL; one action per tick; configured slippage/fee"
    )
    return result
