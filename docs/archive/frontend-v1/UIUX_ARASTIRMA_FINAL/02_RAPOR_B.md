# Çok-Stratejili Algoritmik Trading Dashboard'u — Bilgi Mimarısi, Navigasyon, Form, Gerçek-Zamanlı Gösterim, Tema ve Performans için Kaynaklı UX Araştırma Raporu

**Belge türü:** Bağımsız, kaynaklı tasarım araştırması (herhangi bir özel ürüne/koda erişim iddiası içermez)
**Hazırlanma tarihi:** 21 Eylül 2026
**Kapsam:** 10+ yapılandırma/izleme modülü ailesi içeren (DCA/averaging-down, spot grid, futures grid, hedge/iki-bacaklı, portföy rebalancing, sinyal-tetikli botlar, çoklu eşzamanlı bot/parite, strateji şablonları, canlı fiyatla paper trading, uyarı/bildirim merkezi, denetim/dışa aktarma, geçmiş veri zaman çizgisi/replay) web tabanlı tek-panel ürünler.
**Bilinçli kapsam dışı:** Yüksek kontrast modu, ekran okuyucu uyumluluk testleri, WCAG puanlaması, marka/logo/renk paleti kimliği, backend/API tasarımı, kaynaksız A/B test iddiaları. ARIA kaynakları **yalnızca yapısal/navigasyon desenleri** için kullanılmıştır.

**Kanıt sınıflandırması (belge boyunca):**
- **CONFIRMED** — doğrudan birincil/resmî kaynak desteği var,
- **CONDITIONAL** — kaynak ilkeyi destekliyor ama uygulama bağlama (kullanıcı uzmanlığı, ekran boyutu, veri hacmi) bağlı,
- **JUDGMENT** — kaynakların kesin cevabı yok; tasarımcı kararı. Gerekçe şeffaf biçimde belirtilir.

---

## 1. Executive Summary

Bu ölçekte bir ürünün en büyük riski, 11 özellik ailesinin her birinin navigasyonda kendi başına bir "hedef" haline gelmesidir. Araştırmanın bulguları tek bir mimari karara yakınsıyor:

1. **Strateji aileleri navigasyon öğesi DEĞİLDİR; veri türüdür.** DCA, grid, hedge vb. tek bir "Botlar/Stratejiler" çalışma alanı içinde *tür* olarak yaşar; navigasyon ise işlevsel 4–5 bölümle sınırlı kalır. Resmî tasarım sistemleri üst düzey navigasyonda pratik sınırı **3–5 hedef** olarak verir; 5+ hedefte çekmece (drawer)/yan panel önerilir [S1][S2][S3].
2. **Birincil navigasyon: kalıcı, gruplanabilir sol yan panel (sidebar); üst bar: evrensel araçlar** (arama/komut paleti, oluştur, bildirim, hesap, workspace/tema değiştirici). Atlassian 2024–25'te tam olarak bu yöne geçti ve gerekçelerini (ölçek, yoğunluk, aşinalık, progressive disclosure) yayımladı [S8]; Carbon UI Shell "soldan sağa = üründen globale" kuralını ve sağ üst switcher/bildirim yerleşimini resmîleştirir [S10][S11].
3. **Bağlam kalıcılığı:** Konum-tabanlı breadcrumb + bot detayında sabit üst bilgi (ad, tür, durum, PnL, başlat/durdur). NN/g breadcrumb'ı 1995'ten beri "neredeyse sıfır maliyetli, hiç sorun çıkarmayan" ikincil navigasyon olarak doğruluyor [S6][S7].
4. **Basit/uzman ayrımı: sayfa-modu değil, form-içi kademeli açılma (progressive disclosure).** NN/g'nin klasik çalışması: ilk ekranda yalnız en önemli seçenekler; ikincil seviye talep üzerine; **2 seviyeden derin açılma pratikte kullanılabilirliği düşürür** [S12]. Atlassian ve Polaris aynı ilkeyi tasarım sistemi prensibi olarak benimser [S8][S14]. Risk/para ile ilgili alanlar (stop-loss, maksimum pozisyon, tasfiye koşulları) **asla** katlanmış "gelişmiş" bölümüne gizlenmez — bu, NN/g'nin "sık ihtiyaç duyulan her şey ilk seviyede olmalı" kriterinin ve hata-önleme sezgiselinin doğrudan sonucudur [S12][S21] *(alan seçimi = CONDITIONAL/JUDGMENT)*.
5. **Config formu: ilk kurulumda sihirbaz (wizard), sonrasında tek-sayfa bölümlü form + sağda canlı önizleme paneli.** NN/g sihirbazı açıkça "acemi kullanıcılar ve *seyrek yapılan* süreçler (ör. kurulum/yapılandırma)" için önerir; uzman/sık kullanıcı için sihirbazın kontrol kısıtlaması dezavantajdır [S15]. Canlı hesaplama önizlemesi, 0,1 sn altı geri bildirim eşiğiyle birleşince "durum görünürlüğü" sezgiselini doğrudan karşılar [S18][S21].
6. **Gerçek-zamanlı gösterim: abone-bazlı seçici render + erteleme (deferral) + virtualization.** React'ın resmî dokümantasyonu `useDeferredValue`/`useTransition`/`memo`/`useSyncExternalStore` ile "acil" ve "ertelenebilir" render'ı ayırmayı belgeler [S25–S29]; web.dev/Chrome, INP ≤ 200 ms bütçesini ve 50 ms üstü uzun karelerin (LoAF) teşhisini resmî eşik olarak verir [S30–S33]; uzun liste/tablolar için virtualization resmî web.dev rehberidir [S34].
7. **Bildirim hiyerarşisi: geçici onay = toast/flag; kalıcı kritik sistem durumu = banner; bot-içi bağlamsal durum = section/status mesajı; geçmiş ve merkez = kalıcı bildirim paneli + rozet sayacı; yıkıcı işlem = yalnızca özetleyen seçenekli onay diyaloğu.** Bu ayrım Atlassian'ın resmî mesaj-bileşeni rehberinde ve NN/g'nin hata/bildirim rehberlerinde birebir tanımlıdır [S13][S19][S20][S22].
8. **Tema: 3 katmanlı design-token mimarisi** (primitive → semantik rol → component token), CSS custom properties + `data-theme` bağlamı; W3C Design Tokens CG formatı ($value/$type, alias, grup) kaynak-of-truth olarak kullanılabilir [S36][S37]; M3 "şema ≠ tema" ayrımını ve token bağlamı (dark theme) kavramını, M2/M3 koyu yüzey yaklaşımını (saf siyah değil koyu gri, koyu temada daha açık/desatüre tonlar) belgeler [S4][S5].
9. **Hız: modül-bazlı code-splitting (React.lazy + Suspense), rota ve ağır-bileşen seviyesinde lazy loading, memoization, virtualization, tick throttle/batching, layout-thrashing'ten kaçınma, ağır hesapların (replay/backtest) worker'a alınması.** Tümü resmî React ve web.dev dokümantasyonunda belgelenmiş desenlerdir [S25–S29][S30–S35].
10. **Çoklu bot izleme: kart-özet → detay (drawer/aynı sayfa detay) geçişi.** Shneiderman'ın görsel bilgi-arama mantrası ("önce genel görünüm, zoom/filtre, sonra talebe-göre detay") [S16] ve NN/g'nin karmaşık-uygulama rehberi #7 ("ikincil bilgiye ana ekrandan ayrılmadan erişim") [S17] bu deseni doğrudan destekler. Few'ün "tek ekranı aşma" pitfall'u özet ekranın tasarım kısıtıdır [S23].

---

## 2. Önerilen Bilgi Mimarisi (Modül Gruplama + Navigasyon Hiyerarşisi)

### 2.1 İlke: Özellik ailelerini değil, işleri (jobs) gruplayın

11 yapılandırma ailesi (DCA, spot grid, futures grid, hedge, rebalancing, sinyal botu, şablonlar, paper trading, çoklu bot, uyarılar, denetim, replay) düz bir menüye konursa iki kanıtlı antipattern oluşur:

- **Üst sınır ihlali:** M3, 5'ten fazla navigasyon öğesini açıkça önermez; M2, 5+ üst-düzey hedef için navigation drawer'ı (yan panel) doğru bileşen olarak tabloyla belirtir [S1][S2].
- **"Junk-drawer" menüler:** NN/g, kategorize edilemeyen öğelerin atıldığı düşük-kokulu (low information scent) menüleri uygulama tasarımının en yaygın 10 hatasından biri sayar [S24]; etiketler "kullanıcının tahmin edebileceği" kokuya sahip olmalıdır [S25a].

**Çözüm:** Strateji aileleri tek bir **"Botlar & Stratejiler"** çalışma alanının *içinde tür/filtre* olarak yaşar (hepsi aynı varlık türüdür: "çalışan bir bot konfigürasyonu"). Şablonlar, bu alanın "oluştur" akışının girişidir. Paper trading, replay ve geçmiş veri, "Piyasa & Veri" iş grubuna; uyarı merkezi ve denetim/dışa aktarma "Olaylar & Denetim" grubuna bağlanır.

### 2.2 Önerilen 3-seviyeli hiyerarşi

```
SEVİYE 0 — Workspace kabuğu (her ekranda kalıcı)
┌────────────────────────────────────────────────────────────────────┐
│ Üst bar: [Ürün adı] [Arama / Komut paleti ⌘K] ... [Bildirim 🔔(3)]  │
│          [Hesap] [Tema] [Workspace/Borsa değiştirici (en sağ)]      │
├──────────┬─────────────────────────────────────────────────────────┤
│ Sol      │ SEVİYE 1 — Bölüm (4–5 adet)                             │
│ yan      │  1. Genel Bakış      (portföy özeti, aktif botlar,      │
│ panel    │                       son olaylar — "dashboard of       │
│ (bölüm   │                       dashboards")                      │
│ listesi) │  2. Botlar & Stratejiler (tüm türler: DCA, spot/futures │
│          │       grid, hedge, rebalance, sinyal; şablon galerisi;  │
│          │       çoklu bot tablo/kart görünümü)                    │
│          │  3. Piyasa & Veri    (canlı fiyatlar, geçmiş veri,      │
│          │       replay/timeline, paper trading ortamı)            │
│          │  4. Olaylar & Denetim (uyarı/bildirim merkezi, uyarı    │
│          │       kuralları, denetim günlüğü, dışa aktarma)         │
│          │  5. Ayarlar          (hesap/borsa bağlantıları, API     │
│          │       anahtarları, tercihler, tema)                     │
├──────────┼─────────────────────────────────────────────────────────┤
│          │ SEVİYE 2 — Nesne/örnek                                  │
│          │  Bot listesi → tek bot workspace'i                      │
│          │  (sabit başlık: ad · tür · çift · durum · PnL ·         │
│          │   Başlat/Durdur) + breadcrumb:                         │
│          │   Genel Bakış > Botlar > BTC-Grid-01 > Emirler          │
│          │  İçerik sekmeleri (in-page tabs, ~5–7):                 │
│          │   Özet | Pozisyonlar | Emirler | Ayarlar | Günlük |     │
│          │   Performans/Replay                                     │
└──────────┴─────────────────────────────────────────────────────────┘
```

### 2.3 Bu mimarinin kaynak dayanakları

