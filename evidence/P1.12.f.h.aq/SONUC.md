# P1.12.f.h.aq — Durable CORE01 replay receipt Store preflight

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / NO_GO_CONFIRMED`  
**Legacy migration/publish:** `NOT_APPLICABLE`

## Uygulanan minimum dikey dilim

- Mevcut greenfield Futures DCA journal read-only incelenerek CORE01 replay
  receipt sahibi için gerekli `core_replay_receipts` schema contract’ı tanımlandı.
- Receipt alanları, fingerprint primary identity ve mapping/event/posting/
  release scope unique constraint’ı birlikte kontrol ediliyor.
- Mevcut schema’da receipt tablosu olmadığı kanıtlandı; preflight
  `BLOCKED` dönüyor ve gerekli tabloyu kendisi oluşturmuyor.
- Fixture üzerinde tam kolon ve iki unique scope bulunduğunda preflight yalnız
  `READY` kararı veriyor; bu karar Store aktivasyonu veya ekonomik binding
  authority’si değil.
- Malformed table, eksik kolon veya eksik unique constraint fail-closed kalıyor.

## Kanıt

- Durable replay Store preflight odak testleri: `3/3 PASS`.
- İlişkili Futures DCA CORE/schema/release kümesi: `43/43 PASS`.
- Tam proje: `tools/run_checks.py` — `599/599 PASS`.
- `compileall`: `PASS`.
- Workspace: `PASS`, `235` aktif Python dosyası; backup layout
  `EMPTY_OR_NOT_PLACED`.
- `git diff --check`: whitespace hatası yok; yalnız mevcut LF/CRLF dönüşüm
  uyarıları görüldü.
- Hiçbir SQLite schema oluşturma/migration, receipt yazımı, restart Store
  aktivasyonu, canlı Binance emri veya venue mutation yapılmadı.

## Karar

Current journal schema receipt owner’ı taşımadığı için durable replay Store
implementasyonu bu kapıda bilinçli olarak `NO_GO` kaldı. Gerekli dış kaynak,
manuel kayıt veya eski migration girdisi yok; sonraki güvenli adım greenfield
journal schema’sına receipt owner’ı ekleyen ayrı migration/replay fazıdır.

## Sıradaki tek iş

`P1.12.f.h.ar` — yalnız greenfield journal için `core_replay_receipts` schema
revision/migration ve exact append/load contract’ını, mevcut event/release/
posting atomicity’sini açmadan uygulamak.
