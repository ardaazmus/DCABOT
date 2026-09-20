"""Offline conditional trigger-to-execution identity contract."""

from dataclasses import dataclass, replace
from enum import StrEnum
import re

from dcabot.application.spot_order_lifecycle import SpotSide
from dcabot.domain.numbers import exact_text, positive


class ConditionalExecutionError(ValueError):
    """Raised when a conditional lifecycle boundary cannot be trusted."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class ConditionalStatus(StrEnum):
    ARMED = "ARMED"
    TRIGGERED = "TRIGGERED"
    EXECUTION_IDENTIFIED = "EXECUTION_IDENTIFIED"
    CANCELED = "CANCELED"
    QUARANTINED = "QUARANTINED"


class ConditionalExecutionOutcome(StrEnum):
    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True, slots=True)
class ConditionalExecutionResult:
    execution: "ConditionalExecution"
    outcome: ConditionalExecutionOutcome


@dataclass(frozen=True, slots=True)
class ConditionalExecution:
    """Immutable trigger/execution identity with no fill or core authority."""

    conditional_order_id: str
    symbol: str
    side: SpotSide
    trigger_kind: str
    trigger_price: str
    status: ConditionalStatus = ConditionalStatus.ARMED
    trigger_event_id: str | None = None
    observed_at_ms: int | None = None
    observed_price: str | None = None
    execution_order_id: str | None = None
    execution_order_type: str | None = None
    execution_event_id: str | None = None
    execution_observed_at_ms: int | None = None
    cancel_event_id: str | None = None
    canceled_at_ms: int | None = None
    quarantine_event_id: str | None = None
    quarantined_at_ms: int | None = None
    quarantine_reason: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.conditional_order_id, "CONDITIONAL_ORDER_ID_INVALID")
        _symbol(self.symbol)
        try:
            object.__setattr__(self, "side", SpotSide(self.side))
            object.__setattr__(self, "status", ConditionalStatus(self.status))
            trigger_price = positive(self.trigger_price)
        except (TypeError, ValueError) as exc:
            raise ConditionalExecutionError(
                "CONDITIONAL_INPUT_INVALID", "Conditional execution girdisi geçersiz."
            ) from exc
        object.__setattr__(self, "trigger_price", exact_text(trigger_price))
        if not isinstance(self.trigger_kind, str) or not 1 <= len(self.trigger_kind) <= 32:
            raise ConditionalExecutionError("CONDITIONAL_TRIGGER_KIND_INVALID", "Trigger türü bounded metin olmalıdır.")
        if any(ord(char) < 0x20 or ord(char) == 0x7F for char in self.trigger_kind):
            raise ConditionalExecutionError("CONDITIONAL_TRIGGER_KIND_INVALID", "Trigger türü kontrol karakteri taşıyor.")
        for value, code in (
            (self.trigger_event_id, "CONDITIONAL_TRIGGER_EVENT_INVALID"),
            (self.execution_order_id, "CONDITIONAL_EXECUTION_ORDER_ID_INVALID"),
            (self.execution_event_id, "CONDITIONAL_EXECUTION_EVENT_INVALID"),
            (self.cancel_event_id, "CONDITIONAL_CANCEL_EVENT_INVALID"),
            (self.quarantine_event_id, "CONDITIONAL_QUARANTINE_EVENT_INVALID"),
        ):
            if value is not None:
                _identifier(value, code)
        for value, code in (
            (self.observed_at_ms, "CONDITIONAL_TRIGGER_TIME_INVALID"),
            (self.execution_observed_at_ms, "CONDITIONAL_EXECUTION_TIME_INVALID"),
            (self.canceled_at_ms, "CONDITIONAL_CANCEL_TIME_INVALID"),
            (self.quarantined_at_ms, "CONDITIONAL_QUARANTINE_TIME_INVALID"),
        ):
            if value is not None and (type(value) is not int or value < 0):
                raise ConditionalExecutionError(code, "Zaman negatif olmayan integer olmalıdır.")
        if self.observed_price is not None:
            try:
                object.__setattr__(self, "observed_price", exact_text(positive(self.observed_price)))
            except ValueError as exc:
                raise ConditionalExecutionError("CONDITIONAL_OBSERVED_PRICE_INVALID", "Gözlenen fiyat geçersiz.") from exc
        if self.execution_order_type is not None and self.execution_order_type not in {"MARKET", "LIMIT"}:
            raise ConditionalExecutionError("CONDITIONAL_EXECUTION_TYPE_INVALID", "Execution order türü desteklenmiyor.")
        if self.status is ConditionalStatus.ARMED and any(
            value is not None
            for value in (self.trigger_event_id, self.observed_at_ms, self.observed_price)
        ):
            raise ConditionalExecutionError("CONDITIONAL_STATE_INVALID", "ARMED state trigger gözlemi taşıyamaz.")
        if self.status is ConditionalStatus.TRIGGERED and self.trigger_event_id is None:
            raise ConditionalExecutionError("CONDITIONAL_STATE_INVALID", "TRIGGERED state trigger kimliği taşımalıdır.")
        if self.status is ConditionalStatus.EXECUTION_IDENTIFIED and (
            self.trigger_event_id is None
            or self.execution_order_id is None
            or self.execution_order_type is None
            or self.execution_event_id is None
        ):
            raise ConditionalExecutionError("CONDITIONAL_STATE_INVALID", "Execution state kimlikleri eksik.")
        if self.execution_order_id is not None and self.status is not ConditionalStatus.EXECUTION_IDENTIFIED:
            raise ConditionalExecutionError("CONDITIONAL_STATE_INVALID", "Execution kimliği yalnız execution state’inde bulunabilir.")
        if self.status is ConditionalStatus.CANCELED and (
            self.cancel_event_id is None or self.canceled_at_ms is None
        ):
            raise ConditionalExecutionError("CONDITIONAL_STATE_INVALID", "CANCELED state confirmation kimliği taşımalıdır.")
        if self.status is ConditionalStatus.QUARANTINED and (
            self.quarantine_event_id is None
            or self.quarantined_at_ms is None
            or self.quarantine_reason is None
        ):
            raise ConditionalExecutionError("CONDITIONAL_STATE_INVALID", "QUARANTINED state evidence kimliği taşımalıdır.")

    def observe_trigger(
        self,
        *,
        trigger_event_id: str,
        observed_at_ms: int,
        observed_price: str,
    ) -> ConditionalExecutionResult:
        """Record a trigger observation; it never creates an execution or fill."""

        _identifier(trigger_event_id, "CONDITIONAL_TRIGGER_EVENT_INVALID")
        _time(observed_at_ms, "CONDITIONAL_TRIGGER_TIME_INVALID")
        try:
            price = exact_text(positive(observed_price))
        except ValueError as exc:
            raise ConditionalExecutionError("CONDITIONAL_OBSERVED_PRICE_INVALID", "Gözlenen fiyat geçersiz.") from exc
        if self.status is ConditionalStatus.TRIGGERED and (
            self.trigger_event_id,
            self.observed_at_ms,
            self.observed_price,
        ) == (trigger_event_id, observed_at_ms, price):
            return ConditionalExecutionResult(self, ConditionalExecutionOutcome.DUPLICATE)
        if self.status is not ConditionalStatus.ARMED:
            raise ConditionalExecutionError("CONDITIONAL_TRIGGER_CONFLICT", "Trigger yalnız ARMED state’inde kabul edilir.")
        return ConditionalExecutionResult(
            replace(
                self,
                status=ConditionalStatus.TRIGGERED,
                trigger_event_id=trigger_event_id,
                observed_at_ms=observed_at_ms,
                observed_price=price,
            ),
            ConditionalExecutionOutcome.ACCEPTED,
        )

    def bind_execution(
        self,
        *,
        execution_order_id: str,
        execution_order_type: str,
        execution_event_id: str,
        observed_at_ms: int,
    ) -> ConditionalExecutionResult:
        """Bind an explicit executable order identity after a trigger."""

        _identifier(execution_order_id, "CONDITIONAL_EXECUTION_ORDER_ID_INVALID")
        _identifier(execution_event_id, "CONDITIONAL_EXECUTION_EVENT_INVALID")
        _time(observed_at_ms, "CONDITIONAL_EXECUTION_TIME_INVALID")
        if execution_order_type not in {"MARKET", "LIMIT"}:
            raise ConditionalExecutionError("CONDITIONAL_EXECUTION_TYPE_INVALID", "Execution order türü desteklenmiyor.")
        if self.status is ConditionalStatus.EXECUTION_IDENTIFIED and (
            self.execution_order_id,
            self.execution_order_type,
            self.execution_event_id,
            self.execution_observed_at_ms,
        ) == (execution_order_id, execution_order_type, execution_event_id, observed_at_ms):
            return ConditionalExecutionResult(self, ConditionalExecutionOutcome.DUPLICATE)
        if self.status is not ConditionalStatus.TRIGGERED:
            if self.status is ConditionalStatus.CANCELED:
                raise ConditionalExecutionError("CONDITIONAL_CANCEL_RACE", "Cancel confirmation sonrası execution kabul edilemez.")
            if self.status is ConditionalStatus.QUARANTINED:
                raise ConditionalExecutionError("CONDITIONAL_QUARANTINED", "Quarantine sonrası execution kabul edilemez.")
            raise ConditionalExecutionError("CONDITIONAL_EXECUTION_REQUIRES_TRIGGER", "Execution kimliği yalnız trigger sonrası kabul edilir.")
        if self.observed_at_ms is not None and observed_at_ms < self.observed_at_ms:
            raise ConditionalExecutionError("CONDITIONAL_EXECUTION_OUT_OF_ORDER", "Execution gözlemi trigger’dan önce olamaz.")
        return ConditionalExecutionResult(
            replace(
                self,
                status=ConditionalStatus.EXECUTION_IDENTIFIED,
                execution_order_id=execution_order_id,
                execution_order_type=execution_order_type,
                execution_event_id=execution_event_id,
                execution_observed_at_ms=observed_at_ms,
            ),
            ConditionalExecutionOutcome.ACCEPTED,
        )

    def confirm_cancel(
        self,
        *,
        cancel_event_id: str,
        observed_at_ms: int,
    ) -> ConditionalExecutionResult:
        """Record explicit cancellation; it cannot overwrite execution identity."""

        _identifier(cancel_event_id, "CONDITIONAL_CANCEL_EVENT_INVALID")
        _time(observed_at_ms, "CONDITIONAL_CANCEL_TIME_INVALID")
        if self.status is ConditionalStatus.CANCELED and (
            self.cancel_event_id,
            self.canceled_at_ms,
        ) == (cancel_event_id, observed_at_ms):
            return ConditionalExecutionResult(self, ConditionalExecutionOutcome.DUPLICATE)
        if self.status is ConditionalStatus.EXECUTION_IDENTIFIED:
            raise ConditionalExecutionError("CONDITIONAL_CANCEL_RACE", "Execution kimliği sonrası cancel sessizce onaylanamaz.")
        if self.status in {ConditionalStatus.QUARANTINED}:
            raise ConditionalExecutionError("CONDITIONAL_QUARANTINED", "Quarantine sonrası cancel confirmation kabul edilmez.")
        if self.status not in {ConditionalStatus.ARMED, ConditionalStatus.TRIGGERED}:
            raise ConditionalExecutionError("CONDITIONAL_CANCEL_INVALID", "Cancel yalnız bekleyen conditional state’inde kabul edilir.")
        if self.observed_at_ms is not None and observed_at_ms < self.observed_at_ms:
            raise ConditionalExecutionError("CONDITIONAL_CANCEL_OUT_OF_ORDER", "Cancel trigger gözleminden önce olamaz.")
        return ConditionalExecutionResult(
            replace(self, status=ConditionalStatus.CANCELED, cancel_event_id=cancel_event_id, canceled_at_ms=observed_at_ms),
            ConditionalExecutionOutcome.ACCEPTED,
        )

    def quarantine(
        self,
        *,
        evidence_event_id: str,
        observed_at_ms: int,
        reason: str,
    ) -> ConditionalExecutionResult:
        """Quarantine gap/stale/conflict evidence without inventing execution."""

        _identifier(evidence_event_id, "CONDITIONAL_QUARANTINE_EVENT_INVALID")
        _time(observed_at_ms, "CONDITIONAL_QUARANTINE_TIME_INVALID")
        if reason not in {"GAP", "STALE", "CONFLICT"}:
            raise ConditionalExecutionError("CONDITIONAL_QUARANTINE_REASON_INVALID", "Quarantine nedeni desteklenmiyor.")
        if self.status is ConditionalStatus.QUARANTINED and (
            self.quarantine_event_id,
            self.quarantined_at_ms,
            self.quarantine_reason,
        ) == (evidence_event_id, observed_at_ms, reason):
            return ConditionalExecutionResult(self, ConditionalExecutionOutcome.DUPLICATE)
        if self.status is ConditionalStatus.CANCELED:
            raise ConditionalExecutionError("CONDITIONAL_CANCEL_RACE", "Canceled state quarantine ile değiştirilemez.")
        if self.status is ConditionalStatus.EXECUTION_IDENTIFIED:
            raise ConditionalExecutionError("CONDITIONAL_EXECUTION_CONFLICT", "Execution kimliği bağlandıktan sonra quarantine yeni execution state’i üretemez.")
        return ConditionalExecutionResult(
            replace(
                self,
                status=ConditionalStatus.QUARANTINED,
                quarantine_event_id=evidence_event_id,
                quarantined_at_ms=observed_at_ms,
                quarantine_reason=reason,
            ),
            ConditionalExecutionOutcome.ACCEPTED,
        )


def create_conditional_execution(
    *,
    conditional_order_id: str,
    symbol: str,
    side: SpotSide,
    trigger_kind: str,
    trigger_price: str,
) -> ConditionalExecution:
    """Create an armed, venue-neutral conditional observation projection."""

    return ConditionalExecution(
        conditional_order_id=conditional_order_id,
        symbol=symbol,
        side=side,
        trigger_kind=trigger_kind,
        trigger_price=trigger_price,
    )


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)


def _identifier(value: object, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ConditionalExecutionError(code, "Kimlik geçersiz.")


def _symbol(value: object) -> None:
    if not isinstance(value, str) or not 1 <= len(value) <= 32 or value != value.strip():
        raise ConditionalExecutionError("CONDITIONAL_SYMBOL_INVALID", "Symbol bounded metin olmalıdır.")
    if any(ord(char) < 0x20 or ord(char) == 0x7F for char in value):
        raise ConditionalExecutionError("CONDITIONAL_SYMBOL_INVALID", "Symbol kontrol karakteri taşıyor.")


def _time(value: object, code: str) -> None:
    if type(value) is not int or value < 0:
        raise ConditionalExecutionError(code, "Zaman negatif olmayan integer olmalıdır.")
