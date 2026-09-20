"""Diagnose the real testnet order-status lookup used by Faz 3.2 REST catch-up.

There is no live order-placement flow yet (Faz 3.5), so there is no genuine
interrupted attempt to catch up on. This script instead validates the query
mechanics themselves against the real venue: pass a client order ID that was
never placed (any short string) to confirm the -2013/NOT_FOUND path, or a
real venue order ID (from an order you placed manually on testnet.binance.vision)
to confirm the FOUND path and the exact response field names this code relies on.

Usage:
    uv run --frozen python tools/run_order_status_lookup_diagnostic.py \
        <credential_id> <symbol> --client-order-id <id>
    uv run --frozen python tools/run_order_status_lookup_diagnostic.py \
        <credential_id> <symbol> --order-id <venue_order_id>

Prints only the redacted OrderLookup result — no credential/secret material.
"""

import argparse
import asyncio
import time

from dcabot.application.reconciliation import OrderLookup
from dcabot.application.signed_request import Clock
from dcabot.application.windows_credential_provider import WindowsCredentialManagerProvider
from dcabot.data_adapters.binance_testnet_user_stream import (
    query_binance_testnet_order_status,
    query_binance_testnet_order_status_by_client_id,
)


class WallClock:
    def now_ms(self) -> int:
        return int(time.time() * 1000)


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("credential_id")
    parser.add_argument("symbol")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--client-order-id")
    group.add_argument("--order-id", type=int)
    args = parser.parse_args()

    provider = WindowsCredentialManagerProvider()
    clock: Clock = WallClock()

    if args.client_order_id is not None:
        result: OrderLookup = await query_binance_testnet_order_status_by_client_id(
            args.credential_id, args.symbol, args.client_order_id, provider=provider, clock=clock
        )
    else:
        result = await query_binance_testnet_order_status(
            args.credential_id, args.symbol, args.order_id, provider=provider, clock=clock
        )

    print(f"kind={result.kind.value} venue_order_id={result.venue_order_id}")


if __name__ == "__main__":
    asyncio.run(main())
