---
Durum: TAMAMLANDI (v1) — Claude bağımsız araştırması, AA.0 kapsamında
Metodoloji: docs/ARASTIRMA_FAZ16_QWEN_VIZYON_HARITASI.md §8.6.0
Ham malzeme: docs/ARASTIRMA_AA0_RAW_INVENTORY.md (ayrı bir ajanla çıkarılan, yorumsuz envanter — bu belgenin sentezi bu envantere ve benim domain/application katmanı bilgime dayanıyor)
Bu dosya, muse'un ayrı ve bağımsız docs/ARASTIRMA_AA0_UX_MUSE.md dosyasını yazana kadar OKUNMADAN tamamlandı. Sonuçlar Arda "bitti" dediğinde çapraz değerlendirilecek.
---

# AA.0 — Claude bağımsız araştırması: Qwen 15+3 ekran → DCABOT dönüşüm/geliştirme planı

## ÖNCE: Ham envanterde bulunan bir hatayı düzeltiyorum

Ham envanter belgesi (ayrı bir ajanla, kod-okumalı ama yorumsuz üretildi), `regime_detection`, `momentum_oscillators`, `signal_condition_ast` adlı modüllerin **kod tabanında hiç bulunamadığını** yazmış. Bu yanlış — üçü de gerçekten var (`src/dcabot/application/regime_detection.py`, `momentum_oscillators.py`, `signal_condition_ast.py`, kendim bu oturumda yazdım, testli). Muhtemelen ajanın grep taraması yanlış terim/büyük-küçük harf kombinasyonuyla arandı. `take_profit_ladder` zaten bir dosya adı değil, bir Config alanı adı — o kısım doğru.

Ama ham envanterin **asıl vardığı sonuç doğru ve kritik**: bunların HİÇBİRİ `api.py`'ye import edilmemiş. Kendi doğrulamamı yaptım:

```
grep -n "^from dcabot" src/dcabot/server/api.py | grep -iE "margin_mode|correlation|regime|momentum|signal_condition|bollinger|reinvest|active_deals|indicator_registry|whale|anti_liquidation|volatility_adaptive"
→ yalnızca 1 eşleşme: liquidation_status_service (satır 191)
```

## 🔴 EN ÖNEMLİ BULGU (AA'nın kendi planını değiştiren bir bulgu)

**BÜYÜK FAZ D/F/G/H/I'nin ürettiği hemen hemen HER motor modülünün sıfır HTTP endpoint'i var.** Margin Mode (preflight/registry/cross-admission), Korelasyon Riski, Rejim Tespiti (ADX/BBW), Momentum Osilatörleri (MACD/StochRSI), Bollinger Bantları, Kleene AST, Reinvest Havuzu, Max Active Deals registry, Whale Wall Detection, Anti-Liquidation'ın çoğu (yalnız `liquidation_status_service` bağlı) — bunların hepsi **test edilmiş, doğru, çalışan Python fonksiyonları** ama **frontend'in bunlara erişebileceği hiçbir `/api/...` yolu yok**. `Config.margin_mode`/`order_type`/`max_active_safety_orders`/`take_profit_ladder`/`stop_loss_rate`/`max_deal_duration_seconds`/`profit_asset` alanları BotWizard formunda VAR (kendi kodumu kontrol ettim, G.1-I.1 UI takipleri bu alanları gerçekten forma ekledi) — ama bu, yalnız **"bot oluşturma anında bir Config alanı olarak kaydedilebiliyor"** demek; "bir botun/deal'ın **çalışırken** bu alanlara göre ne yaptığını gösteren bir canlı görünüm var" demek DEĞİL. Örnek: bir kullanıcı Margin Mode=CROSS seçip botu kaydedebilir, ama hiçbir ekranda o botun margin-mode pre-flight durumunu, sembol-registry kilidini veya Cross-admission kararını GÖREMEZ — çünkü bunu gösterecek endpoint yok.

**Sonuç:** AA.1-AA.15'in "artık backend hazır, qwen'in yerleşimine gerçek veriyle bağlanabilir" varsayımı KISMEN yanlış. Backend'in EKONOMİK/MATEMATİKSEL çekirdeği hazır (bu doğru ve önemli), ama bunu göstermek için **önce bir API-kablolama katmanı** (yeni `/api/margin-mode/*`, `/api/risk/correlation`, `/api/indicators/*`, `/api/deals/active-limits`, `/api/reinvest-pool/{bot_id}` gibi uç noktalar, hepsi zaten var olan application-katmanı fonksiyonlarını çağıran ince FastAPI route'ları) gerekiyor. Bunu **AA'nın öncesine, ayrı bir dilim olarak** ekliyorum (aşağıda "AA.-1" olarak, plan bölümünde).

## Genel gözlem: qwen mockup'larının kendi sahte-veri deseni

