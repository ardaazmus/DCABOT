"""Offline-only sender boundary with explicit ambiguous-result handling."""

from dataclasses import dataclass
from typing import Mapping, Protocol

from dcabot.application.order_attempt import (
    AttemptState,
    OrderAttempt,
    OrderAttemptError,
    request_fingerprint,
)
from dcabot.persistence.attempt_store import AttemptStore


class AmbiguousTransportError(RuntimeError):
    """The transport cannot prove whether the venue accepted the request."""


class DefinitiveTransportError(RuntimeError):
    """The transport has a definitive non-acceptance classification."""

    def __init__(self, code: str, _detail: str = "") -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class TransportAccepted:
    """Acknowledgement only; it is not a fill or economic result."""

    venue_order_id: int | None = None


class OrderTransport(Protocol):
    """Offline/fake transport contract used before any real venue adapter exists."""

    def send(
        self, attempt: OrderAttempt, payload: Mapping[str, object]
    ) -> TransportAccepted: ...


class OrderSender:
    """Coordinate durable attempt transitions without retries or economic logic."""

    def __init__(self, store: AttemptStore, *, clock_us) -> None:
        self.store = store
        self.clock_us = clock_us

    def send(
        self,
        attempt_id: str,
        payload: Mapping[str, object],
        transport: OrderTransport,
    ) -> OrderAttempt:
        """Send only after persistence; ambiguity always becomes UNKNOWN."""

        current = self.store.get(attempt_id)
        if current.state is AttemptState.UNKNOWN:
            raise OrderAttemptError(
                "ATTEMPT_RECONCILIATION_REQUIRED", "UNKNOWN attempt körlemesine tekrar gönderilemez."
            )
        if current.state is not AttemptState.PERSISTED:
            raise OrderAttemptError(
                "ATTEMPT_NOT_PERSISTED", "Network mutation öncesi attempt PERSISTED olmalıdır."
            )
        try:
            fingerprint = request_fingerprint(payload)
        except OrderAttemptError:
            raise
        if fingerprint != current.request_fingerprint_sha256:
            raise OrderAttemptError(
                "ATTEMPT_PAYLOAD_MISMATCH", "Gönderim payload’ı hazırlanan attempt ile eşleşmiyor."
            )

        sending = self.store.mark_sending(attempt_id, now_us=self.clock_us())
        try:
            result = transport.send(sending, payload)
        except AmbiguousTransportError:
            return self.store.mark_unknown(
                attempt_id,
                now_us=self.clock_us(),
                reason="TRANSPORT_AMBIGUOUS",
            )
        except DefinitiveTransportError as exc:
            return self.store.mark_rejected(
                attempt_id,
                now_us=self.clock_us(),
                reason=exc.code,
            )
        if not isinstance(result, TransportAccepted):
            return self.store.mark_unknown(
                attempt_id,
                now_us=self.clock_us(),
                reason="TRANSPORT_RESULT_INVALID",
            )
        return self.store.mark_acknowledged(
            attempt_id,
            now_us=self.clock_us(),
            venue_order_id=result.venue_order_id,
        )
