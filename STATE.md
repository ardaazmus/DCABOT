# Durum — 2026-09-21

Aktif faz: **Faz 3.3 backend tamam; frontend paneli Codex'e devredildi (bkz. TASK.md).** Faz 3.1 (`evidence_scope=REAL_TESTNET`), 3.2 (kod tamam, kısmi REAL_TESTNET) kapalı. P1 `p1-demo-complete` etiketiyle kapalı. Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 910/910 PASS (0 skip); canlı sunucuda (credential ayarlanmadan) yeni uç noktalar 409 fail-closed + OpenAPI şeması doğru.
Eksenler: implementation=IN_PROGRESS(3.3 frontend bekliyor) · verification=PASS(backend offline+kısmi canlı) · evidence_scope=LOCAL_INTEGRATION · review=NOT_RUN(3.3) · deployment=NOT_DEPLOYED

## Faz 3.3 — Salt-okunur hesap ekranı: backend tamam (bu oturum, Claude yaptı)
- **Bulgu:** `binance_testnet_account.py` (signed) hiç P2.05 kabul kapısından geçmemiş, hiç API/UI'a bağlanmamıştı; P2.05 yalnız public exchangeInfo'yu kapsıyordu (bkz. docs/KARARLAR.md).
- **Genişletme:** `fetch_binance_testnet_account` artık sıfır olmayan gerçek testnet bakiyelerini (`asset/free/locked`) döndürüyor — testnet olduğu için (mainnet değil) güvenlik ilkesini ihlal etmiyor; `__repr__` hâlâ değerleri basmıyor.
- **Yeni:** `fetch_binance_testnet_open_orders` (`GET /api/v3/openOrders`, signed, redakte).
- **Yeni API:** `GET /api/testnet/account`, `GET /api/testnet/open-orders` — `DCABOT_TESTNET_CREDENTIAL_ID` env değişkeni yoksa `409 TESTNET_CREDENTIAL_NOT_CONFIGURED`.
- **Test:** 14 yeni offline test (9 adapter, 5 API). Tam checker 910/910 PASS. Canlı sunucuda (credential ayarlanmadan, Claude gerçek credential'a hiç dokunmadı) 409 fail-closed + OpenAPI şeması doğrulandı.
- **Frontend:** Codex'e devredildi — TASK.md'de dosya-allowlist'li brief.

## Faz 3.2 — REST catch-up (önceki tur, kod tamam)
`run_rest_catch_up`, client_order_id lookup, gerçek snapshot cursor, -2013 ayrımı. Ayrıntı git geçmişinde.

## Faz 3.1 — Reconnect worker (önceki tur, kapalı, `evidence_scope=REAL_TESTNET`)
Gerçek testnet'e karşı çalıştırıldı, bir gerçek bug bulundu ve düzeltildi.

## Kodda mevcut
- P2 salt-okunur Binance testnet: public/account/open-orders/user-stream adaptörleri + reconnect worker (REAL_TESTNET) + REST catch-up (offline+kısmi REAL_TESTNET) + hesap/açık-emir API uç noktaları (offline+kısmi canlı, frontend bekliyor).

## Bilinen sınırlar
- Signed mutating request (gerçek emir), mutation ve mainnet: NO-GO.
- 3.3 frontend paneli henüz yok (backend hazır, Codex'e devredildi).
- 3.2'nin tam REAL_TESTNET kanıtı 3.5'i bekliyor.
- Simülasyon: OHLC intrabar sırası INDETERMINATE; tam stress ekonomik modeli NO-GO.
- API tek worker'a bağlı. Python 3.13 zorunlu; uv sync --frozen.

## Kararlar (bkz. `docs/KARARLAR.md`)
Faz 3.1 REAL_TESTNET kanıtıyla kapandı; Faz 3.2 kod tamam; Faz 3.3 backend'i P2.05'in gerçek kapsamını netleştirerek ve bakiye değerlerini testnet için açarak tamamladı.

## Sıradaki adım
Codex/muse'in TASK.md brief'indeki frontend panelini (bakiye tablosu + açık emir tablosu + "TESTNET" rozeti) bitirmesi bekleniyor. Bittiğinde Claude diff'i, tsc/vitest'i ve tam checker'ı doğrulayıp kapatacak.
