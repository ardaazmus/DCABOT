# P1 — Kritik Davranışlar, Matematik Modeller ve Uygulama Çerçevesi
## Anonim, kanıtlı ve fazlara ayrılmış kapsamlı araştırma talebi

## 1. Araştırmanın amacı

Yerel, offline çalışan ve tarihsel piyasa verisiyle DCA simülasyonu yapan bir finansal yazılımın P1 ana fazlarını güvenli biçimde planlamak için kapsamlı bir araştırma paketi hazırla.

Bu çalışma kod yazma talebi değildir. Amaç:

- kritik domain davranışlarını netleştirmek,
- matematiksel modelleri ve birimlerini tanımlamak,
- state-machine ve event authority sınırlarını çıkarmak,
- hangi davranışların production’a alınabileceğini belirlemek,
- hangi iddiaların mutlaka local code/test ile doğrulanması gerektiğini ayırmak,
- uygulama sırasında tekrar tekrar araştırma isteme ihtiyacını azaltacak bir ön çerçeve oluşturmaktır.

Araştırma sonucu doğrudan uygulama talimatı sayılmayacaktır. Her öneri `ACCEPT`, `SIMPLIFY`, `DEFER`, `REJECT` veya `LOCAL-CODE-REQUIRED` kararıyla sınıflandırılmalıdır.

## 2. Anonimlik ve güvenlik sınırı

Gerçek proje adı, kullanıcı adı, yerel disk yolu, repository adı, gerçek hesap, API key, token, credential, veritabanı yolu, özel URL veya kullanıcı verisi isteme.

Tüm örneklerde şu anonim adları kullan:

- `LOCAL_SIMULATOR`
- `BASE_ORDER`
- `SAFETY_ORDER`
- `EXIT_ORDER`
- `QUOTE_ASSET`
- `BASE_ASSET`
- `VENUE_A`
- `DATASET_A`
- `CONFIG_A`

Gerçek borsa, kütüphane veya standart adı yalnız kaynak göstermek için kullanılabilir; yerel projenin kimliğini çıkarmaya çalışma.

Eğer bir iddia local implementation görülmeden çözülemiyorsa cevap uydurma. Bunun yerine `LOCAL-CODE-REQUIRED` bölümü aç ve yalnız gerekli küçük kod/test parçalarını iste.

## 3. Kanıt standardı

Her önemli iddia için aşağıdaki formatı kullan:

```text
CLAIM_ID:
İDDİA:
DURUM: VERIFIED | CONDITIONAL | UNSUPPORTED | LOCAL-CODE-REQUIRED
KAYNAK:
KANIT ÖZETİ:
BU KAYNAK NEYİ KANITLAMAZ:
LOCAL UYGULAMAYA UYGULANABİLİRLİK:
ÖNERİLEN KARAR: ACCEPT | SIMPLIFY | DEFER | REJECT
GEREKLİ TEST:
```

Kaynak önceliği:

1. Resmi exchange/API dokümanları ve resmi ürün sözleşmeleri.
2. FIX, ISO, IEEE, Python ve ilgili teknik standartlar.
3. Akademik makaleler ve hakemli araştırmalar.
4. Backtest/simülasyon kütüphanelerinin resmi dokümantasyonu.
5. Güvenilir teknik kaynaklar.
6. Rakip ürün dokümanları yalnız davranış keşfi için; matematik veya doğruluk kanıtı olarak değil.

Her kaynak için doğrudan URL, başlık, erişim tarihi ve hangi iddiayı desteklediğini yaz. Kaynağın kapsamını aşan genelleme yapma.

## 4. Zorunlu araştırma yöntemi

Her bölümde şu sırayı uygula:

1. Domain kavramlarını tanımla.
2. Kaynaklı davranışları çıkar.
3. Kaynakların çeliştiği noktaları göster.
4. Offline historical simulator için hangi varsayımın seçilebileceğini belirt.
5. State/event geçişlerini tanımla.
6. Exact matematik ve birimleri belirt.
7. Negative case ve fail-closed davranışını yaz.
8. Bağımsız test oracle’ını tanımla.
9. Public API, persistence ve UI’ya etkisini ayır.
10. En küçük uygulanabilir slice için kabul kriteri ver.

Şu ayrımı hiçbir bölümde bozma:

```text
Observation  !=  Candidate  !=  Accepted Economic FILL  !=  ORDER_FINAL  !=  Persisted Result
```

Frontend hesaplaması, grafik koordinatı veya UI göstergesi ekonomik state authority olarak kabul edilmemelidir.

## 5. Her araştırma bölümünün zorunlu teslim formatı

