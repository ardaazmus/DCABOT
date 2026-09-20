"""Offline start-condition gate for the Futures DCA lifecycle."""

from dataclasses import dataclass
from enum import StrEnum

from dcabot.application.signal_readiness import SignalReadiness


class FuturesDcaStartGateError(ValueError):
    """Raised when a Futures DCA start boundary is not representable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class FuturesDcaStartMode(StrEnum):
    """Explicit start families; calendar DCA is a separate product."""

    IMMEDIATE = "IMMEDIATE"
    CLOSED_CANDLE = "CLOSED_CANDLE"
    SIGNAL = "SIGNAL"


class FuturesDcaStartStatus(StrEnum):
    """Read-only start decision status."""

    ELIGIBLE = "ELIGIBLE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class FuturesDcaStartEvaluation:
    """Start gate result without lifecycle, order, or fill authority."""

    mode: FuturesDcaStartMode
    status: FuturesDcaStartStatus
    event_time_us: int
    reason: str
    signal_id: str | None = None
    order_authority: str = "NONE"

    def __post_init__(self) -> None:
        if self.order_authority != "NONE":
            raise FuturesDcaStartGateError(
                "FUTURES_DCA_START_ORDER_AUTHORITY_INVALID",
                "Start gate order authority taşıyamaz.",
            )
        if type(self.event_time_us) is not int or self.event_time_us < 0:
            raise FuturesDcaStartGateError(
                "FUTURES_DCA_START_TIME_INVALID",
                "Start event zamanı sıfır veya pozitif integer olmalıdır.",
            )


def assess_futures_dca_start(
    *,
    mode: FuturesDcaStartMode | str,
    event_time_us: int,
    closed_bar_time_us: int | None = None,
    signal_readiness: SignalReadiness | None = None,
) -> FuturesDcaStartEvaluation:
    """Evaluate one explicit start condition without creating a deal or order.

    ``SIGNAL`` delegates closed-bar, warmup, and staleness ownership to the
    existing ``SignalReadiness`` gate. ``CLOSED_CANDLE`` uses only source-time
    ordering; wall-clock time and processing time are intentionally absent.
    """

    try:
        start_mode = FuturesDcaStartMode(mode)
    except (TypeError, ValueError) as error:
        raise FuturesDcaStartGateError(
            "FUTURES_DCA_START_MODE_INVALID",
            "Start mode IMMEDIATE, CLOSED_CANDLE veya SIGNAL olmalıdır.",
        ) from error
    if type(event_time_us) is not int or event_time_us < 0:
        raise FuturesDcaStartGateError(
            "FUTURES_DCA_START_TIME_INVALID",
            "Start event zamanı sıfır veya pozitif integer olmalıdır.",
        )
    if closed_bar_time_us is not None and (
        type(closed_bar_time_us) is not int or closed_bar_time_us < 0
    ):
        raise FuturesDcaStartGateError(
            "FUTURES_DCA_START_CLOSED_BAR_INVALID",
            "Closed-bar zamanı sıfır veya pozitif integer olmalıdır.",
        )
    if signal_readiness is not None and not isinstance(
        signal_readiness, SignalReadiness
    ):
        raise FuturesDcaStartGateError(
            "FUTURES_DCA_START_SIGNAL_INVALID",
            "Signal readiness güvenli tipte olmalıdır.",
        )

    if start_mode is FuturesDcaStartMode.IMMEDIATE:
        if closed_bar_time_us is not None or signal_readiness is not None:
            raise FuturesDcaStartGateError(
                "FUTURES_DCA_START_CONTEXT_CONFLICT",
                "IMMEDIATE başlangıç closed-bar veya signal context taşıyamaz.",
            )
        return FuturesDcaStartEvaluation(
            mode=start_mode,
            status=FuturesDcaStartStatus.ELIGIBLE,
            event_time_us=event_time_us,
            reason="IMMEDIATE_CONDITION_MET",
        )

    if start_mode is FuturesDcaStartMode.CLOSED_CANDLE:
        if closed_bar_time_us is None or signal_readiness is not None:
            raise FuturesDcaStartGateError(
                "FUTURES_DCA_START_CONTEXT_CONFLICT",
                "CLOSED_CANDLE yalnız explicit closed-bar zamanı taşımalıdır.",
            )
        if event_time_us > closed_bar_time_us:
            return FuturesDcaStartEvaluation(
                mode=start_mode,
                status=FuturesDcaStartStatus.BLOCKED,
                event_time_us=event_time_us,
                reason="WAITING_FOR_CLOSED_BAR",
            )
        return FuturesDcaStartEvaluation(
            mode=start_mode,
            status=FuturesDcaStartStatus.ELIGIBLE,
            event_time_us=event_time_us,
            reason="CLOSED_CANDLE_CONFIRMED",
        )

    if closed_bar_time_us is not None or signal_readiness is None:
        raise FuturesDcaStartGateError(
            "FUTURES_DCA_START_CONTEXT_CONFLICT",
            "SIGNAL yalnız mevcut SignalReadiness sonucu taşımalıdır.",
        )
    if event_time_us != signal_readiness.event_time_us:
        raise FuturesDcaStartGateError(
            "FUTURES_DCA_START_SIGNAL_TIME_CONFLICT",
            "Start event zamanı signal source zamanı ile eşleşmelidir.",
        )
    if signal_readiness.status != "READY":
        return FuturesDcaStartEvaluation(
            mode=start_mode,
            status=FuturesDcaStartStatus.BLOCKED,
            event_time_us=event_time_us,
            reason=f"SIGNAL_{signal_readiness.status}",
            signal_id=signal_readiness.signal_id,
        )
    return FuturesDcaStartEvaluation(
        mode=start_mode,
        status=FuturesDcaStartStatus.ELIGIBLE,
        event_time_us=event_time_us,
        reason="SIGNAL_READY",
        signal_id=signal_readiness.signal_id,
    )
