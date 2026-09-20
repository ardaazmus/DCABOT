# P1.12.f.h.l — Minimum Futures DCA v1 schema kapısı

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; binding `NO-GO`

## Kanıt

Boş ve inert `futures_dca_journal_v1` SQLite şeması oluşturuldu. Şema,
profile revision, journal event, reservation ve economic posting sahipliklerini
aynı bounded database içinde tanımlar; foreign key, state check, application
id ve schema version ile korunur. Profile/event/reservation/posting satırı
ve ekonomik varsayılan yazılmaz.

Odak test: `tests/test_futures_dca_journal_schema.py` — `2/2 PASS`.

## Sınır

Bu yalnız schema initializer’dır. Mevcut split store’lardan veri taşımaz,
profile revision üretmez, fee/slippage/rounding veya release hesabı yapmaz,
transaction coordinator ve order/fill/live authority açmaz. Existing target
üzerine yazma reddedilir.

Tam proje kontrolü `tools/run_checks.py` — `535/535 PASS` (yükseltilmiş yerel
Windows Credential Manager erişimiyle).

## Sonraki tek iş

Yeni schema üzerinde yalnız immutable profile revision insert/replay validator
oluşturulmalı; event/reservation/posting binding’i ekonomik kararlar
kanıtlanmadan açılmamalıdır.
