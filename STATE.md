# Durum — 2026-09-21

Aktif faz: **Faz 3.5 (tek testnet emri) kodu tamam, offline doğrulandı; REAL_TESTNET kanıtı Arda'yı bekliyor.** Faz 3.1 (`evidence_scope=REAL_TESTNET`), 3.2 (kod tamam), 3.3 (tamam), 3.4 (karar, 7 kural onaylı) kapalı. P1 `p1-demo-complete` etiketiyle kapalı. Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 929/929 PASS; frontend tsc/vitest önceki turdan temiz.
Eksenler: implementation=DONE(3.5 kod) · verification=PASS(offline) · evidence_scope=LOCAL_INTEGRATION(3.5; REAL_TESTNET Arda'yı bekliyor) · review=NOT_RUN(3.5) · deployment=NOT_DEPLOYED

## Faz 3.5 — Tek testnet emri (bu oturum, Claude yaptı)
- **Mutation'ı tek dosyaya hapsetme kararı:** signed emir/iptal fonksiyonları mevcut (read-only vaat eden) `binance_testnet_user_stream.py`'ye değil, yeni `data_adapters/binance_testnet_order_execution.py`'ye kondu — "projede mutation yapabilen TEK dosya" olarak adlandırıldı, kasıtlı ayrı (bkz. docs/KARARLAR.md).
- **Kapı:** `application/testnet_order_execution.py` — Faz 3.4'ün 7 kuralını sırayla uyguluyor: onay → kill-switch (iki kez, transport'ta da tekrar) → tek-eşzamanlı-mutation (`AttemptStore.count_in_flight_attempts()`, yeni) → exact filtre doğrulama (mevcut `validate_order_candidate`) → `max_entry_notional` → `prepare/persist/mark_sending` (mevcut, durable-before-send) → gönder → `mark_acknowledged`/hata durumunda `mark_unknown` (Faz 3.2'nin REST catch-up'ının çözeceği durum — döngü kapanıyor).
- **CLI aracı:** `tools/run_single_testnet_order.py <credential_id> <symbol> <BUY|SELL> <qty> <price>` — iki ayrı execution-anında onay (gönder, iptal), sabit düşük `MAX_ORDER_NOTIONAL_CAP=50`. Claude hiç çalıştırmadı/çalıştıramaz.
- **Test:** 19 yeni offline test (9 transport, 7 kapı, 3 CLI filtre-çıkarma). Tam checker 929/929 PASS.
- **REAL_TESTNET durumu:** henüz Arda çalıştırmadı — bkz. TASK.md.

## Faz 3.1-3.4 özeti (önceki turlar — ayrıntı git geçmişinde)
3.1 reconnect worker (REAL_TESTNET, bir gerçek bug bulundu/düzeltildi), 3.2 REST catch-up (kod tamam), 3.3 salt-okunur hesap ekranı (tamam, backend Claude + frontend Codex), 3.4 mutation gate 7 kuralı (karar, kod yok).

## Kodda mevcut
- P2 Binance testnet: public/account/open-orders/user-stream adaptörleri (salt-okunur) + reconnect worker (REAL_TESTNET) + REST catch-up + hesap/açık-emir API+UI + **tek dosyada mutation** (`binance_testnet_order_execution.py`) + mutation gate (`testnet_order_execution.py`) + CLI kanıt aracı.

## Bilinen sınırlar
- Faz 3.5'in REAL_TESTNET kanıtı yok — Arda `tools/run_single_testnet_order.py`'yi yerelde `DCABOT_TRADING_ENABLED=true` ile çalıştırmalı.
- Faz 3.3'ün `ready` durumu yalnız sahte veriyle test edildi.
- 3.2'nin tam REAL_TESTNET kanıtı da 3.5'in gerçek çalıştırmasına bağlı (kesintiye uğramış bir attempt oluşması gerekiyor).
- Simülasyon: OHLC intrabar sırası INDETERMINATE; tam stress ekonomik modeli NO-GO.
- Mainnet: kesin NO-GO, Arda'nın açık onayı olmadan asla (Faz 4).

## Kararlar (bkz. `docs/KARARLAR.md`)
Faz 3.4 mutation gate 7 kuralı onaylandı; Faz 3.5 bu kuralları uygulayan kodu yazdı, mutation'ı tek dosyaya hapsetme kararı alındı.

## Sıradaki adım
Arda'nın `tools/run_single_testnet_order.py`'yi yerelde çalıştırıp gerçek bir testnet LIMIT emri gönder→gör→iptal et döngüsünü tamamlaması bekleniyor. Kanıt geldiğinde Claude STATE.md'yi `evidence_scope=REAL_TESTNET` olarak günceller; Faz 3'ün geri kalanı (3.6 restart kurtarma, 3.7 uçtan uca DCA) sırada.
