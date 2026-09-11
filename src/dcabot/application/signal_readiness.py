"""Readiness gate for event-time signals and closed-bar strategies."""

from dataclasses import dataclass

from dcabot.application.signal_event_contract import SignalEvent


class SignalReadinessError(ValueError):
    """Raised when a readiness gate input cannot be trusted."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class SignalReadiness:
    """Read-only signal gate result without strategy or economic authority."""

    signal_id: str
    status: str
    event_time_us: int
    closed_bar_time_us: int
    warmup_bars_observed: int
    required_warmup_bars: int
    max_staleness_us: int


def assess_signal_readiness(
    signal: SignalEvent,
    *,
    closed_bar_time_us: int,
    warmup_bars_observed: int,
    required_warmup_bars: int,
    max_staleness_us: int,
) -> SignalReadiness:
    """Classify one signal against explicit closed-bar and warmup gates.

    ``closed_bar_time_us`` is the latest source bar boundary known to be
    closed. A signal after that boundary waits for a closed bar. Staleness is
    measured only against source event time; wall-clock and processing time
    are intentionally absent. A ``READY`` result is still only a gate result
    and cannot create a candidate, order, or fill.
    """

    if not isinstance(signal, SignalEvent):
        raise SignalReadinessError(
            "SIGNAL_READINESS_EVENT_INVALID", "Signal event kaydı geçersiz."
        )
    _nonnegative_integer(closed_bar_time_us, "SIGNAL_CLOSED_BAR_TIME_INVALID")
    _nonnegative_integer(warmup_bars_observed, "SIGNAL_WARMUP_COUNT_INVALID")
    _positive_integer(required_warmup_bars, "SIGNAL_WARMUP_REQUIRED_INVALID")
    _nonnegative_integer(max_staleness_us, "SIGNAL_STALENESS_INVALID")

    if signal.event_time_us > closed_bar_time_us:
        status = "WAITING_FOR_CLOSED_BAR"
    elif signal.event_time_us < closed_bar_time_us - max_staleness_us:
        status = "STALE"
    elif warmup_bars_observed < required_warmup_bars:
        status = "WARMING_UP"
    else:
        status = "READY"

    return SignalReadiness(
        signal_id=signal.signal_id,
        status=status,
        event_time_us=signal.event_time_us,
        closed_bar_time_us=closed_bar_time_us,
        warmup_bars_observed=warmup_bars_observed,
        required_warmup_bars=required_warmup_bars,
        max_staleness_us=max_staleness_us,
    )


def _nonnegative_integer(value: int, code: str) -> None:
    if type(value) is not int or value < 0:
        raise SignalReadinessError(code, "Değer sıfır veya pozitif integer olmalıdır.")


def _positive_integer(value: int, code: str) -> None:
    if type(value) is not int or value < 1:
        raise SignalReadinessError(code, "Değer pozitif integer olmalıdır.")
