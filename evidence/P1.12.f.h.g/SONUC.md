# P1.12.f.h.g — Futures DCA tek journal sahiplik kapısı

**Tarih:** 2026-09-17  
**Durum:** `DEFERRED / NO-GO / LOCAL_PASS`

## Karşılaştırma

`SpotBindingStore` tek SQLite bağlantısında `BEGIN IMMEDIATE` ile event,
projection ve reconciliation yazımını birlikte commit/rollback edebilen bir
referans kalıbıdır. Ancak bu store’un sahibi Spot order lifecycle ve CORE01
Spot binding’idir; Futures DCA profile, multiplier, fee/funding, reservation
release ve position commitment schema’sını taşımaz.

`FuturesDcaEventStore` yalnız DCA fill event checksum/sequence/replay’i,
`ReservationLedger` ise yalnız account capacity/reservation projection’ını
taşır. Bunlar ayrı SQLite bağlantılarıdır. Spot journal’a yeni tablo eklemek
veya iki mevcut store’u adapter ile ardışık çağırmak, tek transaction veya
Futures ekonomik authority’si kanıtlamaz.

## Karar

İleride seçilecek tek bounded Futures DCA journal’ının sahibi ayrı bir
Futures-DCA persistence modülü olmalıdır. Migration/revision sınırı en az şu
immutable kapsamları birlikte taşımalıdır:

- venue/symbol/effective-time/profile revision ve multiplier,
- event/execution/order identity ve local sequence,
- gross/effective commitment, fee/slippage/rounding policy,
- reservation owner, consumed/releasable amount ve release identity,
- partial/cancel/late/UNKNOWN quarantine state,
- economic posting cursor, checksum ve restart replay version.

Bu schema ve migration planı yazılmadan mevcut Spot journal yeniden
kullanılmayacak, iki-store workaround’u production binding sayılmayacak ve
yeni persistence coordinator açılmayacaktır.

## Kanıt ve sınır

- `src/dcabot/persistence/spot_binding_store.py`: tek bağlantılı atomic Spot
  transaction kalıbı incelendi.
- `src/dcabot/persistence/futures_dca_event_store.py` ve
  `src/dcabot/application/account_reservation_ledger.py`: ayrı sahiplik ve
  transaction sınırları incelendi.
- Önceki tam proje kontrolü `tools/run_checks.py`: `527/527 PASS`.
- Production kodu, schema, veri, credential, canlı çağrı/emir ve dependency
  değişmedi.

Sıradaki tek iş, yukarıdaki ortak immutable sözleşmeyi bağımsız oracle ve
failure-injection ile doğrulayan migration/transaction contract kararıdır.
