# Durum — 2026-09-21

Aktif faz: **Faz 3.2 (REST catch-up) kodu tamam, offline doğrulandı.** REAL_TESTNET kanıtı kısmi (sorgu mekaniği doğrulanabilir, tam uçtan uca kanıt 3.5'i bekliyor). Faz 3.1 `evidence_scope=REAL_TESTNET` ile kapalı. P1 `p1-demo-complete` etiketiyle kapalı. Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 899/899 PASS (0 skip); frontend değişmedi (tsc/vitest önceki turdan temiz).
Eksenler: implementation=DONE(3.2 kod) · verification=PASS(offline) · evidence_scope=LOCAL_INTEGRATION(3.2; REAL_TESTNET kısmi — sorgu mekaniği) · review=NOT_RUN(3.2) · deployment=NOT_DEPLOYED

## Faz 3.2 — REST catch-up (bu oturum, Claude yaptı, delege edilmedi)
- **Ne yapıldı:** `src/dcabot/application/rest_catch_up.py` (`run_rest_catch_up`) — blocking attempt'leri gerçek signed WS-API sorgusuyla çözüp `apply_authoritative_snapshot`'a bağlıyor.
- **Kapsam onaylandıktan sonra ortaya çıkan 3 zorunlu ek** (bkz. docs/KARARLAR.md, hepsi minimal/additive):
  1. `query_binance_testnet_order_status_by_client_id` — SENDING→UNKNOWN attempt'lerin (asıl kritik durum) `venue_order_id`'si hiç yok; `client_order_id` ile sorgu gerekiyordu.
  2. `ReconciliationCoordinator.last_accepted_event` (yeni salt-okunur property + `_last_event` alanı) — gerçek bir snapshot cursor'ı sahte veri uydurmadan kurmak için zorunluydu. 34/34 önceki reconciliation testi hâlâ PASS.
  3. Venue'nun `-2013` (order not found) cevabı artık exception değil `OrderLookup.not_found()`.
- **Yeni:** `AttemptStore.list_resolvable_attempts()` (yalnız UNKNOWN/RECONCILING — UNRESOLVED kasıtlı hariç, `can_transition` ona çıkış vermiyor, kalıcı blok tasarım gereği).
- **Test:** 6 yeni `tests/test_rest_catch_up.py` + 4 yeni order-status testi (`tests/test_binance_testnet_user_stream.py`), tümü offline sahte-socket. Tam checker 899/899 PASS.
- **REAL_TESTNET durumu:** `tools/run_order_status_lookup_diagnostic.py` ile sorgu mekaniği (clientOrderId alan adı, -2013 kodu) gerçek venue'ya karşı doğrulanabilir — henüz Arda çalıştırmadı. Tam uçtan uca (gerçek kesintiye uğramış bir emir) kanıt Faz 3.5'i (emir gönderme) bekliyor.

## Faz 3.1 — Reconnect worker (önceki tur, kapalı, `evidence_scope=REAL_TESTNET`)
Gerçek testnet'e karşı çalıştırıldı, bir gerçek bug (`ConnectionClosedError`) bulundu ve düzeltildi. Ayrıntı git geçmişinde.

## Kodda mevcut
- P2 salt-okunur Binance testnet: public/account/user-stream adaptörleri + reconnect worker (REAL_TESTNET) + REST catch-up (offline + kısmi REAL_TESTNET).
- Diğerleri önceki oturumlardan değişmedi (bkz. git geçmişi).

## Bilinen sınırlar
- Signed mutating request (gerçek emir), mutation ve mainnet: NO-GO.
- 3.2'nin tam REAL_TESTNET kanıtı 3.5'i (tek testnet emri) bekliyor — henüz gerçek bir kesintiye uğramış emir senaryosu yok.
- Order list (OCO) reconciliation ve toplu `openOrders` sorgusu bu dilimin kapsamı dışında (kasıtlı, bkz. onaylanan kapsam).
- Simülasyon: OHLC intrabar sırası INDETERMINATE; gerçek likidite modeli yok. Tam stress ekonomik modeli NO-GO.
- API tek worker'a bağlı. Python 3.13 zorunlu; uv sync --frozen.

## Kararlar (bkz. `docs/KARARLAR.md`)
Faz 3.1 REAL_TESTNET kanıtıyla kapandı; Faz 3.2 dar kapsamı Arda onayladı, implementasyon sırasında 3 zorunlu ek keşfedildi ve uygulandı (client_order_id lookup, gerçek snapshot cursor, -2013 ayrımı).

## Sıradaki adım
İki seçenek: (1) `tools/run_order_status_lookup_diagnostic.py`'yi Arda çalıştırıp 3.2'nin sorgu mekaniğini gerçek venue'ya karşı doğrulasın (hızlı, opsiyonel — kod zaten offline kanıtlı). (2) Doğrudan **Faz 3.3 — salt-okunur hesap ekranı**'na geç. Roadmap sırası zaten 3.3, ama 3.2'nin tam kanıtı olmadan devam etmek proje kuralınca sorun değil (yalnız 3.1 gibi "evidence_scope=REAL_TESTNET üretmiyorsa iş sayılmaz" kuralı 3.2'nin *kendi kapanışı* için geçerli, 3.3'ü engellemiyor).
