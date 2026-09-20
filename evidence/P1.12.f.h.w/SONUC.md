# P1.12.f.h.w — Provenance target schema/migration taslağı

**Tarih:** 2026-09-17  
**Durum:** `CONTRACT_READY / IMPLEMENTATION_PENDING`; migration `NO-GO`

## Taslak

Mevcut v1 journal dosyası yerinde değiştirilmeyecek. Provenance binding için
yeni, ayrı ve bounded target dosyası hazırlanacak. Target’ta mevcut immutable
`profile_revisions` sahibine bağlı şu tablo bulunacak:

```sql
profile_source_snapshots(
  source_snapshot_id TEXT PRIMARY KEY,
  profile_revision_id TEXT UNIQUE NOT NULL,
  source_kind TEXT NOT NULL,
  source_row_id TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  source_schema_revision TEXT NOT NULL,
  observed_time_us INTEGER NOT NULL,
  source_state TEXT NOT NULL
    CHECK(source_state IN ('ACCEPTED','UNKNOWN','QUARANTINED')),
  FOREIGN KEY(profile_revision_id) REFERENCES profile_revisions(revision_id)
)
```

Migration sırası:

1. split kaynakları read-only envanterle;
2. yalnız eksiksiz ve exact profile revision + provenance çiftlerini target’a
   hazırla;
3. FK/unique/hash/state/replay doğrulamasını target üzerinde tamamla;
4. target commit ve reopen kanıtı olmadan public/persistent authority üretme;
5. eksik, UNKNOWN veya conflict satırlarını target authority’sine yükseltme.

## Sınır

Bu faz SQL ve sıralama taslağıdır; mevcut v1 schema version değiştirilmedi,
in-place migration, split-store veri taşıma, source adapter fetch’i ve canlı
venue authority açılmadı. Target schema implementasyonu failure/replay oracle’ı
ve bağımsız inceleme geçmeden başlamayacak.

Son tam proje kapısı `548/548 PASS`; bu fazda üretim kodu değişmedi.

## Sonraki tek iş

Bu target taslağını gerçek production initializer’a dönüştürmeden önce bounded
target oluşturma, FK/unique/hash doğrulaması ve publish edilmeyen failure/restart
testlerini yazmak.
