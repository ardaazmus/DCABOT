# P1.13.c — Spot grid fee ve cycle/equity projection

## Durum

`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.

## Uygulanan en küçük davranış

`SpotGridFeeProfile` yalnız açık `quote_asset` fee, exact decimal `fee_rate`,
explicit `fee_quantum` ve `EXACT_NO_ROUNDING` mode kabul ediyor. Üçüncü/base
fee asset’i ve venue quantization profili fail-closed kalıyor.

`project_spot_grid_cycle` accepted BUY ve SELL çiftini önce mevcut immutable
spot inventory projection üzerinden doğruluyor. Matched cycle profit’i iki
notionalın farkından iki quote-fee düşülerek ayrı hesaplanıyor. Total equity,
cycle sonrası quote cashflow ile açık base inventory’nin explicit mark price
üzerindeki değerini topluyor; mark fiyatı cycle profit’i değiştirmiyor.

Projection salt-okunur, `order_authority=NONE`; persistence, Store binding,
pending order/reserve, replacement, API/UI ve venue mutation açmıyor. State
önceden aynı fill’i içeriyorsa fee posting state’te bulunmadığı için tekrar
ücretlendirme güvenli kabul edilmiyor ve işlem fail-closed oluyor.

## Kanıt

- Odak `tests/test_spot_grid_cycle_accounting.py`: `5/5 PASS`.
- İlişkili Spot Grid kümesi (`P1.13.a–c`): `13/13 PASS`.
- Bağımsız `Decimal` oracle: `PASS`; mark değişirken cycle profit sabit,
  total equity değişiyor.
- Negatif sınırlar: base/third fee asset, non-zero venue quantum, yanlış
  cycle yönü/miktarı ve tekrar ücretleme `BLOCKED`.
- Read-only AST/write-surface: `PASS`.
- Compile: `PASS`; workspace kontrolü: `PASS`; `git diff --check`: `PASS`.
- Tam proje: `707` testte `705 PASS`; faz dışı Windows Credential Manager
  `Windows error 1312` nedeniyle `2` environment error.
- Gerçek source export, migration/publish, Binance/Testnet mutation, Store
  persistence veya canlı order açılmadı.

## Açık sınırlar

Per-fill venue rounding, base/third-asset fee conversion, reserved-fee
valuation, partial-fill/replacement/replay persistence ve public grid sonucu
ayrı kapılardır. Bu kod yalnız ilk offline `arithmetic + quote-asset-fee-only`
profilinin accepted matched cycle projection’ıdır.

## Sonraki tek iş

`P1.13.d` — geometric seviye precision/quantization karar kapısı.
