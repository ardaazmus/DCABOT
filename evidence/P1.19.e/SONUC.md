# P1.19.e — Light Theme ve Uzman Görünüm Karar Araştırması

## Sonuç

```text
PHASE = P1.19.e
GATE = COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED
LOCAL_RESULT = LOCAL_PASS
SUPPLIED_REPORT_STATUS = REJECTED_AS_LOCAL_EVIDENCE
LIGHT_THEME_DECISION = DEFER
EXPERT_VIEW_DECISION = DEFER
CONTRAST_ORACLE = PARTIAL_LOCAL_PASS
SCREEN_READER_RUNTIME = NOT_RUN
WINDOWS_HCM_RUNTIME = NOT_RUN
PRODUCTION_READINESS = NO
BACKEND_CONTRACT_CHANGE = NO
ECONOMIC_AUTHORITY_CHANGE = NO
FRONTEND_CALCULATION_ALLOWED = NO
```

Kullanıcı tarafından sağlanan rapor karar niyeti bakımından değerlendirildi; fakat yerel kanıt olarak doğrudan kabul edilmedi. Rapor, `package.json`, component dosyaları, backend response modeli ve `styles.css` okunamadığını açıkça belirttiği halde bu dosyalar hakkında kesin envanter ve renk iddiaları kuruyor. Güncel checkout üzerinde gerçek kaynaklar okunarak rapor yeniden denetlendi.

Bu mikro fazda uygulamaya light theme veya yeni uzman görünüm eklenmedi. Kararların ertelenmesi artık “kod okunamadı” gerekçesine değil, doğrulanmış tasarım/kontrat ve yardımcı teknoloji kanıtlarının henüz tamamlanmamış olmasına dayanır.

## Denetlenen gerçek kapsam

| Alan | Yerel kanıt | Sonuç |
|---|---|---|
| Frontend stack | `frontend/package.json:1-23` | React `19.1.1`, Vite `7.3.6`, TypeScript `5.9.2`; rapordaki React 18/Vite 5 beklentisi doğru değil |
| Entry point | `frontend/src/main.tsx:1-10` | Gerçek `StrictMode` + `createRoot` akışı okundu |
| Frontend response types | `frontend/src/datasetCatalog.ts:64-177` | `ReadOnlyExplanation`, historical response, economic summary ve status alanları mevcut |
| Explanation UI | `frontend/src/ExplanationSection.tsx:8-80` | `ERROR → WARNING → INFO`, grup içi backend sırası, native `details/summary`, `aria-controls` doğrulandı |
| Backend response contract | `src/dcabot/server/api.py:422-482,549-567` | Strict response modelleri ve `explanations` alanı doğrulandı |
| Read-only authority | `src/dcabot/application/read_only_explanations.py:1-12,143-177` | Bounded, kural tabanlı açıklama; yeniden ekonomik hesap veya action üretimi yok |
| CSS token/focus | `frontend/src/styles.css:1-6` | 7 CSS custom property; 5’i renk tokenı; ortak `:focus-visible` mevcut |
| Responsive/runtime | `evidence/P1.19.d/SONUC.md` | 320/390/768/1024/1280 taşmama ve 18 focus durağı local CDP ile PASS |

## Rapor ile yerel gerçek arasındaki kritik farklar

| Sağlanan rapordaki iddia | Yerel bulgu | Değerlendirme |
|---|---|---|
| Dosyalar okunamadı; package bilgisi varsayıldı | Dosyalar okunabilir ve gerçek içerik denetlendi | `REJECTED_AS_LOCAL_EVIDENCE` |
| React 18 / Vite 5 bekleniyor | React 19.1.1 / Vite 7.3.6 | Yanlış/varsayımsal |
| CSS token sistemi yok | 7 custom property mevcut; ancak kapsam kısmi | “Yok” iddiası yanlış; `TOKEN_STATUS=PARTIAL` |
| Gerçek backend response schema yok | Pydantic modelleri ve frontend type’ları mevcut | `BACKEND_CONTRACT=VERIFIED` |
| Responsive ve focus tamamen test edilmedi | P1.19.d local CDP evidence ile temel smoke PASS | Runtime kanıtı kısmen zaten var |
| Gerçek renkler okunamadı; palette varsayıldı | Güncel CSS literal’ları doğrudan inventory edildi | Varsayımsal palette bölümü kullanılmadı |
| Light theme kararı için yalnız genel eksikler var | Ürün dokümanında hedef var; exact palette/token sözleşmesi yok | Karar `DEFER`, gerekçe düzeltildi |

