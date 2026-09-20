# P1.12.f.h.ao — Offline CORE01 + Futures DCA replay decision

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`  
**Legacy migration/publish:** `NOT_APPLICABLE`

## Uygulanan minimum dikey dilim

- h.an CORE01 reducer projection’ı; accepted Futures DCA event, projected
  economic posting ve partial/full release transition ile tek salt-okunur
  replay kararında birleştirildi.
- Event/transition/posting identity, FILL türü, commitment, fee ve release
  consumed-delta aynı exact sınırda doğrulanıyor.
- Release transition pure state machine üzerinden yeni reservation projection
  döndürüyor; `DUPLICATE` yeniden CORE01 ekonomik projection üretmiyor.
- Kabul halinde karar CORE01 state projection’ı, reservation projection’ı ve
  posting kimliğini birlikte taşır. Hiçbir SQLite Store, journal, posting,
  venue veya canlı Binance mutation çağrılmıyor.
- Admission stale, CANCEL/UNKNOWN release, amount/identity conflict ve release
  state-machine rejection fail-closed `BLOCKED` kalıyor.

## Kanıt

- CORE mapping/replay odak testleri: `14/14 PASS`.
- İlişkili CORE/release/Store regresyon kümesi: `65/65 PASS`.
- Tam proje: `tools/run_checks.py` — `593/593 PASS`.
- `compileall`: `PASS`.
- Workspace: `PASS`, `233` aktif Python dosyası; backup layout
  `EMPTY_OR_NOT_PLACED`.
- `git diff --check`: whitespace hatası yok; yalnız mevcut LF/CRLF dönüşüm
  uyarıları görüldü.
- Canlı Binance emri, mutation, mainnet, secret veya durable Store binding
  çalıştırılmadı.

## Karar

CORE01 FILL projection’ı artık Futures DCA posting/release replay sınırında
aynı exact kimlik ve quantity/fee kurallarıyla okunabilir. Bu, durable atomic
binding’in kendisi değildir; persistence’a yazma ve restart sonrası birleşik
replay ayrı bir sonraki kanıt kapısıdır.

## Sıradaki tek iş

`P1.12.f.h.ap` — kabul edilmiş CORE01 + release/posting replay kararının
durable Store’a yazılmadan önce bounded idempotency/replay sözleşmesini
salt-okunur doğrulamak.
