# Emir, kalıcılık ve kurtarma sözleşmesi

Durum: yeni kökün hedef uygulama sözleşmesi; CORE01 yalnız offline olay/journal alt kümesini uygular. Dış gönderim, hesap-geneli rezerv/outbox ve venue recovery henüz yoktur. Önceki V3 fikirleri sadeleştirildi; P1 simulated ekonomi ve P2 gerçek Binance sınırlarıyla kanıtlanarak uygulanacak.

## Ayrı durumlar

| Eksen | Örnek | Ekonomik anlam |
|---|---|---|
| Komut | Accepted/Rejected | Yerel politika kararı |
| Gönderim bilgisi | Prepared/Unknown/Acknowledged/NoEffectProven | Dış etkinin ne kadar bilindiği |
| Borsa emir yaşamı | New/PartiallyFilled/Filled/Canceled/Expired | Emir bilgisi; fill listesi yerine geçmez |
| İptal talebi | None/Pending/Confirmed/Unknown | Canceled yaşam durumu ile aynı nesne değil |
| Muhasebe kapsamı | Incomplete/Complete/Conflict | Fill/fee/funding kapsama kanıtı |
| Koruma | Required/Working/Degraded/Unknown | Pozisyonun azaltma/stop görünümü |

CANCEL_PENDING ve PARTIALLY_FILLED aynı anda doğru olabilir. Terminal emirden sonra geç gelen benzersiz fill/fee işlenir. Stale snapshot güncel miktarı sessizce geriye götürmez; çelişki reconciliation ister.

## Kimlik

Yerel command_id, attempt_id, outbox effect_id, reservation_id birbirinden ayrıdır. Yerel kimlik ömür boyu tekrar kullanılmaz. Exchange order/trade ID kapsamı adaptörden gelir; başlangıç key: environment+venue/product+account+symbol+ID türü+source ID. Alanların yeterliliği resmî contract/fixture ile kanıtlanır.

WS event dedup ile ekonomik execution dedup farklıdır: aynı trade REST ve WS'den gelebilir. Unique economic key aynıysa payload aynı → ikinci posting yok; aynı key farklı ekonomik payload → conflict, tahmini düzeltme yok. Cumulative filled_qty artışı tek başına fiyat/fee/execution kimliği sağlamaz.

## A — Kabul transaction'ı

1. Idempotency key ve payload digest kontrolü: aynı key/aynı payload aynı sonucu döndürür; farklı payload reddedilir.
2. Hesap revizyonu üzerinde serileştir; risk, config, instrument rules, ownership ve freshness kontrol et.
3. Risk kaynaklarını ayrı ölç: notional, collateral, fee varlığı, açık emir sayısı, exit kapasitesi.
4. Command + rezerv + outbox aynı yerel transaction'da commit olur.
5. Commit'ten sonra accepted döndür. Snapshot zaten venue açık emir yükünü içeriyorsa yerel rezervi watermark ile eşleştir; aynı yükü iki kez düşme.

100 birim politika bütçesinde 70 ve 50 isteyen iki process'ten en fazla biri kabul edilir. Aynı kabulün tekrarı ek 70 yaratmaz. Bu örnek futures marjin formülü değildir.

## B — Gönderim

Kalıcı PREPARED attempt ağdan önce commit edilir: command, client ID, payload digest, config/risk/capability/credential generation, hazırlık zamanı. Secret/imza kaydedilmez. Sender güncel yetki ve account ownership'i kontrol eder, ağ çağrısını açık DB transaction dışında yapar, sonra sonucu kalıcılaştırır.

Crash PREPARED ile POST arasında veya POST ile sonuç commit'i arasında olabilir. Sonucu bulunmayan attempt olası dış etki taşır. Restart outbox'ı kör POST yapmaz. Lease/fence yerel yazmayı sınırlar; borsa fence token'ını uygulamıyorsa ağ sınırında mutlak tek gönderici garantisi vermez. Eski worker durdurulmadan/yoldaki istekler uzlaştırılmadan devir tamamlanmaz.

## C — Dış sonuç

| Durum | İzinli sonraki adım |
|---|---|
| Kesin kabul, order ID | Kaydet; fill/fee ve order gözlemlerini sürdür |
| Transport timeout / belirsiz yanıt | UNKNOWN; aynı ekonomik POST'u tekrarlama; query/stream |
| Belgelenmiş no-effect ret | Yeni attempt ancak güncel risk/yetki ve adapter kuralıyla |
| 429/throttle | Belgelenmiş backoff; belirsiz ekonomik outcome varsa önce çöz |
| Bilinmeyen enum/schema | Karantina/uyarı; varsayılan başarı yok |

