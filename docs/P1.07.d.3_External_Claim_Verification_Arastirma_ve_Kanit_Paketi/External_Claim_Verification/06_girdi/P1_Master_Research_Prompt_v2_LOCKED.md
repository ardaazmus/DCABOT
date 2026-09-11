# P1 Master Research v2 — LOCKED DELIVERY PROMPT
## Kritik bot davranışları ve matematik modelleri için eksiksiz, kaynaklı araştırma talebi

## 0. Bu görevin bağlayıcı niteliği

Bu metni baştan sona uygula. Bu bir konu listesi, fikir alma veya önceki raporu özetleme talebi değildir. P1’in kritik alanları için gerçek dış araştırma yap ve sonuçları kanıtlı, dosyalanmış, tekrar denetlenebilir bir araştırma paketi olarak teslim et.

Soruları yalnızca tekrar etmek, kaynak URL’lerini listelemek, önceki AI cevabını yeniden yazmak veya “local code gerekli” diyerek dış araştırmayı bırakmak tamamlanmış teslim sayılmaz.

Araştırmanın her zorunlu konusu için şu dört sonuçtan biri verilmelidir:

```text
VERIFIED
CONDITIONAL
UNSUPPORTED
NOT_VERIFIED / BLOCKED
```

Hiçbir zorunlu soru cevapsız bırakılamaz. Dış kaynakla cevaplanamayan konu `NOT_VERIFIED/BLOCKED` olarak açıkça kaydedilmeli, neden açıklanmalı, gerekli local code/test dar biçimde istenmeli ve araştırmanın geri kalan bölümleri yine de tamamlanmalıdır.

`RESEARCH_COMPLETE: YES` yalnız bu promptun teslim gate’leri eksiksiz geçerse kullanılabilir. Herhangi bir zorunlu dosya, bölüm, iddia, kaynak, test, formül veya karar eksikse:

```text
RESEARCH_COMPLETE: NO
MISSING_DELIVERABLES:
BLOCKING_REASONS:
```

## 1. Önceki raporlar hakkında kesin kural

Önceki AI yanıtları, önceki araştırma raporları, varsayımsal kararlar ve prompt metinleri kanıt değildir.

Bunları yalnızca:

- arama terimi,
- konu keşfi,
- karşılaştırma başlığı,
- yeniden doğrulanacak iddia

olarak kullan.

Önceki rapor “araştırıldı”, “standardır”, “production-ready’dir” veya “local code yoktur” diyorsa bunu yeni kaynaklarla yeniden kontrol et.

Teslimde `claims/PREVIOUS_CLAIM_RECHECK.md` dosyasını oluştur ve önceki iddiaların her birini şu tabloyla yeniden değerlendir:

| Önceki iddia | Yeni kaynakla kontrol edildi mi? | Sonuç | Kaynak | Düzeltme |
|---|---:|---|---|---|
|  |  | CONFIRMED / REVISED / REJECTED / NOT_VERIFIED |  |  |

## 2. Proje bağlamı

İncelenen ürün, yerel ve offline çalışan tarihsel piyasa verisi tabanlı bir DCA simülatörüdür. P1’de amaç gerçek borsa emri göndermek değil; doğrulanabilir, deterministic ve açık varsayımlı bir simülasyon ürünüdür.

P1 sırası:

```text
P1.05 sonuç/ekonomi
P1.06 kalıcı run
P1.07 partial fill/order davranışları
P1.08 multi-deal lifecycle
P1.09 advanced DCA/sizing
P1.10 TP/SL/trailing/breakeven
P1.11 shared virtual account
P1.12 spot/futures modelleri
P1.13 grid aileleri
P1.14 rebalancing/signal/template
P1.15 hedge/cross/two-leg
P1.16 walk-forward/OOS/stress
P1.17 simulated public runtime
P1.18 explanation/notification/template sharing
P1.19 UX/accessibility/install
P1.20 final acceptance
```

## 3. Anonimlik ve güvenlik

