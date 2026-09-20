# P1.12.f.a — Futures DCA exact plan projection sonucu

**Tarih:** 2026-09-16
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`

## Kapsam

`src/dcabot/application/futures_dca_plan.py` seçilen USD_M/USDT/one-way/
isolated profile içinde offline Futures DCA planı üretir. Long safety emirleri
anchor’ın altında, short safety emirleri üstünde ilerler. Deviation kümülatif,
volume multiplier geometrik olarak uygulanır. Base/safety miktarı BASE_QTY veya
QUOTE_NOTIONAL olarak seçilebilir; quantity-step sonrası gerçekleşebilir quote
tahsis ve toplam capital ayrı raporlanır.

Bu yalnız projection/candidate sözleşmesidir. Order, fill, position, average
entry mutation, exit, reserve, persistence, venue veya live mutation authority
taşımaz.

## Kabul kanıtı

- `3/3` odak test PASS: long cumulative ladder/volume, short yön, budget ve
  anchor sınırları.
- Cumulative deviation örneği `1% → 3%` olarak doğrulandı.
- Quantity-step quantization sonrası quote allocation sessizce hedefe
  yuvarlanmıyor; gerçekleşebilir değer (`1.9998`, `3.9964`) raporlanıyor.
- Tam proje kontrolü `tools/run_checks.py`: `505/505 PASS`.
- Compile/workspace kontrolleri tam proje kontrolünde PASS.

## Açık sınır

Bağımsız Decimal/Fraction oracle, average-entry fill binding, maximum active
order/pending reserve, DCA lifecycle/exit, durable replay ve Futures DCA venue
profile acceptance sonraki alt fazlardır. Pionex Futures DCA exact alanları bu
araştırmada doğrulanmadığı için Pionex parity iddiası yapılmaz.
