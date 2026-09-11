"""Exact threshold and time trigger projections for offline rebalancing."""

from dataclasses import dataclass

from dcabot.domain.numbers import Q, bounded, exact_text, number


class RebalanceTriggerError(ValueError):
    """Raised when a rebalancing trigger cannot be evaluated safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class ThresholdTriggerDecision:
    """Read-only threshold decision without order or fill authority."""

    policy: str
    status: str
    deviation: str
    threshold: str


@dataclass(frozen=True, slots=True)
class TimeTriggerDecision:
    """Read-only elapsed-time decision without order or fill authority."""

    policy: str
    status: str
    elapsed_us: int
    interval_us: int


def evaluate_threshold_trigger(
    *, current_weight: str, target_weight: str, threshold: str
) -> ThresholdTriggerDecision:
    """Evaluate ``abs(current-target) >= threshold`` exactly."""

    current = _weight(current_weight)
    target = _weight(target_weight)
    try:
        limit = number(threshold)
    except ValueError as error:
        raise RebalanceTriggerError(
            "REBALANCE_THRESHOLD_INVALID",
            "Threshold decimal string olmalıdır.",
        ) from error
    if limit < 0 or limit > 1:
        raise RebalanceTriggerError(
            "REBALANCE_THRESHOLD_INVALID",
            "Threshold 0 ile 1 arasında olmalıdır.",
        )
    deviation = bounded(abs(current - target))
    try:
        return ThresholdTriggerDecision(
            policy="THRESHOLD",
            status="TRIGGERED" if deviation >= limit else "NOT_TRIGGERED",
            deviation=exact_text(deviation),
            threshold=exact_text(limit),
        )
    except ValueError as error:
        raise RebalanceTriggerError(
            "REBALANCE_TRIGGER_UNREPRESENTABLE",
            "Threshold sonucu exact decimal sözleşmesine sığmıyor.",
        ) from error


def evaluate_time_trigger(
    *, last_rebalance_time_us: int, observation_time_us: int, interval_us: int
) -> TimeTriggerDecision:
    """Evaluate ``observation-last >= interval`` with source integer times."""

    _time(last_rebalance_time_us, "REBALANCE_TIME_INVALID")
    _time(observation_time_us, "REBALANCE_TIME_INVALID")
    if type(interval_us) is not int or interval_us < 1:
        raise RebalanceTriggerError(
            "REBALANCE_INTERVAL_INVALID",
            "Interval pozitif integer microseconds olmalıdır.",
        )
    if observation_time_us < last_rebalance_time_us:
        raise RebalanceTriggerError(
            "REBALANCE_TIME_ORDER_INVALID",
            "Observation zamanı son rebalancing zamanından eski olamaz.",
        )
    elapsed = observation_time_us - last_rebalance_time_us
    return TimeTriggerDecision(
        policy="TIME_INTERVAL",
        status="TRIGGERED" if elapsed >= interval_us else "NOT_TRIGGERED",
        elapsed_us=elapsed,
        interval_us=interval_us,
    )


def _weight(value: str) -> Q:
    try:
        result = number(value)
    except ValueError as error:
        raise RebalanceTriggerError(
            "REBALANCE_WEIGHT_INVALID",
            "Weight decimal string olmalıdır.",
        ) from error
    if result < 0 or result > 1:
        raise RebalanceTriggerError(
            "REBALANCE_WEIGHT_INVALID",
            "Weight 0 ile 1 arasında olmalıdır.",
        )
    return result


def _time(value: int, code: str) -> None:
    if type(value) is not int or value < 0:
        raise RebalanceTriggerError(code, "Zaman sıfır veya pozitif integer olmalıdır.")