Raporun “light theme” ve “uzman görünüm” önerileri, gerçek kod kanıtı olmadan yazıldığı için implementation packet olarak kullanılamaz. Raporun ekonomik authority sınırı ve frontend hesap yasağı ise mevcut proje kurallarıyla uyumludur ve korunmuştur.

## Gerçek CSS inventory ve kontrast oracle

Bağımsız, network-free oracle:

Not (2026-09-20): `.cluster/` klasörü temizlendi; aşağıki script yolu artık diskte yok, tarihsel kayıttır.

```text
Oracle: .cluster/P1.19.e-audit/contrast_oracle.mjs
CSS: frontend/src/styles.css
CSS custom properties: 7 total
Color custom properties: 5
Normalized hex literal keys: 142
Hex literal occurrences: 352
```

Kullanılan gerçek tokenlar:

```text
--ui-bg-body       #09121c
--ui-bg-sidebar   #0b1621
--ui-text         #e6edf5
--ui-border       #223241
--ui-focus-ring   #42a5ff
```

`--ui-focus-ring-width` ve `--ui-focus-ring-offset` de yapısal token olarak mevcut; bunlar renk sayısına dahil edilmedi. CSS’in önemli bir bölümü hâlâ component-specific hex ve `rgba` değerleri kullanıyor. Bu nedenle mevcut durum tam semantic token sistemi değil, kısmi token sistemidir.

### Ölçülen çiftler

| Çift | Oran | Eşik | Sonuç |
|---|---:|---:|---|
| `#e6edf5` / `#09121c` primary text | 15.96:1 | 4.5:1 | PASS |
| `#8294a5` / `#09121c` muted helper | 6.03:1 | 4.5:1 | PASS |
| `#ffffff` / `#1373df` primary button | 4.62:1 | 4.5:1 | PASS |
| `#42a5ff` / `#09121c` focus ring | 7.23:1 | 3:1 | PASS |
| `#42a5ff` / `#0b1621` focus ring/sidebar | 7.00:1 | 3:1 | PASS |
| `#f5c55b` / `#09121c` warning | 11.68:1 | 4.5:1 | PASS |
| `#ffaaa5` / `#09121c` error | 10.36:1 | 4.5:1 | PASS |
| `#45c793` / `#09121c` success | 8.83:1 | 4.5:1 | PASS |
| `#eef4fa` / `#0b1722` input text | 16.34:1 | 4.5:1 | PASS |
| `#dce7f0` / `#10202d` table heading | 13.21:1 | 4.5:1 | PASS |
| `#cbd8e4` / `#10202d` table text | 11.43:1 | 4.5:1 | PASS |
| `#223241` / `#09121c` border/body | 1.44:1 | 3:1 | FAIL |

`FAIL` olan border çifti, tüm sınırların otomatik olarak erişilemez olduğu anlamına gelmez; ancak sınır anlam taşıyan UI component’lerinde 3:1 eşiği bakımından açık risktir. Panel gradientleri ve `rgba` overlay’leri gerçek composited arka plan olduğundan bu tablo tam renk matrisi değildir. Sonuç bu nedenle `CONTRAST_ORACLE=PARTIAL_LOCAL_PASS`; “tüm UI WCAG geçti” iddiası kurulamaz.

## Backend contract ve uzman görünüm sınırı

Gerçek backend modeli `ReadOnlyExplanationResponse` için `extra="forbid"`, `strict=True`, `frozen=True`; `severity` yalnız `INFO`, `WARNING`, `ERROR`; `context` ise `dict[str, int | str]` ile sınırlıdır (`src/dcabot/server/api.py:449-457`). Historical response economic summary, assumptions, actions, ambiguity ve explanations alanlarını taşır (`:468-482`). Fixed-slice response ayrıca action/marker authority alanlarını taşır (`:549-567`).

Bu kanıt şunları destekler:

- UI mevcut backend alanlarını okuyabilir ve gösterebilir.
- UI PnL, fee, balance, reserve, risk veya başka ekonomik değer türetemez.
- `NOT_MODELED`, `NOT_AVAILABLE`, `OPEN_AT_END` ve `INDETERMINATE` değerleri sıfırla veya başarıyla değiştirilemez.
- Mevcut açıklama component’i severity’yi yeniden icat etmiyor; backend severity değerlerini sunum gruplarında kullanıyor.

