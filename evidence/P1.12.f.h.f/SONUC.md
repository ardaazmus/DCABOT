# P1.12.f.h.f — Futures DCA partial/cancel/late/UNKNOWN release kapısı

**Tarih:** 2026-09-17  
**Durum:** `DEFERRED / NO-GO / LOCAL_PASS`

## Bulgu

Mevcut Futures DCA event contract’ı yalnız immutable fill event identity,
deal/config revision scope, sequence, execution id, level, quantity ve price
taşır. Reservation kaydı yalnız `reservation_id`, owner, asset ve toplam
amount taşır. Fill event’i reservation identity’si, consumed/releasable
miktar, terminal status, cancel nedeni, late/UNKNOWN sınıfı veya release
cursor’ı taşımıyor.

Bu nedenle partial fill sonrası kalan miktarın, cancel sonrası serbest kalan
miktarın veya late/UNKNOWN olayın kullanılabilir bakiyeden düşülecek miktarın
hangi immutable kayıtla tek kez uygulanacağı belirlenemiyor. Event sequence’i
tek başına release identity değildir.

## Karar

Partial/cancel/late/UNKNOWN release ancak aynı ekonomik transaction içinde
order/fill identity, reservation identity, state transition, consumed ve
releasable exact miktar, quarantine sonucu ve idempotency cursor’ı birlikte
tanımlanınca açılabilir. Eksik venue sonucu `cancel` veya `UNKNOWN` diye
varsayılmayacak; release miktarı zero/current balance ile doldurulmayacak.

Bu kapı geçilmeden Futures DCA lifecycle, reservation release, economic
posting ve canlı reconciliation authority `DEFERRED / NO-GO` kalır.

## Kanıt ve sınır

- `futures_dca_event_contract.py` ve `futures_dca_event_store.py` yalnız fill
  event identity/scope/sequence/replay taşır.
- `account_reservation.py` ve `futures_dca_reservation.py` yalnız candidate
  reservation projection üretir; release/consumption authority yoktur.
- Mevcut Futures DCA zinciri ve tam proje kontrolü `527/527 PASS` olarak
  korunmuştur.
- Production kodu, veri, credential, canlı çağrı/emir ve dependency
  değişmedi.

Sıradaki tek iş, profile revision + multiplier + fee/slippage/rounding ile
bu release identity’sini tek bounded journal transaction sözleşmesinde
birleştirmektir.
