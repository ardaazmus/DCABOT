# P1.12.f.h.i — Minimum Futures DCA journal schema/migration sözleşmesi

**Tarih:** 2026-09-17  
**Durum:** `CONTRACT_READY / IMPLEMENTATION_PENDING`; production binding `NO-GO`

## Minimum hedef

Futures DCA için Spot journal’dan bağımsız yeni bir `futures_dca_journal_v1`
SQLite dosyası hedeflenir. Mevcut `FuturesDcaEventStore` ve
`ReservationLedger` dosyaları bu migration’ın içine sessizce birleştirilmez;
iki-store durumu production atomicity kanıtı değildir.

Tek bounded transaction içinde aşağıdaki immutable sahiplikler birlikte
commit edilmelidir:

1. **scope/profile:** venue, product, symbol, settlement asset, margin mode,
   position mode, effective time, immutable profile revision ve explicit
   contract-size/multiplier;
2. **event:** event/execution/order identity, local sequence, event kind,
   observed/execution time, canonical payload hash ve replay version;
3. **execution economics:** fill base quantity, effective execution price,
   gross commitment, fee amount/asset, slippage reference ve rounding-policy
   revision;
4. **reservation:** owner/account/version, asset, reserved, consumed,
   releasable amount, release identity ve terminal/quarantine state;
5. **posting:** economic posting identity, source event identity, posting
   cursor, checksum ve posting state.

## Schema invariantleri

- Her immutable scope/profile revision bir kez yazılır; aynı identity farklı
  payload ile gelirse `CONFLICT` olur ve projection ilerlemez.
- Event sequence ve checksum replay sırasında baştan doğrulanır; duplicate
  exact payload no-op, farklı payload fail-closed olur.
- `UNKNOWN`, `LATE`, `CONFLICT` veya eksik fee/slippage/rounding authority
  ekonomik posting ve reservation release üretmez; quarantine kaydı olmadan
  kullanılabilir bakiye artırılamaz.
- `consumed + releasable` ve tüm exact decimal alanlar tek canonical metin
  gösterimiyle saklanır; sessiz float/rounding yoktur.
- Commit başarısızlığında event, reservation ve posting’in hiçbiri görünmez;
  restart replay aynı projection/version üretir.
- Bounded limit, SQLite `application_id` ve `user_version` ile doğrulanır;
  desteklenmeyen schema sürümü açılmaz.

## Migration sınırı

Migration in-place değildir. Önce yeni hedef dosya oluşturulur, kaynak event ve
reservation kayıtları checksum/sequence/profile kapsamı ile doğrulanır, sonra
replay oracle’ı çalıştırılır. Herhangi bir gap, conflict, UNKNOWN veya eksik
immutable alan varsa hedef aktive edilmez; mevcut kaynaklar değişmeden kalır.
Activation ancak doğrulanmış hedefe açık bir revision/cutover kaydıyla yapılır.

Mevcut Spot journal’a tablo eklemek, iki Futures store’u ardışık çağırmak veya
eksik alanları varsayılan değerle doldurmak migration sayılmaz.

## Açık bırakılan ekonomik kararlar

Bu taslak alan sahipliğini ve transaction sınırını belirler; fee asset/fee
hesabı, slippage referansının venue authority’si, rounding kuralları, partial /
cancel / late / UNKNOWN release miktarı ve funding posting formülü için
varsayım yapmaz. Bu kararlar exact oracle ve conflict/replay testleriyle
kanıtlanmadan production implementation açılmaz.

Yeni dependency, credential, canlı çağrı/emir veya dış kaynak eklenmedi.

## Sonraki tek iş

Bu sözleşme için minimum migration validator ve conflict/replay testleri
oluşturulmalı; validator geçmeden gerçek schema/coordinator yazılmamalıdır.
