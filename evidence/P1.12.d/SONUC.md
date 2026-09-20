# P1.12.d — Linear futures ledger durable replay sonucu

**Tarih:** 2026-09-16
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`

## Kapsam

Bu mikro-faz yalnız `LinearLedgerEvent` ücret ve funding projection’ının
offline kalıcı replay sınırını kurar. Pozisyon, emir, fill, CORE01 state,
venue kimliği, canlı transport veya mutation authority eklenmemiştir.

Uygulama: `src/dcabot/persistence/linear_ledger_store.py`
Odak test: `tests/test_linear_ledger_store.py`

## Kabul kanıtı

- `4/4` odak test PASS.
- Restart sonrası exact ledger replay PASS.
- Aynı event kimliği ve aynı payload duplicate olduğunda `DUPLICATE`; farklı
  payload conflict olduğunda fail-closed PASS.
- Event zamanı geriye gittiğinde reducer reddi PASS.
- Payload checksum bozulduğunda store açılışı fail-closed PASS.
- Tam proje kontrolü `tools/run_checks.py`: `499/499 PASS`.
- Compile/workspace kontrolleri tam proje kontrolünde PASS.
- `git diff --check` yalnız mevcut CRLF uyarıları verdi; whitespace hatası yok.

## Sınır

Bu kayıt P1.12.d’nin fee/funding projection alt kümesini kapatır. Futures
position/execution persistence, risk-tier/liquidation snapshot, margin,
Futures DCA lifecycle, core binding ve gerçek Binance reconciliation ayrı
bağımlılıklardır ve açılmamıştır.
