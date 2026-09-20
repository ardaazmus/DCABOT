# P1.12.f.h.ag — Durable atomic Futures DCA release transition update

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`  
**Legacy migration/publish:** `NOT_APPLICABLE`

## Uygulanan minimum dikey dilim

- Greenfield journal schema revision `3` içine immutable
  `reservation_releases` history sahibi eklendi.
- Release history satırı ile güncel reservation projection’ı aynı
  `BEGIN IMMEDIATE` transaction’ında güncelleniyor.
- Optimistic `version` ve monotonic `release_cursor` koşulları SQL update
  sınırında korunuyor; cursor gap, history eksikliği ve duplicate conflict
  fail-closed kalıyor.
- Canonical payload + SHA-256 checksum ile release history restart sonrası
  doğrulanarak replay ediliyor.
- Injected release insert failure sonrası history ve reservation projection
  birlikte rollback oluyor.

Bu dilim reservation release authority’sini durable hale getirir; CORE01
economic posting ile release’in tek transaction’a birleşmesi, venue
reconciliation ve canlı Binance emri hâlâ açılmamıştır.

## Kanıt

- Release store + transition + journal schema odak testleri: `17/17 PASS`.
- Tam proje: `tools/run_checks.py` — `572/572 PASS`.
- `compileall`: `PASS`.
- Workspace: `PASS`, `228` aktif Python dosyası; backup layout `EMPTY_OR_NOT_PLACED`.
- Canlı Binance emri, mutation, mainnet, secret veya migration çalıştırılmadı.

## Sıradaki tek iş

`P1.12.f.h.ah` — durable release transition ile economic-posting cursor’ını
aynı transaction’da bağlayan fail-closed acceptance kapısı.
