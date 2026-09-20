# P1.12.f.i.d — custom candidate offline sizing/pre-acceptance köprüsü

## Sonuç

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`

Immutable custom candidate acceptance artık mevcut offline sizing/pre-acceptance
kapısına salt-okunur olarak bağlanıyor. Quote-notional custom ladder’ın ilk
quantized seviyesi mevcut `SizingCandidate`, kalan seviyeleri mevcut
`LadderBinding` olarak değerlendirilir; toplam actual quote commitment eligible
budget’a karşı yeniden kontrol edilir. Candidate acceptance identity yeniden
doğrulanmadan köprü çalışmaz.

BASE_QTY custom ladder için örtük quote bütçesi üretilmedi; açık quote bütçesi
olmadığı için `FUTURES_DCA_CUSTOM_PRE_ACCEPTANCE_UNIT_UNSUPPORTED` ile fail-closed
reddedilir. Sonuç `order_authority=NONE` taşır. Persistence, reserve, order
attempt, venue transport, Binance/Testnet mutation ve mainnet açılmadı.

## Kanıt

- Odak: `tests.test_futures_dca_custom_ladder tests.test_futures_dca_plan tests.test_instrument_filters tests.test_sizing_pre_acceptance` — `27/27 PASS`
- Custom bridge + ilişkili instrument/sizing sınırları: `23/23 PASS`
- Tam proje: `uv --cache-dir D:\project\DCABOT\.uv-cache run --isolated --frozen python tools/run_checks.py` — `628` test; `626` PASS, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error
- Python `compileall`: `PASS`
- Candidate acceptance module write-surface AST kontrolü: `PASS`; persistence/HTTP write çağrısı yok
- `git diff --check`: `PASS` (yalnız mevcut LF/CRLF uyarıları)

## Sınır ve sonraki iş

Bu köprü yalnız offline sizing/pre-acceptance kanıtıdır; gerçek bakiye keşfi,
rezerv ayırma, order authority, durable persistence veya venue confirmation
değildir. Sıradaki tek iş `P1.12.g` DCA start/stop/TP/trailing/breakeven
lifecycle sözleşmesidir.