Teknik doğruluk için proje adı veya non-sensitive kod adı gerektiğinde kullanılabilir. Ancak hiçbir koşulda şunları isteme veya teslim dosyasına koyma:

- API key, secret, token, password, credential,
- canlı hesap/pozisyon/bakiye bilgisi,
- wallet veya account kimliği,
- private URL veya özel kullanıcı verisi,
- `.env` içeriği,
- veritabanı sırrı,
- gereksiz tam repository arşivi.

Local code gerekiyorsa yalnız ilgili sembol, branch veya test gövdesini iste. Her snippet için maksimum boyut, neden ve kapanacak soruyu belirt.

## 4. Araştırmanın zorunlu akışı

Her konu için şu sırayı uygula:

1. Terimleri tanımla.
2. Birincil kaynakları bul.
3. Kaynak sürümü ve güncelliğini kaydet.
4. Kaynakta doğrudan bulunan davranışı çıkar.
5. Kaynak kapsamını aşan yorumu ayır.
6. Kaynak çatışmalarını çöz veya unresolved bırak.
7. Offline simulator’a uygulanabilirliği değerlendir.
8. Event/state geçişini yaz.
9. Matematiksel değişkenleri, asset/unit ve precision’ı yaz.
10. Positive, negative, ambiguity, EOF ve replay davranışını yaz.
11. Bağımsız oracle ve test fixture’ı yaz.
12. `ACCEPT`, `SIMPLIFY`, `DEFER`, `REJECT` kararını ver.
13. Local code gerekiyorsa dar code request oluştur.

## 5. Kaynak ve çatışma standardı

Kaynak önceliği:

1. Resmi exchange/API dokümanı.
2. FIX, ISO, IEEE, IETF, Python veya ilgili resmi standart.
3. Hakemli akademik kaynak.
4. Resmi backtest/simülasyon dokümanı.
5. Güvenilir teknik kaynak.
6. Rakip ürün dokümanı; yalnız özellik keşfi.

Her kaynak kartında zorunlu alanlar:

```text
SOURCE_ID:
PUBLISHER:
TITLE:
URL:
ACCESS_DATE:
SOURCE_VERSION:
DOC_LAST_UPDATED:
PRODUCT_VERSION_APPLICABILITY:
EXACT_SECTION_OR_HEADING:
SUPPORTED_CLAIMS:
UNSUPPORTED_CLAIMS:
ARCHIVE_REFERENCE_IF_AVAILABLE:
```

Sürüm veya güncelleme tarihi kaynakta yoksa `VERSION_UNAVAILABLE` veya `LAST_UPDATED_UNAVAILABLE` yaz; tahmin etme.

Kaynaklar çelişirse şu kaydı oluştur:

```text
CONFLICT_ID:
SOURCE_A:
SOURCE_B:
CONFLICTING_PROPOSITIONS:
PRODUCT_AND_VERSION_SCOPE:
PRECEDENCE_REASON:
CONFLICT_STATUS: RESOLVED | UNRESOLVED
SELECTED_RULE:
DO_NOT_IMPLEMENT_IF_UNRESOLVED: YES | NO
```

Çözülemeyen ve ekonomik sonucu değiştiren çatışma `DO_NOT_IMPLEMENT_IF_UNRESOLVED: YES` olmalıdır.

## 6. Her iddia için zorunlu kayıt

`claims/CLAIM_REGISTER.md` içinde her kritik iddiayı aşağıdaki formatta kaydet:

```text
CLAIM_ID:
PHASE:
TOPIC:
CLAIM:
TYPE: DOMAIN | MATHEMATICAL | CODE_BEHAVIOR | DATA | API | PERSISTENCE | UI | SECURITY
STATUS: VERIFIED | CONDITIONAL | UNSUPPORTED | NOT_VERIFIED | LOCAL_CODE_REQUIRED | BLOCKED
SOURCES:
SOURCE_SECTIONS:
EVIDENCE_SUMMARY:
SOURCE_SCOPE_LIMIT:
CONFLICT_STATUS:
LOCAL_APPLICABILITY:
IMPLEMENTATION_DECISION: ACCEPT | SIMPLIFY | DEFER | REJECT
EXPECTED_TEST:
NEGATIVE_EXPECTATION:
REQUIRED_CODE_OR_FIXTURE:
```

