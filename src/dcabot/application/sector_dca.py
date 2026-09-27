"""Sector-style DCA bot parameters (3Commas/Bitsgap/Pionex vocabulary) and
their exact translation into an engine `Config`.

The user speaks in quote amounts and percentages; the engine speaks in
fractions, base quantities and venue grids. Everything here is exact
Fraction math; nothing is rounded except where the venue grid demands it
(quantities floor to `qty_step`, the base price ceils to `tick`, exactly as
`/api/preview/full` already does).
"""

from dataclasses import dataclass

from dcabot.domain.config import MAX_COOLDOWN_SECONDS, Config
from dcabot.domain.engine import State, target
from dcabot.domain.math import Position, directional_stop_loss
from dcabot.domain.numbers import Q, align, exact_text, number, round_quantum, text

SECTOR_DCA_FIELDS = frozenset(
    {
        "symbol",
        "base_order",
        "safety_order",
        "max_safety_orders",
        "max_active_safety_orders",
        "price_deviation",
        "safety_order_volume_scale",
        "safety_order_step_scale",
        "take_profit",
        # F09a: optional trailing TP percent; absent/null means fixed TP.
        "trailing_take_profit",
        "stop_loss",
        "direction",
        "cooldown_seconds",
        "min_price",
        "max_price",
        "market_type",
        "leverage",
        "symbols",
        "max_active_deals",
        "combined_take_profit",
    }
)
# Entry gates (G1-kalan/a) and direction default when absent, so every
# stored shape -- pre-G1 (no direction), direction-era (no gates) --
# keeps parsing; any other deviation still fails closed.
_SECTOR_OPTIONAL_FIELDS = frozenset(
    {"direction", "cooldown_seconds", "min_price", "max_price", "market_type", "leverage", "symbols", "max_active_deals", "combined_take_profit", "trailing_take_profit"}
)
_SECTOR_REQUIRED_FIELDS = SECTOR_DCA_FIELDS - _SECTOR_OPTIONAL_FIELDS
_HUNDRED = Q(100)
PERCENT_DISPLAY_PLACES = 4
PRICE_DISPLAY_PLACES = 12


class SectorDcaError(ValueError):
    """Raised when sector parameters cannot become a valid engine config."""

    def __init__(self, code: str, message: str, *, field: str | None = None) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.field = field


@dataclass(frozen=True, slots=True)
class SectorDcaParams:
    symbol: str
    base_order: Q
    safety_order: Q
    max_safety_orders: int
    max_active_safety_orders: int | None
    price_deviation: Q
    safety_order_volume_scale: Q
    safety_order_step_scale: Q
    take_profit: Q
    trailing_take_profit: Q | None
    stop_loss: Q | None
    direction: str
    cooldown_seconds: int
    min_price: Q | None
    max_price: Q | None
    market_type: str
    leverage: int
    symbols: tuple[str, ...]
    max_active_deals: int
    combined_take_profit: Q | None


@dataclass(frozen=True, slots=True)
class SymbolRules:
    symbol: str
    status: str
    base_asset: str
    quote_asset: str
    tick: str
    qty_step: str
    min_qty: str
    min_notional: str


def bot_unsupported_reason(rules: "SymbolRules") -> str | None:
    """Why a DCA bot cannot run on this symbol, or None if it can."""

    if rules.status != "TRADING":
        return "NOT_TRADING"
    if rules.quote_asset != "USDT" or rules.symbol != rules.base_asset + "USDT":
        return "QUOTE_UNSUPPORTED"
    return None


def _decimal(raw: dict, name: str, *, low: Q, high: Q | None, low_inclusive: bool = False) -> Q:
    value = raw.get(name)
    try:
        parsed = number(value)
    except (TypeError, ValueError) as exc:
        raise SectorDcaError("SECTOR_FIELD_INVALID", "Sayı ondalık metin olmalıdır.", field=name) from exc
    too_low = parsed < low if low_inclusive else parsed <= low
    if too_low or (high is not None and parsed >= high):
        raise SectorDcaError("SECTOR_FIELD_OUT_OF_RANGE", "Değer izin verilen aralığın dışında.", field=name)
    return parsed