HTTP status tek başına evrensel retry tablosu değildir. Örneğin Binance Futures 503 mesaj varyantları farklı execution semantiği taşır; “unknown” çeşidi önce sorgulama gerektirir. Endpoint, ürün ve hata mesajı beraber eşlenir. [Binance General Info](https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/general-info)

## D — Ekonomik kayıt transaction'ı

Normalize observation + dedup sonucu + benzersiz execution + posting + pozisyon/projection + ilgili rezerv değişimi birlikte commit edilir. Crash öncesi hiçbiri veya tamamı görünür; retry ikinci ekonomik etki yapmaz. Raw büyük payload dış dosyada ise içerik önce dayanıklı hale gelir ve transaction referansı onu bağlar; eksik ham veriden “tam kanıt” çıkmaz.

Kısmi fill'de pending yük ilgili kısım için pozisyon yüküne taşınır, kalan emir rezervi korunur. Cancel talebi, lease timeout veya yerel TTL rezerv bırakmaz. Final fill kapsamı ve emir terminal sonucu çözüldüğünde yalnız gerçekten boşa çıkan miktar bırakılır.

Tek kullanımlık onay `consume WHERE used=false AND version=expected` ile aynı ekonomik kabul transaction'ına bağlanır. Eski Approval nesnesini save ederek used=true'yu false'a çevirmek yasaktır. Dış kullanıcı oturumu/onayı sadece boolean değildir.

## Bilgi kapsamı

Query sonucu `Found | NotFoundInScope | Incomplete | Unavailable | Unsupported` ve şu metadata'yı taşır: environment/account/product/symbol, istenen ve kapsanan zaman, pagination/cursor, retention sınırı, as_of, source watermark, complete.

Open-orders boşluğu kapanmış emri dışlamaz. Bir not-found, geç yanıt veya timeout yokluk kanıtı değildir. Tam history de önceki attempt'in ilgili ürün/endpoint/retention aralığını kapsamıyorsa yeniden ekonomik gönderim kanıtı olamaz. Belirsizlik deadline'ı emir tekrarına değil uyarı ve operatör incelemesine gider.

## Başlangıç ve recovery kapısı

Restart'ta varsayılan `allow_new_risk=false`. Sıra:

1. Tek writer sahipliği, DB schema ve kalıcılık doğrulanır.
2. Komut/attempt/rezerv/ledger yüklenir; PREPARED sonucu olmayanlar UNKNOWN olur.
3. Hesap modu, pozisyon, bakiye, plain/algo açık emirler ve ilgili execution/fee kapsamı uzlaştırılır. Boş liste doğrulanmış flat değildir.
4. Kimlik, miktar, yön, symbol, status ve kapsama farkları ayrı blocker olarak kaydedilir.
5. Düzeltme önerisinin üretilmesi yeterli değildir: düzeltme kalıcı uygulanır, yeniden reconciliation yapılır.
6. Yeni risk ancak tüm kritik blocker'lar kapanıp risk/permission/freshness geçerse açılır. İşlem geçmişinin saklama sınırı nedeniyle kanıt kayıpsa manuel işlem gerekir.

Read/reconcile açık kalabilir. Koruyucu azaltma kendi izin/kapsamı doğrulanmışsa ayrı yoldan uygulanabilir. Cancel-all flatten değildir. Sahibi bilinmeyen emri otomatik iptal etme; başka uygulamanın koruyucu emri olabilir. Sahiplik ve niyet belirlendikten sonra kapsamlı cancel veya azaltma yapılır.

JSON checkpoint yalnız hızlandırıcıdır; authoritative ledger yerine geçmez. Checkpoint'te schema_version, commit/config sürümü, son ledger seq/hash gerekir. Dosya bulunamaması temiz hesap anlamına gelmez. Bozuk/eksik snapshot kapalı riskle restore edilir.

## Operasyonel kabul

Crash her transaction/gönderim sınırında denenir; restart sonrası tek komut, tek ekonomik execution, dengeli posting ve doğru rezerv kalır. Manuel müdahale, bağlantı kopması, geç fill, fee düzeltmesi ve UNKNOWN görünürdür. Bu kapılar geçmeden gerçek emir yetkisi genişletilmez.
