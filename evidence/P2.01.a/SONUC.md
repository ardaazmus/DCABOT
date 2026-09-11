# P2.01.a — Binance Spot Testnet Public Connectivity ve exchangeInfo Snapshot

## Sonuç

```text
P2.01.a = COMPLETE_WITH_LIMITATION / LOCAL_PASS
IMPLEMENTATION_GATE = ACCEPT_WITH_LIMITATION
TRADING_ACTIVATION = NO-GO
ACCOUNT_CAPABILITY = NOT_IMPLEMENTED
ORDER_PATH = NOT_IMPLEMENTED
PRODUCTION_READINESS = NO
```

Bu dilimde yalnızca Binance Spot Testnet’in kimlik doğrulaması gerektirmeyen
public `exchangeInfo` REST yüzeyi uygulandı. Sembol metadata’sı bounded bir
snapshot’a dönüştürülüyor ve yerel API’den read-only olarak sunuluyor.

## Kapsam ve kesin sınır

Kullanılan tek dış kaynak yolu:

```text
GET https://testnet.binance.vision/api/v3/exchangeInfo?symbol=BTCUSDT
```

Kullanılmayan ve bu dilimde açılmayan yollar:

- API key, secret, `Authorization` veya imza üretimi
- `/sapi/*`
- account veya API-key restriction endpoint’leri
- `/api/v3/order`, `/api/v3/order/test`, cancel veya transfer
- WebSocket market stream/API
- frontend wizard, persistence veya ekonomik hesaplama

Snapshot bir ürün/filtre gözlemidir; hesap yetkisi veya emir yetkisi kanıtı
olarak sunulmaz.

## Uygulanan sözleşme

Yeni adaptör: `src/dcabot/data_adapters/binance_testnet_public.py`

Sabit ve allowlist dışına çıkmayan davranışlar:

- REST tabanı yalnız `https://testnet.binance.vision/api`.
- İstek yalnız `GET` ve `Accept: application/json` ile gönderilir.
- Kullanıcı tarafından URL veya header verilemez.
- Timeout en fazla 30 saniye, varsayılan 5 saniyedir.
- Response byte sınırı 256 KiB’dir; `Content-Encoding` yalnız `identity` olabilir.
- Symbol 1–32 karakterlik, başı/sonu boşluksuz ve kontrol karakteri içermeyen
  UTF-8 metin olarak kabul edilir. Sorgu parametresi UTF-8 percent-encoding ile
  üretilir; istemci ASCII-only sembol varsayımı yapmaz.
- `exchangeInfo` içinden yalnız istenen sembol seçilir.
- `permissions` alanı yoksa boş kabul edilir; bu alan hesap/API-key yetkisi
  olarak yorumlanmaz. `permissionSets`, symbol/exchange filters ve rate limits
  bounded metadata olarak normalize edilir.
- `response_sha256` response bytes’ın SHA-256 değeridir.
- `observed_at_us` yerel gözlem zamanıdır; Binance server zamanı değildir.

Yeni endpoint:

```text
GET /api/venue-snapshots/binance-spot-testnet?symbol=BTCUSDT
```

Yanıt açıkça `environment=BINANCE_SPOT_TESTNET`, `read_only=true` ve
`credential_required=false` alanlarını taşır. Secret, API key, hesap bakiyesi,
emir veya fill alanı taşımaz. Başarısız upstream, malformed response, oversized
response ve bilinmeyen sembol ayrı Problem Details kodlarıyla fail-closed
sonuçlanır.

## Gerçek public endpoint kanıtı

2026-09-11 tarihinde gerçek public endpoint’e yalnızca GET gönderildi.

Gözlenen yanıt özeti:

```text
environment       = BINANCE_SPOT_TESTNET
symbol            = BTCUSDT
status            = TRADING
base_asset        = BTC
quote_asset       = USDT
permissions       = []
permission_sets   = [[SPOT]]
filter_count      = 11
rate_limit_count  = 4
response_sha256   = 836896d316416fe0cc4a9001365aa2df14fdaf0febdb660a3e8f8be3b4d8b937
credentials       = none
```

Canlı yanıtta `permissions` boş geldiği için adapter bunu `SPOT` yetkisi var
şeklinde yorumlamaz. Bu, public ürün snapshot’ının hesap veya key capability
yerine geçmediğine dair önemli bir sınırdır.

## Test ve doğrulama

| Kontrol | Sonuç |
|---|---|
| Public snapshot adaptör/API odak testleri | `7/7 PASS` |
| Tüm Python proje kontrolleri | `366/366 PASS` |
| Python 3.13 compileall | `PASS` |
| Workspace kontrolü | `PASS`, 150 aktif Python dosyası |
| Frontend build | `PASS` |
| FastAPI/ASGI endpoint smoke | `200`, read-only sözleşme PASS |
| Gerçek Binance public GET | `PASS` |
| Gerçek account/signed testnet bağlantısı | `NOT_RUN` |
| Emir/order-test/cancel | `NO-GO`, çalıştırılmadı |

ASGI smoke için yalnızca geçici test bağımlılığı kullanıldı; proje
`pyproject.toml` veya lock dosyasına eklenmedi.

## Resmi kanıt

- [Binance Spot Testnet General Info](https://github.com/binance/binance-spot-api-docs/blob/master/testnet/general-info.md) — testnet REST tabanı, yalnız `/api/*` sınırı, sanal bakiye ve reset kısıtları.
- [Binance Spot REST API](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md) — `exchangeInfo`, public endpoint yüzeyi, symbol/filter ve security type ayrımı.
- [Binance Spot Testnet Changelog](https://github.com/binance/binance-spot-api-docs/blob/master/testnet/CHANGELOG.md) — 2026-09-09 reseti, `CANCEL_ONLY` status değişikliği ve UTF-8/Unicode symbol desteği.
- [Binance Spot Testnet WebSocket Streams](https://github.com/binance/binance-spot-api-docs/blob/master/testnet/web-socket-streams.md) — bu dilimde kullanılmayan ayrı market stream yüzeyi.

## Karar ve sonraki sınır

P2.01.a public connectivity ve read-only `exchangeInfo` snapshot için
uygulama kapısını geçmiştir. Ancak bu sonuç connection wizard’ın, account
capability’nin veya trading activation’ın tamamlandığı anlamına gelmez.

Sıradaki dilim P2.01.b olabilir: public snapshot’ın UI’da salt-okunur ve
hesap/emir capability’sinden ayrı gösterimi. Signed account bağlantısı,
credential injection ve emir yaşam döngüsü için ayrı açık kullanıcı kararı ve
güvenli secret yönetimi gerekir; bu rapor bunları açmaz.
