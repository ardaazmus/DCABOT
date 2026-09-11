# P1 Master Research v2
## Kritik bot davranışları, matematik modelleri, kod sözleşmeleri ve gerçek kanıt teslimi

## 0. Görevin özeti

Bu bir genel fikir veya özet istemi değildir. P1 kapsamındaki kritik davranışlar ve matematik modeller için gerçek, kaynaklı ve uygulanabilir bir araştırma paketi hazırla.

Bu araştırma:

- soruları yalnız tekrar etmeyecek,
- önceki AI yanıtlarını kaynak kabul etmeyecek,
- kaynaklı cevap verecek,
- cevaplanmayan soruları açıkça `NOT_VERIFIED` veya `BLOCKED` işaretleyecek,
- local code görülmeden local implementation hakkında kesin hüküm vermeyecek,
- her kritik iddiayı test edilebilir bir kabul koşuluna dönüştürecek,
- faz sırasını bozmadan implementation-ready sınırları çıkaracaktır.

Ana hedef, uygulama sırasında her küçük belirsizlikte araştırmayı baştan başlatmamak; fakat ekonomik sonucu veya state authority’yi değiştiren hiçbir konuyu da cevapsız bırakmamaktır.

Bu doküman araştırmacıya hangi soruların cevaplanacağını söyler. Araştırmacının görevi bu soruların cevaplarını dış kaynaklarla gerçekten bulmak, karşılaştırmak ve kanıtlamaktır.

## 1. Önceki raporlar ve AI yanıtları hakkında kesin kural

Önceki AI cevapları, önceki derin araştırma raporları, varsayımsal özetler ve bu promptun kendisi kanıt değildir.

Önceki raporları yalnız:

- araştırma konusu keşfi,
- arama terimi üretimi,
- olası kaynak listesi,
- kontrol edilmesi gereken iddia listesi

olarak kullanabilirsin.

Bir önceki raporda “bu konu araştırıldı”, “bu davranış standarttır” veya “production’a hazırdır” deniyorsa, bunu yeniden birincil kaynaklarla kontrol etmeden doğru kabul etme.

Teslimde ayrıca şu tabloyu doldur:

| Önceki iddia | Yeni birincil kaynakla kontrol edildi mi? | Sonuç | Kanıt |
|---|---:|---|---|
|  |  | CONFIRMED / REVISED / REJECTED / NOT_VERIFIED |  |

## 2. Kimlik, anonimlik ve güvenlik sınırı

Araştırma gerektiğinde proje bağlamının ve teknik isimlerin paylaşılmasına izin veriyorum; bu, araştırma kalitesini artırıyorsa kullanılabilir. Ancak aşağıdakiler hiçbir koşulda istenmeyecek veya teslim dosyasına konmayacaktır:

- API key, secret, token, password, credential,
- private URL, account ID, wallet address veya kullanıcı verisi,
- `.env` içeriği,
- canlı hesap bilgisi,
- veritabanı sırları,
- işletim sistemi kullanıcı adı ve ev dizini,
- gereksiz tam repository arşivi.

Gerçek proje adı veya gerçek dosya adı yalnız gerçekten gerekli ise kullanılabilir. Gereksiz kimlik bilgileri anonimleştirilebilir.

Local code gerekiyorsa tüm repository isteme. Yalnız belirli sembol, branch veya test gövdesini iste. Her kod talebinde neden gerektiğini ve hangi soruyu kapatacağını belirt.

## 3. Araştırmacının çalışma zorunluluğu

Her ana bölüm için gerçek araştırma yap:

1. Birincil kaynakları bul.
2. Kaynağın güncelliğini ve kapsamını kontrol et.
3. Kaynakta gerçekten yazan davranışı çıkar.
4. Farklı kaynakları karşılaştır.
5. Çelişki varsa çözüm veya açık belirsizlik kaydı oluştur.
6. Offline historical simulator için uygulanabilirliği ayrıca değerlendir.
7. Matematiksel değişkenleri ve birimleri tanımla.
8. State/event geçişlerini çıkar.
9. Negative/fail-closed davranışını tanımla.
10. Bağımsız test oracle’ı öner.
11. Implementation kararı ver.

