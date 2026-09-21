"""Run one real DCA deal (base + safety + TP) on Binance Spot Testnet.

This is the ONLY way to produce evidence_scope=REAL_TESTNET for Faz 3.7
(docs/YOL_HARITASI.md). It reuses the exact core reducer
(dcabot.domain.engine.State/apply/decision) Faz 2's historical simulation
already uses, and every real order goes through Faz 3.4's mutation gate
(docs/KARARLAR.md, 2026-09-21) exactly as Faz 3.5/3.6 do.

Usage:
    $env:DCABOT_TRADING_ENABLED = 'true'
    uv run --frozen python tools/run_testnet_dca_deal.py \
        <credential_id> <symbol> <base_asset> \
        --base-qty 0.001 --safety-qty 0.001 --safety-count 1 \
        --deviation 0.05 --take-profit 0.02

Each real order (base, each triggered safety, the final TP) asks for a
separate typed "EVET" before it is sent -- nothing here is automatic. The
loop itself (checking price/fills and deciding what's next) is read-only
and does not need confirmation.

Known limitation (deliberate, not an oversight): the DCA session's State
lives only in this process's memory. A crash mid-deal loses the session
(not the underlying venue orders -- recover_stuck_attempts still protects
those at the attempt level), and this run cannot be resumed; a fresh run
starts a new deal. A durable live-deal store is future work.
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from tempfile import gettempdir
from urllib.request import urlopen

from dcabot.application.instrument_filters import InstrumentFilterProfile
from dcabot.application.signed_request import Clock
from dcabot.application.testnet_dca_session import (
    TestnetDcaSessionError,
    apply_mark,
    build_live_config,
    new_session,
    place_next_action,
    propose_next_action,
    sync_order_fills,
)
from dcabot.application.testnet_order_execution import TestnetOrderExecutionError, recover_stuck_attempts
from dcabot.data_adapters.binance_testnet_account import fetch_binance_testnet_account
from dcabot.data_adapters.binance_testnet_order_execution import trading_kill_switch_enabled
from dcabot.data_adapters.binance_testnet_public import fetch_binance_testnet_exchange_info
from dcabot.application.windows_credential_provider import WindowsCredentialManagerProvider
from dcabot.domain.numbers import exact_text, number
from dcabot.persistence.attempt_store import AttemptStore


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
        raise SystemExit("Gerekli filtreler exchangeInfo'da bulunamadi.")
    min_notional = notional_filter.get("minNotional") or notional_filter.get("notional")
    return InstrumentFilterProfile(
        profile_id=f"{symbol.lower()}-dca",
        qty_step=lot_filter["stepSize"],
        price_tick=price_filter["tickSize"],
        min_qty=lot_filter["minQty"],
        min_notional=min_notional,
    )


def _fetch_ticker_price(symbol: str) -> str:
    with urlopen(
        f"https://testnet.binance.vision/api/v3/ticker/price?symbol={symbol}", timeout=10
    ) as response:
        return json.loads(response.read().decode("utf-8"))["price"]


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("credential_id")
    parser.add_argument("symbol")
    parser.add_argument("base_asset")
    parser.add_argument("--base-qty", required=True)
    parser.add_argument("--safety-qty", required=True)
    parser.add_argument("--safety-count", type=int, required=True)
    parser.add_argument("--deviation", required=True)
    parser.add_argument("--take-profit", required=True)
    args = parser.parse_args()

    provider = WindowsCredentialManagerProvider()
    clock: Clock = WallClock()

    print("Hesap ve exchangeInfo okunuyor (salt okunur)...")
    account = fetch_binance_testnet_account(args.credential_id, provider=provider, clock=clock)
    snapshot = fetch_binance_testnet_exchange_info(args.symbol)
    profile = _filter_profile(args.symbol, snapshot.filters)
    config = build_live_config(
        profile,
        symbol=args.symbol,
        base_asset=args.base_asset,
        base_qty=args.base_qty,
        safety_qty=args.safety_qty,
        safety_count=args.safety_count,
        deviation=args.deviation,
        take_profit=args.take_profit,
        target_quote="0",
        initial_equity="1000",
        max_entry_notional=str(MAX_ORDER_NOTIONAL_CAP),
        minimum_equity="10",
    )
    print(f"Hesap tipi: {account.account_type} | trade acik: {account.can_trade}")

    if not trading_kill_switch_enabled():
        print("DCABOT_TRADING_ENABLED 'true' degil -- yalnizca goruntuleme yapildi, hicbir emir gonderilmeyecek.")
        return

    store_path = Path(gettempdir()) / "dcabot_single_testnet_order_attempts.sqlite"
    with AttemptStore(store_path) as store:
        recovered = await recover_stuck_attempts(
            store=store, credential_id=args.credential_id, provider=provider, clock=clock,
            now_us=int(time.time() * 1_000_000),
        )
        for attempt in recovered:
            print(f"Onceki oturumdan kalan attempt kurtarildi: {attempt.attempt_id} -> {attempt.state.value}")

        price = _fetch_ticker_price(args.symbol)
        session = new_session(config, args.symbol)
        session = apply_mark(session, price)
        print(f"Guncel mark: {price}")

        role_sequence = 0
        while True:
            for binding in session.bindings:
                order = session.state.orders.get(binding.local_order_id)
                if order is not None and not order.complete:
                    session = await sync_order_fills(
                        session, binding.role, credential_id=args.credential_id, provider=provider, clock=clock
                    )

            action = propose_next_action(session)
            if action is None:
                position_qty = session.state.position.qty
                if position_qty == 0 and session.bindings and any(
                    b.role == "EXIT" for b in session.bindings
                ):
                    print("Deal tamamlandi: pozisyon kapandi.")
                    break
                mark_text = exact_text(session.state.mark) if session.state.mark is not None else "?"
                print(f"Su anda aksiyon yok. Pozisyon: {exact_text(position_qty)}. Mark: {mark_text}")
                answer = input("Fiyati/dolumlari kontrol et [k], cik [q]: ").strip().lower()
                if answer == "q":
                    break
                price = _fetch_ticker_price(args.symbol)
                session = apply_mark(session, price)
                print(f"Guncel mark: {price}")
                continue

            role, qty = action
            print(f"Sirada: {role} {exact_text(qty)} {args.symbol}")
            if not _confirm(f"Bu {role} emrini GERCEKTEN gondermek istiyor musun?"):
                print("Bu adim atlandi (onaylanmadi).")
                answer = input("Fiyati/dolumlari kontrol et [k], cik [q]: ").strip().lower()
                if answer == "q":
                    break
                price = _fetch_ticker_price(args.symbol)
                session = apply_mark(session, price)
                continue

            role_sequence += 1
            attempt_id = f"dca-{role.lower().replace(':', '-')}-{int(time.time())}-{role_sequence}"
            try:
                session, result = await place_next_action(
                    session,
                    role=role,
                    qty=qty,
                    store=store,
                    attempt_id=attempt_id,
                    credential_id=args.credential_id,
                    provider=provider,
                    clock=clock,
                    now_us=int(time.time() * 1_000_000),
                    max_entry_notional=MAX_ORDER_NOTIONAL_CAP,
                    capability_snapshot_hash=account.response_sha256,
                )
            except (TestnetOrderExecutionError, TestnetDcaSessionError) as exc:
                print(f"Emir gonderilemedi (fail-closed): {exc}", file=sys.stderr)
                raise SystemExit(1) from exc
            print(f"Gonderildi: {role} venue_order_id={result.placed.order_id} status={result.placed.status}")


if __name__ == "__main__":
    asyncio.run(main())
