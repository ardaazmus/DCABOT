"""Offline max-DCA and terminal boundary for the Futures DCA lifecycle."""

from dataclasses import dataclass
from enum import StrEnum


class FuturesDcaStopContractError(ValueError):
    """Raised when a Futures DCA stop boundary is not representable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class FuturesDcaStopReason(StrEnum):
    """Explicit stop sources kept separate from ladder exhaustion."""

    MAX_DCA_REACHED = "MAX_DCA_REACHED"
    STOP_LOSS = "STOP_LOSS"
    TIMEOUT = "TIMEOUT"
    MARKET_CLOSE = "MARKET_CLOSE"
    BOT_STOP = "BOT_STOP"
    USER_STOP = "USER_STOP"
    LADDER_EXHAUSTED = "LADDER_EXHAUSTED"


class FuturesDcaStopStatus(StrEnum):
    """Read-only continuation or terminal boundary decision."""

    CONTINUE = "CONTINUE"
    STOP = "STOP"
    EXHAUSTED = "EXHAUSTED"


@dataclass(frozen=True, slots=True)
class FuturesDcaStopRequest:
    """An explicit external stop request without execution authority."""

    reason: FuturesDcaStopReason

    def __post_init__(self) -> None:
        if not isinstance(self.reason, FuturesDcaStopReason):
            raise FuturesDcaStopContractError(
                "FUTURES_DCA_STOP_REQUEST_REASON_INVALID",
                "External stop request reason güvenli enum olmalıdır.",
            )
        if self.reason in {
            FuturesDcaStopReason.MAX_DCA_REACHED,
            FuturesDcaStopReason.LADDER_EXHAUSTED,
        }:
            raise FuturesDcaStopContractError(
                "FUTURES_DCA_STOP_REQUEST_REASON_INVALID",
                "External stop request explicit external reason taşımalıdır.",
            )


@dataclass(frozen=True, slots=True)
class FuturesDcaStopEvaluation:
    """Pure stop decision that cannot create an order or mutate a lifecycle."""

    completed_dca_count: int
    max_dca_count: int
    ladder_level_count: int
    status: FuturesDcaStopStatus
    reason: FuturesDcaStopReason | None
    order_authority: str = "NONE"

    def __post_init__(self) -> None:
        if self.order_authority != "NONE":
            raise FuturesDcaStopContractError(
                "FUTURES_DCA_STOP_ORDER_AUTHORITY_INVALID",
                "Stop değerlendirmesi order authority taşıyamaz.",
            )


def assess_futures_dca_stop(
    *,
    completed_dca_count: int,
    max_dca_count: int,
    ladder_level_count: int,
    stop_request: FuturesDcaStopRequest | None = None,
) -> FuturesDcaStopEvaluation:
    """Classify max-DCA, explicit stop, or full-ladder terminal boundaries.

    An explicit stop request is kept distinct from ``EXHAUSTED``. A complete
    ladder is terminal only when no external stop request is present; a
    max-DCA cap stops further averaging while unconsumed ladder levels remain.
    No wall-clock, venue, order, fill, reserve, or persistence state is read.
    """

    _positive_integer(max_dca_count, "FUTURES_DCA_MAX_COUNT_INVALID")
    _positive_integer(ladder_level_count, "FUTURES_DCA_LADDER_COUNT_INVALID")
    _nonnegative_integer(completed_dca_count, "FUTURES_DCA_COMPLETED_COUNT_INVALID")
    if max_dca_count > ladder_level_count:
        raise FuturesDcaStopContractError(
            "FUTURES_DCA_MAX_COUNT_EXCEEDS_LADDER",
            "Max-DCA sayısı ladder seviyelerini aşamaz.",
        )
    if completed_dca_count > ladder_level_count:
        raise FuturesDcaStopContractError(
            "FUTURES_DCA_COMPLETED_COUNT_EXCEEDS_LADDER",
            "Tamamlanan DCA sayısı ladder seviyelerini aşamaz.",
        )
    if stop_request is not None and not isinstance(
        stop_request, FuturesDcaStopRequest
    ):
        raise FuturesDcaStopContractError(
            "FUTURES_DCA_STOP_REQUEST_INVALID",
            "Stop request güvenli Futures DCA tipinde olmalıdır.",
        )

    if stop_request is not None:
        return FuturesDcaStopEvaluation(
            completed_dca_count=completed_dca_count,
            max_dca_count=max_dca_count,
            ladder_level_count=ladder_level_count,
            status=FuturesDcaStopStatus.STOP,
            reason=stop_request.reason,
        )
    if completed_dca_count == ladder_level_count:
        return FuturesDcaStopEvaluation(
            completed_dca_count=completed_dca_count,
            max_dca_count=max_dca_count,
            ladder_level_count=ladder_level_count,
            status=FuturesDcaStopStatus.EXHAUSTED,
            reason=FuturesDcaStopReason.LADDER_EXHAUSTED,
        )
    if completed_dca_count >= max_dca_count:
        return FuturesDcaStopEvaluation(
            completed_dca_count=completed_dca_count,
            max_dca_count=max_dca_count,
            ladder_level_count=ladder_level_count,
            status=FuturesDcaStopStatus.STOP,
            reason=FuturesDcaStopReason.MAX_DCA_REACHED,
        )
    return FuturesDcaStopEvaluation(
        completed_dca_count=completed_dca_count,
        max_dca_count=max_dca_count,
        ladder_level_count=ladder_level_count,
        status=FuturesDcaStopStatus.CONTINUE,
        reason=None,
    )


def _nonnegative_integer(value: int, code: str) -> None:
    if type(value) is not int or value < 0:
        raise FuturesDcaStopContractError(
            code, "Değer sıfır veya pozitif integer olmalıdır."
        )


def _positive_integer(value: int, code: str) -> None:
    if type(value) is not int or value < 1:
        raise FuturesDcaStopContractError(code, "Değer pozitif integer olmalıdır.")
