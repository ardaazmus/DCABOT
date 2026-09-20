# P1.12.f.h.s — Profile revision + contract-size source adapter kapısı

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; venue/migration binding `NO-GO`

## Kanıt

Explicit `FuturesDcaProfileRevisionSource` adapter’ı, mevcut sabit Futures
profilini journal’ın immutable profile revision’ına yalnız caller’ın verdiği
source alanlarıyla dönüştürüyor:

- revision identity ve symbol;
- effective time;
- exact positive contract-size;
- fee/slippage/rounding policy revision identity’leri.

Profilin venue/product/settlement/margin/position alanları mevcut explicit
profil scope’undan gelir; contract-size `1` varsayılmaz, source alanı olmadan
revision üretilemez. Invalid identity, zaman veya contract-size fail-closed
kalır.

Odak test: `tests/test_futures_dca_profile_source.py` — `2/2 PASS`.  
Tam proje kontrolü `tools/run_checks.py` — `545/545 PASS` (çalışan runtime’a
dokunmadan izole, kilitli bağımlılık ortamında).

## Sınır

Adapter venue’dan veri çekmez, Binance `exchangeInfo` veya hesap authority’si
iddia etmez, source provenance hash’i saklamaz ve mevcut split store’ları
migrate etmez. Fee/slippage/rounding policy içeriği hâlâ yalnız explicit
revision identity’dir; ekonomik hesap, release, posting ve canlı order açılmaz.

## Sonraki tek iş

Profile source provenance ve snapshot identity’sini, gerçek venue verisi olmadan
yalnız explicit fixture/read-only kanıtla bağlayan karar kapısını hazırlamak.
