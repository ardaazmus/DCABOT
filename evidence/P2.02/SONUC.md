# P2.02 — Offline attempt/outbox ilk dikey dilimi

## Sonuç

```text
P2.02_FIRST_SLICE = IMPLEMENTED_WITH_LIMITATION
IMPLEMENTATION = LOCAL_PASS
FULL_P2.02 = IN_PROGRESS
REAL_TESTNET_MUTATION = NO-GO
MAINNET = NO-GO
PRODUCTION_READINESS = NO
```

P2.02’nin ilk güvenli diliminde external-operation attempt kimliği, durable
SQLite kaydı, gönderim öncesi kalıcılık şartı ve belirsiz sonuç recovery sınırı
uygulandı. Bu dilim ağ erişimi, API key, secret, imzalı istek veya ekonomik
hesaplama açmaz.

## Uygulanan davranış

- `PREPARED -> PERSISTED` geçişi durable store içinde yapılmadan transport
  çağrısı başlatılamaz.
- `PERSISTED -> SENDING` yalnız atomik state transition ile açılır.
- Ambiguous/timeout/transport failure sonucu `UNKNOWN` olur.
- `UNKNOWN` attempt kör tekrar gönderilemez; yalnız `RECONCILING` durumuna
  geçebilir.
- Process restart sonrasında `SENDING` kayıtları `UNKNOWN` ve
  `RESTART_DURING_SEND` olarak quarantine edilir.
- Aynı attempt kimliğinin aynı içeriği idempotent, farklı içeriği conflict’tir.
- Request fingerprint canonical JSON SHA-256’dır; raw request payload store’a
  yazılmaz.
- Credential, signature, authorization, token ve private-key alanları taşıyan
  payload reddedilir.
- Payload fingerprint’ı 64 KiB serialized byte sınırıyla bounded’dır.
- Venue sabit olarak `BINANCE_SPOT_TESTNET` ile sınırlıdır.
- `ACKNOWLEDGED`, fill veya ekonomik sonuç olarak yorumlanmaz.

## Değişen dosyalar

- `src/dcabot/application/order_attempt.py`
- `src/dcabot/application/order_sender.py`
- `src/dcabot/persistence/attempt_store.py`
- `tests/test_order_attempts.py`

## Kanıt

| Kontrol | Sonuç |
|---|---|
| P2.02 odak testleri | `9/9 PASS` |
| Tüm Python regresyonu | `375/375 PASS` |
| Python 3.13 compileall | `PASS` |
| Workspace kontrolü | `PASS`, 154 aktif Python dosyası |
| Frontend | Bu dilimde değişmedi; P2.01.b build kanıtı geçerli |
| Gerçek Testnet mutation | Çalıştırılmadı |
| API key/secret | Kullanılmadı ve istenmedi |
| Mainnet | Kullanılmadı |

## Sınırlar ve kalan P2.02 işleri

Bu ilk dilim tam P2.02 kabulü değildir. Aşağıdakiler hâlâ uygulanmadı:

- Ed25519/RSA/HMAC signer abstraction ve resmi test vektörleri,
- clock skew ve `recvWindow` politikası,
- Windows Credential Locker/DPAPI sağlayıcısının proje mimarisine bağlanması,
- signed account capability,
- gerçek REST/WS reconciliation,
- API/UI entegrasyonu,
- herhangi bir gerçek Testnet order/cancel çağrısı.

Bu nedenle trading activation `NO-GO` kalır. Sonraki tek küçük iş, gerçek ağ
çağrısı olmadan imzalı istek zaman/credential sınırının ve dummy-key test
vektörlerinin eklenmesidir.

## P2.02.a — Offline signer ve request-time sınırı

```text
P2.02.a_IMPLEMENTATION = IMPLEMENTED_WITH_LIMITATION
P2.02.a_VERIFICATION = LOCAL_PASS
REAL_SIGNED_REQUEST = NO-GO
REAL_TESTNET_MUTATION = NO-GO
```