def _sector_fields_accepted(keys: set[str]) -> bool:
    return _SECTOR_REQUIRED_FIELDS <= keys <= SECTOR_DCA_FIELDS


def parse_sector_dca(raw: object) -> SectorDcaParams:
    """Strictly parse the wizard payload; unknown or missing keys fail closed."""

    if not isinstance(raw, dict) or not _sector_fields_accepted(set(raw)):
        raise SectorDcaError("SECTOR_FIELDS_INVALID", "Strateji alanları beklenen kümeyle eşleşmiyor.")
    symbol = raw["symbol"]
    if not isinstance(symbol, str) or not symbol.isascii() or not symbol.isalnum() or not symbol.isupper() or not 5 <= len(symbol) <= 20:
        raise SectorDcaError("SECTOR_FIELD_INVALID", "Sembol büyük harf alfanumerik olmalıdır.", field="symbol")
    count = raw["max_safety_orders"]
    if type(count) is not int or not 0 <= count <= 50:
        raise SectorDcaError("SECTOR_FIELD_OUT_OF_RANGE", "Max safety orders 0..50 olmalıdır.", field="max_safety_orders")
    active = raw["max_active_safety_orders"]
    if active is not None and (type(active) is not int or not 1 <= active <= max(count, 1) or count == 0):
        raise SectorDcaError(
            "SECTOR_FIELD_OUT_OF_RANGE",
            "Max active safety orders boş ya da 1..max safety orders olmalıdır.",
            field="max_active_safety_orders",
        )
    stop_loss_raw = raw["stop_loss"]
    direction = raw.get("direction", "LONG")
    if direction not in ("LONG", "SHORT"):
        raise SectorDcaError("SECTOR_FIELD_INVALID", "Yön LONG ya da SHORT olmalıdır.", field="direction")
    cooldown = raw.get("cooldown_seconds", 0)
    if type(cooldown) is not int or not 0 <= cooldown <= MAX_COOLDOWN_SECONDS:
        raise SectorDcaError(
            "SECTOR_FIELD_OUT_OF_RANGE", "Cooldown 0..31536000 saniye olmalıdır.", field="cooldown_seconds"
        )
    min_price = None if raw.get("min_price") is None else _decimal(raw, "min_price", low=Q(0), high=None)
    max_price = None if raw.get("max_price") is None else _decimal(raw, "max_price", low=Q(0), high=None)
    if min_price is not None and max_price is not None and min_price > max_price:
        raise SectorDcaError("SECTOR_FIELD_OUT_OF_RANGE", "Min fiyat max fiyatı aşamaz.", field="min_price")
    market_type = raw.get("market_type", "SPOT")
    if market_type not in ("SPOT", "FUTURES"):
        raise SectorDcaError("SECTOR_FIELD_INVALID", "Pazar SPOT ya da FUTURES olmalıdır.", field="market_type")
    leverage_raw = raw.get("leverage")
    if leverage_raw is None:
        leverage = 3 if market_type == "FUTURES" else 1
    elif type(leverage_raw) is not int or not 1 <= leverage_raw <= 10:
        raise SectorDcaError("SECTOR_FIELD_OUT_OF_RANGE", "Kaldıraç 1..10 olmalıdır.", field="leverage")
    elif market_type == "SPOT" and leverage_raw != 1:
        raise SectorDcaError("SECTOR_FIELD_OUT_OF_RANGE", "Spot piyasada kaldıraç 1 olmalıdır.", field="leverage")
    else:
        leverage = leverage_raw
    symbols_raw = raw.get("symbols")
    if symbols_raw is None:
        symbols: tuple[str, ...] = (symbol,)
    else:
        if (
            not isinstance(symbols_raw, list)
            or not 1 <= len(symbols_raw) <= 10
            or any(
                not isinstance(item, str)
                or not item.isascii()
                or not item.isalnum()
                or not item.isupper()
                or not 5 <= len(item) <= 20
                for item in symbols_raw
            )
            or len(set(symbols_raw)) != len(symbols_raw)
            or symbols_raw[0] != symbol
        ):
            raise SectorDcaError(
                "SECTOR_FIELD_OUT_OF_RANGE",
                "symbols benzersiz 1..10 parite olmalı, ilki symbol ile aynı.",
                field="symbols",
            )
        symbols = tuple(symbols_raw)
    max_active_raw = raw.get("max_active_deals")
    if max_active_raw is None:
        max_active_deals = 1
    elif isinstance(max_active_raw, bool) or not isinstance(max_active_raw, int) or not 1 <= max_active_raw <= 10:
        raise SectorDcaError(
            "SECTOR_FIELD_OUT_OF_RANGE", "Max active deals 1..10 olmalıdır.", field="max_active_deals"
        )
    else:
        max_active_deals = max_active_raw
    combined_raw = raw.get("combined_take_profit")
    combined_take_profit = None if combined_raw is None else _decimal(raw, "combined_take_profit", low=Q(0), high=_HUNDRED)
    trailing_raw = raw.get("trailing_take_profit")
    trailing_take_profit = None if trailing_raw is None else _decimal(raw, "trailing_take_profit", low=Q(0), high=_HUNDRED)
    # F09a: trailing arms off the per-deal TP target, which combo bots
    # suppress (take_profit None) -- the pair fails closed here with a
    # named field instead of dying deep inside Config.parse.
    if trailing_take_profit is not None and combined_take_profit is not None:
        raise SectorDcaError(
            "SECTOR_FIELD_OUT_OF_RANGE",
            "Trailing take-profit kombine kar hedefiyle birlikte kullanılamaz.",
            field="trailing_take_profit",
        )
    return SectorDcaParams(
        symbol=symbol,
        base_order=_decimal(raw, "base_order", low=Q(0), high=Q(10**9)),
        safety_order=_decimal(raw, "safety_order", low=Q(0), high=Q(10**9)),
        max_safety_orders=count,
        max_active_safety_orders=active,
        price_deviation=_decimal(raw, "price_deviation", low=Q(0), high=_HUNDRED),
        safety_order_volume_scale=_decimal(raw, "safety_order_volume_scale", low=Q(0), high=Q(11)),
        safety_order_step_scale=_decimal(raw, "safety_order_step_scale", low=Q(0), high=Q(11)),
        take_profit=_decimal(raw, "take_profit", low=Q(0), high=_HUNDRED),
        trailing_take_profit=trailing_take_profit,
        stop_loss=None if stop_loss_raw is None else _decimal(raw, "stop_loss", low=Q(0), high=_HUNDRED),
        direction=direction,
        cooldown_seconds=cooldown,
        min_price=min_price,
        max_price=max_price,
        market_type=market_type,
        leverage=leverage,
        symbols=symbols,
        max_active_deals=max_active_deals,
        combined_take_profit=combined_take_profit,
    )