Şu davranışlar araştırma tamamlandı sayılmayacaktır:

- yalnız kaynak URL’si listelemek,
- yalnız rakip ürün açıklaması vermek,
- “genellikle böyledir” demek,
- soruları cevaplamadan tekrar etmek,
- kaynakta olmayan bir formülü tahmin etmek,
- local code görülmeden “mevcut sistemde var/yok” demek,
- test expected state’i vermemek,
- önceki raporu yeniden özetlemek.

## 4. Her kritik iddia için zorunlu kanıt formatı

Her iddia için ayrı kayıt oluştur:

```text
CLAIM_ID:
PHASE:
TOPIC:
CLAIM:
CLAIM_TYPE: DOMAIN | MATHEMATICAL | CODE_BEHAVIOR | DATA | API | PERSISTENCE | UI | SECURITY
STATUS: VERIFIED | CONDITIONAL | UNSUPPORTED | NOT_VERIFIED | LOCAL_CODE_REQUIRED | BLOCKED
PRIMARY_SOURCE_URLS:
SOURCE_TITLE_AND_SECTION:
SOURCE_VERSION_OR_LAST_UPDATED:
ACCESS_DATE:
EVIDENCE_SUMMARY:
SOURCE_SCOPE_LIMIT:
CONFLICT_STATUS: NONE | RESOLVED | UNRESOLVED
PRECEDENCE_REASON:
LOCAL_APPLICABILITY:
IMPLEMENTATION_DECISION: ACCEPT | SIMPLIFY | DEFER | REJECT
EXPECTED_TEST:
NEGATIVE_EXPECTATION:
REQUIRED_LOCAL_CODE_OR_FIXTURE:
```

`STATUS=VERIFIED` yalnız doğrudan kaynak veya bağımsız hesapla desteklenen iddialarda kullanılabilir.

`STATUS=CONDITIONAL` ise koşulları eksiksiz yazılmalıdır.

`STATUS=LOCAL_CODE_REQUIRED` veya `BLOCKED` olan bir iddia implementation-ready kabul edilemez.

## 5. Kaynak standardı

Kaynak önceliği:

1. Resmi exchange/API dokümanları.
2. FIX, ISO, IEEE, Python ve diğer resmi teknik standartlar.
3. Akademik ve hakemli araştırmalar.
4. Resmi backtest/simülasyon dokümantasyonları.
5. Güvenilir teknik dokümantasyon.
6. Rakip ürün sayfaları; yalnız özellik keşfi için.

Her kaynak için zorunlu alanlar:

- URL,
- başlık,
- yayıncı,
- erişim tarihi,
- sayfa/heading/section,
- sürüm veya `last updated` bilgisi,
- hangi iddiaları desteklediği,
- hangi iddiaları desteklemediği.

Kaynak güncel sürüm bilgisini vermiyorsa `VERSION_UNAVAILABLE` yaz. Bu bilgiyi uydurma.

## 6. Kaynak çatışması kuralı

İki kaynak farklı davranış söylüyorsa bunları sessizce birleştirme.

Şu formatı kullan:

```text
CONFLICT_ID:
SOURCE_A:
SOURCE_B:
CONFLICTING_PROPOSITIONS:
PRODUCT_SCOPE:
VERSION_SCOPE:
PRECEDENCE_RULE:
CONFLICT_STATUS: RESOLVED | UNRESOLVED
DECISION:
DO_NOT_IMPLEMENT_IF_UNRESOLVED: YES | NO
```

Öncelik belirlerken şu sırayı değerlendir:

1. Aynı ürün, aynı market, aynı endpoint ve aynı sürüm.
2. Aynı venue için daha yeni resmi sözleşme.
3. Daha dar ve doğrudan kapsamlı kaynak.
4. Genel standardın üzerindeki venue-specific kural.
5. Çözülemiyorsa `UNRESOLVED`.

Çözülemeyen ve ekonomik sonucu etkileyen çatışma implementation’ı durdurmalıdır.

## 7. Global cross-cutting model

