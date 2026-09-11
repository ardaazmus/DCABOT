# P1.19.f — Exact Token/Palette ve Safe Detailed-View Implementation Gate

## Sonuç

```text
PHASE = P1.19.f
GATE = DEFERRED / NO-GO / LOCAL_PASS
LIGHT_THEME = DEFER
DETAILED_VIEW = SIMPLIFY_TO_EXISTING_DISCLOSURES
THEME_PERSISTENCE = DEFER
BORDER_CONTRAST_FOLLOW_UP = REQUIRED
BACKEND_CONTRACT_CHANGE = NO
ECONOMIC_AUTHORITY_CHANGE = NO
FRONTEND_CALCULATION_ALLOWED = NO
APP_CODE_CHANGED = NO
PRODUCTION_READINESS = NO
```

Bu kapı, P1.19.e’de bulunan gerçek checkout kanıtı üzerinden yürütüldü. Uygulamaya yeni light theme, theme toggle, persistence veya ayrı expert-mode state eklenmedi. Mevcut `details/summary` teknik ayrıntı açılımları, güvenli detailed-view davranışının zaten bulunan en küçük karşılığı olarak kabul edildi; aynı davranışı yeni bir görünüm modu adıyla çoğaltmak bu fazda reddedildi.

## Gerçek kanıt özeti

| Alan | Kanıt | Sonuç |
|---|---|---|
| CSS tokenları | `frontend/src/styles.css:1-6` | 7 custom property; 5 renk tokenı, kapsam kısmi |
| CSS renk kapsamı | P1.19.e bağımsız inventory | 142 normalized hex key, 352 literal occurrence; ayrıca `rgba`/gradient yüzeyler var |
| Focus | `frontend/src/styles.css:5-6`, P1.19.d | Ortak `:focus-visible`; local 18/18 focus durağı PASS |
| Responsive | P1.19.d | 320/390/768/1024/1280px yatay taşma yok |
| Backend contract | `src/dcabot/server/api.py:449-482,549-567` | Strict read-only explanations ve historical response doğrulandı |
| Frontend type | `frontend/src/datasetCatalog.ts:64-177` | Economic summary/status/explanation alanları type edilmiş |
| Mevcut disclosure | `frontend/src/ExplanationSection.tsx:28-36`, `:68-78` | Raw backend technical detail native disclosure ile gösteriliyor |
| NVDA/JAWS ve gerçek HCM | `evidence/P1.19.d/SONUC.md` | NOT_RUN |

## Exact token/palette kararı

### Kabul edilen mevcut temel

```text
--ui-bg-body       #09121c
--ui-bg-sidebar   #0b1621
--ui-text         #e6edf5
--ui-border       #223241
--ui-focus-ring   #42a5ff
--ui-focus-ring-width  2px
--ui-focus-ring-offset 3px
```

Bu değerler mevcut koyu görünümün gerçek değerleridir. Bunlar light palette değildir ve light theme için doğrudan yeniden kullanılmayacaktır.

### Ölçülmüş kontrast kararı

P1.19.e oracle’ındaki 12 seçilmiş gerçek çiftin 11’i geçti; `#223241` / `#09121c` border/body çifti `1.44:1` ile 3:1 UI eşiğini geçmedi. Tam composited gradient/alpha matrisi mevcut değildir.

Kanıt: [contrast_audit.csv](contrast_audit.csv).

Karar:

- Border tokenı otomatik olarak “uygun” ilan edilmez.
- Light palette tasarlanırken bu border rolü için ayrı, ölçülmüş bir değer zorunludur.
- Mevcut dark border değeri bu kapıda sessizce değiştirilmez; görsel regression ve component rolü birlikte kontrol edilmelidir.

### Light theme neden açılmadı?

1. Tüm gerçek renk kullanımları semantic role’lere eşlenmiş değildir.
2. Alfa ve gradient yüzeylerde basit hex/hex karşılaştırması yeterli değildir.
3. Light palette için exact foreground/background matrisi ve state kombinasyonları yoktur.
4. Theme state’in `config_hash`, dataset, result ve economic response’dan ayrıldığı bir runtime test yoktur.
5. NVDA/JAWS ve gerçek Windows High Contrast Mode çalıştırılmamıştır.

Bu eksikler uygulama sırasında varsayımla doldurulamaz. `localStorage`, `prefers-color-scheme` veya theme toggle bu nedenle eklenmedi.

## Safe detailed-view kararı