| Karar | Gerekçe | Kaynak | Sınıf |
|---|---|---|---|
| Birincil navigasyon sol yan panelde, her ekranda görünür | Atlassian: ürün navigasyonunu üst bardan sidebar'a taşıdı; gerekçe: "dikey alan ve bilgi yoğunluğu … dropdown menülerle mümkün olmayan kuşbakışı görünüm"; ayrıca Google Workspace/Slack/Teams aşinalığı. NN/g: gizli navigasyon (hamburger) ölçülebilir biçimde daha az keşfedilir, düşük bilgi kokusu taşır; üst düzey kategorileri dropdown'a gömmek keşfi zorlaştırır | [S8][S38][S39] | **CONFIRMED** (görünürlük ilkesi) |
| Bölüm sayısı 4–5; bölüm içi derinlik en fazla 1 açılır-kapanır seviye | M3: nav bar/rail için 3–5 hedef, "5'ten fazla öğe koymayın"; M2: 5+ üst hedef → drawer; Fluent 2 Nav: "Nav yalnızca bir seviye iç içe geçmeyi destekler … daha derin ve karmaşık hiyerarşi gerekiyorsa Tree kullanın" | [S1][S2][S3] | **CONFIRMED** (sayı sınırı); bölüm adlandırması = **JUDGMENT** (kart sıralama/tree testi ile doğrulanmalı) |
| Üst bar yalnız evrensel eylemler: arama, oluştur, bildirim, hesap, switcher | Atlassian: "üst bar artık tutarlı biçimde arama ve oluştur gibi evrensel eylemlere ayrılmış"; Carbon UI Shell: "soldan sağa = üründen globale"; arama en soldaki ikon (genişleyebilsin), bildirimler sağdan 3., hesap sağdan 2., switcher en sağda ve konumu asla kaymaz | [S8][S10] | **CONFIRMED** |
| Workspace/borsa/hesap değiştirici (context switcher) üst barın en sağında | Carbon: "switcher, kullanıcının ürünler ve sistemler arasında kolayca gezinmesini sağlar … en sağdaki ikon her zaman switcher olmalı; böylece sistemler arası geçişte ikon kaymaz" | [S10][S11] | **CONFIRMED** (bileşen varlığı ve konumu); trading'e özgü "borsa bazlı workspace" semantiği = **JUDGMENT** |
| Strateji aileleri navigasyonda değil, "Botlar" modülünde tür/filtre olarak | Fluent: navigasyon öğeleri kısa, taranabilir, hedef-odaklı olmalı; "arama ve sabitleme, tutarlı navigasyonun yerine geçmez" (tersi de doğru: tür listesi navigasyonu şişirmemeli). NN/g: junk-drawer antipattern'i; mega menü yalnızca gerçekten çok sayıda *hedef* varsa anlamlıdır — oysa burada hedefler tek bir listede filtrelenen aynı tür nesnelerdir | [S3][S24][S40] | **CONDITIONAL** — kullanıcı zihinsel modeli "strateji türüne göre" navigasyonu bekliyorsa (kard testiyle ölçülür) bölüm altında ikinci seviye tür grupları eklenebilir |
| Bot detayında içerik sekmeleri (in-page), bölüm navigasyonuyla karıştırılmaz | NN/g Tabs: "sayfa-içi sekmelerle gezinme sekmelerini aynı kontrol içinde karıştırmak kullanıcıyı yönünü kaybettirir"; sekmeler tek satır, panelin üstünde; "farklı sekmelerdeki bilgiye aynı anda ihtiyaç varsa sekme kullanmayın" → bu yüzden Özet sekmesi kritik KPI'ları tekrar eder | [S41] | **CONFIRMED** (ayrım kuralı); sekme sayısı ~7 = **JUDGMENT** (kaynak üst sınır vermez; "tek satır + kısa etiket" kısıtı fiilî sınır) |
| Breadcrumb: konum-tabanlı (tarihçe-tabanlı değil), tüm üst öğeler tıklanabilir, ana gezinmenin yerini almaz | NN/g: "breadcrumb'lar site hiyerarşisini göstermeli, kullanıcının geçmişini değil"; "breadcrumb'lar küresel gezinmenin yerini almamalı, tamamlamalı"; 1995'ten beri öneriliyor, testlerde "hiç sorun çıkarmadığı" gözlemlendi | [S6][S7] | **CONFIRMED** |
| Derin modüllerde (ör. Ayarlar alt sayfaları) bağlamsal ikincil yan panel | Atlassian/Jira platform rehberi: "derin bilgi mimarisine sahip uygulamalar bağlamsal sidebar deseninden yararlanabilir … daha derin sayfalar için uygulama-içi navigasyon kullanın (progressive disclosure deseni)"; iç içe sidebar (nesting) deseninden kaçının | [S9] | **CONFIRMED** (desen); hangi modüllerde uygulanacağı = **JUDGMENT** |
| Komut paleti (⌘K) hızlandırıcı olarak eklenir, navigasyonun yerine geçmez | NN/g: "arama, gezinmenin yerine geçemez — navigasyon insanlara sitede ne bulabileceklerini gösterir ve arama uzayının yapısını öğretir"; Fluent: "arama ve sabitleme tutarlı navigasyonun ikamesi değildir"; Nielsen sezgisi #7: "hızlandırıcılar acemiye görünmez, uzmanı hızlandırır" → palet görünür navigasyonun *üzerine* eklenen uzman kısayoludur. Yapısal implementasyon: ARIA combobox deseni | [S42][S3][S21][S43] | **CONDITIONAL** — palet olmadan da tüm işlevler görünür navigasyonla ulaşılabilir olmalı; etkinlik iddiası için bu üründe test gerekir |
| Genel Bakış = "dashboard of dashboards": tek ekran, operasyonel odak | Few pitfall #1: dashboard tek ekran sınırını aşmamalı (bağlantılar scroll arkasında kaybolur); NN/g: operasyonel dashboard (şu anki durumu izle, hızlı karar) ile analitik dashboard (karşılaştır, trend çıkar) ayrımı — trading izleme operasyoneldir; preattentive, uzunluk-tabanlı (lineer) grafikler alan/açı-tabanlı (pie/gauge) grafiklerden üstündür | [S23][S44] | **CONFIRMED** |

---

## 3. Soru A — Navigasyon Hiyerarşisi Detayları

### A1. 10+ modülde gruplama stratejisi

**Öneri:** Üç katman: (0) workspace kabuğu, (1) 4–5 işlevsel bölüm, (2) nesne workspace'i. Strateji türleri, bildirim türleri ve veri kaynakları *filtre/facet* olarak modül içinde yaşar.