Aşağıdaki konular her fazda tekrar farklı anlamda tanımlanmayacak; master seviyede ortak sözleşme olarak araştırılacaktır.

### 7.1 Zaman taxonomy’si

Şu zaman türlerinin farkını ve her event için sahibini araştır:

- `event_time`,
- `receive_time`,
- `processing_time`,
- `bar_open_time`,
- `bar_close_time`,
- `effective_time`,
- `persistence_time`,
- `display_time`.

Her event için hangi zamanın ekonomik karar verdiğini yaz. Wall-clock veya processing delay’in historical economic time ile karıştırılmasını reddet.

### 7.2 Execution identity

Canonical execution identity’nin bileşenlerini araştır:

- venue scope,
- order identity,
- venue execution identity,
- local event identity,
- economic side,
- timestamp veya sequence,
- payload hash.

`execution_identity` alanını kendi içinde tekrar eden hatalı bir formül yazma. Duplicate, conflicting duplicate ve late event ayrı sınıflar olmalıdır.

### 7.3 Atomic economic transition

Şu invariant’ı tüm ilgili fazlarda kontrol et:

```text
Accepted Economic FILL
→ position/cost mutation
→ fee mutation
→ cumulative/leaves mutation
→ reserve/commitment mutation if enabled
→ dedupe identity recording
→ resulting state/version recording
```

Bu değişiklikler ya tek atomic semantic transition olarak commit edilmeli ya da hiçbiri commit edilmemelidir.

### 7.4 Canonical serialization ve hash

Araştır:

- field ordering,
- omitted/default fields,
- null ve absent farkı,
- Decimal/Fraction serialization,
- timezone normalization,
- schema version,
- hash algorithm,
- canonical JSON veya eşdeğer format,
- Unicode/encoding normalization.

Ekonomik olarak aynı olan iki canonical state’in farklı hash üretmemesi; farklı olan iki state’in aynı hash’e zorlanmaması gerekir.

### 7.5 Numeric boundary

Şu sınırları ayrı ayrı tanımla:

```text
input parse
→ exact internal representation
→ economic calculation
→ persistence representation
→ public API representation
→ UI display formatting
```

`economic rounding != API serialization rounding != UI formatting` ayrımını açıkça test et.

### 7.6 Global result taxonomy

En az şu durumların anlamını ortaklaştır:

```text
VALID
INVALID_INPUT
UNSUPPORTED
AMBIGUOUS
INDETERMINATE
CORRUPT
STALE
CONFLICT
UNKNOWN
OPEN_AT_END
LOCAL_CODE_REQUIRED
```

Her durum için:

- ekonomik state değişir mi,
- public summary üretilebilir mi,
- persistence yapılabilir mi,
- yeni risk kararı verilebilir mi,
- UI’da nasıl görünmelidir

cevaplarını ver.

## 8. P1.05/P1.06 — Sonuç ve kalıcı run kapanışları

Araştır ve cevapla:

- realized/unrealized/equity/fees/funding/ROI/drawdown ayrımı,
- `OPEN_AT_END` ekonomik summary sınırı,
- `INDETERMINATE` committed prefix ve final summary ayrımı,
- run capture identity,
- dataset/config/model/kernel hash,
- seed policy,
- immutable persistence,
- save/reopen/reproduce/compare,
- export/audit,
- result hash ve canonical replay.

Her ekonomik metriğin:

- exact formülünü,
- asset/unit’ini,
- hangi eventlerden üretildiğini,
- incomplete durumda neden gizleneceğini veya gösterileceğini

belirt.

## 9. P1.07 — Order, partial fill, reserve ve historical execution

Bu bölüm zorunlu derin araştırma bölümüdür. Her alt soruya kaynaklı cevap ver.

### 9.1 Order lifecycle

- `OPEN`, `PARTIALLY_FILLED`, `FILLED`, `CANCELED`, `UNKNOWN`, `OPEN_AT_END`, `INDETERMINATE`.
- `original_qty`, `cum_qty`, `leaves_qty`, terminal remainder.
- Full quantity fill ile final coverage farkı.
- `ORDER_FINAL` ve anchor owner.
- Pending BASE varken BASE/SAFETY/EXIT kararı.
- Duplicate/conflicting/late event.
- Adapter/core reducer authority.

