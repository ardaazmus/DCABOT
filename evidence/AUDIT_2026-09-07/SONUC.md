# 2026-09-07 — Kapsamlı ve matematiksel analiz iddia denetimi

## Kapsam ve yöntem

Kullanıcı tarafından sağlanan `kapsamli_analiz.md` ve `matematik_analiz.md` talimat olarak değil, doğrulanması gereken iddia/öneri raporları olarak ele alındı. Kaynak kod, aktif sözleşmeler, mevcut testler, gerçek yerel public artifact ve resmi Binance public-data kaydı karşılaştırıldı.

Kullanıcının istediği kanıt sırası uygulandı: mevcut durum kontrolü → kontrollü test/hesap → farklı bağımsız kontrol → sonuç → yalnız kanıtlanan küçük değişiklik.

## Başlangıç baseline'ı

```text
uv run --frozen python tools/run_checks.py
Ran 82 tests ... OK
```

Baseline sırasında production kodu değiştirilmedi.

## İddia sonuçları

| İddia | Bağımsız kontrol | Sonuç | Karar |
|---|---|---|---|
| H-01: Spot 2025 timestamp milisaniye olabilir | Gerçek yerel ilk bar: `1735689600000000`; parser dönem sınırıyla 24 barı kabul ediyor. Resmi Binance Public Data README, 2025-01-01 sonrası Spot veriyi mikro-saniye olarak ve aynı kline örneğiyle tanımlıyor. | İddia doğrulanmadı; mevcut mikro-saniye sözleşmesi doğru. | Kod ve belge değiştirilmedi. |
| TP/slippage gerçek hedefi kaçırabilir | `qty=1,cost=100,target=5,fee=.001,tick=.01,slippage=.01`: eşik `105.11`, satış fill'i `104.05`, net `3.94595`. | Sayısal fark gerçek; bunun bug olup olmadığı tetikleme-vs-execution sözleşmesine bağlı. | Araştırma olmadan formül değiştirilmedi. |
| `step_multiplier < 1` planı sessizce sıkıştırır | `build_plan` formülü increment'i çarpanla güncelliyor; config yalnız pozitiflik istiyor. | Matematiksel davranış doğru; “yanlış config” sınıflandırması kanıtlanmış bug değil. | Şimdilik değişiklik yok. |
| Gap simülasyonda ayrıca kontrol edilmiyor | `_validate_bar` sıra/OHLC/kapalı bar kontrol ediyor; kalite katmanı gap'i warning olarak raporluyor; simülasyon sabit interval reddetmiyor. | Kod davranışı doğru gözlendi. Ürün politikası (reject/incomplete/warn) açık değil. | Dış araştırma kapısı açıldı. |
| Config gerçek BTC artifact'ta başarı üretemiyor | İlk open yaklaşık `93576`; `base_qty=1` notional `93576`; `max_entry_notional=1000`; ayrıca `leverage=1` ve fee vardır. Önceki gerçek artifact smoke'u `422 REDUCER_POLICY_REJECTED` verdi. | İddia doğru; demo config gerçek artifact ile uyumsuz. | Finansal sizing araştırması olmadan `paper.json` değiştirilmedi. |
| Simulate validation hata formatı tutarsız | Handler path kümesinde simulate yoktu; doğrudan handler kontrolü `application/json`, status 422 verdi. | İddia doğru. | Küçük API düzeltmesi uygulandı ve test edildi. |
| Body limit yalnız validate endpoint'inde | Middleware yalnız `/api/historical-runs/validate` için çalışıyor; diğer küçük JSON POST'lar ortak middleware'den geçiyor. Data-quality kendi Content-Length/20 MiB kontrolüne sahip. | İddia statik olarak doğru; güvenli ortak limit politikası ayrıca tasarım kararı gerektiriyor. | Dış araştırma olmadan ortak middleware eklenmedi. |
| Quality issue listesi sınırsız | Her closed=false satırı ayrı issue üretebiliyor; `MAX_ROWS=100000` var fakat issue sayısı için ayrı limit yok. | İddia doğru; response sözleşmesi etkilenir. | Ayrı güvenlik/contract araştırmasına bırakıldı. |
| TOCTOU: simulate config'i iki kez dosyadan okuyor | `simulate_historical_run` tek `raw_config = _load_config()` nesnesini plan ve parse için tekrar kullanıyor. | Bu iddia mevcut kaynakta yanlış. | Değişiklik yapılmadı. |
| `exact_text` 13–24 basamak yolu test edilmemiş | Bağımsız hesapta `1/10^13` ve `12.3456789012345` başarıyla round-trip; `1/3` beklenen şekilde reddedildi. | Davranış doğru; test kapsamı eksik olabilir fakat production bug kanıtlanmadı. | Şimdilik production değişikliği yok. |

