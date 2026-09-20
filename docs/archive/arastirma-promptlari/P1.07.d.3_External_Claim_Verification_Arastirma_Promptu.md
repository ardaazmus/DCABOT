# Anonim Araştırma Promptu

## Konu

OHLCV tabanlı tarihsel bir DCA simülatöründe aşağıdaki teknik iddianın bağımsız ve kaynaklı olarak doğrulanması:

> Strict fixed-limit historical observation policy’si henüz DCA state-machine’e güvenli bir adapter olarak bağlanmış değildir. Reserve lifecycle, BASE-only end-to-end economic posting ve binding invariant’ları kanıtlanmadan production binding uygulanmamalıdır.

Bu çalışma bir proje kod incelemesi değildir. Herhangi bir özel repository, ürün adı, kurum, kullanıcı, dosya yolu, API anahtarı veya gizli bilgi varsaymayın. Amaç, iddianın genel teknik doğruluğunu ve güvenli bir DCA tarihsel simülasyonunda hangi kanıtların zorunlu olduğunu incelemektir.

---

## 1. Araştırma sınırı

Yalnız şu kapsamı araştırın:

- long-only DCA/averaging-down stratejisi,
- BASE entry order,
- SAFETY ve EXIT rollerinin neden ayrı tutulması gerektiği,
- OHLCV’den türetilen strict fixed-limit gözlemi,
- synthetic fill candidate ile ekonomik FILL event’inin ayrılması,
- exact quantity/price/fee muhasebesi,
- pending order, partial fill, remaining quantity ve terminal order state,
- reserve/risk commitment yaşam döngüsü,
- anchor ve safety coverage sahipliği,
- duplicate/late fill ve idempotency,
- placement barı ile eligible bar ayrımı,
- aynı-bar belirsizliği ve EOF davranışı.

Şu konular araştırma dışıdır:

- gerçek exchange connector, Binance/Coinbase hesabı veya API entegrasyonu,
- testnet/live trading,
- order-book, queue priority veya liquidity replay,
- yeni fee, slippage, margin veya reserve formülü icadı,
- public API, UI, persistence veya marker tasarımı,
- futures, short, hedge, leverage veya liquidation modeli,
- performans/kârlılık iddiası,
- belirli bir özel projenin mevcut koduna erişim iddiası.

---

## 2. Anonim baseline

### 2.1 Fixed-limit historical policy

- Order immutable bir kimliğe sahiptir.
- Placement barı fill için uygun değildir.
- Yalnız placement sonrasındaki canonical closed barlar değerlendirilir.
- BUY için low < limit, SELL için high > limit strict penetration fill candidate üretir.
- low = limit veya high = limit yalnız equality observation’dır; fill commit etmez.
- Fill fiyatı declared limit fiyatıdır; advantageous open price improvement yapılmaz.
- Bir barda en fazla bir fixed slice commit edilir.
- filled + leaves = original exact korunur.
- Dataset sonuna kadar kalan miktar varsa sentetik cancel, expiry, forced exit veya forced fill üretilmez.
- Intrabar sıra ekonomik sonucu belirleyemiyorsa yeni fill commit edilmez ve sonuç belirsiz kalır.

### 2.2 DCA core state-machine

- INTENT order oluşturur; tek başına pozisyon veya ekonomik fill üretmez.
- FILL ekonomik pozisyon, maliyet, realized sonuç ve fee etkisini uygular.
- ORDER_FINAL order coverage/state gözlemini kapatır; eksik veya çelişkili coverage complete sayılmaz.
- BASE tamamlandığında veya domain kuralı izin verdiğinde anchor oluşabilir.
- SAFETY kararları anchor, ladder, coverage ve önceki order state’ine bağlıdır.
- Pending/unresolved order varken yeni risk açılması engellenmelidir.
- Partial safety coverage sessizce tamamlanmış sayılamaz.
- Late veya duplicate fill ekonomik durumu yanlış biçimde ikinci kez commit etmemelidir.

Bu baseline’ın herhangi bir maddesini özel bir local implementation gerçeği olarak sunmayın. Genel model ile local implementation kanıtı arasındaki sınırı açıkça koruyun.

---

## 3. Ana araştırma soruları

### A. İddianın teknik doğruluğu