### 9.2 Reserve/commitment

- Asset/unit nedir?
- Quantity mi, quote amount mı, risk capacity mi?
- Acquisition owner hangi eventtir?
- Reduction owner hangi eventtir?
- Release owner hangi eventtir?
- Candidate reserve mutation yapabilir mi?
- Equality observation reserve’i değiştirir mi?
- Partial fill sonrası commitment nasıl kalır?
- Fee dahil mi?
- Farklı fee asset conversion nasıl yapılır?
- Rounding ve step owner kimdir?
- Explicit cancel/expiry/EOF davranışı nedir?
- Ambiguity’de reserve mutation yapılır mı?
- Crash/retry atomicity nasıl sağlanır?
- `reserve_model=NONE` ile numeric zero nasıl ayrılır?

Initial-margin estimate’i reserve sayma. Bunun aynı kavram olduğunu göstermek için local code ve test zinciri gerekir.

### 9.3 Historical OHLCV limit/stop assumptions

- Placement bar eligible mi?
- Equality touch ne ifade eder?
- Strict penetration ne ifade eder?
- Gap/open fill price nedir?
- Fixed slice ve exact remainder nasıl hesaplanır?
- Aynı bar path ambiguity nasıl sınıflandırılır?
- Committed prefix nerede kesilir?
- EOF forced fill/cancel/expiry midir?
- Stop ve limit authority ayrımı nedir?

### 9.4 P1.07 zorunlu test matrisi

Her testte fixture, event sırası, expected state, negative assertion ve bağımsız kontrol bulunmalıdır:

1. Pending BASE no-fill.
2. Equality observation.
3. Strict candidate.
4. Rejected candidate.
5. Accepted partial fill.
6. Full fill without final coverage.
7. Full fill with valid final coverage.
8. Partial BASE blocks SAFETY.
9. Explicit cancel.
10. EOF pending order.
11. Ambiguous committed prefix.
12. Known duplicate.
13. Conflicting duplicate.
14. New late fill.
15. Crash/retry.
16. Deterministic replay.
17. Legacy policy isolation.
18. `reserve_model=NONE` versus explicit reserve profile.

### 9.5 P1.07 kararları

Reserve için ayrı ayrı karar ver:

- Current v1 NONE boundary.
- Candidate-time reserve.
- INTENT-time reserve.
- ACTIVE-time reserve.
- FILL-time commitment reduction.
- Explicit cancel release.
- EOF behavior.
- Future explicit reserve profile.

## 10. P1.08 — Multi-deal lifecycle

Araştır:

- deal start/stop/pause/finish/copy,
- cooldown,
- restart,
- active config revision,
- deal isolation,
- failed/aborted/completed/paused statuses,
- lifecycle event dedupe,
- persistence and replay,
- multi-deal acceptance tests.

## 11. P1.09 — Advanced DCA and sizing

Araştır:

- BASE/QUOTE/balance-percent sizing,
- custom ladder,
- safety amount,
- reinvest,
- budget/exposure limit,
- quantity/tick/notional rounding,
- fee/funding effect,
- ladder sum invariant,
- exact numeric model,
- preview ile economic posting ayrımı.

Her formül için variable/unit/sign/precision/rounding/owner/oracle tablosu zorunludur.

## 12. P1.10 — TP, SL, trailing ve breakeven

Araştır:

- trigger versus execution,
- multiple TP quantity conservation,
- stop/limit/market farkı,
- trailing activation/ratchet,
- breakeven,
- fee-aware target,
- gap/ambiguity,
- cancel-replace,
- late fill,
- partial exit sonrası risk gate.

## 13. P1.11 — Shared virtual account

Araştır:

- account ownership,
- pair/bot position ownership,
- shared balance/exposure,
- account reservation,
- concurrency,
- double counting,
- restart/replay,
- multi-writer conflict.

## 14. P1.12 — Spot ve linear futures

