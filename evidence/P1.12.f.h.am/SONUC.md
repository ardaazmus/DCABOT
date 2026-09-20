# P1.12.f.h.am — Offline CORE01 economic FILL boundary admission

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`  
**Legacy migration/publish:** `NOT_APPLICABLE`

## Uygulanan minimum dikey dilim

- Explicitly admitted `FuturesDcaCoreOrderMapping`, accepted Futures DCA fill
  envelope ve projected economic posting tek bir salt-okunur karar kapısında
  birlikte doğrulanıyor.
- Event/posting/profile identity, accepted `FILL` türü, commitment, fee,
  funding, posting state ve fee asset eşleşmeleri fail-closed kontrol ediliyor.
- Futures DCA gross commitment’ın CORE01 `qty * price` sınırında temsil
  edilemediği durumda karar `BLOCKED`; contract-size veya başka bir ekonomik
  varsayım üretilmiyor.
- Mevcut CORE01 order/intent admission’ı geçtikten sonra terminal/UNKNOWN
  order, overfill ve off-grid quantity/price yine `BLOCKED` kalıyor.
- Kabul halinde yalnız değişmez tuple biçiminde CORE01 `FILL` event önerisi
  üretiliyor. `apply`, ekonomik state, posting, persistence, Store veya venue
  mutation çağrılmıyor.

## Kanıt

- CORE mapping/fill admission odak testleri: `10/10 PASS`.
- İlişkili CORE/Store regresyon kümesi: `48/48 PASS`.
- Tam proje: `tools/run_checks.py` — `589/589 PASS`.
- `compileall`: `PASS`.
- Workspace: `PASS`, `233` aktif Python dosyası; backup layout
  `EMPTY_OR_NOT_PLACED`.
- `git diff --check`: whitespace hatası yok; yalnız mevcut LF/CRLF dönüşüm
  uyarıları görüldü.
- Canlı Binance emri, mutation, mainnet, secret, economic posting veya
  CORE01 Store binding çalıştırılmadı.

## Karar

Admitted mapping artık Futures DCA fill envelope ile CORE01 economic `FILL`
sınırında temsil edilebilir bir salt-offline admission kararı verebiliyor.
Bu karar ekonomik reducer geçişi veya durable binding değildir; sonraki aşama
yalnız kabul edilmiş tuple’ın CORE01 reducer projection’ında doğrulanmalıdır.

## Sıradaki tek iş

`P1.12.f.h.an` — admitted CORE01 `FILL` tuple’ını kopya state üzerinde exact
reducer transition olarak doğrulayan, persistence ve venue mutation içermeyen
offline projection kapısı.
