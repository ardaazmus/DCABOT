# P1.12.f.h.j — Migration validator ve conflict/replay oracle kapısı

**Tarih:** 2026-09-17  
**Durum:** `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; production validator/binding `IMPLEMENTATION_PENDING`

## Kanıt

Bağımsız draft migration oracle şu preflight kurallarını doğruladı:

- profile revision sabit ve sequence kesintisiz olmalıdır;
- event identity duplicate/conflict üretmemelidir;
- reservation identity ve posting cursor bulunmalıdır;
- payload checksum canonical biçimde doğrulanmalıdır;
- `UNKNOWN` veya quarantine state ekonomik migration olarak kabul edilmemelidir;
- geçerli kayıtlar aynı sırada replay edilmelidir.

Odak test: `tests/test_futures_dca_migration_validator_gate.py` — `3/3 PASS`.

## Sınır

Bu test production migration validator değildir; h.i’deki normalized schema
sözleşmesi için bağımsız oracle’dır. Mevcut iki Futures DCA store’u henüz bu
alanları birlikte taşımadığı için gerçek migration/binding açılmadı. Mevcut
Spot journal’a veri aktarımı, varsayılan profile/multiplier veya UNKNOWN için
release uydurulmadı.

Tam proje kontrolü `tools/run_checks.py` — `532/532 PASS` (yükseltilmiş yerel
Windows Credential Manager erişimiyle).

## Sonraki tek iş

Production schema/coordinator yazmadan önce bu validator sözleşmesi gerçek
Futures DCA kaynak tiplerine bağlanmalı ve tam proje testinde doğrulanmalıdır.