Bu bölüm zorunlu derin araştırma bölümüdür. Venue-specific formülleri evrensel formül gibi sunma.

### 14.1 Ürün ve fiyat modeli

- Spot inventory versus futures position.
- Linear long/short.
- Contract size ve settlement asset.
- Mark/index/last/trigger price.
- Funding rate ve funding time.
- Trading/funding/liquidation fee.

### 14.2 Margin modeli

- Wallet balance.
- Margin balance.
- Available balance/margin.
- Position margin.
- Order margin.
- Initial margin.
- Maintenance margin.
- Isolated margin.
- Cross margin.
- Leverage.
- Unrealized PnL effect.
- Margin call.
- Liquidation.
- Partial liquidation.
- Bankruptcy/negative balance behavior.

Her alanın asset/unit ilişkisini ayrı tabloyla ver.

### 14.3 Futures test/oracle matrisi

Bağımsız expected calculation ver:

- long profit/loss,
- short profit/loss,
- positive/negative funding,
- fee deduction,
- isolated exhaustion,
- cross shared loss,
- mark/index divergence,
- maintenance boundary,
- liquidation,
- partial close,
- restart/replay.

Bir venue dokümanı yoksa liquidation veya margin formülünü `ACCEPT` yapma; `DEFER` veya `LOCAL_CODE_REQUIRED` işaretle.

## 15. P1.13 — Grid families

Araştır:

- arithmetic/geometric grid,
- level generation,
- inventory conservation,
- grid profit versus total equity,
- trailing/infinity/reverse grid,
- leveraged grid,
- partial fill,
- level replacement,
- order dedupe.

Her varyantı ayrı model ve ayrı test kapsamı olarak ele al.

## 16. P1.14 — Rebalancing, signal ve templates

Araştır:

- target allocation,
- threshold/time rebalancing,
- event-time,
- signal dedupe/replay protection,
- indicator warmup,
- closed-bar rule,
- template version/hash,
- import/export security,
- template’in emir authority’si olmaması.

## 17. P1.15 — Hedge, cross ve iki bacak

Bu bölüm zorunlu derin araştırma bölümüdür.

### 17.1 Hedge/netting

- Net position versus hedge position.
- Long/short ayrı state mi?
- Same-symbol opposite-side orders.
- Reduce-only/close-position.
- Position owner/deal owner.
- Fee/funding/settlement.

### 17.2 Cross margin

Ayrı bir asset/unit tablosu hazırla:

- wallet balance,
- margin balance,
- available balance,
- position margin,
- order margin,
- maintenance requirement,
- unrealized PnL,
- realized PnL,
- bankruptcy/equity boundary.

### 17.3 Two-leg lifecycle

- One-leg-filled.
- Other-leg-unfilled.
- Leg sequencing.
- Timeout.
- Partial hedge.
- Spread.
- Funding/borrow/transfer.
- One-leg liquidation.
- Atomicity.
- Recovery/replay.

İki bacaklı model için ayrı state-machine, formül seti ve bağımsız oracle ver. Spot/futures varsayımlarını otomatik birleştirme.

## 18. P1.16 — Walk-forward, OOS ve stress

Bu bölüm zorunlu derin araştırma bölümüdür.

### 18.1 Time split/leakage

- Train/validation/test.
- Walk-forward window türleri.
- Purging.
- Embargo.
- Indicator warmup leakage.
- Parameter-selection leakage.
- Dataset adjustment leakage.

### 18.2 OOS freeze rule

Şunu açıkça cevapla:

```text
OOS sonucu görüldükten sonra tuning yapılırsa aynı OOS artık untouched evaluation değildir.
Yeni tuning için yeni untouched holdout gerekir.
```

Bu kuralın kaynaklarını, istisnalarını ve testini ver.

### 18.3 Run comparison ve multiple testing

- Dataset/config/model/kernel identity.
- Seed.
- Deterministic replay.
- Failed/dropped/invalid run.
- Hyperparameter multiple testing.
- Benchmark.
- Selection protocol.

### 18.4 Stress

