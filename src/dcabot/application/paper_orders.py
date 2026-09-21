"""Simulated orders and fills inside one credential-free paper session.

Fill policy (explicit, v1): every fill cites one ACCEPTED source observation
and executes exactly at that observation's price. MARKET fills unconditionally;
LIMIT BUY needs observation price at or below the limit, LIMIT SELL at or
above. No spread, fee, margin, or short selling: BUY needs cash, SELL needs a
long position. Placement is shape-only; economic authority lives in the fill.
"""

from dataclasses import dataclass, replace
import hashlib
import json
import re

from dcabot.application.paper_trading_gate import PaperSession
from dcabot.data_adapters.public_feed import PublicObservation
from dcabot.domain.numbers import Q, bounded, exact_text, number, positive


_ORDER_ID = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
_SIDES = frozenset({"BUY", "SELL"})
_TYPES = frozenset({"MARKET", "LIMIT"})
_OPEN = frozenset({"SIMULATED_NEW", "SIMULATED_PARTIAL"})


class PaperOrderError(ValueError):
    """Raised when a simulated order, fill, or cancel cannot proceed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class PaperOrder:
    """One immutable simulated order; fills only via cited observations."""

    client_order_id: str
    symbol: str
    side: str
    order_type: str
    qty: str
    limit_price: str | None
    filled_qty: str
    status: str
    order_time_us: int


@dataclass(frozen=True, slots=True)
class PaperPosition:
    """Long-only base quantity held for one symbol in a paper session."""

    symbol: str
    qty: str


@dataclass(frozen=True, slots=True)
class PaperFill:
    """One immutable simulated fill bound to a source observation event."""

    fill_id: str
    client_order_id: str
    event_id: str
    symbol: str
    side: str
    price: str
    qty: str
    notional: str
    fill_time_us: int


def place_paper_order(
    *,
    session: PaperSession,
    symbol: str,
    side: str,
    order_type: str,
    qty: str,
    limit_price: str | None,
    client_order_id: str,
    order_time_us: int,
) -> tuple[PaperSession, PaperOrder, str]:
    """Place a shape-checked simulated order; returns NEW or DUPLICATE."""

    _require_session(session)
    if symbol not in session.symbols:
        raise PaperOrderError(
            "PAPER_SYMBOL_NOT_ALLOWED", "Symbol bu paper sessionda yok."
        )
    if side not in _SIDES:
        raise PaperOrderError("PAPER_SIDE_INVALID", "Side yalnız BUY veya SELL.")
    if order_type not in _TYPES:
        raise PaperOrderError("PAPER_TYPE_INVALID", "Type yalnız MARKET veya LIMIT.")
    try:
        amount = positive(qty)
    except ValueError as error:
        raise PaperOrderError(
            "PAPER_QTY_INVALID", "Qty pozitif decimal string olmalıdır."
        ) from error
    limit: Q | None = None
    if order_type == "MARKET":
        if limit_price is not None:
            raise PaperOrderError(
                "PAPER_PRICE_INVALID", "MARKET emir limit price taşıyamaz."
            )
    else:
        if not isinstance(limit_price, str):
            raise PaperOrderError(
                "PAPER_PRICE_INVALID", "LIMIT emir price string gerektirir."
            )
        try:
            limit = positive(limit_price)
        except ValueError as error:
            raise PaperOrderError(
                "PAPER_PRICE_INVALID", "Limit price pozitif decimal olmalıdır."
            ) from error
    if not isinstance(client_order_id, str) or _ORDER_ID.fullmatch(client_order_id) is None:
        raise PaperOrderError(
            "PAPER_ORDER_ID_INVALID", "Client order id kimliği geçersiz."
        )
    _require_time(order_time_us, "PAPER_TIME_INVALID")

    orders = _orders(session)
    for prior in orders:
        if prior.client_order_id != client_order_id:
            continue
        if (
            prior.symbol == symbol
            and prior.side == side
            and prior.order_type == order_type
            and number(prior.qty) == amount
            and (prior.limit_price is None) == (limit is None)
            and (limit is None or number(prior.limit_price) == limit)
            and prior.order_time_us == order_time_us
        ):
            return session, prior, "DUPLICATE"
        raise PaperOrderError(
            "PAPER_ORDER_CONFLICT",
            "Aynı client order id farklı parametreyle kullanılamaz.",
        )

    try:
        order = PaperOrder(
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            qty=exact_text(amount),
            limit_price=None if limit is None else exact_text(limit),
            filled_qty="0",
            status="SIMULATED_NEW",
            order_time_us=order_time_us,
        )
    except ValueError as error:
        raise PaperOrderError(
            "PAPER_ORDER_UNREPRESENTABLE",
            "Emir exact decimal sözleşmesine sığmıyor.",
        ) from error
    return replace(session, orders=(*session.orders, order)), order, "NEW"


def fill_paper_order(
    *,
    session: PaperSession,
    client_order_id: str,
    observation: PublicObservation,
    fill_qty: str,
    fill_time_us: int,
) -> tuple[PaperSession, PaperFill, str]:
    """Fill from one cited observation at exactly its price; FILLED/DUPLICATE."""

    _require_session(session)
    if not isinstance(observation, PublicObservation):
        raise PaperOrderError("PAPER_OBSERVATION_INVALID", "Observation geçersiz.")
    _require_time(fill_time_us, "PAPER_FILL_TIME_INVALID")
    if observation.event_time_us > fill_time_us:
        raise PaperOrderError(
            "PAPER_FILL_TIME_INVALID",
            "Fill kaynağı olan eventten önce olamaz.",
        )
    try:
        amount = positive(fill_qty)
    except ValueError as error:
        raise PaperOrderError(
            "PAPER_FILL_QTY_INVALID", "Fill qty pozitif decimal olmalıdır."
        ) from error

    orders = _orders(session)
    index = next(
        (i for i, o in enumerate(orders) if o.client_order_id == client_order_id),
        None,
    )
    if index is None:
        raise PaperOrderError("PAPER_ORDER_UNKNOWN", "Emir bu sessionda yok.")
    order = orders[index]
    fill_id = hashlib.sha256(
        json.dumps(
            {
                "client_order_id": client_order_id,
                "event_id": observation.event_id,
                "fill_qty": exact_text(amount),
                "fill_time_us": fill_time_us,
                "session_id": session.session_id,
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    fills = _fills(session)
    for prior in fills:
        if prior.fill_id == fill_id:
            return session, prior, "DUPLICATE"
    if order.status not in _OPEN:
        raise PaperOrderError("PAPER_ORDER_CLOSED", "Emir artık doldurulamaz.")
    if observation.symbol != order.symbol:
        raise PaperOrderError(
            "PAPER_OBSERVATION_MISMATCH",
            "Observation emir symbolüyle eşleşmiyor.",
        )
    if fill_time_us < order.order_time_us:
        raise PaperOrderError(
            "PAPER_FILL_TIME_INVALID",
            "Fill emir zamanından önce olamaz.",
        )
    try:
        price = number(observation.price)
        total = number(order.qty)
        filled = number(order.filled_qty)
    except ValueError as error:
        raise PaperOrderError(
            "PAPER_ORDER_STATE_INVALID", "Emir fiyat/miktar durumu geçersiz."
        ) from error
    if amount > total - filled:
        raise PaperOrderError(
            "PAPER_FILL_QTY_INVALID", "Fill kalan miktarı aşamaz."
        )
    if order.order_type == "LIMIT":
        assert order.limit_price is not None
        limit = number(order.limit_price)
        touched = price <= limit if order.side == "BUY" else price >= limit
        if not touched:
            raise PaperOrderError(
                "PAPER_FILL_PRICE_NOT_TOUCHED",
                "Observation fiyatı limite değmedi.",
            )

    try:
        notional = bounded(price * amount)
        cash = number(_cash(session))
        positions = {p.symbol: number(p.qty) for p in _positions(session)}
        held = positions.get(order.symbol, Q(0))
        if order.side == "BUY":
            if notional > cash:
                raise PaperOrderError(
                    "PAPER_INSUFFICIENT_CASH", "Simüle nakit yetersiz."
                )
            cash = bounded(cash - notional)
            positions[order.symbol] = bounded(held + amount)
        else:
            if amount > held:
                raise PaperOrderError(
                    "PAPER_INSUFFICIENT_POSITION", "Simüle pozisyon yetersiz."
                )
            cash = bounded(cash + notional)
            remainder = bounded(held - amount)
            if remainder == 0:
                positions.pop(order.symbol, None)
            else:
                positions[order.symbol] = remainder
        new_filled = bounded(filled + amount)
        fill = PaperFill(
            fill_id=fill_id,
            client_order_id=client_order_id,
            event_id=observation.event_id,
            symbol=order.symbol,
            side=order.side,
            price=exact_text(price),
            qty=exact_text(amount),
            notional=exact_text(notional),
            fill_time_us=fill_time_us,
        )
        updated = replace(
            order,
            filled_qty=exact_text(new_filled),
            status="SIMULATED_FILLED" if new_filled == total else "SIMULATED_PARTIAL",
        )
        new_orders = list(orders)
        new_orders[index] = updated
        return (
            replace(
                session,
                cash=exact_text(cash),
                positions=tuple(
                    PaperPosition(symbol=s, qty=exact_text(q))
                    for s, q in sorted(positions.items())
                ),
                orders=tuple(new_orders),
                fills=(*session.fills, fill),
            ),
            fill,
            "FILLED",
        )
    except PaperOrderError:
        raise
    except ValueError as error:
        raise PaperOrderError(
            "PAPER_FILL_UNREPRESENTABLE",
            "Fill exact decimal sözleşmesine sığmıyor.",
        ) from error


def cancel_paper_order(
    *, session: PaperSession, client_order_id: str, cancel_time_us: int
) -> tuple[PaperSession, PaperOrder]:
    """Cancel an open simulated order; filled/canceled orders stay terminal."""

    _require_session(session)
    _require_time(cancel_time_us, "PAPER_TIME_INVALID")
    orders = _orders(session)
    index = next(
        (i for i, o in enumerate(orders) if o.client_order_id == client_order_id),
        None,
    )
    if index is None:
        raise PaperOrderError("PAPER_ORDER_UNKNOWN", "Emir bu sessionda yok.")
    order = orders[index]
    if order.status not in _OPEN:
        raise PaperOrderError("PAPER_ORDER_CLOSED", "Emir zaten terminal.")
    if cancel_time_us < order.order_time_us:
        raise PaperOrderError(
            "PAPER_TIME_INVALID", "Cancel emir zamanından önce olamaz."
        )
    updated = replace(order, status="SIMULATED_CANCELED")
    new_orders = list(orders)
    new_orders[index] = updated
    return replace(session, orders=tuple(new_orders)), updated


def _require_session(session: PaperSession) -> None:
    if not isinstance(session, PaperSession) or session.status != "PAPER_ACTIVE":
        raise PaperOrderError("PAPER_SESSION_INVALID", "Paper session geçersiz.")


def _require_time(value: int, code: str) -> None:
    if type(value) is not int or value < 0:
        raise PaperOrderError(code, "Zaman sıfır veya pozitif integer olmalıdır.")


def _cash(session: PaperSession) -> str:
    if not isinstance(session.cash, str):
        raise PaperOrderError("PAPER_SESSION_STATE_INVALID", "Session nakdi geçersiz.")
    return session.cash


def _orders(session: PaperSession) -> tuple[PaperOrder, ...]:
    if not isinstance(session.orders, tuple) or any(
        not isinstance(o, PaperOrder) for o in session.orders
    ):
        raise PaperOrderError("PAPER_SESSION_STATE_INVALID", "Session emirleri geçersiz.")
    return session.orders  # type: ignore[return-value]


def _positions(session: PaperSession) -> tuple[PaperPosition, ...]:
    if not isinstance(session.positions, tuple) or any(
        not isinstance(p, PaperPosition) for p in session.positions
    ):
        raise PaperOrderError(
            "PAPER_SESSION_STATE_INVALID", "Session pozisyonları geçersiz."
        )
    return session.positions  # type: ignore[return-value]


def _fills(session: PaperSession) -> tuple[PaperFill, ...]:
    if not isinstance(session.fills, tuple) or any(
        not isinstance(f, PaperFill) for f in session.fills
    ):
        raise PaperOrderError("PAPER_SESSION_STATE_INVALID", "Session filleri geçersiz.")
    return session.fills  # type: ignore[return-value]
