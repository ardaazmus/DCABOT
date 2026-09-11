# P1 Master Research — FINAL
## Tek bağlayıcı araştırma talebi: P1.05–P1.20 kritik bot davranışları ve matematik modelleri

## 1. Görevin gerçek amacı

P1’in kritik alanları için gerçek dış araştırma yap ve sonucu sınıflandırılmış bir araştırma klasörü olarak teslim et.

Bu görev:

- soru listesi hazırlama görevi değildir,
- önceki raporu özetleme görevi değildir,
- yalnız P1.07 reserve/order araştırması değildir,
- local test çalıştırılmış gibi sonuç uydurma görevi değildir,
- genel finans bilgisiyle formül tahmin etme görevi değildir.

Her zorunlu soruya kaynaklı cevap, koşullu cevap, açıkça doğrulanamayan cevap veya gerekçeli erteleme kararı ver.

## 2. Önceki teslim hakkında bağlayıcı uyarı

Mevcut çalışma klasöründe bulunan önceki `External_Claim_Verification` paketi yalnız `P1.07.d.3` kapsamındadır. Bu paket:

- 18 rapor bölümü,
- 15 kaynak kartı,
- 30 önerilen local test,
- 14 local gate,
- 48 araştırma oracle kontrolü

içerir; fakat `local_tests_executed=0` ve production kararı `DEFER` durumundadır. Bu paket P1 master araştırması değildir.

Önceki paketin veya herhangi bir AI yanıtının sonucu kanıt kabul edilmez. Önceki içerik yalnız yeniden doğrulanacak iddiaları bulmak için kullanılabilir.

Bu teslimde yalnız P1.07 raporu üretmek, P1.12/P1.15/P1.16’yı atlamak veya P1.07 paketini master araştırma gibi sunmak kesin teslim hatasıdır.

## 3. Zorunlu tamamlanma kuralı

`RESEARCH_COMPLETE: YES` yazabilmek için aşağıdaki 15 ana raporun tamamı mevcut olmalıdır:

```text
P1.05/P1.06
P1.07
P1.08
P1.09
P1.10
P1.11
P1.12
P1.13
P1.14
P1.15
P1.16
P1.17
P1.18
P1.19
P1.20
```

Her raporda kapsam, kaynak, iddia, matematik, state-machine, test, oracle, API/persistence/UI etkisi ve karar bulunmalıdır.

Bir ana rapor, zorunlu alt başlık veya kritik iddia eksikse:

```text
RESEARCH_COMPLETE: NO
MISSING_DELIVERABLES:
BLOCKING_REASONS:
```

Eksik konuyu sessizce kapsam dışı bırakma.

## 4. Proje bağlamı ve uygulama sınırı

Ürün yerel/offline tarihsel piyasa verisiyle çalışan bir DCA simülatörüdür. P1’de gerçek borsa emri gönderme veya canlı hesap yönetimi yapılmaz.

Temel ilkeler:

- Core reducer tek ekonomik authority’dir.
- UI ekonomik hesap yapmaz.
- Grafik koordinatı veya marker ekonomik karar vermez.
- Observation, candidate, accepted economic FILL, ORDER_FINAL ve persisted result ayrı kavramlardır.
- Para girişleri exact Decimal/string sınırında; core iç muhasebe exact rational/Fraction olabilir.
- Bilinmeyen değer numeric `0` yapılamaz.
- Venue-specific davranış universal finans kuralı sayılamaz.
- Plan/status/menü/mock gerçek implementation kanıtı değildir.

## 5. Kimlik ve güvenlik

Teknik doğruluk için proje veya dosya adı gerektiğinde kullanılabilir; ancak şu bilgiler istenmeyecek ve teslim edilmeyecektir:

- API key, secret, token, password, credential,
- canlı hesap veya cüzdan bilgisi,
- özel URL,
- kullanıcı verisi,
- `.env` içeriği,
- veritabanı sırrı,
- gereksiz tam repository.

Local code gerekiyorsa yalnız ilgili branch/symbol/test gövdesini iste. Her code request neden gerektiğini ve hangi soruyu kapatacağını yazmalıdır.

## 6. Kaynak standardı

Kaynak önceliği:

1. Resmi exchange/API dokümanları.
2. FIX, ISO, IETF, IEEE, Python ve ilgili resmi standartlar.
3. Hakemli akademik kaynaklar.
4. Resmi backtest/simülasyon dokümanları.
5. Güvenilir teknik dokümanlar.
6. Rakip ürün dokümanları yalnız özellik keşfi için.

Her kaynak kartı şu alanları taşımalıdır:

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

Kaynak sürüm/tarih vermiyorsa `VERSION_UNAVAILABLE` yaz; uydurma.

## 7. Kaynak çatışması standardı