Ham envanterde çok sayıda yer işaretlendiği gibi, qwen HTML'leri KENDİ İÇİNDE bolca sahte veri üretiyor (rastgele-yürüyüş fiyat simülasyonu, hardcoded bot/deal dizileri, `Math.random()` order book/ping/PnL, "RUNNING" servis kartları, hardcoded AI önerileri). Qwen'in kendisi bunların bir kısmını dürüstçe etiketliyor (`.simbadge`, "(demo)", "(simüle)", "KURGUSAL"), bir kısmını etiketlemiyor (sec-orders'daki order book, sec-conn'daki ping testi, sec-deploy'daki "RUNNING" servis kartları — bunlar gerçek veri izlenimi veriyor ama tamamen `Math.random()`). **Kural (Arda'nın bağlayıcı ilkesi + AGENTS.md):** DCABOT'un AA uygulaması bu sahte-veri desenini KOPYALAMAZ. qwen'in nesne DİZİLİMİ (kart nerede, hangi sırada, hangi görsel biçimde) taban alınır; qwen'in SAHTE VERİ ÜRETİM MANTIĞI asla taşınmaz. Karşılığı olmayan her alan ya (a) gerçek bir backend endpoint'ine bağlanır (varsa/eklenebiliyorsa), ya da (b) dürüstçe "veri yok / yakında / devre dışı" gösterilir — asla `Math.random()`/hardcoded dizi ile doldurulmaz.

---

## AA.1 — sec-status ("Sistem Özeti")

**[Nesne Envanteri]** 3 sütunlu faz-özeti kartı (düz metin) + dairesel ilerleme göstergesi + 4 sayaç (parametre/doğrulama/Monte Carlo/API-anahtar-gerekli) + boş `#phaseGrid`.

**[DCABOT Karşılığı]** KISMİ. `SystemStatusCard.tsx` zaten var ve `apiStatus`/`datasets`/`canary` gösteriyor — kavramsal olarak aynı yuvaya oturuyor ama qwen'in "dairesel ilerleme + sayaç animasyonu" görsel dilini taşımıyor.