`VERIFIED` etiketi yalnız doğrudan kaynak veya bağımsız hesapla desteklenen iddialar için kullanılabilir.

## 7. Global invariant’lar

### 7.1 Zaman türleri

Şu zamanların farkını ve owner’ını bütün ilgili fazlar için tanımla:

- `event_time`,
- `receive_time`,
- `processing_time`,
- `bar_open_time`,
- `bar_close_time`,
- `effective_time`,
- `persistence_time`,
- `display_time`.

Her event için ekonomik kararı hangi zamanın verdiğini yaz. Processing veya wall-clock zamanını historical event-time yerine koyma.

### 7.2 Execution identity

Canonical identity bileşenlerini araştır:

- venue scope,
- order identity,
- execution identity,
- local event identity,
- economic side,
- event sequence/timestamp,
- canonical payload hash.

Bilinen duplicate, aynı identity ile farklı payload conflict’i ve yeni late event ayrı sınıflandırılmalıdır.

### 7.3 Atomic economic transition

Şu invariant’ı P1.07, P1.10, P1.11, P1.12, P1.15 ve P1.16 için ayrı kontrol et:

```text
Accepted Economic FILL
→ position/cost mutation
→ fee mutation
→ cumulative/leaves mutation
→ reserve/commitment mutation if enabled
→ dedupe identity recording
→ resulting state/version recording
```

Bu ekonomik etkiler ya tek atomic semantic transition olarak commit edilmeli ya da hiçbiri commit edilmemelidir.

### 7.4 Canonical serialization/hash

Araştır:

- field ordering,
- omitted/default/null alanları,
- Decimal/Fraction serialization,
- timezone normalization,
- schema version,
- algorithm,
- encoding/Unicode normalization,
- canonical JSON veya eşdeğer format.

### 7.5 Numeric boundary

Şu sınırları ayrı tanımla:

```text
input parse
→ exact internal representation
→ economic calculation
→ persistence representation
→ public API representation
→ UI formatting
```

Economic rounding, API serialization ve UI formatting aynı işlem değildir. Unknown/not-modeled değerleri numeric `0` yapma.

### 7.6 Global result taxonomy

