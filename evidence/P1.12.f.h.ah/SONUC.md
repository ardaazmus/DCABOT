# P1.12.f.h.ah — Durable release + economic-posting atomic binding

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`  
**Legacy migration/publish:** `NOT_APPLICABLE`

## Uygulanan minimum dikey dilim

- Kabul edilmiş `PARTIAL_FILL` ve `FULL_FILL` event’i, release transition’ı,
  reservation projection güncellemesi ve economic posting aynı bounded SQLite
  `BEGIN IMMEDIATE` transaction’ında bağlandı.
- Fill event kimliği transition event’iyle; posting source, commitment ve fee
  alanları event ile; consumed delta da event gross commitment ile birebir
  eşleşmeden yazma yapılmıyor.
- Event, release veya posting yalnız kısmen durable ise işlem fail-closed
  rollback oluyor; tam tekrar `DUPLICATE`, tümü yeni işlem `ACCEPTED` dönüyor.
- Cancel, late fill ve `UNKNOWN` transition’ları ekonomik posting’e bağlanmıyor;
  bunlar release-only sınırında kalıyor. Canlı Binance emri, mutation, mainnet,
  secret, venue reconciliation veya CORE01 canlı binding’i açılmadı.

## Kanıt

- Release transition + durable release store + schema + atomic posting odak
  testleri: `20/20 PASS`.
- Tam proje: `tools/run_checks.py` — `575/575 PASS`.
- `compileall`: `PASS`.
- Workspace: `PASS`, `229` aktif Python dosyası; backup layout
  `EMPTY_OR_NOT_PLACED`.
- Economic posting insert failure injection event, release history ve
  reservation projection’ının birlikte rollback olduğunu doğruladı.
- `git diff --check`: yalnız mevcut LF/CRLF dönüşüm uyarıları; whitespace hatası
  yok.

## Sıradaki tek iş

`P1.12.f.h.ai` — durable economic posting replay’sini CORE01 ekonomik authority
ile güvenli, offline ve fail-closed sınırda bağlayan sonraki mikro-faz.