1. Generic single-limit OHLCV policy’sinin DCA state-machine’e doğrudan bağlanması neden risklidir?
2. Observation, synthetic fill candidate ve authoritative economic fill ayrımı neden gerekli olabilir?
3. Bir policy’nin teknik olarak DCA’ya bağlanabilir olması production binding için yeterli midir?
4. Kanıtlanmadan production binding uygulanmamalıdır sonucu güvenlik ve finansal doğruluk açısından makul müdür?
5. İddianın hangi kısımları kesin, hangileri koşullu veya implementation-dependent’tır?

### B. BASE-only neden ilk aday olabilir?

1. BASE entry’nin SAFETY ve EXIT’e göre hangi bağımlılıkları daha azdır?
2. BASE-only binding neden ilk vertical slice için daha denetlenebilirdir?
3. BASE partial fill, BASE complete fill ve BASE no-fill durumları nasıl ayrılmalıdır?
4. BASE order tamamlanmadan SAFETY planı veya yeni risk açılması güvenli midir?
5. BASE-only adayın zorunlu olarak kanıtlaması gereken upstream/downstream state’ler nelerdir?

### C. Event ve lifecycle bağlama

Aşağıdaki akış için güvenli bir contract önerin:

~~~text
strategy intent
→ order active
→ historical OHLC observation
→ synthetic fill candidate
→ reducer validation
→ authoritative FILL
→ order state update
→ BASE anchor / coverage update
→ next DCA decision
~~~

Şunları açıkça ayırın:

- order creation,
- order active/eligible state,
- market observation,
- candidate generation,
- economic fill commit,
- partial fill,
- terminal finalization,
- open position state,
- open order state.

External kaynaklar yalnızca genel lifecycle modelini desteklemelidir. Belirli bir local reducer’ın alan adlarını veya branch davranışını kanıtlanmış gibi göstermeyin.

### D. Reserve ve risk commitment

1. Pending BASE order bir risk/reserve commitment yaratmalı mıdır?
2. Reserve intent anında mı, order active olduğunda mı, candidate oluştuğunda mı, yalnız FILL’de mi ele alınabilir?
3. Partial fill sonrasında reserve ve leaves nasıl ilişkilendirilebilir?
4. Equality observation reserve tüketmeli midir?
5. Ambiguous bar veya OPEN_AT_END sonrasında reserve state nasıl ele alınmalıdır?
6. Yeni reserve formülü uydurmadan mevcut domain modelinin kanıtlanması neden zorunludur?
7. Exchange hold dokümanları local simulator reserve semantiğini doğrudan kanıtlar mı?

Tek bir evrensel reserve formülü uydurmayın. Kararın mevcut ürün/domain sözleşmesine bağlı olduğunu gerektiğinde açıkça belirtin.

### E. Anchor, coverage ve ekonomik posting

1. BASE anchor hangi event’in sonucu olmalıdır?
2. Partial BASE fill anchor oluşturmalı mıdır?
3. Anchor’ı adapter’ın hesaplaması neden iki source of truth riski doğurur?
4. Anchor ile average/cost basis hangi koşullarda aynı kabul edilebilir?
5. Coverage tamamlanması quantity’nin tamamen dolmasıyla aynı şey midir?
6. ORDER_FINAL ile open position ve open order durumları nasıl ayrılmalıdır?
7. Adapter’ın yalnız candidate üretip core reducer’ın position, anchor, coverage ve fee state’inin tek sahibi olması neden tercih edilebilir?

### F. Placement, look-ahead ve OHLC ambiguity

1. Placement barının aynı bar OHLC’siyle değerlendirilmesi hangi look-ahead riskini doğurur?
2. ACTIVE_NEXT_BAR gibi conservative bir timing sözleşmesi ne zaman gerekir?
3. Equality touch ile strict penetration arasında tarihsel simülasyon açısından fark nedir?
4. OHLC verisi tek başına intrabar event sırasını kanıtlar mı?
5. Aynı barda BASE fill, SAFETY trigger ve EXIT trigger birlikte görülürse neden deterministic favorable ordering seçilmemelidir?
6. Ambiguity durumunda yeni fill’i durdurmak ve prefix’i korumak hangi riski azaltır?
7. EOF’de pending order için sentetik cancel, expiry, exit veya fill üretmek neden ayrı bir model kararıdır?

### G. Duplicate, late fill ve idempotency