def max_deal_quote_cost(params: SectorDcaParams, *, fee_rate: Q, fee_quantum: Q) -> Q:
    """Price-free upper bound of one deal's quote spend (margin + fees).

    QUOTE sizing floors every order's quantity, so each fill's notional
    never exceeds its quote sizing at any price; fees ceil per fill.
    Futures divides the subtotal by leverage, rounding UP to the money
    quantum (conservative, like `summarize_deal_plan`).
    """

    if fee_rate < 0 or fee_quantum <= 0:
        raise SectorDcaError("SECTOR_FEE_INVALID", "Fee oranı/kuantumu geçersiz.")
    orders = [params.base_order] + [
        params.safety_order * params.safety_order_volume_scale**index
        for index in range(params.max_safety_orders)
    ]
    subtotal = sum(orders, Q(0))
    fees = sum(-(-(order * fee_rate) // fee_quantum) * fee_quantum for order in orders)
    margin = subtotal / params.leverage
    if params.leverage != 1:
        margin = align(margin, fee_quantum, up=True)
    return margin + fees


def derive_deal_config(
    params: SectorDcaParams,
    *,
    rules: SymbolRules,
    reference_price: Q,
    budget: Q,
    template: dict,
) -> dict:
    """Return a raw engine config for a sector DCA bot.

    Base and safety orders both use QUOTE sizing: every order's quantity is
    its quote amount divided by that order's own price, floored to the grid,
    so the config stays valid across deals at any price. `reference_price`
    only validates venue minimums now. Fees, slippage and drawdown guard come
    from `template` (the canonical paper config), never from the client.
    """

    if rules.symbol != params.symbol:
        raise SectorDcaError("SECTOR_RULES_MISMATCH", "Borsa kuralları başka bir sembole ait.")
    reason = bot_unsupported_reason(rules)
    if reason == "NOT_TRADING":
        raise SectorDcaError("SECTOR_SYMBOL_NOT_TRADING", "Bu parite şu an işlemde değil.", field="symbol")
    if reason == "QUOTE_UNSUPPORTED":
        raise SectorDcaError(
            "SECTOR_QUOTE_UNSUPPORTED", "Şimdilik yalnız USDT pariteleri destekleniyor.", field="symbol"
        )
    if reference_price <= 0:
        raise SectorDcaError("SECTOR_PRICE_INVALID", "Referans fiyat pozitif olmalıdır.")
    if budget <= 0:
        raise SectorDcaError("SECTOR_FIELD_OUT_OF_RANGE", "Bütçe pozitif olmalıdır.", field="budget")
    tick = number(rules.tick)
    base_price = align(reference_price, tick, up=True)
    raw = dict(template)
    raw.update(
        {
            "symbol": params.symbol,
            "base_asset": rules.base_asset,
            "quote_asset": "USDT",
            "base_qty": exact_text(params.base_order),
            "base_sizing": "QUOTE",
            "safety_qty": exact_text(params.safety_order),
            "safety_sizing": "QUOTE",
            "safety_count": params.max_safety_orders,
            "max_active_safety_orders": params.max_active_safety_orders,
            "deviation": exact_text(params.price_deviation / _HUNDRED),
            "step_multiplier": exact_text(params.safety_order_step_scale),
            "volume_multiplier": exact_text(params.safety_order_volume_scale),
            "tick": rules.tick,
            "qty_step": rules.qty_step,
            "min_qty": rules.min_qty,
            "min_notional": rules.min_notional,
            "initial_equity": exact_text(budget),
            # Futures paper: the notional ceiling is the margin-implied
            # multiple of the budget; spot keeps budget*1 byte-identical.
            "max_entry_notional": exact_text(budget * params.leverage),
            "minimum_equity": "0",
            # No hidden forced exit: sector DCA bots (3Commas/Bitsgap/Pionex)
            # close a deal only on take profit or the user's own stop loss.
            # The template's 25% equity-drawdown halt would liquidate an
            # ordinary DCA drawdown behind the user's back.
            "max_drawdown": "0.99",
            "leverage": exact_text(Q(params.leverage)),
            "direction": params.direction,
            "margin_mode": "ISOLATED",
            "take_profit": None if params.combined_take_profit is not None else exact_text(params.take_profit / _HUNDRED),
            # F09a: percent in, fraction out; None keeps fixed-TP behavior.
            "trailing_take_profit_rate": None if params.trailing_take_profit is None else exact_text(params.trailing_take_profit / _HUNDRED),
            "target_mode": "GROSS_PRICE_RETURN",
            "take_profit_ladder": None,
            "stop_loss_rate": None if params.stop_loss is None else exact_text(params.stop_loss / _HUNDRED),
            "stop_loss_confirmation_bars": None if params.stop_loss is None else 1,
            "cooldown_seconds": params.cooldown_seconds,
            "min_entry_price": None if params.min_price is None else exact_text(params.min_price),
            "max_entry_price": None if params.max_price is None else exact_text(params.max_price),
        }
    )
    try:
        config = Config.parse(raw)
    except ValueError as exc:
        raise SectorDcaError("SECTOR_CONFIG_INVALID", _config_message(exc)) from exc
    base_qty = config.base_order_qty(base_price)
    try:
        if base_qty <= 0:
            raise ValueError
        config.check_order(base_qty, base_price)
    except ValueError as exc:
        raise SectorDcaError(
            "SECTOR_BASE_ORDER_TOO_SMALL",
            f"Base order borsa minimumunun altında (en az {rules.min_notional} USDT).",
            field="base_order",
        ) from exc
    try:
        config.plan(base_price)
    except ValueError as exc:
        raise SectorDcaError("SECTOR_CONFIG_INVALID", _config_message(exc)) from exc
    return raw


def _config_message(exc: ValueError) -> str:
    detail = str(exc)
    if "minimum" in detail or "collapsed" in detail:
        return "Safety order borsa minimumunun altında ya da kademe çok sık; tutarı ya da sapmayı artırın."
    if "grid" in detail:
        return "Değerler borsanın fiyat/miktar adımına oturmuyor."
    return "Parametreler geçerli bir bot oluşturmuyor."


def summarize_deal_plan(raw_config: dict, reference_price: Q) -> dict:
    """Wizard summary in sector terms, all exact text from engine functions."""

    config = Config.parse(raw_config)
    short = config.direction == "SHORT"
    base_price = align(reference_price, config.tick, up=not short)
    levels = config.plan(base_price)
    base_qty = config.base_order_qty(base_price)
    base_amount = base_qty * base_price
    total_qty = base_qty + sum((level.qty for level in levels), Q(0))
    orders_total = base_amount + sum((level.qty * level.price for level in levels), Q(0))
    # The engine admits an order only if its notional plus its fee fits the
    # free cash, so a budget equal to the order total alone would reject the
    # last safety order. Fees use the simulator's own per-fill rounding.
    fees = sum(
        (
            round_quantum(notional * config.fee_rate, config.fee_quantum)
            for notional in [base_amount, *(level.qty * level.price for level in levels)]
        ),
        Q(0),
    )
    # Futures paper (G1-kalan/b): the requirement is the isolated margin,
    # not the notional. The division is generally non-terminating, so the
    # margin rounds UP to the money quantum (conservative); spot divides
    # by one and keeps its exact bytes.
    leverage = config.leverage
    margin = orders_total / leverage
    if leverage != 1:
        margin = align(margin, config.fee_quantum, up=True)
    required = margin + fees
    state = State(
        position=Position(base_qty, base_amount),
        anchor=base_price,
        mark=base_price,
    )
    take_profit_price = target(state, config)
    last_price = levels[-1].price if levels else base_price
    if short:
        coverage = (last_price - base_price) / base_price * _HUNDRED
    else:
        coverage = (base_price - last_price) / base_price * _HUNDRED
    return {
        "symbol": config.symbol,
        "base_price": exact_text(base_price),
        "base_order": {"price": exact_text(base_price), "qty": exact_text(base_qty), "amount": exact_text(base_amount)},
        "safety_orders": [
            {
                "index": level.index,
                "price": exact_text(level.price),
                "qty": exact_text(level.qty),
                "amount": exact_text(level.qty * level.price),
                "deviation_percent": text(
                    (level.price - base_price) / base_price * _HUNDRED
                    if short
                    else (base_price - level.price) / base_price * _HUNDRED,
                    PERCENT_DISPLAY_PLACES,
                ),
            }
            for level in levels
        ],
        "required_funds": exact_text(required),
        "orders_total": exact_text(orders_total),
        "estimated_fees": exact_text(fees),
        "budget": exact_text(config.initial_equity),
        "within_budget": required <= config.initial_equity,
        "price_coverage_percent": text(coverage, PERCENT_DISPLAY_PLACES),
        "average_price_all_filled": text(required / total_qty, PRICE_DISPLAY_PLACES),
        "take_profit_price": None if take_profit_price is None else exact_text(take_profit_price),
        "stop_loss_price_initial": (
            None
            if config.stop_loss_rate is None
            else exact_text(directional_stop_loss(config.direction_enum, base_price, config.stop_loss_rate))
        ),
    }
