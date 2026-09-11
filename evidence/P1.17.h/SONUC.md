# P1.17.h — Binance REST public payload normalization

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Production readiness: `NO`  
Tarih: 2026-09-10

## 1. Kapsam

Yalnızca önceden decode edilmiş Binance Spot public REST kayıtları normalize edildi:

- `/api/v3/trades` tek kayıt mapping’i;
- `/api/v3/aggTrades` tek kayıt mapping’i;
- açık `REST` transport scope’u;
- REST’in `E/exchange event time` alanı taşımadığı için `exchange_time_us=None`;
- explicit millisecond/microsecond timestamp seçimi;
- exact canonical decimal, symbol scope ve event identity;
- REST observation’ın bounded generic replay içindeki duplicate/scope ilişkisi.

Bu fazda HTTP/REST client, network, rate-limit/retry, catch-up, reconnect, persistence, API/UI, credential, candidate/order/fill veya ekonomik hesap açılmadı.

## 2. Claim → RED → minimum uygulama → GREEN

### Claim A — REST payload’ları mevcut canonical observation’a açık REST scope’u ile aktarılabilir

**RED:** REST testleri, beklenen fonksiyonlar henüz bulunmadığı için import aşamasında durdu:

```text
ImportError: cannot import name 'normalize_binance_rest_agg_trade_payload'
```

**Minimum uygulama:** `binance_public.py` içine yalnız decoded tek kayıt kabul eden iki REST normalizer eklendi. `symbol`, allowlist ve zamanlar caller tarafından açık verilir. REST kaydında bulunmayan exchange event time `None` olarak kalır; WS normalizer yeniden kullanılmadı.

**GREEN:** REST normalizasyon testleri `7/7 PASS`.

### Claim B — REST `trades` ve `aggTrades` alanları doğru identity/time/numeric sınırına bağlanır

REST `trades` için `id → event_id`, `time → event_time_us`, `price → price`, `qty → quantity`, `isBuyerMaker → is_buyer_maker` mapping’i doğrulandı. `quoteQty` ve `isBestMatch` payload bütünlüğü için exact/bool guard’dan geçirildi.

REST `aggTrades` için `a → event_id`, `T → event_time_us`, `p/q → price/quantity`, `m → is_buyer_maker`, `f/l → first_trade_id/last_trade_id` mapping’i doğrulandı. `M` bool ve `f <= l` aralığı fail-closed kontrol edildi.

Her iki REST mapping’inde:

- `source_id=binance-spot-public-v3`;
- `transport=REST`, `product=SPOT`;
- `source_sequence=None`;
- fiyat/miktar JSON decimal string olarak exact canonical parse;
- payload hash canonical JSON üzerinden oluşturulur;
- `exchange_time_us` üretilmez.

### Claim C — Timestamp unit hatası ve payload/scope hataları sessiz kabul edilmez

Millisecond modunda ms plausibility guard ve `*1000`, microsecond modunda us plausibility guard ve aynen taşıma doğrulandı. Microsecond değerini millisecond moduna vermek reddedildi; microsecond modunda çift çarpım oluşmadı.

Float price, allowlist dışı symbol ve eksik aggregate identity alanı reddedildi. Symbol query bağlamı allowlist dışında ise REST payload kabul edilmedi.

### Claim D — REST identity’si WS ile sessizce birleştirilmez

Aynı REST kaydının tekrar oynatılması `ACCEPTED → DUPLICATE` üretir. Aynı event ID’ye sahip WS kaydı REST kaydının üzerine yazılmaz; farklı transport immutable identity nedeniyle `CONFLICT` ile fail-closed kapanır. REST `TRADE` ile REST `AGG_TRADE` aynı cursor scope’unda karıştırıldığında `WRONG_SCOPE` oluşur.

## 3. Bağımsız ikinci kontrol

Production karar tablosunu kopyalamayan ayrı expected-outcome kontrolü çalıştırıldı:

```text
INDEPENDENT_BINANCE_REST_NORMALIZATION_ORACLE=PASS
```

Kontrol edilen beklenen sonuçlar:

```text
REST event_id=28457, event_time_us=1700000000000000,
exchange_time_us=None, source_sequence=None
duplicate outcomes = ACCEPTED, DUPLICATE
mixed REST trade/aggTrade scope = ACCEPTED, WRONG_SCOPE
```

## 4. Regresyon ve sınır kontrolü

```text
tests.test_binance_rest_normalization: 7/7 PASS
tools/run_checks.py: 353/353 PASS
compileall: PASS
tools/check_workspace.py: PASS
active_python_files: 144
```

Bu sonuç Binance REST endpoint’ine bağlanıldığını, gerçek response alındığını, catch-up kapsamının tamamlandığını veya ekonomik işlem yolunun açıldığını kanıtlamaz. Yalnız fixture tabanlı mapping ve boundary davranışı kanıtlanmıştır.

## 5. Sonuç ve sonraki tek iş

P1.17.h `LOCAL_PASS` olarak kapanır; production readiness `NO` kalır. REST kayıtları canonical observation’a güvenli, açık ve WS’den ayrık transport scope’u ile aktarılabilir.

Sonraki tek mikro faz:

**P1.17.i — Binance public observation capability boundary (network-free)**

REST ve WS normalize edilmiş observation’ların hiçbir candidate/order/fill/economic authority portuna ulaşmadığını, yalnız read-only observation/replay sınırında kaldığını mevcut local graph ve negatif testlerle kanıtlamak. Canlı network, reconnect/catch-up, persistence, API/UI ve ekonomik hesap yine açılmayacak.