Her faz/konu için ayrı bir Markdown dosyası üret veya klasör içinde ayrı başlık altında şu bölümleri kullan:

1. Kapsam ve kapsam dışı maddeler.
2. Terimler ve tanımlar.
3. Kaynak envanteri.
4. Kanıtlı iddia matrisi.
5. State-machine ve event geçişleri.
6. Matematiksel model ve değişken birimleri.
7. Exact numeric/rounding kuralları.
8. Ambiguity, EOF, gap, duplicate ve late-event davranışı.
9. Public contract etkisi.
10. Persistence/replay etkisi.
11. UI/UX etkisi; ekonomik hesap UI’ya bırakılmamalı.
12. Test matrisi.
13. Bağımsız reference oracle önerisi.
14. ACCEPT/SIMPLIFY/DEFER/REJECT kararı.
15. Implementation-ready kabul kriterleri.
16. Local code/test talebi gerekiyorsa anonim ve dar talep.
17. Açık sorular ve sonraki kanıt kapısı.

Her test için beklenen state’i ve beklenmeyen state’i yaz. Yalnız “test edilmelidir” demek yeterli değildir.

## 6. P1 kapsam haritası

### P1.05/P1.06 kapanış eksikleri

Mevcut tarihsel sonuç, ekonomik özet ve kalıcı run akışının kapsamlı ürün kabulüne yaklaşması için şu konuları incele:

- realized, unrealized, fees, funding, equity, drawdown ve ROI’nin ayrımı,
- `OPEN_AT_END` ve `INDETERMINATE` sonuçlarında ekonomik özet sınırı,
- run capture, immutable persistence, reopen, reproduce ve compare,
- dataset/config/model/kernel hash ilişkisi,
- export ve audit bağlantısı,
- kaydedilmiş sonuç ile yeniden hesaplanan sonucun aynı olup olmadığının oracle’ı.

Kapsamlı finansal metrikleri zorunlu yapma. Her metriğin veri ve model gereksinimini ayrıca belirt.

### P1.07 — Partial fill, order lifecycle ve historical execution

Bu bölüm en derin araştırma bölümlerinden biri olmalıdır.

#### 6.1 Reserve ve commitment lifecycle

Şunları ayrı ayrı cevapla:

- Reserve hangi asset ve unit cinsindedir?
- Reserve monetary amount mı, quantity mi, risk capacity mi?
- Acquisition owner `INTENT`, `ACTIVE`, accepted `FILL` veya başka event mi?
- Reduction owner kimdir?
- Release owner kimdir?
- Candidate reserve mutation yapabilir mi?
- Equality observation reserve’i etkiler mi?
- Partial fill sonrası remaining commitment nasıl hesaplanır?
- Fee reserve’e dahil mi?
- Fee başka asset’teyse conversion nasıl yapılır?
- Rounding/step/tick owner kimdir?
- Explicit cancel, expiry ve EOF reserve’i nasıl etkiler?
- Ambiguous OHLC bar’da reserve mutation yapılabilir mi?
- Duplicate ve late fill reserve’i ikinci kez değiştirebilir mi?
- Crash/retry sırasında position, fee, leaves ve reserve tek atomic transition mı?
- `reserve_model=NONE` durumu numeric `0` ile nasıl ayrıştırılır?

`initial_margin_estimate` ile persistent reserve/commitment state’ini otomatik olarak eşitleme. Aynı kavram olduklarını kanıtlamak için local code/test gereksinimini açıkça yaz.

#### 6.2 Order lifecycle

- `OPEN`, `PARTIALLY_FILLED`, `FILLED`, `CANCELED`, `UNKNOWN`, `OPEN_AT_END`, `INDETERMINATE` ayrımı.
- `original_qty = cumulative_filled + leaves + explicit_terminal_remainder` invariant’ı.
- Full quantity FILL ile final coverage arasındaki fark.
- `ORDER_FINAL` hangi şartlarda anchor oluşturabilir?
- Pending BASE varken ikinci BASE, SAFETY ve EXIT davranışı.
- Accepted FILL’in tek ekonomik authority olması.
- Duplicate execution identity ve conflicting duplicate.
- Late fill after final.
- Adapter ile core reducer arasındaki ownership.

#### 6.3 Historical OHLCV execution assumptions

- Placement bar eligible mi?
- Equality touch ile strict penetration ayrımı.
- Gap/open fill price.
- Fixed slice ve exact remainder.
- Aynı bar içinde birden fazla olası sıra.
- Ambiguous bar’da committed prefix.
- EOF’de forced fill/cancel/expiry yasağı veya koşullu kullanımı.
- Stop/limit/market davranışlarının birbirine karıştırılmaması.