Bu alt faz, [APPLICATION_POLICY] olarak imzalı REST payload üretiminin ağsız
çekirdeğini ekledi. `HmacSha256Signer` yalnız bellekteki dummy/test anahtarıyla
çalışır; secret `repr`, `SignedRequest` veya durable attempt kaydına taşınmaz.
Parametre sırası korunur, UTF-8 değerler percent-encode edilir, `apiKey`,
`signature`, `timestamp`, `recvWindow` ve credential-bearing parametreler
caller payload’ından reddedilir. İmza sonucu ephemeral `SignedRequest` içinde
ayrı tutulur; HTTP header, URL gönderimi veya transport eklenmemiştir.

`Clock` portu integer Unix milliseconds döndürür. `recvWindow` için bu dilimde
1..60000 integer-millisecond policy uygulanır; default 5000 ms’dir. Zaman
uygunluğu supplied `server_time_ms` ile deterministik kontrol edilir:
request timestamp’i server time’dan en fazla 1 saniye gelecekte olabilir ve
geçmiş farkı `recvWindow` sınırını aşamaz. [OFFICIAL_BINANCE] Binance’ın güncel
REST timing dokümanı da `recvWindow` default/maximum ve bu predicate’i
tanımlar. Bu alt faz microsecond/decimal `recvWindow`, gerçek clock sync,
Ed25519/RSA signer, API-key header injection ve signed account doğrulamasını
bilinçli olarak açmaz.

### Değişen dosyalar

- `src/dcabot/application/signed_request.py`
- `tests/test_signed_request.py`

### Alt faz kanıtı

| Kontrol | Sonuç |
|---|---|
| RED: modül yokken odak test | Beklenen `ModuleNotFoundError` |
| HMAC + bağımsız SHA-256 oracle | PASS |
| UTF-8 payload ve exact signature payload | PASS |
| Unsafe/duplicate/timing parametre reddi | PASS |
| Unknown key type fail-closed | PASS |
| recvWindow boundary | PASS |
| Timestamp boundary ve future tolerance | PASS |
| P2.02.a odak testleri | `6/6 PASS` |
| Gerçek secret/API key | Kullanılmadı |
| HTTP/network/Testnet mutation | Çalıştırılmadı |

### Açık kalanlar

- Ed25519 ve RSA için gerçek private-key provider/signer uygulaması yoktur.
- HMAC signer yalnız offline test abstraction’ıdır; üretim default’u değildir.
- `recvWindow` bu alt fazda integer milliseconds ile sınırlıdır; Binance’ın
  decimal/microsecond seçeneği ayrıca kanıtlanmadan açılmayacaktır.
- API key’in `X-MBX-APIKEY` header’ına bağlanması, signed account capability,
  clock synchronization ve gerçek transport yoktur.
- `P2.02_FULL`, P2.04 reconciliation ve trading activation kapanmamıştır.

## P2.02.b — Ephemeral credential provider ve signed-account sınırı

```text
P2.02.b_IMPLEMENTATION = IMPLEMENTED_WITH_LIMITATION
P2.02.b_VERIFICATION = LOCAL_PASS
WINDOWS_OS_VAULT = NOT_IMPLEMENTED
SIGNED_ACCOUNT_HTTP = NO-GO
```

Bu alt fazda [APPLICATION_POLICY] olarak `CredentialProvider` portu ve yalnız
offline testlerde kullanılabilen `EphemeralCredentialProvider` eklendi. Gerçek
Windows Credential Locker/DPAPI bağlantısı, disk persistence ve OS vault yazımı
yoktur. `CredentialMaterial` secret ve API key’i yalnız süreç belleğinde taşır;
`repr` ve public metadata API key/secret değerlerini içermez.

`AccountCapability` source ayrımı zorunludur. `PUBLIC_VENUE_METADATA` kaynağı
`can_trade` veya `trade_scope_verified` üretemez. `SIGNED_ACCOUNT_CONTEXT` ise
ancak `signed_request_verified=True` ile kurulabilir. Bu, public
`exchangeInfo` snapshot’ının account veya API-key trade yetkisi olarak
yorumlanmasını engeller; signed HTTP response parser’ı veya venue doğrulaması
eklemez.

### Değişen dosyalar

- `src/dcabot/application/credential_boundary.py`
- `tests/test_credential_boundary.py`

### Alt faz kanıtı

