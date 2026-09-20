# Durum — 2026-09-21

Aktif faz: **Faz 3.6 (dolum + restart kurtarma) tamamen kapandı — `evidence_scope=REAL_TESTNET`.** Faz 3.1-3.5 kapalı (3.1, 3.5, 3.6 canlı kanıtlı). P1 `p1-demo-complete` etiketiyle kapalı. Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 934/934 PASS; gerçek testnet'te restart kurtarma tam döngüsü kanıtlandı.
Eksenler: implementation=DONE(3.6) · verification=PASS · evidence_scope=REAL_TESTNET(3.1,3.5,3.6) · review=NOT_RUN(3.6) · deployment=NOT_DEPLOYED

## Faz 3.6 — Dolum + restart kurtarma: REAL_TESTNET kanıtı alındı (bu oturum)
- **Bulunan risk + fix:** `recover_after_restart()` yalnız `SENDING`'i kurtarıyordu; `PREPARED`/`PERSISTED`'de ölen bir süreç kalıcı kilitlenmeye yol açabilirdi. `can_transition`'a `PREPARED→UNKNOWN`/`PERSISTED→UNKNOWN` eklendi, `recover_after_restart()` üç durumu da kapsıyor artık.
- **Elle Ctrl+C pratik değil çıktı** (Arda iki kez denedi — ağ round-trip'i sub-saniye, insan reflexiyle isabet imkânsız). Bunun yerine `tools/run_single_testnet_order.py --simulate-crash-at {prepared,persisted,sending}` eklendi: gerçek `AttemptStore` geçişleriyle attempt'i istenen durumda bırakıp `os._exit()` ile sert çıkar (gerçek çökmenin sahici vekili, veri zaten commit edilmiş).
- **Gerçek kanıt:** `--simulate-crash-at persisted` ile attempt `PERSISTED`'de bırakıldı → bayraksız sonraki çalıştırma `Onceki oturumdan kalan attempt kurtarildi: single-order-1789948270 -> UNRESOLVED` (gerçek venue sorgusu doğru "yok" dedi) → yeni emir (`venue_order_id=4429087`) bloke olmadan NEW→FOUND→CANCELED tamamladı.
- **Test:** 4 offline test (üç durumda crash simülasyonu + kurtarma sonrası blok kalkması). Tam checker 934/934 PASS.

## Faz 3.1-3.5 özeti (önceki turlar — ayrıntı git geçmişinde)
3.1 reconnect worker (REAL_TESTNET), 3.2 REST catch-up (kod tamam), 3.3 salt-okunur hesap ekranı (tamam), 3.4 mutation gate 7 kuralı (karar), 3.5 tek testnet emri (REAL_TESTNET, iki bug bulundu/düzeltildi).

## Kodda mevcut
- P2 Binance testnet: tüm katmanlar canlı kanıtlı (public/account/open-orders/user-stream, reconnect worker, REST catch-up, mutation gate, tek dosyada mutation, restart kurtarma) + CLI kanıt araçları (biri deterministik crash-simülasyonu dahil).

## Bilinen sınırlar
- `PERCENT_PRICE_BY_SIDE` offline pre-check yok (DEFERRED, venue zaten reddediyor).
- Faz 3.3'ün `ready` durumu yalnız sahte veriyle test edildi.
- Simülasyon: OHLC intrabar sırası INDETERMINATE; tam stress ekonomik modeli NO-GO.
- Mainnet: kesin NO-GO, Arda'nın açık onayı olmadan asla (Faz 4).

## Kararlar (bkz. `docs/KARARLAR.md`)
Faz 3.6 REAL_TESTNET kanıtıyla kapandı; kalıcı kilitlenme riski bulunup düzeltildi; elle Ctrl+C'nin pratik olmadığı keşfedilip deterministik crash-simülasyon aracı eklendi.

## Sıradaki adım
Roadmap sırası: **Faz 3.7 — DCA botu testnet'te uçtan uca** (base + 1-2 safety + TP). Bu, Faz 3'ün son dilimi — tamamlanınca kapanış (bağımsız review + `git tag p2-testnet-complete`) sırada. Henüz kapsam araştırması/TASK.md brief'i yazılmadı.
