# P1.12.f.h.x — Bounded provenance target initializer + failure/restart kapısı

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; migration ve publish `NO-GO`

## Kanıt

Yeni `futures_dca_provenance_target.py` mevcut v1 journal dosyasını yerinde
değiştirmeden yeni bir bounded SQLite target oluşturuyor. Target, mevcut v1
`profile_revisions` sahibine bağlı `profile_source_snapshots` tablosunu,
`ACCEPTED` profile revision başına partial unique index'i ve target'ın henüz
yayınlanmadığını belirten metadata owner'ını kuruyor.

Target davranışı üç testle doğrulandı:

- ACCEPTED snapshot aynı identity ile yeniden yazıldığında `DUPLICATE` olur;
  UNKNOWN snapshot saklanabilir ancak accepted replay'e alınmaz;
- aynı snapshot identity farklı payload hash ile, aynı profile revision ikinci
  ACCEPTED snapshot ile ve eksik profile revision ile fail-closed olur;
- commit öncesi SQLite trigger hatası dışarıya gerçek `IntegrityError` olarak
  taşınır, transaction rollback olur ve reopen sonrası snapshot görünmez.

Odak test: `tests/test_futures_dca_provenance_target.py` — `3/3 PASS`.  
Tam proje kontrolü: `tools/run_checks.py` — `551/551 PASS` (çalışan runtime'a
dokunmadan izole, kilitli bağımlılık ortamında).

## Sınır

Bu target mevcut v1 dosyasını migrate etmez, split-store verisi kopyalamaz,
source/venue authority yayınlamaz ve ekonomik, release, posting veya canlı
order davranışı açmaz. Migration, target doğrulama ve publish kapısı olmadan
`READY` kabul edilmez. Hedef dosya yalnız yeni dosya olarak başlatılabilir;
mevcut journal üzerinde in-place schema değişikliği yapılmadı.

## Sonraki tek iş

Target üzerindeki profile/provenance satırlarını read-only source sözleşmesiyle
doğrulayan ve publish kararını açıkça `NO-GO`/`READY` olarak ayıran minimum
validation kapısını yazmak; gerçek split-store migration açmamak.