Farklı kaynakların davranışları çelişirse sessizce birleştirme. `sources/SOURCE_CONFLICTS.md` içinde şu formatı kullan:

```text
CONFLICT_ID:
SOURCE_A:
SOURCE_B:
CONFLICTING_PROPOSITIONS:
PRODUCT_MARKET_VERSION_SCOPE:
PRECEDENCE_REASON:
CONFLICT_STATUS: RESOLVED | UNRESOLVED
SELECTED_RULE:
DO_NOT_IMPLEMENT_IF_UNRESOLVED: YES | NO
```

Çözülemeyen ve ekonomik sonucu etkileyen çatışma implementation’ı bloke eder.

## 8. İddia kayıt standardı

`claims/CLAIM_REGISTER.md` içinde her kritik iddiayı kaydet:

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

`VERIFIED` yalnız doğrudan kaynak veya bağımsız hesapla kanıtlanan iddialar içindir. Local code görülmeden local implementation hakkında kesin hüküm verme.

## 9. Her faz raporu için zorunlu 17 bölüm

P1.05–P1.20 raporlarının her biri şu başlıkların tamamını içermelidir:

1. Kapsam ve kapsam dışı.
2. Terimler ve tanımlar.
3. Kaynak envanteri.
4. İddia karar matrisi.
5. State-machine ve event geçişleri.
6. Matematiksel model.
7. Asset/unit/precision/rounding.
8. Time, ambiguity, EOF, gap, duplicate, late event.
9. Core/API contract etkisi.
10. Persistence/replay/hash etkisi.
11. UI/UX ve yanlış yorum riski.
12. Positive/negative test matrisi.
13. Bağımsız oracle.
14. Metamorphic/property test değerlendirmesi.
15. ACCEPT/SIMPLIFY/DEFER/REJECT kararı.
16. Implementation-ready kabul koşulları.
17. Local code/test talebi ve açık blokajlar.

Bir başlık ilgili değilse “N/A” yazıp nedenini açıkla; başlığı silme.

## 10. Global ortak model

### 10.1 Zaman taxonomy’si

Her ilgili fazda şu zamanların farkını ve owner’ını ver:

- `event_time`,
- `receive_time`,
- `processing_time`,
- `bar_open_time`,
- `bar_close_time`,
- `effective_time`,
- `persistence_time`,
- `display_time`.

Historical event-time ile wall-clock/processing-time karıştırılamaz.

### 10.2 Execution identity

Canonical identity bileşenlerini araştır:

- venue scope,
- order identity,
- execution identity,
- local event identity,
- side,
- timestamp/sequence,
- canonical payload hash.

Known duplicate, conflicting duplicate ve yeni late event ayrı sınıflardır.

### 10.3 Atomic transition

P1.07, P1.10, P1.11, P1.12, P1.15 ve P1.16 için şu invariant’ı kontrol et:

```text
Accepted Economic FILL
→ position/cost
→ fee
→ cumulative/leaves
→ reserve/commitment if enabled
→ dedupe identity
→ resulting state/version
```

Bu etkiler ya birlikte commit edilmeli ya da hiçbiri commit edilmemelidir.

### 10.4 Canonical hash/serialization

Field ordering, null/absent/default, Decimal/Fraction, timezone, schema version, algorithm, encoding ve canonical JSON kurallarını ver.

### 10.5 Numeric boundary

```text
parse → exact internal → economic calculation → persistence → API → UI formatting
```

Economic rounding, API serialization ve UI formatting ayrıdır.

### 10.6 Result taxonomy

Şu durumların economic/API/persistence/UI anlamını ver:

```text
VALID, INVALID_INPUT, UNSUPPORTED, AMBIGUOUS, INDETERMINATE,
CORRUPT, STALE, CONFLICT, UNKNOWN, OPEN_AT_END,
LOCAL_CODE_REQUIRED, BLOCKED
```

## 11. P1.05/P1.06

Realized/unrealized/equity/fee/funding/ROI/drawdown ayrımı; incomplete summary; dataset/config/model/kernel identity; seed; immutable persistence; save/reopen/reproduce/compare; export/audit; result hash ve deterministic replay araştırılmalıdır.

## 12. P1.07 — Derin araştırma zorunlu

### 12.1 Order lifecycle

`OPEN`, `PARTIALLY_FILLED`, `FILLED`, `CANCELED`, `UNKNOWN`, `OPEN_AT_END`, `INDETERMINATE`; original/cumulative/leaves/terminal remainder; full fill-final coverage ayrımı; anchor owner; pending BASE/SAFETY/EXIT; adapter/core authority.

### 12.2 Reserve/commitment

