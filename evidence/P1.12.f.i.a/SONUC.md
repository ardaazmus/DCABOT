# P1.12.f.i.a — quantity-step ve quote/base candidate sözleşmesi

## Sonuç

Durum: `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`

Custom Futures DCA ladder artık mevcut `InstrumentFilterProfile` ve
`validate_order_candidate` sözleşmesine bağlanıyor. `BASE_QTY` allocation doğrudan
quantity-step grid’ine aşağı yuvarlanıyor; `QUOTE_NOTIONAL` allocation exact fiyatla
quantity’e çevrilip aynı grid’e aşağı yuvarlanıyor. Her candidate requested allocation,
quantized quantity, gerçekleşen allocation ve quote notional alanlarını birlikte taşır.

Tick uyuşmazlığı, quantity-step sonrası sıfıra düşme, quantity minimumu, min-notional
ve off-grid adaylar fail-closed kalır. Conservation, hedef allocation değil post-
quantization gerçekleşen allocation üzerinden yeniden kanıtlanır; böylece kalan bütçe
sessizce harcanmış sayılmaz. Bu faz yalnız yerel read-only candidate projection üretir;
emir gönderme, persistence, venue mutation, Binance veya mainnet açılmaz.

## Kanıt

- Odak: `tests.test_futures_dca_custom_ladder tests.test_futures_dca_plan tests.test_instrument_filters` — `14/14 PASS`
- İlişkili: Futures DCA plan/oracle/fill projection/fill oracle/reservation/contract-size,
  ladder binding/conservation, sizing ve math kümeleri — `49/49 PASS`
- Tam proje: `uv --cache-dir D:\project\DCABOT\.uv-cache run --isolated --frozen python tools/run_checks.py` — `619/619 PASS`
- Python `compileall`: `PASS`
- Workspace: `PASS`, `239` aktif Python dosyası, `EMPTY_OR_NOT_PLACED` yedek düzeni
- `git diff --check`: `PASS` (yalnız mevcut LF/CRLF uyarıları)

## Sınır ve sonraki iş

Bu kanıt gerçek exchange instrument metadata kaynağı, order authority, persistence veya
canlı işlem kanıtı değildir. `SHARE`, contract-size ve gerçek venue filtrelerinin dış
kaynaktan doğrulanması bu fazın dışındadır. Sıradaki tek iş
`P1.12.f.i.b` bağımsız candidate/oracle incelemesi ve kritik gate’tir.