| Kontrol | Sonuç |
|---|---|
| RED: modül yokken odak test | Beklenen `ModuleNotFoundError` |
| Ephemeral provider round-trip ve redaction | PASS |
| HMAC credential boş material reddi | PASS |
| Public metadata → account capability engeli | PASS |
| Signed account imza doğrulaması zorunluluğu | PASS |
| Capability nesnesinde secret/API key alanı yok | PASS |
| P2.02.b odak testleri | `6/6 PASS` |
| Gerçek secret/API key | Kullanılmadı; yalnız dummy test material |
| Windows OS vault | Bağlanmadı |
| Signed account HTTP/Testnet mutation | Çalıştırılmadı |

### Güncel P2.02 durumu

P2.02’nin offline attempt/outbox, signer/time ve credential/capability sınır
dilimleri yerel olarak geçmiştir. Buna rağmen full P2.02 kabulü verilmez.
Windows gerçek provider seçimi/entegrasyonu, signed account request/response,
clock synchronization, REST/WS reconciliation, order lifecycle, restart
recovery’nin genişletilmiş matrisi ve açık kullanıcı yetkili Testnet mutation
hâlâ beklemektedir. Trading activation ve mainnet `NO-GO` kalır.

## P2.02.c — Windows Credential Manager HMAC sağlayıcı sınırı

```text
P2.02.c_IMPLEMENTATION = IMPLEMENTED_WITH_LIMITATION
P2.02.c_VERIFICATION = LOCAL_PASS
SIGNED_ACCOUNT_HTTP = NO-GO
REAL_TESTNET_MUTATION = NO-GO
```

Windows’un yerleşik `Advapi32` Credential Manager API’si üzerinden yalnız
geçerli kullanıcı kapsamındaki generic credential okunup yazılabilir. Target
adı `DCABOT:BINANCE_SPOT_TESTNET:<credential_id>` ile bounded’dır; API key
Windows credential kullanıcı alanında, HMAC secret credential blob’ında tutulur.
Secret hiçbir response, log, durable run/attempt kaydı veya repr içine girmez.
CLI yardımcı programı değerleri echo etmeden `getpass` ile alır ve yalnız
redacted kayıt sonucu yazdırır.

Bu dilimde yalnız HMAC key family desteklenir; Ed25519/RSA, signed account
response parser’ı, API/UI bağlantısı, gerçek HTTP/WS ve Testnet mutation hâlâ
uygulanmamıştır. Kullanıcının oluşturduğu gerçek anahtar bu test sırasında
okunmamış ve kullanılmamıştır; odak testi yalnız dummy material ile çalışmıştır.

| Kontrol | Sonuç |
|---|---|
| Windows provider dummy round-trip + redaction | PASS |
| Desteklenmeyen Ed25519 provider family’si | FAIL-CLOSED/PASS |
| P2.02 credential boundary odak testleri | `8/8 PASS` |
| Gerçek Binance API key/secret | Kullanılmadı |
| Signed account HTTP / Testnet mutation | Çalıştırılmadı |

Kullanıcı kurulumu: `uv run --frozen python tools/configure_testnet_credential.py testnet-readonly` komutu yerelde çalıştırılır; API key ve secret terminalde echo edilmeden girilir. Bu komut çalıştırılmadan provider’da gerçek credential bulunması beklenmez.

## P2.02.d — İmzalı Testnet hesap okuması

```text
P2.02.d_IMPLEMENTATION = IMPLEMENTED_WITH_LIMITATION
P2.02.d_VERIFICATION = LIVE_READ_ONLY_PASS
REAL_TESTNET_MUTATION = NO-GO
TRADING_ACTIVATION = NO-GO
```

Windows Credential Manager’daki `testnet-readonly` kaydı, yalnız sabit
`GET https://testnet.binance.vision/api/v3/account` endpoint’ine bağlanan HMAC
adapter’ında kullanıldı. İmzalı query yalnız `timestamp`, `recvWindow` ve
`signature` taşıdı; API key yalnız `X-MBX-APIKEY` header’ında gönderildi.
Adapter, bakiye değerlerini tutmadan yalnız hesap türü, izinler, yetki
boole’ları, bakiye sayısı, response hash’i ve `SIGNED_ACCOUNT_CONTEXT`
capability’si döndürür. Sonuç ephemeral’dır; order, persistence, reconciliation
ve ekonomik posting bağlantısı yoktur.