- Spread.
- Slippage.
- Latency.
- Volume participation.
- Partial fill.
- OHLC ambiguity.
- Missing/gap.
- Best/worst case.
- Stress sonucunun normal backtest gibi sunulmaması.

## 19. P1.17 — Public fiyatla simulated runtime

Araştır:

- read-only feed,
- stale data,
- gap/reconnect,
- clock/event ordering,
- simulated adapter,
- credential isolation,
- venue execution ID ile local identity farkı,
- runtime failure ve recovery.

## 20. P1.18 — Explanation, notifications ve templates

Araştır:

- offline rule-based explanation,
- rejection/risk explanation,
- severity taxonomy,
- optional LLM boundary,
- LLM’nin state değiştirememesi,
- template integrity/version/hash,
- notification replay/dedupe.

## 21. P1.19 — UX, accessibility ve kurulum

Görsel/UI kararlarını finansal authority ile karıştırma. Görsel araştırma gerekiyorsa kaynak ve ekran kanıtı ayrıca ver.

Araştır:

- desktop/mobile responsive,
- 320px,
- keyboard/focus,
- screen reader,
- contrast/grayscale,
- empty/loading/error,
- `INDETERMINATE`, `CORRUPT`, `OPEN_AT_END`,
- dark/light theme,
- offline Windows startup/install,
- API value ile UI formatting ayrımı.

## 22. P1.20 — Final acceptance

Final kabul için mekanik bir gate üret.

Bir faz ancak şu koşullarda `IMPLEMENTATION_READY=YES` olabilir:

```text
- critical claim unresolved değil,
- LOCAL_CODE_REQUIRED blocking claim yok,
- venue-specific formül scope’u belli,
- independent oracle hazır,
- positive ve negative testler tanımlı,
- deterministic replay tanımlı,
- persistence/reopen etkisi belli,
- public authority belli,
- fail-closed davranış belli,
- legacy isolation belli,
- güvenlik sınırı belli.
```

`PRODUCTION_READY` ifadesini yalnız canlı/testnet sınırları da kanıtlanmışsa kullan. Offline P1 için gerekirse `IMPLEMENTATION_READY` ve `PHASE_ACCEPTED` kullan.

## 23. Test ve oracle standardı

Her ana model için şu test sınıflarını düşün:

- example-based,
- boundary,
- negative,
- deterministic replay,
- duplicate/conflict,
- crash/retry,
- metamorphic/property-based,
- serialization/hash,
- persistence/reopen.

Zorunlu metamorphic örnekler:

- Aynı fill’i parçalara bölmek ekonomik toplamı değiştirmemeli.
- Bilinen duplicate ekonomik state’i değiştirmemeli.
- Replay sayısı sonucu değiştirmemeli.
- Export/import sonucu değiştirmemeli.
- Exact remainder quantity conservation’ı korumalı.
- Suffix ambiguity committed prefix’i geri almamalı.
- Venue-specific formula başka venue’ye taşınınca otomatik geçerli sayılmamalı.

Reference oracle production reducer, production helper veya aynı formül utility’sini import edemez.

## 24. Local code request protokolü

Bir cevabı local code olmadan veremiyorsan, cevabı uydurma ve şu formatta dar talep oluştur:

```text
LOCAL_CODE_REQUEST_ID:
PHASE:
UNKNOWN_QUESTION:
WHY_EXTERNAL_SOURCES_CANNOT_ANSWER:
EXACT_SYMBOL_OR_BRANCH_REQUIRED:
MAX_SNIPPET_SIZE:
REDACTION_RULES:
EXPECTED_DECISION_AFTER_CODE:
```

İzin verilen örnek talepler:

- `State`, `Order`, `Position` schema’sı.
- `INTENT`, `FILL`, `ORDER_FINAL`, `UNKNOWN`, `MARK` branch’i.
- Initial-margin estimate çağrı zinciri.
- Pending blocker.
- Historical adapter candidate → core FILL.
- Anchor/SAFETY decision chain.
- Duplicate/late fill persistence testleri.
- Partial/EOF/ambiguity/cancel fixture’ları.
- Public DTO/serializer/legacy testleri.

İstenmeyenler:

- bütün repository,
- bütün `.env`,
- credential veya canlı hesap,
- gereksiz frontend/backend dosyaları,
- private veri.

## 25. Araştırma klasörü teslim standardı

Aşağıdaki klasör yapısını kullan:

```text
P1_KRITIK_ARASTIRMA_V2/
├── 00_README.md
├── 01_MASTER_DECISION_SUMMARY.md
├── 02_CROSS_CUTTING_INVARIANTS.md
├── 03_P1.05_P1.06_CLOSURE.md
├── 04_P1.07_ORDER_RESERVE.md
├── 05_P1.08_DEAL_LIFECYCLE.md
├── 06_P1.09_ADVANCED_DCA_SIZING.md
├── 07_P1.10_TP_SL_TRAILING.md
├── 08_P1.11_SHARED_ACCOUNT.md
├── 09_P1.12_FUTURES_MODEL.md
├── 10_P1.13_GRID_FAMILIES.md
├── 11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md
├── 12_P1.15_HEDGE_CROSS_TWO_LEG.md
├── 13_P1.16_WALK_FORWARD_STRESS.md
├── 14_P1.17_SIMULATED_RUNTIME.md
├── 15_P1.18_EXPLANATION_NOTIFICATIONS.md
├── 16_P1.19_UX_ACCESSIBILITY_INSTALL.md
├── 17_P1.20_FINAL_ACCEPTANCE.md
├── claims/
│   ├── CLAIM_REGISTER.md
│   └── PREVIOUS_CLAIM_RECHECK.md
├── sources/
│   ├── SOURCE_INDEX.md
│   ├── SOURCE_CARDS.md
│   └── SOURCE_CONFLICTS.md
├── evidence/
│   ├── EVIDENCE_MANIFEST.md
│   ├── PRIMARY_SOURCE_EVIDENCE.md
│   └── URL_ARCHIVE_REFERENCES.md
├── formulas/
│   ├── FORMULA_REGISTER.md
│   └── INDEPENDENT_ORACLE_SPEC.md
├── test_matrices/
│   ├── P1.07_TESTS.md
│   ├── P1.12_TESTS.md
│   ├── P1.15_TESTS.md
│   └── P1.16_TESTS.md
├── code_requests/
│   └── LOCAL_CODE_REQUIRED.md
└── MANIFEST.md
```

## 26. Zorunlu dosya içerikleri

### `00_README.md`

- Araştırma tarihi.
- Araştırmacı/model bilgisi.
- Kaynak sayısı.
- Birincil kaynak sayısı.
- Kaynak sürümü bulunamayan kaynak sayısı.
- Local code görülüp görülmediği.
- Gerçek test çalıştırıldı mı?
- Hangi bölümler `IMPLEMENTATION_READY` değil?
- Hangi sorular `BLOCKED`?
- Önceki raporlardan hangileri yeniden doğrulandı?

### `01_MASTER_DECISION_SUMMARY.md`

| Faz | Araştırıldı mı? | Ana karar | Implementation-ready mı? | Kritik açık | Sonraki kanıt |
|---|---:|---|---:|---|---|
| P1.05/P1.06 |  |  |  |  |  |
| P1.07 |  |  |  |  |  |
| P1.08 |  |  |  |  |  |
| P1.09 |  |  |  |  |  |
| P1.10 |  |  |  |  |  |
| P1.11 |  |  |  |  |  |
| P1.12 |  |  |  |  |  |
| P1.13 |  |  |  |  |  |
| P1.14 |  |  |  |  |  |
| P1.15 |  |  |  |  |  |
| P1.16 |  |  |  |  |  |
| P1.17 |  |  |  |  |  |
| P1.18 |  |  |  |  |  |
| P1.19 |  |  |  |  |  |
| P1.20 |  |  |  |  |  |

Her satır için ayrıca:

```text
Şimdi uygulanabilir:
Şimdilik uygulanamaz:
Uygulama sırasında yeniden kanıt gerekebilir:
```

### `CLAIM_REGISTER.md`

Tüm kritik iddiaları `CLAIM_ID` ile listele. Hiçbir kritik iddia ana karar özetinin dışında kalmamalıdır.