Asset, unit, acquisition/reduction/release owner, INTENT/ACTIVE/FILL timing, candidate/equality etkisi, partial fill, fee asset, rounding, cancel/expiry/EOF, ambiguity, duplicate/late, crash/retry, `NONE` versus numeric zero ve initial-margin ayrımını cevapla.

### 12.3 Historical OHLCV

Placement bar, equality touch, strict penetration, gap/open fill, fixed slice, exact remainder, same-bar ambiguity, committed prefix, EOF ve limit/stop/market authority.

### 12.4 Zorunlu testler

Pending no-fill, equality, strict candidate, rejected candidate, partial fill, full-no-final, full-valid-final, partial BASE blocks SAFETY, explicit cancel, EOF, ambiguous prefix, known duplicate, conflicting duplicate, late fill, crash/retry, deterministic replay, legacy isolation ve NONE/explicit reserve karşılaştırması.

## 13. P1.08–P1.11

Multi-deal start/pause/stop/finish/copy/cooldown/restart/config revision; BASE/QUOTE/balance-percent sizing, ladder/reinvest/budget/rounding; multi-TP/SL/trailing/breakeven trigger-execution ayrımı; shared account ownership/reservation/concurrency/double counting/replay araştırılmalıdır.

## 14. P1.12 — Derin futures araştırması

Spot inventory ile futures position ayrımı; linear long/short; contract size; settlement; mark/index/last/trigger price; funding; trading/funding/liquidation fee; wallet/margin/available balance; position/order margin; initial/maintenance margin; isolated/cross; leverage; realized/unrealized PnL; margin call; liquidation; partial liquidation; bankruptcy/negative balance.

Her venue-specific formül için kaynak, sürüm, asset/unit, rounding ve bağımsız oracle ver. Venue kaynağı yoksa liquidation veya margin formülünü `DEFER/BLOCKED` bırak.

Long/short PnL, funding, fee, isolated exhaustion, cross loss, mark/index divergence, maintenance boundary, liquidation, partial close ve replay testleri zorunludur.

## 15. P1.13–P1.14

Arithmetic/geometric grid, inventory, grid profit/equity, trailing/infinity/reverse, leveraged grid, partial fill, level replacement; rebalancing target/threshold/time, signal event-time/dedup/warmup/closed-bar, template version/hash/import/export/authority araştırılmalıdır.

## 16. P1.15 — Derin hedge/cross/two-leg araştırması

Net versus hedge position; long/short ayrı state; opposite-side order; reduce-only/close-position; position/deal owner; wallet/margin/available/position/order margin; maintenance/bankruptcy; one-leg-filled, other-leg-unfilled, sequencing, timeout, partial hedge, spread, funding/borrow/transfer, one-leg liquidation, atomicity ve recovery.

İki bacak için ayrı state-machine, formül ve bağımsız oracle ver. Spot/futures varsayımlarını otomatik birleştirme.

## 17. P1.16 — Derin walk-forward/OOS/stress araştırması

Train/validation/test, walk-forward window, purging, embargo, indicator warmup leakage, parameter-selection leakage, dataset adjustment leakage, seed, deterministic replay, failed/dropped/invalid run, benchmark ve multiple testing araştırılmalıdır.

Şu OOS kuralını kaynak ve testle doğrula:

```text
OOS sonucu görüldükten sonra tuning yapılırsa aynı OOS untouched evaluation değildir.
Yeni tuning için yeni untouched holdout gerekir.
```

Spread, slippage, latency, volume participation, partial fill, OHLC ambiguity, missing/gap ve best/worst stress sonucu ayrı modellenecektir.

## 18. P1.17–P1.20

Public read-only feed, stale/gap/reconnect, clock/order timing, simulated adapter, failure recovery; offline explanation/notification/template; 320px, keyboard, screen reader, contrast, empty/loading/error, `INDETERMINATE`, `CORRUPT`, `OPEN_AT_END`, theme ve Windows offline install; final P1 data/math/core/persistence/security/UI/E2E/independent-review gate’leri araştırılmalıdır.

Yeni UI/görsel karar gerekiyorsa bunu ayrıca kaynaklı UI/UX kanıtı olarak ver; ekonomik authority’yi UI’ya taşıma.

## 19. Formula standardı

Her formül için şu tabloyu doldur:

| Formula ID | Formula | Variables | Asset/unit | Sign | Precision | Rounding owner | Input state | Output state | Failure | Venue | Independent oracle | Sources |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

Float epsilon, unknown→0, asset conversion olmadan scalar toplama ve venue-specific formülü universal kabul etme yaklaşımlarını ayrıca değerlendir.

## 20. Test/oracle standardı

Her kritik iddia için fixture, event sırası, expected state, negative assertion, bağımsız ikinci kontrol ve test status ver.

Oracle production reducer/helper/formula utility’sini import edemez.

Değerlendirilecek metamorphic/property testleri:

