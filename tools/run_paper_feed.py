"""Fetch real Binance Spot public trades (read-only, credential-free proof).

Usage: uv run --frozen python tools/run_paper_feed.py [SYMBOL] [LIMIT]
Prints count, first/last price, and event ids. No credentials, no orders.
"""

import sys
import time

sys.path.insert(0, "src")

from dcabot.data_adapters.binance_public import BinanceTimeUnit
from dcabot.data_adapters.binance_public_transport import (
    fetch_binance_public_trades,
)


def main(argv: list[str]) -> int:
    symbol = argv[1] if len(argv) > 1 else "BTCUSDT"
    limit = int(argv[2]) if len(argv) > 2 else 5
    now_us = time.time_ns() // 1000
    observations = fetch_binance_public_trades(
        symbol,
        limit=limit,
        allowed_symbols=frozenset({symbol}),
        receive_time_us=now_us,
        processing_time_us=now_us,
        time_unit=BinanceTimeUnit.MILLISECONDS,
    )
    print(f"symbol={symbol} count={len(observations)}")
    for obs in observations:
        print(
            f"  event={obs.event_id} price={obs.price} qty={obs.quantity} "
            f"time_us={obs.event_time_us}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