#### 6.4 P1.07 test matrisi

En az şu testleri ayrıntılı fixture ve expected state ile ver:

- no-fill pending order,
- equality observation,
- strict candidate,
- rejected candidate,
- accepted partial fill,
- full fill without final coverage,
- full fill plus valid final coverage,
- partial BASE blocks SAFETY,
- explicit cancel,
- EOF pending order,
- ambiguous committed prefix,
- known duplicate,
- conflicting duplicate,
- late fill,
- crash/retry replay,
- deterministic replay,
- legacy profile isolation,
- `reserve_model=NONE` versus explicit numeric reserve.

### P1.08 — Multi-deal lifecycle

Araştır:

- deal start/stop/pause/finish/copy state-machine’i,
- cooldown ve restart davranışı,
- immutable active config revision,
- bir deal’in diğer deal’in order/risk state’ini etkilememesi,
- saved run ile active deal ayrımı,
- failed/aborted/completed/paused durumları,
- lifecycle event dedupe ve persistence.

### P1.09 — Advanced DCA and sizing

Araştır:

- BASE, QUOTE ve balance-percent sizing,
- custom ladder ve safety amount matematiği,
- reinvest ve realized profit ayrımı,
- maximum budget ve maximum exposure,
- quantity/tick/notional rounding,
- fee/funding dahil sizing sınırları,
- ladder quantity sum invariant’ı,
- exact Fraction/Decimal boundary.

Kullanıcıya gösterilen önizleme ile accepted economic order state’ini ayrı tut.

### P1.10 — Multi-TP, SL, trailing ve breakeven

Araştır:

- trigger ile execution ayrımı,
- multiple take-profit quantity conservation,
- stop ve limit fill farkı,
- trailing activation ve ratchet state,
- breakeven hesabı,
- fee-aware target,
- gap ve ambiguity,
- cancel-replace ve late fill,
- partial exit sonrası yeni risk gate.

### P1.11 — Shared virtual account

Araştır:

- account ownership,
- pair/bot bazlı position ownership,
- ortak balance ve exposure,
- concurrent order reservation,
- double counting önleme,
- restart ve replay,
- multi-writer conflict.

### P1.12 — Spot ve linear futures modeli

Bu bölüm en derin araştırma bölümlerinden biri olmalıdır.

#### 6.5 Ürün ayrımı

- Spot inventory ile futures position aynı state olarak modellenebilir mi?
- Linear futures long/short yönleri.
- Contract size, quote/base settlement ve quantity unit.
- Mark price, index price, last price ve trigger price farkları.
- Funding payment ve funding timestamp.
- Trading fee, funding fee ve liquidation fee ayrımı.

#### 6.6 Margin modeli

- Initial margin.
- Maintenance margin.
- Available margin.
- Isolated margin.
- Cross margin.
- Leverage.
- Unrealized PnL’nin margin state’e etkisi.
- Margin call ve liquidation threshold.
- Partial liquidation.
- Exact formula, asset/unit ve rounding.

#### 6.7 Test/oracle gereksinimleri

En az şu modeller için bağımsız oracle fixture’ları öner:

- long price increase/decrease,
- short price increase/decrease,
- funding positive/negative,
- fee deduction,
- isolated margin exhaustion,
- cross margin shared loss,
- mark/index divergence,
- liquidation boundary,
- partial close,
- restart/replay.

Spot ve futures’i aynı reserve veya fee formülüyle birleştiren önerileri varsayılan olarak `REJECT` veya `DEFER` değerlendir.

### P1.13 — Grid ve related strategy families

Araştır:

- arithmetic/geometric grid,
- grid level generation,
- inventory conservation,
- grid profit ile total equity farkı,
- trailing up/down,
- infinity/reverse grid,
- leveraged grid’in ayrı risk modeli,
- partial fill ve level replacement,
- grid order dedupe.

Her grid ailesini yalnız isim değişikliğiyle aynı model kabul etme.

### P1.14 — Rebalancing, signal ve templates

Araştır:

- target allocation ve threshold rebalancing,
- event-time ve dedupe,
- webhook/signal replay protection,
- indicator warmup ve closed-bar rule,
- strategy template versioning,
- import/export güvenliği,
- template’in yetkisiz emir açamaması.

### P1.15 — Hedge, cross ve çift bacaklı modeller

Bu bölüm en derin araştırma bölümlerinden biri olmalıdır.

#### 6.8 Hedge ve netting

