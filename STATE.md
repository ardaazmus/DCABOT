# Durum — 2026-09-21

Aktif faz: **Faz 3.5 (tek testnet emri) tamamen kapandı — `evidence_scope=REAL_TESTNET`.** Faz 3.1-3.4 kapalı. P1 `p1-demo-complete` etiketiyle kapalı. Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 930/930 PASS; gerçek testnet'te tam döngü kanıtlandı.
Eksenler: implementation=DONE(3.5) · verification=PASS · evidence_scope=REAL_TESTNET(3.5) · review=NOT_RUN(3.5) · deployment=NOT_DEPLOYED

## Faz 3.5 — Tek testnet emri: REAL_TESTNET kanıtı alındı (bu oturum)
- **Gerçek döngü:** Arda `tools/run_single_testnet_order.py`'yi çalıştırdı. `venue_order_id=4423471`: gönder→`NEW`→sorgula→`FOUND`→iptal→`CANCELED`. Mutation gate'in 7 kuralı (kill-switch, tutar tavanı, execution-anında onay×2, durable-before-send, tek eşzamanlı mutation) canlı doğrulandı.
- **Yol boyunca bulunan 2 gerçek bug, ikisi de düzeltildi:**
  1. Venue'nun temiz reddi (`PERCENT_PRICE_BY_SIDE` filtre hatası, `-1013`) yanlışlıkla `UNKNOWN`'a düşüyordu — yeni `OrderRejectedByVenue` istisnası ile artık doğru şekilde `REJECTED`'e gidiyor (terminal, REST catch-up gerektirmez).
  2. `OrderAttempt.venue_error_code` negatif olamaz diye doğrulanıyordu (önceki oturumdan, `order_attempt.py`) — ama Binance'in kodları her zaman negatif. Düzeltildi, işaret serbest, bounded (`abs<=1_000_000`).
- **Doğrulama:** 1 yeni offline test (gerçek `-1013` senaryosuyla), tam checker 930/930 PASS. İkinci bir canlı mutation'a gerek kalmadı — düzeltme salt yerel muhasebede, transport zaten kanıtlanmıştı.
- **DEFERRED (acil değil):** `InstrumentFilterProfile` `PERCENT_PRICE_BY_SIDE`'ı henüz modellemiyor — venue'nun kendi reddi zaten fail-closed güvenlik ağı, offline pre-check ileride eklenebilir.

## Faz 3.1-3.4 özeti (önceki turlar — ayrıntı git geçmişinde)
3.1 reconnect worker (REAL_TESTNET), 3.2 REST catch-up (kod tamam), 3.3 salt-okunur hesap ekranı (tamam), 3.4 mutation gate 7 kuralı (karar).

## Kodda mevcut
- P2 Binance testnet: public/account/open-orders/user-stream adaptörleri + reconnect worker (REAL_TESTNET) + REST catch-up + hesap/açık-emir API+UI + tek dosyada mutation + mutation gate + CLI kanıt aracı — **tamamı canlı kanıtlı** (3.1 ve 3.5 gerçek testnet'te çalıştı).

## Bilinen sınırlar
- `PERCENT_PRICE_BY_SIDE` offline pre-check yok (DEFERRED, venue zaten reddediyor).
- Faz 3.3'ün `ready` durumu yalnız sahte veriyle test edildi.
- 3.2'nin REST catch-up'ı gerçek bir kesintiye uğramış attempt üzerinde henüz test edilmedi (3.5'in başarılı geçmesi nedeniyle böyle bir attempt oluşmadı).
- Simülasyon: OHLC intrabar sırası INDETERMINATE; tam stress ekonomik modeli NO-GO.
- Mainnet: kesin NO-GO, Arda'nın açık onayı olmadan asla (Faz 4).

## Kararlar (bkz. `docs/KARARLAR.md`)
Faz 3.5 REAL_TESTNET kanıtıyla kapandı; iki gerçek bug (UNKNOWN/REJECTED ayrımı, venue_error_code işareti) canlı test sırasında bulunup düzeltildi.

## Sıradaki adım
Roadmap sırası: **Faz 3.6 — Dolum + restart kurtarma** (süreç ortada öldürülür, yeniden başlayınca tek ekonomik kayıt). Henüz kapsam araştırması/TASK.md brief'i yazılmadı.
