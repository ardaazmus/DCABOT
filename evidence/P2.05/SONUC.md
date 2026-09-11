# P2.05 — Salt-okunur Binance Spot Testnet kabul kapısı

## Karar

```text
P2.05_READ_ONLY_GATE = ACCEPT_WITH_LIMITATION
P2.05_FULL_CAMPAIGN = DEFER
IMPLEMENTATION_GATE = READY_WITH_LIMITATION
TRADING_ACTIVATION = NO-GO
PRODUCTION_READINESS = NO
```

Bu kayıt yalnız public Testnet metadata’sı ve mevcut offline/fake güvenlik
durumları için kabul kanıtıdır. Signed account, User Data Stream, gerçek emir,
cancel, order-list, mainnet veya secret kullanımı bu dilimde açılmadı.

## Doğrulanan kapsam

- Public `exchangeInfo` snapshot’ı yalnız `BINANCE_SPOT_TESTNET` ortamından alınır.
- Public başarı durumu hesap/API-key trade yetkisi, bakiye, reserve, PnL, fee,
  emir kabulü veya fill olarak yorumlanmaz.
- `permissionSets` ürün gereksinimi olarak kalır; account capability üretmez.
- Bilinmeyen venue status ham değeri korunur ve UI fail-closed gösterimine bırakılır.
- Malformed JSON, oversized response, unknown symbol ve upstream hata sınıfları
  başarıya çevrilmez.
- API Problem Details hata gövdesi upstream exception metnini, secret veya key
  bilgisini dışarı taşımaz.
- Native disclosure teknik ayrıntıyı gösterir; UI ekonomik hesap üretmez.

## Kabul matrisi

| ID | Senaryo | Sonuç |
|---|---|---|
| R-01 | Public snapshot başarı | PASS |
| R-02 | Unknown symbol | PASS |
| R-03 | Malformed JSON | PASS |
| R-04 | Oversized response | PASS |
| R-05 | Upstream hata sınıflarının sanitized Problem Details eşlemesi | PASS |
| R-06 | `permissions`/`permissionSets` public-account ayrımı | PASS |
| R-07 | Unknown venue status’ın ham korunması | PASS |
| R-08 | Credential/header boundary | PASS |
| R-09 | Canlı public Testnet GET | PASS |
| R-10 | Mainnet ve mutation | NO-GO |

## Güncel doğrulama

- `uv run --frozen python tools/run_checks.py`: **417/417 PASS**
- `uv run --frozen python -m compileall -q src tests`: **PASS**
- `uv run --frozen python tools/check_workspace.py`: **PASS**, 164 aktif Python dosyası
- `cd frontend && npm run build`: **PASS**, Vite 7.3.6 / 36 modül
- P2.05 odak public/Binance kabul grubu: **29/29 PASS**
- `git diff --check`: **PASS**
- Canlı public GET: HTTP 200, `BTCUSDT=TRADING`, 11 filter, 4 rate limit.

## UI ve erişilebilirlik sınırı

P2.01.b kanıtındaki doğrudan Chrome CDP smoke sonuçları 320/768/1280 px
taşmama, snapshot sınırı ve keyboard/focus davranışını doğrulamaktadır.
NVDA/JAWS, Windows High Contrast Mode ve bağımsız tam ekran okuyucu oturumu
çalıştırılmadı. Bu nedenle WCAG veya production accessibility certification
iddiası yapılmaz.

## Sonraki kapı

P2.05 read-only kabulü `ACCEPT_WITH_LIMITATION` olarak kaydedildi. Full signed
entegrasyon, User Data Stream, durable mutation recovery, bağımsız erişilebilirlik
QA ve gerçek Testnet mutation ayrı kapılardır. Her gerçek Testnet mutation için
execution anında açık kullanıcı yetkilendirmesi gerekir; mainnet kalıcı NO-GO’dur.
