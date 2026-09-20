"""Offline Futures DCA plan projection for the selected safe profile."""

from dataclasses import dataclass
from fractions import Fraction as Q

from dcabot.application.instrument_filters import (
    InstrumentFilterError,
    InstrumentFilterProfile,
    ValidatedOrderCandidate,
    validate_order_candidate,
)
from dcabot.application.ladder_conservation import (
    LadderConservation,
    LadderConservationError,
    validate_ladder_allocations,
)
from dcabot.domain.numbers import align, bounded, exact_text, number, positive


class FuturesDcaPlanError(ValueError):
    """Raised when a Futures DCA plan cannot be represented exactly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FuturesDcaProfile:
    """The selected v1 Futures profile; no live venue capability is implied."""

    venue: str = "BINANCE"
    product_family: str = "USD_M"
    settlement_asset: str = "USDT"
    margin_asset: str = "USDT"
    contract_type: str = "PERPETUAL"
    position_mode: str = "ONE_WAY"
    margin_mode: str = "ISOLATED"
    leverage: str = "1"

    def __post_init__(self) -> None:
        if (
            self.venue,
            self.product_family,
            self.settlement_asset,
            self.margin_asset,
            self.contract_type,
            self.position_mode,
            self.margin_mode,
        ) != ("BINANCE", "USD_M", "USDT", "USDT", "PERPETUAL", "ONE_WAY", "ISOLATED"):
            raise FuturesDcaPlanError("FUTURES_DCA_PROFILE_UNSUPPORTED", "Yalnız seçilen USD_M/USDT/one-way/isolated profil desteklenir.")
        try:
            leverage = positive(self.leverage)
        except ValueError as error:
            raise FuturesDcaPlanError("FUTURES_DCA_LEVERAGE_INVALID", "Leverage pozitif exact decimal olmalıdır.") from error
        object.__setattr__(self, "leverage", exact_text(leverage))


@dataclass(frozen=True, slots=True)
class FuturesDcaLevel:
    """One safety order candidate before venue acceptance."""

    index: int
    price: str
    quantity: str
    quote_allocation: str


@dataclass(frozen=True, slots=True)
class FuturesDcaProjection:
    """Exact base/safety capital preview without order authority."""

    profile: FuturesDcaProfile
    price_tick: str
    quantity_step: str
    side: str
    anchor_price: str
    base_quantity: str
    base_quote_allocation: str
    levels: tuple[FuturesDcaLevel, ...]
    required_capital: str
    max_covered_deviation: str
    last_safety_price: str | None


@dataclass(frozen=True, slots=True)
class FuturesDcaCustomLevelSpec:
    """One per-safety-order override before quantity/venue quantization."""

    index: int
    cumulative_deviation: str
    allocation: str


@dataclass(frozen=True, slots=True)
class FuturesDcaCustomLevel:
    """One exact custom level with an explicit allocation unit."""

    index: int
    cumulative_deviation: str
    price: str
    allocation: str


@dataclass(frozen=True, slots=True)
class FuturesDcaCustomProjection:
    """Read-only custom ladder projection without order or venue authority."""

    profile: FuturesDcaProfile
    side: str
    anchor_price: str
    price_tick: str
    allocation_unit: str
    levels: tuple[FuturesDcaCustomLevel, ...]
    conservation: LadderConservation


@dataclass(frozen=True, slots=True)
class FuturesDcaCustomCandidateLevel:
    """One post-quantization candidate with requested and actual allocation."""

    index: int
    price: str
    requested_allocation: str
    quantity: str
    actual_allocation: str
    quote_notional: str


@dataclass(frozen=True, slots=True)
class FuturesDcaCustomCandidateProjection:
    """Custom ladder candidates accepted by local instrument filters only."""

    ladder: FuturesDcaCustomProjection
    instrument: InstrumentFilterProfile
    levels: tuple[FuturesDcaCustomCandidateLevel, ...]
    conservation: LadderConservation


def project_futures_dca_plan(
    *,
    side: str,
    anchor_price: str,
    base_amount: str,
    base_sizing: str,
    safety_amount: str,
    safety_sizing: str,
    safety_count: int,
    deviation: str,
    step_multiplier: str,
    volume_multiplier: str,
    price_tick: str,
    quantity_step: str,
    budget: str | None = None,
    profile: FuturesDcaProfile | None = None,
) -> FuturesDcaProjection:
    """Build a finite long/short DCA ladder and capital preview offline."""

    if side not in ("LONG", "SHORT"):
        raise FuturesDcaPlanError("FUTURES_DCA_SIDE_INVALID", "Side LONG veya SHORT olmalıdır.")
    if base_sizing not in ("BASE_QTY", "QUOTE_NOTIONAL") or safety_sizing not in (
        "BASE_QTY",
        "QUOTE_NOTIONAL",
    ):
        raise FuturesDcaPlanError("FUTURES_DCA_SIZING_INVALID", "Sizing BASE_QTY veya QUOTE_NOTIONAL olmalıdır.")
    if type(safety_count) is not int or not 0 <= safety_count <= 50:
        raise FuturesDcaPlanError("FUTURES_DCA_COUNT_INVALID", "Safety count integer 0..50 olmalıdır.")
    try:
        anchor = positive(anchor_price)
        base = positive(base_amount)
        safety = positive(safety_amount)
        increment = positive(deviation)
        step = positive(step_multiplier)
        volume = positive(volume_multiplier)
        tick = positive(price_tick)
        qty_step = positive(quantity_step)
        budget_value = None if budget is None else positive(budget)
    except ValueError as error:
        raise FuturesDcaPlanError("FUTURES_DCA_NUMERIC_INVALID", "Plan alanları exact decimal olmalıdır.") from error
    if align(anchor, tick, up=False) != anchor:
        raise FuturesDcaPlanError("FUTURES_DCA_ANCHOR_OFF_GRID", "Anchor price tick grid üzerinde olmalıdır.")
    profile_value = FuturesDcaProfile() if profile is None else profile
    if not isinstance(profile_value, FuturesDcaProfile):
        raise FuturesDcaPlanError("FUTURES_DCA_PROFILE_INVALID", "Futures profile güvenli tipte olmalıdır.")
    base_quantity = base if base_sizing == "BASE_QTY" else base / anchor
    base_quantity = align(base_quantity, qty_step, up=False)
    if base_quantity <= 0:
        raise FuturesDcaPlanError("FUTURES_DCA_BASE_QUANTITY_INVALID", "Base quantity quantization sonrası pozitif kalmalıdır.")
    base_quote = bounded(base_quantity * anchor)
    levels: list[FuturesDcaLevel] = []
    cumulative = Q(0)
    previous = anchor
    quantity_value = safety
    for index in range(1, safety_count + 1):
        cumulative = bounded(cumulative + increment)
        raw_price = anchor * (1 - cumulative) if side == "LONG" else anchor * (1 + cumulative)
        price = align(raw_price, tick, up=side == "SHORT")
        if side == "LONG" and price >= previous or side == "SHORT" and price <= previous:
            raise FuturesDcaPlanError("FUTURES_DCA_LEVEL_INVALID", "Safety seviyeleri yönsel olarak ilerlemiyor.")
        quantity = quantity_value if safety_sizing == "BASE_QTY" else quantity_value / price
        quantity = align(quantity, qty_step, up=False)
        if quantity <= 0:
            raise FuturesDcaPlanError("FUTURES_DCA_QUANTITY_INVALID", "Safety quantity quantization sonrası pozitif kalmalıdır.")
        levels.append(FuturesDcaLevel(index, exact_text(price), exact_text(quantity), exact_text(bounded(price * quantity))))
        previous = price
        increment = bounded(increment * step)
        quantity_value = bounded(quantity_value * volume)
    required = bounded(base_quote + sum((number(level.quote_allocation) for level in levels), Q(0)))
    if budget_value is not None and required > budget_value:
        raise FuturesDcaPlanError("FUTURES_DCA_BUDGET_EXCEEDED", "DCA plan toplam kapital bütçesini aşamaz.")
    return FuturesDcaProjection(
        profile=profile_value,
        price_tick=exact_text(tick),
        quantity_step=exact_text(qty_step),
        side=side,
        anchor_price=exact_text(anchor),
        base_quantity=exact_text(base_quantity),
        base_quote_allocation=exact_text(base_quote),
        levels=tuple(levels),
        required_capital=exact_text(required),
        max_covered_deviation=exact_text(cumulative),
        last_safety_price=levels[-1].price if levels else None,
    )


def project_futures_dca_custom_ladder(
    *,
    side: str,
    anchor_price: str,
    levels: tuple[FuturesDcaCustomLevelSpec, ...],
    price_tick: str,
    allocation_unit: str,
    budget: str,
    profile: FuturesDcaProfile | None = None,
) -> FuturesDcaCustomProjection:
    """Project per-level deviation/allocation overrides without venue mutation."""

    if side not in ("LONG", "SHORT"):
        raise FuturesDcaPlanError("FUTURES_DCA_SIDE_INVALID", "Side LONG veya SHORT olmalıdır.")
    if not isinstance(levels, tuple) or len(levels) > 50 or any(
        not isinstance(level, FuturesDcaCustomLevelSpec) for level in levels
    ):
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_LEVELS_INVALID",
            "Custom level tuple 0..50 adet güvenli spec taşımalıdır.",
        )
    if allocation_unit not in ("BASE_QTY", "QUOTE_NOTIONAL"):
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_UNIT_INVALID",
            "Custom allocation unit BASE_QTY veya QUOTE_NOTIONAL olmalıdır.",
        )
    try:
        anchor = positive(anchor_price)
        tick = positive(price_tick)
    except ValueError as error:
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_NUMERIC_INVALID",
            "Anchor ve price tick exact pozitif decimal olmalıdır.",
        ) from error
    if align(anchor, tick, up=False) != anchor:
        raise FuturesDcaPlanError(
            "FUTURES_DCA_ANCHOR_OFF_GRID",
            "Anchor price tick grid üzerinde olmalıdır.",
        )
    profile_value = FuturesDcaProfile() if profile is None else profile
    if not isinstance(profile_value, FuturesDcaProfile):
        raise FuturesDcaPlanError(
            "FUTURES_DCA_PROFILE_INVALID", "Futures profile güvenli tipte olmalıdır."
        )
    previous_deviation = Q(0)
    previous_price = anchor
    custom_levels: list[FuturesDcaCustomLevel] = []
    for expected_index, level in enumerate(levels, start=1):
        if type(level.index) is not int or level.index != expected_index:
            raise FuturesDcaPlanError(
                "FUTURES_DCA_CUSTOM_INDEX_INVALID",
                "Custom level index 1’den başlayıp ardışık ilerlemelidir.",
            )
        try:
            deviation = positive(level.cumulative_deviation)
            allocation = positive(level.allocation)
        except ValueError as error:
            raise FuturesDcaPlanError(
                "FUTURES_DCA_CUSTOM_LEVEL_INVALID",
                "Custom deviation ve allocation exact pozitif decimal olmalıdır.",
            ) from error
        if deviation <= previous_deviation or (side == "LONG" and deviation >= 1):
            raise FuturesDcaPlanError(
                "FUTURES_DCA_CUSTOM_DEVIATION_INVALID",
                "Custom deviation anchor’a göre strict artmalı ve LONG için 1’den küçük olmalıdır.",
            )
        raw_price = anchor * (1 - deviation) if side == "LONG" else anchor * (1 + deviation)
        price = align(raw_price, tick, up=side == "SHORT")
        if price <= 0 or (
            side == "LONG" and price >= previous_price
        ) or (side == "SHORT" and price <= previous_price):
            raise FuturesDcaPlanError(
                "FUTURES_DCA_CUSTOM_PRICE_INVALID",
                "Custom seviyeler tick sonrası yönsel olarak strict ilerlemelidir.",
            )
        custom_levels.append(
            FuturesDcaCustomLevel(
                expected_index,
                exact_text(deviation),
                exact_text(price),
                exact_text(allocation),
            )
        )
        previous_deviation = deviation
        previous_price = price
    try:
        conservation = validate_ladder_allocations(
            allocation_unit=allocation_unit,
            allocations=tuple(level.allocation for level in custom_levels),
            budget=budget,
        )
    except LadderConservationError as error:
        raise FuturesDcaPlanError(error.code, str(error)) from error
    return FuturesDcaCustomProjection(
        profile_value,
        side,
        exact_text(anchor),
        exact_text(tick),
        allocation_unit,
        tuple(custom_levels),
        conservation,
    )


def bind_futures_dca_custom_candidates(
    ladder: FuturesDcaCustomProjection,
    instrument: InstrumentFilterProfile,
) -> FuturesDcaCustomCandidateProjection:
    """Quantize a custom ladder and validate candidates without posting orders."""

    if not isinstance(ladder, FuturesDcaCustomProjection):
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_LADDER_INVALID",
            "Custom ladder güvenli projection tipinde olmalıdır.",
        )
    if ladder.allocation_unit not in ("BASE_QTY", "QUOTE_NOTIONAL"):
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_UNIT_INVALID",
            "Custom allocation unit BASE_QTY veya QUOTE_NOTIONAL olmalıdır.",
        )
    if not isinstance(instrument, InstrumentFilterProfile):
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_INSTRUMENT_INVALID",
            "Instrument filter profili güvenli tipte olmalıdır.",
        )
    try:
        instrument_tick = exact_text(positive(instrument.price_tick))
        quantity_step = positive(instrument.qty_step)
    except ValueError as error:
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_INSTRUMENT_INVALID",
            "Instrument filter metadata exact pozitif decimal olmalıdır.",
        ) from error
    if instrument_tick != ladder.price_tick:
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_PRICE_TICK_MISMATCH",
            "Custom ladder price tick’i instrument filter tick’i ile eşleşmelidir.",
        )
    candidates: list[FuturesDcaCustomCandidateLevel] = []
    actual_allocations: list[str] = []
    for level in ladder.levels:
        try:
            allocation = positive(level.allocation)
            price = positive(level.price)
            raw_quantity = (
                allocation
                if ladder.allocation_unit == "BASE_QTY"
                else allocation / price
            )
            quantity = align(raw_quantity, quantity_step, up=False)
        except ValueError as error:
            raise FuturesDcaPlanError(
                "FUTURES_DCA_CUSTOM_CANDIDATE_INVALID",
                "Custom candidate decimal alanları geçersiz.",
            ) from error
        if quantity <= 0:
            raise FuturesDcaPlanError(
                "FUTURES_DCA_CUSTOM_QUANTITY_COLLAPSED",
                "Quantity-step quantization sonrası aday miktarı sıfıra düştü.",
            )
        try:
            validated: ValidatedOrderCandidate = validate_order_candidate(
                instrument,
                quantity=exact_text(quantity),
                price=level.price,
            )
        except InstrumentFilterError as error:
            raise FuturesDcaPlanError(error.code, str(error)) from error
        except ValueError as error:
            raise FuturesDcaPlanError(
                "FUTURES_DCA_CUSTOM_INSTRUMENT_INVALID",
                "Instrument filter profili doğrulanamadı.",
            ) from error
        actual_allocation = (
            validated.quantity
            if ladder.allocation_unit == "BASE_QTY"
            else validated.notional
        )
        actual_allocations.append(actual_allocation)
        candidates.append(
            FuturesDcaCustomCandidateLevel(
                index=level.index,
                price=validated.price,
                requested_allocation=level.allocation,
                quantity=validated.quantity,
                actual_allocation=actual_allocation,
                quote_notional=validated.notional,
            )
        )
    try:
        conservation = validate_ladder_allocations(
            allocation_unit=ladder.allocation_unit,
            allocations=tuple(actual_allocations),
            budget=ladder.conservation.budget,
        )
    except LadderConservationError as error:
        raise FuturesDcaPlanError(error.code, str(error)) from error
    return FuturesDcaCustomCandidateProjection(
        ladder=ladder,
        instrument=instrument,
        levels=tuple(candidates),
        conservation=conservation,
    )