Bu kanıt tek başına “expert view” adında yeni bir ürün modu tanımlamaya yetmez. Mevcut response’ta ayrı simple/expert contract veya `view_mode` alanı yoktur. En güvenli gelecek kapsamı, aynı response üzerinde yalnız sunum düzeyinde progressive disclosure olabilir; raw `context` üzerinden ekonomik hesap/yorum üretilmesi `NO-GO` olarak kalır.

## Erişilebilirlik ve responsive kanıt durumu

P1.19.d’den devralınan gerçek local kanıt:

- `main=1`, `nav=1`, `aside=2`, `section=7`, `header=1`; accessibility tree 575 düğüm.
- Etkin controlsız isimli kontrol bulunmadı; toplam 18 focus durağı.
- 320, 390, 768, 1024 ve 1280 genişliklerinde `scrollWidth == clientWidth`.
- Tüm focus duraklarında görünür `:focus-visible` ring; örnek `rgb(66, 165, 255) solid 2px`.
- Native `details/summary` ve browser forced-colors emülasyonu PASS.

Bunlar gerçek DOM/CDP kanıtıdır; NVDA/JAWS’ın sesli duyurusunu veya gerçek Windows High Contrast Mode servis davranışını kanıtlamaz.

```text
SCREEN_READER_RUNTIME = NOT_RUN
WINDOWS_HCM_RUNTIME = NOT_RUN
FULL_WCAG_CONFORMANCE = NOT_CLAIMED
```

## Karar

### Light theme — `DEFER`

Light/dark hedefi ürün dokümanında bulunuyor; ancak uygulama için şu kanıtlar eksik:

1. Mevcut 142 normalized hex key ve alpha/gradient yüzeyleri için role-based semantic token eşlemesi.
2. Light palette’nin tüm gerçek foreground/background ve state çiftleri için contrast matrisi.
3. Theme default, toggle ve persistence kararının economic identity’den ayrı olduğunun test kanıtı.
4. Light theme’in keyboard, forced-colors ve ekran okuyucu davranışının runtime doğrulaması.

Bu koşullar kapanmadan light palette, `localStorage` theme state’i veya yeni toggle eklenmeyecek.

### Uzman görünüm — `DEFER`

Backend contract doğrulanmış olsa da simple/expert alan matrisi ve ürün tanımı mevcut response’ta ayrı bir sözleşme olarak yoktur. Yeni mode eklemek yerine önce aynı response için açık bir field mapping hazırlanmalıdır. Raw technical context’in ekonomik yoruma dönüştürülmesi ve frontend hesaplaması kalıcı `NO-GO` sınırıdır.

## Minimum sonraki kanıt

| Öncelik | Gerekli çıktı | Kapanış koşulu |
|---|---|---|
| P0 | Semantic token + light palette matrisi | Her rol için gerçek hex, kullanım alanı, contrast sonucu ve fail düzeltmesi |
| P0 | Safe simple/detail field mapping | Aynı backend response; ekonomik türetme yok; raw context ekonomik amaçla gösterilmiyor |
| P1 | Theme state policy | Default/toggle/persistence; `config_hash`, dataset ve response değişmiyor |
| P1 | Runtime AT/HCM | NVDA veya JAWS oturum notu ve gerçek Windows HCM kontrolü |
| P1 | Light/dark responsive matrix | 320/390/768/1024/1280, yatay taşma ve focus görünürlüğü |

## QA kaydı

| Kontrol | Sonuç |
|---|---|
| Local source inspection | PASS |
| Independent contrast oracle | PASS; 11 key pair PASS, 1 border pair FAIL |
| Existing P1.19.d responsive/focus evidence | PASS |
| Existing P1.19.d frontend build | PASS — 35 module |
| Existing P1.19.d Python regression | PASS — `359/359` |
| Existing P1.19.d compile/workspace | PASS |
| NVDA/JAWS speech runtime | NOT_RUN |
| Real Windows HCM | NOT_RUN |
| App code changed in P1.19.e | NO |

## Sonraki kapı

P1.19.e araştırma kapısı `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED` olarak kapanmıştır. Light theme ve uzman görünüm implementasyonu açılmamıştır. Sıradaki tek karar kapısı, exact token/palette ve safe presentation field mapping’i aynı anda taşıyan `P1.19.f` implementation gate olmalıdır; bu kanıtlar gelmeden uygulama koduna geçilmez.