| Kontrol | Sonuç |
|---|---|
| Fake transport, bağımsız HMAC oracle ve secret redaction | `3/3 PASS` |
| Gerçek Testnet signed account GET | `PASS` |
| Account type / permission | `SPOT` / `SPOT` |
| Account flags | `can_trade=True`, `can_withdraw=True`, `can_deposit=True` |
| Dönen bakiye değerleri | Tutulmadı; yalnız `balances_count=502` |
| Capability | `SIGNED_ACCOUNT_CONTEXT`, imza doğrulama durumu `True` |
| Gerçek Testnet order/mutation | Çalıştırılmadı |
| WebSocket, reconciliation, mainnet | Çalıştırılmadı |

Gerçek çağrı, kullanıcının makinesindeki Credential Manager kaydından yapıldı;
API key ve secret sohbete, loga, Git’e veya kanıt dosyasına yazılmadı. Response
hash’i güvenli kanıt kimliğidir; hesap bakiyesi veya finansal posting kanıtı
değildir. Bu alt faz signed account read-only kabulüdür; full P2.02 ve trading
activation kapanmamıştır.

### P2.02.b kapanış kalite kapısı

`P2.02.b` için tam yerel kontrol `387/387 PASS`, Python 3.13
`compileall=PASS`, workspace kontrolü `PASS` (`158` aktif Python dosyası) ve
frontend production build `PASS` verdi. Frontend veya backend API değişmedi;
bu nedenle yeni browser/AT kanıtı üretilmedi. Gerçek Windows OS vault,
signed-account HTTP, Testnet mutation, NVDA/JAWS ve production readiness
`NOT_RUN/NO` olarak kalır.

## P2.04.a — Offline WebSocket/REST reconciliation ve restart recovery

```text
P2.04.a_IMPLEMENTATION = IMPLEMENTED_WITH_LIMITATION
P2.04.a_VERIFICATION = LOCAL_PASS
REAL_WEBSOCKET = NO-GO
REAL_SIGNED_REST = NO-GO
TRADING_ACTIVATION = NO-GO
```

Bu alt faz yalnız [OFFLINE_ORACLE] fake WebSocket/Fake REST sınırını uygular.
`ReconciliationCoordinator`, public bağlantı ile ekonomik senkronizasyonu ayrı
tutar: reconnect sonrası state doğrudan `SYNCED` olmaz; `UNKNOWN`, `GAP`,
`STALE` veya restart sonrası kayıtlar authoritative REST reconciliation olmadan
ekonomik olarak kullanılabilir kabul edilmez.

WebSocket tarafında global sequence garantisi varsayılmaz. Aynı event fingerprint’i
ile gelen tekrar `DUPLICATE` ve etkisizdir; aynı event ID’nin farklı payload ile
gelmesi `CONFLICT`, eski event zamanı ise `OUT_OF_ORDER` olarak `GAP` durumunu
açar. Ham event payload’ı coordinator içinde saklanmaz; yalnız bounded identity ve
fingerprint tutulur.

Fake REST `FOUND` sonucu UNKNOWN attempt’i yalnız `ACKNOWLEDGED` durumuna taşır;
fill veya ekonomik sonuç iddia etmez. `NOT_FOUND`, `UNAVAILABLE` ve `CONFLICT`
sonuçları `UNRESOLVED` olarak kalır; bunlar reject veya “order kesin yok” anlamına
gelmez ve `SYNCED` kapısını açık bırakmaz. Restart sırasında `SENDING` kayıtları
mevcut store invariant’ı ile `UNKNOWN` olarak karantinaya alınır.

### Değişen dosyalar

- `src/dcabot/application/reconciliation.py`
- `src/dcabot/persistence/attempt_store.py`
- `tests/test_reconciliation.py`

### RED → GREEN ve kalite kanıtı

