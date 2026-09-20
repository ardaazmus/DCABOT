# P1.12.f.h.z — Source-to-target eşleme ve immutable migration manifest kapısı

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; migration/publish `NO-GO`

## Kanıt

`FuturesDcaProvenanceMigrationMapping`, source kind/row identity, target row
identity, profile revision, payload hash, source schema revision, observed time
ve state alanlarını tek bir immutable eşleme satırında tutuyor. Bu satırlar
canonical JSON üzerinden SHA-256 ile deterministik bir manifest hash’ine
bağlanıyor.

Read-only manifest kararı:

- aynı eşleme aynı manifest hash’ini üretir;
- manifest target’ın ACCEPTED provenance satırlarıyla birebir eşleşirse
  `READY` döner;
- UNKNOWN, duplicate source, duplicate target, profile conflict, empty
  manifest veya target mismatch `NO_GO` döner.

Odak test: `tests/test_futures_dca_provenance_target.py` — `8/8 PASS`.  
Tam proje kontrolü: `tools/run_checks.py` — `556/556 PASS` (çalışan runtime'a
dokunmadan izole, kilitli bağımlılık ortamında).

## Sınır

Manifest yalnız read-only karar artefaktıdır; dosyaya yazılmaz, source verisi
kopyalanmaz, mevcut v1 journal yerinde değiştirilmez ve target publish edilmez.
`READY`, eşlemenin target ile tutarlı olduğunu gösterir; migration yürütme
izni değildir. Economic posting, release, venue authority ve canlı order
davranışı açılmadı.

## Sonraki tek iş

Manifest + target reopen sonrasında bağımsız bir kontrol/oracle ile hash ve
eşleme bütünlüğünü tekrar doğrulayan son publish öncesi kapıyı tasarlamak;
bağımsız kanıt olmadan migration başlatmamak.
