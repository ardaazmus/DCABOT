# P1.12.f.h.v — Provenance SQLite failure/replay oracle kapısı

**Tarih:** 2026-09-17  
**Durum:** `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; production schema binding `NO-GO`

## Kanıt

Bağımsız stdlib SQLite oracle, h.u provenance schema taslağının temel
invariant’larını doğruladı:

- ACCEPTED source snapshot restart sonrası aynı identity/hash/state ile replay
  edilir;
- aynı snapshot identity aynı payload hash ile `DUPLICATE`, farklı hash ile
  `PROVENANCE_CONFLICT` olur;
- aynı tabloda UNKNOWN snapshot saklanabilse de accepted authority replay’ine
  alınmaz;
- commit öncesi injected failure rollback sonrası partial provenance satırı
  görünmez.

Odak test: `tests/test_futures_dca_provenance_oracle.py` — `3/3 PASS`.  
Tam proje kontrolü `tools/run_checks.py` — `548/548 PASS` (çalışan runtime’a
dokunmadan izole, kilitli bağımlılık ortamında).

## Sınır

Bu test production journal schema’sını değiştirmez; schema version yükseltmez,
migration çalıştırmaz ve venue/source authority oluşturmaz. Provenance tablosu
henüz production profile revision’a bağlanmadı; ekonomik, release, posting ve
canlı order davranışı açılmadı.

## Sonraki tek iş

Oracle ile doğrulanan provenance owner’ını bounded production schema’ya bağlayan
minimum migration adımını tasarlamak; mevcut v1 dosyalarını in-place değiştirmemek
ve migration kanıtı olmadan `READY` üretmemektir.
