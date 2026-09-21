# Çok-Stratejili Trading Dashboard UI/UX Araştırması

**Araştırma tarihi:** 21 Eylül 2026  
**Kapsam:** Yalnızca bilgi mimarisi, navigasyon, config-form UX, gerçek zamanlı dashboard sunumu, görsel tema mimarisi ve frontend render performansı. Belirli bir ürün/repository varsayılmamıştır.

## 1. Executive summary

Kaynakların ortak yönü, 10+ strateji ailesi bulunan bir uygulamanın **“her özelliği ayrı menü/sekmeye koyan” düz bir mimariyle ölçeklenmemesi** yönünde.

En sağlam model:

> **Global top bar + kalıcı/collapsible sol navigasyon + sayfa-içi sınırlı tabs + aktif bağlam header'ı + opsiyonel command palette**

Atlassian, top navigation'ı global/cross-app işlemlerle sınırlar ve ürün içi navigasyonu side-nav'a taşır. Carbon ise beşten fazla ikincil navigasyon öğesi veya sık bölüm değiştirme varsa left panel kullanılmasını önerir.

Strateji türlerinin — DCA, spot grid, futures grid, hedge vb. — her birini ana navigasyona koymak yerine bunları **“Strategy / Automation” domain'i altında alt tipler** olarak ele almak daha ölçeklenebilir. Bu spesifik gruplama kaynaklardan doğrudan çıkmıyor; kaynak ilkelerinin trading domain'ine uygulanmış hali olduğu için aşağıdaki sınıflandırmada **CONDITIONAL**.

Ayrıca:

- **6+ yatay tab kullanmamak** güçlü biçimde destekleniyor. Carbon çoğu durumda maksimum altı tab öneriyor; Fluent tabs'i yalnız küçük ve yakın ilişkili içerik kümeleri için uygun görüyor.
- **Command palette ana navigasyonun yerine geçmemeli.** GitHub bunu hızlı navigasyon/komut katmanı olarak kullanıyor; ancak görünür IA'nın yerine kullanılmasına dair resmi bir kanıt yok.
- **Progressive disclosure kullanmak doğru**, fakat uygulamayı tamamen “Simple Mode / Expert Mode” şeklinde iki ayrı ürüne bölmek için güçlü kanıt yok. NN/g gelişmiş ve seyrek kullanılan seçeneklerin sonradan açılmasını açıkça öneriyor.
- Yeni ve karmaşık yapılandırma **wizard**, mevcut botu hızlı düzenleme ise **sectioned single-page form** olmalı. Wizard her config ekranında kullanılmamalı.
- Çoklu bot izleme için **tablo ana çalışma yüzeyi**, kartlar ise genel durum/özet görünümü olarak daha uygun. Carbon data-table'ın tüm kaynakları görüntüleme, sıralama, filtreleme ve satır bazlı işlem için uygun olduğunu açıkça belirtiyor.
- Açık/koyu tema **semantic design tokens** üzerinden yönetilmeli; component içinde hard-coded renk kullanımı istisna olmalı. Atlassian ve Carbon bunu doğrudan destekliyor.
- Büyük dashboard performansında **virtualization + bounded DOM + lazy/code splitting + ölçülmüş selective memoization + granular subscriptions** temel teknikler.

---

# 2. Önerilen bilgi mimarisi

## Temel prensip

IA'yı **strateji isimlerine göre değil, kullanıcının yaptığı işe göre** organize etmek daha sağlamdır.

Önerilen hiyerarşi:

```text
GLOBAL TOP BAR
├─ Workspace / Account switcher
├─ Global Search / Command Palette
├─ Paper / Live environment indicator
├─ Notifications
└─ Profile / Global settings


PRIMARY SIDE NAV
├─ Overview
│
├─ Automation
│   ├─ Bots / Sessions
│   ├─ Strategies
│   └─ Templates
│
├─ Portfolio
│   └─ Rebalancing
│
├─ Monitor
│   ├─ Positions
│   ├─ Orders
│   └─ Event Stream
│
├─ Simulation
│   ├─ Paper Trading
│   └─ Replay / Historical Timeline
│
├─ Alerts
│
├─ Audit & Export
│
└─ Settings
```

DCA, spot grid, futures grid, hedge, signal-triggered vb.:

```text
Automation
   ↓
Strategies
   ↓
Create strategy
   ↓
[DCA | Spot Grid | Futures Grid | Hedge | Signal | ...]
```

şeklinde bir **type selection** olur.

