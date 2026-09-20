"""Exact arithmetic spot-grid level generation before order authority."""

from dataclasses import dataclass

from dcabot.domain.numbers import Q, align, bounded, exact_text, number, positive


class SpotGridLevelError(ValueError):
    """Raised when an arithmetic spot-grid level set is unsafe to publish."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class ArithmeticGridLevels:
    """Exact arithmetic levels, without inventory, order, fee, or fill state."""

    lower_price: str
    upper_price: str
    interval_count: int
    step: str
    levels: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GeometricGridLevels:
    """Exact geometric levels with explicit tick-grid validation."""

    lower_price: str
    upper_price: str
    interval_count: int
    ratio_numerator: str
    ratio_denominator: str
    price_tick: str
    tick_origin: str
    levels: tuple[str, ...]


def _parse_price(value: str, field_name: str) -> Q:
    try:
        return positive(value)
    except ValueError as error:
        raise SpotGridLevelError(
            "GRID_PRICE_INVALID", f"{field_name} pozitif decimal string olmalıdır."
        ) from error


def _validate_interval_count(interval_count: int) -> None:
    if (
        isinstance(interval_count, bool)
        or not isinstance(interval_count, int)
        or not 1 <= interval_count <= 1000
    ):
        raise SpotGridLevelError(
            "GRID_INTERVAL_INVALID", "interval_count 1 ile 1000 arasında tam sayı olmalıdır."
        )


def _exact_nth_root(value: int, degree: int) -> int | None:
    if value < 0 or degree < 1:
        return None
    if value in (0, 1):
        return value
    high = 1 << ((value.bit_length() + degree - 1) // degree + 1)
    low = 0
    while low + 1 < high:
        middle = (low + high) // 2
        if middle**degree <= value:
            low = middle
        else:
            high = middle
    return low if low**degree == value else None


def build_arithmetic_grid_levels(
    *, lower_price: str, upper_price: str, interval_count: int
) -> ArithmeticGridLevels:
    """Build ``N + 1`` exact levels for ``(upper - lower) / N``.

    The function is deliberately limited to arithmetic level generation. It does
    not quantize venue prices, create orders, reserve funds, mutate inventory, or
    calculate fees and profit. A non-terminating decimal result is rejected
    instead of being rounded without an explicit profile policy.
    """

    lower = _parse_price(lower_price, "lower_price")
    upper = _parse_price(upper_price, "upper_price")
    if upper <= lower:
        raise SpotGridLevelError(
            "GRID_BOUNDS_INVALID", "upper_price lower_price değerinden büyük olmalıdır."
        )
    _validate_interval_count(interval_count)

    step = bounded((upper - lower) / interval_count)
    levels = tuple(bounded(lower + step * index) for index in range(interval_count + 1))
    try:
        rendered_step = exact_text(step)
        rendered_levels = tuple(exact_text(level) for level in levels)
        return ArithmeticGridLevels(
            lower_price=exact_text(lower),
            upper_price=exact_text(upper),
            interval_count=interval_count,
            step=rendered_step,
            levels=rendered_levels,
        )
    except ValueError as error:
        raise SpotGridLevelError(
            "GRID_LEVEL_UNREPRESENTABLE",
            "Seviye exact decimal sözleşmesine sığmıyor; sessiz yuvarlama yapılmadı.",
        ) from error


def build_geometric_grid_levels(
    *,
    lower_price: str,
    upper_price: str,
    interval_count: int,
    price_tick: str,
    tick_origin: str,
) -> GeometricGridLevels:
    """Build geometric levels only when ratio and every level are exact.

    The ratio is computed as an exact rational root. Non-perfect roots and
    off-tick levels are rejected; this function never performs venue rounding.
    """

    lower = _parse_price(lower_price, "lower_price")
    upper = _parse_price(upper_price, "upper_price")
    if upper <= lower:
        raise SpotGridLevelError(
            "GRID_BOUNDS_INVALID", "upper_price lower_price değerinden büyük olmalıdır."
        )
    _validate_interval_count(interval_count)
    try:
        tick = positive(price_tick)
        origin = number(tick_origin)
    except ValueError as error:
        raise SpotGridLevelError(
            "GRID_TICK_INVALID", "price_tick pozitif, tick_origin exact decimal olmalıdır."
        ) from error

    value_ratio = bounded(upper / lower)
    numerator_root = _exact_nth_root(value_ratio.numerator, interval_count)
    denominator_root = _exact_nth_root(value_ratio.denominator, interval_count)
    if numerator_root is None or denominator_root is None:
        raise SpotGridLevelError(
            "GRID_GEOMETRIC_RATIO_UNREPRESENTABLE",
            "Geometric ratio exact rational kök değil; yaklaşık seviye yayınlanmadı.",
        )
    ratio_value = bounded(Q(numerator_root, denominator_root))
    levels = tuple(bounded(lower * ratio_value**index) for index in range(interval_count + 1))
    try:
        if any(align(level, tick, up=False, origin=origin) != level for level in levels):
            raise SpotGridLevelError(
                "GRID_GEOMETRIC_TICK_OFF_GRID",
                "Geometric seviye declared tick grid’inde değil; quantization yapılmadı.",
            )
        return GeometricGridLevels(
            lower_price=exact_text(lower),
            upper_price=exact_text(upper),
            interval_count=interval_count,
            ratio_numerator=str(ratio_value.numerator),
            ratio_denominator=str(ratio_value.denominator),
            price_tick=exact_text(tick),
            tick_origin=exact_text(origin),
            levels=tuple(exact_text(level) for level in levels),
        )
    except SpotGridLevelError:
        raise
    except ValueError as error:
        raise SpotGridLevelError(
            "GRID_GEOMETRIC_LEVEL_UNREPRESENTABLE",
            "Geometric ratio veya seviye exact decimal sözleşmesine sığmıyor.",
        ) from error