Şu durumların ekonomik, API, persistence ve UI anlamını yaz:

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
BLOCKED
```

## 8. P1.05/P1.06 sonuç ve kalıcı run araştırması

Mutlaka cevapla:

- realized/unrealized/equity/fee/funding/ROI/drawdown ayrımı,
- incomplete/indeterminate result summary sınırı,
- dataset/config/model/kernel identity,
- seed ve deterministic replay,
- immutable save/reopen/reproduce/compare,
- export/audit,
- result hash ve canonical serialization,
- kaydedilmiş sonuç ile yeniden hesaplanan sonuç arasındaki fark.

Her metriğin formülünü, asset/unit’ini, owner’ını, incomplete durumda gösterilip gösterilmeyeceğini ve bağımsız oracle’ını ver.

## 9. P1.07 derin araştırma: order, partial fill, reserve

### 9.1 Order lifecycle

Şunları kaynaklı ve state-machine biçiminde cevapla:

- `OPEN`, `PARTIALLY_FILLED`, `FILLED`, `CANCELED`, `UNKNOWN`, `OPEN_AT_END`, `INDETERMINATE`,
- original/cumulative/leaves/terminal remainder,
- full quantity fill ile final coverage farkı,
- anchor owner ve timing,
- pending BASE varken BASE/SAFETY/EXIT,
- duplicate/conflict/late fill,
- adapter/core authority.

### 9.2 Reserve/commitment lifecycle

Mutlaka cevapla:

- reserve asset ve unit,
- quantity/quote/risk-capacity anlamı,
- acquisition owner event’i,
- reduction owner event’i,
- release owner event’i,
- `INTENT`, `ACTIVE`, candidate veya accepted `FILL` seçimi,
- candidate reserve mutation yapabilir mi,
- equality touch etkisi,
- partial fill sonrası commitment,
- fee dahilliği ve farklı fee asset conversion,
- rounding/step owner,
- explicit cancel/expiry/EOF,
- ambiguous bar davranışı,
- duplicate/late/crash/retry,
- `reserve_model=NONE` ile numeric zero farkı,
- initial-margin estimate ile reserve ayrımı.

### 9.3 Historical OHLCV execution

- placement bar eligibility,
- equality touch,
- strict penetration,
- gap/open fill,
- fixed slice ve exact remainder,
- same-bar path ambiguity,
- committed prefix cutoff,
- EOF’de forced fill/cancel/expiry,
- limit/stop/market authority.

### 9.4 P1.07 test matrisi

Her test için fixture, event sırası, expected state, negative assertion ve bağımsız kontrol ver:

1. Pending BASE no-fill.
2. Equality observation.
3. Strict candidate.
4. Rejected candidate.
5. Accepted partial fill.
6. Full fill without final coverage.
7. Full fill with valid final coverage.
8. Partial BASE blocks SAFETY.
9. Explicit cancel.
10. EOF pending.
11. Ambiguous committed prefix.
12. Known duplicate.
13. Conflicting duplicate.
14. New late fill.
15. Crash/retry.
16. Deterministic replay.
17. Legacy isolation.
18. NONE reserve versus explicit reserve.

## 10. P1.08–P1.11 lifecycle, sizing ve shared account

### P1.08

Start, pause, stop, finish, copy, cooldown, restart, immutable config, failed/aborted/completed/paused ve lifecycle dedupe state-machine’lerini çıkar.

### P1.09

BASE/QUOTE/balance-percent sizing, custom ladder, safety amount, reinvest, max budget/exposure, tick/notional rounding, fee/funding etkisi ve ladder conservation formüllerini ver.

### P1.10

Multi-TP, SL, trailing, breakeven, trigger/execution ayrımı, fee-aware target, gap, ambiguity, cancel-replace, late fill ve partial exit risk gate’ini araştır.

### P1.11

Multi-bot/pair shared virtual account, ownership, account reservation, concurrency, double counting, restart/replay ve conflict davranışını araştır.

## 11. P1.12 derin araştırma: spot ve linear futures

### 11.1 Ürün ve fiyat

- Spot inventory versus futures position.
- Linear long/short.
- Contract size ve settlement asset.
- Mark/index/last/trigger price.
- Funding rate/time.
- Trading/funding/liquidation fee.

### 11.2 Margin/accounting

Asset/unit tablosu ile cevapla:

- wallet balance,
- margin balance,
- available balance/margin,
- position margin,
- order margin,
- initial margin,
- maintenance margin,
- isolated margin,
- cross margin,
- leverage,
- unrealized/realized PnL,
- margin call,
- liquidation,
- partial liquidation,
- bankruptcy/negative balance.

### 11.3 Futures oracle/test

Long/short PnL, positive/negative funding, fee, isolated exhaustion, cross shared loss, mark/index divergence, maintenance boundary, liquidation, partial close ve replay için bağımsız expected calculation ver.

Venue-specific formülü universal finans formülü gibi sunma. Venue ve sürüm kaynağı yoksa liquidation/margin kararını `DEFER` veya `BLOCKED` bırak.

## 12. P1.13–P1.14 strategy families

Grid için arithmetic/geometric level, inventory, grid profit/equity farkı, trailing/infinity/reverse, leveraged grid, partial fill ve level replacement’ı ayrı modeller halinde araştır.

Rebalancing/signal/template için target allocation, threshold/time, event-time, dedupe/replay, indicator warmup, closed-bar, version/hash, import/export security ve template authority’sini araştır.

## 13. P1.15 derin araştırma: hedge, cross margin, two-leg

### 13.1 Hedge/netting

- Net versus hedge position.
- Long/short ayrı state veya net state.
- Opposite-side same-symbol orders.
- Reduce-only/close-position.
- Position/deal owner.
- Fee/funding/settlement.

### 13.2 Cross margin

Wallet balance, margin balance, available balance, position margin, order margin, maintenance requirement, realized/unrealized PnL ve bankruptcy boundary ilişkisini asset/unit tablosuyla ver.

### 13.3 Two-leg lifecycle

One-leg-filled, other-leg-unfilled, sequencing, timeout, partial hedge, spread, funding/borrow/transfer, one-leg liquidation, atomicity, recovery ve replay için ayrı state-machine ve oracle ver.

## 14. P1.16 derin araştırma: walk-forward, OOS, stress

### 14.1 Leakage

Train/validation/test, walk-forward windows, purging, embargo, indicator warmup leakage, parameter-selection leakage ve dataset adjustment leakage’i kaynaklı cevapla.

### 14.2 OOS freeze

Şu kuralın kaynak ve testini ver:

```text
OOS sonucu görüldükten sonra tuning yapılırsa aynı OOS untouched evaluation olmaktan çıkar.
Yeni tuning için yeni untouched holdout gerekir.
```

### 14.3 Comparison/multiple testing

Dataset/config/model/kernel identity, seed, deterministic replay, failed/dropped/invalid run, benchmark ve hyperparameter multiple testing protokolünü çıkar.

### 14.4 Stress

Spread, slippage, latency, volume participation, partial fill, OHLC ambiguity, missing/gap, best/worst case ve stress sonucunun normal backtest gibi sunulmaması için model/test ver.

## 15. P1.17–P1.20 runtime, explanation, UX ve final

### P1.17

Read-only feed, stale/gap/reconnect, clock/event ordering, simulated adapter, credentialsiz demo, local/venue execution identity ve failure recovery.

### P1.18

Offline explanation, rejection/risk reason, severity, notification dedupe, optional LLM boundary, state değiştiremeyen assistant ve template integrity.

### P1.19

Desktop/mobile, 320px, keyboard/focus, screen reader, contrast/grayscale, empty/loading/error, `INDETERMINATE`, `CORRUPT`, `OPEN_AT_END`, dark/light, offline Windows install/startup. Yeni görsel karar için kaynak ve ekran kanıtı ver.

### P1.20

Feature matrix, data, math, core authority, reserve/order, persistence, UI, security, Windows E2E, independent review, packaging ve known limitations final gate’lerini çıkar.

## 16. Formula ve exact numeric standardı

Her formül için şu tablo zorunludur:

| Alan | Cevap |
|---|---|
| Formula ID |  |
| Formula |  |
| Variables |  |
| Asset/unit |  |
| Sign convention |  |
| Precision |  |
| Rounding owner |  |
| Input event/state |  |
| Output state |  |
| Failure behavior |  |
| Venue applicability |  |
| Independent oracle |  |
| Source |  |

Float epsilon, unknown→0, asset conversionu olmayan scalar toplama ve venue-specific formülü evrenselleştirme yaklaşımlarını açıkça değerlendir.

## 17. Bağımsız oracle ve test standardı

Oracle production reducer, production helper, aynı formula utility’si veya aynı state-machine’i import edemez.

Her kritik alan için:

- literal fixture,
- bağımsız Decimal/Fraction veya tablo hesabı,
- expected state,
- negative state,
- boundary case,
- replay case,
- serialization/hash case

ver.

Metamorphic/property testleri de değerlendir:

- known duplicate sonucu değiştirmemeli,
- replay sayısı sonucu değiştirmemeli,
- exact remainder korunmalı,
- suffix ambiguity prefix’i geri almamalı,
- export/import state’i değiştirmemeli,
- venue-specific formula başka venue’ye otomatik taşınmamalı.

Partial fill parçalama için fee/rounding policy bilinmiyorsa “sonuç kesin değişmez” deme; koşullu karar ver.

## 18. Local code request standardı

External kaynak local implementation’ı kanıtlayamaz. Bu durumda şu kaydı oluştur:

```text
LOCAL_CODE_REQUEST_ID:
PHASE:
UNKNOWN_QUESTION:
WHY_EXTERNAL_SOURCES_CANNOT_ANSWER:
EXACT_SYMBOL_OR_BRANCH:
EXACT_TEST_OR_FIXTURE:
MAX_SNIPPET_SIZE:
REDACTION_RULES:
DECISION_AFTER_CODE:
```

İstenecek kod yalnız şunlardan biri olabilir:

- State/Order/Position/reserve schema,
- INTENT/FILL/ORDER_FINAL/UNKNOWN/MARK branch’i,
- initial-margin çağrı zinciri,
- pending blocker,
- historical adapter → core FILL,
- anchor/SAFETY decision chain,
- duplicate/late/persistence test body’si,
- partial/EOF/ambiguity/cancel fixture’ı,
- public DTO/serializer/legacy testi.

Tüm repository, secret, credential veya gereksiz dosya isteme.

## 19. Zorunlu teslim klasörü

Tam teslimi şu yapıda üret:

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
├── claims/CLAIM_REGISTER.md
├── claims/PREVIOUS_CLAIM_RECHECK.md
├── sources/SOURCE_INDEX.md
├── sources/SOURCE_CARDS.md
├── sources/SOURCE_CONFLICTS.md
├── evidence/EVIDENCE_MANIFEST.md
├── evidence/PRIMARY_SOURCE_EVIDENCE.md
├── formulas/FORMULA_REGISTER.md
├── formulas/INDEPENDENT_ORACLE_SPEC.md
├── test_matrices/P1.07_TESTS.md
├── test_matrices/P1.12_TESTS.md
├── test_matrices/P1.15_TESTS.md
├── test_matrices/P1.16_TESTS.md
├── code_requests/LOCAL_CODE_REQUIRED.md
└── MANIFEST.md
```