1. Deterministic historical replay’de aynı candidate veya FILL neden tekrar gelebilir?
2. Duplicate FILL’in position, fee, reserve ve anchor üzerinde zararı nedir?
3. Order identity, bar identity ve slice sequence gibi alanların dedupe rolü nedir?
4. Order final olduktan sonra gelen late fill nasıl fail-closed veya explicit unresolved state’e çevrilebilir?
5. Dış protokol execution identifier’ları local idempotency sözleşmesini doğrudan belirler mi?

### H. SAFETY ve EXIT neden ertelenebilir?

SAFETY için ayrı kanıt gerektiren bağımlılıkları açıklayın:

- anchor timing,
- safety ladder index,
- previous safety coverage,
- pending BASE/SAFETY blocker,
- partial safety,
- safety stop,
- aynı-bar safety/TP sırası,
- reserve increment.

EXIT için ayrı kanıt gerektiren bağımlılıkları açıklayın:

- open-position predicate,
- exit quantity,
- partial realized accounting,
- cost/average behavior,
- pending exit blocker,
- exit/safety concurrency,
- EOF’de pending exit ile residual position ayrımı,
- opposite-side duplicate/late fill.

Bu roller için tek bir ortak limit fill kuralının yeterli olduğunu varsaymayın.

---

## 4. Kaynak ve kanıt kuralları

Mümkün olduğunca birincil ve resmi kaynaklar kullanın:

- FIX Trading Community veya resmi FIX field/order-state belgeleri,
- borsaların resmi order lifecycle, limit order ve account hold belgeleri,
- resmi candle/OHLC veri tanımları,
- resmi backtest broker-emulator ve historical fill belgeleri,
- Python Decimal/Fraction resmi dokümantasyonu,
- JSON/RFC veya ilgili serialization standartları,
- akademik veya standartlaştırılmış kaynaklar.

Her kaynak için kurum/yazar, başlık, doğrudan URL veya kalıcı tanımlayıcı, yayın/erişim tarihi, desteklediği kesin iddia ve local implementation’a taşınamayacak sonucu verin.

Search snippet’ini kanıt saymayın. Exchange davranışını local simulator davranışıyla eşitlemeyin. Kaynaksız industry standard ifadesi kullanmayın. Reserve, anchor veya fee formülü icat etmeyin. Synthetic historical fill’i gerçek exchange fill’i olarak adlandırmayın.

---

## 5. İstenen karar matrisi

Aşağıdaki her iddia için CONFIRMED, CONDITIONAL, UNSUPPORTED veya LOCAL-CODE-REQUIRED sınıfı kullanın:

| İddia | Sınıf | Kaynak/kanıt | Local code’da ayrıca ne kanıtlanmalı? | Production etkisi |
|---|---|---|---|---|
| Generic fixed-limit policy DCA state-machine’e doğrudan bağlanmamalı |  |  |  |  |
| BASE-only ilk aday olarak daha küçük kapsamlıdır |  |  |  |  |
| Observation ve economic fill ayrılmalıdır |  |  |  |  |
| Pending BASE reserve lifecycle’ı binding blocker’ıdır |  |  |  |  |
| BASE anchor adapter’da değil core’da sahiplenilmelidir |  |  |  |  |
| Placement barı fill için eligible olmamalıdır |  |  |  |  |
| Equality touch tek başına strict synthetic fill üretmemelidir |  |  |  |  |
| Ambiguous same-bar ordering’de yeni ekonomik commit yapılmamalıdır |  |  |  |  |
| EOF pending order sentetik olarak kapatılmamalıdır |  |  |  |  |
| Duplicate/late fill idempotency kanıtı gerekir |  |  |  |  |
| SAFETY ve EXIT BASE ile aynı ilk fazda açılmamalıdır |  |  |  |  |

---

## 6. Minimum local evidence gate

Dış araştırma local kodu doğrulayamaz. Buna rağmen production binding için gereken minimum local kanıt paketini tanımlayın.

### Gate A — Reducer claim inventory

Her madde için claim, kaynak dosya/test türü, input fixture, beklenen state transition, counterexample testi ve ekonomik riski yazın.

En az şu maddeler bulunmalıdır:

1. INTENT order active yapar.
2. INTENT tek başına position/fill üretmez.
3. Yalnız FILL economic position/accounting’i değiştirir.
4. Partial fill exact leaves üretir.
5. Duplicate FILL ikinci kez ekonomik posting yapmaz.
6. Late FILL güvenli biçimde işaretlenir veya reddedilir.
7. BASE anchor timing’i açıktır.
8. Coverage complete tanımı açıktır.
9. Pending/unresolved order yeni riski sınırlar.
10. Fee/slippage tek authoritative pipeline’a aittir.
11. ORDER_FINAL open order ile open position’ı karıştırmaz.

### Gate B — Historical timing proof

Strategy intent’in hangi bar anında üretildiği, placement barının eligible olup olmadığı, sonraki barın ne zaman değerlendirildiği ve ambiguity’de hangi event’in durduğu test veya açık contract ile gösterilmelidir.

### Gate C — BASE-only integration

~~~text
intent
→ active order
→ placement identity
→ next-bar observation
→ equality/no-touch/strict candidate
→ reducer guard
→ partial/full FILL
→ final coverage
→ anchor/position state
→ next decision
~~~

SAFETY ve EXIT bu test paketinde unreachable veya explicit deferred olmalıdır.

### Gate D — Exact accounting

Original, filled, leaves, fill price, fee, position quantity, position cost, anchor, reserve/commitment ve final/open status bağımsız bir referans tablo veya rational/Decimal oracle ile kontrol edilmelidir.

---

## 7. Test matrisi

Her test için expected result ve nedenini verin:

1. Placement barında strict penetration var; fill oluşmuyor.
2. Sonraki barda equality touch var; observation var, fill yok.
3. Sonraki barda strict penetration var; exact declared limit candidate oluşuyor.
4. BASE partial fill; leaves korunuyor.
5. BASE final coverage olmadan SAFETY intent reddediliyor veya engelleniyor.
6. BASE final coverage sonrası anchor yalnız core authority ile oluşuyor.
7. Pending BASE varken ikinci BASE veya SAFETY intent engelleniyor.
8. Duplicate candidate/FILL aynı ekonomik posting’i iki kez oluşturmuyor.
9. Late fill açıkça UNKNOWN/blocker durumuna gidiyor.
10. Ambiguous same-bar event’te yeni fill commit edilmiyor.
11. EOF’de pending order sentetik olarak kapanmıyor.
12. Aynı input tekrarı aynı state/result üretiyor.
13. Legacy non-limit model yeni binding’den etkilenmiyor.
14. Exact Decimal/reference oracle sonucuyle state sonucu eşleşiyor.

Production kodu yazmayın. Her testin hangi local contract açığını kapattığını belirtin.

---

## 8. Beklenen nihai çıktı

Raporun sonunda şu bölümler bulunmalıdır:

1. Executive summary
2. İddianın cümle cümle doğrulaması
3. External evidence ile local-code evidence ayrımı
4. BASE-only adayının bağımlılık haritası
5. Reserve/anchor/coverage blocker analizi
6. Placement/look-ahead/ambiguity/EOF analizi
7. Duplicate/late-fill/idempotency analizi
8. SAFETY ve EXIT’in neden ayrı tutulduğu
9. Minimum local evidence gate
10. RED→GREEN test matrisi
11. Production’a geçiş acceptance checklist’i
12. Karar: ACCEPT / SIMPLIFY / DEFER / REJECT
13. Kaynak listesi ve her kaynağın sınırı

Nihai karar için şu seçenekleri kullanın:

- DEFER: Local reducer/reserve/anchor/binding kanıtı olmadan production’a geçilmemeli.
- SIMPLIFY: Yalnız açıkça tanımlı, ekonomik posting yapmayan observation/candidate katmanı araştırma prototipi olarak tutulabilir.
- ACCEPT: Ancak external kaynaklar ve verilen kabul testleri production binding için yeterli kanıt sağlıyorsa; local-code testlerinin yine de zorunlu olduğunu ayrıca yazın.

Araştırma raporu local repository’yi görmediği için local implementation hakkında kesin mevcut veya yok iddiası kurmamalıdır. Kanıtlanamayan her madde LOCAL-CODE-REQUIRED veya KANIT YOK olarak bırakılmalıdır.

---

## 9. Araştırmacının kesin çalışma yöntemi

Bu promptu alan araştırmacı aşağıdaki sırayı zorunlu olarak izlemelidir:

