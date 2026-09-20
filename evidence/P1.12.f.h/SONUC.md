# P1.12.f.h — Futures DCA atomic binding yeniden açılma sözleşmesi

**Tarih:** 2026-09-17  
**Durum:** `CONTRACT_READY / IMPLEMENTATION_PENDING`

## Seçilen hedef

Mevcut iki ayrı SQLite ledger’ı adapter ile bağlamak yerine, Futures DCA
event, reservation ve fill-release geçişlerinin tek bounded SQLite journal
üzerinde aynı `BEGIN IMMEDIATE` transaction’ında tutulması hedeflenmiştir.
Harici broker veya yeni dış altyapı gerektirmeyen en küçük güvenli seçenek
budur.

## Zorunlu transaction sözleşmesi

Tek transaction içinde şu kayıtlar birlikte ilerlemelidir:

1. local event identity/sequence ve execution dedupe,
2. reservation owner/account version ve active miktar,
3. fill’in gerçekleşen base quantity’si ile quote commitment’ı,
4. partial/cancel/late/UNKNOWN/conflict sonucu reservation reduce/release,
5. varsa fee/funding ve economic posting cursor’ı.

Commit başarısız olursa bu kayıtların hiçbiri görünmemeli; restart replay aynı
projection ve aynı reservation version’ını üretmelidir. Exact duplicate no-op,
farklı payload conflict ve checksum bozulması fail-closed kalmalıdır.

## Uygulama öncesi açık kararlar

- Base→quote commitment hangi fill price, fee asset, fee, slippage ve rounding
  kuralıyla hesaplanacak?
- Partial fill’de kalan reservation ve cancel release miktarı kim tarafından
  exact olarak yazılacak?
- Late/UNKNOWN/conflicting event hangi state’i quarantine edip hangi miktarı
  kullanılabilir bakiyeden çıkaracak?
- Position commitment, economic posting ve reservation transition aynı schema
  içinde hangi immutable identity ile bağlanacak?

Bu sorular cevaplanmadan yeni ekonomik adapter veya iki-store transaction
workaround’u eklenmeyecektir. P1.12.f.g’nin `DEFERRED / NO-GO` kararı geçerlidir;
bu kayıt yalnız yeniden açılma tasarım sınırını belirler.

## Kanıt

`P1.12.f.h.a` failure-injection kapısı, event journal commit’i ile reservation
commit’i arasındaki ayrı SQLite sınırının restart sonrası split state ürettiğini
`1/1 PASS` ile gösterdi. Kanıt: `evidence/P1.12.f.h.a/SONUC.md`.

`P1.12.f.h.b` incelemesi, DCA profile/fill katmanında explicit contract-size
ve multiplier bulunmadığını; mevcut lineer futures matematiğinin ise bunu
zorunlu tuttuğunu doğruladı. Commitment unit kapısı çözülmeden atomic binding
açılmayacak. Kanıt: `evidence/P1.12.f.h.b/SONUC.md`.

- `ReservationLedger` ve `FuturesDcaEventStore` ayrı transaction sınırlarının
  mevcut olduğu yerel kod incelemesiyle doğrulandı.
- Reservation odak testleri `5/5 PASS`, event store odak testleri `4/4 PASS`.
- Son tam proje kontrolü `tools/run_checks.py`: `524/524 PASS`.
- Bu sözleşme için üretim kodu veya veri değişmedi; dış kaynak/bağımlılık
  eklenmedi.
- `P1.12.f.h.a` sonrasında yenilenen tam proje kontrolü `525/525 PASS` oldu.

## Sıradaki tek karar

Contract-size/multiplier için bağımsız oracle `P1.12.f.h.c` ile doğrulandı;
ancak profile-revision, fee/slippage/rounding, partial/cancel/late/UNKNOWN
release ve tek transaction sözleşmeleri hâlâ exact biçimde yazılmadıkça
`P1.12.g` lifecycle ve canlı reservation authority açılmayacaktır.
