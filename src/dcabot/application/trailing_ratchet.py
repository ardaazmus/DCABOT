"""Exact long trailing-stop ratchet as a trigger-only application contract."""

from dataclasses import dataclass

from dcabot.domain.numbers import Q, bounded, exact_text, positive


class TrailingRatchetError(ValueError):
    """Raised when a trailing state or observation is invalid."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class TrailingLongState:
    """Long trailing state; trigger state is not an execution or a fill."""

    status: str
    activation_price: str
    distance: str
    high_water: str | None
    stop_price: str | None


@dataclass(frozen=True, slots=True)
class TrailingLongPercentageState:
    """Long percentage trailing state; trigger state is not an execution or a fill."""

    status: str
    activation_price: str
    rate: str
    high_water: str | None
    stop_price: str | None


@dataclass(frozen=True, slots=True)
class TrailingShortState:
    """Short trailing state; trigger state is not an execution or a fill."""

    status: str
    activation_price: str
    distance: str
    low_water: str | None
    stop_price: str | None


@dataclass(frozen=True, slots=True)
class TrailingShortPercentageState:
    """Short percentage trailing state; trigger state is not an execution or a fill."""

    status: str
    activation_price: str
    rate: str
    low_water: str | None
    stop_price: str | None


def _positive(value: str, code: str, label: str) -> Q:
    try:
        return positive(value)
    except ValueError as error:
        raise TrailingRatchetError(code, f"{label} pozitif decimal string olmalıdır.") from error


def _rate(value: str, code: str = "TRAILING_RATE_INVALID") -> Q:
    rate = _positive(value, code, "Trailing rate")
    if rate >= 1:
        raise TrailingRatchetError(
            code, "Trailing rate 0 ile 1 arasında olmalıdır."
        )
    return rate


def arm_long_trailing(*, activation_price: str, distance: str) -> TrailingLongState:
    """Create an inactive long trailing trigger with a fixed price distance."""

    activation = _positive(
        activation_price, "TRAILING_ACTIVATION_INVALID", "Activation price"
    )
    trailing_distance = _positive(
        distance, "TRAILING_DISTANCE_INVALID", "Trailing distance"
    )
    if trailing_distance >= activation:
        raise TrailingRatchetError(
            "TRAILING_DISTANCE_INVALID",
            "Trailing distance activation price’tan küçük olmalıdır.",
        )
    try:
        return TrailingLongState(
            status="INACTIVE",
            activation_price=exact_text(activation),
            distance=exact_text(trailing_distance),
            high_water=None,
            stop_price=None,
        )
    except ValueError as error:
        raise TrailingRatchetError(
            "TRAILING_STATE_UNREPRESENTABLE",
            "Trailing state exact decimal sözleşmesine sığmıyor.",
        ) from error


def observe_long_trailing(
    state: TrailingLongState, *, price: str
) -> TrailingLongState:
    """Update long high-water and return a trigger-only trailing projection."""

    if not isinstance(state, TrailingLongState):
        raise TrailingRatchetError(
            "TRAILING_STATE_INVALID", "Trailing state geçersiz."
        )
    if state.status not in ("INACTIVE", "ACTIVE", "TRIGGERED"):
        raise TrailingRatchetError(
            "TRAILING_STATE_INVALID", "Trailing state status geçersiz."
        )
    if state.status == "TRIGGERED":
        raise TrailingRatchetError(
            "TRAILING_ALREADY_TRIGGERED", "Tetiklenmiş trailing yeniden gözlenemez."
        )
    observed = _positive(price, "TRAILING_PRICE_INVALID", "Observed price")
    activation = _positive(
        state.activation_price, "TRAILING_STATE_INVALID", "Activation price"
    )
    distance = _positive(
        state.distance, "TRAILING_STATE_INVALID", "Trailing distance"
    )
    if distance >= activation:
        raise TrailingRatchetError(
            "TRAILING_STATE_INVALID",
            "Trailing distance activation price’tan küçük olmalıdır.",
        )
    if state.status == "INACTIVE":
        if observed < activation:
            return state
        high_water = observed
    else:
        if state.high_water is None or state.stop_price is None:
            raise TrailingRatchetError(
                "TRAILING_STATE_INVALID", "Active trailing high-water ve stop taşır."
            )
        high_water = _positive(
            state.high_water, "TRAILING_STATE_INVALID", "High-water"
        )
        if observed > high_water:
            high_water = observed
    stop = bounded(high_water - distance)
    status = "TRIGGERED" if observed <= stop else "ACTIVE"
    try:
        return TrailingLongState(
            status=status,
            activation_price=exact_text(activation),
            distance=exact_text(distance),
            high_water=exact_text(high_water),
            stop_price=exact_text(stop),
        )
    except ValueError as error:
        raise TrailingRatchetError(
            "TRAILING_STATE_UNREPRESENTABLE",
            "Trailing state exact decimal sözleşmesine sığmıyor.",
        ) from error


def arm_short_trailing(*, activation_price: str, distance: str) -> TrailingShortState:
    """Create an inactive short trailing trigger with a fixed price distance."""

    activation = _positive(
        activation_price, "TRAILING_ACTIVATION_INVALID", "Activation price"
    )
    trailing_distance = _positive(
        distance, "TRAILING_DISTANCE_INVALID", "Trailing distance"
    )
    if trailing_distance >= activation:
        raise TrailingRatchetError(
            "TRAILING_DISTANCE_INVALID",
            "Trailing distance activation price’tan küçük olmalıdır.",
        )
    try:
        return TrailingShortState(
            status="INACTIVE",
            activation_price=exact_text(activation),
            distance=exact_text(trailing_distance),
            low_water=None,
            stop_price=None,
        )
    except ValueError as error:
        raise TrailingRatchetError(
            "TRAILING_STATE_UNREPRESENTABLE",
            "Trailing state exact decimal sözleşmesine sığmıyor.",
        ) from error


def observe_short_trailing(
    state: TrailingShortState, *, price: str
) -> TrailingShortState:
    """Update short low-water and return a trigger-only trailing projection."""

    if not isinstance(state, TrailingShortState):
        raise TrailingRatchetError(
            "TRAILING_STATE_INVALID", "Trailing state geçersiz."
        )
    if state.status not in ("INACTIVE", "ACTIVE", "TRIGGERED"):
        raise TrailingRatchetError(
            "TRAILING_STATE_INVALID", "Trailing state status geçersiz."
        )
    if state.status == "TRIGGERED":
        raise TrailingRatchetError(
            "TRAILING_ALREADY_TRIGGERED", "Tetiklenmiş trailing yeniden gözlenemez."
        )
    observed = _positive(price, "TRAILING_PRICE_INVALID", "Observed price")
    activation = _positive(
        state.activation_price, "TRAILING_STATE_INVALID", "Activation price"
    )
    distance = _positive(
        state.distance, "TRAILING_STATE_INVALID", "Trailing distance"
    )
    if distance >= activation:
        raise TrailingRatchetError(
            "TRAILING_STATE_INVALID",
            "Trailing distance activation price’tan küçük olmalıdır.",
        )
    if state.status == "INACTIVE":
        if observed > activation:
            return state
        low_water = observed
    else:
        if state.low_water is None or state.stop_price is None:
            raise TrailingRatchetError(
                "TRAILING_STATE_INVALID", "Active trailing low-water ve stop taşır."
            )
        low_water = _positive(
            state.low_water, "TRAILING_STATE_INVALID", "Low-water"
        )
        if observed < low_water:
            low_water = observed
    stop = bounded(low_water + distance)
    status = "TRIGGERED" if observed >= stop else "ACTIVE"
    try:
        return TrailingShortState(
            status=status,
            activation_price=exact_text(activation),
            distance=exact_text(distance),
            low_water=exact_text(low_water),
            stop_price=exact_text(stop),
        )
    except ValueError as error:
        raise TrailingRatchetError(
            "TRAILING_STATE_UNREPRESENTABLE",
            "Trailing state exact decimal sözleşmesine sığmıyor.",
        ) from error


def arm_long_percentage_trailing(
    *, activation_price: str, rate: str
) -> TrailingLongPercentageState:
    """Create an inactive long trailing trigger with a fixed percentage rate."""

    activation = _positive(
        activation_price, "TRAILING_ACTIVATION_INVALID", "Activation price"
    )
    trailing_rate = _rate(rate)
    try:
        return TrailingLongPercentageState(
            status="INACTIVE",
            activation_price=exact_text(activation),
            rate=exact_text(trailing_rate),
            high_water=None,
            stop_price=None,
        )
    except ValueError as error:
        raise TrailingRatchetError(
            "TRAILING_STATE_UNREPRESENTABLE",
            "Trailing state exact decimal sözleşmesine sığmıyor.",
        ) from error


def observe_long_percentage_trailing(
    state: TrailingLongPercentageState, *, price: str
) -> TrailingLongPercentageState:
    """Update long percentage high-water and return a trigger-only projection."""

    if not isinstance(state, TrailingLongPercentageState):
        raise TrailingRatchetError(
            "TRAILING_STATE_INVALID", "Trailing state geçersiz."
        )
    if state.status not in ("INACTIVE", "ACTIVE", "TRIGGERED"):
        raise TrailingRatchetError(
            "TRAILING_STATE_INVALID", "Trailing state status geçersiz."
        )
    if state.status == "TRIGGERED":
        raise TrailingRatchetError(
            "TRAILING_ALREADY_TRIGGERED", "Tetiklenmiş trailing yeniden gözlenemez."
        )
    observed = _positive(price, "TRAILING_PRICE_INVALID", "Observed price")
    activation = _positive(
        state.activation_price, "TRAILING_STATE_INVALID", "Activation price"
    )
    trailing_rate = _rate(state.rate, "TRAILING_STATE_INVALID")
    if state.status == "INACTIVE":
        if observed < activation:
            return state
        high_water = observed
    else:
        if state.high_water is None or state.stop_price is None:
            raise TrailingRatchetError(
                "TRAILING_STATE_INVALID", "Active trailing high-water ve stop taşır."
            )
        high_water = _positive(
            state.high_water, "TRAILING_STATE_INVALID", "High-water"
        )
        if observed > high_water:
            high_water = observed
    stop = bounded(high_water * (1 - trailing_rate))
    status = "TRIGGERED" if observed <= stop else "ACTIVE"
    try:
        return TrailingLongPercentageState(
            status=status,
            activation_price=exact_text(activation),
            rate=exact_text(trailing_rate),
            high_water=exact_text(high_water),
            stop_price=exact_text(stop),
        )
    except ValueError as error:
        raise TrailingRatchetError(
            "TRAILING_STATE_UNREPRESENTABLE",
            "Trailing state exact decimal sözleşmesine sığmıyor.",
        ) from error


def arm_short_percentage_trailing(
    *, activation_price: str, rate: str
) -> TrailingShortPercentageState:
    """Create an inactive short trailing trigger with a fixed percentage rate."""

    activation = _positive(
        activation_price, "TRAILING_ACTIVATION_INVALID", "Activation price"
    )
    trailing_rate = _rate(rate)
    try:
        return TrailingShortPercentageState(
            status="INACTIVE",
            activation_price=exact_text(activation),
            rate=exact_text(trailing_rate),
            low_water=None,
            stop_price=None,
        )
    except ValueError as error:
        raise TrailingRatchetError(
            "TRAILING_STATE_UNREPRESENTABLE",
            "Trailing state exact decimal sözleşmesine sığmıyor.",
        ) from error


def observe_short_percentage_trailing(
    state: TrailingShortPercentageState, *, price: str
) -> TrailingShortPercentageState:
    """Update short percentage low-water and return a trigger-only projection."""

    if not isinstance(state, TrailingShortPercentageState):
        raise TrailingRatchetError(
            "TRAILING_STATE_INVALID", "Trailing state geçersiz."
        )
    if state.status not in ("INACTIVE", "ACTIVE", "TRIGGERED"):
        raise TrailingRatchetError(
            "TRAILING_STATE_INVALID", "Trailing state status geçersiz."
        )
    if state.status == "TRIGGERED":
        raise TrailingRatchetError(
            "TRAILING_ALREADY_TRIGGERED", "Tetiklenmiş trailing yeniden gözlenemez."
        )
    observed = _positive(price, "TRAILING_PRICE_INVALID", "Observed price")
    activation = _positive(
        state.activation_price, "TRAILING_STATE_INVALID", "Activation price"
    )
    trailing_rate = _rate(state.rate, "TRAILING_STATE_INVALID")
    if state.status == "INACTIVE":
        if observed > activation:
            return state
        low_water = observed
    else:
        if state.low_water is None or state.stop_price is None:
            raise TrailingRatchetError(
                "TRAILING_STATE_INVALID", "Active trailing low-water ve stop taşır."
            )
        low_water = _positive(
            state.low_water, "TRAILING_STATE_INVALID", "Low-water"
        )
        if observed < low_water:
            low_water = observed
    stop = bounded(low_water * (1 + trailing_rate))
    status = "TRIGGERED" if observed >= stop else "ACTIVE"
    try:
        return TrailingShortPercentageState(
            status=status,
            activation_price=exact_text(activation),
            rate=exact_text(trailing_rate),
            low_water=exact_text(low_water),
            stop_price=exact_text(stop),
        )
    except ValueError as error:
        raise TrailingRatchetError(
            "TRAILING_STATE_UNREPRESENTABLE",
            "Trailing state exact decimal sözleşmesine sığmıyor.",
        ) from error
