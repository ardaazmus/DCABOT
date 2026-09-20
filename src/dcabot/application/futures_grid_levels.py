"""Exact Futures Grid v1 profile and level projection before economic state."""

from dataclasses import dataclass

from dcabot.application.spot_grid_levels import (
    SpotGridLevelError,
    build_arithmetic_grid_levels,
    build_geometric_grid_levels,
)
from dcabot.domain.numbers import align, exact_text, number, positive


class FuturesGridLevelError(ValueError):
    """Raised when a Futures Grid v1 level projection is unsafe."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FuturesGridProfile:
    """The selected isolated USDⓈ-M Futures Grid profile, without venue authority."""

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
        ) != (
            "BINANCE",
            "USD_M",
            "USDT",
            "USDT",
            "PERPETUAL",
            "ONE_WAY",
            "ISOLATED",
        ):
            raise FuturesGridLevelError(
                "FUTURES_GRID_PROFILE_UNSUPPORTED",
                "Yalnız seçilen USD_M/USDT/one-way/isolated profil desteklenir.",
            )
        try:
            leverage = positive(self.leverage)
        except ValueError as error:
            raise FuturesGridLevelError(
                "FUTURES_GRID_LEVERAGE_INVALID",
                "Leverage pozitif exact decimal olmalıdır.",
            ) from error
        object.__setattr__(self, "leverage", exact_text(leverage))


@dataclass(frozen=True, slots=True)
class FuturesGridLevelProjection:
    """Exact grid levels with explicit direction and flat-start policy only."""

    profile: FuturesGridProfile
    direction: str
    initial_position_policy: str
    level_mode: str
    lower_price: str
    upper_price: str
    interval_count: int
    price_tick: str
    tick_origin: str
    levels: tuple[str, ...]
    arithmetic_step: str | None
    ratio_numerator: str | None
    ratio_denominator: str | None


def _parse_tick(price_tick: str, tick_origin: str):
    try:
        return positive(price_tick), number(tick_origin)
    except ValueError as error:
        raise FuturesGridLevelError(
            "FUTURES_GRID_TICK_INVALID",
            "price_tick pozitif, tick_origin exact decimal olmalıdır.",
        ) from error


def _ensure_tick_grid(levels: tuple[str, ...], price_tick: str, tick_origin: str) -> None:
    tick, origin = _parse_tick(price_tick, tick_origin)
    if any(align(number(level), tick, up=False, origin=origin) != number(level) for level in levels):
        raise FuturesGridLevelError(
            "FUTURES_GRID_TICK_OFF_GRID",
            "Futures Grid seviyesi declared tick grid’inde değil; quantization yapılmadı.",
        )


def project_futures_grid_levels(
    *,
    profile: FuturesGridProfile,
    direction: str,
    initial_position_policy: str,
    level_mode: str,
    lower_price: str,
    upper_price: str,
    interval_count: int,
    price_tick: str,
    tick_origin: str,
) -> FuturesGridLevelProjection:
    """Project exact Futures Grid levels without position or order authority.

    The v1 slice accepts LONG, SHORT, and NEUTRAL as explicit strategy
    directions, but only a flat initial-position policy. Margin, leverage
    effects, funding, liquidation, fills, replacement, and P&L are separate
    contracts and are deliberately absent from this result.
    """

    if not isinstance(profile, FuturesGridProfile):
        raise FuturesGridLevelError(
            "FUTURES_GRID_PROFILE_INVALID",
            "Futures Grid profile güvenli tipte olmalıdır.",
        )
    if direction not in ("LONG", "SHORT", "NEUTRAL"):
        raise FuturesGridLevelError(
            "FUTURES_GRID_DIRECTION_INVALID",
            "Direction LONG, SHORT veya NEUTRAL olmalıdır.",
        )
    if initial_position_policy != "FLAT":
        raise FuturesGridLevelError(
            "FUTURES_GRID_INITIAL_POSITION_UNSUPPORTED",
            "Bu dikey dilim yalnız explicit FLAT başlangıç politikasını destekler.",
        )
    if level_mode not in ("ARITHMETIC", "GEOMETRIC"):
        raise FuturesGridLevelError(
            "FUTURES_GRID_LEVEL_MODE_INVALID",
            "Level mode ARITHMETIC veya GEOMETRIC olmalıdır.",
        )
    _parse_tick(price_tick, tick_origin)
    try:
        if level_mode == "ARITHMETIC":
            result = build_arithmetic_grid_levels(
                lower_price=lower_price,
                upper_price=upper_price,
                interval_count=interval_count,
            )
            _ensure_tick_grid(result.levels, price_tick, tick_origin)
            return FuturesGridLevelProjection(
                profile=profile,
                direction=direction,
                initial_position_policy=initial_position_policy,
                level_mode=level_mode,
                lower_price=result.lower_price,
                upper_price=result.upper_price,
                interval_count=result.interval_count,
                price_tick=exact_text(positive(price_tick)),
                tick_origin=exact_text(number(tick_origin)),
                levels=result.levels,
                arithmetic_step=result.step,
                ratio_numerator=None,
                ratio_denominator=None,
            )
        result = build_geometric_grid_levels(
            lower_price=lower_price,
            upper_price=upper_price,
            interval_count=interval_count,
            price_tick=price_tick,
            tick_origin=tick_origin,
        )
        return FuturesGridLevelProjection(
            profile=profile,
            direction=direction,
            initial_position_policy=initial_position_policy,
            level_mode=level_mode,
            lower_price=result.lower_price,
            upper_price=result.upper_price,
            interval_count=result.interval_count,
            price_tick=result.price_tick,
            tick_origin=result.tick_origin,
            levels=result.levels,
            arithmetic_step=None,
            ratio_numerator=result.ratio_numerator,
            ratio_denominator=result.ratio_denominator,
        )
    except SpotGridLevelError as error:
        raise FuturesGridLevelError(
            "FUTURES_GRID_LEVELS_INVALID",
            f"Exact Futures Grid level projection reddedildi: {error.code}.",
        ) from error
