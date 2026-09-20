# P1.12.f.h.u — Immutable provenance schema taslağı

**Tarih:** 2026-09-17  
**Durum:** `CONTRACT_READY / IMPLEMENTATION_PENDING`; schema migration `NO-GO`

## Taslak

Profile revision’dan ayrı immutable `profile_source_snapshots` sahibi önerildi.
Minimum alanlar:

- `source_snapshot_id` primary identity;
- `profile_revision_id` immutable profile foreign key;
- bounded `source_kind` ve `source_row_id`;
- `payload_hash` ve `source_schema_revision`;
- integer `observed_time_us`;
- `source_state` (`ACCEPTED`, `UNKNOWN`, `QUARANTINED`).

Beklenen kısıtlar:

- aynı snapshot identity aynı hash ile exact duplicate, farklı hash ile conflict;
- `profile_revision_id` başına tek accepted source snapshot;
- UNKNOWN/QUARANTINED snapshot profile authority’si olamaz;
- ham payload/secret saklanmaz; yalnız bounded hash ve kimlik tutulur;
- restart replay source identity, hash, state ve revision bağını değiştirmez.

## Sınır

Bu yalnız schema/migration taslağıdır. V1 mevcut tabloya uygulanmadı, schema
version yükseltilmedi, migration çalıştırılmadı ve profile provenance production
authority’si açılmadı. Unique/foreign-key davranışının SQLite failure/replay
testi geçmeden implementation’a alınması `NO-GO` kalır.

Son doğrulanmış proje kapısı `545/545 PASS`; bu fazda üretim kodu değişmedi.

## Sonraki tek iş

Bu tablo taslağını stdlib SQLite failure/replay ve duplicate/conflict oracle’ı ile
bağımsız doğrulamak; ardından schema version/migration binding kararını vermek.
