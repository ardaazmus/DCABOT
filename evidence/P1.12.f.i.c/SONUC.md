# P1.12.f.i.c — immutable custom candidate acceptance-boundary sözleşmesi

## Sonuç

Durum: `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`

Custom candidate projection artık yeniden doğrulanıp immutable bir acceptance
snapshot’a bağlanıyor. Snapshot deterministik SHA-256 candidate identity ile Futures
DCA profili, instrument filter metadata’sı, ladder seviyeleri ve post-quantization
conservation alanlarını kapsıyor. Tam eşleşmeyen veya sonradan değiştirilmiş candidate
projection fail-closed `FUTURES_DCA_CUSTOM_ACCEPTANCE_CONFLICT` olarak reddediliyor.

Acceptance sonucu yalnız `order_authority=NONE` taşır. Persistence, order attempt,
venue transport, Binance/Testnet mutation ve mainnet bu fazda açılmadı.

## Kanıt

- Odak: `tests.test_futures_dca_custom_ladder tests.test_futures_dca_plan tests.test_instrument_filters` — `20/20 PASS`
- İlişkili: Futures DCA plan/oracle/fill projection/fill oracle/reservation/contract-size,
  ladder binding/conservation, sizing ve math kümeleri — `55/55 PASS`
- Tam proje: `uv --cache-dir D:\project\DCABOT\.uv-cache run --isolated --frozen python tools/run_checks.py` — `625/625 PASS`
- Deterministic identity ve tam candidate snapshot yeniden doğrulaması: `PASS`
- Tamper/conflict fail-closed ve acceptance write-surface: `PASS`
- Python `compileall`: `PASS`
- Workspace: `PASS`, `240` aktif Python dosyası, `EMPTY_OR_NOT_PLACED` yedek düzeni
- `git diff --check`: `PASS` (yalnız mevcut LF/CRLF uyarıları)

## Sınır ve sonraki iş

Bu snapshot gerçek emir kabulü, durable persistence veya venue confirmation değildir;
`order_authority=NONE` bilinçli olarak korunur. Sıradaki tek iş
`P1.12.f.i.d` custom candidate acceptance’ını mevcut offline sizing/pre-acceptance
köprüsüne bağlayan read-only sözleşmedir.