Backend response’ta ayrı `simple`, `expert` veya `view_mode` alanı bulunmuyor. Ancak mevcut API zaten şu güvenli alanları sağlıyor:

- execution/status/application code
- dataset, profile, assumptions
- backend summary/final economic summary
- actions
- ambiguity
- bounded `ReadOnlyExplanation` (`code`, `severity`, `title`, `message`, `source`, `context`)

Mevcut `ExplanationSection` severity gruplarını backend sırasını grup içinde koruyarak gösteriyor ve `details/summary` ile teknik ayrıntıyı açıyor. Bu davranış yeterli bir progressive disclosure temelidir.

### Kabul edilen sınır

`DETAILED_VIEW = SIMPLIFY_TO_EXISTING_DISCLOSURES`

Yeni expert-mode toggle eklenmeyecek. Gerekirse ileride aynı response üzerinde yalnız şu sunum işlemleri yapılabilir:

- teknik ayrıntıları native disclosure ile açıp kapatma;
- backend’in verdiği alanları aynen gösterme;
- ekonomik alanları yeniden hesaplamama;
- raw `context` içinden PnL, fee, balance, reserve, risk veya öneri çıkarmama.

### Reddedilen sınır

- Yeni backend `view_mode` contract’ı: `NO-GO`.
- Ayrı expert economic model/config: P1.19.f kapsamı dışında ve `NO-GO`.
- Raw context’i “uzman analiz” olarak yorumlamak: `NO-GO`.
- Frontend’de toplam, PnL, fee, reserve veya risk hesaplamak: kalıcı `NO-GO`.
- Mevcut disclosure’ları gizleyip audit alanlarını kaybetmek: `NO-GO`.

## Karşı örnek ve fail-closed sonucu

| Karşı örnek | Gözlenen risk | Karar |
|---|---|---|
| `--ui-border` body üzerinde 1.44:1 | Bazı sınır rolleri görünürlük eşiğini geçmiyor | Light palette/token düzeltmesinde zorunlu follow-up |
| 142 hex key + rgba/gradient | Tüm palette için tek bir varsayılan mapping güvenilir değil | Tam token audit olmadan light theme yok |
| Backend’de view-mode yok | Frontend mode anlamı uydurabilir | Yeni mode contract’ı yok; mevcut disclosure korunur |
| `context` ekonomik yoruma açık | UI yanlış authority üretebilir | Raw context’ten türetme NO-GO |
| NVDA/JAWS/HCM NOT_RUN | Gerçek AT davranışı kanıtlanmamış | Production readiness NO |

## Kabul/test matrisi

| Kontrol | Sonuç |
|---|---|
| Local source/contract inspection | PASS |
| Exact current token inventory | PASS; kapsam kısmi olarak kaydedildi |
| Selected contrast oracle | PASS; 11 PASS / 1 FAIL |
| Existing responsive/focus runtime evidence | PASS; P1.19.d |
| Existing native detailed disclosure | PASS |
| Light theme implementation | NOT_STARTED / DEFERRED |
| Expert-mode implementation | NOT_STARTED / SIMPLIFIED_TO_EXISTING_DISCLOSURES |
| Theme persistence identity test | NOT_RUN |
| NVDA/JAWS runtime | NOT_RUN |
| Real Windows HCM | NOT_RUN |
| Python regression | PASS — `359/359` carried from P1.19.e validation |
| Frontend build | PASS — Vite 35 modules carried from P1.19.e validation |

## Implementation gate

```text
LIGHT_THEME_IMPLEMENTATION = DEFERRED
EXPERT_MODE_IMPLEMENTATION = NO-GO_FOR_NEW_MODE
EXISTING_DISCLOSURE = ACCEPTED_AS_MINIMUM_DETAIL_VIEW
BORDER_ROLE_REVIEW = REQUIRED_BEFORE_LIGHT_THEME
FULL_WCAG_CONFORMANCE = NOT_CLAIMED
```

P1.19.f’nin amacı yeni görsel davranış eklemek değil, hangi davranışın güvenli biçimde eklenemeyeceğini kesinleştirmektir. Bu amaç tamamlandı. App, backend, API, persistence ve ekonomik hesap kodu değişmedi.

## Sonraki gerekli karar

Light theme’in açılması için tek anlamlı sonraki adım ürün/onay düzeyinde exact palette ve default/persistence kararını vermektir. Bu karar gelmeden yeni renk değerleri veya theme state yazılmayacaktır. Detailed view için ayrıca yeni backend contract gerekmiyor; mevcut disclosure yaklaşımı yeterli başlangıçtır.