## 20. Zorunlu master karar tablosu

`01_MASTER_DECISION_SUMMARY.md` içinde her satırı doldur:

| Faz | Araştırma tamam mı? | Karar | Implementation-ready? | Kritik açık | Kanıt | Sonraki gate |
|---|---:|---|---:|---|---|---|
| P1.05/P1.06 |  |  |  |  |  |  |
| P1.07 |  |  |  |  |  |  |
| P1.08 |  |  |  |  |  |  |
| P1.09 |  |  |  |  |  |  |
| P1.10 |  |  |  |  |  |  |
| P1.11 |  |  |  |  |  |  |
| P1.12 |  |  |  |  |  |  |
| P1.13 |  |  |  |  |  |  |
| P1.14 |  |  |  |  |  |  |
| P1.15 |  |  |  |  |  |  |
| P1.16 |  |  |  |  |  |  |
| P1.17 |  |  |  |  |  |  |
| P1.18 |  |  |  |  |  |  |
| P1.19 |  |  |  |  |  |  |
| P1.20 |  |  |  |  |  |  |

Her faz için ayrıca doldur:

```text
Şimdi uygulanabilir:
Şimdilik uygulanamaz:
Uygulama sırasında yeni kanıt gerektirebilecek tek konu:
```

## 21. Evidence manifest standardı

