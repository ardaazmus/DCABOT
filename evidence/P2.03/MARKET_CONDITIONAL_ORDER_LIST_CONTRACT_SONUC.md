# P2.03 — MARKET, conditional ve order-list sözleşme araştırması

Tarih: 2026-09-16
Kapsam: Binance Spot resmi sözleşmesi ile mevcut DCABOT ekonomik/venue sınırının karşılaştırılması

## Karar

```text
MARKET_CORE_BINDING = DEFERRED / NO-GO
MARKET_BASE_QUANTITY_CONTRACT = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
CONDITIONAL_LIFECYCLE = DEFERRED / NO-GO
ORDER_LIST_OCO_LIFECYCLE = DEFERRED / NO-GO
NEW_ECONOMIC_CODE = NOT_AUTHORIZED
LIVE_SIGNED_INTEGRATION = NO-GO
REAL_TESTNET_MUTATION = NO-GO
```

Bu araştırma yalnızca resmi, herkese açık Binance dokümantasyonunu kullandı; API
anahtarı, hesap, signed request veya emir çalıştırılmadı.

## Resmi venue bulguları

- Binance Spot sözlüğü `MARKET` emrini mevcut en iyi fiyatlar ve likiditeyle
  eşleştirilen bir emir olarak tanımlar. `quantity` base miktarını, `quoteOrderQty`
  ise harcanacak/alınacak quote miktarını belirtir; gerçekleşen base miktarı piyasa
  likiditesine bağlıdır. Bu nedenle quote bütçesi tek başına ekonomik base fill
  değildir. [Spot API Glossary](https://developers.binance.com/en/docs/products/spot/faqs/spot_glossary)
- Aynı sözlük `stopPrice` alanını STOP_LOSS/TAKE_PROFIT türlerinde emrin ne zaman
  tetiklenip order book’a yerleştirileceğini belirleyen alan olarak tanımlar;
  `STOP_LOSS` tetiklenince MARKET, `STOP_LOSS_LIMIT` tetiklenince LIMIT emri
  oluşturur. Bu, trigger gözlemi ile execution/fill olayının ayrılmasını gerektirir.
  [Spot API Glossary](https://developers.binance.com/en/docs/products/spot/faqs/spot_glossary)
- Binance order-list tanımı birden fazla emrin tek birim olarak gruplanmasını
  içerir. OCO’da bir bacak çalışınca diğer bacak otomatik olarak expire olur;
  working ve pending order rolleri farklıdır. [Spot API Glossary](https://developers.binance.com/en/docs/products/spot/faqs/spot_glossary)
- Spot WebSocket hesap yüzeyi order-list durumunu `orderListId`,
  `listClientOrderId`, `contingencyType`, `listStatusType`, `listOrderStatus` ve
  bacak kimlikleriyle döndürür; açık order-list sorgusu signed USER_DATA yüzeyidir.
  [Spot WebSocket account API](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-api/account)
- User Data Stream aboneliği kimlik doğrulamalı WebSocket yüzeyidir. Bu nedenle
  venue olayının alınması, yerel ekonomik kabul veya canlı entegrasyon kanıtı
  değildir. [Spot User Data Stream](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-api/user-data-stream)

## Mevcut checkout karşılaştırması

| Alan | Yerel gerçek | Sonuç |
|---|---|---|
| MARKET core binding | `domain.engine.Order.limit` zorunlu; `FILL` fiyatı bu limite göre kontrol ediyor; binder yalnız `LIMIT` kabul ediyor. | MARKET etkin fiyatı, quote→base dönüşümü, kümülatif quote ve slippage modeli olmadan ekonomik posting yapılamaz. |
| Conditional | Spot lifecycle’da trigger/activation/gap/trigger sonrası order identity modeli yok; mevcut core event’i yalnız explicit `INTENT` + fill kabul ediyor. | Trigger gözlemi execution adımı yerine geçirilemez; yeni model varsayımla açılamaz. |
| Order-list/OCO | Core `Order` içinde parent/list/leg kimliği yok; lifecycle ve journal tek order kimliği etrafında; list-level state/restart koordinasyonu yok. | Bacaklardan birinin fill/cancel/expire durumunun diğerine etkisi ve atomic replay kanıtlanmadan açılamaz. |

## Açılabilmesi için minimum sözleşme

### MARKET

1. `BASE_QUANTITY` ve `QUOTE_BUDGET` istek birimleri birbirinden ayrılmalı.
2. Her fill için exact base qty, quote qty, effective price, fee asset ve
   cumulative totals korunmalı; quote bütçesi base miktarına varsayımla çevrilmemeli.
3. Partial fill, likidite tükenmesi, slippage sınırı, residual/terminal durum ve
   reconciliation kimliği tanımlanmalı.
4. Core ekonomik event şeması limit emrine özel olmaktan çıkarılmadan binder
   MARKET’i kabul etmemeli.

### Conditional

1. `ARMED → TRIGGERED → EXECUTION_CANDIDATE → ACCEPTED_FILL` ayrımı ve her
   aşamanın sahibi tanımlanmalı.
2. Trigger price, event/effective time, gap/stale davranışı, tetiklenince oluşan
   MARKET veya LIMIT order identity’si ve cancel/expire yarışları belirlenmeli.
3. Trigger tek başına position, PnL veya core fill değiştirmemeli.

### Order-list/OCO

1. `list_id`, `list_client_id`, leg identity, contingency type ve working/pending
   rolü immutable biçimde taşınmalı.
2. List-level state transition, leg fill/cancel/expire koordinasyonu ve
   bireysel bacak iptalinin listeye etkisi tanımlanmalı.
3. Restart/replay sırasında liste ve bacakların tek transaction içinde yeniden
   kurulması, duplicate/conflict ve exactly-once economic posting kanıtlanmalı.

## RED / bağımsız kontrol / kapanış

- **RED:** `tests/test_spot_lifecycle_core_binding.py` içindeki
  `test_market_event_is_not_mapped_to_limit_core`, MARKET olayının mevcut limit
  tabanlı core’a geçirilmediğini gösterir.
- **Bağımsız karşılaştırma:** Resmi venue tanımı MARKET’in likiditeye bağlı
  gerçekleşen miktarını ve order-list’in liste/bacak kimliklerini ayrı gerçekler
  olarak tanımlar; mevcut core bu alanların hiçbirini tam olarak temsil etmiyor.
- **Kapanış:** Mevcut fail-closed sınırı doğru davranıştır. Bu kapı yeni ekonomik
  veya venue kodu eklemeden `LOCAL_PASS` olarak kapanır; uygulama ancak yukarıdaki
  sözleşmeler ayrı bir karar kapısından geçtiğinde açılabilir.

## 2026-09-16 — conditional trigger → execution mikro-görevi

Yerel stop/exit sınırı yeniden denetlendi. `domain.engine` trigger gözlemini
`decision()` ile, executable order identity’sini `INTENT` ile, ekonomik geçişi
`FILL` ile ve terminal venue gözlemini `ORDER_FINAL` ile ayrı tutuyor. Yeni
conditional sınıfı veya venue adapter’ı eklenmedi.

`tests/test_stop_trigger_contract.py` içine eklenen
`test_canceled_stop_keeps_trigger_and_partial_fill_separate`, tetiklenmiş stop
sonrasında `0.4` kısmi fill + `CANCELED` terminal gözleminin yalnızca `0.4`
pozisyon azaltımı yaptığını, kalan `0.6` miktarın yeni STOP kararında kaldığını
ve kalan miktarın sessizce doldurulmadığını doğrular. Bu, trigger’ın execution
ve fill yerine geçirilmesini engelleyen mevcut fail-closed sınırı güçlendirir.

Karar: `CONDITIONAL_TRIGGER_EXECUTION_BOUNDARY = LOCAL_PASS_WITH_LIMITATION`;
gerçek venue conditional identity, gap/stale ve cancel yarışları hâlâ
`DEFERRED / NO-GO` kapsamındadır.

## 2026-09-16 — order-list/OCO mikro-görevi

Aktif kaynak ve test yüzeyi yeniden tarandı. `orderListId`,
`listClientOrderId`, contingency/list status, working/pending rolü veya
list-level replay owner taşıyan aktif bir order-list modeli bulunmadı.
`two_leg_fill_projection.py` mevcutta yalnız HEDGE position identity ve
accepted-fill projection’ıdır; kendi sözleşmesi de bunun order, reserve veya
persistence authority’si olmadığını belirtir. Bu nedenle HEDGE iki-leg modeli
OCO kanıtı olarak sayılmadı.

P1.10.j’deki cancellation confirmation, replacement identity, late-fill
authority ve reserve/commitment owner eksikleri bu checkout’ta hâlâ geçerlidir.
Liste/bacak kimliği ve atomic restart/replay sahibi belirlenmeden OCO adapter’ı
veya yeni ekonomik state yazmak varsayımsal davranış ekler.

Karar: `ORDER_LIST_OCO_LIFECYCLE = DEFERRED / NO-GO / LOCAL_PASS`;
uygulama veya yeni test eklenmedi. Yeniden açılma önkoşulu, önce offline/fake
immutable list/leg state tablosu ile atomic replay owner sözleşmesinin kabul
edilmesidir.

## Yerel doğrulama

```text
uv run --frozen python tools/run_checks.py: 459/459 PASS
uv run --frozen python -O tools/run_checks.py: 459/459 PASS
uv run --frozen python -m compileall -q src tests: PASS
uv run --frozen python tools/check_workspace.py: PASS
frontend npm run build: PASS
```

Bu kayıt canlı Binance transport, signed account, User Data Stream, Testnet
mutation veya mainnet readiness kanıtı değildir.

## 2026-09-16 — MARKET / BASE_QUANTITY offline ekonomik sözleşmesi

İlk açılabilir MARKET dilimi yalnız explicit `BASE_QUANTITY` kabul eder; bunun
`quoteOrderQty` olmadığı özellikle korunmuştur. `MarketBaseExecution`, her fill
için exact base miktarı, gross quote miktarı, türetilmiş effective price, fee ve
fee asset bilgisini immutable biçimde taşır. Toplam base/quote ve weighted
effective price exact hesaplanır; BUY/SELL slippage yönü explicit reference
price ve integer bps sınırıyla kontrol edilir.

Partial fill, residual, `FILLED` coverage, `CANCELED`/`EXPIRED` terminal durumu,
duplicate execution ve farklı payload conflict davranışları fail-closed olarak
kanıtlandı. Non-terminating effective price dış decimal sözleşmesine sessizce
yuvarlanmaz; reddedilir. Bu model core `INTENT/FILL` event’i üretmez, `domain.engine`
limit-price varsayımına bağlanmaz ve quoteOrderQty dönüşümü yapmaz.

```text
MARKET_BASE_QUANTITY_CONTRACT = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
MARKET_CORE_BINDING = DEFERRED / NO-GO
QUOTE_ORDER_QTY = DEFERRED / NO-GO
REAL_TESTNET_MARKET_ORDER = NO-GO
```

Odak testleri `6/6 PASS` verdi. Bir sonraki MARKET açılma kapısı, bu contract’ın
venue execution identity/reconciliation ve core’da limitten bağımsız ekonomik
event şemasıyla ayrıca bağlanmasıdır; bu dilimde yapılmadı.

## 2026-09-16 — MARKET execution identity/reconciliation binding

`MarketBaseExecution` içindeki exact `MarketFill`, mevcut redacted
`VenueSpotEventMappingCandidate` ve `UserDataEvent ↔ OrderLookup` kanıtına yalnız
şu koşullarla bağlanır: lookup `FOUND` ve birebir order kimliği taşımalı, stream
kararı `ACCEPTED` veya `DUPLICATE` olmalı, bağlantı durumu quarantine edilmemeli,
venue event/Spot event/order/execution kimlikleri birebir eşleşmeli ve fill aynı
MARKET execution state’inde bulunmalıdır.

Üretilen `MarketExecutionReconciliationBinding` immutable bir in-memory kanıt
nesnesidir. Core event üretmez, journal’a ekonomik tutar yazmaz, lookup sonucunu
tek başına fill saymaz. Mismatch, `GAP`, `CONFLICT`, `NOT_FOUND` veya farklı
execution payload’ı fail-closed reddedilir.

```text
MARKET_EXECUTION_RECONCILIATION_BINDING = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
MARKET_DURABLE_ECONOMIC_REPLAY = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
MARKET_CORE_BINDING = DEFERRED / NO-GO
```

Odak binding testleri `3/3 PASS` verdi. Durable replay için ayrı bounded SQLite
projection eklendi. `MarketBaseExecution` state’i ve redacted
`MarketExecutionReconciliationBinding` canonical JSON + SHA-256 checksum ile
aynı transaction’da yazılır; aynı venue event duplicate, farklı payload conflict
olarak ele alınır. Immutable execution kimliği/fill prefix’i, binding identity
tekilliği, terminal state, checksum ve hata sonrası rollback doğrulanır.
Restart replay yalnız exact MARKET state ve binding’leri döndürür; core event,
balance, order authority, secret veya canlı taşıma üretmez. Store tek execution
projection’ı ve 1.000 binding sınırıyla bounded’dır.

```text
MARKET_DURABLE_ECONOMIC_REPLAY = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
MARKET_CORE_BINDING = DEFERRED / NO-GO
QUOTE_ORDER_QTY = DEFERRED / NO-GO
REAL_TESTNET_MARKET_ORDER = NO-GO
```

Durable replay odak testleri `5/5 PASS`; tam ve optimize suite `478/478 PASS`.
Limitten bağımsız core ekonomik event şeması, `quoteOrderQty`, conditional ve
order-list/OCO lifecycle ayrı karar kapısı olarak kapalıdır.

## 2026-09-16 — MARKET core binding decision gate

Mevcut guarded `LIMIT → core` binder ile iki MARKET lifecycle biçimi kontrol
edildi: `quoteOrderQty` ve explicit base `quantity`. Her ikisi de
`CORE_ORDER_TYPE_UNSUPPORTED` döndürdü; `core_state`, lifecycle ve `core_events`
değişmedi. Bu, mevcut `domain.engine.Order.limit` zorunluluğu ile `FILL`
limit-fiyat kontrolünün MARKET effective price’ına varsayımla uygulanamayacağını
gösterir.

```text
MARKET_CORE_BINDING = DEFERRED / NO-GO / LOCAL_PASS
```

Core’a geçiş için limitten bağımsız ekonomik event şeması, fee-asset/quantity
authority ve bağımsız oracle gerekir. Bu gereklilikler kanıtlanmadan core binder
genişletilmedi. Core binding odak sınıfı `8/8 PASS`; tam ve optimize suite
`479/479 PASS`.

## 2026-09-16 — Conditional trigger → execution contract

Venue-neutral immutable conditional projection trigger gözlemini explicit
execution order identity’sinden ayırır. `ARMED → TRIGGERED` geçişi yalnız
redacted trigger event kimliği, event zamanı ve gözlenen fiyatla kaydedilir;
execution veya fill üretilmez. `TRIGGERED → EXECUTION_IDENTIFIED` geçişi
explicit `MARKET`/`LIMIT` execution order türü, order kimliği, execution event
kimliği ve zamanı zorunlu kılar.

Aynı trigger/execution payload’ı duplicate olarak idempotenttir; farklı payload
conflict verir. Execution-before-trigger ve out-of-order reddedilir. `GAP`,
`STALE`, `CONFLICT` quarantine’ı trigger kimliğini korur ancak yeni execution’ı
engeller. Explicit cancel confirmation, execution identity sonrası gelen cancel
yarışını sessizce başarı saymaz. Bu projection fill, core event, persistence,
gerçek venue veya mutation authority taşımaz.

```text
CONDITIONAL_TRIGGER_EXECUTION = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
CONDITIONAL_DURABLE_REPLAY = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
CONDITIONAL_VENUE_IDENTITY = DEFERRED / NO-GO
```

Odak trigger/execution testleri `6/6 PASS`. Conditional projection ayrı bounded
SQLite store’da canonical payload + SHA-256 checksum ile persist/replay edilir;
state geçiş sırası atlanamaz, aynı payload duplicate, immutable kimlik değişimi
conflict ve checksum tamper fail-closed’dur. Restart replay yalnız conditional
projection’dır; fill, core event, order authority, secret veya canlı venue
üretmez. Durable replay odak testleri `3/3 PASS`; tam ve optimize suite
`488/488 PASS`.

```text
CONDITIONAL_DURABLE_REPLAY = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
CONDITIONAL_VENUE_IDENTITY = DEFERRED / NO-GO
CONDITIONAL_LIVE_INTEGRATION = NO-GO
```

Venue-specific Binance identity, live User Data Stream ve gerçek conditional
execution ayrı kanıt kapıları olarak kapalıdır.

## 2026-09-18 — SQLite atomic durable replay owner

Önceki in-memory OCO projection, yeni bir venue veya ekonomik authority
eklenmeden `src/dcabot/persistence/order_list_store.py` içindeki bounded SQLite
owner’a bağlandı. Store yalnız şu alanları sahiplenir:

- immutable OCO identity ve iki leg kimliği,
- canonical JSON + SHA-256 checksum’lı observation kayıtları,
- monotonic sequence ve en fazla `128` observation,
- exact duplicate/no-op, farklı payload conflict ve ordered replay,
- `BEGIN IMMEDIATE` içinde append + commit veya rollback.

Create/reopen sonrası aynı `OrderListSnapshot` yeniden üretiliyor. Şema,
metadata, identity, event sequence, payload checksum, identity eşleşmesi,
terminal OCO koordinasyonu ve bozuk kayıtlar restart sırasında fail-closed
doğrulanıyor. Test trigger’ı ile observation insert’i zorla başarısız
olduğunda transaction sonunda kısmi kayıt kalmadığı kanıtlandı.

```text
ORDER_LIST_OCO_IDENTITY = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
ORDER_LIST_OCO_STATE_PROJECTION = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
ORDER_LIST_OCO_DURABLE_REPLAY = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
ORDER_LIST_OCO_LIFECYCLE = DEFERRED / NO-GO
ORDER_LIST_OCO_VENUE_RECONCILIATION = DEFERRED / NO-GO
MARKET_CORE_BINDING = DEFERRED / NO-GO
REAL_SIGNED_ORDER_LIST = NO-GO
REAL_TESTNET_MUTATION = NO-GO
```

`tests/test_order_list_store.py` odak kümesi `4/4 PASS`; OCO contract + store
birleşik odak `8/8 PASS`. Tam `tools/run_checks.py` sonucu `796` testte
`794 PASS`; kalan iki hata Windows Credential Manager ortamındadır: yazma
`1312`, cleanup `CREDENTIAL_NOT_FOUND`. Compileall, workspace (`292` aktif
Python dosyası) ve `git diff --check` PASS. Bu kayıt gerçek signed order-list,
User Data Stream, venue reconciliation, cancel-replace, fill/core posting veya
mainnet readiness kanıtı değildir. Sıradaki asistan-owned güvenli dilim venue
event reconciliation ve cancel-replace identity karar kapısıdır.

## 2026-09-18 — Offline OCO order-list identity/state replay sınırı (ara kayıt)

Resmî Binance glossary ve Spot WebSocket trading sözleşmesi güncel checkout ile
yeniden karşılaştırıldı. OCO’nun iki bacaklı bir order-list olduğu; `orderListId`,
`listClientOrderId`, `contingencyType`, `listStatusType`, `listOrderStatus` ve
working/pending rollerinin ayrı venue gerçekleri olduğu doğrulandı. Kaynaklar:

- [Spot API Glossary](https://developers.binance.com/en/docs/products/spot/faqs/spot_glossary)
- [Spot WebSocket trading requests](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-api/trade)

İlk açılabilir OCO dili `src/dcabot/application/order_list_contract.py` içinde
yalnız venue-fact projection olarak uygulandı:

- immutable `orderListId` + `listClientOrderId` + `OCO` kimliği,
- tam iki bacak ve `WORKING` → `PENDING` rol sırası,
- OCO working/pending order-type sınırı,
- `EXEC_STARTED`/`EXECUTING`/`ALL_DONE`/`REJECT` list durumları ve bounded leg
  status gözlemleri,
- aynı event payload’ında idempotent `DUPLICATE`, aynı event ID ile farklı
  payload’da `CONFLICT`, geriye giden event-time/status’ta fail-closed red,
- `ALL_DONE` için iki terminal bacak ve bir bacak `FILLED` ise diğer bacakta
  `CANCELED`/`EXPIRED`/`EXPIRED_IN_MATCH` koordinasyon kontrolü.

Bu model fiyat, miktar, fee, reserve, fill, core event, cancel-replace veya
transport authority taşımaz. Bounded in-memory observation geçmişi 128 kayıtla
sınırlıdır. Bu bölüm SQLite owner eklenmeden önceki ara kanıt kaydıdır; hemen
üstteki güncel bölümde aynı projection’ın SQLite atomic replay sahibi doğrulandı.

```text
ORDER_LIST_OCO_IDENTITY = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
ORDER_LIST_OCO_STATE_PROJECTION = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
ORDER_LIST_OCO_DURABLE_REPLAY = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
ORDER_LIST_OCO_LIFECYCLE = DEFERRED / NO-GO
MARKET_CORE_BINDING = DEFERRED / NO-GO
REAL_SIGNED_ORDER_LIST = NO-GO
REAL_TESTNET_MUTATION = NO-GO
```

Odak `tests/test_order_list_contract.py` `4/4 PASS` verdi; bu ara kayıt için
P2.03 koruma kümesi `77/77 PASS` geçti. SQLite durable owner’ın güncel sonucu
üstteki bölümde `4/4` ek store testi ve tam `796` testte `794 PASS` olarak
kanıtlanmıştır. Canlı order-list, signed account, User Data Stream
orchestration, core economic posting veya mainnet readiness yine kanıtlanmış
değildir; sıradaki ayrı kapı venue event reconciliation ve cancel-replace
identity davranışıdır.

## 2026-09-18 — Venue event reconciliation ve cancel-replace identity

Resmî [Binance Spot WebSocket account sözleşmesi](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-api/account),
[trade sözleşmesi](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-api/trade)
ve [Spot API Glossary](https://developers.binance.com/en/docs/products/spot/faqs/spot_glossary)
ile karşılaştırma
sonucunda OCO event kimliği `orderListId` + `listClientOrderId` ve leg kimliği
`orderId` + `clientOrderId` olarak sınırlandı. `src/dcabot/application/order_list_reconciliation.py`
yalnız bu identity alanlarını redacted evidence’a bağlıyor:

- exact liste ve leg eşleşmesi `MATCHED`,
- liste veya leg kimliği uyuşmazlığı `CONFLICT`,
- raw payload, fiyat, miktar, fill, fee, reserve ve core event tutulmuyor.

Cancel-replace için resmî `cancelResult`/`newOrderResult` ayrımı immutable
prior/replacement identity ile sınıflandırıldı. İki sonuç da `SUCCESS` ise
replacement kimliği zorunlu `CONFIRMED`; cancel `SUCCESS`, yeni emir `FAILURE`
ise yalnız cancel teyidi kaydediliyor; cancel `FAILURE`, yeni emir `SUCCESS`
ise `CANCEL_REJECTED_NEW_CONFIRMED` dönüyor ve yeniden reconciliation gerekiyor.
Eksik veya tutarsız sonuç `UNKNOWN`; prior identity hiçbir durumda sessizce
replacement’a taşınmıyor. Bu kod venue event’i fill, core posting, economic
state, signed transport veya mutation kabulüne yükseltmiyor.

```text
ORDER_LIST_OCO_VENUE_RECONCILIATION = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
ORDER_LIST_OCO_CANCEL_REPLACE_IDENTITY = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
ORDER_LIST_OCO_DURABLE_EVENT_JOURNAL = DEFERRED / NO-GO
MARKET_CORE_BINDING = DEFERRED / NO-GO
REAL_SIGNED_ORDER_LIST = NO-GO
REAL_TESTNET_MUTATION = NO-GO
```

`tests/test_order_list_reconciliation.py` `5/5 PASS`; OCO contract + durable
store + reconciliation odak kümesi `13/13 PASS`. Tam checker `801` testte
`799 PASS`; iki Windows Credential Manager ortam hatası (`1312`,
`CREDENTIAL_NOT_FOUND`) kaldı. Compileall, workspace (`294` aktif Python
dosyası) ve `git diff --check` PASS. Sıradaki asistan-owned güvenli dilim durable venue-event journal ve
cancel-replace observation sequencing’dir.

## 2026-09-18 — Durable venue-event journal ve observation sequencing

Önceki exact venue reconciliation sonucu artık yeni bir venue veya ekonomik
authority eklenmeden `src/dcabot/persistence/order_list_event_store.py` içindeki
bounded SQLite journal’a bağlandı. Journal şu sınırları birlikte doğrular:

- immutable OCO identity ve exact working/pending leg identity,
- canonical JSON + SHA-256 checksum’lı venue event/cancel-replace observation,
- monotonic sequence ve en fazla `128` observation,
- exact duplicate/no-op; farklı payload veya bozuk kayıt conflict/corrupt,
- out-of-order ve terminal OCO sonrası yeni observation redleri,
- `BEGIN IMMEDIATE` ile append commit veya rollback,
- restart sonrası aynı ordered snapshot’ın yeniden kurulması.

`OrderListEventStore` yalnız redacted venue-fact observation taşır. Fiyat,
miktar, fee, reserve, fill, core event, economic state, signed transport,
order mutation veya User Data Stream orchestration üretmez. Cancel-replace
observation prior/replacement identity’yi OCO identity’sine sessizce taşımaz.

```text
ORDER_LIST_OCO_VENUE_RECONCILIATION = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
ORDER_LIST_OCO_CANCEL_REPLACE_IDENTITY = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
ORDER_LIST_OCO_DURABLE_EVENT_JOURNAL = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS
ORDER_LIST_OCO_LIFECYCLE = DEFERRED / NO-GO
REAL_SIGNED_ORDER_LIST = NO-GO
REAL_TESTNET_MUTATION = NO-GO
```

Kaynak sözleşmeleri: [Binance Spot WebSocket account](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-api/account),
[Binance Spot WebSocket trade](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-api/trade)
ve [Spot API Glossary](https://developers.binance.com/en/docs/products/spot/faqs/spot_glossary).

`tests/test_order_list_event_store.py` odak kümesi `5/5 PASS`; P2.03 OCO
contract + SQLite owner + reconciliation kümesi `18/18 PASS`. Tam checker
`806` testte `804 PASS`; kalan iki hata Windows Credential Manager ortamında
write `1312` ve cleanup `CREDENTIAL_NOT_FOUND`. Compileall, workspace (`296`
aktif Python dosyası) ve `git diff --check` PASS. Bu sonuç gerçek signed
order-list/User Data Stream, core economic posting veya mainnet readiness
kanıtı değildir. Sıradaki asistan-owned güvenli dilim read-only User Data
Stream order-list event parser/adapter contract kapısıydı; bu dilim
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md` altında `27/27 PASS` ile kapandı.
P2.04 parser çıktısının bounded SQLite journal sınırına read-only bağlanması
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md` altında `25/25 PASS` ile kapandı.
Sıradaki asistan-owned güvenli dilim read-only stream sequence/gap quarantine
ve reconnect/catch-up sınırının offline doğrulanmasıdır.
