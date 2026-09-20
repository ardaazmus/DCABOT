"""Run the read-only Binance Spot Testnet User Data Stream reconnect worker live.

This is the ONLY way to produce evidence_scope=REAL_TESTNET for Faz 3.1
(docs/YOL_HARITASI.md). It connects to the real testnet with a credential
already stored locally via tools/configure_testnet_credential.py, prints
every connection-state transition, and never signs a mutating request.

Usage:
    uv run --frozen python tools/run_user_stream_reconnect_worker.py <credential_id>

To observe the reconnect/gap arc: start this, then disable and re-enable
your network connection. Watch for DISCONNECTED -> RECONNECTING ->
RECONNECTED in the printed transitions; a real GAP requires an actual
missed event during the outage and is not guaranteed on every run.

Stop with Ctrl+C. This script never writes to any local store; it only
prints redacted connection-state transitions to stdout.
"""

import argparse
import asyncio
import sys
import time

from dcabot.application.reconciliation import ReconciliationCoordinator
from dcabot.application.signed_request import Clock
from dcabot.application.user_stream_reconnect_worker import (
    ReconnectWorkerError,
    ReconnectWorkerEvent,
    UserStreamReconnectWorker,
)
from dcabot.application.windows_credential_provider import WindowsCredentialManagerProvider
from dcabot.data_adapters.binance_testnet_user_stream import BinanceTestnetUserDataStream


class WallClock:
    def now_ms(self) -> int:
        return int(time.time() * 1000)


def _print_transition(event: ReconnectWorkerEvent) -> None:
    print(f"[{event.connection_state.value}] {event.kind} {event.detail}".rstrip(), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the read-only testnet User Data Stream reconnect worker against the real venue."
    )
    parser.add_argument(
        "credential_id",
        help="Local credential identity previously stored with tools/configure_testnet_credential.py",
    )
    args = parser.parse_args()

    provider = WindowsCredentialManagerProvider()
    clock: Clock = WallClock()
    coordinator = ReconciliationCoordinator()

    def stream_factory() -> BinanceTestnetUserDataStream:
        return BinanceTestnetUserDataStream(args.credential_id, provider=provider, clock=clock)

    worker = UserStreamReconnectWorker(
        stream_factory, coordinator=coordinator, on_transition=_print_transition
    )

    print("Read-only testnet User Data Stream reconnect worker basliyor. Ctrl+C ile durdur.")
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        print("Durduruldu (Ctrl+C).")
    except ReconnectWorkerError as exc:
        print(f"Bagli kalamadi (fail-closed): {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
