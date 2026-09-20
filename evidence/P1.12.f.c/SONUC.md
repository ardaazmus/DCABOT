# P1.12.f.c — Futures DCA fill/average-entry ve pending projection sonucu

**Tarih:** 2026-09-16  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`

## Kapsam

`src/dcabot/application/futures_dca_fill_projection.py` seçilmiş offline
Futures DCA planına gözlemlenmiş base/safety fill’leri bağlar. Exact weighted
average-entry, pozisyon quantity/notional, tamamlanan safety sayısı ve
`max_active_safety_orders` ile sınırlı pending safety seviyeleri üretilir.
Kısmi safety fill’in yalnız kalan miktarı plan limitinde reserved quote olarak
hesaplanır.

Güvenli v1 sınırı: base tamamlanmadan safety fill kabul edilmez; safety
seviyeleri atlanamaz; aynı execution kimliğinin exact duplicate’i idempotent,
farklı payload’ı conflict’tir. Sonlu dış decimal’e sığmayan average-entry
yaklaşıklaştırılmadan fail-closed olur.

Bu projection order command, venue event adapter, core mutation, fee/funding,
position persistence veya canlı emir authority taşımaz.

## Kabul kanıtı

- Odak projection: `4/4 PASS`.
- Bağımsız Decimal oracle: `2/2 PASS`.
- Long/short average-entry, kısmi fill kalan rezervi, duplicate/conflict,
  base-before-safety ve sıra atlama sınırları doğrulandı.
- Tam proje kontrolü `tools/run_checks.py`: `513/513 PASS`.
- Compile/workspace kontrolleri tam proje kontrolünde PASS.

## Açık sınır

Gerçek event identity/sequence, active order ve shared-account reservation
binding, fee/funding ile net average, DCA lifecycle/exit, durable replay ve
venue parity sonraki mikro-fazlardır. Pionex Futures DCA exact alanları
doğrulanmadan parity iddiası yapılmaz.