Böylece her yeni strateji ailesi ana sidebar'a yeni bir entry eklemez.

**Durum: CONDITIONAL.** Side-nav ve grouping ilkesi güçlü kaynak desteğine sahip; trading domain'ine uygulanmış grup adları tasarım kararıdır.

Atlassian'ın ayrımı oldukça nettir:

> “Top nav is for global, cross-app actions only.”

Ürün içindeki bölümler/projeler/space'ler ise side-nav'a gider.

- [Atlassian Navigation System](https://atlassian.design/components/navigation-system/migration-guide)
- [Carbon UI Shell – Left Panel](https://carbondesignsystem.com/components/UI-shell-left-panel/usage/)

---

# 3. Navigasyon hiyerarşisi

## Desktop

Önerim:

**Top bar**  
→ yalnız global kapsam.

**Sol sidebar**  
→ temel ürün modülleri.

**Page header**  
→ aktif çalışma bağlamı.

**Tabs**  
→ yalnız aynı entity'nin alt görünümleri.

Örneğin:

```text
Bots / Running Bots / ETH Grid #04

ETH Grid #04
Futures Grid · ETH/USDT · Running · Paper

[Overview] [Configuration] [Orders] [Positions] [Events]
```

Bu durumda `Overview / Configuration / Orders / Positions / Events`, aynı botun farklı görünümleri oldukları için tab kullanımına uygundur.

Buna karşılık:

```text
DCA
Spot Grid
Futures Grid
Hedge
Rebalancing
Signals
Paper
Replay
Alerts
Audit
...
```

şeklinde yatay tabs yanlış seviyedir.

Carbon:

> “In most scenarios, you should use no more than six tabs.”

Daha fazlasında başka navigasyon desenleri, özellikle side-nav öneriliyor.

- [Carbon Tabs Usage](https://v10.carbondesignsystem.com/components/tabs/usage/)
- [Fluent 2 Tablist](https://fluent2.microsoft.design/components/web/react/core/tablist/usage)

**Durum: CONFIRMED.**

---

# 4. Aktif bot/strateji bağlamı

Burada breadcrumb tek başına yeterli değil.

Önerilen üçlü:

```text
Breadcrumb
Bots / Futures Grid / ETH Grid #04

Context header
ETH Grid #04
ETH/USDT · Futures Grid · Paper · Running

Local navigation
Overview | Config | Orders | Positions | Events
```

NN/g breadcrumbs'ın wayfinding sağladığını ve kullanıcının IA içindeki yerini göstermesini öneriyor. Carbon da >2 seviyeli hiyerarşilerde breadcrumb'ı öneriyor.

- [NN/g – Breadcrumbs: 11 Design Guidelines](https://www.nngroup.com/articles/breadcrumbs/)

**Breadcrumb:** CONFIRMED.  
**Her zaman görünür entity/context header:** CONDITIONAL.

Kaynaklar “trading bot header” diye özel bir desen tanımlamıyor. Fakat karmaşık uygulamalardaki wayfinding ilkelerinin mantıklı uygulaması bu.

---

# 5. Command palette

Eklenmesini öneririm, fakat **navigation replacement olarak değil, accelerator olarak**.

Örneğin:

```text
Ctrl / Cmd + K

> eth grid

Go to: ETH Grid #04
Open: ETH Grid #04 configuration
Filter bots by ETH
Go to: Strategies → Grid
```

veya:

```text
> replay
Open Historical Replay
```

GitHub'ın command palette'i uygulamanın herhangi bir yerinden navigation, search ve commands sağlıyor.

- [GitHub Command Palette Documentation](https://docs.github.com/en/get-started/accessibility/github-command-palette)

Ancak arama-first navigasyonun **ana navigasyondan daha iyi olduğuna dair genel bir HCI kanıtı bulunmamaktadır**.

Bu nedenle:

**Sidebar + search + command palette:** CONDITIONAL.  
**Command palette-only IA:** local judgment; önerilmez.

---

# 6. Progressive disclosure: Simple / Expert

Buradaki en önemli karar:

## İki tamamen ayrı ürün modu yapmayın

Şunun yerine:

```text
Order sizing
──────────────
Amount          [ .... ]

Advanced ▸
```

veya:

```text
Grid Settings
─────────────
Price range
Grid count

Advanced settings ▾
  Spacing model
  Trigger condition
  Trailing parameters
  ...
```

NN/g'nin progressive-disclosure prensibi:

> “Initially, show users only a few of the most important options.”

ve gelişmiş/seçrek özellikleri kullanıcı istediğinde açmak.

- [NN/g – Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/)

Karmaşık uygulamalar için NN/g ayrıca staged disclosure öneriyor: ilgili seçenek aktif olduğunda gelişmiş seçenekleri göstermek.

### Dolayısıyla en iyi ayrım

**Field-group / section seviyesinde progressive disclosure.**

Şu modelden kaçının:

```text
○ Beginner mode
● Expert mode
```

ve expert moda geçince ekranın tamamının değişmesi.

Bunun problemi, kullanıcının iki farklı mental model öğrenmesi ve bir seçeneğin hangi modda bulunduğunu hatırlamak zorunda kalmasıdır.

Bu son çıkarım **local judgment**, progressive disclosure prensibinin kendisi ise **CONFIRMED**.

---

# 7. Varsayılan görünümde gizlenmemesi gerekenler

Simple görünümde bile işlemin temel niteliğini değiştiren veya sonuçları doğrudan etkileyen bilgiler secondary disclosure içine gömülmemeli.

UI açısından kalıcı görünür tutulması gereken kategori:

- **Paper / live environment**
- aktif hesap/workspace
- kullanılan market/parite
- strateji türü
- aktif/pause/stopped/error durumu
- tahsis edilen maksimum kaynak/limit
- varsa kaldıraç/margin modu gibi yüksek etkili çalışma modu
- temel loss/stop/kill-switch korumasının açık/kapalı durumu
- kaydetme ile gerçekten çalıştırma/activate arasındaki fark

Bu spesifik alan listesi resmi tasarım sistemlerinde tanımlanmıyor.

Bu nedenle:

**Risk-kritik state'in gizlenmemesi:** CONDITIONAL.  
**Hangi alanların “risk-critical” olduğu:** ürün-domain judgment.

---

# 8. Config-form mimarisi

Tek bir form biçimini her durumda kullanmak yanlış olur.

## A. Yeni strateji/bot oluşturma

**Wizard.**

Örnek:

```text
1. Context
2. Strategy
3. Core Parameters
4. Advanced / Conditions
5. Review
```

NN/g wizard'ı özellikle:

- seyrek yapılan,
- karmaşık,
- adımları birbirine bağlı,
- seçimlere göre dallanan

işlemler için uygun görüyor.

- [NN/g – Wizards: Definition and Design Recommendations](https://www.nngroup.com/articles/wizards/)
- [Carbon Forms Pattern](https://preview.carbondesignsystem.com/building-blocks/core/patterns/forms)

Wizard'ın faydalarından biri, ilgisiz alanları kaldırarak hata olasılığını azaltmasıdır. Carbon da multistep form için alanlar arasında **logical** ve bölümler arasında **linear relationship** olması gerektiğini söylüyor.

**Durum: CONFIRMED, koşullu kullanım.**

---

# 9. Mevcut config'i düzenleme

Burada wizard daha kötü olabilir.

Deneyimli kullanıcı:

> “grid spacing değerini değiştireceğim”

dediğinde 5 adımlı wizard'dan tekrar geçmek istemez.

Bu nedenle existing entity edit ekranı:

```text
Configuration

▾ General
▾ Market & execution
▾ Strategy parameters
▸ Advanced parameters
▸ Notifications

                    ┌─────────────────────┐
                    │ Configuration       │
                    │ preview / summary   │
                    │                     │
                    │ Estimated structure │
                    │ Active constraints  │
                    └─────────────────────┘
```

şeklinde olmalı.

Accordion burada **uzun ve ilişkili section'ları bölmek için** yararlı olabilir; fakat her küçük alanı accordion yapmak etkileşim maliyetini artırır. NN/g, desktop'ta accordion'ların karmaşık içerik için otomatik çözüm olmadığını özellikle belirtiyor.

- [NN/g – Accordions](https://www.nngroup.com/topic/accordions/)
- [W3C APG – Accordion](https://www.w3.org/WAI/ARIA/apg/patterns/accordion/)

**Sectioned edit form:** CONDITIONAL.  
**Her şeyi accordion yapmamak:** CONFIRMED.

---

# 10. Side panel / drawer ne için kullanılmalı?

Side panel:

**uygun**

```text
Rename bot
Edit alert
Change tag
Quick parameter inspection
View order detail
```

gibi kısa, bağlamsal işler için.

Ana strategy configuration gibi onlarca parametreli işlemin drawer içine sıkıştırılması önerilmez.

Atlassian'ın yeni navigation sisteminde supplementary content için `Panel`, navigation için ise `SideNav` ayrımı yapılması da bu yaklaşımı destekliyor.

- [Atlassian Navigation System](https://atlassian.design/components/navigation-system/migration-guide)

**Durum: CONDITIONAL.**

---

# 11. Gerçek zamanlı parametre preview

Config formuna “sonuç ne olacak?” özeti eklemek güçlü bir desen.

Desktop:

```text
┌──────────────────────────┬──────────────────┐
│ Configuration            │ Live Preview     │
│                          │                  │
│ Core settings            │ 12 grid levels   │
│ ...                      │ Range ...        │
│ Advanced                 │ Allocation ...   │
│ ...                      │                  │
└──────────────────────────┴──────────────────┘
```

Preview **sticky right panel** olabilir.

Önemli ayrım:

> Preview, formülün deterministik çıktısını göstermeli; gelecekteki piyasa performansını tahmin ediyormuş gibi sunulmamalı.

Örneğin “12 grid level oluşacak” türü sistem çıktıları uygundur.

Overview+detail yaklaşımı HCI literatüründe iyi bilinen bir desen, ancak araştırmalar etkinliğin **task-dependent** olduğunu gösteriyor.

- [Procedia Computer Science – Overview+Detail Study](https://www.sciencedirect.com/science/article/pii/S1877050921003343)

**Durum: CONDITIONAL.**

---

# 12. Tutarlı strategy form sistemi

DCA/Grid/Hedge için ayrı ayrı tamamen farklı form UI üretmek yerine aynı **config grammar** kullanılmalı.

Örneğin ortak component ailesi:

```text
Section
FieldGroup
NumericParameter
RangeParameter
PercentageParameter
ToggleParameter
ConditionalField
AdvancedSection
ValidationMessage
CalculatedPreview
ParameterSummary
```

Strategy-specific farklar data/schema seviyesinde tanımlanabilir.

Böylece:

```text
DCA
 ├─ Base
 ├─ Entry
 ├─ Ladder
 ├─ Exit
 └─ Advanced

Grid
 ├─ Base
 ├─ Range
 ├─ Grid
 ├─ Exit
 └─ Advanced
```

aynı visual grammar'ı korur.

Bu **design-system/component consistency** prensipleriyle uyumludur ancak bu spesifik schema mimarisi kaynak tarafından dikte edilmez.

**Durum: local judgment call.**

---

# 13. Çoklu bot/oturum izleme

Burada tek cevap “cards” değil.

## Overview

Az sayıda en önemli durum:

```text
Active      12
Paused       3
Warnings     2
Errors       1
```

ve birkaç summary card.

## Operasyonel çalışma ekranı

Table:

| Bot | Strategy | Pair | Status | Runtime | State | Alert |
|---|---|---|---|---|---|---|
| Bot 01 | Grid | ETH/... | Running | ... | ... | — |
| Bot 02 | DCA | ... | Paused | ... | ... | Warning |

Carbon data table:

- büyük veri setlerini düzenlemek,
- belirli kaydı bulmak,
- tüm resources'ları göstermek,
- sorting,
- filtering,
- row expansion,
- batch actions

için tasarlanmıştır.

- [Carbon Data Table](https://carbondesignsystem.com/components/data-table/usage/)

Bu nedenle:

**10–100+ bot → table-first**

daha iyi ölçeklenir.

**3–8 kritik item → cards** kullanılabilir.

Kesin “8” sayısı kaynaklı threshold değildir; **local judgment**.

---

# 14. Drill-down deseni

En iyi model:

```text
Portfolio / Bot Fleet Overview
            ↓
Filtered Bot Table
            ↓
Selected Bot
            ↓
Bot Detail
 ├ Overview
 ├ Config
 ├ Orders
 ├ Positions
 └ Events
```

Yani:

> **Overview → collection → entity → detail**

“Dashboard-of-dashboards” yaklaşımı yerine bunu öneriyorum.

Overview+detail literatürü bunun genel mantığını destekliyor; fakat trading dashboard'a özel zorunlu pattern değildir.

- [ACM – Review of Overview+Detail, Zooming and Focus+Context](https://doi.org/10.1145/1456650.1456652)

**Durum: CONDITIONAL.**

---

# 15. Notification / status mimarisi

Burada üç ayrı kanal olmalı.

### Page / component state

İşin mevcut durumunu temsil eder:

```text
Running
Paused
Connecting
Order pending
Disconnected
Validation error
```

Kalıcıdır.

### Toast

Geçici event:

```text
Configuration saved
Export started
Alert rule created
```

Carbon toast'ların kısa, “at-a-glance” mesajlar olması gerektiğini ve üç satırı aşmamasını öneriyor.

### Notification center

Tarihçesi önemli olaylar:

```text
Bot stopped
Connection lost
Execution failed
Threshold warning
...
```

Badge:

```text
Notifications  ● 3
```

yalnız “kaç unread event var?” gibi ikincil attention signal olarak kullanılmalı.

- [Carbon Notification Pattern](https://carbondesignsystem.com/patterns/notification-pattern/)

Son iki ayrımın spesifik sistematiği **CONDITIONAL**, toast'ın kısa/transient olması **CONFIRMED**.

---

# 16. Gerçek zamanlı frontend render mimarisi

En önemli hata şu olur:

```text
WebSocket tick
   ↓
update entire dashboard React state
   ↓
rerender everything
```

Bunun yerine:

```text
WebSocket / event source
        ↓
normalized realtime store
        ↓
entity/topic subscriptions
        ↓
selectors
        ↓
only affected widget
```

Örneğin:

```text
price:ETH
   → ETH price widget

bot:143:status
   → Bot 143 row
   → Bot 143 header

orders:143
   → Bot 143 order table
```

React'ın `useSyncExternalStore` API'si external store abonelik modeli için doğrudan bir primitive sağlar ve snapshot değişmediğinde aynı değerin döndürülmesini ister.

- [React – useSyncExternalStore](https://react.dev/reference/react/useSyncExternalStore)

**Granular subscription:** CONFIRMED principle.

---

# 17. Batching

React 18+ birden fazla state update'i otomatik olarak batch edebilir:

> React groups multiple state updates into a single re-render.

- [React 18 – Automatic Batching](https://react.dev/blog/2022/03/29/react-v18)

Ancak yüksek frekanslı bağımsız network event'lerini uygulama seviyesinde de coalesce etmek gerekebilir.

Örneğin, her fiyat mesajında DOM güncellemek yerine UI-facing value:

```text
socket events
   ↓
latest value cache
   ↓
frame/update scheduler
   ↓
render latest value
```

şeklinde tutulabilir.

`requestAnimationFrame()` callback'i browser'ın bir sonraki repaint'inden önce çalıştırır.

- [MDN – requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame)

**Event coalescing:** CONDITIONAL.  
**Her network tick'i doğrudan React tree'ye yaymamak:** güçlü engineering recommendation.

---

# 18. Virtualization

Orders, activity logs, replay events veya bot tablolarında yüzlerce/binlerce row varsa virtualization kullanılmalı.

web.dev:

> “List virtualization ... only rendering what is visible to the user.”

Bu doğrudan:

- rendered DOM node sayısını,
- layout maliyetini,
- scrolling maliyetini

azaltır.

- [web.dev – Virtualize Large Lists](https://web.dev/articles/virtualize-long-lists-react-window)

**Durum: CONFIRMED.**

---

# 19. DOM bütçesi

Görünmeyen bütün bot widget'larını DOM'da tutmak iyi fikir değildir.

web.dev, DOM büyüdükçe initial rendering ve sonraki DOM update'lerinin maliyetinin arttığını belirtiyor.

- [web.dev – DOM Size and Interactivity](https://web.dev/articles/dom-size-and-interactivity)

Bu nedenle:

```text
50 bots ×
  chart +
  orders +
  positions +
  history
```

aynı anda DOM'a mount edilmemeli.

**Durum: CONFIRMED.**

---

# 20. `content-visibility`

Uzun dashboard sections için ek optimizasyon olabilir:

```css
.widget-section {
  content-visibility: auto;
}
```

web.dev bunun off-screen subtree rendering'ini erteleyebildiğini ve başlangıç render işini azaltabildiğini açıklıyor.

- [web.dev – content-visibility](https://web.dev/articles/content-visibility)

Bu virtualization'ın yerine geçmez.

**Durum: CONDITIONAL.**

---

# 21. Code splitting / lazy loading

Şunların tümünü ilk bundle'a dahil etmek gereksiz:

```text
Replay engine UI
Advanced strategy editor
Audit/export
Large charts
Historical analysis
Template manager
```

Route ve feature seviyesinde lazy loading kullanılabilir.

web.dev, `React.lazy` ve `Suspense` ile component'leri ayrı JS chunk'larına bölmenin ilk JS payload'ını azaltabildiğini açıklıyor.

- [web.dev – Code Splitting with React.lazy and Suspense](https://web.dev/articles/code-splitting-suspense)

**Durum: CONFIRMED.**

---

# 22. Memoization

`memo`, `useMemo`, `useCallback` dashboard'ın her yerine otomatik uygulanmamalı.

React:

> “You should only rely on memo as a performance optimization.”

Yalnız pahalı ve sık tekrarlanan rendering ölçüldüğünde uygulanmalı.

React Profiler hangi component'in ne kadar render maliyeti oluşturduğunu ölçebilir.

```text
Measure
↓
Locate expensive rerender
↓
Optimize
↓
Measure again
```

- [React – memo](https://react.dev/reference/react/memo)
- [React – Profiler](https://react.dev/reference/react/Profiler)

**Durum: CONFIRMED.**

---

# 23. Urgent / non-urgent update ayrımı

Örneğin kullanıcı search/filter alanına yazarken:

```text
Typing                     → urgent
Large filtered bot table   → defer / transition
Chart recomputation        → potentially non-urgent
```

React docs `useTransition` ve `useDeferredValue` ile non-critical rendering'in ertelenebileceğini açıkça belirtiyor.

- [React Hooks – Performance Hooks](https://react.dev/reference/react/hooks)

**Durum: CONFIRMED technique; kullanım yeri CONDITIONAL.**

---

# 24. Tema mimarisi

Açık/koyu tema component-level renk değiştirerek yapılmamalı.

Yanlış:

```css
.card {
  background: #ffffff;
}

.dark .card {
  background: #151515;
}
```

Temel mimari:

```css
:root {
  --surface-page: ...;
  --surface-panel: ...;
  --surface-raised: ...;

  --text-primary: ...;
  --text-secondary: ...;

  --border-subtle: ...;

  --status-positive: ...;
  --status-warning: ...;
  --status-danger: ...;
}

[data-theme="dark"] {
  --surface-page: ...;
  --surface-panel: ...;
  ...
}
```

Component:

```css
.card {
  background: var(--surface-panel);
  color: var(--text-primary);
  border-color: var(--border-subtle);
}
```

Atlassian:

> “Choose tokens based on meaning ... not specific values.”

- [Atlassian Design Tokens](https://atlassian.design/tokens/design-tokens/)
- [Carbon Color and Themes](https://carbondesignsystem.com/elements/color/overview/)

Carbon da token rolünün değişmemesini, theme'in yalnız gerçek value mapping'ini değiştirmesini öneriyor.

**Durum: CONFIRMED.**

---

# 25. Component-level override politikası

Yeni bir modül:

```css
background: #18191b;
```

gibi kendi dark-mode rengini getirmemeli.

Gerekirse component semantic token eklenmeli:

```text
surface.widget
surface.chart
border.widget
text.metric
status.running
status.paused
status.error
```

ama token'ın theme mapping'i merkezi kalmalı.

Atlassian themes:

> “Themes are how we switch color schemes and styles everywhere using a single set of tokens.”

**Durum: CONFIRMED principle.**

---

# 26. Önerilen nihai ekran modeli

Bu ölçekte ürün için önerilen desktop shell:

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Workspace ▾     Search / Cmd-K            Paper      Alerts      User   │
├──────────────────┬───────────────────────────────────────────────────────┤
│                  │ Bots / Grid / ETH Grid #04                           │
│ Overview         │                                                       │
│                  │ ETH Grid #04              ● Running                   │
│ Automation       │ Futures Grid · ETH/... · Paper                        │
│   Bots           │                                                       │
│   Strategies     │ Overview  Config  Orders  Positions  Events           │
│   Templates      ├───────────────────────────────────────────────────────┤
│                  │                                                       │
│ Portfolio        │                                                       │
│                  │                    CONTENT                            │
│ Monitor          │                                                       │
│   Positions      │                                                       │
│   Orders         │                                                       │
│   Events         │                                                       │
│                  │                                                       │
│ Simulation       │                                                       │
│ Alerts           │                                                       │
│ Audit & Export   │                                                       │
│ Settings         │                                                       │
└──────────────────┴───────────────────────────────────────────────────────┘
```

Bu mimari:

- breadth'i sidebar'a,
- global actions'ı topbar'a,
- context'i page header'a,
- aynı entity içindeki alt görünümleri tabs'e,
- power-user speed'i Cmd-K'ya

dağıtıyor.

---

# 27. Karar matrisi

| Karar | Statü | Kanıt |
|---|---|---|
| 10+ module için side-nav kullanmak | **CONFIRMED** | Carbon, Atlassian |
| Global actions top-nav; app-specific sections side-nav | **CONFIRMED** | Atlassian |
| 6+ yatay tab'den kaçınmak | **CONFIRMED** | Carbon |
| Tabs'i yakın ilişkili local content için kullanmak | **CONFIRMED** | Fluent, Carbon |
| Breadcrumb ile hierarchy/context göstermek | **CONFIRMED** | NN/g, Carbon |
| Breadcrumb + persistent trading context header | **CONDITIONAL** | Wayfinding kaynaklı, domain uyarlaması |
| Cmd-K palette'i secondary accelerator yapmak | **CONDITIONAL** | GitHub shipped pattern; evrensel superiority kanıtı yok |
| Cmd-K'yı tek navigasyon yapmak | **local judgment: tavsiye edilmez** | Güçlü karşılaştırmalı kanıt yok |
| Progressive disclosure | **CONFIRMED** | NN/g |
| Global Simple/Expert yerine section-level advanced disclosure | **CONDITIONAL** | Progressive-disclosure sentezi |
| Yeni karmaşık bot oluşturmayı wizard yapmak | **CONFIRMED / CONDITIONAL** | NN/g, Carbon |
| Mevcut config editini sectioned single-page yapmak | **CONDITIONAL** | Wizard/accordion trade-off'larından sentez |
| Her section'ı accordion yapmak | **desteklenmiyor** | NN/g accordion interaction cost |
| Preview'ı form yanında göstermek | **CONDITIONAL** | Overview+detail araştırması task-dependent |
| Çoklu bot operasyon ekranında table-first | **CONFIRMED / CONDITIONAL** | Carbon table resource management |
| Summary için cards | **CONDITIONAL** | Dashboard synthesis |
| Toast'ı kısa/geçici kullanmak | **CONFIRMED** | Carbon notification pattern |
| Event history için notification center | **CONDITIONAL** | Notification semantics sentezi |
| Granular realtime subscriptions | **CONFIRMED technique** | React external-store API |
| Automatic batching | **CONFIRMED** | React |
| Uzun lists/tables için virtualization | **CONFIRMED** | web.dev |
| DOM miktarını sınırlamak | **CONFIRMED** | web.dev |
| Feature/route code splitting | **CONFIRMED** | web.dev |
| Her component'i memoize etmek | **desteklenmiyor** | React |
| Profiler ile ölçüp selective memoization yapmak | **CONFIRMED** | React |
| Semantic design tokens ile light/dark theme | **CONFIRMED** | Atlassian, Carbon |
| Trading-strategy-specific exact menu grouping | **local judgment** | Tasarım sistemleri domain taxonomy belirlemiyor |

---

# 28. Ana kaynak kaydı

| Kurum / yazar | Kaynak | Tarih | Desteklediği iddia |
|---|---|---:|---|
| Nielsen Norman Group / Jakob Nielsen | [Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/) | 3 Aralık 2006 | Gelişmiş/seçrek fonksiyonları secondary disclosure'a alma |
| Nielsen Norman Group / Raluca Budiu | [Wizards: Definition and Design Recommendations](https://www.nngroup.com/articles/wizards/) | 25 Haziran 2017 | Dallanan/karmaşık ve seyrek süreçlerde wizard kullanımı |
| Nielsen Norman Group | [8 Design Guidelines for Complex Applications](https://www.nngroup.com/articles/complex-application-design/) | erişim 21 Eylül 2026 | Karmaşık uygulamalarda staged disclosure ve clutter azaltma |
| Nielsen Norman Group / Page Laubheimer | [Breadcrumbs: 11 Design Guidelines](https://www.nngroup.com/articles/breadcrumbs/) | 23 Aralık 2018; erişim 21 Eylül 2026 | Hierarchical wayfinding |
| Atlassian Design System | [Navigation System](https://atlassian.design/components/navigation-system/migration-guide) | erişim 21 Eylül 2026 | Top-nav/global ve side-nav/app-specific ayrımı |
| Carbon Design System | [UI Shell Left Panel](https://carbondesignsystem.com/components/UI-shell-left-panel/usage/) | erişim 21 Eylül 2026 | Çok sayıda secondary item için side navigation |
| Carbon Design System | [Tabs](https://v10.carbondesignsystem.com/components/tabs/usage/) | erişim 21 Eylül 2026 | Genellikle ≤6 tab, daha fazlası için alternatif navigasyon |
| Fluent 2 | [Tablist](https://fluent2.microsoft.design/components/web/react/core/tablist/usage) | erişim 21 Eylül 2026 | Tabs küçük ve yakın ilişkili content setleri içindir |
| Carbon Design System | [Forms](https://preview.carbondesignsystem.com/building-blocks/core/patterns/forms) | erişim 21 Eylül 2026 | Progressive disclosure, accordion ve multistep form kullanımı |
| Carbon Design System | [Data Table](https://carbondesignsystem.com/components/data-table/usage/) | erişim 21 Eylül 2026 | Resource listeleri, sorting, filtering, expansion, batch operations |
| Carbon Design System | [Notification Pattern](https://carbondesignsystem.com/patterns/notification-pattern/) | erişim 21 Eylül 2026 | Toast sınırları ve notification yapısı |
| Atlassian Design System | [Design Tokens](https://atlassian.design/tokens/design-tokens/) | erişim 21 Eylül 2026 | Semantic token ve theme architecture |
| Carbon Design System | [Color](https://carbondesignsystem.com/elements/color/overview/) | erişim 21 Eylül 2026 | Role-based tokens ve theme value mapping |
| W3C WAI-ARIA APG | [Tabs](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/) / [Accordion](https://www.w3.org/WAI/ARIA/apg/patterns/accordion/) / [Breadcrumb](https://www.w3.org/WAI/ARIA/apg/patterns/breadcrumb/) | erişim 21 Eylül 2026 | UI pattern'lerinin yapısal modelleri |
| React | [React 18](https://react.dev/blog/2022/03/29/react-v18) | 29 Mart 2022 | Automatic batching |
| React | [useSyncExternalStore](https://react.dev/reference/react/useSyncExternalStore) | erişim 21 Eylül 2026 | External realtime stores için subscription primitive |
| React | [memo](https://react.dev/reference/react/memo) / [Profiler](https://react.dev/reference/react/Profiler) | erişim 21 Eylül 2026 | Selective, measured memoization |
| web.dev | [Virtualize large lists with react-window](https://web.dev/articles/virtualize-long-lists-react-window) | erişim 21 Eylül 2026 | Long list/table virtualization |
| web.dev | [DOM Size and Interactivity](https://web.dev/articles/dom-size-and-interactivity) | erişim 21 Eylül 2026 | Büyük DOM'un interactivity maliyeti |
| web.dev | [Code Splitting with React.lazy and Suspense](https://web.dev/articles/code-splitting-suspense) | erişim 21 Eylül 2026 | Lazy loading / chunking |
| web.dev | [content-visibility](https://web.dev/articles/content-visibility) | 5 Ağustos 2020; erişim 21 Eylül 2026 | Off-screen rendering'in ertelenmesi |
| MDN | [requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame) | erişim 21 Eylül 2026 | Paint-synchronized updates |
| Procedia Computer Science | [Empirical Study of Overview+Detail](https://www.sciencedirect.com/science/article/pii/S1877050921003343) | 2021 | Overview/detail etkisinin task-dependent olması |
| Cockburn, Karlson, Bederson / ACM Computing Surveys | [Review of Overview+Detail, Zooming and Focus+Context](https://doi.org/10.1145/1456650.1456652) | 2009 | Overview/detail ve focus/context desenlerinin karşılaştırılması |

---

# 29. Nihai karar

Bu ölçekte bir üründe **en savunulabilir ana tasarım**, **kalıcı sol modül navigasyonu + global üst bar + entity-level context header + sınırlı local tabs** kombinasyonudur. Formlarda **progressive disclosure**, yeni karmaşık konfigurasyonda **wizard**, mevcut konfigurasyon düzenlemede **sectioned direct-edit**, monitoring'de ise **overview + filtrelenebilir/virtualized table + entity detail** daha tutarlı bir sistem oluşturur.

En önemli ayrım şu: kaynaklar navigation, tabs, progressive disclosure, forms, data tables, tokens ve render teknikleri konusunda oldukça güçlü; fakat **“DCA burada, Grid burada, Hedge şurada olmalı” gibi trading-domain taxonomy kararlarını kaynaklar belirlemiyor**. Bu kısım mutlaka kullanıcı görevleri, card sorting ve tree testing ile doğrulanması gereken **local product judgment** alanıdır.

Ek IA doğrulama kaynağı:

- [NN/g – Information Architecture Study Guide](https://www.nngroup.com/articles/ia-study-guide/)
