# P1.17.f — Binance normalized observation → local replay binding

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Production readiness: `NO`  
Tarih: 2026-09-10

## 1. Kapsam

P1.17.e’de normalize edilen Binance Spot `@trade` ve `@aggTrade` observation kayıtları, mevcut bounded local replay cursor’ına bağlandı.

Bu dilim yalnızca şunları yapar:

- `binance-spot-public-v3` + `WEBSOCKET` + `SPOT` scope doğrulaması;
- `TRADE` ve `AGG_TRADE` stream scope ayrımı;
- `source_sequence` alanının Binance için `None` kalması;
- mevcut generic replay’in duplicate/conflict ve event-time kurallarının yeniden kullanılması;
- local deterministic replay sonucu üretimi.

WebSocket/REST client, network, reconnect, REST catch-up, persistence, API/UI, credential, candidate/order/fill, reserve, PnL ve ekonomik hesap eklenmedi.

## 2. Claim → RED → uygulama → GREEN

### Claim A — Normalize edilmiş Binance observation generic replay’e güvenli aktarılabilir

**RED:** `replay_binance_observations` çağrısı mevcut değildi:

```text
ImportError: cannot import name 'replay_binance_observations'
```

**Minimum uygulama:** `src/dcabot/data_adapters/binance_public.py` içine ince binding eklendi. Fonksiyon Binance profile/scope ve `source_sequence=None` invariant’ını kontrol ettikten sonra mevcut `replay_observations` fonksiyonuna delegasyon yapar; ikinci bir cursor/replay mantığı oluşturmaz.

**GREEN:** `tests/test_binance_public_normalization.py` `9/9 PASS`.

### Claim B — Duplicate/conflict ve event-time davranışı korunur

Aynı trade payload’ı iki kez replay edildiğinde ikinci kayıt `DUPLICATE` ve accepted count değişmez. Aynı event ID farklı payload hash’i ile geldiğinde `CONFLICT` ve cursor `FAILED` olur. Daha eski event time geldiğinde `OUT_OF_ORDER` ve cursor `GAP` olur. Hiçbir suspect kayıt accepted history’ye eklenmez.

### Claim C — Trade ve aggTrade aynı replay scope’u değildir

Bir cursor’da önce `TRADE`, sonra `AGG_TRADE` geldiğinde ikinci gözlem `WRONG_SCOPE` olur ve cursor `FAILED` durumuna geçer. Böylece farklı stream identity’si sessizce tek akış gibi birleştirilmez.

### Claim D — Binance ID’si sequence olarak bağlanamaz

Replay binding, `source_sequence` alanı dolu olan Binance observation’ı fail-closed reddeder. `t/a` yalnız event identity olarak kalır; örneğin 5000 → 5002 geçişi venue sequence sürekliliği varsayılmadan generic replay’e aktarılabilir.

## 3. Bağımsız kontrol

Üretim replay fonksiyonunun iç karar tablosunu kopyalamayan ayrı fixture kontrolü, beklenen outcome dizisini ve accepted count/state değerini doğruladı:

```text
INDEPENDENT_BINANCE_REPLAY_BINDING_ORACLE=PASS
```

Kontrol edilen beklenen sıra:

```text
ACCEPTED → DUPLICATE → ACCEPTED
accepted_count = 2
final_state = SYNCED
```

## 4. Regresyon ve sınır kontrolü

```text
tests.test_binance_public_normalization: 9/9 PASS
tools/run_checks.py: 345/345 PASS
compileall: PASS
tools/check_workspace.py: PASS
active_python_files: 142
```

Bu sonuç Binance canlı feed’inin veya reconnect/catch-up algoritmasının çalıştığını kanıtlamaz. Replay yalnız local ve caller-supplied deterministic zamanlarla çalışır.

## 5. Sonuç ve sonraki tek iş

P1.17.f `LOCAL_PASS` olarak kapanır; production readiness `NO` kalır. Normalized observation’ın ekonomik fill’e dönüşmesi hâlâ bu proje sınırının dışındadır.

Sonraki tek mikro faz:

**P1.17.g — Binance public profile acceptance matrix (network-free)**

Tek bir bounded acceptance matrix içinde trade/aggTrade mapping, unit mismatch, malformed payload, wrong scope, duplicate/conflict, event-time order, replay ve economic-boundary no-op davranışlarının birlikte kanıtlanması ele alınacak. Canlı transport, reconnect worker, REST catch-up, persistence, API/UI ve economic fill yine kapsam dışıdır.
