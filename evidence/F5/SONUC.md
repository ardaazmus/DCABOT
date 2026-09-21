# Faz 5 SONUC — Futures grid projeksiyon API+UI (likidasyonsuz)

Kutu: LCR-12 venue liquidation NO-GO (docs/KARARLAR.md). Bu faz yalniz
VERIFIED kalan kismi implemente eder: grid/PnL/trailing/funding projeksiyonu.
Reverse/Infinity DEFERRED (standart model yok). Futures mutation PLAN.

## Kapsam
- 5 endpoint: grid/levels, position/pnl, trailing/arm, trailing/observe, funding.
- FuturesPanel: 4 form + sonuc gosterimi, App bolumune bagli.
- Tum hesap exact (Decimal/Fraction); UI sayi hesabi yapmaz.

## Dogrulama
- `uv run --frozen python tools/run_checks.py`: 1107/1107 PASS.
- `npx tsc -b`: temiz. `npx vitest run`: 66/66 PASS (FuturesPanel 3).
- API testleri (`tests/api/test_futures_*`): 12/12 PASS.
- Canli smoke (127.0.0.1:8009): levels 90/95/100/105/110, pnl 10,
  trailing ACTIVE 103/98, funding -0.021 — F5_SMOKE_PASS.

## Sinirlar
- Likidasyon yetkisi yok (`isolated_liquidation` ESTIMATE_ONLY).
- Emir gonderimi yok; tum cikti projeksiyon/snapshot.
- `gate F5`: PASS.