**[Backend-Gerçeklik]** `/api/health`, `/api/capabilities`, `/api/risk/canary` zaten var ve gerçek veri döndürüyor. Qwen'in sayaçları ("TARANAN PARAMETRE", "MONTE CARLO SİM") DCABOT'ta gerçek karşılığı olan sayılar DEĞİL — bunlar qwen'in kendi geliştirme sürecine özgü hedef sayılardı. **Bunları birebir taşımak "uydurma veri" olur.** Bunun yerine aynı GÖRSEL FORMAT (dairesel gauge + sayaç kartları) gerçek DCABOT sayılarıyla doldurulmalı: örn. "Aktif Faz" yerine gerçek roadmap durumu (STATE.md'den), "Checker Durumu" (son `run_checks.py` sonucu, varsa CI'dan), "Aktif Bot Sayısı" (`/api/bots`), "Canary Durumu" (`/api/risk/canary`).

**[Sektör-Karşılaştırma + İyileştirme]** 3Commas/Pionex/Bitsgap'in hiçbirinde bu tarz bir "sistem/geliştirme durumu" paneli yok (onlar SaaS, kullanıcı geliştirme durumunu görmez) — bu DCABOT'a özgü, self-hosted/şeffaf bir artı olabilir ama qwen'in ORİJİNAL amacı (geliştiricinin kendi ilerlemesini izlemesi) DCABOT'un son-kullanıcı arayüzü için doğru çerçeve değil. **Öneri:** Bu ekranı "Geliştirici Durumu" (yalnız local/debug modda görünür, opsiyonel) olarak MU yoksa doğrudan Genel Bakış'a mı gömülü bir "Sistem Sağlığı" mini-kartı olarak mı ele alacağımıza Arda karar vermeli — bu bir ÜRÜN kararı (§ aşağıdaki açık sorular).

**[Teknik Not + Öncelik]** Düşük öncelik — diğer 14 ekranın hiçbiri buna bağımlı değil. Basit (yalnız statik + birkaç gerçek sayı), yeni bağımlılık gerektirmiyor.

---

## AA.2 — sec-overview ("Genel Bakış") — EN BÜYÜK VE EN KRİTİK DİLİM

**[Nesne Envanteri]** 4 stat kartı (Toplam Yatırılan/Bakiye/uPnL/Bugünkü Kâr) + canlı piyasa grafiği (sembol seçici, interval çubuğu, indikatör çubuğu SMA/EMA/Bollinger/Hacim/RSI/MACD) + Kâr Grafiği (Gün/Hafta/Ay) + Canlı Sistem Akışı feed'i + Açık İşlemler mini-kart grid'i.

**[DCABOT Karşılığı]** KISMİ-GÜÇLÜ. `HeroChartPanel.tsx` zaten "merkezi bileşen" olarak var ve gerçek bar/fiyat verisiyle çalışıyor; `DashboardPanel.tsx` genel gösterge verisi çekiyor (`/api/dashboard`); `SymbolSelector.tsx` sembol seçimini zaten yapıyor. Eksik olan: 4-stat-kart yerleşimi (qwen formatında), Kâr Grafiği'nin dönem-chip'li (Gün/Hafta/Ay) versiyonu, "Canlı Sistem Akışı" feed paneli (DCABOT'ta `EventPanel.tsx` var ama Genel Bakış'a değil "events" bölümüne bağlı — konumu farklı), indikatör çubuğunun (SMA/EMA/Bollinger/RSI/MACD) grafiğin ÜZERİNE bindirilmiş toggle-chip hâli.

**[Backend-Gerçeklik — DETAYLI]**
- 4 stat kartı: `/api/dashboard` zaten equity/PnL benzeri alanlar döndürüyor olabilir (ham envanterde teyit edilmedi, `api.py:6578` doğrudan okunmalı) — eğer eksikse bu gerçek bir veri-toplama sorusu (hangi bot/deal'ların toplamı gösterilecek, tek-bot mu çoklu-bot mu).
- İndikatör çubuğu (SMA/EMA): `signal_native_indicators.py` zaten var VE `/api/signals/indicators/cross` üzerinden kısmen bağlı — SMA/EMA overlay'i gerçek veriyle mümkün.
- İndikatör çubuğu (Bollinger/RSI-benzeri/MACD): **BURADA G.4'ün `bollinger_bands.py`/`momentum_oscillators.py` devreye girer — ama az önceki kritik bulgu gereği hiçbiri api.py'ye bağlı değil.** Bu ekran G.4'ün asıl "vitrin"i olacaktı; şu an gösterilemez. **AA'nın en somut "önce API ekle" ihtiyacı burada.**
- Kâr Grafiği: hangi veri kaynağından besleneceği (tek deal mi, bot-toplamı mı, hesap-toplamı mı) net değil — bu bir ürün kararı gerektirir (bkz. açık sorular).
- Canlı Sistem Akışı: `/api/events` zaten var, doğrudan taşınabilir.

**[Sektör-Karşılaştırma + İyileştirme]** 3Commas'ın "Dashboard"u ve Bitsgap'in ana ekranı da tam olarak bu 4-öğeyi (özet stat + fiyat grafiği + kâr eğrisi + aktif işlemler) birleştiriyor — qwen'in dizilimi sektör normuyla uyumlu, taban olarak sağlam. **İyileştirme fırsatı:** hiçbiri MACD/Bollinger/StochRSI'yi DOĞRUDAN ana grafiğin üzerine bindirmiyor (genelde ayrı bir "Indicators" sekmesi) — DCABOT bunu qwen'in tasarladığı gibi tek ekranda toggle-chip olarak sunarsa, ve gerçekten G.4'ün üç-değerli-mantık sinyal sistemine bağlarsa (örn. bir chip aktifken "AL sinyali" gibi bir Kleene-AST sonucu gösterirse), bu üç rakibin HİÇBİRİNDE olmayan bir entegrasyon olur.

**[Teknik Not + Öncelik]** **En yüksek öncelik** (kullanıcının ilk gördüğü ekran). Lightweight-charts zaten kullanılıyor mu kontrol edilmeli (qwen CDN'den çekiyor, DCABOT muhtemelen kendi grafik kütüphanesini kullanıyor — `CandleChart.tsx`/`TradingChart.tsx` var, hangisinin lightweight-charts'a eşdeğer olduğu teyit edilmeli). Yeni bağımlılık İSTENMEMELİ (offline-first) — mevcut grafik bileşenine indikatör-overlay katmanı eklemek yeterli olmalı.

---

## AA.3 — sec-bots + sec-botdetail ("Botlarım" + "Bot Detay")

**[Nesne Envanteri]** Bot kart grid'i (şablon chip'leri, tıklanınca detaya gider) + Bot Detay (geri butonu, tip/durum chip, uPnL, aç/kapa switch, hızlı-bot-geçiş chipbar, 6 sütun performans metrik grid'i, sparkline, canlı grafik+parametre-overlay, "Aktif Ayarlar" tam parametre listesi, o botun deal'ları).

**[DCABOT Karşılığı]** GÜÇLÜ. `BotTable.tsx` + `BotContextHeader` zaten kart/liste + profil özeti yapıyor; `BotDetailView.tsx` zaten grafik+taslak-parametre+likidasyon durumu gösteriyor (`LiquidationStatusSection.tsx` üzerinden). En büyük fark: qwen'in "6 sütun performans metriği" (winRate, maxDD, totalDeals, upDays vb.) ve "hızlı bot geçiş chipbar"ı DCABOT'ta yok/farklı yerleşimde.

**[Backend-Gerçeklik]** Bot performans metrikleri (winRate, maxDD, profit) — DCABOT'ta bunlar gerçek geçmiş deal verisinden HESAPLANABİLİR (`/api/bots/{bot_id}` + deal geçmişi), ama qwen'de olduğu gibi HAZIR bir tek endpoint'ten gelmiyor; bu alan bir agregasyon gerektirir (yeni küçük bir endpoint veya frontend-tarafı hesap — tercihen backend, exact-Fraction tutarlılığı için). "Aktif Ayarlar" tam parametre grid'i: artık `Config`'in TÜM alanları (margin_mode, order_type×4, max_active_safety_orders, take_profit_ladder, stop_loss_rate, max_deal_duration, profit_asset dahil) `/api/bots/{bot_id}` üzerinden dönüyorsa (teyit edilmeli) doğrudan gösterilebilir — bu, G-I fazlarının en doğal "vitrin" noktalarından biri.

**[Sektör-Karşılaştırma + İyileştirme]** 3Commas'ın Bot Detay sayfası tam olarak bu grid+ayarlar+deal-listesi düzenini kullanıyor — qwen taban olarak doğru. **İyileştirme:** hiçbir rakip margin_mode/order_type/take_profit_ladder gibi ayrıntıları TEK bir "Aktif Ayarlar" grid'inde bu kadar şeffaf göstermiyor (genelde ayrı sekmelere dağıtıyorlar) — DCABOT'un qwen'in kompakt grid'ini kullanıp TÜM Config alanlarını (13+ alan) burada göstermesi gerçek bir farklılaşma noktası.

**[Teknik Not + Öncelik]** Yüksek öncelik. Performans-metrik agregasyonu için küçük bir backend hesap fonksiyonu gerekebilir (yalnız Claude, exact-Fraction).

---

## AA.4 — sec-deals + sec-dealdetail ("Aktif İşlemler" + "İşlem Detay")

**[Nesne Envanteri]** Deal tablosu (Sembol/Yön/Lev/Ort.Giriş/Güncel/PnL%/SO-Doluluk/TP-Mesafe/Aksiyon) + "Smart Trade Terminal" manuel pozisyon paneli + Deal Detay (8-sütun bilgi grid'i, grafik, "Seviyeler" paneli, Fon-Ekle/Panic-Sell aksiyonları, bağlı-bot bilgisi).

**[DCABOT Karşılığı]** KISMİ. `DealDetailView.tsx` var (lifecycle/history/replay). Deal TABLOSU (liste görünümü) ayrı bir bileşen olarak görünmüyor — ham envanterde `DealPanel.tsx` "Klasik/legacy" grubunda, event-ekleme/replay odaklı, qwen'in "tablo + satır-aksiyon" formatında değil.

**[Backend-Gerçeklik]** "SO Doluluk" — artık G.3'ün `effective_max_active_safety_orders`/eşzamanlı-SO state machine'i sayesinde GERÇEK bir "N/M dolu" sayısı hesaplanabilir (`decision()`/`report()`'tan). "TP Mesafe" — `target()`/ladder hesaplarından gerçek. "Smart Trade Terminal" (manuel pozisyon açma) — DCABOT'un felsefesiyle (yalnız deal/bot akışından pozisyon açılır, keyfi manuel emir yok, credential/mutation kısıtları) ÇELİŞEBİLİR; bu ekranın DCABOT'a UYARLANMADAN birebir taşınması riskli — **ürün kararı gerektirir** (aşağıda açık soru).

**[Sektör-Karşılaştırma + İyileştirme]** 3Commas'ın "Smart Trade" özelliği gerçek ve popüler ama DCABOT'un "yalnız bot/deal akışı, keyfi manuel emir yok" ilkesiyle gerginlik yaratıyor. **Öneri:** Smart Trade panelini AA'ya dahil ETMEMEK, ya da salt-okunur bir "hızlı bak" formuna indirgemek (gerçek emir vermeden hesap-önizlemesi).

**[Teknik Not + Öncelik]** Orta-yüksek öncelik. Deal listesi için yeni bir tablo bileşeni gerekebilir (mevcut `BotTable.tsx`'in deal-versiyonu).

---

## AA.5 — sec-dca ("Bot Kur")

**[Nesne Envanteri]** Şablon chip'leri + canlı önizleme grafiği + 5 mini-stat (Ort.Maliyet/TP/SL/Likidasyon/Toplam Marjin) + indikatör çubuğu + tam DCA form alanları.

**[DCABOT Karşılığı]** GÜÇLÜ — `BotWizard.tsx` zaten bu formun kapsamlı bir versiyonu (G-I'nin TÜM yeni alanları dahil: margin_mode, order_type×4+slippage, max_active_safety_orders, take_profit_ladder editörü, reinvest, SL onay barı, max deal duration, profit_asset+uyarı — kendi doğrulamamla teyit ettim). Eksik olan yalnız qwen'in GÖRSEL yerleşimi (5 mini-stat kutucuğu + canlı grafik-üstü önizleme) — `BotWizard`'ın kendisi muhtemelen dikey form listesi tarzında, qwen'in "solda form, sağda canlı grafik+mini-stat" iki-sütun yerleşiminde değil.

**[Backend-Gerçeklik]** `/api/preview` zaten DCA ladder önizleme hesabı yapıyor — 5 mini-stat'ın tamamı (Ort. Maliyet, TP, SL, Likidasyon UYARISI [LCR-12 gereği tahmin değil, "hesapla-ama-asla-otorite-değil" notuyla], Toplam Marjin) buradan veya `Config`'in kendi alanlarından türetilebilir.

**[Sektör-Karşılaştırma + İyileştirme]** Bu, DCABOT'un G-I fazlarıyla ZATEN 3Commas+Pionex+Bitsgap toplamını aşan tek form (margin_mode+4 order_type+concurrent-SO+ladder+reinvest+SL-confirmation+max-duration+profit_asset hiçbirinde birlikte yok). **Bu ekran AA'nın en güçlü "biz daha iyiyiz" vitrin noktası** — öncelik yüksek olmalı ama risk düşük (form zaten var, yalnızca yerleşim/görsel iş).

**[Teknik Not + Öncelik]** Yüksek öncelik, düşük risk (backend tamamen hazır ve zaten bağlı).

---

## AA.6 — sec-datastore ("Veri Pipeline")

**[Nesne Envanteri]** Parite panosu (spot/futures probe) + Doğrulama Laboratuvarı (6 kural) + Toplu İndirme Planı (manifesto/Python/Bash script üretici + "İndirdim→Kaydet" butonu) + Kayıtlı Yerel Depo.

**[DCABOT Karşılığı]** GÜÇLÜ — `DatasetCatalogPanel.tsx` zaten dataset/download/profile/run-plan/preflight işlevlerini kapsıyor.

**[Backend-Gerçeklik]** Çoğu zaten `/api/datasets/*` ile bağlı. Tek dikkat noktası: qwen'in "İndirdim → Depoya Kaydet" butonu ham envanterde AÇIKÇA sahte-kayıt riski taşıyan bir öğe olarak işaretlenmiş (kullanıcı gerçekte indirmese bile "kayıtlı" gösterebiliyor) — **bu davranış DCABOT'a KESİNLİKLE taşınmamalı**, DCABOT'un kendi indirme-işi (`/api/dataset-downloads/{job_id}`) zaten gerçek bir iş takibi yapıyor, qwen'in sahte "elle onayla" desenine geri dönülmemeli.

**[Sektör-Karşılaştırma + İyileştirme]** Hiçbir rakipte (3Commas/Pionex/Bitsgap) bu derece şeffaf bir "veri pipeline" ekranı yok (SaaS'lar veri kaynağını gizler) — DCABOT'un kendine özgü, offline-first artısı. Zaten var olan gerçek iş takibini kullanmak üzere qwen'in görselini adapte etmek yeterli.

**[Teknik Not + Öncelik]** Orta öncelik, düşük risk.

---

## AA.7 — sec-backtest ("Backtest Studio")

**[Nesne Envanteri]** Veri kaynağı formu + DCA parametreleri + maliyet modeli + "ANTİ-HALÜSİNASYON KURALLARI" kutusu + 9 metrik kartı + equity eğrisi + fiyat+işlem grafiği + işlem geçmişi tablosu + Optimizasyon/Walk-Forward/Monte Carlo alt-sekmeleri (heatmap, ilerleme çubuğu).

**[DCABOT Karşılığı]** GÜÇLÜ. `DatasetCatalogPanel`/`SavedRunsPanel` + Faz 14'ün overfitting-direnç altyapısı (embargo/CPCV/PBO/DSR, sweep orkestratörü, sampler) zaten var — bu qwen ekranının "arkasında" DCABOT'ta muhtemelen qwen'in JS-simülasyonundan DAHA SAĞLAM bir motor var (gerçek exact-Fraction backtest, tarayıcı-içi yaklaşık JS değil).

**[Backend-Gerçeklik]** `/api/sweeps/optimize`, `/api/historical-runs/*` zaten bağlı. Heatmap/Walk-Forward/Monte Carlo görselleştirmesi — Faz 14'ün PBO/DSR/CPCV çıktısı muhtemelen ZATEN hesaplanıyor ama qwen'in ısı-haritası/Monte-Carlo-histogram GÖRSEL formatında sunulmuyor olabilir (teyit edilmeli: `/api/sweeps/optimize` çıktısının tam şemasını okumak gerekir).

**[Sektör-Karşılaştırma + İyileştirme]** Hiçbir rakip (3Commas/Pionex/Bitsgap) CPCV/PBO/DSR gibi overfitting-direnç istatistiklerini KULLANICIYA GÖSTERMİYOR (dahili varsa bile gizli) — DCABOT bunu qwen'in "Walk-Forward DAYANIKLI/ZAYIF/OVERFIT" rozet dilini kullanarak gösterirse, akademik-seviye bir şeffaflık sunar, hiçbir rakipte yok.

**[Teknik Not + Öncelik]** Yüksek değer ama karmaşık — heatmap/histogram için mevcut grafik altyapısının (canvas mı SVG mi) genişletilmesi gerekebilir. Orta-yüksek öncelik.

---

## AA.8 — sec-modules + sec-core ("Gelişmiş Modüller" + "Çekirdek & Modül Mimarisi")

**[Nesne Envanteri]** Modül tanıtım kartları (içerik tanımı ham envanterde bulunamadı) + "Mimari Topoloji" (animasyonlu event-bus şeridi, dekoratif) + "Event Bus Trafiği (simüle)" + Modül Kayıt Defteri + "Yeni Strateji Plugin'i Ekle" formu (iskelet, gerçek plugin sistemi yok).

**[DCABOT Karşılığı]** YOK.

**[Backend-Gerçeklik]** DCABOT'ta gerçek bir "plugin sistemi" veya "event bus" YOK (mimarisi zaten pure-reducer + REST, mesaj-kuyruğu değil) — qwen'in bu ekranı KENDİ mockup'ında bile "simüle"/iskelet olarak işaretli, gerçek bir mimari değil.

**[Sektör-Karşılaştırma + İyileştirme]** Hiçbir rakipte "plugin ekle" arayüzü yok (kapalı sistemler). **Öneri: AA.8'i AA.12 (Deploy) gibi bilinçli kapsam-dışı bırakmak** — gerçek bir plugin mimarisi olmadan bu ekranı "gerçek gibi" göstermek doğrudan uydurma-veri ilkesini ihlal eder. Eğer Arda gerçek bir plugin/modül-kayıt sistemi istiyorsa bu AYRI, büyük bir mimari karardır (mevcut roadmap'te yok).

**[Teknik Not + Öncelik]** **Düşük öncelik, muhtemelen kapsam-dışı** (AA.12 ile aynı gerekçeyle) — Arda'ya açık soru.

---

## AA.9 — sec-ai ("AI Önerici")

**[Nesne Envanteri]** "KURGUSAL"/"GERÇEK LLM" rozetli sohbet paneli + "Kalıcı Hafıza Bankası" (aslında yalnız tarayıcı-oturumu, kalıcı değil) + (file 17'de) 3 tamamen hardcoded öneri kartı.

**[DCABOT Karşılığı]** YOK (dış LLM asistanı sorusu zaten "Arda'ya açık sorular" listesinde bekliyor).

**[Backend-Gerçeklik]** Yok — dış LLM entegrasyonu henüz onaylanmadı.

**[Sektör-Karşılaştırma + İyileştirme]** 3Commas'ın "SmartTrade AI" ve benzerleri gerçek (ücretli) LLM entegrasyonları sunuyor. DCABOT bu konuda henüz karar vermedi.

**[Teknik Not + Öncelik]** **Tamamen bloke** — "dış LLM asistanı açılsın mı?" açık sorusuna bağlı. Karar gelmeden bu ekran ele alınamaz; alınırsa bile qwen'in "3 hardcoded öneri kartı" deseni KESİNLİKLE taşınmaz (gerçek LLM çağrısı olmadan "AI önerisi" göstermek düz uydurmadır).

---

## AA.10 — sec-risk ("Risk Paneli") — İKİNCİ EN KRİTİK DİLİM

**[Nesne Envanteri]** Circuit Breaker (drawdown switch/eşik/kill-switch) + Liquidation Engine (3 statik chip + boş liste) + Korelasyon Matrisi (6x6 grid) + Funding&Spread Tarayıcı.

**[DCABOT Karşılığı]** KISMİ. `RiskPanel.tsx` zaten canary/kill-switch/açıklama gösteriyor (`/api/risk/kill-switch`, `/api/risk/canary`, `/api/risk/explain`). `LiquidationStatusSection.tsx` zaten `liquidation_status_service` üzerinden GERÇEK likidasyon-durumu gösteriyor (D fazının ürünü, ZATEN bağlı). Korelasyon Matrisi ve Funding&Spread Tarayıcı — DCABOT'ta YOK.

**[Backend-Gerçeklik]** Circuit Breaker + Liquidation: BAĞLI (yukarıda). **Korelasyon Matrisi: `correlation_risk.py`/`correlation_scores.py` var ama api.py'ye bağlı DEĞİL** (kritik bulgu) — bu, F.2'nin doğrudan vitrin noktası ve şu an gösterilemez. Funding&Spread Tarayıcı: DCABOT'ta funding-hesabı `/api/futures/funding` var ama bir "tarayıcı" (çoklu sembol karşılaştırma tablosu) hâlinde değil — yeni bir agregasyon endpoint'i gerektirir.

**[Sektör-Karşılaştırma + İyileştirme]** Hiçbir rakip korelasyon-riskini bu şekilde (6x6 matris + admisyon kapısı) göstermiyor — F.2 zaten rakiplerin ötesinde bir özellik, yalnız API eksik. Likidasyon durumunun "asla kendi tahminimizi otorite gibi göstermeme" ilkesi (LCR-12) zaten DCABOT'a özgü bir dürüstlük artısı, hiçbir rakipte böyle açık bir uyarı yok.

**[Teknik Not + Öncelik]** **Yüksek öncelik AMA API-kablolama ön-koşullu.** Korelasyon matrisi için `/api/risk/correlation` gibi yeni bir endpoint (yalnız Claude — exact/float sınırına dokunuyor) + hangi sembol çiftlerinin karşılaştırılacağı (kullanıcının aktif botları mı, gözlem listesi mi) ürün kararı gerektiriyor.

---

## AA.11 — sec-grid ("Infinity Grid + Hybrid Engine")

**[Nesne Envanteri]** Grid görselleştirme canvas'ı + Hybrid Engine 3-faz kartı + kontrol paneli (grid adımı slider, floor-auto-adjust, futures-rebalancing switch).

**[DCABOT Karşılığı]** KISMİ — `FuturesPanel.tsx`/`FuturesDcaForm.tsx` grid seviyeleri/pnl/trailing/funding işlevlerini kapsıyor ama qwen'in görsel grid-canvas'ı ve "Hybrid Engine" 3-faz konsepti DCABOT'ta yok (DCABOT'ta grid ve DCA ayrı stratejiler, "hybrid" tek bir motor değil).

**[Backend-Gerçeklik]** `/api/futures/grid/*` zaten bağlı, gerçek. "Hybrid Engine" (DCA→Grid→Kâr-realizasyon 3-fazlı otomatik geçiş) — DCABOT'ta BÖYLE BİR MOTOR YOK, bu qwen'in kendi icadı bir konsept. **Bu, uydurulamaz** — DCABOT'un grid ve DCA'sı ayrı config'ler/deal'lar.

**[Sektör-Karşılaştırma + İyileştirme]** Pionex'in "Infinity Grid" ürünü gerçek ve popüler; DCABOT'un futures-grid'i buna eşdeğer. "Hybrid" 3-faz otomatik-geçiş konsepti hiçbir rakipte de yok (qwen'in kurgusu). **Öneri:** Grid görselleştirmesi (canvas) gerçek grid-seviyesi verisiyle taşınabilir; "Hybrid Engine" 3-faz otomasyonu AYRI bir ürün kararı/motor-tasarımı gerektirir, AA'ya dahil edilmemeli (yeni bir BÜYÜK FAZ konusu olabilir).

**[Teknik Not + Öncelik]** Orta öncelik; Hybrid-otomasyon kısmı kapsam-dışı bırakılmalı.

---

## AA.12 — sec-deploy ("Deploy")

Roadmap zaten bunu bilinçli kapsam-dışı olarak işaretlemiş (offline-first ilkesiyle çelişiyor) — ben de aynı sonuca vardım. Ham envanterdeki "RUNNING" servis kartlarının hepsi qwen'de bile sahte (`#svcGrid` gerçek servis kontrolü yapmıyor) — bu ekranın birebir taşınması hem gereksiz hem sahte-durum riski taşıyor. **Değişiklik önerisi yok, mevcut karar doğru.**

---

## AA.13 — sec-compare + sec-config + sec-portfolio (iterasyon #17, "Strateji Laboratuvarı")

**[Nesne Envanteri]** Portföy donut grafiği + bot-bazlı PnL progress-bar listesi + Strateji Karşılaştırma (DCA/Grid/Hybrid motor karşılaştırma grafiği+tablosu) + Yeni Strateji Konfigüratörü (paper-fırlat formu) + AI Önerileri (hardcoded, bkz. AA.9).

**[DCABOT Karşılığı]** KISMİ-ZAYIF. `RebalancePanel.tsx`/`RebalancePlanPanel.tsx` portföy-benzeri hesap yapıyor ama qwen'in "donut+bot-bazlı PnL" formatında değil. Strateji karşılaştırma — DCABOT'ta YOK ayrı bir ekran olarak (ama `SavedRunsPanel.tsx`'in "kayıtlı koşuları karşılaştır" işlevi kavramsal olarak yakın).

**[Backend-Gerçeklik]** Portföy donut'u — hesap-geneli pozisyon dağılımı DCABOT'ta `Config.profit_asset`/deal listesinden türetilebilir ama HAZIR bir "portföy dağılımı" endpoint'i yok. Strateji karşılaştırma — `SavedRunsPanel`'in kayıtlı-koşu-karşılaştırma altyapısı zaten var, bu ekran ona görsel bir ön-yüz olabilir. "Paper Fırlat" — `PaperPanel.tsx`/`/api/paper/sessions` zaten gerçek paper-trading akışı sağlıyor, qwen'in "yalnızca bellekte, sayfa yenilenince kaybolan" sahte akışının YERİNE gerçek paper-session akışı konulmalı.

**[Sektör-Karşılaştırma + İyileştirme]** Hiçbir rakipte DCA/Grid/Hybrid'i AYNI VERİ üzerinde yan yana karşılaştıran bir "strateji lab" yok — bu, DCABOT'un Faz 14 (overfitting-direnç) altyapısıyla birleşince gerçek bir farklılaşma olabilir (rakipler ham backtest sonucu gösterir, DCABOT PBO/DSR ile "bu sonuç şansa mı dayanıyor" sorusunu da cevaplar).

**[Teknik Not + Öncelik]** Orta öncelik — portföy-donut için yeni küçük bir agregasyon endpoint'i gerekir; strateji-karşılaştırma `SavedRunsPanel` üzerine inşa edilebilir (düşük risk, mevcut altyapı).

---

## AA.14 — sec-conn + sec-execlog + sec-history + sec-orders (iterasyon #18, "Testnet Execution Console")

**[Nesne Envanteri]** API Key/Secret girişi (sahte kaydetme) + sahte ping testi + **tamamen `Math.random()` order book** + DRY-RUN emir formu (rastgele NEW→WORKING→FILLED simülasyonu, rastgele PnL) + execution log + emir geçmişi tablosu.

**[DCABOT Karşılığı]** GÜÇLÜ AMA FARKLI FELSEFE. `BinanceAccountPanel.tsx` (`/api/testnet/account`, `/api/testnet/open-orders`) ZATEN GERÇEK testnet verisi çekiyor — qwen'in sahte-ping/sahte-order-book/sahte-PnL simülasyonunun YERİNE DCABOT'ta GERÇEK bir testnet bağlantısı var. **Bu, kritik bir uyarı gerektiriyor: qwen'in bu ekranını "birebir" taşımak YASAK olmalı** çünkü qwen'in tüm emir-yaşam-döngüsü/order-book/ping'i `Math.random()` — DCABOT'un gerçek testnet verisi varken sahte simülasyon deseni kopyalanırsa bu doğrudan "sahte veriyi gerçek gibi gösterme" ihlali olur.

**[Backend-Gerçeklik]** `/api/testnet/account`, `/api/testnet/open-orders`, `testnet_order_execution.py` (mutation-gate, 7 kural) zaten var ve gerçek. API Key girişi — DCABOT'un credential-güvenlik çizgisi gereği (AGENTS.md) bu ekrandan .env yazımı YAPILMAZ, yalnız MEVCUT (zaten ayarlanmış) credential'ların DURUMU gösterilir.

**[Sektör-Karşılaştırma + İyileştirme]** Hiçbir rakip "dry-run execution console" sunmuyor (onlar doğrudan canlı) — DCABOT'un P2 (testnet) altyapısını GERÇEK veriyle bu ekrana taşıması, sahte-simülasyon değil, rakiplerin sunmadığı gerçek bir şeffaflık katmanı olur.

**[Teknik Not + Öncelik]** Orta öncelik. **En yüksek "sahte veri riski" taşıyan ekran** — dikkatli inceleme/dürüst-boş-durum tasarımı şart (testnet credential yoksa "bağlantı yok" dürüstçe gösterilmeli, sahte ping asla).

---

## AA.15 — sec-exec + sec-lab + sec-tests (iterasyon #21/#22, "Mission Control")

**[Nesne Envanteri]** Sadeleştirilmiş execution console (AA.14'ün küçük hâli) + Strateji Lab (DCA/Grid karşılaştırma, AA.13'ün küçük hâli) + Motor Testleri (GERÇEK client-side unit test çalıştırıcı, 7-14 test).

**[DCABOT Karşılığı]** sec-exec/sec-lab → AA.14/AA.13 ile aynı analiz geçerli (bunlar aynı ekranların küçültülmüş tekrarları). **sec-tests YENİ bir kavram** — DCABOT'ta "tarayıcıda motor testi çalıştır" diye bir ekran yok (testler zaten `tools/run_checks.py` ile CI/local'de çalışıyor, 1893 test).

**[Backend-Gerçeklik]** sec-tests'in DCABOT karşılığı YOK ve muhtemelen GEREKMİYOR — DCABOT'un test altyapısı zaten çok daha kapsamlı (gerçek Fraction-oracle testleri, digit-growth testleri, vb.), bunu tarayıcıda yeniden implemente etmek hem gereksiz hem qwen'in JS-motoruyla DCABOT'un gerçek Python motoru arasında bir TUTARSIZLIK riski yaratır (iki ayrı, birbirinden bağımsız "DCA engine" var olur). **Bu ekranın amacı (kullanıcıya "motor doğru çalışıyor" güvencesi vermek) yerine**, gerçek `run_checks.py` sonucunu (CI rozetinden veya bir "son doğrulama" zaman damgasından) gösteren bir "Sistem Sağlığı" kartı önerilir — AA.1 ile birleşebilir.

**[Sektör-Karşılaştırma + İyileştirme]** Hiçbir rakip kullanıcıya "motor testleri" göstermiyor — bu qwen'e özgü bir geliştirici-güven mockup'ı, son-kullanıcı özelliği değil.

**[Teknik Not + Öncelik]** Düşük öncelik. sec-tests'in DOĞRUDAN taşınması ÖNERİLMEZ (gereksiz + tutarsızlık riski); AA.1'in "Sistem Sağlığı" kartına gerçek checker-durumu olarak entegre edilmesi önerilir.

---

## ÖZET: Önerilen ek dilim — "AA.-1: API-kablolama katmanı" (AA'dan ÖNCE gelmeli)

AA.2 (Genel Bakış'ın MACD/Bollinger overlay'i) ve AA.10'un (Korelasyon Matrisi) tam olarak vitrinlenebilmesi için, aşağıdaki (zaten var, test edilmiş, yalnızca API'siz) modüllerin ince FastAPI route'larla `api.py`'ye bağlanması gerekiyor — bu **saf kablolama**, yeni matematik değil, ama exact/float sınırına dokunduğu için **yalnız Claude** yapmalı:
- `momentum_oscillators.py` (MACD/StochRSI) → `/api/indicators/macd`, `/api/indicators/stoch-rsi`
- `bollinger_bands.py` → `/api/indicators/bollinger`
- `correlation_risk.py` → `/api/risk/correlation`
- `regime_detection.py` → `/api/risk/regime` (opsiyonel, AA.10'a ek olabilir)
- `margin_mode_preflight.py`/`registry.py`/`cross_admission.py` → bot detay ekranında margin-mode durumu göstermek isteniyorsa
- `reinvest_pool.py` → AA.13'ün portföy ekranı reinvest-havuzu göstermek isteyecekse
- `active_deals_registry.py` → deal-açma akışında "sınır doldu" mesajı göstermek isteniyorsa
- `indicator_registry.py` → yukarıdaki indikatör endpoint'lerinin ortak giriş noktası olabilir

Bu, ayrı bir küçük dilim (yarım-bir-gün ölçeğinde, TDD'li) olarak AA.1'den önce planlanmalı.

## Arda'ya açık ürün soruları (bu araştırmadan çıkan, teknik olmayan kararlar)

1. AA.1 (Sistem Özeti) geliştirici-durumu mu, yoksa son-kullanıcı "Sistem Sağlığı" kartı mı olsun?
2. AA.4'ün "Smart Trade Terminal"i (manuel pozisyon açma) DCABOT'a hiç dahil edilsin mi, yoksa salt-okunur önizlemeye mi indirilsin?
3. AA.8 (plugin/event-bus mimarisi) tamamen kapsam-dışı mı kalsın (öneri: evet), yoksa gerçek bir plugin-mimari kararı mı verilsin (büyük, ayrı iş)?
4. AA.9 (AI Önerici) — dış LLM asistanı sorusu hâlâ açık; bu ekran o karara bağlı kilitli kalmaya devam ediyor.
5. AA.11'in "Hybrid Engine" 3-faz otomasyonu — gerçek bir motor olarak istenirse ayrı bir BÜYÜK FAZ konusu; AA'ya dahil edilmemesi öneriliyor.
6. Genel Bakış'ın "Kâr Grafiği" hangi kapsamda (tek-bot/çoklu-bot/hesap-toplamı)?

## Kaynaklar
- `docs/ARASTIRMA_AA0_RAW_INVENTORY.md` (ham envanter, bu belgenin temel girdisi)
- `docs/qwen_referans/iterasyonlar/{14,17,18,21,22}_*.html` (doğrudan referans)
- `docs/KARARLAR.md` (G.1-I.2 motor kararları, backend-gerçeklik kontrolü için)
- Kendi kodum: G.1-I.2'de bizzat yazdığım `Config`/`engine.py`/`application/*.py` dosyaları (hangi alan gerçekten var, hangi endpoint yok — birinci elden bilgi)