1. Önce iddiayı parçalara ayırın.
2. Her parçayı external evidence, local-code evidence veya henüz kanıtlanmamış olarak sınıflandırın.
3. Dış kaynakların yalnızca genel prensibi desteklediğini, özel local implementation’ı kanıtlamadığını belirtin.
4. Local implementation bilinmiyorsa tahmin yürütmeyin.
5. Eksik local kanıt varsa aşağıdaki code-request protocol’e göre dar ve anonim bir kod isteği hazırlayın.
6. Kod gelmeden production implementation, API exposure, persistence migration veya UI kararı vermeyin.
7. Kod geldiğinde yalnız istenen sembol ve test parçalarını inceleyin; tüm repository’yi istemeyin.
8. Her iddia için önce başarısız olabilecek bir RED testi, sonra beklenen GREEN davranışı ve ayrıca bağımsız ikinci kontrol tanımlayın.
9. Bir testin yalnızca aynı production helper’ını tekrar çağırarak kendisini doğrulamasına izin vermeyin.
10. Son kararı yalnız kabul gate’lerinin tek tek durumuna göre verin.

Araştırmacı “muhtemelen”, “genellikle”, “industry standard olarak” veya “mevcut kodda vardır/yoktur” ifadelerini kanıtsız kesin sonuç olarak kullanmamalıdır.

---

## 10. Zorunlu code-request protocol

Local reducer, reserve, anchor veya binding davranışı dışarıdan kesin olarak doğrulanamaz. Bu durumda araştırmacı doğrudan geniş repository istemek yerine aşağıdaki dar kod talebini vermelidir.

### 10.1 Kod isteme koşulu

Şu maddelerden biri local-code evidence olmadan kapanamıyorsa kod isteyin:

- order state ve unsettled/pending tanımı,
- INTENT’in order oluşturma davranışı,
- FILL’in tek ekonomik posting noktası olması,
- partial fill ve leaves güncellemesi,
- duplicate/late fill davranışı,
- ORDER_FINAL coverage semantiği,
- BASE anchor oluşturma event’i,
- safety coverage/index ve blocker davranışı,
- reserve veya risk commitment lifecycle’ı,
- historical strategy decision timing’i,
- fixed-limit observation’ın reducer’a nasıl çevrileceği,
- config/model version veya immutable identity,
- mevcut testlerin gerçek acceptance davranışını kanıtlayıp kanıtlamadığı.

### 10.2 İstenecek kod parçaları

İstek yalnız aşağıdaki anonim ve sınırlı parçaları kapsamalıdır:

1. State, Position, Order ve ilgili immutable value type tanımları.
2. INTENT, FILL, ORDER_FINAL, UNKNOWN ve MARK event’lerini uygulayan reducer fonksiyonu.
3. Pending/unsettled order, blocker, reserve veya risk gate hesaplayan fonksiyonlar.
4. BASE anchor ve safety ladder kararını üreten fonksiyonlar.
5. Tarihsel OHLC bar lifecycle’ında strategy decision ve fill candidate üreten fonksiyonlar.
6. Fixed-limit policy’nin observation/result dataclass’ları ve trigger fonksiyonu.
7. Fee/slippage/quantity/tick exact dönüşümünün tek sahibi olan yardımcı fonksiyonlar.
8. Duplicate, late fill ve persistence dedup davranışını gösteren ilgili testler.
9. Historical fixed-limit veya DCA simulation davranışını gösteren mevcut test fixture’ları.
10. Config hash/model version üretiminde kullanılan canonicalization kodu; secret veya gerçek path içermeyen bölüm.

### 10.3 Kod isteme biçimi

Araştırmacı kod isterse kullanıcıya aşağıdaki biçimde tek ve açık bir istek vermelidir:

~~~text
Lütfen yalnız aşağıdaki anonim kod parçalarını gönderin:

1. [rol] State/Order/Position tanımları:
   - sınıf/fonksiyon adlarını koruyun,
   - dosya yolu, proje adı, kullanıcı adı ve gerçek sembol değerlerini maskeleyin.

2. [rol] Event reducer:
   - INTENT, FILL, ORDER_FINAL, UNKNOWN ve MARK branch’leri,
   - reserve/blocker/anchor güncellemeleri,
   - dış servis, credential ve gerçek URL satırlarını çıkarın.

3. [rol] Historical decision adapter:
   - bar index/time,
   - placement/eligible bar kararı,
   - observation’dan candidate’a geçiş,
   - reducer’a gönderilen event payload’ı.

4. [rol] İlgili testler:
   - test adı,
   - fixture,
   - beklenen state/result,
   - duplicate/late/ambiguity/EOF vakaları.

