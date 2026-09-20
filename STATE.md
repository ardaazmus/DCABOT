# Durum — 2026-09-20

Aktif faz: Faz 2.1 — demo akışı denetimi (Faz 1 tamamlandı). Dal: codex/latest-state-2026-09-20.
Doğrulanan: uv sync --frozen başarılı; tam checker 871/871 PASS (2 skip); frontend tsc -b temiz, vitest 13/13 PASS (12 mevcut + 1 reducer testi).
Eksenler: implementation=IN_PROGRESS · verification=PASS · evidence_scope=LOCAL_INTEGRATION · review=NOT_RUN (büyük faz bağımsız incelemesi yapılmadı) · deployment=NOT_DEPLOYED

## Faz 1 sonucu
- Rapor #2 _quality_response düzeltildi ve kapatıldı: JSONResponse + Cache-Control no-store.
- Rapor #6 FAILED=4 en yüksek öncelik olarak doğrulandı; fail-closed sınır kabul edildi.
- Rapor #4: paper config modül cache'i mtime değişiminde yenileniyor; bağımsız kopya döndürülüyor.
- Rapor #8: CORS listesi DCABOT_CORS_ORIGINS ile yapılandırılabilir; boş/wildcard değer yerel allowlist'e döner.
- Rapor #10: App.tsx dataset/simulation/saved-runs state grupları reducer ile yönetiliyor; davranış korunuyor.
- Rapor #9: global state için uvicorn tek worker sınırı açıkça kaydedildi.
- Rapor #3 eski bulgu: mevcut canonical bar sözleşmesi quote_volume/trade_count alanlarını kullanmıyor; kod değişikliği gerektiren açık bulgu değil.

## Kodda mevcut (arayüz uçtan uca elle denenmedi — Faz 2.1)
- Yerel arayüz (FastAPI 127.0.0.1:8000 + React/Vite 5173): veri seti kaydı, sınırlı public indirme (Binance BTCUSDT 1h), kalite raporu, OHLC grafik verisi, tarihsel profil seçimi, doğrulama ve kapalı-bar simülasyon (≤ 1000 bar), sonucu SQLite'a kaydetme, kayıtlı run listesi/detayı.
- CLI tools/bot.py: demo, init/replay/status/audit, preview. Sentetik tick, tick başına en çok bir emir, anında tam dolum.
- Çekirdek: exact Decimal/Fraction ladder, net TP, drawdown; idempotent SQLite kayıtları.
- Offline sözleşmeler arayüz dışı doğrulandı; UI'ya bağlılıkları Faz 2.1'de denetlenecek.
- P2 salt-okunur Binance testnet sınırı: public, account, user-stream adaptörleri.

## Bilinen sınırlar
- Signed REST/WS emir, mutation ve mainnet: NO-GO. Gerçek reconnect worker ve REST catch-up yok.
- Simülasyon: OHLC intrabar sırası INDETERMINATE; gerçek likidite modeli yok.
- P1'de eksik: kapsamlı ekonomik metrikler, reproduce/compare, etkileşimli marker, stress ekonomik modeli.
- API tek worker'a bağlı (modül düzeyinde global state).
- Python 3.13 zorunlu. Bağımlılıklar uv sync --frozen (FastAPI, uvicorn, websockets).

## Arda'dan bekleyen kararlar
1. engine.py:292: State.orders deal bitince temizlenmiyor; tek-deal tasarımı bilinçli mi?
2. Faz 2 dondurma listesi onayı: Futures/Reverse/Infinity Grid, two-leg, rebalancing, signal bot, çoklu bot, LLM asistan P1 sonrasına kalsın mı?
3. Testnet mutation gate koşulları (Faz 3.4; henüz erken).