`evidence/EVIDENCE_MANIFEST.md` ve `MANIFEST.md` içinde:

- tüm dosya yolları,
- dosya boyutları,
- araştırma sürümü,
- oluşturulma tarihi,
- kaynak sayısı,
- birincil kaynak sayısı,
- checksum,
- kaynak arşiv durumu

bulunmalıdır.

Tam web sayfası veya telifli doküman kopyalama. Kısa kanıt pasajı/paraphrase, heading, URL, sürüm ve tarih yeterlidir.

## 22. Final completeness gate

Teslimden önce aşağıdaki her satıra `PASS` veya `FAIL` yaz:

| Gate | Sonuç |
|---|---|
| Bütün P1.05–P1.20 bölümleri mevcut |  |
| P1.07 derin soruları cevaplandı |  |
| P1.12 derin soruları cevaplandı |  |
| P1.15 derin soruları cevaplandı |  |
| P1.16 derin soruları cevaplandı |  |
| Her kritik iddianın kaynak/status/kararı var |  |
| Her formülün unit/precision/rounding/oracle bilgisi var |  |
| Kaynak sürümü ve erişim tarihi var |  |
| Kaynak çatışmaları kaydedildi |  |
| Event-time taxonomy global olarak işlendi |  |
| Execution identity işlendi |  |
| Atomic transition işlendi |  |
| Canonical hash işlendi |  |
| Numeric boundary işlendi |  |
| Result taxonomy işlendi |  |
| Independent oracle production’dan ayrıldı |  |
| Negative ve fail-closed testleri var |  |
| Metamorphic/property test değerlendirmesi var |  |
| OOS freeze kuralı var |  |
| Market-data integrity gate’i var |  |
| Import/export/security gate’i var |  |
| Local code request’leri dar ve anonim |  |
| Previous claim recheck mevcut |  |
| Evidence manifest mevcut |  |
| SHA-256 manifest mevcut |  |
| Eksik konular açıkça BLOCKED/NOT_VERIFIED |  |

