"""Telegram fan-out worker: poll the event log on an interval, never crash the app.

Owns one daemon thread. Each tick builds the current token loader and
runs `TelegramNotifier.poll_once`; every exception is swallowed into
the settings' last-error slot (via the notifier's own handling or a
`TELEGRAM_WORKER_FAILED` fallback) so a Telegram outage never affects
trading or the API.
"""

from dataclasses import dataclass
from threading import Event, Lock, Thread
from typing import Callable
import traceback

from dcabot.application.telegram_notify import TelegramNotifier


@dataclass(frozen=True)
class TelegramWorkerDeps:
    settings: object
    vault: object | None
    send_message: Callable[[str, str, str], int]
    log: object
    interval_seconds: float = 15.0


class TelegramWorker:
    def __init__(self, deps: TelegramWorkerDeps) -> None:
        self._deps = deps
        self._stop = Event()
        self._lock = Lock()
        self._thread: Thread | None = None
        self._running = False

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._stop.clear()
            self._thread = Thread(target=self._loop, name="telegram-fanout", daemon=True)
            self._thread.start()
            self._running = True

    def stop(self) -> None:
        with self._lock:
            thread = self._thread
            self._running = False
        self._stop.set()
        if thread is not None:
            thread.join(timeout=5)

    def tick(self) -> None:
        """One fan-out pass; safe to call directly in tests and startup."""
        from dcabot.server.v2_notifications_telegram import TELEGRAM_CREDENTIAL_ID

        deps = self._deps

        def load_token() -> str:
            assert deps.vault is not None
            material = deps.vault.load(TELEGRAM_CREDENTIAL_ID)  # type: ignore[attr-defined]
            return material.secret.decode("utf-8")

        try:
            TelegramNotifier(
                send_message=deps.send_message,
                load_token=load_token,
                settings=deps.settings,
                log=deps.log,
            ).poll_once()
        except Exception:
            traceback.print_exc()
            try:
                deps.settings.set_telegram_error("TELEGRAM_WORKER_FAILED")  # type: ignore[attr-defined]
            except Exception:
                traceback.print_exc()

    def _loop(self) -> None:
        while not self._stop.wait(self._deps.interval_seconds):
            self.tick()