| Kontrol | Sonuç |
|---|---|
| RED: reconciliation modülü yokken odak test | Beklenen `ModuleNotFoundError` |
| Restart `SENDING -> UNKNOWN` ve sync bloklama | PASS |
| Fake REST `FOUND` ile yalnız ACKNOWLEDGED çözümü | PASS |
| Fake REST `NOT_FOUND` ile UNRESOLVED sınırı | PASS |
| Reconnect sonrası doğrudan SYNCED engeli | PASS |
| Duplicate/out-of-order/conflict event davranışı | PASS |
| P2.04.a odak testleri | `6/6 PASS` |
| Tam Python regresyon | `393/393 PASS` |
| Python 3.13 compileall | PASS |
| Workspace kontrolü | PASS (`160` aktif Python dosyası) |
| Frontend production build | PASS |
| Gerçek WebSocket/signed REST/Testnet mutation | Çalıştırılmadı |

### Açık kalanlar

- Gerçek Binance WebSocket API User Data Stream subscription/reconnect kodu yoktur.
- Gerçek signed REST order query yoktur; Fake REST yalnız recovery oracle’ıdır.
- Event schema, executionReport lifecycle, partial fill ve cancel race P2.03’e
  bırakılmıştır.
- Testnet reset tespiti için coordinator fail-closed geçişi vardır; gerçek
  Testnet reset sonrası canlı recovery kanıtı yoktur.
- NVDA/JAWS, Windows HCM ve yeni browser runtime QA bu backend-only alt fazda
  çalıştırılmadı; önceki UI sınırlaması devam eder.

## P2.04.b — REST/stream disagreement, freshness ve reset quarantine

```text
P2.04.b_IMPLEMENTATION = IMPLEMENTED_WITH_LIMITATION
P2.04.b_VERIFICATION = LOCAL_PASS
REAL_WEBSOCKET = NO-GO
REAL_SIGNED_REST = NO-GO
TRADING_ACTIVATION = NO-GO
```

Bu alt faz [OFFLINE_ORACLE] ile P2.04.a state machine’inin karşı-örneklerini
genişletir. Stream event’indeki order kimliği authoritative REST lookup ile
farklıysa coordinator `GAP` durumuna geçer ve iki kaynaktan birini seçerek
ekonomik sonuç üretmez. `GAP` sonrasında yeni event’ler kabul edilmez; yeniden
bağlanma ve reconciliation gerekir.

Snapshot freshness yaşı inclusive sınırla değerlendirilir: `now - observed >=
max_age` olduğunda state `STALE` olur. Gelecek zaman damgası güvenilir fresh
kanıt sayılmaz ve `UNKNOWN` durumuna alınır. `STALE` otomatik olarak `SYNCED`
veya işlem yapılabilir duruma dönmez.

Testnet reset tespitinde event identity cache temizlenir, state
`RECONCILIATION_REQUIRED` olur ve yeni authoritative snapshot doğrulanmadan
`SYNCED` kapısı açılmaz. Bu alt faz eski ekonomik kayıtları silmez veya yeniden
hesaplamaz; canlı reset sonrası state quarantine/rebuild henüz uygulanmamıştır.

### Değişen dosyalar

- `src/dcabot/application/reconciliation.py`
- `tests/test_reconciliation.py`

### RED → GREEN ve kalite kanıtı

| Kontrol | Sonuç |
|---|---|
| REST/stream order identity disagreement | `GAP`, PASS |
| Freshness inclusive boundary | `STALE`, PASS |
| Reset sonrası yeni authoritative snapshot zorunluluğu | PASS |
| GAP sonrası event quarantine | PASS |
| P2.04.b odak testleri | `10/10 PASS` |
| Tam Python regresyon | `397/397 PASS` |
| Python 3.13 compileall | PASS |
| Workspace kontrolü | PASS (`160` aktif Python dosyası) |
| Frontend production build | PASS |
| Gerçek WebSocket/signed REST/Testnet mutation | Çalıştırılmadı |

### Açık kalanlar

- Binance WebSocket API User Data Stream subscription ve reconnect adapter’ı
  henüz yoktur.
- REST/stream event schema, executionReport lifecycle, partial fill ve cancel
  race P2.03 kapsamındadır.
- Gerçek Testnet reset sonrası durable state quarantine ve rebuild canlı olarak
  doğrulanmadı.
- `SYNCED` yalnız offline coordinator state’idir; account veya order yetkisi
  kanıtlamaz.