Bir satır bile `FAIL` ise `RESEARCH_COMPLETE: YES` yazma.

## 23. Son teslim mesajı

Son mesajını şu formatta ver:

```text
RESEARCH_COMPLETE: YES | NO
PACKAGE_ROOT:
TOTAL_REQUIRED_PHASES:
COMPLETED_PHASE_REPORTS:
BLOCKED_PHASES:
VERIFIED_CLAIMS:
CONDITIONAL_CLAIMS:
UNSUPPORTED_CLAIMS:
LOCAL_CODE_REQUIRED_COUNT:
PRIMARY_SOURCE_COUNT:
SOURCE_CONFLICT_COUNT:
FORMULA_COUNT:
TEST_MATRIX_COUNT:
ORACLE_STATUS:
MANIFEST_STATUS:
SHA256_STATUS:
IMPLEMENTATION_READY_PHASES:
DEFERRED_PHASES:
REJECTED_APPROACHES:
MISSING_DELIVERABLES:
BLOCKING_REASONS:
```

Bu son teslim alanlarından herhangi birini boş bırakma. Değer bilinmiyorsa `UNKNOWN` yaz ve nedenini ilgili dosyada açıkla.

## 24. Uygulama sırasında yeni kanıt talebi

Araştırma tamamlandıktan sonra local implementation sırasında kritik belirsizlik çıkarsa sessizce varsayım yapma:

```text
NEW_EVIDENCE_REQUIRED: YES
PHASE:
UNKNOWN_BEHAVIOR:
CURRENT_LOCAL_EVIDENCE:
WHY_IMPLEMENTATION_CHANGES:
MINIMUM_RESEARCH_QUESTION:
REQUIRED_CODE_SNIPPET_IF_ANY:
DO_NOT_IMPLEMENT_UNTIL:
```

Yeni kanıt yalnız ekonomik sonuç, event authority, exact formula, asset/unit, persistence/replay, venue-specific davranış, güvenlik veya yeni UI/UX anlamını değiştiriyorsa istenebilir.

## 25. Son bağlayıcı talimat

Şimdi araştırmayı gerçekten yap. Önceki raporu temel alma. Her zorunlu soruyu cevapla veya açıkça `NOT_VERIFIED/BLOCKED` kaydı oluştur. Hiçbir iddiayı kaynaksız kabul etme. Hiçbir local implementation davranışını kod görmeden kesinleştirme. Büyük production kod blokları yazma. Araştırma paketini, manifestini ve checksum’ını eksiksiz teslim et.
