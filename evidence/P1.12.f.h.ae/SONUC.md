# P1.12.f.h.ae — Greenfield journal event/reservation/posting binding

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`  
**Legacy migration/publish:** `NOT_APPLICABLE`

## Uygulanan minimum dikey dilim

- Yeni greenfield journal schema revision `2` içinde reservation `version`ından
  ayrı exact `release_cursor` alanı eklendi.
- `FuturesDcaEconomicPosting` ve canonical checksum/replay doğrulaması eklendi.
- Kabul edilmiş event, onun reservation/fill-release projection’ı ve economic
  posting cursor’ı tek `BEGIN IMMEDIATE` transaction’ında yazılıyor.
- Event `ACCEPTED` değilse economic posting bağlanmıyor.
- Posting source identity, commitment ve fee event ile eşleşmiyorsa fail-closed
  reddediliyor.
- Posting cursor atlanırsa event, reservation ve posting birlikte rollback
  oluyor.
- Exact duplicate yeniden çalıştırmada `DUPLICATE`; farklı payload/source/cursor
  `CONFLICT/NO_GO` davranışında kalıyor.

## Kanıt

- Mevcut journal schema odak testleri: `10/10 PASS`.
- Yeni greenfield binding testleri: `3/3 PASS`.
- Odak toplamı: `13/13 PASS` (`10` mevcut journal + `3` yeni binding testi).
- Tam proje: `tools/run_checks.py` — `565/565 PASS`.
- `compileall`: `PASS`.
- Workspace: `PASS`, `224` aktif Python dosyası; backup layout `EMPTY_OR_NOT_PLACED`.
- `git diff --check`: whitespace hatası yok; yalnız mevcut LF/CRLF uyarıları.

## Sınır

Bu dilim gerçek venue/funding hesabı, CORE01 economic Store binding’i, API/UI,
recovery lifecycle, partial/cancel/late/UNKNOWN transition otoritesi, Binance
emri veya migration çalıştırmaz. `funding_amount` yalnız çağıranın verdiği
exact posting projection’ı olarak saklanır; venue’den varsayımla üretilmez.

## Sonraki tek iş

`P1.12.f.h.af` — partial/cancel/late/UNKNOWN için explicit release transition
ve release-cursor state machine karar/test kapısı.