- Net position ile hedge position farkı.
- Long ve short’un ayrı mı, net mi tutulacağı.
- Same-symbol opposite-side order davranışı.
- Reduce-only ve close-position semantics.
- Position owner ve deal owner.

#### 6.9 Cross margin ve iki bacak

- Bacaklar arası ortak margin.
- One-leg-filled / other-leg-unfilled state.
- Leg sequencing ve timeout.
- Partial hedge.
- Spread, funding, borrow, transfer ve fee.
- One-leg liquidation.
- Atomicity ve recovery.

Her iki bacaklı davranış için ayrı state-machine ve bağımsız oracle iste. Spot ve futures varsayımlarını aynılaştırma.

### P1.16 — Walk-forward, OOS ve stres çalışma alanı

Bu bölüm en derin araştırma bölümlerinden biri olmalıdır.

#### 6.10 Time split ve leakage

- Train/validation/test ayrımı.
- Walk-forward window türleri.
- Purging ve embargo gereksinimi.
- Indicator warmup leakage.
- Parameter selection leakage.
- Dataset boundary ve corporate/action-like adjustments gerekiyorsa bunların etkisi.

#### 6.11 Run comparison

- Aynı dataset/config/model/kernel identity.
- Seed ve deterministic replay.
- Failed/dropped/invalid run ayrımı.
- OOS sonucunun in-sample sonuçtan ayrılması.
- Hyperparameter multiple-testing riski.
- Benchmark ve baseline seçimi.

#### 6.12 Stres modeli

- Spread/slippage.
- Latency.
- Volume participation.
- Partial fill.
- OHLC ambiguity.
- Missing/gap data.
- Worst-case ve best-case ayrımı.
- Stress sonucunun normal backtest sonucu gibi sunulmaması.

Her önerinin veri sızıntısı ve reproducibility riskini ayrıca yaz.

### P1.17 — Public fiyatla simulated runtime

Araştır:

- Read-only public feed.
- Stale data.
- Gap/reconnect.
- Clock and event ordering.
- Simulated adapter sınırı.
- Credential olmadan demo.
- Live exchange order id’si ile local simulated execution identity ayrımı.

### P1.18 — Açıklama, bildirim ve template paylaşımı

Araştır:

- Offline rule-based explanation.
- Risk/rejection explanation.
- Event/notification severity.
- Optional LLM sınırı.
- LLM’nin economic state değiştirememesi.
- Template paylaşımında version/hash/integrity.

### P1.19 — UX, erişilebilirlik ve kurulum

Bu bölüm için görsel araştırma gerekirken yeni görsel kararları doğrudan varsayma. Görsel kaynak gerekiyorsa ayrıca anonim görsel araştırma alt talebi üret.

Araştır:

- responsive desktop/mobile,
- 320px görünüm,
- keyboard/focus,
- screen reader,
- color/grayscale ve risk severity,
- empty/loading/error/indeterminate/corrupt states,
- dark/light theme,
- offline Windows installation/startup.

UI financial values’ı yeniden hesaplamamalı; backend contract’ını aynen göstermelidir.

### P1.20 — Final P1 acceptance

Final kabul için zorunlu gate listesi üret:

- feature matrix coverage,
- data ingestion and checksum,
- deterministic historical run,
- exact math oracle,
- core authority,
- reserve/order lifecycle,
- persistence/reopen,
- UI responsive/accessibility,
- security and secret isolation,
- Windows E2E,
- independent review,
- demo package and known limitations.

Bir özelliğin menüde görünmesini implementation kanıtı sayma.

## 7. Matematiksel model standardı

Her matematiksel model için şu tabloyu doldur:

| Alan | Zorunlu içerik |
|---|---|
| Değişken | Sembol ve anlamı |
| Birim | Base asset, quote asset, contract, percentage vb. |
| İşaret | Pozitif/negatif yönü |
| Precision | Exact numeric gereksinimi |
| Rounding | Hangi event ve hangi owner |
| Input | Hangi state/event alanlarından gelir |
| Output | Hangi state’i değiştirir |
| Authority | Core, adapter, venue veya UI |
| Invariant | Her durumda korunacak eşitlik |
| Failure | Fail-closed davranış |
| Oracle | Production’dan bağımsız beklenen sonuç |

`float`, epsilon veya bilinmeyeni numeric `0` yapma önerilerini özellikle işaretle.

## 8. Kod davranışı talep protokolü

Local code görülmeden production kararı veremiyorsan, tüm repository’yi isteme. Aşağıdaki dar taleplerden yalnız gerekeni seç:

