# P1.12.f.h.e — Futures DCA fee/slippage/rounding karar kapısı

**Tarih:** 2026-09-17  
**Durum:** `DEFERRED / NO-GO / LOCAL_PASS`

## Bulgu

Mevcut `FuturesDcaFill` yalnız execution identity, level index, quantity ve
price taşır. Fee, fee asset, effective execution price, slippage reference,
execution time veya rounding policy alanları yoktur. DCA pending reserve de
plan level quantity’si ile level price çarpımından oluşur; fee ve slippage
commitment’a dahil edilmez.

Spot MARKET sözleşmesindeki `quote_quantity`, `effective_price`, fee ve
slippage alanları bu boşluğu gösteren karşılaştırma kanıtıdır; Futures DCA’ya
doğrudan kopyalanamaz. Futures profile, multiplier ve venue execution
semantics’i farklıdır.

## Karar

Futures DCA atomic binding açılmadan önce şu alanların tek immutable fill
contract’ında sahipliği belirlenmelidir:

- gross base/quote ve multiplier uygulanmış commitment,
- venue execution price ile referans/slippage policy,
- fee amount + fee asset + fee profile revision,
- quantity/price/fee quantization ve residual policy,
- partial/cancel/late/UNKNOWN durumunda tüketilen ve serbest bırakılan exact
  miktarın identity’si.

Eksik alanlar zero, current price veya varsayılan rounding ile doldurulmayacak.
Bu nedenle fee/slippage/rounding bağlı reservation ve economic posting
`DEFERRED / NO-GO` kalır.

## Kanıt ve sınır

- `src/dcabot/application/futures_dca_fill_projection.py`: DCA fill ve
  pending reserve alanları incelendi.
- `src/dcabot/application/market_base_quantity.py`: fee/effective-price/
  slippage sözleşmesi karşılaştırma için incelendi; DCA authority değildir.
- Production kodu, veri, credential, canlı çağrı/emir ve dependency değişmedi.
- Önceki tam proje kontrolü `tools/run_checks.py`: `527/527 PASS`.
- `git diff --check`: whitespace hatası yok; yalnız mevcut CRLF uyarıları var.

Sıradaki tek iş, bu alanların profile revision ve release identity ile tek
bounded journal transaction’ında exact contract olarak tanımlanmasıdır.