### `FORMULA_REGISTER.md`

Her formül için:

- formül,
- değişkenler,
- birimler,
- işaret,
- precision,
- rounding,
- owner,
- input state,
- output state,
- failure state,
- bağımsız oracle,
- venue applicability.

### `INDEPENDENT_ORACLE_SPEC.md`

Production implementation’dan bağımsız, küçük ve tekrarlanabilir oracle fixture’ları tanımla. Oracle’ın production kodunu import etmediğini açıkça göster.

### `MANIFEST.md`

- bütün dosya listesi,
- dosya boyutu,
- araştırma sürümü,
- oluşturulma tarihi,
- kaynak sayısı,
- SHA-256 manifest referansı.

## 27. Kanıt dosyası ve telif sınırı

Tam web sayfalarını veya uzun dokümanları kopyalama. Bunun yerine:

- kısa gerekli kanıt pasajı veya doğru paraphrase,
- URL,
- başlık/heading,
- erişim tarihi,
- sürüm/last updated,
- kaynak kapsam sınırı

sakla.

Kaynak ekran görüntüsü veya arşiv gerekirse yalnız kanıt için gerekli küçük parçayı kullan. Telifli içeriği tam olarak çoğaltma.

## 28. Araştırmanın tamamlandığını söyleme şartı

Araştırma ancak şu koşullarda “tamamlandı” denebilir:

- Her P1 bölümü için dosya veya bölüm mevcut.
- Her kritik sorunun cevabı, `NOT_VERIFIED/BLOCKED` durumu veya gerekçeli `DEFER` kararı var.
- P1.07, P1.12, P1.15 ve P1.16 derin kapsamı eksiksiz işlendi.
- Her kritik formülün birim ve oracle bilgisi var.
- Kaynak sürümü ve çatışmaları kaydedildi.
- Local code gerektiren sorular ayrı listelendi.
- Test expected/negative state’leri var.
- Production implementation kararı ile araştırma bulgusu birbirinden ayrıldı.
- Folder manifest ve checksum teslim edildi.

Bu koşullardan biri eksikse son raporda şu ifadeyi kullan:

```text
RESEARCH_COMPLETE: NO
MISSING_DELIVERABLES:
BLOCKING_REASONS:
```

## 29. Uygulama sırasında yeni kanıt kapısı

Araştırma tesliminden sonra uygulama sırasında yeni bir belirsizlik çıkarsa sessizce varsayım yapma. Şu formatta bildir:

```text
NEW_EVIDENCE_REQUIRED: YES
PHASE:
UNKNOWN_BEHAVIOR:
CURRENT_LOCAL_EVIDENCE:
WHY_IT_CHANGES_IMPLEMENTATION:
MINIMUM_NEW_RESEARCH_QUESTION:
REQUIRED_CODE_SNIPPET_IF_ANY:
SAFE_ANONYMOUS_REQUEST:
DO_NOT_IMPLEMENT_UNTIL:
```

Yeni araştırma yalnız gerçekten şu durumlardan biri varsa istenebilir:

- ekonomik state sonucu değişiyorsa,
- event authority değişiyorsa,
- exact formül veya asset/unit belirsizse,
- persistence/replay bütünlüğü etkileniyorsa,
- venue-specific davranış universal sanılacaksa,
- güvenlik/veri bütünlüğü riski varsa,
- yeni UI/UX kararı kullanıcı yorumunu değiştirecekse.

## 30. Son teslim talimatı

Şimdi bu promptu baştan sona uygula. Önceki araştırma raporunu yeniden özetleme. Her ana bölüm için gerçek kaynaklı araştırma yap. Cevaplanmayan soruları gizleme. Local implementation görülmeden local code hakkında kesin konuşma. Büyük genel kod blokları yazma; gerekli olursa yalnız dar, anonim kod talebi veya küçük bağımsız oracle/pseudocode ver.

Son teslimde hem klasör yapısını hem de `01_MASTER_DECISION_SUMMARY.md` dosyasını sağla. Araştırma ile implementation arasındaki sınırı açık tut.
