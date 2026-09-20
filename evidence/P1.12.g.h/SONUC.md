# P1.12.g.h — Futures DCA fee-aware exit-candidate ve quantization boundary

## Kapsam

Bu mikro-faz, g.d’deki explicit settlement-notional fee/funding profilini g.f
exit-candidate sınırına bağlar:

- fee-aware breakeven yalnız seçilmiş `TAKE_PROFIT` adayına bağlanır;
- `STOP_LOSS` ve `TRAILING_STOP` için breakeven fiyatı kullanılmaz;
- fee profili eksikliği, settlement asset mismatch ve off-grid fee-aware hedef
  fail-closed kalır;
- price tick üzerinde olmayan hedef sessizce aşağı/yukarı yuvarlanmaz;
- g.f’nin ortak exit-capacity doğrulaması yeniden kullanılır, over-close aday
  üretemez;
- sonuç salt-okunurdur ve `order_authority=NONE` taşır.

Gerçek order/fill, OCO/cancel-replace, reserve mutation, persistence/recovery ve
Binance/Testnet mutation bu fazın kapsamına alınmadı.

## Kanıt

- Odak: `uv run --frozen python -m unittest tests.test_futures_dca_fee_aware_exit -v`
  — `9/9 PASS`.
- Tam proje: `uv run --frozen python tools/run_checks.py` — `690` test;
  `688 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle
  `2` environment error.
- Bağımsız Fraction capacity oracle, LONG/SHORT exact boundary, trigger kapsamı,
  profil zorunluluğu, settlement mismatch, off-grid/no-rounding ve over-close
  sınırlarını doğruladı.
- `uv run --frozen python -m compileall -q src tests` PASS.
- AST/write-surface testi persistence/transport write çağrısı bulunmadığını
  doğruladı; `order_authority=NONE`.
- `git diff --check` PASS.

## Karar

`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.

Bu kanıt fee-aware TP candidate ve exact quantization sınırını kapatır.
Fee conversion, venue-specific commission/funding source, OCO/cancel-replace,
durable recovery/replay ve Binance account/order akışı sonraki kapılardır.

## Sonraki tek mikro-faz

`P1.12.h.a` durable recovery/replay readiness, `P1.12.h.b` profile-bound
recovery capability, `P1.12.h.c` durable profile recovery snapshot/stale-
profile quarantine ve `P1.12.h.d` immutable profile-source provenance
cross-check kapılarını kapattı; sıradaki `P1.13.c` Spot Grid fee
asset/rounding ve matched cycle profit-total equity ayrımının karar kapısıdır.
