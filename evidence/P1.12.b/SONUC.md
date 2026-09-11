# P1.12.b — Linear futures partial-close quantity ve gross PnL

## Durum

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.

## Uygulanan en küçük davranış

`src/dcabot/application/linear_futures_math.py` içinde `project_partial_close` eklendi:

- Close miktarı contract quantity olarak doğrulanır; `contract_size` ile effective base-equivalent close miktarı ayrı hesaplanır.
- Partial ve full close için kalan contract quantity exact korunur; over-close fail-closed reddedilir.
- Long/short gross realized PnL, exit-entry farkının yönlü ve settlement-asset karşılığı olarak hesaplanır.
- Bu projection fee, funding allocation, margin, liquidation, reserve veya core `Store` mutasyonu yapmaz.

## Doğrulama zinciri

- RED: `project_partial_close` yokken yeni suite import failure; mevcut P1.12.a testleri korunuyordu.
- GREEN: yeni partial-close suite ile tam regresyon `248/248 PASS`.
- Bağımsız kontrol: production import etmeden Decimal oracle `PASS`; Q=1.25, close=0.5, entry=40000 için long exit=43000 ve short exit=37000 sonuçları ayrı ayrı `1500`, kalan `0.75`.
- Workspace/compile: `uv run --frozen python tools/check_workspace.py` → `PASS`; `105` aktif Python dosyası.
- Negative kontrol: over-close `LINEAR_FUTURES_CLOSE_OVERFLOW` ile reddedildi.

## Araştırma temeli

`docs/P1_KRITIK_ARASTIRMA_FINAL/09_P1.12_FUTURES_MODEL.md` partial close’u linear futures state-machine içinde kabul ediyor; net closed PnL için fee/funding allocation politikasının ayrıca dondurulmasını istiyor. Bu uygulama yalnız kabul edilen quantity + gross PnL çekirdeğini taşır.

## Açık sınır ve üretim kararı

Net realized sonuç, trading fee ve funding ile birleştirilmedi. Fee asset, maker/taker, per-fill rounding, funding event identity/time, duplicate/replay ve persistence sözleşmeleri yokken bunları aynı hesapta toplamak yanlış net sonuç üretebilir. Margin/liquidation ve cross/isolated davranışı bu fazın dışındaki profile kapılarıdır.

## Sonraki tek iş

`P1.12.c` — timestamped funding/trading-fee ledger event identity, duplicate/replay ve net-result binding karar kapısı.
