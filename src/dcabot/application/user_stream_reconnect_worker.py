"""Bounded reconnect worker for the read-only Binance Testnet User Data Stream.

Wraps BinanceTestnetUserDataStream (single bounded connection, no reconnect
by its own design) with ReconciliationCoordinator (offline connection/event
state machine) to survive a real disconnect: detect it, back off, reconnect,
and resume feeding events into the coordinator. The worker never mutates,
never signs a new kind of request, and never retries without bound.

Reaching ConnectionState.SYNCED requires an authoritative REST snapshot
(Faz 3.2, not implemented here) — this worker only drives the connect /
disconnect / reconnect / gap-detection arc that Faz 3.1 scopes.
"""

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable, Protocol

from dcabot.application.reconciliation import ConnectionState, EventDecision, ReconciliationCoordinator
from dcabot.data_adapters.binance_testnet_user_stream import (
    BinanceTestnetUserDataStream,
    BinanceTestnetUserStreamError,
)


DEFAULT_BACKOFF_SCHEDULE_SECONDS: tuple[float, ...] = (1, 2, 4, 8, 16)
DEFAULT_MAX_RECONNECT_ATTEMPTS = 5


class ReconnectWorkerError(RuntimeError):
    """Raised when the reconnect worker fails closed instead of retrying forever."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class Sleeper(Protocol):
    def __call__(self, seconds: float) -> Awaitable[None]: ...


StreamFactory = Callable[[], BinanceTestnetUserDataStream]


@dataclass(frozen=True, slots=True)
class ReconnectWorkerEvent:
    """One observable transition, for callers that want live evidence/logging."""

    kind: str
    connection_state: ConnectionState
    detail: str = ""


class UserStreamReconnectWorker:
    """Drive one User Data Stream through disconnect/backoff/reconnect/gap detection."""

    __slots__ = (
        "_stream_factory",
        "_coordinator",
        "_sleep",
        "_backoff_schedule",
        "_max_attempts",
        "_on_transition",
    )

    def __init__(
        self,
        stream_factory: StreamFactory,
        *,
        coordinator: ReconciliationCoordinator,
        sleep: Sleeper = asyncio.sleep,
        backoff_schedule_seconds: tuple[float, ...] = DEFAULT_BACKOFF_SCHEDULE_SECONDS,
        max_attempts: int = DEFAULT_MAX_RECONNECT_ATTEMPTS,
        on_transition: Callable[[ReconnectWorkerEvent], None] | None = None,
    ) -> None:
        if not callable(stream_factory):
            raise ReconnectWorkerError(
                "WORKER_STREAM_FACTORY_INVALID", "stream_factory çağrılabilir olmalıdır."
            )
        if not isinstance(coordinator, ReconciliationCoordinator):
            raise ReconnectWorkerError(
                "WORKER_COORDINATOR_INVALID", "Geçerli bir ReconciliationCoordinator gerekir."
            )
        if not callable(sleep):
            raise ReconnectWorkerError("WORKER_SLEEP_INVALID", "sleep çağrılabilir olmalıdır.")
        if (
            not isinstance(backoff_schedule_seconds, tuple)
            or not backoff_schedule_seconds
            or any(
                type(value) not in (int, float) or value <= 0
                for value in backoff_schedule_seconds
            )
        ):
            raise ReconnectWorkerError(
                "WORKER_BACKOFF_INVALID",
                "Backoff programı pozitif değerler içeren dolu bir tuple olmalıdır.",
            )
        if type(max_attempts) is not int or max_attempts < 1:
            raise ReconnectWorkerError(
                "WORKER_MAX_ATTEMPTS_INVALID", "max_attempts pozitif integer olmalıdır."
            )
        self._stream_factory = stream_factory
        self._coordinator = coordinator
        self._sleep = sleep
        self._backoff_schedule = backoff_schedule_seconds
        self._max_attempts = max_attempts
        self._on_transition = on_transition

    async def run(self, *, max_events: int | None = None) -> ConnectionState:
        """Connect, receive events, reconnect on drop; return the final state.

        ``max_events`` bounds the loop so tests (and a caller that wants one
        bounded pass rather than an infinite live loop) can drive it
        deterministically. ``None`` runs until a fatal error or the stream
        factory/socket raises ``StopIteration``-style exhaustion in tests.
        """

        attempts = 0
        events_received = 0
        connected_once = False
        stream: BinanceTestnetUserDataStream | None = None
        self._coordinator.begin_connect()
        while True:
            if stream is None:
                try:
                    stream = self._stream_factory()
                    await stream.connect()
                except BinanceTestnetUserStreamError as exc:
                    stream = None
                    attempts = await self._register_failure(attempts, exc)
                    continue
                if connected_once:
                    self._coordinator.reconnect()
                    self._emit("RECONNECTED", f"attempt={attempts}")
                else:
                    self._coordinator.public_snapshot_ready()
                    self._emit("CONNECTED")
                connected_once = True
                attempts = 0
            try:
                event = await stream.recv_execution_report()
            except BinanceTestnetUserStreamError as exc:
                stream = None
                attempts = await self._register_failure(attempts, exc)
                continue
            decision = self._coordinator.accept_event(event)
            events_received += 1
            self._emit("EVENT", decision.value)
            if max_events is not None and events_received >= max_events:
                return self._coordinator.state

    async def _register_failure(self, attempts: int, exc: BinanceTestnetUserStreamError) -> int:
        """Count one connect-or-recv drop, back off, and fail closed past the bound.

        Both failure sites (an initial/reconnect ``connect()`` and a live
        ``recv()``) route through here so a socket that connects but then
        fails on every ``recv()`` cannot spin without bound or backoff.
        """

        attempts += 1
        self._coordinator.on_disconnect()
        self._emit("DISCONNECTED", str(exc))
        if attempts > self._max_attempts:
            self._emit("FAILED", "max_reconnect_attempts_exceeded")
            raise ReconnectWorkerError(
                "WORKER_RECONNECT_EXHAUSTED", "Bağlantı yeniden deneme sınırı aşıldı."
            ) from exc
        backoff = self._backoff_schedule[min(attempts - 1, len(self._backoff_schedule) - 1)]
        self._emit("RECONNECTING", f"attempt={attempts} backoff={backoff}")
        await self._sleep(backoff)
        return attempts

    def _emit(self, kind: str, detail: str = "") -> None:
        if self._on_transition is not None:
            self._on_transition(ReconnectWorkerEvent(kind, self._coordinator.state, detail))
