# P1.12.f.h.ap — Offline replay idempotency contract

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`  
**Legacy migration/publish:** `NOT_APPLICABLE`

## Uygulanan minimum dikey dilim

- Accepted CORE01 + Futures DCA replay kararının event, posting, release
  transition ve mapping alanlarından bounded canonical fingerprint üretildi.
- Aynı scope ve aynı fingerprint ile gelen retry yalnız `DUPLICATE` kararı
  alıyor; CORE01 economics yeniden uygulanmıyor.
- Aynı scope altında commitment/fee/payload/transition farkı `CONFLICT`,
  farklı event/posting/release scope’u `BLOCKED` kalıyor.
- Receipt yalnız accepted replay kararından üretilebiliyor; in-memory frozen
  contract’tır, SQLite Store veya journal kaydı değildir.
- Secret, venue transport, Binance mutation, durable write ve restart replay
  authority’si açılmadı.

## Kanıt

- CORE mapping/replay odak testleri: `17/17 PASS`.
- İlişkili CORE/release/Store regresyon kümesi: `68/68 PASS`.
- Tam proje: `tools/run_checks.py` — `596/596 PASS`.
- `compileall`: `PASS`.
- Workspace: `PASS`, `233` aktif Python dosyası; backup layout
  `EMPTY_OR_NOT_PLACED`.
- `git diff --check`: whitespace hatası yok; yalnız mevcut LF/CRLF dönüşüm
  uyarıları görüldü.

## Karar

Replay için exact duplicate, same-scope conflict ve scope conflict ayrımı
durable Store’a yazmadan kanıtlandı. Bu receipt henüz persistence authority’si
değildir; sonraki aşama aynı sözleşmenin bounded durable Store/restart sınırını
ayrı failure/replay kanıtıyla ele almalıdır.

## Sıradaki tek iş

`P1.12.f.h.aq` — replay receipt’in bounded durable Store’a alınması için
schema/idempotency/restart contract karar kapısı; canlı venue binding yok.