1. `State`, `Order`, `Position` ve varsa reserve/commitment schema’sı.
2. `INTENT`, `FILL`, `ORDER_FINAL`, `UNKNOWN`, `MARK` reducer branch’i.
3. Initial-margin estimate ve çağıran acceptance path.
4. Pending/unsettled blocker.
5. Historical adapter candidate → core FILL call chain’i.
6. Anchor creation ve SAFETY decision zinciri.
7. Duplicate/late fill ve persistence dedupe test body’si.
8. Partial fill, EOF, ambiguity ve cancel fixture’ları.
9. Fee/slippage/quantity conversion owner’ı.
10. Public DTO/serializer ve legacy compatibility testi.

Kod talebinde:

- Her snippet en fazla yaklaşık 120 satır olsun.
- Gerçek isimleri placeholder ile değiştir.
- Secret, credential, token, path, URL, DB adı ve kullanıcı verisi alma.
- Yalnız belirli soruyu cevaplayan branch/test’i iste.
- Kod verilmezse mevcut implementation hakkında kesin hüküm verme.

## 9. Klasör teslim biçimi

Araştırmayı aşağıdaki gibi tasniflenmiş bir klasör olarak teslim et:

```text
P1_KRITIK_ARASTIRMA/
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
├── sources/
│   ├── SOURCE_INDEX.md
│   └── SOURCE_CARDS.md
├── decision_matrices/
│   ├── CLAIM_DECISION_MATRIX.md
│   ├── FORMULA_MATRIX.md
│   └── PHASE_GATE_MATRIX.md
├── test_matrices/
│   ├── P1.07_TESTS.md
│   ├── P1.12_TESTS.md
│   ├── P1.15_TESTS.md
│   └── P1.16_TESTS.md
└── code_requests/
    ├── LOCAL_CODE_REQUIRED.md
    └── ANONYMIZED_SNIPPET_REQUESTS.md
```

`00_README.md` içinde şu bilgileri yaz:

- Araştırma tarihi.
- Kullanılan kaynak sayısı.
- Birincil kaynak sayısı.
- Local code görülüp görülmediği.
- Hangi konuların production-ready olmadığı.
- Hangi kararların yalnız conditional olduğu.
- Araştırmanın kapsamadığı konular.

## 10. Master decision summary zorunluluğu

`01_MASTER_DECISION_SUMMARY.md` dosyası en fazla birkaç sayfalık yönetici özeti olsun ve şu tabloyu içersin:

| Faz | Konu | Karar | Production’a hazır mı? | Kritik açık | Gerekli sonraki kanıt |
|---|---|---|---|---|---|
| P1.07 | Reserve/order |  |  |  |  |
| P1.12 | Futures |  |  |  |  |
| P1.15 | Hedge/cross |  |  |  |  |
| P1.16 | Walk-forward |  |  |  |  |

Her faz için ayrıca şu üç ifadeyi yaz:

```text
Şimdi uygulanabilir:
Henüz uygulanamaz:
Uygulama sırasında tekrar kanıt istenebilir:
```

## 11. Araştırma sonunda beklenen sonuç

Araştırma şunları üretmeli:

1. P1’in kritik domain çerçevesi.
2. Faz sırasını bozmayan implementation gate’leri.
3. Her kritik model için state-machine.
4. Her kritik hesap için formül ve bağımsız oracle yaklaşımı.
5. Reserve/order, futures, hedge/cross ve walk-forward için derin test matrisi.
6. Local code gerekli olan noktaların dar ve anonim listesi.
7. Hangi konular için daha sonra ayrıca araştırma istenmesinin zorunlu olduğu.
8. Araştırma raporu ile implementation kararının karıştırılmaması için açık sınırlar.

## 12. Son kural

Genel, kaynaksız veya “sektörde genellikle böyledir” türü ifadelerle production kararı verme.

Bir model ekonomik sonucu, risk kararını, state authority’yi, persistence bütünlüğünü veya kullanıcı yorumunu değiştiriyorsa bunu kritik kabul et.

Kritik bir belirsizlik çıktığında sessizce varsayım yapma. Şu formatta ayrıca bildir:

```text
NEW_EVIDENCE_REQUIRED: YES
PHASE:
UNKNOWN_BEHAVIOR:
WHY_IT_CHANGES_IMPLEMENTATION:
SAFE_ANONYMOUS_RESEARCH_REQUEST:
REQUIRED_CODE_SNIPPET_IF_ANY:
DO_NOT_IMPLEMENT_UNTIL:
```

Bu dosyanın amacı, araştırmayı tek bir ana pakette toplamak ve uygulama sırasında yalnız gerçekten kritik yeni kanıt gerektiğinde durmaktır.
