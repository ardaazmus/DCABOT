# AA0 — Ham Envanter (Raw Inventory)

Bu belge, DCABOT-v2 frontend yeniden tasarımı için ham, yorumsuz bir envanterdir. Üç bölüm içerir:
1. `qwen_referans/iterasyonlar/` altındaki 5 HTML mockup dosyasının section-bazlı UI nesne envanteri.
2. Mevcut `frontend/src/*.tsx` dosyalarının envanteri (App.tsx / appSections.ts kablolamasına göre).
3. `src/dcabot/server/api.py` HTTP endpoint envanteri, özellik alanına göre gruplu, ve api.py'ye bağlı olmayan application modüllerinin listesi.

Bu belge **tasarım kararı içermez**; yalnızca gözlemlenen olguları kaydeder. Sentez/karşılaştırma ayrı bir adımda yapılacaktır.

Kaynak dosyalar:
- `docs/qwen_referans/iterasyonlar/14_1787388842.html` (3047 satır) - "Faz 4.5 Gercek Optimizasyon", sidebar navli ana mockup.
- `docs/qwen_referans/iterasyonlar/17_1787399213.html` (430 satir) - "Strateji Laboratuvari" (tabli, sidebar yok).
- `docs/qwen_referans/iterasyonlar/18_1787401208.html` (310 satir) - "Testnet Execution Console" (tabli, sidebar yok).
- `docs/qwen_referans/iterasyonlar/21_1787405549.html` (338 satir) - "Mission Control" / "Uretim Surumu" (sidebar navli, sadelestirilmis).
- `docs/qwen_referans/iterasyonlar/22_1787406517.html` (282 satir) - 21 ile neredeyse ayni iskelet, "Bitmis Arayuz" basligi, biraz daha sadelestirilmis (test sayisi 14 -> 7, karsilastirma DCA/Grid'e indirgenmis, Hybrid/deploy talimati yok).

---

## PART 1 - Qwen HTML Section Envanteri

Genel gozlem (tum 5 dosyada ortak): Tailwind CDN + lightweight-charts CDN + Google Fonts (Space Grotesk/JetBrains Mono) kullanan, tek-dosya, framework'suz (vanilla JS) mockuplar. Ortak CSS siniflari: .panel (cam-blur kart), .ptitle (kucuk baslik), .chip/.chipBtn (etiket/sekme), .livebadge (yesil "canli" rozet), .simbadge (sari "simulasyon/demo" rozet), .drybadge (mor "dry-run" rozet), .tab-section/.tab-section.active (JS ile goster/gizle, fadeUp animasyonu), .fin (form input), .lgbox (kucuk istatistik kutusu), #toast/.show (alt-sag toast bildirimi, translateY gecisi), .pingr/@keyframes pingd (yesil nabiz/ping noktasi - "canli" gostergesi).

Genel JS mimarisi (file 14, 21, 22 ortak): market global state objesi (candles, mode: connecting|live|sim, ws), Binance public REST + WebSocket (wss://data-stream.binance.vision) ile canli kline cekme; basarisiz olursa seedSim/seedSimSymbol/startSim fonksiyonlari ile rastgele yuruyus (random walk) sahte mum verisi uretir ve market.mode='sim' yaparak .simbadge/"SIMULASYON" rozetiyle isaretler. Bu, projenin "gercek veri gibi gosterilen sahte veri yasak" kuraliyla catisan, mockup'in kendi icinde etiketledigi ama yine de urettigi onemli bir fake-data noktasidir.

### sec-status (yalnız file 14)
- Panel 1: "📡 Sistem Özeti — Faz 1 ✓ · Faz 4 ✓ · Faz 4.5 aktif" başlıklı kart, 3 sütun: "✅ FAZ 1 · VERİ PIPELINE", "🧪 FAZ 4 + 4.5 · BACKTEST", "⏳ SIRADA" — düz metin açıklamalar, veri bağlı değil.
- Panel 2: Dairesel ilerleme göstergesi (conic-gradient, `#progBar`/`#progPct` — JS ile `%0`'dan başlayıp dolduruluyor, `data-count` attribute'lu sayaç animasyonu: "TARANAN PARAMETRE" 0→5, "DOĞRULAMA KATMANI" 0→3, "MONTE CARLO SİM" 0→500, "API ANAHTARI GEREKEN" 0→0). Bu sayılar **hardcoded hedef değerler**, gerçek veriden gelmiyor.
- `#phaseGrid` (boş div, JS ile doldurulacak faz kartları — script'in geri kalanında görülmedi, muhtemelen roadmap kartları).
- Fake/sahte veri: sayaç hedef değerleri (5, 3, 500, 0) tamamen mockup'a hardcoded, gerçek sistem durumunu yansıtmıyor.

### sec-overview (file 14 ve file 21/22'de var, farklı derinlikte)
**File 14 (zengin versiyon):**
- 4 stat kartı: "Toplam Yatırılan (demo)" `#cardInvested` = "4.230,55 USDT", "Kullanılabilir Bakiye" `#cardBalance` = "5.769,45 USDT", "Demo PnL (canlı fiyatla)" `#cardUpnl` = "+$0,00", "Bugünkü Kâr" `#cardToday` = "+0,00 USDT" — tümü hardcoded başlangıç değerleri, "(demo)" etiketli.
- "Canlı Piyasa Grafiği" paneli: `TradingView Lightweight Charts` chip'i, sembol seçici (`#symPickerBtn` → `#marketPanel` açılır panel: arama kutusu `#mktSearch`, sonuç listesi `#mktList`, sütunlar: Çift/Fiyat/24s %/Hacim), interval çubuğu `#ivBar`, indikatör çubuğu `#ovIndBar` (SMA/EMA/Bollinger/Hacim/RSI/MACD chip'leri, `applyIndicators` ile aç/kapa), grafik container `#ovChart` (lightweight-charts candlestick, gerçek Binance klines veya `seedSim` fallback).
- "Kâr Grafiği (demo hesap)" paneli: Günlük/Haftalık/Aylık chip seçici (`#periodBar`), `<canvas id="profitChart">` — grafiğin veri kaynağı script'in görülen kısmında bulunamadı (muhtemelen sahte/placeholder).
- "Canlı Sistem Akışı" paneli: `#feedList` (son 9 olay, `addFeed()` ile eklenen renkli log satırları: info/ok/warn/err tonları), alt kısımda "Veri Modu" (`#feedMode`: canlı/bağlanıyor/simülasyon) ve "Sonraki Funding" sayaç (`#fundCount`, "--:--:--" placeholder, gerçek değeri hesaplanmıyor).
- "Açık İşlemler (özet)" paneli: `#miniDeals` grid (mini kartlar), "Tümünü gör →" linki `data-goto="deals"` ile deals sekmesine atlıyor.
- Fake data: cardInvested/cardBalance başlangıç sayıları hardcoded demo rakamları; `appData.balance=5769.45, invested=4230.55` gibi sabitler JS'de tanımlı.

**File 21/22 (sadeleştirilmiş "Genel Bakış"):**
- Tek panel: "CANLI PİYASA · TRADINGVIEW LIGHTWEIGHT CHARTS" başlığı + sembol select (`#ovSym`: BTCUSDC/ETHUSDC/SOLUSDC) + `#ovChart`.
- 4 stat kartı (file 21 only): "PORTFÖY PnL" `#oPnl`="+$0", "AKTİF BOT" `#oBots`="6", "AÇIK DEAL" `#oDeals`="5", "PARİTE SKORU" `#oParity`="%78" — sabit placeholder metinler, güncellenmiyor (file 22'de bu 4-kart grid'i yok, sadece hero'daki 3 mini stat var: `#hBots`, `#hPnl`, `#hParity`).
- Fark: file 14'teki feed/mini-deals/profit-chart tamamen kaldırılmış; file 21/22 çok daha minimal.

### sec-bots
**File 14:** "Bot Kartları" başlığı, "Bir karta tıklayın → tam sayfa bot detayı açılır" alt yazı, şablon chip'leri (🛡️ Muhafazakar / ⚖️ Dengeli / 🔥 Agresif — `data-tpl`), `#botGrid` (JS ile doldurulan bot kartları — 6 hardcoded bot: `appData.bots` dizisi, her biri `id, name, dir, status, profit, perf24, deals, winRate, totalDeals, maxDD, upDays` alanlarıyla, ör. "BTCUSDC · Hybrid DCA+Grid" profit 1240.55, winRate 78, maxDD 12.4 — **tamamen kurgusal/sahte istatistikler**).

**File 21/22:** Sadece `#botGrid` container, aynı 5-6 elemanlı sabit `bots` dizisinden (`{n:'BTCUSDC·Hybrid',p:1240}` vb.) render ediliyor, kart içinde sadece isim + PnL + "RUNNING · paper" etiketi.
- Fake data: her iki versiyonda da bot listesi ve performans metrikleri (winRate, maxDD, profit) tamamen JS içinde sabit kodlanmış, hiçbir backend'den gelmiyor.

### sec-botdetail (yalnız file 14)
- Geri dön butonu `#bdBack` ("← Botlarım"), başlık `#bdTitle`, tip chip `#bdType`, durum chip `#bdStatus`, uPnL `#bdUpnl`, bot aç/kapa switch `#bdSwitch`.
- "DİĞER BOTLAR · hızlı geçiş" paneli: `#botChipBar` (chipbar, diğer botlara hızlı geçiş).
- `#bdStats` (grid, 6 sütun — bot performans metrik kartları).
- `#bdSpark` (canvas sparkline).
- "Canlı Grafik · Bot Parametre Overlay" paneli: `#botIndBar` indikatör çubuğu + `#botChartPage` (lightweight-charts, muhtemelen giriş/TP/SL/likidasyon price-line overlay'leri `setOverlays()` ile).
- "Aktif Ayarlar (tüm parametreler)" `#bdSettings` (grid, mono font, key-value).
- "Bu Botun Aktif Deal'ları" `#bdDeals`.
- Fake data: tüm bot parametreleri `botParams` sabit objesinden (id→{sym,type,dir,lev,bo,so,soCount,dev,stepScale,volScale,tp,sl,entry,margin}) geliyor.

### sec-deals
**File 14:** "Active Deals" başlığı + "Smart Trade Terminal" toggle butonu (`#stToggle`) → açılır panel `#stPanel` (manuel pozisyon formu: Sembol select, Yön select LONG/SHORT, Boyut input, TP% input, "Pozisyon Aç" butonu — tamamen demo, gerçek emir göndermiyor). Tablo `#dealsBody`, sütunlar: Sembol, Yön, Lev, Ort. Giriş, Güncel, PnL%, SO Doluluk, TP Mesafe, Aksiyon.
**File 21/22:** Sade tablo, sütunlar: Sembol, Yön, Ort. Giriş, Güncel, PnL%, SO — Smart Trade paneli ve Lev/TP Mesafe/Aksiyon sütunları kaldırılmış.
- Fake data: `appData.deals` (file14) / `deals` (file 21/22) sabit dizi — 3-5 kurgusal deal (BTCUSDC LONG entry 64250, vb.), fiyat güncellemesi canlı Binance verisiyle simüle ediliyor ama deal'ların kendisi hiç gerçek değil.

### sec-dealdetail (yalnız file 14)
- Geri buton `#ddBack`, başlık `#ddTitle`, yön chip `#ddSide`, PnL `#ddPnl`, "CANLI FİYAT" livebadge.
- "DİĞER İŞLEMLER" hızlı geçiş chipbar `#dealChipBar`.
- `#ddInfo` (grid, 8 sütun bilgi kartı).
- "İşlem Grafiği" paneli: `#dealIndBar` + `#dealChartPage`.
- "Seviyeler" paneli `#ddLevels` (grid, SO seviyeleri muhtemelen).
- "Aksiyonlar & Bağlı Bot" paneli: "➕ Fon Ekle (manuel SO)" butonu `#ddAdd`, "🚨 Panic Sell" butonu `#ddPanic`, bağlı bot bilgisi `#ddBotLink`.

### sec-dca (yalnız file 14)
- Başlık "Bot Kur — DCA Yapılandırması", şablon chip'leri (Muhafazakar/Dengeli/Agresif) + "💾 Botu Kaydet" butonu.
- "Parametre Önizleme Grafiği" paneli: parite select `#dcaPair`, "📍 Girişi Güncel Fiyata Sabitle" butonu `#pinEntry`.
- 5 mini-stat: "ORT. MALİYET" `#lgAvg`, "TAKE PROFIT" `#lgTp`, "STOP LOSS" `#lgSl`, "LİKİDASYON" `#lgLiq`, "TOPLAM MARJİN" `#lgMargin` — hepsi "—" başlangıç, form değiştikçe JS ile hesaplanıp dolduruluyor (canlı hesap, sahte değil — girdiye bağlı deterministik matematik).
- İndikatör çubuğu `#dcaIndBar` + grafik `#dcaChart` (price-line overlay'li).
- `#dcaForm` (grid, JS ile üretilen tüm DCA form alanları — script'in görülen kısmında liste yok, muhtemelen BO/SO/SO-count/deviation/step-scale/vol-scale/TP/SL/budget/cooldown gibi alanlar, file 14'ün backtest formundakiyle aynı isimlendirme).

### sec-datastore (yalnız file 14) — "Faz 1 · Veri Pipeline — LAB"
- "API ANAHTARI GEREKMEZ" livebadge.
- Bölüm 1 "Parite Panosu": "🔄 Yeniden Test Et" butonu `#probeBtn`, `#pairBoard` grid — her parite için Binance spot/futures ticker sorgulanıp (`probePair`) spot✓/futures✓ rozetleri, fiyat, "depoda: N snapshot" bilgisi; XMR gibi delisted paritede kırmızı uyarı metni "Bu çift Binance'te listeli değil…" gösteriliyor. **Bu gerçek API çağrısı (fake değil), ama sonuç arayüz metni hardcoded senaryo (XMR) varsayımına göre yazılmış.**
- Bölüm 2 "Doğrulama Laboratuvarı": parite chip'leri `#labChips`, "🔬 Çek & Doğrula" butonu `#labRun` → gerçek Binance kline çekip `validateKlines()` ile 6 kural kontrolü (satır sayısı, monoton zaman, tekrarsızlık, OHLC tutarlılığı, NaN kontrolü, boşluk oranı) — sonuç `#labResult` chip'leri (✓/✗ renkli) + `#pipChart` grafiği.
- Bölüm 3 "Toplu İndirme Planı": çift arama/ekleme (`#dsSearch`→`#dsPickList`), hızlı-ekle chip'leri (BTCUSDC/ETHUSDC/SOLUSDC/XRPUSDC/XMRUSDC), interval chip'leri (1m/5m/1h), plan özeti kutusu (KAPSAM/DOSYA SAYISI/TAHMİNİ BOYUT — `curPlan()` ile hesaplanan, gerçek matematik ama gerçek indirme yapmıyor), 4 buton: "📋 Manifesto" (JSON), "🐍 Python Script" (gerçek çalışabilir fetch script'i üretiyor — `makePythonScript()`), "🐚 Bash Script" (`makeBashScript()`), "⬇ İndirdim → Depoya Kaydet" (`localStorage`'a sahte "snapshot" kaydı ekliyor — **kullanıcı gerçekte indirmese bile buton basılırsa "kayıtlı" gibi gösteriliyor, bu bir dürüstlük/fake-data riski**). Sağ tarafta klasör yapısı `<pre>` bloğu ve doğrulama kuralları listesi (statik metin).
- Bölüm 4 "Kayıtlı Yerel Depo": `#dsRegistry` — `localStorage` key `hg_datastore_v1` içindeki "snapshots" listesi, her kayıt için GÜNCEL/GERİDE rozeti, "⬆ Artımlı Güncelle" butonu (`data-dsact="topup"`).

### sec-backtest (file 14 zengin; file 21/22 çok sadeleştirilmiş)
**File 14 — "Faz 4 + 4.5 · Gerçek Backtest & Optimizasyon":**
- "GERÇEK VERİ · ANAHTARSIZ" livebadge + "SONUÇLAR HESAPLANIR" simbadge.
- `#btDataSrc` bilgi çubuğu.
- 3 sütunlu form: (1) Veri Kaynağı — parite/interval/gün-aralığı select'leri + "📥 Geçmiş Veriyi Çek (Binance)" butonu `#btFetch` (gerçek Binance REST kline sayfalama, `btFetchData()` — retry/host fallback, 60 sayfa limiti, dedup+sort), durum metni `#btFetchStatus`, doğrulama chip'leri `#btValid`; (2) "DCA Strateji Parametreleri" — 10 sayısal input (Base Order, Safety Order, Max SO, İlk Sapma%, Step Scale, Volume Scale, TP%, SL%, Bütçe, Cool-down); (3) "Maliyet Modeli & Korumalar" — Maker%/Taker%/Slipaj bps input'ları + "ANTİ-HALÜSİNASYON KURALLARI" statik liste (6 madde: doğrulama kapısı, komisyon düşümü, slipaj, look-ahead yok, nakit yetersizse SO atlanır, min 5 işlem + OOS şartı) + "▶ BACKTEST'İ ÇALIŞTIR" butonu `#btGo`.
- Sonuç bölümü `#btResults` (başlangıçta gizli): 9 metrik kartı `#btMetrics` (Net Kâr/ROI/İşlem/Win Rate/Profit Factor/Max DD/Sharpe/SO Dolum/Bütçe), Equity eğrisi `<canvas id="btEquity">` (custom canvas çizim, tepe-drawdown kesikli çizgi overlay'i), Fiyat+işlem noktaları grafiği `#btPriceChart2` (lightweight-charts + giriş/çıkış arrow marker'ları), İşlem geçmişi tablosu `#btTradesBody` (son 60 işlem: Giriş/Çıkış/Giriş Fx/Çıkış Fx/SO/Sebep/PnL/PnL%), "🚀 Bu parametreleri canlı bota kopyala" butonu `#btDeploy` (→ `bots` sekmesine geçiş + toast, gerçek bot oluşturmuyor).
- Optimizasyon alt-sekmeleri (`#btpTabs`): "Parametre Optimizasyonu" / "Walk-Forward" / "Monte Carlo".
  - **Parametre Optimizasyonu**: 10 min/max input (TP/Sapma/Step/Vol/SO adet), Tarama Tipi select (Rastgele 100/250 aday, Izgara ≤300 kombinasyon), Amaç Fonksiyonu select (Sharpe/Net/Profit Factor), Walk-Forward switch `#opWf`, "🧬 OPTİMİZASYONU BAŞLAT" butonu — gerçek client-side backtest motoru (`runDcaBacktest`) her aday için tekrar çalıştırılıyor (chunk'lı async loop, ilerleme çubuğu `#opProgressBar`/ETA), sonuç tablosu `#optResults` (14 sütun: #/TP%/Sapma%/Step/Vol/SO/İşlem/Net/Win%/Sharpe/MaxDD/OOS Net/OOS Sharpe/aksiyon — "→ DCA formuna" apply butonu), gerçek ısı haritası `#optHeat` (TP×Sapma ort. skor, renk kodlu heatcell'ler, `.heatcell:hover` scale animasyonu).
  - **Walk-Forward**: `#wfRow` — IS/OOS net+Sharpe karşılaştırması, "✓ DAYANIKLI" / "⚠ ZAYIF" / "⚠ OVERFIT" rozetleri (gerçek hesaplanan degrade yüzdesine göre).
  - **Monte Carlo**: `#mcStats` (P5/Medyan/P95/Negatif bitiş olasılığı — gerçek işlem PnL'lerinin 500x bootstrap'ı, `renderRealMC()`), histogram `#mcCanvas`.
- Not: Bu sekmedeki hesaplamalar **gerçek Binance geçmiş verisi üzerinde gerçek matematikle** yapılıyor (fake değil) ama motor tamamen tarayıcıda JS ile simüle ediliyor, gerçek exchange emri yok; arayüz bunu "SONUÇLAR HESAPLANIR" rozetiyle doğru şekilde etiketliyor.

**File 21/22 — çok sade "Backtest" sekmesi:** Tek buton "▶ Çalıştır" `#btRun`, sadece 4 metrik kartı (Net/Win%/MaxDD/İşlem) `#btMetrics`. Motor basitleştirilmiş `DCAEngine` class'ı (file 14'ün tam motorundan çok daha basit, komisyon/slipaj yok). Fake data yok ama çok yüzeysel/iskelet.

### sec-modules (yalnız file 14)
- Başlık "3Commas'ın Ötesine Geçen Modüller", `#modGrid` (JS ile doldurulan kart grid'i — script'in görülen bölümünde içerik tanımı bulunamadı, muhtemelen adaptif/AI-destekli modül tanıtım kartları, `.modmini` class'ı CSS'te tanımlı).

### sec-ai (file 14 ve file 17'de var, farklı bağlamda)
**File 14 — "Bot AI · Copilot":**
- "🔧 GELİŞTİRME AŞAMASI: KURGUSAL" simbadge + "🚀 DEPLOY'DA: GERÇEK LLM + VEKTÖR HAFIZA" livebadge — **mockup kendi kendini açıkça "kurgusal" olarak etiketliyor**, bu iyi bir dürüstlük sinyali.
- Sohbet paneli: yeşil ping noktası + "Bot AI" etiketi + "model: kurgusal-hg-1" (fake model adı, açıkça etiketlenmiş), `#aiChat` (mesaj listesi), öneri chip'leri `#aiChips`, input `#aiInput` + "Gönder" butonu `#aiSend`.
- "🧠 Kalıcı Hafıza Bankası" paneli: `#memCount`, "HAFIZADAN OKUNAN" `#memReads` ("0 sorgu"), "TAHMİNİ TASARRUF" `#memTokens` ("~0 tok"), "📸 Durum Snapshot'ı Al" `#memSnap`, "📋 JSON Dışa Aktar" `#memExport`, hafıza listesi `#memList` — `addAiMemory()` fonksiyonu, backtest/optimizasyon sonuçlarını otomatik "hafızaya" ekliyor (yalnızca tarayıcı oturumu içinde, kalıcı değil — "kalıcı" etiketi yanıltıcı olabilir).

**File 17 — "🤖 AI Önerileri" (Strateji Laboratuvarı sekmesi):**
- `#aiRecs` — 3 adet **tamamen hardcoded** öneri kartı (`renderAI()` içinde sabit dizi): " Hybrid ağırlığını artır" (emerald), "⚠️ XRP DCA'da SL sıkılaştır" (amber), "🔬 Parite eşiği kontrolü" (cyan). Bu öneriler hiçbir gerçek hesaplamaya dayanmıyor, düz metin şablonu. **Açık fake-data örneği: AI önerisi gibi sunulan statik metin.**

### sec-risk (yalnız file 14)
- "⛔ Circuit Breaker" paneli: "Korumayı Aktifleştir" switch `#armSw`, "Günlük Drawdown" `#ddNow` (sabit "-%1,8") / "Eşik" `#ddThreshVal` (sabit "-%5,0"), ilerleme çubuğu `#ddBar` (sabit %36 width), range slider `#ddThresh` (2-15 arası), "⛔ GLOBAL KILL-SWITCH" büyük buton `#killBig`.
- "⚠️ Liquidation Engine" paneli: 3 statik chip (Cross/Isolated MM, Tiered MMR, Auto-Deleverage), `#liqList` (JS ile doldurulacak, tanım görülmedi).
- "🔗 Korelasyon Matrisi" paneli: `#corrGrid` (6x6 grid, JS ile doldurulacak — muhtemelen rastgele/hardcoded korelasyon değerleri).
- "📡 Funding & Spread Tarayıcı" paneli: tablo `#fundBody`, sütunlar Sembol/Funding/Spot/Futures/Baz.
- Fake data riski: `-%1,8` drawdown ve `%36` bar genişliği CSS/HTML'de hardcoded (JS ile güncellenmediyse statik sahte veri olarak kalır).

### sec-core (yalnız file 14) — "Çekirdek & Modül Mimarisi"
- "ÇEKİRDEK DONMUŞ v2" chip.
- "Mimari Topoloji" paneli: `#coreTop` / `#coreBottom` (grid, 4 sütun modül kutucukları) + ortada animasyonlu "EVENT BUS · PROTOKOL v2" şeridi — 3 adet `.busdot` elemanı `@keyframes busdot` ile soldan sağa akan noktalar (tamamen dekoratif animasyon, gerçek event bus trafiğini temsil etmiyor).
- "Event Bus Trafiği (simüle)" paneli: `#busRate` ("— olay/dk"), `#busFeed` (log listesi) — panel başlığında "(simüle)" ibaresi açıkça var, dürüst etiketleme.
- "Modül Kayıt Defteri" `#coreRegistry` (grid, 2 sütun).
- "➕ Yeni Strateji Plugin'i Ekle" formu: Modül Adı, Strateji Ailesi select (DCA/Grid/Arbitraj/Sinyal-hibrit/Özel), Açıklama, 2 adet parametre-adı+varsayılan-değer çifti, "🔌 Plugin'i Kaydet (pasif başlar)" butonu — tamamen UI iskeleti, gerçek plugin sistemi yok.

### sec-grid (yalnız file 14) — "Infinity Grid + Hybrid Engine"
- Grid görselleştirme: `<canvas id="gridCanvas">`, 3 legend chip'i (Dinamik Alt Taban/Grid Adımları/Dinamik Üst Tavan).
- "Hybrid Engine Fazları" paneli: 3 adım kartı (`#ph-0`/`#ph-1`/`#ph-2` — FAZ 1 DCA, FAZ 2 Infinity Grid, FAZ 3 Kar Realizasyonu), `.ph-step.on`/`.ph-step.done` durumu geçişli CSS.
- Kontrol paneli: "Grid Adımı" range slider `#gridStepRange` (0.2-3%, gösterge `#gridStepVal`), "Dynamic Floor Auto-Adjustment" switch `#floorSw`, "Futures Rebalancing" switch `#rebSw`, log alanı `#phaseLog` ("Hybrid Engine hazır").

### sec-deploy (file 14 ve file 21 var, farklı derinlik)
**File 14:**
- Uyarı: "Bu sekme hedef deployment senaryosunu canlandırır; metrikler demo amaçlıdır." — açık dürüstlük etiketi.
- `#svcGrid` — servis kartları (postgres/redis/backend/frontend/backtest_worker/bot_ai), her biri yeşil ping + "RUNNING" livebadge (**tamamen sahte "RUNNING" durumu, gerçek servis kontrolü yok**).
- `docker-compose.yml` kod bloğu (statik `<pre>`, gerçek örnek yapı, .env yorum notu "TESTNET anahtari BURADA (sohbette paylasilmaz)").
- "Yayına Alma Terminali (canlandırma)" paneli: `#deployTerm` (terminal benzeri log alanı) + "↻ tekrar" butonu `#rerunBtn` — muhtemelen sahte/canlandırılmış deploy log satırları yazdırıyor (script'in görülen kısmında tanım yok ama "canlandırma" kelimesi ile açıkça sahte olduğu belirtiliyor).

**File 21 — "Kurulum & Durum" (sec-status olarak yeniden adlandırılmış) + ayrı "Deploy" sekmesi:**
- Hero: "KURULUMA HAZIR" + "SUNUCU DEPLOY HAZIR" chip'leri, 3 mini-stat ("%100 FRONTEND", "14/14 MOTOR TESTİ", "FAZ 8 BACKEND BEKLİYOR").
- "KURULUM REHBERİ · SUNUCU DEPLOY" — statik `<pre>` blok: `scp`, nginx config, certbot, docker compose komutları (gerçek örnek, çalıştırılmıyor).
- Ayrı "Deploy" sekmesi: `#svcGrid` (aynı 6 servis, hepsi "RUNNING" — file 14 ile aynı sahte-yeşil desen).
- File 22'de "Kurulum Rehberi" ve "%100/14/14/FAZ8" istatistik kartları tamamen kaldırılmış; sadece hero metni ve `#svcGrid` kalmış.

### sec-tests (yalnız file 21/22) — "Motor Testleri" / "Motor Birim Testleri"
- "▶ Testleri Çalıştır" butonu `#runTests` → gerçek client-side unit testleri (`tests` dizisi, gerçek `assert`-benzeri fonksiyonlar, DCAEngine/GridEngine/CostEngine sınıflarını test ediyor).
- File 21: 14 test (DCA ilk mumda BO, DCA düşüşte SO, DCA TP, DCA SL, Grid INIT, Grid SELL, Grid BUY, Maliyet taker/maker fee, Maliyet LONG/SHORT liq, Arbitraj sinyal, ATR adaptif, Rejim TREND).
- File 22: sadece 7 test (Maliyet/Arbitraj/Gelişmiş testleri çıkarılmış — CostEngine, ATR, regime fonksiyonları hiç tanımlı değil).
- Sonuç listesi `#testList`: her satır `.test-pass`/`.test-fail` sol-border rengi, ✓/✗ ikonu, PASS/FAIL chip'i. Bu **gerçek** (fake olmayan) test çalıştırma — motor mantığı gerçekten test ediliyor, sadece tarayıcıda.

### sec-exec (yalnız file 21/22) — "Execution Console · Dry-Run" (file 18'in küçültülmüş versiyonu, sec id farklı: `sec-exec` vs file18'in `sec-conn`/`sec-orders`/`sec-execlog`/`sec-history`)
- API Key/Secret password input'ları (placeholder "Testnet API Key", gerçek kaydetme yok), "Mod: DRY-RUN · Gerçek emir: KAPALI" bilgi kutusu.
- "EMİR YAŞAM DÖNGÜSÜ" log alanı `#execLog` — boş, dinamik doldurma kodu bu sadeleştirilmiş versiyonda görünmüyor (file 18'deki tam emir yaşam döngüsü mantığı yok).

### sec-lab (yalnız file 21/22) — "Strateji Lab" (file 17'nin küçültülmüş versiyonu)
- Sadece "STRATEJİ KARŞILAŞTIRMA · AYNI VERİ" — `<canvas id="cmpChart">`, DCA(yeşil)/Grid(camgöbeği) çizgileri (file 21'de Hybrid de var, file 22'de sadece DCA/Grid). `renderCompare()` gerçek DCAEngine/GridEngine ile hesaplıyor (fake değil, ama sonuç sadece coin miktarı × kapanış fiyatı gibi kaba bir yaklaşım).

---

## PART 1b — file 17 (Strateji Laboratuvarı) — bağımsız sayfa, üstte ayrıca özetlendi

Bu dosya sidebar yerine üstte tab bar kullanıyor (`data-tab`), 4 sekme: Portföy / Strateji Karşılaştırma / Konfigüratör / AI Önerileri. Hero bölümünde bir tasarım-görsel (qwenlm.ai CDN'den hero image) + "FAZ 7.5+ · AKTİF" ve "VERİ: CANLI BINANCE" chip'leri.

- **sec-portfolio**: Donut grafik `#allocDonut` (custom canvas çizim `drawDonut()`) + lejant `#allocLegend`; "PORTFÖY ÖZETİ" `#portSummary` (Toplam PnL/Aktif Bot/Kazançlı Bot/Zararlı Bot); "BOT BAZINDA CANLI PnL" `#botRows` (her bot için progress-bar genişliği `Math.abs(pnl)/maxAbs*100`). Veri kaynağı: **tamamen hardcoded `bots` dizisi** (5 sahte bot, sabit pnl/alloc değerleri) — hiç API çağrısı yok, "CANLI PnL" etiketi yanıltıcı çünkü değerler sabit.
- **sec-compare**: Parite select + "▶ Karşılaştır" butonu `#cmpRun` → gerçek Binance kline (veya `seedSim` fallback) üzerinde 3 motor (`runDCA`/`runGrid`/`runHybrid`) çalıştırılıp `#cmpChart`'a çiziliyor + metrik tablosu `#cmpTable` (Strateji/Net/ROI/Win%/MaxDD/Sharpe/İşlem). En iyi Sharpe'a göre toast mesajı.
- **sec-config**: "YENİ STRATEJİ KONFİGÜRATÖRÜ" formu (Strateji Tipi DCA/Grid/Hybrid, Parite, Yön LONG/SHORT/BIDIRECTIONAL, BO/SO/MaxSO/Sapma%/TP%/SL% inputları), "🚀 Stratejiyi Fırlat (Paper)" butonu → `launched` dizisine ekliyor (yalnızca bellekte, sayfa yenilenince kaybolur), "🔬 Önce Parite Testi" butonu → sadece toast gösteriyor, gerçek işlev yok.
- **sec-ai**: Yukarıda Part 1'de detaylandırılan 3 hardcoded öneri kartı.

## PART 1c — file 18 (Testnet Execution Console) — bağımsız sayfa

4 sekme: Bağlantı / Emir Yönetimi / Execution Log / Emir Geçmişi. Hero'da "DRY-RUN · GERÇEK EMİR YOK" + "ANAHTAR BEKLENİYOR" chip'leri, 3 mini-stat (Aktif Emir/Dolum/Mod).

- **sec-conn**: API Key/Secret password input'ları + "Anahtarları Kaydet (.env)" butonu (**yalnızca `mode` JS değişkenini 'TESTNET' yapıyor, hiçbir gerçek .env yazımı yok — buton metni yanıltıcı olabilir**), "Bağlantıyı Test Et" butonu → rastgele ping değeri gösteriyor (`rnd(18,60)+' ms'` — **sahte ping, gerçek network testi değil**). "FAZ 8 GEÇİŞ KOŞULLARI" statik checklist.
- **sec-orders**: Order book paneli `#obBids`/`#obAsks` — **tamamen rastgele üretilen bid/ask fiyat+miktar** (`Math.random()`, gerçek order book verisi değil, 1.2sn'de bir yeniden çiziliyor); "YENİ EMİR (DRY-RUN)" formu (Sembol/Yön/Tip/Miktar/Fiyat) + "📨 Emir Ver (DRY-RUN)" butonu → emir yaşam döngüsü simülasyonu: NEW→(600ms sonra)WORKING→(1.5-3.5sn sonra)FILLED, PnL = `(Math.random()-0.45)*qty*price*0.01` (**tamamen rastgele PnL, gerçek fiyat hareketine dayanmıyor**); "AKTİF EMİRLER" listesi `#activeOrders` (İptal butonu ile).
- **sec-execlog**: `#execLog` (zaman damgalı renkli log satırları, "Temizle" butonu).
- **sec-history**: Tablo `#histBody` (Zaman/Sembol/Yön/Tip/Miktar/Fiyat/Durum/PnL).
- Genel not: Bu sayfanın adı "Testnet Execution Console" olsa da hiçbir gerçek testnet API çağrısı yapmıyor; tüm emir yaşam döngüsü, ping süresi ve order book tamamen `Math.random()` ile üretiliyor. Arayüz "DRY-RUN" rozetiyle bunu kısmen etiketliyor ama "Bağlantıyı Test Et" ve order book gibi bazı öğeler gerçek veri izlenimi verebilir.

---

## PART 2 - Mevcut DCABOT Frontend Envanteri (frontend/src/*.tsx, test haric)

Genel mimari: App.tsx (2920 satir) tek buyuk bilesen, useReducerGroup custom hook'uyla gruplu state yonetimi yapiyor; appSections.ts 5 ana nav bolumu taniyor (overview, bots, market, events, settings) + ayri bir lab bolumu (LAB_SECTION, ana nav'dan gorsel olarak ayrik). SectionNav.tsx bu iki grubu ayri nav bloklari olarak render ediyor.

AdvancedTools.tsx bir details/summary sarmalayicisi: varsayilan kapali, 3 grup basligi kullaniyor - tools.classic.label = "Klasik Gorunum (eski panel + deal/exit detayi)" (EN: "Classic View (legacy panel + deal/exit detail)"), tools.strategy.label = "Strateji Arastirma Araclari", tools.planningRisk.label = "Planlama ve Risk Araclari" (bkz. frontend/src/locales/strings.xml:262-264). Yani uc grup da "gelismis/katlanir" ama yalnizca ilki acikca "Klasik/legacy" olarak etiketlenmis.

Asagida her non-test .tsx dosyasi icin ozet. "Wiring" sutunu App.tsx icindeki kullanim noktasini gosterir.
| Dosya | UI / Icerik | Veri/props kaynagi | App.tsx'te wiring | Klasik mi / aktif mi |
|---|---|---|---|---|
| App.tsx | Ana shell: sidebar+topbar+section router, tum state ve fetch orkestrasyonu | Tum alt panellerin state'i burada tutulur | kok bilesen | Aktif (kok) |
| appSections.ts | 5 nav bolumu tanimi + ayri LAB_SECTION | Statik veri | App.tsx importlar sectionById | Aktif (nav yapilandirmasi) |
| SectionNav.tsx | Sol sidebar nav linkleri (ana 5 + ayri Lab linki) | APP_SECTIONS, LAB_SECTION, i18n t() | SectionNav sidebar icinde | Aktif |
| AdvancedTools.tsx | Katlanir details grup sarmalayici | title, children prop | bots bolumunde 3 kez (classic/strategy/planningRisk) | Aktif ama icerigin bir kismi Klasik etiketli |
| HeroChartPanel.tsx | Ana grafik paneli (hero) | bars, status, error, livePrice, symbolLabel, canLoad, loadBusy, onLoad, overlayLines | bots (createView null), bots botDetail, bots createView, market bolumlerinde tekrar tekrar | Aktif, merkezi bilesen |
| BotTable.tsx | Bot listesi tablosu + BotContextHeader (profil ozeti) | rows (botId/name/sessionCount/selected), busy, callback'ler | bots ana gorunumde BotContextHeader + BotTable | Aktif |
| BotWizard.tsx | DCA bot olusturma sihirbazi (cok alanli form, taslak localStorage, kademeli-TP editoru, optimize presetleri) | busy, error, callback'ler, chartBars, optimizeDatasetId/ProfileId | BotCreateView icinde renderForm olarak DCA tipi icin | Aktif (yeni olusturma akisi) |
| BotCreateView.tsx | Bot olusturma sayfasi shell (chart + form secici: DCA/SIGNAL/FUTURES/diger) | botType, chart props, renderForm, aiRecommenderReady | bots bolumunde createView !== null | Aktif |
| BotDetailView.tsx | Tek bot detay sayfasi (grafik, taslak parametreler, likidasyon durumu) | botId, profile, botIds, draftParams, liquidation*, renderChart | bots bolumunde botDetailId !== null | Aktif |
| DealDetailView.tsx | Tek deal detay sayfasi | dealId, lifecycle, history, replayVerified, busy, error | bots bolumunde dealDetailId !== null | Aktif (Klasik DealPanel akisindan aciliyor) |
| BotPanel.tsx | Eski/klasik bot kayit+liste+baglama+kontrol paneli (register/select/updateLists/bind/check) | botIds, profile, sessions, check, callback'ler | AdvancedTools tools.classic.label icinde | Klasik (legacy) |
| DealPanel.tsx | Eski deal olusturma/event ekleme/replay/toplu-aksiyon paneli | dealId, lifecycle, history, bulkResults, callback'ler | tools.classic grubunda | Klasik (legacy) |
| ExitPanel.tsx | Trailing/percent/breakeven exit baglama paneli | binding, percent, breakeven, callback'ler | tools.classic grubunda | Klasik (legacy) |
| forms.tsx | Ortak form primitifleri (Section, FieldGroup, NumericParameter, ToggleSwitchRow, StepperInput, BudgetSlider, LabeledSlider, SegmentedControl, QuickPercentChips, RiskCritical, AdvancedDetails) | Generic prop'lar | Hem eski hem yeni formlarda (NumericParameter dogrudan App.tsx Bot studyosu formunda) | Aktif, paylasilan altyapi |
| RebalancePanel.tsx | Basit rebalance hesaplayici (holdings/prices metin girisi to valuation) | valuation, metin state, callback | tools.strategy grubunda | Aktif |
| RebalancePlanPanel.tsx | Gelismis rebalance plan + disclosure + aday listesi | plan, disclosure, candidates, callback'ler | tools.strategy grubunda | Aktif |
| TemplatePanel.tsx | Strateji sablonu import/sec/bagla/diff paneli | templates, detail, bindResult, diffRows | tools.strategy grubunda | Aktif |
| SignalPanel.tsx | TradingView webhook sinyal hash/assess/bind paneli | payloadHash, readiness, candidate | tools.strategy grubunda VE BotCreateView icinde SIGNAL tipi formu olarak | Aktif (iki yerde) |
| FuturesPanel.tsx | Vadeli islemler grid/pnl/trailing/funding paneli (coklu view tipi) | grid, pnl, trailing, funding, callback'ler | tools.strategy grubunda VE BotCreateView icinde diger tip formu olarak | Aktif (iki yerde) |
| FuturesDcaForm.tsx | Futures DCA formu (Pionex-stili grid seviyeleri ustte) | grid, busy, error, onGrid | BotCreateView icinde FUTURES tipi formu | Aktif |
| TwoLegPanel.tsx | Iki-bacakli (hedge) oturum paneli (start/fill/recovery/timeout/replay) | sessionId, projection, callback'ler | tools.strategy grubunda | Aktif |
| RecurringPanel.tsx | Tekrarlayan zamanlama projeksiyon paneli | schedule, busy, error, onProject | tools.planningRisk grubunda | Aktif |
| RiskPanel.tsx | Risk aciklama + canary durumu + kill-switch paneli | explanation, canary, callback'ler | tools.planningRisk grubunda | Aktif |
| BackupPanel.tsx | Yedek alma/dogrulama paneli | backups, verdict, busy, callback'ler | events bolumunde | Aktif |
| TimelinePanel.tsx | Zaman cizelgesi cerceve/seek paneli | frame, busy, onSeek | events bolumunde | Aktif |
| EventPanel.tsx | Denetim olay listesi paneli | events, busy, onRefresh | events bolumunde | Aktif |
| SavedRunsPanel.tsx | Kaydedilmis backtest kosulari liste/detay/karsilastirma/export (lazy-loaded) | view/runs/detail/compare/export prop'lari | events bolumunde, lazy() ile kod bolunmus | Aktif |
| DashboardPanel.tsx | Genel gosterge paneli | dashboard, busy, error, onRefresh | overview bolumunde | Aktif |
| SystemStatusCard.tsx | API/durum ozet karti (canary dahil) | apiStatus, datasets, canary | overview bolumunde | Aktif |
| HistoricalProfileSelector.tsx | Gecmis veri profili secici + HistoricalProfileStatus tipi | profiles, status, onChange | DatasetCatalogPanel uzerinden market bolumune bagli (dolayli) | Aktif (dolayli) |
| DatasetCatalogPanel.tsx | Veri seti katalogu, indirme isleri, run-plan, ActionTable, PreflightCard (lazy-loaded) | dataset/download/profile/simulation prop'lari | market bolumunde Suspense + lazy() | Aktif |
| HistoricalChart.tsx | Gecmis veri grafigi (bar secimi, taslak fiyat cizgisi) | data, status, simulation, selectedBarIndex, callback'ler | DatasetCatalogPanel icinden kullaniliyor (App.tsx'te dogrudan gorunmuyor) | Aktif (dolayli) |
| BinancePublicSnapshotPanel.tsx | Public testnet snapshot goruntuleyici | snapshot, status, error, onRetry | market bolumunde | Aktif |
| BinanceAccountPanel.tsx | Testnet hesap bakiyesi + acik emirler paneli | account, orders, status, onRetry | settings bolumunde | Aktif |
| SymbolSelector.tsx | Venue sembol arama/secim + son fiyat | symbols, count, selectedSymbol, lastPrice | market bolumunde | Aktif |
| PaperPanel.tsx | Paper-trading oturumu (aktiflestir/emir/dolum/market-refresh) | snapshot, prints, orderDraft, callback'ler | market bolumunde | Aktif |
| LiquidationStatusSection.tsx | Likidasyon durumu goruntuleme mantigi (tip guard + component) | LiquidationStatusView | BotDetailView uzerinden dolayli | Aktif (dolayli) |
| notifications.tsx | Bildirim store, toast yigini, banner, onay diyalogu, bildirim merkezi | NotificationStore sinifi + hook'lar | App.tsx genelinde (NotificationCenter, ToastStack, Banner, ConfirmDialog) | Aktif, capraz-kesen altyapi |
| i18n.tsx | TR/EN string tablosu, useI18n hook'u, I18nProvider | strings.xml parse eder | App.tsx kokten useI18n() | Aktif, capraz-kesen altyapi |
| LabPanel.tsx | Lab bolum iskeleti - yalnizca tanitim metni + tek Whale Wall Detection (Ilk Sakin - Yakinda) placeholder karti, risk onay mekanizmasi localStorage (dcabot.lab.risk_ack) | Yerel state (acknowledged) | activeSection === lab dogrudan LabPanel | Aktif ama icerik iskelet/placeholder |
| Badge.tsx | Kucuk renkli etiket bileseni (tone/label/title) | Generic | Cesitli panellerde kullaniliyor (dolayli) | Aktif, paylasilan atom |
| CandleChart.tsx | Mum grafigi + LiveTickStrip (canli tick seridi) bilesenleri | OHLC verisi, tick listesi | Dogrudan App.tsx'te gorunmuyor (dolayli, teyit edilmeli) | Aktif (dolayli, teyit edilmeli) |
| TradingChart.tsx | Genel amacli ticaret grafigi bileseni (bars/priceLines/markers) | bars, status, priceLines, markers | Dogrudan App.tsx'te gorunmuyor (dolayli, teyit edilmeli) | Aktif (dolayli, teyit edilmeli) |
| ExplanationSection.tsx | Salt-okunur aciklama listesi bileseni | explanations: ReadOnlyExplanation[] | Dogrudan App.tsx'te gorunmuyor (dolayli, teyit edilmeli) | Aktif (dolayli, teyit edilmeli) |
| renderWindow.tsx | useWindowedList hook + WindowExpander (daha fazla goster bileseni) | Generic liste pencereleme | Cesitli uzun listelerde kullanilabilir (dolayli) | Aktif, paylasilan altyapi |
| main.tsx | Uygulama giris noktasi (ReactDOM render) | - | - | Aktif (bootstrap) |

Not: CandleChart, TradingChart, ExplanationSection App.tsx'in okunan bolumunde dogrudan import edilmis gorunmuyor; App.tsx 2920 satir oldugundan bu ucu icin wiring App.tsx'in gorulmeyen kisimlarinda veya baska bilesenler icinde (orn. HeroChartPanel.tsx, RiskPanel.tsx) olabilir - bu belge bunu "teyit edilmeli" olarak isaretler, kesin degildir.

---

## PART 3 - Backend API Endpoint Envanteri (src/dcabot/server/api.py, 6916 satir)

Asagidaki liste @app.get/post/put/delete decorator'larinin grep taramasindan cikarilmistir (satir numaralari api.py icindeki tanim satiridir).

### Historical / Backtest / Dataset
- GET /api/historical-profiles (3748) - gecmis veri profilleri listesi (sabit-slice + sabit-limit profil tipleri).
- GET /api/datasets (4088) - veri seti katalogu listesi.
- PUT /api/dataset-selection (4156) - aktif dataset secimini gunceller.
- GET /api/datasets/{dataset_id}/preflight (4194) - secili dataset icin on-kontrol raporu.
- GET /api/datasets/{dataset_id}/chart-data (4201) - dataset icin grafik barlari.
- POST /api/datasets/{dataset_id}/draft-level (4261) - taslak seviye dogrulama.
- GET /api/datasets/{dataset_id}/run-plan (4298) - kosu plani (run plan) uretimi.
- POST /api/historical-runs/validate (4369) - gecmis kosu dogrulama.
- POST /api/historical-runs (4993) - gecmis simulasyon kosusunu kaydet.
- GET /api/historical-runs (5091) - kayitli kosu listesi.
- GET /api/historical-runs/{run_id} (5124) - kosu detayi.
- GET /api/historical-runs/{run_id}/export (5218) - kosu export (CSV/JSON).
- POST /api/historical-runs/{run_id}/reproduce (5284) - kosuyu yeniden uret.
- Satir 4773 ve 4871'deki isimsiz POST decorator'lari (fonksiyon adi grep ciktisinda ayri satirda oldugu icin gorunmedi) muhtemelen historical simulation/chart-preview ile ilgili; ayrica satir 5384'teki POST muhtemelen dataset-download baslatma - ileri inceleme (dogrudan dosya okuma) gerekir.
- GET /api/dataset-downloads/{job_id} (5412) - indirme isi durumu.
- POST /api/dataset-downloads/{job_id}/cancel (5427) - indirme isini iptal et.
- POST /api/data-quality (6895) - yuklenen CSV/ZIP icin veri kalite raporu (frontend'de DataQualityPanel).

### Bots (bot kayit/profil/oturum)
- POST /api/bots (6164) - yeni bot kaydi.
- GET /api/bots (6187) - bot id listesi.
- GET /api/bots/{bot_id} (6193) - bot profili.
- POST /api/bots/{bot_id}/lists (6202) - bot izin/parite listeleri guncelleme.
- POST /api/bots/{bot_id}/sessions (6218) - bot oturumu baglama.
- POST /api/bots/{bot_id}/check (6241) - bot parite kontrolu.

### Deals (deal yasam donguse)
- POST /api/deals (6257) - yeni deal olustur.
- POST /api/deals/bulk (6280) - toplu deal aksiyonu.
- POST /api/deals/{deal_id}/events (6296) - deal'a event ekle.
- POST /api/deals/{deal_id}/replay (6319) - deal gecmisini replay et.
- GET /api/deals/{deal_id}/timeline (6619) - deal zaman cizelgesi cercevesi.

### Exit / Trailing
- POST /api/exits/trailing (6334) - trailing exit bagla.
- POST /api/exits/trailing/percent-arm (6349) - yuzde-bazli trailing arm.
- POST /api/exits/trailing/percent-observe (6364) - yuzde-bazli trailing gozlem.
- POST /api/exits/breakeven (6379) - breakeven hesapla.

### Preview / Config
- POST /api/preview (5442) - DCA ladder onizleme hesabi (App.tsx'in ana calculate()/calculateCreate() fonksiyonlarinin hedefi).

### Rebalance
- POST /api/rebalance/valuation (5466) - holdings/prices degerleme.
- POST /api/rebalance/plan (5663) - rebalance plani uret.
- POST /api/rebalance/disclose (5678) - plan aciklama/onay.

### Paper Trading
- POST /api/paper/sessions (5487) - paper oturumu ac.
- POST /api/paper/sessions/{session_id}/orders (5510) - paper emir ver.
- POST /api/paper/sessions/{session_id}/fills (5526) - paper dolum kaydet.
- POST /api/paper/sessions/{session_id}/market-refresh (5549) - paper market fiyat yenile.

### Templates (strateji sablonlari)
- POST /api/templates/import (5578) - sablon ice aktar.
- GET /api/templates (5594) - sablon meta listesi.
- GET /api/templates/{template_id} (5604) - sablon detayi.
- GET /api/templates/{template_id}/export (5620) - sablon export.
- POST /api/templates/{template_id}/bind (5631) - sablonu bota bagla.
- POST /api/templates/diff (5647) - iki sablonu karsilastir.

### Signals (TradingView webhook + sinyal isleme)
- POST /api/signals/hash (5693) - sinyal payload hash'i.
- POST /api/signals/assess (5708) - sinyal hazirlik degerlendirmesi.
- POST /api/signals/candidates (5723) - sinyal aday uretimi.
- POST /api/signals/intake (5738) - sinyal alim (imza dogrulamali).
- POST /api/signals/webhook/tradingview (5772) - TradingView webhook endpoint'i.
- GET /api/signals/webhook/status (5812) - webhook durumu.
- GET /api/signals/webhook/intakes (5819) - alinan webhook kayitlari.
- POST /api/signals/indicators/cross (5829) - native indikator kesisim tespiti (signal_native_indicators.detect_crosses).
- POST /api/signals/webhook/{signal_id}/bind (5889) - webhook sinyalini bota bagla.

### Sweep / Optimize
- POST /api/sweeps/optimize (5846) - parametre taramasi optimizasyonu (sweep_optimize.optimize_parameters, sweep_orchestrator, trial_sampler).

### Futures (vadeli islemler - grid/trailing/funding)
- POST /api/futures/grid/levels (5913) - grid seviyeleri hesapla.
- POST /api/futures/grid/placement (5928) - grid emir yerlesimi degerlendirmesi.
- POST /api/futures/grid/position (5945) - grid pozisyon durumu.
- POST /api/futures/ladder/summary (5962) - ladder ozet (bacak listesi).
- POST /api/futures/grid/margin (5979) - grid marjin rezervi projeksiyonu.
- POST /api/futures/grid/lifecycle (5996) - grid yasam dongusu politikasi.
- GET /api/futures/grid/policy (6013) - grid politika okuma.
- GET /api/futures/grid/variants (6020) - grid varyant kapi durumu.
- POST /api/futures/position/pnl (6027) - lineer futures pozisyon PnL/funding projeksiyonu.
- POST /api/futures/trailing/arm (6042) - trailing ratchet arm.
- POST /api/futures/trailing/observe (6057) - trailing ratchet gozlem.
- POST /api/futures/funding (6072) - funding hesabi.

### Two-Leg (hedge)
- POST /api/two-leg/sessions (6087) - iki-bacakli oturum baslat.
- POST /api/two-leg/sessions/{session_id}/fills (6103) - dolum kabul et.
- POST /api/two-leg/sessions/{session_id}/recovery (6119) - kurtarma isaretle.
- POST /api/two-leg/sessions/{session_id}/timeout (6134) - zaman asimi isaretle.
- POST /api/two-leg/sessions/{session_id}/replay (6149) - oturumu replay et.

### Admin / Backup / Ops
- POST /api/admin/backup (6478) - yedek al.
- POST /api/admin/backup/verify (6506) - yedek dosyasini dogrula.
- GET /api/admin/backups (6529) - yedek listesi.
- GET /api/dashboard (6578) - genel gosterge paneli verisi.
- POST /api/recurring/schedule (6663) - tekrarlayan zamanlama projeksiyonu.
- GET /api/events (6686) - denetim olay listesi.

### Risk
- POST /api/risk/explain (6763) - risk aciklamasi uret.
- GET /api/risk/canary (6799) - canary durumu.
- POST /api/risk/kill-switch (6813) - kill-switch ac/kapa.
- GET /api/risk/liquidation-status/{symbol} (6841, response_model=None) - likidasyon durumu (liquidation_status_service).

### Venue / Public / Testnet (market veri erisimi)
- GET /api/venue-snapshots/binance-spot-testnet (3811, ?symbol=) - public testnet snapshot.
- GET /api/public/exchange-symbols (3864) - public sembol listesi.
- GET /api/public/last-price (3909, ?symbol=) - son fiyat.
- GET /api/testnet/account (3977) - Binance testnet hesap bakiyesi.
- GET /api/testnet/open-orders (4011) - testnet acik emirler.

### Diger
- GET /api/health (3794) - saglik kontrolu.
- GET /api/capabilities (3799) - ozellik yetenek bayraklari.
- GET /api/settlement (6884) - settlement profili.

### Application katmanindaki moduller - api.py'ye BAGLI OLMAYAN (import edilmeyen) moduller

src/dcabot/application/ altinda 149 dosya var; api.py'nin "from dcabot.application..." import bloğu (satir 23-216) yalnizca yaklasik 90 sembolu ice aktariyor. Asagidaki moduller kaynak dosyada mevcut ancak api.py icinde hicbir yerde import edilmiyor (yani hicbir HTTP endpoint'i bunlari cagirmiyor - frontend'den erisilemezler):

- src/dcabot/application/margin_mode_registry.py
- src/dcabot/application/margin_mode_cross_admission.py
- src/dcabot/application/margin_mode_preflight.py
- src/dcabot/application/correlation_risk.py
- src/dcabot/analytics/correlation_scores.py
- src/dcabot/application/whale_depth_polling.py
- src/dcabot/data_adapters/binance_public_depth.py
- src/dcabot/application/reinvest_pool.py
- src/dcabot/application/indicator_registry.py

Not: "margin_mode" string'i api.py icinde yalnizca satir 2495'te bir response alani olarak ("margin_mode": profile.margin_mode) geciyor - bu, BotProfile domain nesnesinin zaten var olan bir alanini response'a koyuyor; yukaridaki margin_mode_registry/cross_admission/preflight modullerini cagirmiyor.

Grep taramasinda take_profit_ladder, regime_detection, momentum_oscillators, signal_condition_ast adinda bir modul dosyasi hic bulunamadi (ne api.py'de ne src/ genelinde) - bu isimler mevcut kod tabaninda yok. En yakin karsiliklar: ladder_summary.py / ladder_binding.py / ladder_conservation.py (take-profit ladder ile ilgili; ladder_summary api.py'de importlu ve /api/futures/ladder/summary endpoint'i uzerinden bagli) ve signal_native_indicators.py (momentum/indikator kesisimi ile ilgili; /api/signals/indicators/cross uzerinden bagli).

isolated_liquidation.py adli ayri bir modul de var; api.py'nin import listesinde gorunmedi (yalnizca liquidation_status_service import ediliyor) - bu ayrica dogrulanmali.

futures_dca_* ailesinde (yaklasik 20 dosya: futures_dca_reservation, futures_dca_recovery_capability, futures_dca_recovery_snapshot, futures_dca_recovery_provenance_gate, futures_dca_exit_priority, futures_dca_exit_candidate, futures_dca_exit_identity, futures_dca_fee_aware_exit, futures_dca_core_mapping, futures_dca_core_replay_oracle, futures_dca_event_contract, futures_dca_migration_preflight vb.) yalnizca futures_dca_plan, futures_dca_fill_projection, futures_dca_breakeven_contract api.py'nin dogrudan import blogunda (satir 109-118) goruluyor - geri kalan futures_dca_* dosyalarinin api.py'den dogrudan mi yoksa futures_dca_plan.py gibi baska bir modul uzerinden dolayli mi cagrildigi bu taramada net degil; bu belge yalnizca api.py'nin dogrudan import satirlarini taramistir, dolayli cagri zincirini derinlemesine izlememistir.