## Uygulanan tek değişiklik

`src/dcabot/server/api.py` içindeki `RequestValidationError` Problem Details path kümesine `/api/historical-runs/simulate` eklendi.

TDD kanıtı:

1. Yeni test yazıldı.
2. Test production değişikliği öncesi beklenen nedenle RED oldu: `application/json != application/problem+json`.
3. En küçük path kümesi değişikliği yapıldı.
4. Odak test GREEN oldu.
5. `tools/run_checks.py` sonucu `83/83 PASS`.
6. `compileall -q src tests` ve `tools/check_workspace.py` PASS.

Test: `tests/api/test_historical_simulation.py::test_simulate_request_validation_uses_problem_details_contract`.

## Dış araştırma gerektiren açık kapı

TP/slippage semantiği, gap policy, offline demo sizing ve FastAPI/Starlette gövde-yanıt sınırları tek anonim promptta toplandı:

`docs/archive/arastirma-promptlari/2026-09-07_Kanitli_Audit_Dis_Arastirma_Promptu.md` (2026-09-20'de arşivlendi; içerik/hash değişmedi)

Bu rapor gelmeden:

- `net_take_profit` veya `target` formülü değiştirilmeyecek;
- `step_multiplier` için yeni kısıt/uyarı eklenmeyecek;
- gap'li koşunun status/response sözleşmesi değiştirilmeyecek;
- `config/paper.json` finansal sizing amacıyla değiştirilmeyecek;
- ortak request-body middleware veya issue truncation sözleşmesi eklenmeyecek.

## Resmi kaynak doğrulaması

- [Binance Public Data README](https://github.com/binance/binance-public-data): Spot 1 Ocak 2025 sonrası timestamp biriminin mikro-saniye olduğunu ve kline örneğini belirtir.
- [Binance Spot API REST dokümantasyonu](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md): API timestamp birimleri ve mikro-saniye seçiminin endpoint bağlamını açıklar; public archive sözleşmesiyle karıştırılmamalıdır.

## Faz kararı

P1.06 hâlâ tek aktif ana fazdır ve kalıcı koşu araştırma raporu beklemektedir. Bu audit, P1.06'yı atlamadı; yalnızca kanıtlanan API tutarsızlığını küçük bakım düzeltmesi olarak giderdi. Araştırma raporu geldikten sonra yine tek bir sonraki mikro faz seçilecek ve her karar için yeniden RED → GREEN → bağımsız kontrol → tam regresyon döngüsü uygulanacaktır.

## 2026-09-07 ek araştırma raporu değerlendirmesi

Kullanıcının sağladığı kapsamlı offline simülasyon audit raporu talimat olarak değil, önceki açık iddiaların araştırma sonucu olarak değerlendirildi. Rapordaki yerel uygulama iddiaları ayrıca mevcut runtime ve kaynak kodla kontrol edildi; rapor tek başına local test kanıtı sayılmadı.

| Karar alanı | Kontrol sonucu | Uygulama kararı |
|---|---|---|
| TP/slippage semantiği | Mevcut `raw_reference` tetikleyici referansı, `fill_price` ise slippage/tick hizalaması sonrası fill olarak kullanılıyor; formül değişikliği için execution-target sözleşmesi kanıtlanmadı. | Formül değiştirilmedi; `docs/VERI_VE_SIMULASYON.md` içinde trigger/fill ayrımı belgelendi. |
| Tarih grid’i | Önce RED testleri gap ve bilinmeyen interval’de hata verdi; preflight sonrası iki test GREEN oldu. | Sabit sözleşmeli `1h` için ekonomik state başlamadan exact grid kontrolü eklendi. Hatalar `DATASET_NOT_CONTIGUOUS` ve `INTERVAL_UNKNOWN`. |
| Demo sizing | Rapor da aktif config’i değiştirmeyi önermiyor; gerçek artifact uyumsuzluğu önceki 422 smoke ile korunuyor. | `config/paper.json` değiştirilmedi; aday sizing ayrı kabul testi gerektiriyor. |
| Request/response sınırları | FastAPI `max_body_size` parametresi yok; kurulu Starlette route katmanında native byte sayacı var. RED testinde preview 5.012 byte gövdeyi handler’a geçirip `422` üretti. | Küçük JSON route’larına native 4 KiB sınırı ve quality issue bounding uygulandı; ortak büyük-error Problem Details/byte bütçesi D3 açık kapıdır. |

### Uygulanan B diliminin kanıtı

`tests/data/test_historical_simulation.py` içinde gap ve bilinmeyen interval testleri, `src/dcabot/application/historical_simulation.py` içindeki preflight değişikliğinden önce beklenen biçimde RED oldu. Değişiklikten sonra odak suite `6/6 PASS` verdi. Son bağımsız doğrulamada `tools/run_checks.py` `85/85 PASS`, `compileall -q src tests` ve `tools/check_workspace.py` PASS verdi.

### Uygulanan D1 gövde sınırı diliminin kanıtı

`tests/api/test_request_limits.py` ile önce preview için RED alındı (`422` yerine beklenen `413`). Native Starlette route wrapper’ı yalnız `/api/preview`, dataset selection/download ve historical simulation JSON route’larına bağlandı. Sonraki odak testleri `4/4 PASS` verdi: preview ve simulation 4 KiB üstünü reddetti, başlıksız parçalı gövde de reddedildi, `data-quality` ayrı upload bütçesiyle çalıştı. Tam regresyon `88/88 PASS`; `compileall` ve workspace kontrolü PASS.

### Uygulanan D2 issue bounding diliminin kanıtı

Önce 210 bozuk satırlı fixture ile RED alındı: response `1.681` issue taşıyordu. `_IssueCollector`, ilk 200 örneği saklayıp tam severity sayaçlarını tuttu; sonuç `200` örnek, `1.681` toplam issue, `1.680` error, `1` warning ve `issues_truncated=true` olarak doğrulandı. Message örnekleri 1.024 UTF-8 byte ile sınırlandı. Frontend yalnız TypeScript sözleşmesine yeni alanları aldı; görsel davranış değiştirilmedi. Kalite suite `7/7 PASS`, tam regresyon `91/91 PASS`, frontend build, compile ve workspace kontrolleri PASS.

D3 açık: quality report/error response toplam byte bütçesi ayrı sözleşme çalışmasıdır.

### Uygulanan D3A Problem Details diliminin kanıtı

Native Starlette body-limit katmanı korunarak, yalnız onun ürettiği 413 yanıtını yerel `_problem` sözleşmesine uyarlayan adapter eklendi. Önce RED testinde `text/plain; charset=utf-8` gözlendi; ardından preview, historical simulation ve başlıksız parçalı preview gövdelerinde `413`, `application/problem+json` ve `REQUEST_TOO_LARGE` doğrulandı. D1/D2 davranışları korunarak tam regresyon `91/91 PASS`, compile ve workspace kontrolleri PASS verdi.

D3B açık: quality report/error response toplam byte bütçesi ve tüm büyük hata kaynaklarının ortak sınırı henüz uygulanmadı.

### Uygulanan D3B quality response byte diliminin kanıtı

40.000 ek CSV header’ı içeren, 20 MiB ham giriş sınırı içinde kalan bir fixture önce response gövdesini 256 KiB üstüne çıkardı. `data-quality` handler’ına serileştirilmiş kalite payload ölçümü eklendi; sınır aşımında rapor yerine `422`, `application/problem+json`, `QUALITY_RESPONSE_TOO_LARGE` ve 256 KiB altında bounded body doğrulandı. Normal valid/rejected kalite response’ları korunarak kalite API+veri suite’i `11/11 PASS`, tam regresyon `92/92 PASS`, compile ve workspace kontrolleri PASS verdi.

D3 tamamlandı. Bu dilim tüm genel hata kaynakları için ayrı bir global response middleware’i iddia etmez; kalite report response sözleşmesiyle sınırlıdır.
