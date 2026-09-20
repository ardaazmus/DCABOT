# P1.12.f.h.b — Futures DCA contract-size commitment kapısı

**Tarih:** 2026-09-17  
**Durum:** `DEFERRED / NO-GO / LOCAL_PASS`

## Bulgu

`FuturesDcaProfile` içinde source-verified contract-size/multiplier alanı
bulunmuyor. `project_futures_dca_plan` base ve safety miktarlarını plan
quantity’si olarak üretirken `project_futures_dca_fills` notional’ı doğrudan
`quantity × fill price` ile hesaplıyor. Buna karşılık mevcut lineer futures
matematiği `LinearFuturesPosition.contract_size` değerini zorunlu ve açık
olarak taşır.

Bu iki katman birbirine bağlanmadan DCA fill’inin USDT commitment’ı tüm
USDⓈ-M sembolleri için doğru kabul edilemez. Contract-size’ı örtülü `1`
varsaymak, özellikle position quantity ile base-equivalent quantity
ayrımında ekonomik hata üretir.

## Karar

Contract-size/multiplier; venue, symbol, effective time ve profile revision ile
bağlı immutable bir alan olarak tanımlanmadan P1.12.f.h atomic binding ve
reservation release açılmayacaktır. Bu kapı yalnız commitment unit’ini
inceler; fee/slippage/rounding, partial/cancel/late/UNKNOWN release ve tek
transaction sözleşmeleri ayrıca açık kalır.

## Kanıt ve sınır

- `src/dcabot/application/futures_dca_plan.py`: DCA profile’da multiplier yok.
- `src/dcabot/application/futures_dca_fill_projection.py`: fill notional’ı
  `quantity × price` olarak türetiyor.
- `src/dcabot/application/linear_futures_math.py`: contract-size explicit ve
  sessiz `1` varsayımını reddeden ayrı matematik katmanı mevcut.
- Yeni production code, veri veya dış dependency eklenmedi.
- Son tam proje kontrolü: `525/525 PASS`.

Bağımsız multiplier oracle kapısı `P1.12.f.h.c` ile geçti. Sıradaki tek iş,
profile-revision kapsamı ve fee/slippage/rounding dahil tek-journal
transaction sözleşmesidir.
