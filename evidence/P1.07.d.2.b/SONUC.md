# P1.07.d.2.b — BASE-bound public limit contract readiness

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Bağımsız review: `NOT_RUN`  
Production readiness: `NO`

## Karar

`P1.07.d.2.b` dar kapsamlı bir `SIMPLIFY_WITH_LIMITATION` kararıyla kapatıldı. D.1 strict fixed-limit application policy’si, yalnız açık `historical_demo_btcusdt_1h_v1` fixture profile’ına bağlı, salt-okunur ve persistence’sız bir BASE public contract olarak açıldı. Bu, genel DCA limit desteği veya production execution değildir.

Araştırma paketi dış kanıt olarak değerlendirildi; paketin kendi beyanında local code inspection ve local test execution `0` olduğundan hiçbir öneri doğrudan uygulanmadı. Uygulama kararları mevcut kod, RED → GREEN testleri ve bağımsız ikinci kontrollerle sınandı.

## Uygulanan dar dilim

- `POST /api/historical-runs/simulate-base-limit` eklendi.
- Request strict ve bounded’dır; finansal girişler float değil exact decimal string olmalıdır.
- Profile, dataset, artifact ve config revision eşleşmesi doğrulanır; yalnız explicit historical fixture kabul edilir.
- Sunucu config’inden alınan BASE quantity ile tek BUY `FixedLimitOrder` oluşturulur; istemci original quantity veya role seçemez.
- Public response’ta observation, accepted economic fill/action ve lifecycle state ayrı alanlardır.
- Equality yalnız observation’dır; placement barı fill adayı değildir; strict penetration exact declared limit price’ta fixed slice üretir.
- `INDETERMINATE` durumda action listesi fail-closed biçimde gizlenir ve ambiguity açıkça taşınır.
- `reserve_model=NONE`, `reserve_amount=NOT_MODELED`, `reserve_asset=NOT_APPLICABLE` metadata olarak görünür; numeric reserve hesabı yapılmaz.
- Dataset/artifact/profile/config/order/policy bağını taşıyan deterministik `binding_identity_sha256` üretilir.
- Response `Cache-Control: no-store` taşır ve 256 KiB serialized response sınırı vardır.
- Legacy historical route, mevcut fixed-slice route, profile katalog UI’si, persistence ve frontend akışı genişletilmedi.

## Kanıt zinciri

1. **İddia:** Public adapter observation’ı economic fill gibi yayınlamamalıdır.  
   **Kontrol:** Equality-touch fixture’ı.  
   **Test sonucu:** Observation üretildi, action/fill commit edilmedi; `150/150 PASS`.

2. **İddia:** Placement barı sonraki limit değerlendirmesine dahil edilmemelidir.  
   **Kontrol:** Placement barında limit penetrasyonu, sonraki barlarda uygun olmayan fixture.  
   **Test sonucu:** Fill oluşmadı; `150/150 PASS`.

3. **İddia:** Belirsiz OHLC barı ekonomik action prefix’ini public authority olmadan göstermemelidir.  
   **Kontrol:** Internal ambiguity fixture’ı → public response helper.  
   **Test sonucu:** `INDETERMINATE`, `actions=[]`, ambiguity metadata mevcut; `150/150 PASS`.

4. **İddia:** Aynı ekonomik girdiler aynı public binding kimliğini üretmelidir.  
   **Farklı kontrol:** Aynı payload iki ayrı çağrıda çalıştırıldı.  
   **Test sonucu:** `binding_identity_sha256` eşit ve response `no-store`; `150/150 PASS`.

5. **İddia:** Güvenli sınır ihlalleri genel 500 yerine açık problem response vermelidir.  
   **Kontrol:** `paper` profile, float financial input, off-grid slice ve oversized body.  
   **Test sonucu:** Sırasıyla güvenli rejection / validation / `422` / body-limit rejection; tam suite içinde PASS.

6. **Farklı bağımsız kontroller:** `compileall PASS`, `tools/check_workspace.py PASS`, OpenAPI route check `True`.

## Bilinçli olarak yapılmayanlar

- Explicit numeric reserve ledger ve reserve owner/lifecycle/atomicity.
- SAFETY/EXIT binding, anchor ve coverage’ın genel production adapter’a taşınması.
- Cancellation race, latency, queue, volume participation, stop ve same-bar cancel/fill modeli.
- Persistence, save/reopen/compare ve execution registry/idempotency.
- UI, chart/action marker veya yeni profile katalog akışı.
- Binance testnet/live execution ve gerçek venue replay.

Bu nedenle `production_ready=false` korunur ve P1.07’nin tamamlandığı iddia edilmez.

## Review sonrası güvenli hata-sözleşmesi düzeltmesi

Kaynak-temelli review sırasında yeni endpoint için doğrulanabilir bir contract boşluğu bulundu: request DTO doğrulaması handler’dan önce reddedildiğinde generic `application/json` dönüyor, standart Problem Details ve `Cache-Control: no-store` uygulanmıyordu.

RED ASGI testi bu davranışı `151` testlik suite içinde gösterdi. `RequestValidationError` allowlist’ine `/api/historical-runs/simulate-base-limit` eklendi. GREEN kontrolünde aynı invalid float payload `422`, `application/problem+json`, `REQUEST_VALIDATION_FAILED` ve `Cache-Control: no-store` döndü. Tam regresyon `151/151 PASS`; compile ve workspace PASS.

Scoped Codex Security source scan’ı dört yüzeyi (HTTP boundary, dataset ingestion, historical adapter, offline core/storage) taradı ve eski snapshot’ta reportable bulgu üretmedi. Ancak scan delegated bağımsız worker olmadan çalıştı ve düzeltme scan başladıktan sonra yapıldı; aracın snapshot uyarısı nedeniyle bu sonuç bağımsız acceptance review yerine geçmez. Bağımsız review durumu bu sebeple `NOT_RUN` olarak korunur.

## Değişen dosyalar

- `src/dcabot/server/api.py`
- `src/dcabot/application/historical_base_limit_binding.py`
- `tests/api/test_historical_base_limit_contract.py`
- `tests/api/test_request_limits.py`

## Sonraki tek kapı

Bu dilim için bağımsız review `NOT_RUN` durumundadır. Explicit reserve, SAFETY/EXIT, persistence ve UI ayrı plan kapılarıdır. Plan sırasındaki sonraki geliştirme işi P1.08.a lifecycle authority local inventory olacaktır.
