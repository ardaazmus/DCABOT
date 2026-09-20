# P1.12.f.h.r — Migration source contract karar kapısı

**Tarih:** 2026-09-17  
**Durum:** `CONTRACT_READY / IMPLEMENTATION_PENDING`; migration `NO-GO`

## Karar

Split store’dan v1 journal’a migration ancak her alan için aşağıdaki dört
kanıt birlikte mevcutsa açılabilir:

1. immutable alanın gerçek source authority’si ve source row identity’si;
2. exact decimal/time/state normalization kuralı;
3. profile revision veya event identity ile bağ;
4. eksik, UNKNOWN, conflict ve late verinin quarantine/fail-closed davranışı.

Alan sahipliği şu şekilde ayrıldı:

- **Profile authority:** venue/product/symbol/settlement, margin/position mode,
  effective time, immutable revision, contract-size ve fee/slippage/rounding
  policy revision’ları;
- **Event/execution authority:** event/order/execution identity, sequence,
  profile reference, observed/execution time, fill quantity/price, gross
  commitment, fee/asset, slippage, rounding, payload hash ve state;
- **Reservation authority:** reservation identity, owner/asset, reserved,
  consumed/releasable miktarları, release identity, terminal state, version ve
  source event;
- **Posting authority:** posting identity, source event, cursor, commitment,
  fee/funding, posting state ve checksum.

Mevcut `FuturesDcaEventStore` ve `ReservationLedger` bu sahipliği ve alanların
tamamını taşımadığı için migration varsayılanlarla tamamlanamaz; karar
`NO-GO` olarak korunur.

## Sınır

Bu faz yalnız kaynak sözleşmesi ve kabul şartlarını belirler. Yeni source
adapter, migration, ekonomik default, release transition, venue authority veya
core binding eklenmedi.

## Doğrulama

Mevcut read-only preflight hedefli `1/1 PASS`, son tam proje kapısı
`543/543 PASS` durumundadır. Bu fazda üretim kodu değişmedi.

## Sonraki tek iş

İlk eksik sahiplik olan profile revision + contract-size kaynağı için ayrı,
exact bir source adapter karar kapısı hazırlamak; source bulunamazsa migration’ı
`NO-GO` bırakmaktır.
