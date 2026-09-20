# P1.12.f.h.ab — İnsan kontrollü publish-readiness karar kapısı

**Tarih:** 2026-09-17  
**Durum:** `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; publish/migration `NO-GO`

## Kanıt

`assess_futures_dca_provenance_publish_readiness` target validation, manifest
eşleşmesi ve bağımsız oracle sonucunu tek karar çıktısında birleştiriyor.

- bütün teknik kanıtlar `PASS` ise durum `READY_FOR_REVIEW`;
- `approval_state=REQUIRED` ve `publish_action=BLOCKED` her durumda korunuyor;
- bağımsız oracle `NOT_RUN` veya `FAIL`, target/manifest uyuşmazlığı ve diğer
  önceki NO_GO koşulları readiness’i `NO_GO` yapıyor.

Bu fonksiyon yalnız karar üretir; kullanıcı onayı, migration veya publish
işlemi gerçekleştirmez.

Odak test: `tests/test_futures_dca_provenance_target.py` +
`tests/test_futures_dca_provenance_manifest_oracle.py` — `13/13 PASS`.  
Tam proje kontrolü: `tools/run_checks.py` — `561/561 PASS` (çalışan runtime'a
dokunmadan izole, kilitli bağımlılık ortamında).

## Sınır

Bu kapı provenance target’ı authority olarak yayınlamaz, mevcut v1 dosyasını
değiştirmez, split-store migration başlatmaz ve canlı Binance/economic
posting/release/order davranışı açmaz. `READY_FOR_REVIEW`, teknik kanıtların
insan incelemesine hazır olduğu anlamına gelir; otomatik icra izni değildir.

## Sonraki tek iş

İnsan kontrollü bağımsız inceleme ve kapsamlı kabul kapısını çalıştırmak;
inceleme onayı ve gerçek eksiksiz source kanıtı olmadan migration/publish
başlatmamak.
