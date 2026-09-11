"""Exact arithmetic spot-grid level generation before order authority."""

from dataclasses import dataclass

from dcabot.domain.numbers import Q, bounded, exact_text, positive


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


def _parse_price(value: str, field_name: str) -> Q:
    try:
        return positive(value)
    except ValueError as error:
        raise SpotGridLevelError(
            "GRID_PRICE_INVALID", f"{field_name} pozitif decimal string olmalıdır."
        ) from error


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
    if (
        isinstance(interval_count, bool)
        or not isinstance(interval_count, int)
        or not 1 <= interval_count <= 1000
    ):
        raise SpotGridLevelError(
            "GRID_INTERVAL_INVALID", "interval_count 1 ile 1000 arasında tam sayı olmalıdır."
        )

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
