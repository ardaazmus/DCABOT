# P1.12.f.h.y — Read-only provenance validation ve publish karar kapısı

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; migration ve otomatik publish `NO-GO`

## Kanıt

`validate_futures_dca_provenance_target` target üzerinde yalnız read-only
okuma yapıyor. Profile revision checksum/replay, source snapshot identity ve
hash/state doğrulaması, profile FK varlığı ve her profile için tam bir
`ACCEPTED` provenance bulunması birlikte kontrol ediliyor.

Karar çıktısı açıkça ayrıdır:

- bütün profile revision’lar doğrulanmış tekil ACCEPTED snapshot’a bağlıysa
  `status=READY`, `publish_decision=READY` döner;
- UNKNOWN/QUARANTINED, eksik profile, eksik ACCEPTED source, duplicate accepted
  profile veya bozuk profile/snapshot varsa her ikisi de `NO_GO` döner.

Odak test: `tests/test_futures_dca_provenance_target.py` — `5/5 PASS`.  
Tam proje kontrolü: `tools/run_checks.py` — `553/553 PASS` (çalışan runtime'a
dokunmadan izole, kilitli bağımlılık ortamında).

## Sınır

`READY` yalnız validation kararını ifade eder; target metadata’sını publish
edemez, mevcut v1 journal’ı değiştiremez ve split-store migration başlatamaz.
Venue/source authority, economic posting, release, canlı order ve gerçek
hesap davranışı açılmadı. Migration ve publish için ayrı insan kontrollü
kanıt kapısı gereklidir.

## Sonraki tek iş

Read-only source-to-target eşleme listesini ve immutable migration manifestini
oluşturup, target publish işlemini yalnız manifest + reopen + bağımsız kontrol
kanıtı varsa mümkün kılan karar kapısını tasarlamak; veri taşımayı başlatmamak.