- **Kanıt:** Yukarıdaki tablo. Ek olarak NN/g "Information Foraging/Scent": kullanıcı bir bağlantının değerini etiket + bağlamdan *tahmin eder*; bölüm etiketleri kullanıcı iş dilinde ("Botlar", "Olaylar") olmalı, sistem dilinde ("Strategy Engine Configurations") değil [S25a][S45]. Nielsen sezgisi #2 (sistem ile gerçek dünya eşleşmesi) ve #6 (tanıma > hatırlama) bunu destekler [S21].
- **"Workspace" kavramı:** Atlassian'ın araştırması (16 Jira kullanıcısı) iki net ihtiyaç buldu: *kullanıcıya özelleştirme* (göster/gizle) ve *sık öğelere hızlı erişim* (Starred & Recent). Bu, çok-botlu trading paneline doğrudan çevrilir: **sabitlenmiş botlar + son görüntülenenler** yan panelin üstünde [S8].
- **Sınıf:** Gruplama *ilkesi* **CONFIRMED**; 5 bölümün kesin kompozisyonu **JUDGMENT** (kaynaklar belirli bir ürün taksonomisi vermez; card sorting + tree testing ile doğrulanmalıdır — NN/g'nin IA doğrulama yöntemi budur).

### A2. "Çok fazla sekme" eşiği ve çözümler

**Doğrulanmış eşikler:**
- M3 navigation bar: **3–5 hedef**; "5'ten fazla navigasyon öğesi koymayın — öğeler çakışır ve çeviri metinleri sığmaz; bunun yerine sekme veya menü arkasına gizlenmiş genişletilebilir navigation rail düşünün" [S1].
- M2 tablosu: drawer **5+** üst hedef; bottom nav **3–5**; tabs **2+** (hiyerarşinin her seviyesinde, *benzer* içerik için) [S2].
- Fluent 2 Nav: tek iç içe seviye; kategori düğümleri akordeon gibi davranır, **link değildir** [S3].
- NN/g Tabs: tek satır sekme; karışık tip yasak; aynı anda karşılaştırma gereken içerik sekmeye bölünmez [S41].

**Taşma çözümü (doğrulanmış):**
1. Görünür üst-düzey kategorileri dropdown arkasına *gömmeyin* [S39]; gizli navigasyon kullanım metriklerini düşürür [S38].
2. Gerçekten çok sayıda hedef gerekiyorsa **gruplu, iki-boyutlu mega menü** ("her şey tek bakışta görünür — kaydırma yok; gruplama görsel olarak vurgulanır") [S40].
3. **Favoriler/son kullanılanlar** (Atlassian Starred & Recent — kullanıcı araştırmasıyla doğrulanmış ihtiyaç) [S8].
4. **Komut paleti** yalnız hızlandırıcı olarak (bkz. §2.3 son satır) [S42][S21].
5. Liste-içi tür çeşitliliği (11 strateji ailesi) **facet/filtre** ile çözülür: NN/g "facetler aramayı navigasyona dönüştürür ve bilinmeyen arama uzayında yapı hissi verir" [S42].

**Öneri:** Bu üründe bölüm sayısı 5'te kaldığı için sekme taşması birincil navigasyonda oluşmaz; taşma riski bot-detay sekmelerinde ve bildirim türlerindedir → orada da 7'yi aşan sekme listesi yerine gruplu sekme başlıkları + filtre kullanın. **Sınıf: CONFIRMED** (eşikler ve çözümler kaynaklı); eşiklerin bu ürüne uygulaması **CONDITIONAL** (ekran genişliği ve çeviri uzunluğu M3'ün gerekçesidir).

### A3. Kalıcı bağlam göstergesi ("hangi botta çalışıyorum?")

**Öneri — üçlü kombinasyon (hepsi kaynaklı):**
1. **Konum-tabanlı breadcrumb** her derin sayfada (Genel Bakış > Botlar > BTC-Grid-01 > Emirler). Kaynak: [S6][S7] — breadcrumb "kullanıcının mevcut konumunu hiyerarşide gösterir", "dış bağlantı/deep link ile gelen kullanıcıyı yönlendirir", "hiçbir testte sorun çıkarmadı". **CONFIRMED**.
2. **Bot workspace'inde sabit (sticky) üst bilgi:** bot adı + tür rozeti + parite + çalışma durumu + anlık PnL + Başlat/Durdur eylemi. Dayanak: NN/g karmaşık-uygulama rehberi #8 "önemli bilgi görsel olarak belirgin olmalı"; #7 "birincil ve ikincil bilgi arasında geçişi kolaylaştırın"; Nielsen sezgisi #1 "sistem durumu her zaman görünür olmalı" [S17][S21]. **CONFIRMED (ilke)**, yerleşim **JUDGMENT**.
3. **Üst barda workspace/borsa değiştirici** (çok hesaplı/çok borsalı kullanımda global bağlam). Carbon switcher deseni [S10][S11]. **CONDITIONAL** (çok-hesap gerçekten varsa).

Ek kural: Yıkıcı bağlam eylemlerinde (botu durdur, pozisyon kapat) breadcrumb yetmez; **sonucu özetleyen seçenekli onay diyaloğu** kullanın ("Yes/No" yerine "Botu durdur / Çalışmaya devam etsin"). Kaynak: NN/g confirmation dialogs — "yanıt seçenekleri her seçeneğin ne yapacağını özetlesin" [S22]; Nielsen sezgisi #5 (hata önleme) [S21]. **CONFIRMED**.

---

## 4. Soru B — Progressive Disclosure (Basit/Uzman Ayrımı)

### B1. Form düzeyinde mi, sayfa düzeyinde mi, modül düzeyinde mi?

**Öneri: Alan/bölüm düzeyinde, formun içinde (in-context disclosure). Global bir "Basit mod / Uzman mod" sayfa anahtarı kullanmayın.**

Kanıt zinciri:
- NN/g Progressive Disclosure (Nielsen, 2006): tanım — "gelişmiş veya seyrek kullanılan özellikleri ikincil ekrana erteler; uygulamayı öğrenmesi kolay ve **daha az hataya açık** hale getirir". Kural 1: "başlangıçta yalnızca en önemli birkaç seçeneği göster"; kural 2: "uzmanlaşmış seçenekleri **talep üzerine** sun". Avantaj: ilk ekranda görünen şey kullanıcıya "bu önemli" sinyali verir; acemi hata yapmaktan korunur, uzman seyrek seçenekleri taramaktan kurtulur — "öğrenilebilirlik, kullanım verimliliği ve hata oranı olmak üzere kullanılabilirliğin 5 bileşeninden 3'ünü iyileştirir" [S12]. **CONFIRMED**.
- NN/g 4 Principles to Reduce Cognitive Load in Forms (2025): "uzun formlar kullanıcıyı daha başlamadan bunaltabilir … **karmaşık form tasarlarken yalnızca mevcut göreve ilişkin olanı gösterin**, ek alanları kullanıcı ilerledikçe tanıtın" — bu, çok-sayfa sihirbazı *veya* aynı sayfada koşullu mantık olarak uygulanabilir [S46]. **CONFIRMED**.
- Atlassian (2025): navigasyon tasarım prensiplerinden biri — "yeni kullanıcılar için yaklaşılabilir olmak adına bilgiyi kademeli aç, **güç kullanıcıların ihtiyaç duyduğu işlevselliği koruyarak**" [S8]. **CONFIRMED** (ilke).
- Polaris: "çok parçalı görevleri sindirilebilir adımlara bölün (aka 'progressive disclosure')" [S14]. **CONFIRMED** (ilke).

**Neden global mod anahtarı değil?** NN/g'nin ilerleme kriteri: "birincilden ikincil seviyeye **nasıl ilerleneceği belirgin olmalı**" ve "ikincil seviyeye ilerlemek için **birden çok yol sunmak nadiren iyi fikirdir**". Global bir "Uzman Mod" anahtarı + bölüm içi disclosure + sihirbaz kısayolu = üç paralel ilerleme mekanizması → kaynak kriterine aykırı. Ayrıca "aynı şey için aynı ad aynı yerde" (tutarlılık) kuralı mod-değişince bozulur [S12][S47]. **Sınıf: açılma düzeyi CONFIRMED; "global mod anahtarından kaçın" çıkarımı CONDITIONAL** (kaynak doğrudan "mod anahtarı kullanma" demez; kriterlerden türetilir).

### B2. Uzman alanlara erişim: her zaman görünür-ama-katlı mı, ayrı mod mu?

**Öneri: Her zaman görünür başlıklı, varsayılan kapalı disclosure bölümleri ("Gelişmiş: Grid seviye aralıkları", "Gelişmiş: Trailing mesafesi") + kullanıcının açtığı bölümleri hatırlayan kalıcı durum (oturum/cihaz bazlı).**

- Disclosure düğümü yapısal olarak W3C ARIA APG **Disclosure (Show/Hide)** deseniyle implemente edilir: düğme `aria-expanded` + `aria-controls` taşır; navigasyon menülerinde disclosure kullanımı için APG'de hazır örnek vardır (yapısal amaçla; kontrast/ekran-okuyucu puanlaması bu turun kapsamı dışında) [S43a].
- NN/g: "açıklamanın mekaniği basit olmalı (gelişmiş özellikler düğmesi açıkça görünür bir yerde)" ve "etiket, ilerlendiğinde ne bulunacağına dair **net beklenti** kurmalı (güçlü information scent)" [S12]. → "Gelişmiş ayarlar" jenerik etiketi yerine "Gelişmiş: DCA merdiven aralıkları" gibi içerik-adı veren etiket. **CONFIRMED**.
- Seviye sınırı: "2 disclosure seviyesini aşan tasarımlar tipik olarak düşük kullanılabilirliğe sahiptir; kullanıcılar seviyeler arasında hareket ederken kaybolur" [S12]. → Bu üründe en fazla: basit alanlar → "Gelişmiş" disclosure. Üçüncü seviye (gelişmiş içinde gelişmiş) **yasak**. **CONFIRMED**.
- Form içinde akordeon kullanımı: NN/g (Budiu, 2015) "her adımı bir akordeon altına katlamak, form iş akışını bunaltmadan iletmenin ve çoklu sayfa yüklemesi gerektirmemenin etkili bir yoludur"; karşı-risk: yön kaybı → uzun içerik açıldığında akordeon başlıklarını kalıcı (sticky) tutun, akordeonları jump-link gibi davranacak şekilde ele alın [S48]. **CONDITIONAL** (masaüstü, geniş form bağlamında; mobil kanıtı doğrudan masaüstüne taşımaz).

### B3. Basit görünümde asla gizlenmemesi gereken bilgi

**Öneri — "asla katlama" listesi (her strateji türünde zorunlu görünür):**
1. Yatırılan/tahsis edilen bütçe ve pozisyon büyüklüğü,
2. Kaldıraç (futures grid/hedge'de),
3. Stop-loss / tasfiye-önleyici koşullar,
4. Maksimum eşzamanlı açık emir/adım sayısı,
5. Botun hangi hesapta/borsada ve gerçek mi paper mı çalıştığı (canlı/paper ayrımı — yanlışa-malıyet riski),
6. Aktif durum + Başlat/Durdur.

**Dayanak ve sınıf:** Kaynaklar "risk alanlarını gizlemeyin" cümlesini trading bağlamında kurmaz — bu, şu **CONFIRMED** ilkelerin birleşiminden türetilen bir **CONDITIONAL/JUDGMENT** kuralıdır:
- NN/g PD kriteri: "kullanıcıların **sık ihtiyaç duyduğu her şeyi** ilk seviyede açmalısınız" — bütçe/kaldıraç/stop, her kurulumun zorunlu girdisidir, "seyrek gelişmiş seçenek" değildir [S12].
- Nielsen sezgisi #5 (hata önleme): "iyi hata mesajından da iyisi, problemi baştan önleyen tasarımdır … hata-koşullarını yok edin ya da kullanıcı taahhütte bulunmadan önce onay seçeneği sunun" [S21].
- NN/g: onay diyaloğu + özetleyen seçenekler, yıkıcı eylemler için [S22].
- Ayrıca "gerçek/paper" etiketi, NN/g'nin tutarlılık hatası ("aynı ad aynı yerde") ve "bilginin nasıl kullanılacağını belirtmeme" hatalarından korunmanın doğrudan uygulamasıdır [S47][S24].

---

## 5. Soru C — Config-Ağırlıklı Formlar

### C1. Düzen: tek uzun form mu, sihirbaz mı, yan panel mi?

**Öneri — ikili akış:**
- **İlk kurulum (bot oluşturma): 4–6 adımlı sihirbaz + her adımda sağda canlı önizleme.**
  - NN/g Wizards: "sihirbazları **acemi kullanıcılar veya seyrek yapılan süreçler (ör. yapılandırma veya kurulum)** için kullanın"; "sihirbazlar karmaşık süreci adımlara böldüğü için sayfalar daha sadedir … **hata olasılığını azaltır**"; dallanma ile "kişiler yalnızca kendi durumlarına uygulanan adımları görür" [S15]. Bot oluşturma, ürünün doğası gereği seyrek (kurulum) ve bilgi gerektiren bir süreçtir → sihirbaz endikasyonu **CONFIRMED**.
  - Sihirbaz tasarım kuralları (NN/g): adımlar **kendi kendine yeterli** olmalı (önceki adımdaki bilgiyi gerektirmemeli); yardım/açıklama **sihirbazın yanında** açılmalı, üzerini örtmemeli; "Review & Save" (incele-kaydet) olanağı görünür olmalı [S15]. **CONFIRMED**.
  - Adım sırası ilkeleri (NN/g 2025): **familiarity** (kolay/bilinen alanla başla: ad, parite) → **priority** (önemli sorular ek sorulardan önce: bütçe, tür) → **dependency** (sonraki sorular öncekilere dayanır: grid aralığı ancak tür=grid ise) → **complexity** (basitten karmaşığa: trailing/koşullu mantık en sonda) [S46]. **CONFIRMED**.
- **Sonraki düzenlemeler (mevcut botu değiştirme): tek sayfa, bölümlü form + bölüm içi disclosure + sol mini-IA (jump links).**
  - NN/g sihirbaz dezavantajı: "sihirbazlar kullanıcının **kontrolünü ve yaratıcılığını sınırlar** … sık tekrarlanmak zorunda kalırsa veya kullanıcının alan bilgisi yüksekse hızla sinir bozucu ve aşırı kontrolcü hale gelir" → uzman/sık düzenleme akışında sihirbaz zorunluluğu **kaynağa aykırı**; tek-sayfa erişim sunulmalı [S15]. **CONFIRMED**.
  - Mini-IA/jump-link gerekçesi: NN/g (Budiu): akordeon/jump-link yapısı "kullanıcıya detaya odaklanmadan önce **büyük resmi** verir … sayfanın zihinsel modelini kurmasına yardım eder"; çok uzun sayfalar korkutucudur [S48]. **CONDITIONAL** (form uzunluğu ~2 ekrandan fazlaysa).
- **Koşullu alanlar:** Aynı sayfada dallanma mantığı ("tür = futures grid" seçilince kaldıraç alanı görünür). NN/g bunu açıkça tanımlar: "dallanma mantığı olan formlar … 'sihirbaz' olarak anılan bu yaklaşım önceki girdiye dayanarak ilgili alanları **dinamik biçimde** gösterir … kullanıcının ilgisiz soruları tarama/filterleme dikkat maliyetini azaltır" — yani dallanma tek sayfada da sihirbaz sayılır [S46][S15]. **CONFIRMED**.
- **Uzun dropdown'lardan kaçının:** NN/g (2026): dropdown ~5–15 seçenek aralığında iyidir; 15+ seçenek için **filtrelenebilir combobox** önerilir (parite/borsa seçimleri tam bu vaka) [S49]. **CONFIRMED**.
- **Doğrulama ve hatalar:** inline doğrulama (alan bitince yanında göster), hatalar alanın yanında, renk+ikon çift kodlu, özet tek başına kanıt sayılmaz, modal yalnızca kritik hatalarda; placeholder'ı etiket yerine kullanmayın. Kaynaklar: [S19][S50]. **CONFIRMED**.

### C2. Gerçek-zamanlı parametre önizlemesi ("bu ayarla ne olur?")

**Öneri:** Formun yanında (geniş ekranda sağ sütun, darda alta katlanan) **kalıcı, yapışkan "Sonuç önizleme" paneli**: DCA merdiveni grafiği, grid seviye tablosu, tahmini maliyet/ortalama, trailing mesafe görselleştirmesi; her girdi değişiminde ≤100 ms'de güncellenir; sayısal çıktılar aşırı hassasiyet göstermez (2–4 anlamlı basamak).

**Dayanak:**
- Yanıt süresi limitleri: 0,1 sn = "anlık" hissi; 1 sn = dikkat kesilmeden akan sınır; 10 sn = dikkatin kopması (progress göstergesi gerekir) [S18]. Önizleme hesabı 0,1 sn altında kalmalı; kalamıyorsa `useDeferredValue` ile "bayat (stale)" içerik gösterilip arka planda hesaplanır (React resmî deseni: `isStale = query !== deferredQuery` ile soluklaştırma) [S25]. **CONFIRMED**.
- Shneiderman: görselleştirme arayüzlerinde "on binlerce öğe gösterilse bile **100 ms altı güncelleme** hedeftir" [S16]. **CONFIRMED**.
- Sezgi #1: sistem durumu görünür olmalı — önizleme paneli, "bu ayar ne üretir" durumunun sürekli görünür hâlidir [S21]. **CONFIRMED (ilke)**; panelin konumu (sağ sütun) **JUDGMENT**.
- NN/g sihirbaz kuralı #7: açıklamalar/yardım **alanların yanındaki pencerede** görünmeli, formu örtmemeli → önizleme paneli modal/tooltip değil, kalıcı yan panel olmalı [S15]. **CONFIRMED**.
- Few pitfall #3: "aşırı detay/hassasiyet göstermek" — önizlemede sahte kesinlikten (8 ondalık) kaçının [S23]. **CONFIRMED**.

### C3. Strateji şablonları arasında tutarlılık

**Öneri:** Ortak **form şeması iskeleti** tüm türlerde aynı kalır: (1) Kimlik (ad, parite, hesap, gerçek/paper), (2) Bütçe & risk (zorunlu-görünür), (3) Türe-özgü parametreler (tek dallanma noktası), (4) Tetikleyici/koşullar, (5) Bildirim tercihleri, (6) İncele & etkinleştir. Türe-özgü bölüm dışında alan adları, sırası, birimleri ve bileşenler birebir aynıdır.

**Dayanak:**
- NN/g 2008 hataları #2: "karışıklık, uygulamalar aynı şey için farklı sözcük/komut kullandığında veya aynı sözcüğü farklı kavramlar için kullandığında doğar … **aynı şey için aynı adı aynı yerde** kullanın"; "display inertia" (öğelerin yer değiştirmesi) ihlali [S47]. **CONFIRMED**.
- NN/g Tabs: "tutarlılık kullanılabilirlik sezgisidir; kullanıcının arayüz üzerinde ustalık hissini inşa eder … tutarlılık için tasarım sistemi kullanın" [S41]. **CONFIRMED**.
- Atlassian navigasyon mimarisi dersi: "yüzlerce navigasyon bileşeni ve ürünler arası 23 büyük tutarsızlık … çoğu ihtiyaç **3 yeniden kullanılabilir bileşenle** karşılanabiliyor" — çok-modüllü ürünlerde çeşitlilik, *özellik kombinasyonlu* az sayıda temel bileşenle yönetilir; her modül kendi özel bileşenini yazmaz [S8]. **CONFIRMED (bileşen stratejisi)**.
- Şablon galerisi (hazır DCA/grid ön ayarları): NN/g "No Default Values" hatası — varsayılan sunmamak en yaygın uygulama hatalarındandır; şablonlar güçlü varsayılanlar setidir [S24]. **CONDITIONAL** (şablonların gerçek kullanıcı dağılımından türetilmesi gerekir; kaynaksız "popüler şablon" listesi JUDGMENT).

---

## 6. Soru D — Gerçek-Zamanlı Durum / Olay Akışı

### D1. Çok sayıda canlı widget'ın performanslı render'ı

**Öneri mimarisi (katmanlar):**

1. **Veri katmanı — merkezi abone-store, bileşen-başına seçici abonelik:** Fiyat/emir akışını tek bir harici store'da (WebSocket → store) tutun; React bileşenleri `useSyncExternalStore` ile yalnızca ilgilendikleri dilime abone olur. React resmî dokümantasyonu bu hook'u "harici bir veri kaynağına abone olmak" için belgeler; ayrıca store verisi değişmiyorsa `getSnapshot` aynı referansı döndürmelidir (gereksiz render'ı önleme koşulu) [S29]. **CONFIRMED**.
2. **Güncelleme katmanı — tick throttle + batch:** Ham tick'leri UI'a doğrudan bağlamayın; 100–250 ms'lik kare-uyumlu pencerelerde son değeri yayınlayın. Gerekçe: Shneiderman'ın <100 ms görsel güncelleme hedefi [S16]; web.dev/Chrome'un 50 ms "uzun kare" eşiği ve INP ≤ 200 ms "iyi" bütçesi [S30][S33]. Kesin aralık **JUDGMENT** (kaynaklar sayısal trading tick oranı vermez); mekanizma **CONFIRMED**.
3. **Render katmanı — acil/ertelenebilir ayrımı:**
   - Kullanıcı girdisi (form, tıklama) = acil; fiyat arka plan güncellemeleri = ertelenebilir. `useDeferredValue` "güncellemeleri kesintiye uğratılabilir arka plan render'ına dönüştürür … debounce/throttle'dan farkı sabit gecikme seçtirmemesidir: hızlı cihazda neredeyse anında, yavaş cihazda cihaz hızıyla orantılı gecikir" [S25]. **CONFIRMED**.
   - Sahip olunan state güncellemeleri için `startTransition` (ör. filtre değişince büyük tabloyu yeniden render etmek) [S26]. **CONFIRMED**.
   - Satır/widget bazında `memo`: props değişmedikçe re-render'ı atlar; `useDeferredValue`'nun işe yaraması için alıcı bileşenin memoize olması gerekir (resmî dokümantasyon ve ekosistem rehberleri bu ön koşulu vurgular) [S27][S25]. **CONFIRMED**.
   - "Bayat" içerik göstergesi: React resmî deseni — `isStale = value !== deferredValue` ise soluklaştır/rozet göster [S25]. Canlı veride "son güncelleme" damgasıyla birleştirin (sezgi #1) [S21]. **CONFIRMED**.
4. **Liste katmanı — virtualization:** Emir geçmişi, olay akışı, çok-bot tabloları gibi uzun listelerde yalnız görünür satırları (+ küçük tampon) render edin. web.dev'in resmî rehberi `react-window` ile bunu belgeler; Lighthouse'ın DOM-boyutu uyarı eşiği ekosistem rehberlerinde ~1.400 öğe olarak aktarılır [S34]. Alternatif/resmî kütüphane dokümantasyonu: TanStack Virtual [S34b]. **CONFIRMED**.
5. **Teşhis katmanı:** INP'yi saha verisiyle ölçün (`web-vitals` attribution), 50 ms+ kareleri Long Animation Frames API ile atıflayın (script, render, zorlanmış style/layout ayrımı) [S31][S32][S33]. **CONFIRMED**.

**Anti-pattern (kaynaklı):** Tüm dashboard'u tek state ağacına bağlayıp her tick'te kökten render etmek — React dokümantasyonu deferred değer için "render sırasında yeni nesne yaratıp hemen geçirmeyin, her render'da farklı olacağından gereksiz arka plan render'ı doğurur" uyarısını verir (referans kararlılığı) [S25]; Chrome LoAF dokümantasyonu zorlanmış senkron layout'u (okuma-yazma karıştırma) ölçülebilir gecikme kaynağı olarak belgeler [S33].

### D2. Toast / kalıcı panel / rozet sınırı

**Karar matrisi (her hücre kaynaklı):**

| Durum tipi | Bileşen | Kaynak desteği |
|---|---|---|
| Emir doldu, bot başlatıldı, ayar kaydedildi (geçici onay, eylem gerektirmez) | **Toast/flag** — alt köşe, otomatik kapanır, overlay | Atlassian: "flag'leri onay, uyarı ve **minimal kullanıcı etkileşimi gerektiren** bildirimler için kullanın … ekranın sol altında içeriğin üzerine binerek belirir" [S13]. NN/g bildirim taksonomisi: pasif/bilgilendirici vs eylem-gerektiren [S20] |
| Borsa bağlantısı koptu, API limiti aşıldı, tüm botlar durduruldu (kritik, kalıcı sistem durumu) | **Banner** — üstte, içeriği aşağı iter, kapatılana dek kalır | Atlassian: "banner'ları **yalnızca kritik sistem-düzeyi mesajlar** için kullanın (ör. veri veya işlevsellik kaybı uyarıları)" [S13]; NN/g hata rehberi: "koşullu etiket, toast veya banner minimal etkileşim gerektiren sorunlar için; **modal dikkat ve çözüm gerektiren ağır hatalara saklanmalı**" [S19] |
| Tek botun içindeki durum/uyarı (ör. grid seviyesi doldu, marj %80) | **Section message / satır-içi durum** — ilgili kartın/panelin içinde | Atlassian: "section message'ları ekranın belirli bir bölümünde olan bir şeyi bildirmek için kullanın" [S13]; NN/g: bildirimler "bağlamsal (belirli UI öğesine) veya global (tüm sistem)" olabilir [S20]; NN/g karmaşık-uygulama #7: bağlamı ana ekrandan ayrılmadan göster [S17] |
| Okunmamış olay sayısı | **Rozet (badge) sayacı** — bildirim ikonu üzerinde | M3: "navigation bar'lar hedef ikonunun sağ üst köşesinde rozet gösterebilir; rozetler yeni mesaj sayısı gibi dinamik bilgi içerebilir" [S1]; Carbon: bildirimler üst barda sabit konumda (sağdan 3.) [S10] |
| Olay geçmişi, filtreleme, dışa aktarma | **Kalıcı bildirim merkezi paneli** (sağ panel/drawer) + tüm geçmiş | Carbon right panel: "sağ panel header'daki ikonla çağrılır, o ikona çıpalı kalır, viewport yüksekliğini kaplar, içeriğin üzerinde yüzer; birden çok panel olabilir ama **aynı anda yalnızca biri açık**" [S11]; Shneiderman "history" görevi: "geri alma, tekrar oynatma ve kademeli iyileştirmeyi desteklemek için eylem geçmişini tutun" [S16] |
| Botu durdur / pozisyon kapat (yıkıcı) | **Onay diyaloğu** — özetleyen seçenek etiketleriyle | NN/g: "Yes/No yerine her seçeneğin sonucunu özetleyen yanıtlar verin … yıkıcı eylemleri onay eylemlerinden uzak tutun" [S22][S24] |
| Kullanıcının tanımladığı eşik uyarıları | Uyarı kuralı başına **eşik + sıklık kontrolü** | NN/g (smart-home çalışması, ilke aktarımı): "kullanıcılar uyarıyı tetikleyen kesin koşulları belirleyebilmeli (ör. nem 10 dk boyunca %50 üstündeyse bildir) … tekrar sıklığını kontrol edebilmeli" + "bildirim yorgunluğu oluşunca kritik uyarılar da kaçırılır" [S23a] |

**Sınır kuralı (özet):** Bir bilgi **anınsa ve eylem gerektirmiyorsa** toast; **kalıcı sistem durumuysa** banner; **bir nesneye bağlıysa** o nesnenin içinde section/status; **sayılabilir ve geçmişe sahipse** merkez + rozet; **geri dönülemezse** modal. **Sınıf: CONFIRMED** (taksonomi resmî kaynaklardan birebir kuruldu); trading'e özgü eşik değerleri **JUDGMENT**.

### D3. Kart-özet ↔ detay tablo geçişi (çoklu bot izleme)

**Öneri:** "Botlar" modülü varsayılan olarak **kart grid'i** (bot başına: ad, tür, parite, durum noktası, PnL sparkline, son olay) + görünüm değiştirici ile **yoğun tablo** (sıralanabilir/filtrelenebilir, virtualized). Kart tıklanınca **aynı bağlamda detay** (sağdan açılan drawer veya aynı sayfanın detay seviyesi); tam bot workspace'i ikinci tıklama.

**Dayanak:**
- Shneiderman mantrası: "önce genel görünüm, zoom ve filtre, **sonra talebe-göre detay**" — kart grid'i overview, filtre/facet zoom&filter, drawer details-on-demand'dir; ayrıca "relate" (öğeler arası ilişki: aynı paritedeki botlar) ve "extract" (CSV dışa aktarma) görevleri de taksonominin parçasıdır [S16]. **CONFIRMED**.
- NN/g karmaşık-uygulama #7: "kullanıcıların ana ekrandan/ayrılmadan ikincil bilgiye erişip görüntülemesine izin verin" → drawer, yeni sayfaya zorlamaz [S17]. **CONFIRMED**.
- NN/g anlamsız-bilgi hatası: kart/tablo birincil sütunu insan-okur alan olmalı (bot adı, parite), otomatik üretilen ID'ler geri plana itilmeli [S24]. **CONFIRMED**.
- Few: özet ekranı tek ekrana sığdırılmalı; aşırı detay/hassasiyetten kaçınılmalı → kartlar KPI özetidir, ham emir listesi değildir [S23]. **CONFIRMED**.
- Tablo görünümü gerekli mi? NN/g dashboards: hızlı nicel karşılaştırma için uzunluk-kodlu (bar/sparkline) görselleştirme, alan/açı-kodludan (donut, gauge) üstündür → kart KPI'larında sparkline/bar kullanın [S44]. **CONFIRMED**.
- Kart ↔ tablo arasında hangi görünümün varsayılan olacağı ve geçiş kontrolünün yeri: **JUDGMENT** (kaynaklar doğrudan karşılaştırmaz; "overview→detail" ilkesi ikisini de kapsar).

**Replay/timeline (geçmiş veri):** Shneiderman'ın taksonomisinde "history" birinci sınıf görevdir: "eylemlerin geçmişini tutun — undo, **replay** ve progressive refinement'ı desteklemek için" [S16]. Zaman çizgisi bileşeni, canlı izlemedeki aynı olay-veri şemasını kullanmalı (tutarlılık [S47]) ve scrub sırasında render bütçesi D1'deki erteleme/virtualization kurallarına uymalıdır [S25][S34]. **CONFIRMED (görev varlığı)**; scrub etkileşim tasarımı **JUDGMENT**.

---

## 7. Soru E1 — Açık/Koyu Tema Mimarisi (yalnız görsel mimari)

### 7.1 Öneri: 3 katmanlı token mimarisi

```
Katman 1 — PRIMITIVE (palet):   blue-500: #2f6fed;  gray-900: #16181d; ...
Katman 2 — SEMANTIC (rol):      --color-surface, --color-surface-raised,
                                --color-on-surface, --color-primary, --color-positive,
                                --color-negative, --color-warning, --color-info,
                                --color-border-subtle, ...
Katman 3 — COMPONENT:           --botcard-background: var(--color-surface-raised);
                                --status-dot-live: var(--color-positive); ...

Bağlam:  :root, [data-theme="light"] { --color-surface: #ffffff; ... }
         [data-theme="dark"]        { --color-surface: #121212; ... }
Kaynak-of-truth: W3C DTCG JSON ($value/$type, alias {color.primitive.x}, gruplar)
```

**Kurallar (her biri kaynaklı):**
1. **Bileşenler yalnız Katman-3/Katman-2 token tüketir; asla ham hex kullanmaz.** M3 glossary: "Design tokens: Context — token'ların varsayılan-olmayan değerlere işaret edebildiği koşul kümesi (ör. **dark theme**, dense layout)"; "şema (scheme) renk rollerinin tonlara eşlenmesidir; **tema** birden çok stil/atribütün kombinasyonudur ve kullanıcı bağlamına göre global stilleri ayarlar" — yani dark theme bir *token bağlamıdır*, bileşen-bazlı yeniden yazım değil [S4]. **CONFIRMED**.
2. **Semantik rol adları (surface/on-surface/primary/error…)** M3'ün renk-rolü sisteminden alınır; roller ışık/koyu şemada farklı tonlara eşlenir, bileşen kodu değişmez [S4][S5]. **CONFIRMED**.
3. **Koyu yüzey = saf siyah değil koyu gri.** M2 dark theme: "koyu tema birincil yüzey rengi olarak siyah yerine koyu gri kullanır … önerilen koyu tema yüzey rengi #121212; koyu gri yüzeyler gölge/derinliği ifade edebilir ve göz yorgunluğunu azaltır" [S5]. **CONFIRMED**.
4. **Koyu temada daha açık, desatüre vurgu tonları:** "koyu temada varsayılan doygun palet (900–500) yerine daha açık tonlar (200–50) önerilir … doygun renkler koyu yüzeylerde görsel olarak titreşebilir" [S5]. Trading'e çevirisi: PnL pozitif/negatif ve durum renkleri koyu tema için ayrı ton eşlemesi alır — primitive palet aynı kalır, *rol eşlemesi* değişir. **CONFIRMED (ilke)**; trading renk semantiğinin kendisi kapsam dışı (marka/palet önerisi yapılmıyor).
5. **Yeni modül eklemek temayı bozmaz, çünkü:** yeni modül yalnız Katman-2 rollerini tüketir; Katman-3 component-token'ları yeni modül için türetilir. Bu, Atlassian'ın navigasyon mimarisi dersinin tema karşılığıdır: az sayıda yeniden kullanılabilir primitif + özellik kombinasyonu, yüzlerce özel bileşenin yerine geçer [S8]. Token değişim formatı için W3C DTCG spesifikasyonu (JSON, `$value`/`$type`, alias/referans sistemi, hiyerarşik gruplar) araçlar-arası kaynak-of-truth sağlar [S36]. **CONFIRMED (format/mimari)**; katman adlandırma şeması **JUDGMENT**.
6. **Tema değiştirme mekanizması:** `data-theme` attribute + `prefers-color-scheme` medya sorgusu ile sistem tercihi varsayılanı; geçişte yalnızca custom property değerleri değişir, bileşen yeniden render edilmez. (M3 glossary'deki "tema = kullanıcı bağlamına göre global stil ayarı" tanımıyla uyumlu [S4]; mekanik implementasyon **JUDGMENT**, framework-dışı CSS davranışıdır.)
7. **Grafik/veri-görselleştirme serileri de token'dan beslenir:** chart renkleri Katman-2'den türetilen ayrı bir "data-viz" rol grubu olur; böylece koyu temada seri renkleri tek yerden ayarlanır. (Few pitfall #12 "renk kötüye kullanımı/aşırı kullanımı" ve NN/g treemap renk uyarıları, veri renklerinin sistematik yönetilmesi gereğini destekler [S23][S44a]; "data-viz rol grubu" mimarisi **JUDGMENT**.)

---

## 8. Soru E2 — Performans / Hız (kanıtlanmış frontend desenleri)

| # | Desen | Uygulama (bu üründe) | Kaynak | Sınıf |
|---|---|---|---|---|
| 1 | **Rota + modül bazlı code-splitting** (`React.lazy` + `Suspense`) | Her bölüm (Genel Bakış, Botlar, Piyasa&Veri, Olaylar, Ayarlar) ayrı chunk; ilk açılışta yalnız kabuk + aktif bölüm iner. React resmî referansı `lazy`'yi "bileşen kodunu ağdan yüklenene kadar ertelemek" için, `Suspense`'i fallback gösterimi için belgeler | [S28][S35] | **CONFIRMED** |
| 2 | **Ağır bileşen bazlı lazy loading** | Chart kütüphanesi, replay timeline, monaco-benzeri editörler görünür olmadan yüklenmez; web.dev code-splitting rehberi "kullanıcının ihtiyacı olana dek kodu ertele"yi JS payload azaltmanın birincil yolu olarak belgeler | [S35] | **CONFIRMED** |
| 3 | **Memoization disiplini** (`memo`, `useMemo`, referans kararlılığı) | Tablo satırları, bot kartları memoize; deferred değer alan bileşenler memoize olmak zorunda; render sırasında yeni nesne/array yaratıp child'a geçirmekten kaçın | [S27][S25] | **CONFIRMED** |
| 4 | **Ertelenmiş render** (`useTransition`, `useDeferredValue`) | Filtre/arama değişiminde büyük liste güncellemesi transition; canlı fiyat arka plan güncellemeleri deferred + `isStale` göstergesi | [S25][S26] | **CONFIRMED** |
| 5 | **Virtualization** | Emir/olay geçmişleri, çok-bot tabloları, replay olay listeleri: `react-window`/TanStack Virtual ile yalnız görünür aralık + tampon | [S34][S34b] | **CONFIRMED** |
| 6 | **INP bütçesi ve saha ölçümü** | Hedef: etkileşimlerin 75. yüzdeliğinde ≤200 ms ("iyi"); Mart 2024'ten beri FID'ın yerine Core Web Vital; `web-vitals` attribution + CrUX ile sahada ölç | [S30][S31] | **CONFIRMED** |
| 7 | **LoAF teşhisi** | 50 ms+ kareleri Long Animation Frames API ile atıfla (script süresi, render süresi, zorlanmış style/layout, rAF callback'leri); eşik seçimi INP 200 ms bütçesinin altı (ör. 100 ms) | [S32][S33] | **CONFIRMED** |
| 8 | **Layout thrashing'ten kaçınma** | DOM okumalarını yazımlardan önce grupla; LoAF `forcedStyleAndLayoutDuration` ile izle | [S32][S33] | **CONFIRMED** |
| 9 | **Ağır hesabı worker'a taşıma** | Backtest/replay yeniden-hesaplama, büyük grid optimizasyonu ana thread'i bloklamaz (Chrome rehberi: uzun script yürütümü → "daha küçük görevlere böl, worker kullan") | [S33a] | **CONFIRMED** |
| 10 | **Tick pipeline'ı** (throttle → batch → seçici yayın) | Bkz. §6.1; 50 ms uzun-görev eşiği ve 200 ms INP bütçesi tasarım kısıtıdır | [S16][S30][S33] | **CONFIRMED (kısıt)**; aralık değeri **JUDGMENT** |
| 11 | **`content-visibility` / DOM boyutu disiplini** | Ekran-dışı panel bölümlerinde render işini atla; ekosistem rehberleri Lighthouse DOM-boyutu uyarı eşiğini (~1.400 öğe) aktarır | [S34c] | **CONDITIONAL** (web.dev/Chrome birincil metni bu turda doğrudan çekilmedi; mekanizma Chrome platform dokümantasyonunda mevcut) |
| 12 | **Yükleme geri bildirimi** | 2–10 sn işlemler için spinner, 10 sn+ için yüzde-progress bar (NN/g uygulama hataları); 1 sn üstü "busy" imleci | [S24][S47] | **CONFIRMED** |

---

## 9. Kaynak Listesi (tam künye)

> Erişim tarihi aksine belirtilmedikçe **21.09.2026**'dır. "Yayın" alanı, kaynağın kendisinde/arama dizininde doğrulanabilen tarihi gösterir; yalnızca erişim tarihi doğrulanabilenlerde "erişim" yazılmıştır.

### Nielsen Norman Group (NN/g)
- **[S12]** Nielsen, J. — *Progressive Disclosure* — https://www.nngroup.com/articles/progressive-disclosure/ — Yayın: 03.12.2006. Desteklediği iddialar: PD tanımı; "ilk ekranda yalnız en önemli seçenekler, uzmanlaşmışlar talep üzerine"; "2 seviyeyi aşan disclosure tasarımları tipik olarak düşük kullanılabilirliğe sahiptir"; ilerleme mekaniğinin belirginliği ve güçlü bilgi kokusu kriteri; "sık ihtiyaç duyulan her şey ilk seviyede açılmalı"; PD'nin öğrenilebilirlik, verimlilik ve hata oranını iyileştirmesi; staged disclosure (adımlı/sıralı) ile progressive disclosure (hiyerarşik) ayrımı.
- **[S17]** NN/g — *8 Design Guidelines for Complex Applications* — https://www.nngroup.com/articles/complex-application-design/ — Güncel sürüm: 02.02.2024 (erişim). Desteklediği iddialar: #7 birincil↔ikincil bilgi geçişi (ana ekrandan ayrılmadan ek bilgi); #8 önemli bilginin görsel belirginliği, süslemenin görsel aramayı bozması.
- **[S24]** NN/g — *Top 10 Application-Design Mistakes* — https://www.nngroup.com/articles/top-10-application-design-mistakes/ — Sürüm: 18.02.2019 (erişim). Desteklediği iddialar: junk-drawer menü antipattern'i ("…" / "More" etiketlerinin düşük kokusu); anlamsız ID'lerin birincil sütun yapılması; progress göstergesi eşikleri (2–10 sn spinner, >10 sn progress bar); yıkıcı eylem/onay yakınlığı hatası.
- **[S47]** NN/g — *Top 10 Application-Design Mistakes of 2008* — https://www.nngroup.com/articles/top-10-application-design-mistakes-2008/ — Sürüm: 17.02.2019 (erişim). Desteklediği iddialar: "aynı şey için aynı ad aynı yerde" tutarlılık kuralı; display inertia; 1 sn üstü busy imleci; varsayılan değer sunmama hatası; bilginin nasıl kullanılacağını belirtmeme hatası.
- **[S44]** NN/g — *Dashboards: Making Charts and Graphs Easier to Understand* — https://www.nngroup.com/articles/dashboards-preattentive/ — Sürüm: 06.01.2018 (erişim). Desteklediği iddialar: operasyonel ↔ analitik dashboard ayrımı; preattentive işleme; uzunluk-kodlu (lineer) grafiklerin alan/açı-kodlulardan (donut, gauge, treemap) hızlı ve doğru karşılaştırma için üstünlüğü.
- **[S44a]** NN/g — *Treemaps: Data Visualization of Complex Hierarchies* — https://www.nngroup.com/articles/treemaps/ — Sürüm: 28.09.2019 (erişim). Desteklediği iddia: renk-kodlu nicel veride ikincil sinyal ve sistemli renk yönetimi gereği.
- **[S40]** Nielsen, J. — *Mega Menus Work Well for Site Navigation* — https://www.nngroup.com/articles/mega-menus-work-well/ — Güncellenmiş sürüm: 27.06.2023 (erişim; orijinal 2008). Desteklediği iddialar: çok sayıda seçenek için iki-boyutlu, gruplu, kaydırmasız menüler; "görmek hatırlamaktan iyidir"; düzenli dropdown'ların büyük sitelerde seçenekleri gizlemesi.
- **[S39]** Cardello, J. & Whitenton, K. — *Killing Off the Global Navigation: One Trend to Avoid* — https://www.nngroup.com/articles/killing-global-navigation-one-trend-avoid/ — Yayın: 09.02.2014. Desteklediği iddia: üst-düzey kategorileri dropdown arkasına gizlemek keşfedilebilirliği düşürür; çoğu site üst kategorileri doğrudan göstermekten yararlanır.
- **[S38]** NN/g — *Hamburger Menus and Hidden Navigation Hurt UX Metrics* — https://www.nngroup.com/articles/hamburger-menus/ — Sürüm: 31.01.2020 (erişim; orijinal 2016). Desteklediği iddialar: gizli navigasyon görünür/karma navigasyona göre anlamlı ölçüde daha az kullanılır; düşük belirginlik, düşük bilgi kokusu, ek etkileşim maliyeti.
- **[S6]** NN/g — *Breadcrumbs: 11 Design Guidelines for Desktop and Mobile* — https://www.nngroup.com/articles/breadcrumbs/ — Güncellenmiş sürüm (erişim: 21.09.2026). Desteklediği iddialar: breadcrumb'ın wayfinding işlevi; küresel/yerel navigasyonun yerini almaması (tamamlaması); yalnız gerçek sayfa düğümlerini içermesi; 1995'ten beri önerildiği.
- **[S7]** Nielsen, J. — *Breadcrumb Navigation Increasingly Useful* — https://www.nngroup.com/articles/breadcrumb-navigation-useful/ — Yayın: 09.04.2007. Desteklediği iddialar: konum-tabanlı (hiyerarşi) breadcrumb, tarihçe-tabanlı değil; tek tıkla üst seviyelere erişim; testlerde hiç sorun çıkarmaması; az yer kaplaması.
- **[S42]** Budiu, R. — *Search Is Not Enough: Synergy Between Navigation and Search* — https://www.nngroup.com/articles/search-not-enough/ — Yayın: 07.09.2014. Desteklediği iddialar: aramanın arama-uzayı bilgisi gerektirmesi; navigasyonun tanıma>hatırlama sağlaması ve arama uzayının yapısını öğretmesi; facetlerin aramayı navigasyona dönüştürmesi.
- **[S25a]** NN/g — *Information Scent: How Users Decide Where to Go Next* — https://www.nngroup.com/articles/information-scent/ — Sürüm: 24.01.2024 (erişim). Desteklediği iddia: kullanıcıların bağlantı değeri tahmininin etiket+bağlam+ön bilgiye dayandığı; etiketlemenin navigasyon başarısındaki rolü.
- **[S45]** NN/g — *Information Foraging: A Theory of How People Navigate on the Web* — https://www.nngroup.com/articles/information-foraging/ — Sürüm: 18.09.2024 (erişim). Desteklediği iddia: bilgi kokusu teorisinin navigasyon tasarımına uygulanması.
- **[S41]** Sunwall, E. — *Tabs, Used Right* — https://www.nngroup.com/articles/tabs-used-right/ — Yayın: 02.08.2024. Desteklediği iddialar: sayfa-içi ↔ gezinme sekmelerinin karıştırılmaması; tek sıra sekme; eşit-önemsiz içerik ayrımı; aynı anda görme ihtiyacında sekme kullanılmaması; tanımlayıcı etiketler; tutarlılık için tasarım sistemi.
- **[S15]** NN/g — *Wizards: Definition and Design Recommendations* — https://www.nngroup.com/articles/wizards/ — Yayın: 27.06.2017 (NN/g duyurusu ile doğrulandı); güncellenmiş sürüm 24.01.2024 (erişim). Desteklediği iddialar: sihirbaz tanımı; "acemi kullanıcılar ve seyrek süreçler (ör. yapılandırma/kurulum) için kullanın"; hata olasılığını azaltması; dallanmayla yalnız ilgili adımların gösterilmesi; dezavantaj: kullanıcı kontrolünü/yaratıcılığını sınırlaması, sık kullanımda sinir bozuculuğu; adımların kendi-kendine-yeterliliği; yardımın sihirbazın yanında açılması; Review&Save olanağı.
- **[S46]** NN/g — *Few Guesses, More Success: 4 Principles to Reduce Cognitive Load in Forms* — https://www.nngroup.com/articles/4-principles-reduce-cognitive-load/ — Yayın: 17.07.2025. Desteklediği iddialar: form içi progressive disclosure; dallanma mantığının dinamik alan gösterimi olarak tanımı; soru sırası ilkeleri (familiarity/priority/dependency/complexity); görsel hiyerarşi ve ortak-bölge gruplaması; çok-sayfalı formlarda önceden şeffaflık (süre, gereken belgeler).
- **[S48]** Budiu, R. — *Accordions on Mobile* — https://www.nngroup.com/articles/mobile-accordions/ — Yayın: 31.05.2015. Desteklediği iddialar: akordeonun "mini-IA/büyük resim" işlevi; form adımlarının akordeonla tek sayfada iletilmesi; yön-kaybı ve aşırı kaydırma riskleri; kalıcı başlık ve jump-link çözümleri.
- **[S19]** Neusesser, T. & Sunwall, E. — *Error-Message Guidelines* — https://www.nngroup.com/articles/error-message-guidelines/ — Yayın: 14.05.2023. Desteklediği iddia: etki-temelli hata tasarımı; koşullu etiket/toast/banner ↔ modal (yalnız ağır, çözüm gerektiren hatalar) ayrımı.
- **[S50]** NN/g — *10 Design Guidelines for Reporting Errors in Forms* — https://www.nngroup.com/articles/errors-forms-design-guidelines/ — Sürüm: 12.12.2024 (erişim). Desteklediği iddialar: inline doğrulama tercihi; hata mesajının alan yanında kalması; renk+ikon; modal/onay diyaloğunun seyrek kullanımı; özetin tek gösterge olmaması; input tamamlanmadan doğrulamama.
- **[S20]** NN/g — *Indicators, Validations, and Notifications* — https://www.nngroup.com/articles/indicators-validations-notifications/ — (erişim: 21.09.2026; üçüncül alıntıyla doğrulandı). Desteklediği iddialar: bildirim tanımı (sistem durumu değişimi/kullanıcıyla ilgili olabilecek olay); bağlamsal ↔ global bildirim; eylem-gerektiren ↔ pasif bildirim ayrımı.
- **[S22]** NN/g — *Confirmation Dialogs Can Prevent User Errors — If Not Overused* — https://www.nngroup.com/articles/confirmation-dialog/ — Sürüm: 07.08.2026 (erişim). Desteklediği iddialar: Yes/No yerine sonucu özetleyen seçenek etiketleri; PD ile "daha fazlasını öğren" deseni; varsayılan-Yes'ten kaçınma.
- **[S18]** Nielsen, J. — *Response Times: The 3 Important Limits* — https://www.nngroup.com/articles/response-times-3-important-limits/ — Yayın: 1993; güncelleme 2014 (akademik alıntılarla doğrulandı). Desteklediği iddialar: 0,1 sn (anlık), 1 sn (kesintisiz dikkat), 10 sn (dikkat limiti + progress göstergesi) eşikleri.
- **[S21]** Nielsen, J. — *10 Usability Heuristics for User Interface Design* — https://www.nngroup.com/articles/ten-usability-heuristics/ — Yayın: 24.04.1994; güncelleme 2024. Desteklediği iddialar: #1 sistem durumunun görünürlüğü; #2 gerçek dünya eşleşmesi; #5 hata önleme; #6 tanıma>hatırlama; #7 esneklik/verimlilik — "acemiye görünmez hızlandırıcılar uzmanı hızlandırır"; #8 estetik ve minimalist tasarım.
- **[S23a]** NN/g — *Designing Useful Smart Home Notifications* — https://www.nngroup.com/articles/smart-home-notifications/ — Yayın: 21.02.2026. Desteklediği iddialar (ilke aktarımı, farklı alan): aciliyet-sunum eşleşmesi; bildirim yorgunluğu; eşik/tür/sıklık kontrolünün kullanıcıya verilmesi; kanal seçimi. *(Trading bağlamına aktarım CONDITIONAL'ddır.)*
- **[S51]** NN/g — *Mobile Subnavigation* — https://www.nngroup.com/articles/mobile-subnavigation/ — Sürüm: 20.12.2017 (erişim). Desteklediği iddia: ana menü içi akordeon alt-menülerin düşük etkileşim maliyeti ve tüm yolları desteklemesi.
- **[S49]** NN/g — *Does Your Form Really Need a Dropdown List?* — https://www.nngroup.com/articles/dropdown-list/ — Sürüm: 16.07.2026 (erişim). Desteklediği iddialar: dropdown için ~5–15 seçenek aralığı; 15+ için filtreli combobox; ikincil alanları gizlemede dropdown'ın yoğun yönetim arayüzlerinde faydası.

### Resmî tasarım sistemleri
- **[S1]** Google — *Material Design 3: Navigation bar — Guidelines* — https://m3.material.io/components/navigation-bar/guidelines — (erişim: 21.09.2026). Desteklediği iddialar: 3–5 hedef; "5'ten fazla navigasyon öğesi koymayın — çakışma ve çeviri payı sorunu; tabs veya modal expanded navigation rail düşünün"; navigasyon = farklı sayfalar, tabs = sayfa içi ilişkili içerik; rozet desteği (dinamik sayı); aktif göstergenin yalnız aktif hedefte olması; hedef konumlarının sabitliği.
- **[S2]** Google — *Material Design 2: Understanding navigation* — https://m2.material.io/design/navigation/understanding-navigation.html — (erişim: 21.09.2026). Desteklediği iddialar: lateral/forward navigasyon tanımları; bileşen-hedef sayısı tablosu (drawer: 5+ üst hedef, tüm cihazlar; bottom nav: 3–5, mobil; tabs: 2+, her seviye); birincil navigasyon bileşeninin tüm üst-düzey hedeflere erişim vermesi.
- **[S4]** Google — *Material Design 3: Glossary (Material A–Z)* — https://m3.material.io/foundations/glossary — Yayın: 27.10.2021 (erişim güncel). Desteklediği iddialar: "design tokens: context" tanımı (dark theme bir token bağlamıdır); scheme ↔ theme ayrımı ("dark theme, renk ötesi tasarım kararlarını — elevation, state — içerir"); baseline scheme.
- **[S5]** Google — *Material Design 2: Dark theme* — https://m2.material.io/design/color/dark-theme.html — (erişim: 21.09.2026). Desteklediği iddialar: koyu gri (önerilen #121212) yüzey, saf siyah değil; gölge/derinlik ifadesi ve göz yorgunluğu gerekçesi; koyu temada açık tonlar (200–50) ve desatüre vurgular; doygun renklerin titreşim sorunu.
- **[S8]** Atlassian — *Designing Atlassian's new navigation* (Inside Atlassian / Design blog) — https://www.atlassian.com/blog/design/designing-atlassians-new-navigation — Yayın: 28.02.2025 (Medium sürümü: 25.11.2024). Desteklediği iddialar: birincil ürün navigasyonunun üst bardan sidebar'a taşınması ve gerekçeleri (dikey alan/bilgi yoğunluğu, kuşbakışı görünüm, çoklu araç aşinalığı); üst barın arama/oluştur gibi evrensel eylemlere ayrılması; tasarım prensipleri (öngörülebilirlik, kullanıcı kontrolü/özelleştirme, "yeni kullanıcı için kademeli aç, güç kullanıcı işlevini koru"); 16 kullanıcıyla araştırma → Starred & Recent ihtiyacı; yüzlerce bileşen/23 tutarsızlık → 3 yeniden kullanılabilir bileşene konsolidasyon; hover'da tutarlı item-eylemleri; çökertme (collapse) deseninin testle iyileştirilmesi.
- **[S9]** Atlassian — *Navigation design guidelines (Jira Cloud platform)* — https://developer.atlassian.com/cloud/jira/platform/navigation/ — Sürüm: 19.06.2025 (erişim). Desteklediği iddialar: derin IA için bağlamsal sidebar deseni; tek giriş noktası önerisi; derin sayfalar için uygulama-içi navigasyon + progressive disclosure; iç içe sidebar (nesting) deseninden kaçınma; ilk öğenin landing sayfası olması; başlık/ayraç ile gruplama (ikisi birlikte değil).
- **[S13]** Atlassian Design — *Designing messages (Foundations → Content)* — https://atlassian.design/foundations/content/designing-messages — (erişim: 21.09.2026). Desteklediği iddialar: banner = yalnız kritik sistem-düzeyi mesaj, üstte, içeriği iter; flag = onay/uyarı/kabul, minimal etkileşim, sol altta overlay; section message = ekranın belirli bölümüne bağlı olay; inline message = gereken eylem/önemli bilgi; renk+ikon ile aciliyet kodlaması.
- **[S10]** IBM — *Carbon Design System: UI shell header (usage)* — https://carbondesignsystem.com/components/UI-shell-header/usage/ — Sürüm: 22.05.2023 (erişim güncel). Desteklediği iddialar: shell kavramı ("platformdaki tüm ürünlerce paylaşılan, ürünler arası kalıcı etkileşim desenleri"); soldan sağa = üründen globale; header linkleri + sub-menu (chevron, tıkla açılır, link değildir); ikon yerleşim sırası (arama en solda, bildirim sağdan 3., hesap sağdan 2., switcher en sağda ve kaymaz); dar ekranda sol panel/hamburger'a çökme; switcher tanımı (ürünler/sistemler arası geçiş; son kullanılan/sık kullanılan/tüm uygulamalar).
- **[S11]** IBM — *Carbon Design System v10: UI shell right panel (usage)* — https://v10.carbondesignsystem.com/components/UI-shell-right-panel/usage/ — (arşivlenmiş v10 dokümanı; erişim: 21.09.2026). Desteklediği iddialar: sağ panelin header ikonuyla çağrılması ve ikona çıpalı kalması; tam viewport yüksekliği, içerik üstünde yüzme; birden çok panel tanımlanabilse de aynı anda yalnız birinin açık olması; switcher'ın sağ panelde yaşaması.
- **[S3]** Microsoft — *Fluent 2 Design System: Nav (React) — Usage* — https://fluent2.microsoft.design/components/web/react/core/nav/usage — (erişim: 21.09.2026). Desteklediği iddialar: "Nav yalnızca bir seviye iç içe geçmeyi destekler … daha derin/karmaşık hiyerarşi için Tree kullanın"; "arama ve sabitleme tutarlı navigasyonun ikamesi değildir"; nav kategorilerinin akordeon gibi davranması ve link olmaması; etiketlerin kısa/taranabilir/düz dilde olması; taksonomi ve sıranın platformlar arası tutarlılığı; nav düğümlerinde ikincil eylem minimizasyonu (overflow menü); ikon+girinti ile hiyerarşi.
- **[S3a]** Microsoft — *Fluent 2 Design System: Accessibility — Structure, hierarchy, and navigation* — https://fluent2.microsoft.design/accessibility — (erişim: 21.09.2026; yalnız yapısal bölüm). Desteklediği iddialar: mantıksal/öngörülebilir bilgi organizasyonu; taranabilir başlık hiyerarşisi ile gezinme verimliliği. *(Kontrast/ekran-okuyucu bölümleri bilinçli olarak kullanılmamıştır.)*
- **[S14]** Shopify — *Polaris: Fundamentals* — https://polaris-react.shopify.com/content/fundamentals — (erişim: 21.09.2026; Polaris'in eski sürüm dokümanı). Desteklediği iddialar: "çok parçalı görevleri sindirilebilir adımlara bölün (aka progressive disclosure)"; eyleme odaklanma; tasarım (punto, konum) ile önem iletme.

### W3C
- **[S43]** W3C — *ARIA Authoring Practices Guide (APG)* — https://www.w3.org/WAI/ARIA/apg/ — (yaşayan doküman; erişim: 21.09.2026; yalnız yapısal desenler). İlgili desenler: Tabs (https://www.w3.org/WAI/ARIA/apg/patterns/tabs/), Combobox (https://www.w3.org/WAI/ARIA/apg/patterns/combobox/), Treeview (https://www.w3.org/WAI/ARIA/apg/patterns/treeview/), Dialog/Modal (https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/).
- **[S43a]** W3C — *APG: Disclosure (Show/Hide) Pattern + Disclosure Navigation Menu örneği* — https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/ ve https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/examples/disclosure-navigation/ — (erişim: 21.09.2026). Desteklediği iddialar (yapısal): disclosure düğmesinin `aria-expanded`/`aria-controls` taşıması; navigasyon menülerinin disclosure düğümleriyle kurulması; `aria-current="page"` ile geçerli konumun işaretlenmesi; Escape ile kapanma; kart-içi disclosure varyantı (zengin özetli açılır kart).
- **[S36]** W3C Design Tokens Community Group — *Design Tokens Format Module* — https://tr.designtokens.org/format/ — CG-DRAFT (erişim: 21.09.2026). Desteklediği iddialar: token'lar için standart JSON formatı; `$value`/`$type`/`$description` özellikleri; alias/referans sistemi; hiyerarşik gruplar; platform-bağımsız değişim formatı olma amacı.

### Akademik / uzman literatürü
- **[S16]** Shneiderman, B. — *The Eyes Have It: A Task by Data Type Taxonomy for Information Visualizations* — IEEE Symposium on Visual Languages, 1996 — https://ieeexplore.ieee.org/document/545307/ ; tam metin: https://hci.ucsd.edu/220/EyesHaveIt.pdf — Yayın: 1996. Desteklediği iddialar: Görsel Bilgi-Arama Mantrası ("önce genel görünüm, zoom ve filtre, sonra talebe-göre detay"); 7 görev taksonomisi: overview, zoom, filter, details-on-demand, relate, **history** ("undo, replay ve kademeli iyileştirmeyi desteklemek için eylem geçmişini tutun"), **extract** (alt-koleksiyonların çıkarılması); "on binlerce öğe gösterilse bile 100 ms altı güncelleme hedeftir"; geçici veri tipinde (temporal) görselleştirme.
- **[S23]** Few, S. — *Common Pitfalls in Dashboard Design* (white paper, Perceptual Edge) — https://www.perceptualedge.com/articles/Whitepapers/Common_Pitfalls.pdf — Yayın: Şubat 2006. Desteklediği iddialar: 13 pitfall; #1 "tek ekran sınırını aşmak" (bağlantıların scroll arkasında kaybolması); #3 "aşırı detay/hassasiyet göstermek"; #12 "rengin kötüye/aşırı kullanımı"; dashboard'un tek bakışta iletişim hedefi.

### React resmî dokümantasyonu
- **[S25]** React — *useDeferredValue* — https://react.dev/reference/react/useDeferredValue — (yaşayan doküman; erişim: 21.09.2026). Desteklediği iddialar: UI'ın bir bölümünün güncellenmesini erteleme; deferred değerin "geride kalması" ve kesilebilir arka plan render'ı; `isStale` göstergesi deseni; debounce/throttle'dan farkı (sabit gecikme yok, cihaz hızına orantılı); render sırasında yaratılan yeni nesnelerin gereksiz arka plan render'ına yol açması (referans kararlılığı koşulu).
- **[S26]** React — *useTransition* — https://react.dev/reference/react/useTransition — (erişim: 21.09.2026). Desteklediği iddia: acil olmayan state güncellemelerini transition olarak işaretleme; `isPending` ile bekleyen durum gösterimi.
- **[S27]** React — *memo* — https://react.dev/reference/react/memo — (erişim: 21.09.2026). Desteklediği iddia: props değişmedikçe yeniden render'ın atlanması (seçici re-render temeli).
- **[S28]** React — *lazy* ve *Suspense* — https://react.dev/reference/react/lazy ; https://react.dev/reference/react/Suspense — (erişim: 21.09.2026). Desteklediği iddia: bileşen kodunun ilk kez render edilene dek yüklenmesinin ertelenmesi (code-splitting) ve yükleme sırasında fallback gösterimi.
- **[S29]** React — *useSyncExternalStore* — https://react.dev/reference/react/useSyncExternalStore — (erişim: 21.09.2026). Desteklediği iddia: React dışında yönetilen (ör. WebSocket fiyat feed'i) harici store'lara abone olma; snapshot referans kararlılığı koşulu.

### web.dev / Chrome resmî dokümantasyonu
- **[S30]** web.dev (Google Chrome ekibi) — *Interaction to Next Paint (INP)* — https://web.dev/articles/inp — (erişim: 21.09.2026). Desteklediği iddialar: INP'nin Mart 2024'te FID'ın yerine Core Web Vital olduğu; "iyi" eşiğin 75. yüzdelikte ≤200 ms olduğu.
- **[S31]** web.dev — *Optimize INP* / *Find slow interactions in the field* — https://web.dev/articles/optimize-inp ; https://web.dev/articles/find-slow-interactions-in-the-field — Yayın (ikinci): 07.06.2024. Desteklediği iddialar: INP'nin üç fazı (input delay, processing, presentation delay); `web-vitals` attribution + LoAF ile saha teşhisi; uzun rAF callback'leri ve zorlanmış style/layout'un sunum gecikmesine katkısı.
- **[S32]** web.dev — *Long Animation Frames API* ilgili rehber içerikleri — https://web.dev/articles/find-slow-interactions-in-the-field — Yayın: 07.06.2024. Desteklediği iddia: LoAF'un INP hata ayıklamasının altında yatan API olduğu; script atfı (invoker, kaynak URL, fonksiyon).
- **[S33]** Chrome for Developers — *Long Animation Frames API* — https://developer.chrome.com/docs/web-platform/long-animation-frames — Sürüm: 14.10.2024. Desteklediği iddialar: 50 ms+ kare = "long animation frame"; `blockingDuration`, `forcedStyleAndLayoutDuration` ölçümleri; "iyi INP = tüm etkileşimlerin ≤200 ms yanıtlanması"; 100 ms raporlama eşiği örneği.
- **[S33a]** Chrome for Developers / webperf ekosistemi — uzun görev çözüm rehberi (LoAF dokümantasyonunun çözüm bölümü) — https://developer.chrome.com/docs/web-platform/long-animation-frames — Desteklediği iddia: uzun script yürütümü için "daha küçük görevlere bölme, worker kullanma" çözümü.
- **[S34]** web.dev — *Virtualize long lists with react-window* — https://web.dev/articles/virtualize-long-lists-react-window — (erişim: 21.09.2026; orijinal yayın 2021). Desteklediği iddia: yalnız görünür öğeleri (+tampon) render eden windowing/virtualization tekniğinin büyük liste/tablolar için resmî öneri olması.
- **[S34b]** TanStack — *TanStack Virtual (resmî kütüphane dokümantasyonu)* — https://tanstack.com/virtual/latest — (erişim: 21.09.2026). Desteklediği iddia: framework-agnostic virtualization primitive'leri (`useVirtualizer`, estimateSize, overscan).
- **[S34c]** Ekosistem performans kontrol listesi (ikincil; mekanizma birincil Chrome/web.dev dokümanlarına dayanır) — *Frontend Checklist: Virtualize long lists and tables* — https://frontendchecklist.io/rules/performance/list-virtualization — (erişim: 21.09.2026). Aktardığı iddialar: ~1.400 DOM öğesi Lighthouse uyarı eşiği; `content-visibility: auto` ile ekran-dışı render'ın atlanması; windowing'te öğe boyutu/klavye erişiminin korunması. **Bu tek kaynak ikincildir; ilgili öneri CONDITIONAL sınıflandırılmıştır.**
- **[S35]** web.dev — *Reduce JavaScript payloads with code splitting* — https://web.dev/articles/reduce-javascript-payloads-with-code-splitting — (erişim: 21.09.2026; orijinal yayın 2019). Desteklediği iddia: code-splitting'in JS başlangıç yükünü azaltmanın birincil yolu olduğu; rota-bazlı ve bileşen-bazlı bölme.

---

## 10. Karar Sınıflandırması — Özet Tablo

### CONFIRMED (doğrudan kaynak destekli)
1. Üst-düzey navigasyon hedefi pratik sınırı 3–5; 5+ için drawer/yan panel; navigasyonda tek iç içe seviye (ağaç gerekiyorsa ayrı Tree bileşeni) [S1][S2][S3].
2. Birincil navigasyonun görünür kalması; üst düzey kategorilerin dropdown/hamburger arkasına gizlenmemesi [S38][S39].
3. Üst barın evrensel eylemlere (arama, oluştur, bildirim, hesap, switcher) ayrılması; switcher'ın en sağda sabit konumu [S8][S10].
4. Konum-tabanlı breadcrumb'ın kalıcı bağlam göstergesi olarak kullanımı; navigasyonun yerini almaması [S6][S7].
5. Progressive disclosure'ın alan/bölüm seviyesinde, en fazla 2 seviye derinlikle uygulanması; ilerleme yolunun belirgin ve tek mekanizmalı olması [S12].
6. Sihirbazın "kurulum/seyrek süreç + acemi kullanıcı" endikasyonu; adımların kendi-kendine-yeterliliği; yardımın yanda açılması; incele-kaydet olanağı [S15].
7. Form içi koşullu dallanma ve soru sırası ilkeleri (familiarity→priority→dependency→complexity) [S46].
8. Inline doğrulama; hata mesajının alan yanında kalması; modal'ın yalnız ağır hatalara/yıkıcı onaylara saklanması; onay seçeneklerinin sonucu özetlemesi [S19][S50][S22].
9. Bildirim taksonomisi: flag/toast (geçici, minimal etkileşim) ↔ banner (kritik, kalıcı, sistem-düzeyi) ↔ section message (bağlamsal) ↔ rozet (dinamik sayı) ↔ sağ panel (merkez/switcher) [S13][S20][S1][S11].
10. Overview → zoom/filter → details-on-demand akışı; history/replay ve extract'in birinci sınıf görevler olması; <100 ms görsel güncelleme hedefi [S16].
11. Dashboard'un tek ekrana sığdırılması; aşırı hassasiyetten kaçınılması; hızlı nicel karşılaştırmada uzunluk-kodlu grafik üstünlüğü [S23][S44].
12. Anlamsız ID'lerin birincil sütun yapılmaması; junk-drawer menülerden kaçınılması; "aynı şey için aynı ad aynı yerde" [S24][S47].
13. Dark theme'in bir token *bağlamı* olduğu; koyu gri yüzey (#121212 önerisi); koyu temada açık/desatüre vurgu tonları [S4][S5].
14. W3C DTCG token formatının ($value/$type, alias, grup) değişim standardı olarak kullanılabileceği [S36].
15. INP ≤200 ms bütçesi; 50 ms uzun-kare eşiği; LoAF ile atıf; zorlanmış layout'tan kaçınma [S30][S32][S33].
16. `useDeferredValue`/`useTransition`/`memo`/`useSyncExternalStore`/`lazy`+`Suspense` ile seçici-ertelenmiş render ve code-splitting desenleri [S25–S29].
17. Uzun liste/tabloların virtualize edilmesi [S34][S34b].
18. Yükleme geri bildirim eşikleri (spinner 2–10 sn, progress bar >10 sn; busy imleci >1 sn) [S24][S47].
19. Uzman hızlandırıcıların (klavye kısayolları, komut paleti) "acemiye görünmez, uzmanı hızlandırır" ilkesiyle meşruiyeti — ancak görünür navigasyonun ikamesi olmaması [S21][S42][S3].

### CONDITIONAL (kaynak ilkeyi destekler; uygulama bağlama bağlı)
1. **Komut paleti:** varlığı heuristic #7 ve Atlassian üst-bar-arama deseniyle desteklenir; ancak "bu üründe verimliliği artırdığı" iddiası kendi kullanıcı testiniz olmadan kurulamaz; palet, ARIA combobox yapısıyla implemente edilmelidir [S21][S8][S42][S43].
2. **Strateji türlerinin facet olarak mı ikinci-seviye menü olarak mı sunulacağı:** zihinsel model kart sıralama/tree testiyle doğrulanmalı; Fluent'in "tutarlı taksonomi" ve NN/g'nin facet-övgüsü her iki yolu da açık bırakır [S3][S42].
3. **Kart ↔ tablo varsayılanı ve drawer genişliği:** overview→detail ilkesi CONFIRMED, ama hangi görünümün varsayılan olacağı kullanıcı profiline (izleyici vs. operatör) bağlıdır [S16][S17].
4. **Form düzeni seçimi (sihirbaz vs. tek sayfa):** "ilk kurulum sihirbaz, düzenleme tek sayfa" bölüşümü NN/g endikasyonlarından türetilir; kullanıcıların kurulum sıklığı gerçekten düşükse CONFIRMED'a yaklaşır, sık bot açılıp kapanıyorsa tek-sayfa ağırlığı artmalıdır [S15][S46].
5. **Akordeon-disclosure'un masaüstü yoğun formlarda kullanımı:** kanıt temeli mobil çalışmadır; masaüstünde "içerik bölümler arası kombinasyon gerektirmiyorsa" koşuluyla geçerlidir [S48][S12].
6. **Uyarı eşik/sıklık kontrolleri:** akıllı-ev bildirim çalışmasının ilkelerinin trading uyarılarına aktarımı alan-dışı genellemedir; yön güçlü ama doğrudan kanıt değildir [S23a].
7. **`content-visibility` ve ~1.400 DOM eşiği:** birincil Chrome/web.dev metni bu turda ayrıca çekilmedi; ikincil derleme kaynaklıdır — kendi ölçümünüzle doğrulayın [S34c].
8. **Çoklu hesap/borsa workspace'i:** Carbon switcher deseni CONFIRMED; "borsa bazlı workspace" ürün semantiği, çok-borsalı kullanım gerçekten varsa anlamlıdır [S10].

### JUDGMENT (kaynakların kesin cevabı yok — tasarımcı kararı, gerekçeli)
1. **Bölüm adları ve 5'li kompozisyon** ("Genel Bakış / Botlar & Stratejiler / Piyasa & Veri / Olaylar & Denetim / Ayarlar"): kaynaklar "junk-drawer'dan kaçın, 5'i aşma, kullanıcı dilini kullan" der ama bu ürün için doğru taksonomiyi vermez. Doğrulama: card sorting + tree testing.
2. **Bot-detay sekme seti ve sayısı** (Özet/Pozisyonlar/Emirler/Ayarlar/Günlük/Performans): "tek sıra, kısa etiket, karışık tip yasağı" kısıtları CONFIRMED; kesin bölüşüm judgment.
3. **Risk alanlarının "asla gizlenmez" listesinin içeriği** (§4.3): ilkeler CONFIRMED (sık-needed önde olsun, hata önle), liste türetilmiş judgment; finansal-regülasyon bağlamı ayrıca hukuki gözden geçirme gerektirebilir.
4. **Canlı önizleme panelinin konumu/yoğunluğu** (sağ yapışkan sütun; hangi türev metriklerin gösterileceği): <100 ms ve "yalnız ilgili bilgiyi göster" ilkeleri CONFIRMED; kompozisyon judgment.
5. **Tick throttle aralığı (100–250 ms) ve batch penceresi:** eşikler (50 ms uzun görev, 200 ms INP, 100 ms görsel güncelleme) CONFIRMED; spesifik aralık cihaz/veri hacmi ölçümüyle ayarlanacak judgment.
6. **Token katman adlandırması ve data-viz rol grubu:** M3 rol sistemi ve DTCG formatı CONFIRMED; projenin katman şeması judgment.
7. **Paper-trading'in ayrı bölüm mü, bot-oluşturma akışında "ortam" seçimi mi olduğu:** kaynaklarda doğrudan karşılığı yok; "gerçek/paper" etiketinin hiçbir seviyede gizlenmemesi gerektiği §4.3 türetmesiyle tutarlı olması koşuluyla judgment.
8. **Şablon galerisinin içeriği ve sıralaması:** "varsayılan sunmama hatası" CONFIRMED; hangi şablonların hangi sırayla sunulacağı gerçek kullanım verisi gerektiren judgment.

---

## 11. Uygulama Öncesi Doğrulama Programı (kaynak yöntemleriyle)

1. **Card sorting + tree testing** — 5 bölüm taksonomisinin ve bot-türü gruplamanın kullanıcı zihinsel modeliyle eşleşmesi (JUDGMENT maddelerinin CONFIRMED'a yükseltilme yolu; NN/g'nin IA doğrulama yöntemi).
2. **Görev bazlı kullanılabilirlik testi** — kritik görevler: (a) ilk grid botu kurulumu (sihirbaz + önizleme), (b) mevcut bot parametresini değiştirme (tek-sayfa form), (c) 20 bot arasından sorunlu olanı bulma (kart→drawer), (d) uyarı kuralı tanımlama, (e) replay ile geçmiş olayı inceleme. Ölçütler: görev süresi, hata oranı (PD'nin iyileştirdiğini iddia ettiği 3 bileşen: öğrenilebilirlik, verimlilik, hata [S12]).
3. **Performans bütçesi panosu** — INP ≤200 ms (p75, saha), LoAF >50 ms sayısı, DOM öğe sayısı, ilk bölüm chunk boyutu; `web-vitals` attribution ile sürekli izleme [S30][S32][S33].
4. **Uzman-yeni kullanıcı ayrımı ölçümü** — disclosure bölümlerinin açılma oranı; "uzman" alanların %50+ kullanıcı tarafından açılması, basit/uzman ayrımının yanlış kurgulandığının (PD kriteri: "ikincil seviyeye ilerleme seyrek olmalı") göstergesidir [S12].
5. **Bildirim yorgunluğu izleme** — toast sıklığı, kapatılma/bildirim-merkezine taşınma oranları; eşik kontrollerinin kullanım oranı [S23a].

---

## Ek: Araştırma soruları ↔ bölüm eşlemesi

| Soru | Bölüm | Ana kaynaklar |
|---|---|---|
| A1 gruplama | §2, §3.A1 | S1 S2 S3 S8 S24 S42 |
| A2 sekme eşiği | §3.A2 | S1 S2 S3 S38 S39 S40 S41 |
| A3 kalıcı bağlam | §3.A3 | S6 S7 S10 S17 S21 S22 |
| B1 disclosure düzeyi | §4.B1 | S12 S8 S14 S46 |
| B2 erişim mekanizması | §4.B2 | S12 S43a S48 |
| B3 asla gizlenmeyecekler | §4.B3 | S12 S21 S22 S24 S47 |
| C1 form düzeni | §5.C1 | S15 S46 S48 S49 S19 S50 |
| C2 canlı önizleme | §5.C2 | S15 S16 S18 S21 S23 S25 |
| C3 şablon tutarlılığı | §5.C3 | S8 S24 S41 S47 |
| D1 canlı render | §6.D1 | S16 S25–S29 S30–S34 |
| D2 bildirim sınırı | §6.D2 | S1 S10 S11 S13 S16 S17 S19 S20 S22 S23a |
| D3 kart↔tablo + replay | §6.D3 | S16 S17 S23 S24 S44 S47 |
| E1 tema mimarisi | §7 | S4 S5 S8 S23 S36 S44a |
| E2 performans | §8 | S24–S35 S47 |

---

*Rapor, 21.09.2026 tarihinde erişilen birincil kaynaklara dayanır. Tüm alıntılar kaynak metinlerin İngilizce aslından çevrilmiş veya birebir aktarılmıştır; hiçbir markanın ekran tasarımı kopyalanmamış, yalnızca ilke çıkarılmıştır. Kaynaksız "endüstri standardı" ifadesi kullanılmamıştır; ikincil kaynak kullanılan tek madde (S34c) açıkça CONDITIONAL işaretlenmiştir.*
