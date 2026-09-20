# P1.12.f.h.c — Futures DCA multiplier exact oracle kapısı

**Tarih:** 2026-09-17  
**Durum:** `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; ekonomik binding `DEFERRED / NO-GO`

## Sonuç

Bağımsız `Decimal` oracle, DCA fill projection’ından gelen quantity’yi açık
bir `pnl_multiplier` ile effective quantity ve mark notional’a dönüştürdü.
`0.001` multiplier örneğinde DCA projection’ın mevcut `quantity × price`
notional’ı ile multiplier uygulanmış notional’ın farklı olduğu doğrulandı.

Bu kanıt, sessiz `1` varsayımının güvenli olmadığını ve contract semantics’in
venue/symbol/effective-time/profile-revision ile bağlanması gerektiğini
gösterir. Üretim profile’ına alan eklenmedi; DCA fill, reservation veya
economic posting binding açılmadı.

## Kabul kanıtı

- Yeni odak test: `1/1 PASS`.
- Test public projection ve `LinearFuturesPosition` seam’lerini kullanır;
  beklenen değerler bağımsız `Decimal` hesaplarından gelir.
- Mevcut exact-average ve explicit contract-size sınırları korunmuştur.
- Tam proje kontrolü `tools/run_checks.py`: `526/526 PASS`; compile, workspace
  ve release-manifest kontrolleri PASS.
- Canlı Binance çağrısı, credential, emir/mutation ve dış dependency yoktur.

## Açık karar

Binance crypto USDⓈ-M için `pnl_multiplier=1` yalnız kaynaklı ve sembol
semantiği doğrulanmış immutable profile içinde kabul edilebilir. Genel DCA
profile’ı symbol/revision authority taşımadığı için atomic binding hâlâ
`DEFERRED / NO-GO` durumundadır. Profile kapsamı `P1.12.f.h.d` ile ayrıca
doğrulandı; sıradaki tek iş fee/slippage/rounding ile release kimliklerini tek
journal transaction sözleşmesinde birleştirmektir.
