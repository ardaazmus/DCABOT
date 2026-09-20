# Durum — 2026-09-20

Aktif faz: Faz 1 — kod borcu (Faz 0 temizlik uygulandı). Dal: `codex/latest-state-2026-09-20`.
Doğrulanan: Python 3.13 + `uv sync --frozen` ile tam checker 869/869 PASS (2 skip); frontend `tsc -b` temiz, vitest 12/12 PASS.
Eksenler: implementation=IN_PROGRESS · verification=PASS · evidence_scope=LOCAL_INTEGRATION · review=NOT_RUN (büyük faz bağımsız incelemesi yapılmadı) · deployment=NOT_DEPLOYED

## Kodda mevcut (arayüz uçtan uca elle denenmedi — Faz 2.1)
- Yerel arayüz (FastAPI `127.0.0.1:8000` + React/Vite `5173`): veri seti kaydı, sınırlı public indirme (Binance BTCUSDT 1h), kalite raporu, OHLC grafik verisi, tarihsel profil seçimi, doğrulama ve kapalı-bar simülasyon (≤ 1000 bar), sonucu SQLite'a kaydetme, kayıtlı run listesi/detayı.
- CLI `tools/bot.py`: demo, init/replay/status/audit, preview. Sentetik tick, tick başına en çok bir emir, anında tam dolum.
- Çekirdek: exact Decimal/Fraction ladder, net TP, drawdown; idempotent SQLite kayıtları.
- Offline sözleşmeler (`src/dcabot/application`, `persistence`): Futures DCA/Grid, Spot Grid, two-leg, rebalancing, sinyal/şablon kapıları, OOS/stress lineage, venue event reconciliation ve durable replay journal. Arayüze bağlandıkları doğrulanmadı.
- P2 salt-okunur Binance testnet sınırı: public, account, user-stream adaptörleri.

## Bilinen sınırlar
- Signed REST/WS emir, mutation ve mainnet: NO-GO. Gerçek reconnect worker ve REST catch-up yok.
- Simülasyon: OHLC intrabar sırası `INDETERMINATE`; gerçek likidite modeli yok.
- P1'de eksik: kapsamlı ekonomik metrikler, reproduce/compare, etkileşimli marker, stress ekonomik modeli.
- API tek worker'a bağlı (modül düzeyinde global state).
- Python 3.13 zorunlu. Bağımlılıklar: `uv sync --frozen` (FastAPI, uvicorn, websockets).

## Arda'dan bekleyen kararlar
1. `engine.py:292` (`elif not s.orders …`): tek-deal tasarımı bilinçli mi? Bilinçliyse ölü dal kaldırılır; değilse deal sonunda `orders` sıfırlama davranışı eklenir.
2. Faz 2 dondurma listesi onayı: Futures/Reverse/Infinity Grid, two-leg, rebalancing, signal bot, çoklu bot, LLM asistan P1 sonrasına kalsın mı?
3. Testnet mutation gate koşulları (Faz 3.4; henüz erken).