- known duplicate sonucu değiştirmemeli,
- replay sonucu değiştirmemeli,
- exact remainder korunmalı,
- ambiguity suffix’i prefix’i geri almamalı,
- export/import state’i değiştirmemeli,
- venue-specific formül başka venue’ye otomatik taşınmamalı.

Partial fill parçalama için fee/rounding policy bilinmiyorsa eşdeğerlik iddiasını `CONDITIONAL` bırak.

## 21. Local code request standardı

External kaynak local implementation’ı cevaplayamazsa şu kaydı oluştur:

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

Yalnız State/Order/Position/reserve schema, reducer branch’i, initial-margin call chain, pending blocker, adapter→FILL zinciri, anchor/SAFETY zinciri, dedupe/late testleri, fixture veya public DTO/legacy testleri istenebilir.

`LOCAL_CODE_REQUIRED` demek araştırmanın tamamlandığı anlamına gelmez; dış kaynakla çözülen bölüm yine tamamlanmalı, local blokaj ayrı kayda alınmalıdır.

## 22. Zorunlu teslim klasörü

```text
P1_KRITIK_ARASTIRMA_FINAL/
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

## 23. Master karar özeti

`01_MASTER_DECISION_SUMMARY.md` içinde 15 ana fazın her biri için şu tabloyu doldur:

| Faz | Tam araştırıldı mı? | Karar | Implementation-ready? | Kritik açık | Kaynak | Sonraki gate |
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

## 24. Final completeness gate

Final klasörde aşağıdaki her satıra `PASS` veya `FAIL` yaz:

| Gate | Sonuç |
|---|---|
| 15 ana faz raporu mevcut |  |
| Her raporda 17 zorunlu bölüm mevcut |  |
| P1.07 derin araştırması tamam |  |
| P1.12 derin araştırması tamam |  |
| P1.15 derin araştırması tamam |  |
| P1.16 derin araştırması tamam |  |
| Her kritik iddianın kaynak/status/kararı mevcut |  |
| Her formülün unit/precision/rounding/oracle bilgisi mevcut |  |
| Kaynak sürümü ve çatışmaları kayıtlı |  |
| Event-time taxonomy mevcut |  |
| Execution identity mevcut |  |
| Atomic transition mevcut |  |
| Canonical serialization/hash mevcut |  |
| Numeric boundary mevcut |  |
| Independent oracle production’dan bağımsız |  |
| Positive/negative/property testleri mevcut |  |
| OOS freeze kuralı mevcut |  |
| Data-integrity ve security gate’leri mevcut |  |
| Previous claim recheck mevcut |  |
| Local code request’leri dar ve güvenli |  |
| Evidence manifest mevcut |  |
| MANIFEST ve SHA-256 mevcut |  |
| Eksik konular BLOCKED/NOT_VERIFIED olarak açık |  |

Bir satır `FAIL` ise `RESEARCH_COMPLETE: YES` yazma.

## 25. Son teslim mesajı

Son mesajda şu alanların tamamını doldur:

```text
RESEARCH_COMPLETE: YES | NO
PACKAGE_ROOT:
TOTAL_REQUIRED_PHASES: 15
COMPLETED_PHASE_REPORTS:
MISSING_PHASE_REPORTS:
VERIFIED_CLAIMS:
CONDITIONAL_CLAIMS:
UNSUPPORTED_CLAIMS:
NOT_VERIFIED_CLAIMS:
BLOCKED_CLAIMS:
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

Hiçbir alanı boş bırakma. Bilinmiyorsa `UNKNOWN` yaz ve ilgili dosyada nedenini açıkla.

## 26. Uygulama sırasında yeni kanıt kapısı

Bu araştırma tesliminden sonra implementation sırasında ekonomik sonuç, authority, exact formula, asset/unit, persistence/replay, venue-specific davranış, güvenlik veya yeni UI anlamı değişiyorsa sessiz varsayım yapma:

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

Yeni kanıt kapısı açılması, mevcut master araştırmanın eksik teslim edildiği anlamına gelmez; yalnız implementation sırasında ortaya çıkan yeni local belirsizliği gösterir.

## 27. Son bağlayıcı talimat

Bu promptu baştan sona uygula. Önceki P1.07 paketini master araştırma olarak kabul etme. P1.05/P1.06’dan P1.20’ye kadar bütün zorunlu raporları üret. P1.07, P1.12, P1.15 ve P1.16’yı derinlemesine tamamla. Soruları cevaplamadan listeleme. Kaynaksız iddia üretme. Local code görmeden local implementation sonucu uydurma. Büyük production kodu yazma. Eksik teslimi tamamlanmış gösterme. Araştırma klasörünü, manifestini ve checksum’ını eksiksiz teslim et.
