# P2.01 — Binance Spot Testnet Connection Wizard ve Capability Snapshot Araştırması

## Karar

```text
P2.01_RESEARCH = COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED
P2.01_IMPLEMENTATION_GATE = DEFERRED
TRADING_ACTIVATION = NO-GO
PRODUCTION_READINESS = NO
```

P1.20 demo kapısından sonra P2.01 için mevcut kod ve güncel resmi Binance Spot Testnet dokümantasyonu karşılaştırıldı. Araştırma, bağlantı sihirbazının hangi sınırlarla tasarlanabileceğini kesinleştirdi; credential toplama, imzalı istek, testnet emir veya yeni venue kodu bu dilimde açılmadı.

## Yerel kod bulgusu

- `GET /api/health` mevcut durumda `mode=offline` ve `trading_enabled=false` döndürüyor.
- `GET /api/capabilities` mevcut durumda `data_mode=HISTORY_LOCAL`, `execution_mode=SIMULATED` ve `features.testnet=false` döndürüyor.
- `src/dcabot/venue/` altında testnet adapter/transport implementation bulunmuyor.
- Bootstrap sözleşmesi `testnet`, `mainnet`, `read_only` ve benzeri modları fail-closed reddediyor.
- Mevcut run/store filtreleri credential, secret, token, URL ve path alanlarını dışlıyor.
- Bu bulgular P2.01 kodunun doğrudan mevcut P1 offline akışına eklenmemesi gerektiğini gösteriyor.

## Resmi Testnet transport matrisi

| Yüzey | Resmi adres | Kimlik doğrulama | P2.01 kararı |
|---|---|---|---|
| Spot Testnet REST | `https://testnet.binance.vision/api` | Endpoint’e göre | Kabul; yalnız explicit testnet profile içinde |
| Spot Testnet WebSocket API | `wss://ws-api.testnet.binance.vision/ws-api/v3` | Endpoint’e göre | Ayrı transport; market stream ile karıştırılmaz |
| Spot Testnet Market Streams | `wss://stream.testnet.binance.vision/ws` | Public market stream için gerekmez | Ayrı market-data transport |
| Spot Testnet market-only stream | `wss://data-stream.binance.vision` | Credential yok | User Data Stream değildir |
| `/sapi/*` | Spot Testnet’te desteklenmiyor | — | Kalıcı NO-GO |

Binance’ın resmi Testnet General Info sayfası yalnız `/api/*` endpoint’lerinin desteklendiğini, sanal bakiyelerin taşınamayacağını ve testnet’in periyodik olarak sıfırlanabildiğini belirtir. Bu nedenle testnet account state’i kalıcı ekonomik gerçeklik olarak sunulamaz.

## Capability ve filter snapshot sözleşmesi

P2.01 için ilk güvenli snapshot iki farklı authority olarak tutulmalıdır:

### 1. Ürün/symbol/filter snapshot

Public `GET /api/v3/exchangeInfo` sonucundan, explicit testnet ortamı altında:

- symbol
- status
- baseAsset / quoteAsset
- `permissions` veya `permissionSets`
- symbol filters (`PRICE_FILTER`, `LOT_SIZE`, `MIN_NOTIONAL` ve response’ta gerçekten gelen diğer filtreler)
- exchange rate limits
- snapshot alınma zamanı ve response hash’i

alınabilir. Bu snapshot, hesabın emir yetkisini kanıtlamaz; yalnız testnet’in o andaki ürün ve kural yüzeyini gösterir.

### 2. Account/key capability snapshot

Signed `USER_DATA` account yüzeyinden alınan sonuç ayrı tutulmalıdır. Account endpoint’i için:

- `accountType`
- account response’unda gerçekten bulunan permission/capability alanları
- `canTrade` benzeri alanlar response’ta gerçekten mevcutsa
- testnet ortamı
- alınma zamanı
- redakte response hash’i

gösterilebilir. API key veya secret değeri snapshot’a yazılmaz.

`/api/v3/myFilters` account’a özel filtreleri sorgulayan `USER_DATA` yüzeyidir; testnet yalnız `/api` desteklediği için P2.01’de `/sapi/v1/account/apiRestrictions` kullanılamaz. Account-level permission ile key-level permission aynı şey kabul edilmemelidir.

## Bağlantı sihirbazı için kesin sınır

İlk UI akışı şu adımlarla sınırlı olmalıdır:

1. Ortam seçimi: `BINANCE_SPOT_TESTNET`.
2. Kullanıcıya testnet olduğu ve bakiyelerin sanal olduğu açıkça gösterilir.
3. Credential girişi frontend’in ekonomik/run state’ine bağlanmaz.
4. Connection test yalnız yapılandırılmış testnet endpoint’ine gider.
5. Public exchange/symbol/filter snapshot ile signed account capability snapshot ayrı kartlarda gösterilir.
6. Eksik, çelişkili veya yetkisiz sonuç `UNKNOWN`/`BLOCKED` olarak kalır; UI olumlu capability uydurmaz.
7. Snapshot sonucu emir göndermez, emir doğrulama isteği başlatmaz, bakiye taşımaya çalışmaz.

Önerilen ilk capability durumu:

```text
NOT_CONFIGURED → CONNECTING → CONNECTED_READ_ONLY
                              ├→ CAPABILITY_PARTIAL
                              ├→ BLOCKED
                              └→ FAILED
```

`CONNECTED_READ_ONLY`, yalnız bağlantı ve izin okumasının başarılı olduğunu ifade eder. `TRADE` veya `USER_DATA` capability’si gerçek signed response olmadan `true` yapılamaz.

## Güvenlik ve ekonomik authority kuralları

- API key/secret frontend bundle’ına, URL’ye, log’a, saved run’a, config hash’ine veya rapor çıktısına girmez.
- Secret değeri hiçbir API response’unda geri döndürülmez.
- P2.01 connection state’i historical run identity’sinden ayrıdır.
- Theme, view, connection label ve snapshot hash ekonomik sonuç üretmez.
- `exchangeInfo` filtresi frontend’de order candidate veya fill oluşturmaz.
- `/api/v3/order`, `/api/v3/order/test`, cancel, account mutation ve transfer endpoint’leri bu araştırmada çalıştırılmadı.
- Testnet sanal bakiyesi local reserve veya PnL authority olarak kullanılmaz.
- Testnet reset’i sonrasında eski snapshot otomatik olarak güncel capability sayılmaz; yeniden doğrulama gerekir.

## Neden implementasyon ertelendi?

| Açık konu | Durum | Etki |
|---|---|---|
| Secret saklama/enjeksiyon yöntemi | NOT_VERIFIED | Credential yolu güvenli seçilmeden kod yazılamaz |
| HMAC/RSA/Ed25519 seçimi | NOT_SELECTED | İmza adapter’ı ve key lifecycle değişir |
| Account/key permission response mapping’i | PARTIAL | Account capability ile key capability ayrımı gerekir |
| Testnet runtime bağlantı kanıtı | NOT_RUN | Venue yeteneği gerçek test sayılmaz |
| Symbol/filter snapshot persistence | DEFER | Immutable snapshot şeması gerekir |
| Order/fill/reconciliation | NO-GO | P2.01 connection wizard kapsamı dışı; P2.02–P2.04 |

Bu nedenle minimum sonraki uygulama dilimi, gerçek emir içermeyen `P2.01.a` testnet public connectivity + exchangeInfo snapshot sözleşmesi olmalıdır. Signed account snapshot ancak secret enjeksiyon yöntemi ve kullanıcı tarafından yapılacak kontrollü testnet bağlantısı açıkça onaylandıktan sonra ele alınmalıdır.

## Resmi kaynaklar

1. [Binance Spot Testnet General Info](https://github.com/binance/binance-spot-api-docs/blob/master/testnet/general-info.md) — testnet REST/WS adresleri, yalnız `/api` desteği, sanal bakiye, reset ve genel testnet kısıtları.
2. [Binance Spot Testnet WebSocket Streams](https://github.com/binance/binance-spot-api-docs/blob/master/testnet/web-socket-streams.md) — market stream endpoint’i, ping/pong, 24 saat bağlantı ve timestamp davranışı.
3. [Binance Spot REST API](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md) — public endpoint, `exchangeInfo`, account security type ve filter response yüzeyi.
4. [Binance Spot WebSocket API](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-api.md) — WebSocket API base endpoint’i ve security type ayrımı.
5. [Binance Spot Testnet enums](https://github.com/binance/binance-spot-api-docs/blob/master/testnet/enums.md) — testnet symbol status ve permission enum’ları.

## Nihai sonuç

P2.01’in araştırma/karar kısmı ve P2.01.a public snapshot alt dilimi tamamlandı. Testnet endpoint ve snapshot sınırları resmi kaynaklarla yeterince tanımlı; ancak mevcut proje güvenli credential injection’ı, runtime signed account bağlantısını ve trading activation’ı içermiyor. Bu nedenle tam P2.01 connection wizard implementasyonu `DEFERRED`, trading activation `NO-GO` olarak korunur. P2.01.a kanıtı `evidence/P2.01.a/SONUC.md` içindedir. Bir sonraki küçük dilim: public snapshot’ın UI’da salt-okunur gösterimi için P2.01.b karar/uygulama kapısı.
