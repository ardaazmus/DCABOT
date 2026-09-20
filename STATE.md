# Durum — 2026-09-21

Aktif faz: **Faz 3.6 (dolum + restart kurtarma) kodu tamam, offline doğrulandı; REAL_TESTNET kanıtı Arda'yı bekliyor.** Faz 3.1-3.5 kapalı (3.1, 3.5 `evidence_scope=REAL_TESTNET`). P1 `p1-demo-complete` etiketiyle kapalı. Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 934/934 PASS.
Eksenler: implementation=DONE(3.6 kod) · verification=PASS(offline) · evidence_scope=LOCAL_INTEGRATION(3.6; REAL_TESTNET Arda'yı bekliyor) · review=NOT_RUN(3.6) · deployment=NOT_DEPLOYED

## Faz 3.6 — Dolum + restart kurtarma (bu oturum, Claude yaptı)
- **Bulunan gerçek risk:** `AttemptStore.recover_after_restart()` yalnız `SENDING`'i kurtarıyordu. `prepare()`↔`mark_sending()` arasında ölen bir süreç, attempt'i `PREPARED`/`PERSISTED`'de kalıcı olarak kilitliyordu (`can_transition` çıkış tanımlamıyordu) — tek-eşzamanlı-mutation kuralı bu yüzden gelecekteki her emri sonsuza kadar bloke edebilirdi.
- **Fix:** `order_attempt.py`'nin `can_transition`'ına `PREPARED→UNKNOWN`/`PERSISTED→UNKNOWN` eklendi (muhafazakâr: ağa dokunulmamış olsa bile SENDING'deki crash ile aynı reconciliation yoluna sokuluyor). `recover_after_restart()` artık üç durumu da (`PREPARED, PERSISTED, SENDING`) kurtarıyor.
- **Yeni:** `application/testnet_order_execution.py::recover_stuck_attempts` — oturum başında `coordinator.startup()` + Faz 3.2'nin `lookup_attempt_via_testnet`'ini kullanarak kalan attempt'leri gerçek sorguyla çözer. `tools/run_single_testnet_order.py`'ye yeni emir sorulmadan önce bağlandı.
- **Test:** 4 yeni offline test (crash simülasyonu üç durumda + kurtarma sonrası yeni emrin bloke kalmadığı). Tam checker 934/934 PASS.
- **REAL_TESTNET durumu:** Arda'nın CLI'ı bir onay isteminde `Ctrl+C` ile kesip tekrar çalıştırması bekleniyor — bkz. TASK.md.

## Faz 3.1-3.5 özeti (önceki turlar — ayrıntı git geçmişinde)
3.1 reconnect worker (REAL_TESTNET), 3.2 REST catch-up (kod tamam), 3.3 salt-okunur hesap ekranı (tamam), 3.4 mutation gate 7 kuralı (karar), 3.5 tek testnet emri (REAL_TESTNET, iki gerçek bug bulundu/düzeltildi).

## Kodda mevcut
- P2 Binance testnet: tüm katmanlar (public/account/open-orders/user-stream, reconnect worker, REST catch-up, mutation gate, tek dosyada mutation, restart kurtarma) + CLI kanıt araçları.

## Bilinen sınırlar
- Faz 3.6'nın REAL_TESTNET kanıtı yok — Arda'nın bilinçli Ctrl+C testi bekleniyor.
- `PERCENT_PRICE_BY_SIDE` offline pre-check yok (DEFERRED, venue zaten reddediyor).
- Faz 3.3'ün `ready` durumu yalnız sahte veriyle test edildi.
- Simülasyon: OHLC intrabar sırası INDETERMINATE; tam stress ekonomik modeli NO-GO.
- Mainnet: kesin NO-GO, Arda'nın açık onayı olmadan asla (Faz 4).

## Kararlar (bkz. `docs/KARARLAR.md`)
Faz 3.6 kapsamı onaylandı, implementasyon sırasında kalıcı kilitlenme riski bulunup düzeltildi.

## Sıradaki adım
Arda'nın `tools/run_single_testnet_order.py`'yi çalıştırıp bir onay isteminde `Ctrl+C` ile kesmesi, sonra tekrar çalıştırıp "Onceki oturumdan kalan attempt kurtarildi: ... -> ..." satırını görmesi bekleniyor. Kanıt geldiğinde Claude STATE.md'yi günceller; sıradaki **Faz 3.7 — DCA botu testnet'te uçtan uca** (base + 1-2 safety + TP), Faz 3'ün son dilimi.
