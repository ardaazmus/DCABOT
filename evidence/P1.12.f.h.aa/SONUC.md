# P1.12.f.h.aa — Manifest reopen + bağımsız hash/eşleme oracle kapısı

**Tarih:** 2026-09-17  
**Durum:** `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; migration/publish `NO-GO`

## Kanıt

`tests/test_futures_dca_provenance_manifest_oracle.py` production’ın özel
manifest hash yardımcısını kullanmadan stdlib `json` + `hashlib` ile canonical
hash’i yeniden hesaplıyor ve target SQLite’ı kapatıp yeniden açarak ham
`ACCEPTED` satırını manifest eşlemesine dönüştürüyor.

Bağımsız oracle şu sınırları doğruladı:

- reopen edilmiş target satırı ve bağımsız SHA-256 hesabı manifest ile aynı;
- target payload hash’i sonradan değiştirilirse manifest karşılaştırması
  `NO_GO` olur;
- manifest hash’i değiştirilirse `NO_GO` olur ve target satırı değişmeden kalır.

Odak test: bağlı target testleri + bağımsız oracle — `11/11 PASS`.  
Tam proje kontrolü: `tools/run_checks.py` — `559/559 PASS` (çalışan runtime'a
dokunmadan izole, kilitli bağımlılık ortamında).

## Sınır

Bu bağımsız kontrol test-only oracle’dır; migration manifestini persist etmez,
source verisi taşımaz, mevcut v1 journal’ı değiştirmez ve publish/migration
başlatmaz. Binance, economic posting, release ve canlı order authority’si
açılmadı.

## Sonraki tek iş

Manifest, target ve bağımsız oracle kanıtlarını tek bir insan kontrollü
publish-readiness raporunda birleştiren son karar kapısını tasarlamak;
`READY` kararını migration yürütme iznine çevirmemek.
