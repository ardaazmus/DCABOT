"""Place, check, and cancel exactly one real Binance Spot Testnet LIMIT order.

This is the ONLY way to produce evidence_scope=REAL_TESTNET for Faz 3.5
(docs/YOL_HARITASI.md). Every rule from Faz 3.4's mutation gate
(docs/KARARLAR.md, 2026-09-21) is enforced by
dcabot.application.testnet_order_execution -- this script only adds the
execution-time confirmation prompts the gate requires from its caller.

Usage:
    $env:DCABOT_TRADING_ENABLED = 'true'
    uv run --frozen python tools/run_single_testnet_order.py \
        <credential_id> <symbol> <BUY|SELL> <quantity> <price>

Example (fake numbers, always check the current testnet BTCUSDT price
before choosing a price that would fill or sit far off-market):
    uv run --frozen python tools/run_single_testnet_order.py \
        testnet-readonly BTCUSDT BUY 0.001 20000

The kill-switch (DCABOT_TRADING_ENABLED) must be exactly "true" or nothing
is sent. Without it set, this script still fetches account/exchange info
(read-only) so you can see what WOULD happen, then refuses to place.

Every mutating step asks for a typed "EVET" before it runs. Nothing here
is automatic.
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path
from tempfile import gettempdir

from dcabot.application.instrument_filters import InstrumentFilterProfile
from dcabot.application.signed_request import Clock
from dcabot.application.testnet_order_execution import (
    TestnetOrderExecutionError,
    cancel_gated_testnet_order,
    place_gated_testnet_limit_order,
)
from dcabot.data_adapters.binance_testnet_account import fetch_binance_testnet_account
from dcabot.data_adapters.binance_testnet_order_execution import trading_kill_switch_enabled
from dcabot.data_adapters.binance_testnet_public import fetch_binance_testnet_exchange_info
from dcabot.data_adapters.binance_testnet_user_stream import query_binance_testnet_order_status
from dcabot.application.windows_credential_provider import WindowsCredentialManagerProvider
from dcabot.domain.numbers import number
from dcabot.persistence.attempt_store import AttemptStore


# Deliberately small and fixed for this single-order evidence script -- not
# derived from any bot config, since this tool exists only to prove the
# mutation gate end to end, not to run a strategy.
MAX_ORDER_NOTIONAL_CAP = number("50")


class WallClock:
    def now_ms(self) -> int:
        return int(time.time() * 1000)


def _confirm(prompt: str) -> bool:
    typed = input(f"{prompt} (devam etmek icin tam olarak EVET yaz): ")
    return typed.strip() == "EVET"


def _filter_profile(symbol: str, filters: list[dict[str, str]]) -> InstrumentFilterProfile:
    by_type = {item.get("filterType"): item for item in filters}
    price_filter = by_type.get("PRICE_FILTER")
    lot_filter = by_type.get("LOT_SIZE")
    notional_filter = by_type.get("MIN_NOTIONAL") or by_type.get("NOTIONAL")
    if price_filter is None or lot_filter is None or notional_filter is None:
        raise SystemExit("Gerekli filtreler (PRICE_FILTER/LOT_SIZE/MIN_NOTIONAL) exchangeInfo'da bulunamadi.")
    min_notional = notional_filter.get("minNotional") or notional_filter.get("notional")
    return InstrumentFilterProfile(
        profile_id=f"{symbol.lower()}-live",
        qty_step=lot_filter["stepSize"],
        price_tick=price_filter["tickSize"],
        min_qty=lot_filter["minQty"],
        min_notional=min_notional,
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("credential_id")
    parser.add_argument("symbol")
    parser.add_argument("side", choices=["BUY", "SELL"])
    parser.add_argument("quantity")
    parser.add_argument("price")
    args = parser.parse_args()

    provider = WindowsCredentialManagerProvider()
    clock: Clock = WallClock()

    print("Hesap ve exchangeInfo okunuyor (salt okunur)...")
    account = fetch_binance_testnet_account(args.credential_id, provider=provider, clock=clock)
    snapshot = fetch_binance_testnet_exchange_info(args.symbol)
    profile = _filter_profile(args.symbol, snapshot.filters)

    notional = str(number(args.quantity) * number(args.price))
    print(f"Hesap tipi: {account.account_type} | trade acik: {account.can_trade}")
    print(f"Emir: {args.side} {args.quantity} {args.symbol} @ {args.price} (yaklasik notional {notional})")

    if not trading_kill_switch_enabled():
        print("DCABOT_TRADING_ENABLED 'true' degil -- yalnizca goruntuleme yapildi, hicbir emir gonderilmeyecek.")
        return

    if not _confirm("Bu LIMIT emri GERCEKTEN testnet'e gondermek istiyor musun?"):
        print("Iptal edildi (onaylanmadi). Hicbir istek gonderilmedi.")
        return

    store_path = Path(gettempdir()) / "dcabot_single_testnet_order_attempts.sqlite"
    with AttemptStore(store_path) as store:
        attempt_id = f"single-order-{int(time.time())}"
        now_us = int(time.time() * 1_000_000)
        try:
            result = await place_gated_testnet_limit_order(
                store=store,
                run_id="single-testnet-order",
                attempt_id=attempt_id,
                client_order_id=attempt_id,
                symbol=args.symbol,
                side=args.side,
                quantity=args.quantity,
                price=args.price,
                filter_profile=profile,
                max_entry_notional=MAX_ORDER_NOTIONAL_CAP,
                capability_snapshot_hash=account.response_sha256,
                confirmed=True,
                credential_id=args.credential_id,
                provider=provider,
                clock=clock,
                now_us=now_us,
            )
        except TestnetOrderExecutionError as exc:
            print(f"Emir gonderilemedi (fail-closed): {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

        print(f"Gonderildi. venue_order_id={result.placed.order_id} status={result.placed.status}")

        print("Emir durumu sorgulaniyor (salt okunur)...")
        lookup = await query_binance_testnet_order_status(
            args.credential_id, args.symbol, result.placed.order_id, provider=provider, clock=clock
        )
        print(f"Sorgu sonucu: {lookup.kind.value}")

        if _confirm("Bu emri simdi iptal etmek istiyor musun?"):
            cancelled = await cancel_gated_testnet_order(
                symbol=args.symbol,
                order_id=result.placed.order_id,
                confirmed=True,
                credential_id=args.credential_id,
                provider=provider,
                clock=clock,
            )
            print(f"Iptal edildi. status={cancelled.status}")
        else:
            print("Iptal edilmedi; emir testnet'te acik kalabilir. Elle takip et.")


if __name__ == "__main__":
    asyncio.run(main())