Whole repository, secret, .env, credential, database dump, private URL veya kişisel path göndermeyin.
Kod parçaları eksikse hangi tek parçanın neden gerekli olduğunu belirtin.
~~~

Araştırmacı aynı istekte tüm repository, tüm test klasörü, veritabanı, credential, gerçek kullanıcı adı veya özel path istememelidir.

### 10.4 Kod geldikten sonra yapılacak kontrol

Kod geldikten sonra araştırmacı:

- ilgili fonksiyonun gerçekten çağıran zincire bağlı olduğunu,
- testin production helper’ı ile kendisini doğrulamadığını,
- event sırasının fixture’da açık olduğunu,
- reserve/anchor’ın tek source of truth olduğunu,
- candidate ile economic FILL’in ayrıldığını,
- legacy path’in yeni binding’den etkilenmediğini

ayrı ayrı göstermelidir.

Kod yalnız bir tasarım örneği ise LOCAL-CODE-EVIDENCE olarak değil, PROPOSED DESIGN olarak etiketlenmelidir.

---

## 11. Binding için kesin veri akışı sözleşmesi

Araştırmacı aşağıdaki veri akışının her adımında owner ve kanıtı belirtmelidir:

~~~text
1. Strategy decision
   Owner: DCA strategy/core decision layer
   Output: role, order identity, quantity, declared limit, placement identity

2. Order activation
   Owner: order state/reducer
   Output: active order, eligible-from boundary, pending blocker

3. Market observation
   Owner: historical fixed-limit policy
   Output: NONE, EQUALITY_TOUCH veya STRICT_PENETRATION

4. Synthetic fill candidate
   Owner: historical application adapter
   Output: order identity, bar identity, candidate quantity, declared limit price

5. Economic commit
   Owner: core reducer only
   Output: position, cost, fee, realized, leaves, reserve and blockers

6. Order finalization
   Owner: core order lifecycle
   Output: FILLED, CANCELED, OPEN_AT_END veya explicit unresolved state

7. Next decision
   Owner: DCA core
   Output: BASE/SAFETY/EXIT veya no new risk
~~~

Her satır için şu beş alanı doldurun:

| Adım | Girdi | Mutasyon yetkisi | Çıkış | Kanıt |
|---|---|---|---|---|
| Strategy decision |  |  |  |  |
| Order activation |  |  |  |  |
| Market observation |  |  |  |  |
| Synthetic candidate |  |  |  |  |
| Economic commit |  |  |  |  |
| Order finalization |  |  |  |  |
| Next decision |  |  |  |  |

Bir adapter position, anchor, reserve, realized veya fee hesaplıyorsa bunu doğrudan risk bulgusu olarak işaretleyin. Bunun güvenli olduğu ancak mevcut domain sözleşmesi ve testlerle kanıtlanırsa kabul edilebilir.

---

## 12. BASE-only acceptance için zorunlu senaryo tablosu

Araştırmacı yalnız genel tavsiye vermemeli; aşağıdaki senaryolar için beklenen ön/post state’i ve reddedilmesi gereken davranışı yazmalıdır:

| Senaryo | Beklenen ekonomik sonuç | Beklenen order sonucu | Yeni risk |
|---|---|---|---|
| Placement barında strict penetration | Ekonomik fill yok | Order active/pending | Look-ahead yok |
| Sonraki barda no-touch | Ekonomik fill yok | Leaves değişmez | Yeni risk yok |
| Sonraki barda equality touch | Ekonomik fill yok | Observation yalnız | Fill authority yok |
| Sonraki barda strict penetration | Candidate sonra reducer FILL | Filled veya partial | Core guard zorunlu |
| BASE partial fill | Position yalnız filled kadar açılır | Exact leaves korunur | Anchor timing açık olmalı |
| BASE partial + no final coverage | Position partial olabilir | Coverage incomplete | SAFETY otomatik açılamaz |
| BASE full fill + valid final | Position full açılır | Coverage complete | Anchor core tarafından güncellenir |
| Pending BASE + new SAFETY | Yeni ekonomik risk açılmaz | Intent reddedilir veya bloklanır | Double reservation yok |
| Duplicate FILL | İkinci ekonomik posting yok | Idempotent/rejected | Fee/qty iki kez yazılmaz |
| Late FILL | Açıkça unresolved/UNKNOWN | Coverage geçersizleşir | Sessiz complete yok |
| Ambiguous same-bar | Yeni fill yok | Prefix/state korunur | Favorable ordering yok |
| EOF pending BASE | Forced fill/cancel yok | OPEN_AT_END veya explicit unresolved | Sahte kapanış yok |

