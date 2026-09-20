# P1.12.g.g — Futures DCA candidate identity ve late-fill ayrım contract’ı

## Kapsam

Bu mikro-faz, g.f ile üretilen salt-okunur exit candidate’ın kimliğini ve geç
dolum gözlemini conditional execution’dan ayrı tutar:

- candidate identity; seçilmiş trigger, trigger fiyatı, requested quantity,
  kalan kapasite, açık pozisyon miktarı ve candidate gözlem zamanının canonical
  SHA-256 snapshot’ıdır;
- aynı snapshot aynı identity’yi üretir, zaman veya payload değişimi farklı
  identity üretir; tamper edilmiş hash fail-closed reddedilir;
- late fill yalnız candidate identity’ye bağlı bir observation’dır;
- late fill gözlem zamanı candidate snapshot’tan önce olamaz ve requested
  miktarı aşamaz;
- late fill observation’da execution order identity, order authority veya
  economic posting alanı yoktur.

Mevcut genel conditional execution sözleşmesi bu faza kopyalanmadı ve gerçek
order/fill/persistence akışı açılmadı. `order_authority=NONE` korunur.

## Kanıt

- Odak: `uv run --frozen python -m unittest tests.test_futures_dca_exit_identity -v`
  — `7/7 PASS`.
- Tam proje: `uv run --frozen python tools/run_checks.py` — `681` test;
  `679 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle
  `2` environment error.
- Bağımsız identity/tamper oracle; aynı snapshot, zaman değişimi, out-of-order
  ve over-requested late-fill sınırlarını doğruladı.
- `uv run --frozen python -m compileall -q src tests` PASS.
- AST/write-surface testi persistence/transport write çağrısı bulunmadığını
  doğruladı; `order_authority=NONE`.
- `git diff --check` PASS.

## Karar

`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.

Bu kanıt candidate identity ve late-fill observation sınırını kapatır.
Conditional order binding, fee conversion/rounding, quantization policy,
OCO/cancel-replace, reserve mutation, persistence/recovery ve Binance
account/order akışı sonraki kapılardır.

## Sonraki tek mikro-faz

`P1.12.g.h` ile tamamlandı. Sıradaki tek mikro-faz `P1.12.h`: durable
recovery/replay readiness gate’idir.
