# P1.12.f.g — Futures DCA reservation + fill-release atomicity karar kapısı

**Tarih:** 2026-09-17  
**Durum:** `DEFERRED / NO-GO / LOCAL_PASS`

## Karar

Mevcut checkout’ta Futures DCA event journal’ı ile shared-account
`ReservationLedger` ayrı SQLite dosyaları ve ayrı transaction sınırlarıdır.
Bir event append başarılı olup reservation commit veya fill-release sonraki
adımda başarısız olursa iki kaydın biri kalabilir. Bu nedenle bunlar tek
ekonomik geçiş gibi bağlanamaz.

## Doğrulanan eksikler

- `FILL` quantity’si base asset, reservation quote asset’tir; commitment
  dönüşümünün fiyat, fee, slippage ve rounding sahibi dondurulmamıştır.
- Partial fill, cancel, late fill, UNKNOWN ve conflicting duplicate için
  reservation reduction/release identity’si yoktur.
- Event journal’da reservation id, released amount ve atomic posting cursor’ı
  bulunmaz; reservation ledger’da Futures event sequence/economic posting
  sahibi bulunmaz.
- İki ayrı SQLite connection arasında tek transaction veya kanıtlanmış
  transactional outbox/recovery protokolü yoktur.

## Kanıt

- Mevcut `ReservationLedger` account capacity/version ve reservation commit’i
  kendi SQLite transaction’ında koruyor.
- `FuturesDcaEventStore` event checksum/sequence/replay’i ayrı SQLite
  transaction’ında koruyor.
- Reservation ledger odak testleri: `5/5 PASS`.
- Futures DCA event store odak testleri: `4/4 PASS`.
- Son tam proje kontrolü: `tools/run_checks.py` `524/524 PASS`.
- Bu karar için üretim kodu değiştirilmedi; kullanıcı verisi ve canlı hesap
  etkilenmedi.

## Yeniden açılma koşulları

Tek veritabanı transaction’ı veya crash-safe transactional outbox/recovery;
order/fill/reservation identity; base→quote commitment; fee/slippage/rounding;
partial/cancel/late/UNKNOWN/conflict release; dedup ve restart replay
invariant’ları birlikte tanımlanıp bağımsız test edilmeden atomic binding,
Futures DCA lifecycle veya canlı reservation authority açılmayacaktır.

Bu sonuç mevcut küçük projection’ların başarısız olduğu anlamına gelmez;
yalnız bunların production shared-account atomicity kanıtı olmadığını belirtir.