Tabloda “beklenen” sonucu external kaynakla local implementation sonucu olarak karıştırmayın. Local sonuç için kod ve test kanıtı ayrıca gösterilmelidir.

---

## 13. Karar için kesin durdurma kuralları

Aşağıdaki durumlardan biri varsa nihai karar otomatik olarak DEFER olmalıdır:

1. Reserve owner veya lifecycle’ı bilinmiyorsa.
2. BASE anchor’ın hangi event’te oluştuğu bilinmiyorsa.
3. Pending order varken yeni risk blocker’ı test edilmemişse.
4. Duplicate veya late FILL davranışı test edilmemişse.
5. Candidate’ın core reducer’a girmeden ekonomik state’i değiştirebildiği görülüyorsa.
6. Placement/eligible bar sınırı açık değilse.
7. Same-bar ambiguity’de hangi event’in durduğu bilinmiyorsa.
8. EOF’de sentetik event üretimi açıkça yasaklanmamışsa.
9. Exact quantity/price/fee conservation bağımsız oracle ile kontrol edilmemişse.
10. Legacy modelin değişmediği regresyonla gösterilmemişse.
11. BASE, SAFETY ve EXIT aynı ilk binding içinde ayrıştırılmadan açılıyorsa.
12. Public API veya UI, local binding kanıtı tamamlanmadan değiştirilecekse.

Bu kuralların hiçbiri “kod güzel görünüyor” veya “dış borsa böyle yapıyor” gerekçesiyle geçilemez.

---

## 14. Araştırmacının vermesi gereken nihai dosya yapısı

Raporu aşağıdaki başlık sırasıyla verin:

1. Karar özeti
2. Doğrulanan, koşullu ve kanıtsız iddialar
3. İddianın her cümlesi için kanıt tablosu
4. External evidence sınırları
5. Local-code evidence eksikleri
6. Gerekliyse anonim code request
7. BASE-only lifecycle ve veri akışı
8. Reserve lifecycle analizi
9. Anchor/coverage/position/order ayrımı
10. Placement/look-ahead/ambiguity/EOF analizi
11. Duplicate/late-fill/idempotency analizi
12. SAFETY ve EXIT erteleme gerekçesi
13. RED→GREEN test matrisi
14. Bağımsız oracle/property test matrisi
15. Public API/UI/persistence’e geçiş koşulları
16. Red-line ihlalleri
17. Nihai karar
18. Kaynak listesi ve kaynak sınırları

Her ana bölümün sonunda şu dört satırı ekleyin:

~~~text
Durum: CONFIRMED / CONDITIONAL / UNSUPPORTED / LOCAL-CODE-REQUIRED
Kanıt: [kaynak veya istenen local-code parçası]
Production etkisi: [uygula / yalnız test et / ertele / reddet]
Eksik kapanış koşulu: [tek ve ölçülebilir koşul]
~~~

---

## 15. Anonimlik ve güvenlik son kontrolü

Rapor veya code request içinde aşağıdakiler bulunmamalıdır:

- proje adı,
- gerçek repository URL’si,
- bilgisayar kullanıcı adı,
- Windows/Linux dosya yolu,
- API key, token, secret veya credential,
- veritabanı dosyası veya ham kullanıcı verisi,
- gerçek hesap kimliği,
- özel sunucu adresi,
- özel dataset path’i,
- dış sisteme giriş bilgisi.

Gerekirse şu anonim terimleri kullanın:

| Gerçek kavram | Anonim terim |
|---|---|
| Ürün/proje | local historical simulator |
| Çekirdek | pure economic reducer |
| Dosya | reducer module / historical adapter module |
| Dataset | verified canonical OHLCV input |
| Borsa | external venue |
| Kullanıcı | operator |
| Profil | explicit simulation profile |
| Kayıt | immutable local run record |

Araştırmacı bu prompttan gerçek bir exchange execution, gerçek kârlılık veya production-ready DCA sistemi sonucu çıkaramaz. Nihai amacı yalnızca güvenli binding için gereken kanıt sınırını belirlemektir.
