# P1.17.e — Binance public payload normalization (network-free)

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Production readiness: `NO`  
Tarih: 2026-09-10

## 1. Kapsam

P1.17.d’de denetlenen Binance Spot public profile için yalnız ağsız WebSocket payload normalizasyonu eklendi:

- `@trade` payload’ı → `PublicObservation`;
- `@aggTrade` payload’ı → `PublicObservation`;
- açık timestamp unit seçimi: millisecond veya microsecond;
- exact decimal string parse ve proje canonical numeric biçimi;
- explicit Spot/symbol allowlist kapsamı;
- trade/aggregate-trade stream ayrımı;
- `t/a` event identity’si;
- `source_sequence=None` bağlayıcılığı;
- venue event zamanı ile local receive/processing zamanı ayrımı;
- venue yardımcı kimliklerinin ekonomik olmayan metadata olarak korunması.

Bu dilim WebSocket/REST client, TLS/network, reconnect worker, REST catch-up, persistence, API/UI, credential, candidate/order/fill, reserve, fee, PnL ve ekonomik hesap içermez.

## 2. Claim → RED → uygulama → GREEN → bağımsız kontrol

### Claim A — Rapor payload alanları mevcut generic contract’a taşınabilir

**RED:** `dcabot.data_adapters.binance_public` modülü yoktu:

```text
ModuleNotFoundError: No module named 'dcabot.data_adapters.binance_public'
```

**Minimum uygulama:** `src/dcabot/data_adapters/binance_public.py` eklendi. Mevcut `PublicObservation` geriye uyumlu biçimde `stream_type`, `exchange_time_us`, `is_buyer_maker`, trade-order metadata ve aggregate trade range alanlarını opsiyonel olarak taşıyor. Bu alanlar economic authority değildir.

**GREEN:**

- `tests/test_binance_public_normalization.py`: `5/5 PASS`;
- trade ve aggTrade event type ayrımı;
- event ID ve timestamp unit dönüşümü;
- canonical price/quantity;
- symbol/type/missing-field fail-closed;
- `source_sequence=None`.

### Claim B — Timestamp unit’i tahmin edilmemelidir

Normalizasyon API’si `BinanceTimeUnit.MILLISECONDS` veya `BinanceTimeUnit.MICROSECONDS` enum’unu zorunlu kılar. Millisecond modunda exact `×1000`, microsecond modunda değişmeden aktarım yapılır. Enum dışı veya implicit unit kabul edilmez.

Test edilen karşı örnek: microsecond payload’ı millisecond gibi ikinci kez çarpılmıyor.

### Claim C — Binance `t/a` alanları sequence değildir

Trade `t` veya aggregate trade `a` canonical `event_id` olarak string’e çevrilir. `source_sequence` her iki stream için de `None` kalır. Böylece venue ID’lerinin boşluksuz `+1` olduğu varsayılmaz; P1.17.d’deki `NOT_VERIFIED / APPLICATION_POLICY` kararı korunur.

### Claim D — Numeric alanlar float’a uğramadan normalize edilir

`p` ve `q` yalnız string kabul edilir; proje `number()` ve `exact_text()` sınırından geçer. `50000.00` → canonical `50000`, `0.01000000` → `0.01` olur. Float, exponent, NaN, negatif veya sıfır değerler kabul edilmez.

### Claim E — Raw payload bütünlüğü korunur

Raw decoded payload, sorted-key compact JSON ve `allow_nan=False` ile SHA-256 hash’lenir. Hash normalization sonucuna taşınır. Aynı payload için local receive/processing zamanları değişse dahi payload hash ve event identity değişmez.

## 3. Yerel API sınırı

Eklenen public çağrılar:

```text
normalize_binance_trade_payload(..., time_unit=BinanceTimeUnit.MILLISECONDS)
normalize_binance_agg_trade_payload(..., time_unit=BinanceTimeUnit.MICROSECONDS)
```

Her iki çağrı da `allowed_symbols` allowlist’ini caller’dan ister. Örnek symbol listesi veya exchangeInfo sonucu kod içine hard-code edilmedi. Fonksiyonlar yalnız payload dict kabul eder; network veya credential okuyacak hiçbir bağımlılık içermez.

`@aggTrade` payload’ı constituent trade’lere bölünmez. `a` aggregate identity, `f/l` constituent range metadata’sı olarak taşınır; bu ayrım ekonomik fill anlamına gelmez.

## 4. Bağımsız kontrol

Üretim normalizer formülünü kopyalamayan bağımsız fixture, SHA-256 canonical JSON hash’i ve millisecond dönüşümünü ayrıca hesapladı:

```text
INDEPENDENT_BINANCE_NORMALIZATION_ORACLE=PASS
```

Kontrol ayrıca `source_sequence is None` ve `order/fill/pnl/reserve` alanlarının bulunmadığını doğruladı.

## 5. Regresyon ve kapsam kontrolü

```text
tests.test_binance_public_normalization: 5/5 PASS
tools/run_checks.py: 341/341 PASS
compileall: PASS
tools/check_workspace.py: PASS
active_python_files: 142
```

Canlı Binance route’u, WebSocket client’ı veya REST catch-up kodu eklenmedi. `PublicObservation` hâlâ feed cursor/replay sınırında kalır; economic transition tetiklemez.

## 6. Sonuç ve sonraki tek iş

P1.17.e ağsız normalizasyon açısından `LOCAL_PASS` olarak kapanır; production readiness `NO` kalır. Venue’nin canlı teslim, reconnect ve catch-up davranışı bu kod tarafından kanıtlanmış sayılmaz.

Sonraki tek mikro faz:

**P1.17.f — Binance normalized observation → local replay binding (network-free)**

Normalized trade/aggTrade kayıtlarının mevcut bounded replay cursor’ına doğru stream scope, duplicate/conflict ve event-time davranışıyla bağlanması ele alınacak. Ağ, reconnect, REST catch-up, persistence, API/UI ve economic fill yine kapsam dışıdır.
