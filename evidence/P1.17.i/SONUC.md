# P1.17.i — Binance public observation capability boundary

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Production readiness: `NO`  
Tarih: 2026-09-10

## 1. Kapsam

P1.17.e–h ile normalize edilen Binance Spot REST/WS observation’larının yalnız read-only observation ve bounded replay sınırında kaldığı kontrol edildi.

Kontrol edilen sınırlar:

- normalizer dönüşleri `PublicObservation` ile sınırlı;
- replay dönüşü `ReplayResult` ve `FeedCursor` ile sınırlı;
- ekonomik payload alanları observation/replay çıktısına taşınmıyor;
- Binance adapter import graph’ı network veya economic authority modüllerine bağlanmıyor;
- `source_sequence` ve transport/stream scope sınırları korunuyor.

Canlı WebSocket/REST client, reconnect/catch-up, persistence, API/UI, credential, candidate/order/fill, reserve, balance, PnL veya ekonomik transition açılmadı.

## 2. Claim → local kontrol → sonuç

### Claim A — Normalize/replay çıktısı ekonomik authority değildir

REST ve WS normalizer’ları `PublicObservation`, replay ise `ReplayResult` döndürüyor. Bounded test, bu nesnelerde ve accepted history kayıtlarında `candidate_id`, `order_id`, `fill_id`, `reserve`, `balance` ve `pnl` alanlarının bulunmadığını doğruladı.

Untrusted payload içine ekonomik isimli alanlar eklendiğinde de bu alanlar canonical observation’a taşınmadı. Observation `READ_ONLY`, `PUBLIC_MARKET_DATA`, `NO_CREDENTIAL` ve `NO_REAL_ORDER` sınırında kaldı.

### Claim B — Adapter import graph’ı canlı veya ekonomik yola açılmıyor

`binance_public.py` AST import kontrolü yalnız stdlib ile `public_feed` ve exact numeric `numbers` modüllerini gördü. `socket`, `ssl`, HTTP client, `requests`, `websockets`, `dcabot.application` veya `dcabot.core` import’u bulunmadı.

Bu kontrol, gerçek network erişimi yapılmadığını ve ekonomik module graph’ına bağlanılmadığını kanıtlar; transitif runtime davranışının tümünü kanıtlamaz.

### Claim C — Scope boundary sessiz birleşmeyi engeller

REST ve WS aynı event ID’ye sahip olsa bile farklı transport immutable identity nedeniyle silent overwrite gerçekleşmiyor; generic replay `CONFLICT` ile fail-closed kapanıyor. REST/WS normalize edilmiş kayıtlar ekonomik posting’e değil, yalnız observation/replay tiplerine gidiyor.

## 3. RED → GREEN

Bu fazda mevcut implementation iddiası önce local source/import incelemesiyle kontrol edildi. Ekonomik port import’u veya ekonomik dönüş tipi bulunmadığı için production kodu değişikliği gerekmedi. Eksik olan kanıt yüzeyi iki bounded negatif test ile tamamlandı:

- runtime output/capability field isolation;
- AST import graph network/economic module exclusion.

Odak test sonucu:

```text
tests.test_binance_capability_boundary: 2/2 PASS
```

## 4. Bağımsız kontrol

Test kararlarını kopyalamayan ayrı runtime + import-graph oracle çalıştırıldı:

```text
INDEPENDENT_BINANCE_CAPABILITY_BOUNDARY_ORACLE=PASS
```

## 5. Regresyon ve sınır kontrolü

```text
tools/run_checks.py: 355/355 PASS
compileall: PASS
tools/check_workspace.py: PASS
active_python_files: 145
```

Bu kanıt, canlı Binance feed’inin çalıştığını, reconnect/catch-up kapsamının tamamlandığını veya public observation ile paper-trading economic execution’ın hazır olduğunu göstermez. P1.17 canlı transport ve simulated execution hâlâ PLAN/NO-GO sınırındadır.

## 6. Sonuç ve sonraki tek iş

P1.17.i `LOCAL_PASS` olarak kapanır; production readiness `NO` kalır. Public observation capability boundary güvenli biçimde korunuyor.

Sonraki tek mikro faz:

**P1.17.j — Binance public transport activation readiness gate (network-free)**

Mevcut resmi venue kanıtı, local persistence/catch-up ve reconnect önkoşullarıyla karşılaştırılacak; canlı transport açılmadan activation kararı `ACCEPT`, `DEFER` veya `NO-GO` olarak verilecek. Bu kapı geçmeden network client, reconnect worker, REST catch-up veya economic/paper execution yolu yazılmayacak.
