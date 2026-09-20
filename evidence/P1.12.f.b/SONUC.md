# P1.12.f.b — Futures DCA bağımsız exact oracle sonucu

**Tarih:** 2026-09-16  
**Durum:** `COMPLETE_WITH_LIMITATION / LOCAL_PASS`

## Kapsam

`tests/test_futures_dca_oracle.py`, üretim projection kodunu tekrar
uygulamadan bağımsız `Decimal` matematiğiyle `P1.12.f.a` çıktısını denetler.
Long ve short yönlerinde kümülatif deviation, volume multiplier, base/quote
sizing, quantity-step quantization ve gerçekleşebilir quote allocation
karşılaştırılır.

Bu oracle yalnız test kanıtıdır; order, fill, average-entry, position,
reserve, lifecycle, persistence, venue veya canlı emir authority eklemez.

## Kabul kanıtı

- Odak bağımsız oracle: `2/2 PASS`.
- Long ve short bağımsız hesap sonuçları production projection ile eşleşti.
- Quantity-step sonrası miktar ve quote allocation sessiz hedef yuvarlaması
  yapmadan exact karşılaştırıldı.
- Tam proje kontrolü `tools/run_checks.py`: `507/507 PASS`.
- Compile/workspace kontrolleri tam proje kontrolünde PASS.

## Açık sınır

Bu kapı yalnız plan matematiğini doğrular. Average-entry/fill binding,
maximum active safety order ve pending reservation, DCA start/stop/TP/trailing/
breakeven lifecycle, durable replay ve Futures DCA venue parity sonraki
mikro-fazlardır. Pionex Futures DCA exact alanları doğrulanmadan parity iddiası
yapılmaz.
