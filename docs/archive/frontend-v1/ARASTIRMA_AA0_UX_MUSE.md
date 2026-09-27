# AA.0 UX Araştırması — muse (bağımsız)

Metodoloji: `docs/ARASTIRMA_FAZ16_QWEN_VIZYON_HARITASI.md` §8.6.0 adımları
1–6 aynen izlendi. Birincil kaynak `docs/qwen_referans/iterasyonlar/14_1787388842.html`
(15 `sec-*` bölümü, satır + JS render fonksiyonu referanslı) + ek ekranlar
#17/#18/#21/#22. DCABOT tarafı: `frontend/src/*.tsx` güncel envanteri +
`src/dcabot/server/api.py` gerçek endpoint'leri. Bu rapor bağımsızdır —
`docs/ARASTIRMA_AA0_UX_CLAUDE.md` okunmadı, AA'nın kendisi başlatılmadı.

Notasyon: VAR (birebir) / KISMİ (var ama eksik-farklı) / YOK.
"Dürüst-boş" = veri/karşılık yoksa uydurmadan "veri yok/devre dışı" gösterimi
(Arda'nın bağlayıcı ilkesi). Sektör bilgileri aksi belirtilmedikçe genel ürün
bilgisidir (repo araştırmalarında doğrulanmış bulgular ayrıca işaretlidir).

## AA.1 (=`sec-status`): Durum & Veri Kaynağı

### [Nesne Envanteri] (14: satır 153–200 + JS 2851–2873, 3031)
1. Özet bandı (emerald çerçeveli panel): 📡 ikonu + H2 "Sistem Özeti — Faz 1 ✓ · Faz 4 ✓ · Faz 4.5 aktif" + 3 kart grid'i: "✅ FAZ 1 · VERİ PIPELINE" (açıklama metni), "🧪 FAZ 4 + 4.5 · BACKTEST" (bold vurgulu açıklama), "⏳ SIRADA" (açıklama). Tamamı statik HTML.
2. Yol-haritası kahraman paneli: conic-gradient halka (ortada "4.5" + "OPTİMİZASYON") + H2 "Yol Haritası · Optimizasyon Gerçek Veride" + açıklama paragrafı + animasyonlu ilerleme çubuğu (`#progBar`, 1000ms CSS geçişi; `animateProgress` 24ms tick ile %0→%62 sayar) + "GENEL İLERLEME" etiketi + `#progPct` yüzdesi + 2×2 mini istatistik paneli (`data-count` sayaç animasyonu `runCounter` ile 0'dan hedefe: 5 TARANAN PARAMETRE, 3 DOĞRULAMA KATMANI, 500 MONTE CARLO SİM, 0 API ANAHTARI GEREKEN).
3. `#phaseGrid` (JS `buildRoadmap` doldurur): 8 faz kartı (`roadmap` dizisi, satır 2852–2861). Her kart: ikon kutusu + "Faz N: başlık" + "M görev" sayacı + durum çipi (✓ UI'DA HAZIR yeşil / ⏳ BACKEND amber, `be` bayrağına göre çerçeve rengi de değişir) + madde listesi (✓/▸ kurşunları).

### [DCABOT Karşılığı]
- Özet bandı + faz kartları: **YOK**. `SystemStatusCard` API/dataset/canary durumunu gösterir — amaç farklı (çalışma-zamanı sağlığı, yol haritası değil).
- Kahraman paneli (halka + ilerleme + sayaçlar): **YOK**. Eşdeğer animasyon bileşeni yok (`runCounter`/`animateProgress` karşılığı yok).
- `phaseGrid` durum çipleri: **YOK**.

### [Backend-Gerçeklik]
qwen'in faz içerikleri DCABOT'a taşınamaz (Faz 1/4/4.5 qwen'in kendi geliştirme
aşamaları — DCABOT'ta P1/P2 + Faz 17 A-J var). Bu ekran "bilgi" ekranıdır,
finansal hesap gerektirmez; ancak %62 ve sayaç değerleri qwen'de sabit
gömülü — DCABOT'ta **gerçek** değerlerle beslenmeli: bağlantı modu
(local-only rozeti App.tsx footer'da VAR), dataset sayısı (`/api/public/exchange-symbols`
+ dataset kataloğu VAR), bot/deal/sweep sayıları (`/api/dashboard` VAR:
sessions/bots/deals sayıları + `by_status`), canary/kill-switch durumu
(`/api/risk/canary` VAR). Yani: düzen qwen'den, içerik DCABOT'un gerçek
durum uçlarından. Uydurma veri YOK.

### [Sektör-Karşılaştırma + İyileştirme]
3Commas/Pionex/Bitsgap'te "yol haritası/dev-faz" ekranı yok — bu qwen'e özgü
bir geliştirici-konsolu nesnesi. 3Commas karşılığı en yakın: hesap/ajax
durum + API bağlantı sağlığı göstergeleri. DCABOT daha iyisini yapabilir:
AA.1'i "sistem sağlığı + veri-hazırlık" operasyon ekranına dönüştürmek —
bağlantı modu, veri kataloğu hazırlığı, bot/deal sayaçları, canary durumu,
sweep önbellek durumu — tek bakışta "sistem çalışmaya hazır mı" cevabı.
qwen taban, tavan değil: statik faz listesinden fazlası, canlı operasyon
göstergesi olur.

### [Teknik Not + Öncelik]
- Mevcut `SystemStatusCard` genişletilir + yeni statik paneller; `forms.tsx`
  ailesi yeterli, yeni bağımlılık YOK.
- Sayaç/ilerleme animasyonu: `requestAnimationFrame` + `prefers-reduced-motion`
  saygısı (mevcut `qwenTokens`/tema disipliniyle uyumlu); jank riski düşük
  (4 sayaç + 1 bar).
- Öncelik: DÜŞÜK-ORTA. Bilgi ekranı; tüm verisi hazır endpoint'lerde mevcut,
  bağımsız yapılabilir. AA.2'den sonra.

## AA.2 (=`sec-overview`, en büyük dilim): Genel Bakış

### [Nesne Envanteri] (14: satır 204–269 + JS dağınık)
1. 4 istatistik kartı (2→4 sütun grid): "Toplam Yatırılan (demo)" `#cardInvested`
   + "açık deal'lar üzerinde" alt-yazısı; "Kullanılabilir Bakiye" `#cardBalance` +
   "demo bakiye"; "Demo PnL (canlı fiyatla)" `#cardUpnl` + "Binance WS fiyatları";
   "Bugünkü Kâr" `#cardToday` + "realize · komisyon dahil". Değerler `refreshMoney`/
   `refreshUpnl` (satır 2004–2018) ile `appData` + `engineTick` simülasyonundan
   gelir; kâr/zarar rengi işarete göre değişir (emerald/rose).
2. Canlı Piyasa Grafiği paneli: H2 + "TradingView Lightweight Charts" çipi +
   alt-açıklama ("Varsayılan: BTCUSDC · sembol seçiciden tüm borsayı arayabilirsiniz")
   + `#ivBar` aralık çipleri (JS, `IV_SEC`: 1m/5m/15m/1h) + sembol-seçici butonu
   (`#symPickerBtn`: sembol + fiyat + değişim% + aşağı-ok) + `#marketPanel` açılır
   paneli: arama kutusu (`#mktSearch`, "🔍 Sembol ara…"), sütun başlıkları
   (Çift/Fiyat/24s %/Hacim), kaydırılabilir liste (`#mktList`, `max-h-80`,
   `renderMarketList`), alt-bilgi (`#mktCount` + "Binance spot · hacme göre").
3. "İNDİKATÖRLER" etiketi + `#ovIndBar` çip grubu (`buildIndBar`, satır 1787):
   SMA 20 / EMA 50 / Bollinger 20·2 / Hacim / RSI 14 / MACD — aç/kapa çipleri,
   Lightweight Charts serilerini bindirir (SMA/EMA/BB çizgi, Hacim histogram,
   RSI/MACD alt-panel `makeSub`); overview varsayılanı `{ema, vol}` açık.
   Hesap `calcSMA/calcEMA/calcBB/calcRSI/calcMACD` ile **istemcide float** yapılır.
4. `#ovChart` grafik kabı (`h-72`, Lightweight Charts + `setOverlays` fiyat
   çizgileri + `notifyMarket` canlı bar güncelleme).
5. Kâr Grafiği paneli (2/3 genişlik): H2 "Kâr Grafiği (demo hesap)" + "Quick
   Stats · Günlük / Haftalık / Aylık" + dönem çipleri (`#periodBar`:
   Günlük/Haftalık/Aylık, `active`) + `canvas#profitChart` (`h-48`, `drawProfit`
   satır 2355: ızgara + bezier çizgi + gradient dolgu + son-nokta; renk işarete
   göre). **Veri `genSeries` ile `Math.random` üretilir (satır 2352–2353) —
   tamamen uydurma.**
6. Canlı Sistem Akışı paneli (1/3): H2 + "piyasa + motor olayları" + `#feedList`
   (mono, `max-h-56` kaydırma, `addFeed` ile renkli nokta + saatli satırlar) +
   2 mini-kutu: "Veri Modu" `#feedMode` (CANLI·Binance WS yeşil / bağlantı
   durumu amber, satır 1506) + "Sonraki Funding" `#fundCount` (--:--:-- geri
   sayım, satır 2942).
7. Açık İşlemler (özet) paneli: H2 + "Tümünü gör →" (`data-goto="deals"` bölüm
   geçişi) + `#miniDeals` grid (JS: ilk 5 deal, her biri buton: sembol + LONG/
   SHORT yönü + PnL% + "SO x/y · TP %z"; tıklama deal-detayına gider;
   boş-durum: "Tüm deal'lar kapandı 🎉").
8. Davranış/animasyon: `engineTick` (satır 2029) SAHTE motor — fiyatlar rastgele
   yürüyüş (`seedSim`/`startSim`), SO dolumları simüle; `showToast` bildirimleri;
   `data-goto` ile bölümler arası geçiş; `window.scrollTo smooth`.

### [DCABOT Karşılığı]
- 4 istatistik kartı: **KISMİ**. `DashboardPanel` "Portföy özeti" tablosu var
  ama düzen/coğrafya farklı; değer kümeleri de farklı (bkz. Backend-Gerçeklik).
- Grafik + aralık çipleri + sembol seçici: **KISMİ**. `TradingChart`/`CandleChart`/
  `HeroChartPanel` + `SymbolSelector` mevcut; ama qwen yerleşimi (iv çipleri +
  picker-buton + açılır market paneli tek panelde) YOK.
- Market açılır paneli (arama + 4 sütun + sayaç): **YOK**.
- İndikatör çip çubuğu: **YOK** (Arka-uçta G.4 MACD/StochRSI/Bollinger +
  `signal_native_indicators` VAR ama grafiğe bindirme YOK; sihirbazdaki SMA/EMA
  kesişim önizlemesi farklı amaçlı).
- Kâr grafiği + dönem çipleri: **YOK**.
- Sistem akışı feed'i: **KISMİ** (`EventPanel` + `/api/events` VAR; qwen
  yerleşimi + Veri-Modu/Funding kutuları YOK).
- Funding geri-sayımı: **YOK**.
- miniDeals + "Tümünü gör": **KISMİ** (`BotTable`/`DealPanel` VAR; 5'li mini
  kart + boş-durum YOK). `data-goto` bölüm-geçişi: **VAR** (section nav).
- Toast: **VAR** (`ToastStack`).

### [Backend-Gerçeklik]
- Kart değerleri: `GET /api/dashboard` YALNIZ sayaç verir (sessions, total_cash,
  positions, open_orders, bots, deals/by_status, backups) — yatırılan/uPnL/
  bugünkü-kâr DEĞERLERİ YOK. Paper tarafında oturum-bazlı snapshot (`/api/paper/
  sessions/{id}/market-refresh` POST) mevcut ama toplu portföy-değerlemesi uç
  noktası yok; UI finansal hesap yapamayacağından **yeni sunucu-toplam uç
  noktası gerekir (Claude işi)** — yoksa kartlar dürüst-boş kalır. `total_cash`
  tek hazır değerdir.
- Sembol listesi: `GET /api/public/exchange-symbols` VAR (P2.01); tekil fiyat:
  `GET /api/public/last-price` VAR; anlık-snapshot: `/api/venue-snapshots/
  binance-spot-testnet` VAR. 24s-değişim% + hacim sütunları için uç YOK →
  ya yeni uç (Claude) ya o iki sütun dürüst-boş/kaldırılır.
- Aralıklar: veri kataloğu bar aralıkları VAR (dataset `interval`); canlı
  1m/5m/15m/1h WS akışı testnet-kapsamında — aralık çipleri yalnız gerçekten
  beslenen aralıkları gösterir, gerisi devre-dışı.
- İndikatörler: backend HESAP VAR (`signal_native_indicators`, G.4), ama
  grafiğe seri veren uç YALNIZ `/api/signals/indicators/cross` (kesişim
  olayları). SMA/EMA/BB/RSI/MACD/hacim SERİ uçları YOK → yeni uçlar gerekir
  (Claude); qwen'in istemci-float hesabı ASLA kopyalanmaz (exactness ilkesi).
- Kâr grafiği: qwen verisi rastgele-uydurma. DCABOT'ta deal geçmişi
  (`/api/deals/{id}/timeline` VAR) + realized PnL — dönemlik toplam uç YOK →
  yeni uç (Claude) ya da dürüst-boş ("henüz kapanmış deal yok").
- Feed: `/api/events` VAR (doğrudan bağlanır). Veri-Modu: bağlantı durumu
  istemcide biliniyor (mevcut `apiStatus` disiplini) — sunucu saati/veri
  gerektirmez. Funding geri-sayımı: next-funding-time veren uç YOK
  (P1.13.f.d funding projeksiyonu içsel; venue funding saati testnet
  `positionRisk`/funding-endpoint ister) → dürüst-boş ("bağlı hesap yok").
- miniDeals: deal LİSTE uç YOK (`POST /api/deals` + `/bulk` + timeline VAR,
  GET liste YOK) → liste uç gerekir (Claude) ya da `by_status` sayaçlarıyla
  sınırlı özet. Boş-durum metni taşınır.

### [Sektör-Karşılaştırma + İyileştirme]
- 3Commas dashboard: portföy bakiyesi + toplam kâr + bot/deal sayaçları +
  kâr-grafiği (günlük/haftalık) — qwen'in 4 kart + kâr-grafiği bileşimi buna
  yakınsar; DCABOT 3Commas'tan iyi yapabilir: kartların ALTINA "hangi uçtan,
  hangi saatte" veri-kaynağı notu (dürüstlük rozeti — rakiplerde yok).
- Pionex: bot-kart ağırlıklı ana sayfa + tek-tuş bot açma; Bitsgap: portföy
  toplu-görünüm + demo/live geçişi. DCABOT iyileştirmesi: demo/live
  (paper/testnet) ayrımını qwen'in "(demo)" soneklerinden daha yapısal yap —
  tüm portföy bloğuna tek "PAPER" rozeti + testnet bağlanınca ayrı blok
  (mevcut `BinanceAccountPanel` ile tutarlı).
- Sembol-seçici: 3Commas'ta pair-picker bot-kurulumunda; borsalarda (Binance)
  market-paneli standart. qwen'in açılır market panelini AYNIEN al — ama
  24s%/hacim sütunları uç gelmeden eklenmez.
- İndikatör çubuğu: rakiplerde grafik-üzeri TradingView widget'ı (harici
  bağımlılık). DCABOT farkı: KENDİ backend'inden exact indikatör bindirme —
  offline-first ile tutarlı, rakiplerde yok.

### [Teknik Not + Öncelik]
- KRİTİK: qwen Lightweight Charts'ı CDN'den yükler (harici bağımlılık).
  DCABOT offline-first olduğundan CDN YASAK — mevcut `TradingChart`/
  `CandleChart` çizim yığını korunur, qwen YERLEŞİMİ taşınır, kütüphane
  taşınmaz. Kâr-grafiği canvas'ı (`drawProfit` deseni) bağımsız yeniden
  yazılır (veri gerçeğe bağlanır).
- `SymbolSelector` mevcut konumdAN overview paneline taşınır (8.6.0 AA.2
  maddesi zaten bunu söyler); market arama `exchange-symbols` + istemci
  filtreleme (sunucu araması gerekmez, liste küçüktür).
- `engineTick` simülasyonu ASLA taşınmaz; canlı değerler yalnız gerçek
  uç/WS'den (testnet/public). `showToast`→`ToastStack` VAR.
- Performans: 5 dakikalık WS tick + feed listesi — mevcut `max-h-*` +
  sınırlı-satır disiplini korunur; grafik `devicePixelRatio` (`prepCanvas`
  deseni) mevcut çizimlerde de uygulanır.
- Öncelik: EN YÜKSEK (AA.2 en büyük dilim). Sıra: (1) yerleşim + sayaçlar
  (hazır uçlar), (2) Claude'a yeni uçlar (portföy-toplam, indikatör-serileri,
  kâr-serisi, deal-listesi, ticker-24s), (3) uçlar gelince gerçek-veri
  bağlama; gelmeyen her hücre dürüst-boş.

## AA.3 (=`sec-bots` + `sec-botdetail`): Bot Kartları + Bot Detayı

### [Nesne Envanteri] (14: satır 272–318 + JS 2056–2156, 2317–2343, 2455)
A) Liste: başlık + "karta tıklayın → tam sayfa detay" ipucu + 3 şablon çipi
(🛡️ Muhafazakar / ⚖️ Dengeli / 🔥 Agresif, `tpl-btn` → `applyTemplate` DCA
formunu doldurur + toast + feed) + `#botGrid` kartları (`renderBots`): her
kartta bot adı + "YÖN · DURUM · N aktif deal" satırı + aç/kapa `switch` +
2 mini-kutu (Toplam Kâr, 24s Performans, işaret-renkli) + tip çipi
(DCA/GRID/HYBRID) + "📊 Detay için tıklayın" + 2 buton (⚙️ Düzenle → DCA
sekmesi, Panic Sell → toast+feed). Kart-tıklama (buton dışı) detay açar.
Kill-switch (`appData.kill`) tüm kartları GÜVENLİ MOD'a alır, switch'leri
kilitler. Başlık rozeti `#botCount` = çalışan sayısı.
B) Detay: ← Botlarım geri-butonu + `#bdTitle` + tip çipi + durum çipi
(RUNNING/STOPPED/GÜVENLİ MOD, renk kodlu `syncBotDetailHeader`) + canlı uPnL
(`updateBotPageLive`, deal'lerin toplamı) + bot switch'i + hızlı-geçiş paneli
(`#botChipBar`: durum-noktalı bot çipleri) + 6 istatistik kutusu (`#bdStats`:
Toplam Kâr, 24s Performans, Win Rate, Toplam Deal, Max Drawdown, Çalışma
Süresi) + sparkline `canvas#bdSpark` (`drawBdSpark` — `genSeries` RASTGELE
üretir) + canlı grafik (`#botChartPage` + `#botIndBar` + `botOverlays`:
BOT GİRİŞ çizgisi + GRID ±6 seviye + DİNAMİK TABAN + SO# çizgileri
(kesikli, tek+kapanış etiketli) + ORT. MALİYET + TP + SL + LİKİDASYON —
`liq=avg*(1-0.95/lev)` SAHTE formül, yalnız %25 yakınsa çizilir) + "Aktif
Ayarlar" grid'i (`#bdSettings`: Tip/Sembol/Yön/Kaldıraç/Marjin Modu/Giriş
Fiyatı [+ DCA: BO/SO/SO-sayısı/Deviation/Volume-Step-Scale/TP/SL | GRID:
Grid Adımı] + Durum/WinRate/ToplamDeal) + "Bu Botun Aktif Deal'ları"
(`#bdDeals`: sembole göre filtre, buton-satırlar → deal detayı; boş-durum
"Bu bot için aktif deal yok.").

### [DCABOT Karşılığı]
- Liste başlığı + kart grid'i: **KISMİ** (`BotTable` TABLO düzende var;
  kart düzeni + kâr/24s kutuları + tip çipi YOK).
- Şablon çipleri: **KISMİ** (B.4-ui preset galerisi + sihirbaz preset-bağı
  VAR; liste-başlığı çipleri YOK).
- Kart switch'i (aç/kapa): **YOK** (bot açma/kapama backend'i yok — kayıt
  defteri pasif; bkz. Backend-Gerçeklik).
- Düzenle → form: **KISMİ** (sihirbaz VAR ama create-only; değerle-düzenleme
  modu YOK). Panic Sell: **YOK** (emir yetkisi yok).
- Kill-switch kart-entegrasyonu: **KISMİ** (kill-switch backend + RiskPanel
  VAR; kart kilidi YOK).
- Detay başlık + çipler + uPnL + switch: **KISMİ** (`BotDetailView` VAR:
  geri + başlık + çipler + sayaçlar; uPnL YOK, switch YOK).
- Hızlı-geçiş çipbarı: **VAR** (birebir, aynı etiket metniyle).
- 6 istatistik kutusu: **KISMİ** (6'lı `dl` VAR ama farklı gerçek-olgu
  kümesi: pair/session/bütçe/liste/tip; kâr/24s/winrate/deal/DD/süre YOK).
- Sparkline: **YOK**. Grafik + indikatör-bar + overlay: **KISMİ** (A.3
  `renderChart` + kısmi overlay VAR: safety/deviation; SO/TP/SL/LIQ
  çizgileri YOK).
- Aktif Ayarlar: **KISMİ** (gerçek profil + taslak-etiketli DCA değerleri
  VAR; lev/marjin/giriş + G/H/I alanları YOK — kayıt identity-only).
- Botun deal'ları: **YOK** (bilinçli eksik, dosyada belgeli).

### [Backend-Gerçeklik]
- `GET /api/bots` + `GET /api/bots/{id}` (+ lists/sessions/check POST'ları)
  VAR — liste + profil + sayaçlar gerçek beslenir. `by_status` deal sayacı
  VAR ama BOT-BAZINDA deal sayacı YOK → kart "N aktif deal" için ya yeni uç
  (Claude) ya kartta sayaç dürüst-boş.
- Kâr/24s/winrate/DD/süre/sparkline: backend YOK (deal-kâr geçmişi uçları
  yok; `timeline` olay-bazlı, PnL-bazlı değil) → yeni uçlar (Claude) ya da
  dürüst-boş ("kâr geçmişi uçları yok"). qwen sparkline'ı rastgele-uydurma;
  asla örnek alınmaz.
- Switch (aç/kapa) + Panic: backend YOK ve BU BİR ÜRÜN KARARI — bot
  çalıştırma/durdurma + emir yetkisi testnet-gate ister (AGENTS.md kural 2).
  UI'da buton konulursa ARKA-UÇSUZ kalır → ya kapalı tutulur ya yazılı-onaylı
  testnet dilimine bağlanır. Kill-switch (`/api/risk/kill-switch`) VAR —
  kart kilidi buna bağlanabilir (mevcut yetki içinde).
- Overlay çizgileri: SO/TP/SL seviyeleri `build_plan` matematiğinden
  (C-fazı, exact) + `ladder` — GERÇEK backend karşılığı VAR, uçlaştırılabilir
  (Claude). **LİKİDASYON ÇİZGİSİ ASLA ÇİZİLMEZ**: qwen'in `0.95/lev` formülü
  uydurma; LCR-12 gereği likidasyon yalnız venue'den gelir (`/api/risk/
  liquidation-status` VAR — o değer varsa gösterilir, yoksa hücre boş).
- Ayarlar: Config G/H/I alanları VAR ama bot-kayıt identity-only → "Aktif
  Ayarlar" sunucu-gerçeği gösteremez; mevcut taslak-etiketli gösterim korunur,
  strateji-bağlama orkestrasyon işi (ayrı karar).

### [Sektör-Karşılaştırma + İyileştirme]
- 3Commas "My bots": kart başına kâr/24s/aktif-deal + aç/kapa + düzenleme —
  qwen bunu kopyalar; DCABOT aynı kartı daha-dürüst yapar: her karta veri
  kaynağı rozeti (CANLI-TESTNET / PAPER-TASLAK) + hesaplanamayan hücrede
  "uç yok" notu (rakipler sessizce boş/0 gösterir).
- Pionex: bot-pazar + tek-tık kopyalama; Bitsgap: bot-performans tablosu.
  DCABOT iyileştirmesi: şablon çiplerini B.4-ui galerisine bağla (liste
  başlığındaki 3 çip → galerideki gerçek preset'e derin-bağlantı) — qwen'in
  sabit 3 şablonundan zengin, gerçek-verili.
- Detaydaki 6-kutu + sparkline: 3Commas bot-detayı da benzer; DCABOT farkı:
  overlay'de LİKİDASYON YOK (dürüstlük) + SO/TP/SL exact-backend çizgileri
  (rakiplerde yuvarlak-değer çizgileri).

### [Teknik Not + Öncelik]
- `BotTable` → kart görünümü: YENİ `BotCards` (tablo korunur, görünüm
  seçici eklenir — erişilebilirlik: kartlar `<article>` + başlık hiyerarşisi).
- Switch/Panic: backend-gate'li — YER TUTUCU OLARAK BİLE KONULMAZ (ölü
  buton yasağı); kill-switch kart-kilidi bağımsız yapılabilir.
- Overlay genişletmesi Claude'a bağımlı (plan-seviye uçları); sparkline en
  sona (kâr-serisi ucuna bağımlı).
- Öncelik: YÜKSEK (AA.3 ikinci büyük dilim). Sıra: kartlar (hazır veri) →
  detay istatistikleri (uç-gerekli) → overlay (Claude) → switch/panic
  (ürün+gate kararı).

## AA.4 (=`sec-deals` + `sec-dealdetail`): İşlemler + İşlem Detayı

### [Nesne Envanteri] (14: satır 321–381 + JS 2175–2230, 2231–2316, 2677–2688)
A) Liste: "Active Deals" başlığı + "satıra tıklayın" ipucu + "⚡ Smart Trade
Terminal" aç/kapa butonu + `#stPanel` (Smart Trade formu: Sembol select'i
5 sabit USDC çifti, Yön LONG/SHORT, Boyut USDT `100`, TP % `1.5`, "Pozisyon
Aç" — `stSubmit`: kill-kontrolü + sahte deal push + invested/balance
oynama + deal-detayına atlama) + tablo (`min-w-[900px]`, yatay-kaydırmalı):
9 sütun (Sembol 📈 / Yön rozeti LONG▲-SHORT▼ / Lev / Ort. Giriş / Güncel /
PnL % / SO Doluluk [nokta-matrisi `sobit` + "x/y"] / TP Mesafe [<%0.3 amber,
negatifte "TP!"] / Aksiyon [📈 Detay | + Fon | Panic]). `renderDeals`:
satır-tıklama detay açar (buton-hariç); + Fon: kill-kontrolü + giriş
ortalamasını `entry*0.88+price*0.12` UYDURMA formülle kaydırır + SO+1;
Panic → `closeDeal(d,'PANIC')`. `#dealBadge` sayaç + miniDeals yeniden-render.
B) Detay: ← Aktif İşlemler + `#ddTitle` + yön-lev çipi + `#ddPnl` (% + USD,
işaret-renkli `updateDealPageLive`) + "CANLI FİYAT" rozeti + hızlı-geçiş
çipbarı (`#dealChipBar`: sembol + yön-oku + CANLI PnL, her tick güncellenir)
+ 8 bilgi kutusu (`#ddInfo`: Ort. Giriş / Güncel Fiyat / PnL / Boyut /
Kaldıraç / SO Doluluk / TP Mesafe / Liq Mesafe) + grafik (`#dealChartPage` +
`#dealIndBar` + `dealOverlays`: ORT.GİRİŞ + TP + SL + kalan-SO çizgileri
(max 5, tek+son etiketli) + LİKİDASYON [sahte formül, %22 yakınsa]) +
"Seviyeler" 6-kutu (`#ddLevels`: giriş/TP/SL/Liq renk-kodlu + Kalan SO +
İlk Deviation) + "Aksiyonlar & Bağlı Bot" (➕ Fon Ekle + 🚨 Panic Sell +
`#ddBotLink`: sembole-göre bot eşleşmesi + "🤖 Bot Detayını Aç" ya da
"Bağlı bot bulunamadı (Smart Trade pozisyonu).").

### [DCABOT Karşılığı]
- Tablo + 9 sütun: **YOK** (`DealPanel` ID-bazlı lifecycle konsolu; ticaret
  tablosu değil). Sütun-içi nesneler (yön-rozeti, sobit-matrisi, TP-mesafe,
  satır-aksiyonları): **YOK**.
- Smart Trade terminali: **YOK**.
- Satır-tıklama → detay: **YOK** (liste yok).
- Detay başlık + çipler + PnL + rozet: **KISMİ** (`DealDetailView`: geri +
  başlık + durum + replay-rozeti + olay-sayacı VAR; fiyat/PnL/rozetyok).
- Hızlı-geçiş çipbarı: **YOK** (bilinçli eksik, belgeli).
- 8 bilgi kutusu: **YOK** (4'lü lifecycle-facts VAR: deal/revision/durum/sıra).
- Grafik + dealIndBar + overlay: **YOK** (bilinçli eksik: deal olaylarında
  fiyat/zaman yok).
- Seviyeler: **YOK**. Fon Ekle/Panic: **YOK** (bilinçli: emir yetkisi).
- Bağlı-bot: **YOK** (bilinçli: deal↔bot bağı yok).

### [Backend-Gerçeklik]
- Deal LİSTE ucu YOK (`POST /api/deals`, `/bulk`, `/events`, `/replay` +
  `GET /timeline` VAR) → tablo + çipbar + miniDeals için liste ucu ŞART
  (Claude). Bu, AA'nın en kritik backend-bağımlılığıdır.
- Satır hücreleri: entry/güncel-fiyat/PnL/TP-mesafe — fiyat + PnL hesabı
  sunucuda olmalı (UI hesap YASAK); `timeline` olaylarında fiyat/zaman YOK
  (belgeli) → deal-fiyat modeli ya genişler (Claude + veri-modeli kararı)
  ya tablo "olay-durumu" tablosuna indirgenir (dürüst-alternatif).
- SO x/y: engine `State` safety dolumu VAR (matematik hazır) → uçlaştırılabilir.
- TP Mesafe + "TP!": engine TP mantığı VAR (tetikleme koşulları);
  mesafe hesabı sunucu-ucu olabilir.
- Liq Mesafe + LİKİDASYON: **ASLA** (sahte formül; LCR-12; venue değeri
  varsa o, yoksa boş).
- Fon Ekle/Panic/Smart-Trade-Aç: emir yetkisi → testnet-gate + ürün kararı;
  paper-trading (`/api/paper/sessions/.../orders|fills`) VAR — Smart Trade
  PAPER modda gerçeklenebilir (canlı emir DEĞİL; "PAPER" rozeti zorunlu).
- Bağlı-bot: deal↔bot bağı modelde YOK → ya model genişler (Claude) ya hücre
  dürüst-boş ("bağlantı modeli yok").

### [Sektör-Karşılaştırma + İyileştirme]
- 3Commas "Active deals": tablo (pair/kâr/SO/TP) + deal-detay (grafik +
  SO-tablosu + manuel-SO + panic) — qwen birebir bu. DCABOT iyileştirmesi:
  (1) sobit-matrisi + TP-mesafe aynen alınır (görsel dil), (2) 3Commas'ta
  olmayan "veri-kaynağı" sütunu/rozete eklenir (LIVE-TESTNET/PAPER/TASLAK),
  (3) Panic Sell 3Commas'ta tek-tık; DCABOT'ta onay-diyaloğu (`ConfirmDialog`
  VAR) + kill-switch engeli standart olur (güvenlik farkı).
- Pionex: pozisyon-kartları + tek-tık kapatma; Bitsgap: açık-emir tablosu.
  DCABOT'un deal-tablosu paper/canary bağlamıyla (hangi bakiye, hangi kill
  durumu) rakiplerden şeffaf olur.
- Smart Trade: 3Commas'ın amiral-terminali (çok-koşullu). DCABOT'ta paper-
  kapsamlı mini-terminal makul; "bot-dışı manuel pozisyon" kavramı mevcut
  paper-session modeline uyar (oturum = manuel terminal).

### [Teknik Not + Öncelik]
- Deal-listesi ucu OLMADAN tablo yapılamaz — Claude'a ilk-sıra bağımlılık.
  Tablo `min-w-[900px]` + yatay-kaydırma deseni + `table-wrap` mevcut
  disipliniyle uyumlu; 50+ satırda sanallaştırma (ileride).
- Satır-içi aksiyonlar gate'li (ölü-buton yok): liste önce salt-okunur
  taşınır (Detay + bilgi), Fon/Panic gate-sonrası.
- Öncelik: EN YÜKSEK (liste-ucu ile birlikte). Sıra: liste-ucu (Claude) →
  salt-okunur tablo + detay-iskelet → hücre-gerçekleri (fiyat/PnL uçları) →
  aksiyonlar (gate).

## AA.5 (=`sec-dca`): Bot Kur — DCA Yapılandırması

### [Nesne Envanteri] (14: satır 384–417 + JS 2382–2463)
1. Başlık ("Bot Kur — DCA Yapılandırması" + "Bölüm 2.1 · 3Commas DCA
   parametrelerinin tamamı") + 3 şablon çipi (aynı `tpl-btn`, `templates`
   9'ar değer: bo/so/soCount/dev/volScale/stepScale/tp/sl/lev) + "💾 Botu
   Kaydet" (`saveFormBtn` → toast+feed, gerçek kayıt YOK).
2. Önizleme paneli (cyan çerçeve): H3 + "formu değiştirdikçe SO,TP,SL,
   likidasyon anında güncellenir" + sembol select'i (`#dcaPair`, tek seçenek
   BTCUSDC) + "📍 Girişi Güncel Fiyata Sabitle" (`pinEntry` → `dcaEntry`,
   toast) + 5 bilgi-kutusu (`lgAvg/lgTp/lgSl/lgLiq/lgMargin`: ORT.MALİYET,
   TP, SL, LİKİDASYON, TOPLAM MARJİN) + `dcaIndBar` + `#dcaChart` (`h-80`,
   `updateDcaPreview` her input'ta overlay+değerleri float-hesapla günceller;
   SO satırları "$size" etiketli; "optimizasyon sonuçları buraya iner" notu).
3. `#dcaForm` (`buildForm` + `dcaSpec`, satır 2408–2417): 8 grup, ~28 alan:
   Sipariş Boyutları (BO, SO, Order-Type select); Güvenlik Emirleri (SO
   sayısı, Max Active SO); Ölçekleme (deviation, volume-scale, step-scale,
   SO-deviation-reference select); Giriş Sinyalleri (start-type select,
   conditional-price, cooldown, min/max 24h filtreleri + "Deal Start
   Conditions" çoklu-çip: TradingView Webhook/RSI/MACD/Bollinger/Stoch
   RSI/EMA Cross/Signal API/Çoklu Zaman Dilimi, 2'si seçili); Take Profit
   (TP, trailing-toggle, TP-order-type, Partial TP, Reinvest %); Stop Loss
   (SL, trailing-toggle, breakeven-toggle, SL-timeout sn, Max-Deal-Duration
   gün); Yön & Marjin (margin-mode, leverage range 1–125 + canlı etiket,
   direction Long/Short/Bidirectional); Bot Yönetimi (max-deals bot/global,
   profit-currency USDT/USDC/BTC). Alan tipleri: number/select/toggle/range
   (`fieldHtml`).

### [DCABOT Karşılığı]
- 5-adımlı sihirbaz (`BotWizard`: Kimlik/Giriş/Çıkış/Bütçe/Önizleme) +
  `FuturesDcaForm` + preset-bağı + AI-önerici: **KISMİ** (işlevsel olarak
  qwen formunun ÇOĞUNU kapsar — BO/SO/sayı/deviation/scale'ler/TP/SL/
  trailing/margin/order-type'lar/slippage/ladder/reinvest/SL-bar/süre/
  aksiyon/kâr-birimi/deal-limitleri — ama TEK-SAYFA qwen yerleşimi YOK;
  sihirbaz adım-adım).
- qwen-özel alanlar: leverage-slider (DCABOT Config `leverage` VAR ama
  sihirbazda YOK), start-type/conditional/cooldown/24h-filtreleri (YOK —
  backend karşılığı kısmi: webhook/scheduled/RSI-sinyal modülleri VAR),
  Deal-Start-Conditions çipleri (YOK — G.4 AST backend VAR ama UI YOK),
  trailing-TP (YOK — backend? trailing-stop-loss VAR, trailing-TP YOK),
  breakeven (YOK), Partial-TP-% (H.1 ladder VAR — qwen'in tek-%'sinden
  zengin), TP-order-type (G.2 exit_order_type VAR), SL-timeout-sn (H.2
  bar-sayacı VAR — birim farklı: bar vs saniye, bilinçli mimari kararı),
  profit-currency (I.1 QUOTE/BASE kip VAR — qwen'in 3-sembol listesinden
  farklı model), max-deals (I.2 3-limit VAR — qwen 2-limit).
- Önizleme paneli + 5 kutu + canlı overlay: **KISMİ** (sihirbaz Önizleme
  adımı + `CalculatedPreview` + A.3 grafik-overlay VAR; SO/TP/SL/LIQ
  kutuları YOK — backend: `preview` uç VAR (planned_gross/estimated_margin);
  avg/TP/SL sayısal önizleme YOK (A.3'te belgeli Claude işi); LİQ YOK).
- Sembol select + giriş-sabitleme: **KISMİ** (sihirbaz pair-CSV + `pinEntry`
  benzeri YOK; grafik-sembol `HeroChartPanel` VAR).
- Şablon çipleri + Botu Kaydet: **KISMİ** (preset-bağı VAR; kaydet=yerel
  kayıt VAR — identity-only, strateji sunucuya gitmez).
- "Optimizasyon sonuçları buraya iner": **YOK** (sweep-optimize → sihirbaz
  geri-besleme bağı YOK).

### [Backend-Gerçeklik]
- Form DEĞERLERİ istemci-taslağı (mevcut disiplin korunur); SAYISAL önizleme
  (avg/TP/SL/margin) sunucu-ucu ister (Claude — plan matematiği hazır).
- Start-conditions çipleri → G.4 AST: backend VAR, UI-bağlama + olası
  "koşul → sinyal" değerlendirme ucu gerekir.
- Trailing-TP + breakeven + 24h-filtreleri + cooldown: backend YOK →
  alanlar ya konulmaz ya "motor YOK" rozetiyle pasif (dürüst-boş).
- Kaydet: `/api/bots` identity-only VAR; strateji-payload'lu kayıt YOK →
  qwen "Botu Kaydet"in karşılığı bugünkü yerel-kayıt; strateji-bağlama
  orkestrasyon kararı.
- Optimize→form akışı: sweep-optimize SONUÇ ucu VAR (`/api/sweeps/optimize`
  POST); "kazanan tarifi forma doldur" istemci-eşlemesi yapılabilir
  (hesap yok, yalnız doldurma).

### [Sektör-Karşılaştırma + İyileştirme]
- 3Commas DCA-bot kurulumu: TEK-SAYFA uzun form (qwen bunu kopyalar).
  DCABOT iyileştirmesi: sihirbaz ADIMLARI korunur (yeni-başlayan dostu,
  rakiplerde yok) + "uzman görünümü" olarak qwen tek-sayfa formu İKİNCİ
  görünüm eklenir (aynı taslak-state, iki yerleşim — Pionex'in
  basit/pro-ayrımına benzer ama tek-veri).
- Pionex kaldıraç-slider'ı + Bitsgap risk-önizlemesi: qwen'in lev-slider +
  5-kutu bileşimi yeterli; DCABOT farkı: 5-kutuya "sunucu-hesabı, HH:MM:SS"
  damgası (hesap-şeffaflığı).
- Deal-Start-Conditions: 3Commas'ta TradingView/sinyal-çoklu-seçim var;
  DCABOT G.4 `Any_` ile "HERHANGİ-BİRİ" mantığını AÇIK gösterir (3Commas
  gizler) — dürüstlük farkı.

### [Teknik Not + Öncelik]
- Sihirbaz state'i FORMA TAŞINIR (tek `WizardDraft`, iki yerleşim) — state
  ikileme YOK; `forms.tsx` ailesi + `LabeledSlider` (lev için VAR) yeterli.
- Canlı-önizleme: her tuşta sunucu-çağrısı YOK — debounce (B.5 `useWhatIfAutoRun`
  deseni, 800ms) + "hesaplanıyor" durumu + hata-dürüstlüğü.
- Ölü-alan YOK: motorsuz alan konulmaz (trailing-TP/breakeven/filtreler).
- Öncelik: YÜKSEK. Sıra: tek-sayfa görünüm (mevcut taslak) → sayısal-önizleme
  ucu (Claude) → start-conditions (G.4 UI) → optimize-girdisi.

## AA.6 (=`sec-datastore`): Veri Deposu (LAB)

### [Nesne Envanteri] (14: satır 420–513 + JS 963–1030, 1842–1930)
1. Başlık ("Faz 1 · Veri Pipeline — LAB" + "5 USDC paritesi · anahtarsız ·
   artımlı Parquet deposu") + "API ANAHTARI GEREKMEZ" rozeti.
2. Panel 1 Parite Panosu: "🔄 Yeniden Test Et" (`probeBtn` → `probeAll`) +
   `#pairBoard` (`renderPairBoard`): parite başına kart (sembol + FUTURES✓/
   SPOT✓/BULUNAMADI çipi + spot✓/✗ + futures✓/✗ çipleri + fiyat + değişim% +
   "depoda: N snapshot" + listeli-değilse XMR-açıklaması).
3. Panel 2 Doğrulama Lab: `#labChips` (parite-seçici) + "🔬 Çek & Doğrula"
   (`runLab`: CANLI Binance klines `fetch` 300×1m → `validateKlines` 6 kural:
   satır-sayısı/monoton-zaman/tekrarsızlık/OHLC-tutarlılık/NaN/boşluk-oranı →
   `renderValidChips`: kapı-çipi + kural çipleri) + `#labResult` grid +
   `#pipChart` (h-64) mum-grafiği.
4. Panel 3 Toplu İndirme Planı: `dsSearch`+`dsPickList` (otomatik-tamamlama,
   80-sonuç) + 5 hızlı-ekle çipi + `dsSelChips` (seçili çiftler, piyasa-etiketli
   futures/spot/borsada-yok + ✕-kaldırma) + `dsIvBar` (1m/5m/1h çoklu)
   + özet-kutusu (`dsRange/dsFiles/dsSize`: kapsam/files/MB) + 4 buton
   (📋 Manifesto / 🐍 Python Script / 🐚 Bash Script — panoya-kopyalama
   `makeManifest/makePythonScript/makeBashScript` — + "⬇ İndirdim → Depoya
   Kaydet" `dsRegister`) + klasör-yapısı `prebox` + doğrulama-kuralları
   listesi (SHA256/satır/tekilleştirme/OHLC/404, statik).
5. Panel 4 Kayıtlı Depo: `#dsTotal` ("N snapshot kayıtlı") + `#dsRegistry`
   (`renderRegistry`): snapshot-satırlar (sembol + aralık + piyasa + dönem +
   tazelik + aksiyonlar) + boş-durum ("Henüz kayıtlı snapshot yok…").

### [DCABOT Karşılığı]
- Başlık + rozet: **KISMİ** (`DatasetCatalogPanel` "Geçmiş veri kataloğu"
  VAR; "anahtarsız" rozeti YOK — offline-first rozetleri başka yerde).
- Parite Panosu: **KISMİ** (`BinancePublicSnapshotPanel` sembol/filtre anlık-
  görüntüsü VAR; 5'li keşif-panosu + fiyat/değişim YOK).
- Doğrulama Lab: **KISMİ** (katalog `preflight` + doğrulama-görünümleri VAR;
  canlı-çek + 6-kural çip-dizimi YOK).
- İndirme Planı + script-üretimi + klasör/prebox + kural-listesi: **YOK**.
- Kayıtlı Depo: **KISMİ** (katalog tablosu VAR: dataset/enstrüman/aralık/
  dönem/durum; snapshot-satır zenginliği YOK).

### [Backend-Gerçeklik]
- GÜÇLÜ: `/api/datasets` (liste) + `/{id}/preflight` (doğrulama!) +
  `/{id}/chart-data` + `/{id}/run-plan` + `/historical-runs/*` (validate/
  save/list/detail/export/reproduce) VAR. qwen'in localStorage-deposu yerine
  GERÇEK sunucu-kataloğu var — DCABOT önde.
- Parite-keşif: `/api/public/exchange-symbols` VAR (liste); fiyat/değişim
  sütunları için ticker-ucu YOK (AA.2 ile aynı bağımlılık).
- Lab "canlı-çek": public-klines çekme + doğrulama — backend'de klines-
  normalleştirme (P1.17.e) VAR; "çek & doğrula" TEK-UÇ YOK → ya yeni uç
  (Claude) ya lab "katalog-preflight gösterimi"ne indirgenir (mevcut
  `preflight` + `validate` uçlarıyla TAMAMEN yapılabilir — önerilen).
- Script-üretimi (manifest/py/sh): istemci-metin-üretimi — hesap DEĞİL,
  metin-şablon; yapılabilir ama DCABOT deposu Parquet-değil (artifact+hash
  modeli) → ŞABLONLAR DCABOT FORMATINA YENİDEN YAZILIR (qwen yolu kopyalanmaz).
- Kayıt ("Depoya Kaydet"): DCABOT'ta dataset-kaydı sunucu-tarafı (import
  akışı) → istemci-butonu o uca bağlanır ya da dürüst-boş.

### [Sektör-Karşılaştırma + İyileştirme]
- Rakiplerde (3Commas/Pionex/Bitsgap) veri-deposu/lab KAVRAMI YOK (kapalı
  platformlar) — bu ekran saf qwen/DCABOT farkı. TradingView Pine + Freqtrade
  (açık-kaynak) en yakın benzer: veri-indirme + doğrulama. DCABOT iyileştir
  mesi: qwen'den İLERİDE — `preflight` + `reproduce` + `export` ile
  "denetlenebilir veri" hikâyesi (hash-mühürlü artifact'ler) rakiplerde ve
  amatör araçlarda yok.
- Öneri: panel-3'ü "veri-kaynağı şeffaflığı"na çevir — her dataset-satırına
  artifact-hash + preflight-özeti + reproduce-bağı (mevcut uçlar, sıfır yeni
  backend).

### [Teknik Not + Öncelik]
- Katalog-tablosu VAR — üzerine: parite-panosu (keşif) + lab (preflight-
  görselleştirme) + script-üretici (istemci-metin) eklenir. Yeni bağımlılık YOK.
- Canlı-klines `fetch` qwen'de DOĞRUDAN Binance'e — DCABOT'ta tarayıcı→borsa
  doğrudan-çağrı YOK (sunucu-vekil ilkesi); lab yalnız sunucu-uçlarından beslenir.
- Öncelik: ORTA. Sıra: pano + lab-preflight (hazır uçlar) → script-üretici
  (DCABOT-formatlı) → ticker-sütunları (uç-gerekli).

## AA.7 (=`sec-backtest`, en teknik dilim): Backtest & Optimizasyon

### [Nesne Envanteri] (14: satır 516–679 + JS 1100–1200, 1314–1450)
1. Başlık ("Faz 4 + 4.5 · Gerçek Backtest & Optimizasyon" + boru-hattı
   özeti) + 2 rozet (GERÇEK VERİ·ANAHTARSIZ / SONUÇLAR HESAPLANIR) +
   `#btDataSrc` veri-kaynağı şeridi (`refreshBtDataSrc`).
2. 3-sütun yapılandırma: (1) Veri Kaynağı (parite/interval(1m/5m/15m/1h)/
   aralık(7/30/90/180g) select'leri + "📥 Geçmiş Veriyi Çek" `btFetch`
   [sayfalı Binance klines + 60-sayfa-kırpma + `btFetchStatus` + `btValid`
   kapı-çipleri] ); (2) 10 DCA parametresi (BO/SO/SO-sayısı/deviation/
   step/vol/TP/SL/bütçe/cooldown-mum); (3) Maliyet Modeli (maker/taker %,
   slipaj bps) + "ANTİ-HALÜSİNASYON KURALLARI" statik 6-madde + "▶
   BACKTEST'İ ÇALIŞTIR" (`btRunEngine`: veri-yok/kapı-kaldı kontrolleri +
   `runDcaBacktest` + `btRender` + AI-hafıza `addAiMemory` + toast).
3. Sonuçlar (`#btResults`, koşuya-kadar gizli): 9 metrik-kutusu (`btMetrics`:
   Net Kâr/ROI/İşlem/WinRate/ProfitFactor/MaxDD/Sharpe/SO-Dolum/Bütçe) +
   Equity eğrisi (`drawBtEquity` canvas) + Fiyat+İşlem-noktaları
   (`btPriceChart2` + `btIndBar` + giriş/exit marker'ları `setMarkers`) +
   İşlem Geçmişi tablosu (son 60: Giriş/Çıkış/GirişFx/ÇıkışFx/SO/Sebep-çipi
   [TP/SL]/PnL/PnL%) + "🚀 Bu parametreleri canlı bota kopyala" (`btDeploy`).
4. Faz-4.5 paneli + 3 sekme (`btpTabs`): OPT (parametre-uzayı 5×min/max +
   Tarama-Tipi [Rastgele-100/250, Izgara-≤300] + Amaç-Fonksiyonu [Sharpe/Net/
   PF] + Walk-Forward-toggle + ÇALIŞTIR + ilerleme-çubuğu [sayaç+ETA] +
   TP×sapma ısı-haritası [`renderOptHeat`: ≤6×6 `heatcell`, skor-renkli,
   tooltip'li, min-5-işlem-şartlı] + EN-İYİ-12 tablosu [`renderOptResults`:
   14 sütun (sıra★/TP/dev/step/vol/SO/İşlem⚠/Net/Win/Sharpe/MaxDD/OOS-Net/
   OOS-Sharpe) + "→ DCA formuna" satır-butonu (bt-f + f- alanlarına doldurur
   + önizleme-günceller) + OOS-negatif overfitting-uyarısı]); WF (açıklama +
   `wfRow`: ilk-6 OOS'li aday); MC (açıklama + `mcStats` 4-kutu + `mcCanvas`
   histogram — 500 bootstrap gerçek-trade-PnL).

### [DCABOT Karşılığı]
- Başlık + rozetler + veri-şeridi: **KISMİ** (katalog başlığı VAR; rozet
  disiplini VAR; backtest-bağlamlı şerit YOK).
- 3-sütun yapılandırma: **KISMİ** (dataset-seçici + profil-seçici +
  sihirbaz-DCA-alanları VAR ama DAĞINIK; tek backtest-formu YOK; maker/
  taker/slipaj-maliyet-formu YOK — backend `fee_rate`/`slippage` Config'te
  VAR; anti-halüsinasyon listesi YOK — ilkeler kodda+belgede).
- Çalıştır-butonu + kapı-kontrolü: **KISMİ** (katalog simülasyon-koşumu VAR
  + preflight-kapısı VAR; qwen akışı YOK).
- 9 metrik + equity + fiyat-marker + işlem-tablosu + deploy-kopyalama:
  **KISMİ** (`HistoricalChart` + `SavedRunsPanel` + run-detay VAR; 9'lu
  metrik-dizimi + equity-canvas + marker'lı-fiyat + 60'lık-trade-tablosu
  YOK; deploy-kopyalama YOK).
- OPT sekmesi (uzay/yöntem/ilerleme/ısı-harita/12'li-tablo/forma-doldur):
  **KISMİ** (sihirbaz AI-önerici `/api/sweeps/optimize` TÜKETİR ama bağımsız
  sweep-arayüzü YOK; ısı-harita YOK; aday-tablosu YOK).
- WF sekmesi: **YOK** (backend CPCV VAR ama WF-UI + WF-ucu YOK).
- MC sekmesi: **YOK** (backend PBO/DSR VAR ama MC-UI + MC-ucu YOK).

### [Backend-Gerçeklik]
- Backtest motoru: `historical_simulation` (exact, kapılı) + `/api/datasets/
  {id}/draft-level|run-plan|chart-data` + `/api/historical-runs/*` VAR —
  qwen'in istemci-float `runDcaBacktest`'inden KATBEKAT üstün; UI yalnız
  SONUÇ-GÖSTERİMİ yapar (hesap ASLA istemcide).
- Metrikler (net/ROI/win/PF/DD/Sharpe/SO): run-sonuç-sözleşmesinde KISMEN
  (özet-alanları + `final_economic_summary`); eksik metrik = yeni uç/alan
  (Claude) ya da kutu dürüst-boş. Trade-tablosu: execution-history/action-
  snapshot'lar VAR (`ActionTable` tüketiyor) → tablo yapılabilir.
- Sweep: `/api/sweeps/optimize` VAR (grid/random + exact-net-sıralama) —
  bağımsız OPT-arayüzü DOĞRUDAN buna bağlanır (sıfır yeni backend).
  Isı-harita: istemci-renklendirme (hesap yok, yalnız min-max normalizasyon —
  GÖRSEL ölçekleme, finansal hesap değil; kabul).
- WF/MC: backend modüller VAR (`combinatorial_purged_cv`,
  `overfitting_probability`) ama UÇ YOK → sekme ya "uç-yok" dürüst-boş
  rozetiyle iskelet ya Claude-uçları sonrası. MC-histogram verisi (500
  bootstrap) sunucudan gelmeli.
- Deploy-kopyalama ("canlı bota"): "CANLI" kelimesi YASAK-bağlam — DCABOT
  karşılığı "taslağa/sihirbaza doldur" (paper-yönlü); canlı-emir gate-dışı
  asla.
- Anti-halüsinasyon listesi: DCABOT ilkeleri DAHA KATI (kapılar kodda) →
  liste "çalışma-zamanı kapı-durumu"na çevrilir (preflight: GEÇTİ/KALDI +
  neden — GERÇEK durum, statik-metin değil).

### [Sektör-Karşılaştırma + İyileştirme]
- 3Commas backtest: YOK (kağıt-trading var, tarihsel-sim YOK) — qwen/DCABOT
  burada zaten önde. TradingView Strategy-Tester: metrik-tablosu + equity +
  trade-listesi (qwen bunu kopyalar); Freqtrade: hiperopt + ısı-harita-benzeri.
  DCABOT iyileştirmesi: (1) 9-metrik + equity + trade-tablosu aynen alınır,
  (2) her metriğe "kesinlik rozeti" (EXACT backend / FLOAT-analitik-sınırı —
  F.1/F.2/G.4 boundary disiplinini KULLANICIYA gösterir; kimsede yok),
  (3) "→ DCA formuna" akışı sihirbaza taşınır (mevcut preset-doldurma
  disipliniyle aynı).
- WF/MC: TradingView'de yok; profesyonel araçlarda (QuantConnect) var.
  DCABOT CPCV/PBO'yu UI'ya taşıyan İLK perakende-bot olur — ama yalnız uçlar
  hazırsa; önce iskelet+dürüst-boş.

### [Teknik Not + Öncelik]
- Backtest-UI = SONUÇ-GÖRSELLEŞTİRME katmanı; hesaplama-motoru istemciye
  ASLA taşınmaz (qwen'in `runDcaBacktest.js`'i referans-bile alınmaz).
- Uzun-sweep: J.3 notu geçerli (HTTP-döngüsü + ilerleme; şimdilik senkron,
  ilerleme-çubuğu anketli ya da SSE — yeni bağımlılık yok).
- `btDeploy` "canlı" kelimesi kodda YASAK (linter-dışı-disiplin: metin-
  incelemesi).
- Öncelik: EN YÜKSEK (motor hazır, UI yok — en büyük değer-açığı). Sıra:
  koşu-formu + sonuç-gösterimi (hazır uçlar) → OPT-arayüzü (hazır uç) →
  ısı-harita → WF/MC iskeletleri (uç-sonrası dolar).

## AA.8 (=`sec-modules`): Gelişmiş Modüller

### [Nesne Envanteri] (14: satır 682–685 + JS 2467–2492)
Başlık ("3Commas'ın Ötesine Geçen Modüller" + "Bölüm 2.4 · adaptif / AI
destekli / risk-farkında yetenekler") + `#modGrid` (`renderModules`): 11 kart
(`advMods`): [1] Volatility-Adaptive DCA, [2] Regime Detection & Auto-Switch,
[3] Correlation-Aware Risk Manager, [4] Anti-Liquidation Cascade, [5] Whale
Wall Detection, [6] AI Parametre Önerici, [7] Custom Strategy Scripting,
[8] Circuit Breaker / Kill-Switch, [9] Multi-Exchange Abstraction, [10]
Strategy Marketplace, [11] What-If Simülatörü. Her kart: emoji + başlık +
aç/kapa `switch` (kapalı→`opacity-60` + feed bildirimi) + açıklama + kırmızı
"✗ 3Commas: …" zayıflık-satırı.

### [DCABOT Karşılığı]
Modül-kart ızgarası + toggle'lar: **YOK**. Ancak İÇERİK eşleşmesi güçlü —
11 modülün backend durumu: [1] **VAR** (B.1 `volatility_adaptive_dca`),
[2] **VAR** (F.1 `regime_detection`), [3] **VAR** (F.2 `correlation_risk`),
[4] **YOK + YASAK** (LCR-12: likidasyon-tahmini/kaldıraç-otomatı asla),
[5] **VAR motor** (E.3, UI LabPanel'de "yakında"), [6] **VAR** (B.2 AI-Önerici
+ sweep), [7] **KISMEN** (B.7 `CONTRACT.md` iskelet, BLOCKED), [8] **VAR**
(B.3 kill-switch + RiskPanel), [9] **KISMEN** (B.6 port-desen README, kod
yok), [10] **KISMEN** (B.4-ui preset-galerisi; A/B-sürümleme YOK),
[11] **VAR** (B.5 What-If otomatik-koşu). Toggle-kavramı: DCABOT'ta modüller
"aç/kapa" değil "bağlı sürüm/kapı" ile yönetilir — switch YOK.

### [Backend-Gerçeklik]
Bu ekran YÖNETİM değil KEŞİF ekranı olmalı: modül-varlığını + durumunu
gösteren salt-okunur kartlar (durum: ÇEKİRDEKTE/BAĞLI/İSKELET/YOK —
GERÇEK durum, `run_checks`/katalogdan değil, DERLEME-SABİTİ + uç-yoklaması).
Toggle'lar taşınmaz (DCABOT'ta çalışma-zamanı modül-kapama kavramı yok;
olsa bile ürün+gate kararı). Whale-wall kartı E.3-canlı-gösterime bağlanır
(gelince). Marketplace kartı preset-galerisine derin-bağlanır (VAR).
Anti-Liq kartı KONULMAZ (yasak kavramın reklamı bile yapılmaz).

### [Sektör-Karşılaştırma + İyileştirme]
3Commas "özellik-listesi" pazarlama-sayfası var ama UYGULAMA-İÇİ modül-
galerisi YOK; Pionex/Bitsgap'te de yok. qwen'in "✗ 3Commas: …" satırları
pazarlama-dili — DCABOT'ta "durum + belge-bağı" olur (KARARLAR/kanıt
referanslı, doğrulanabilir iddia). İyileştirme: her karta "kanıt" bağı
(`evidence/FAZ-*/SONUC.md` karşılığı + test-sayısı) — rakiplerde+açık-
kaynakta olmayan denetlenebilirlik vitrini.

### [Teknik Not + Öncelik]
- Salt-okunur kart ızgarası; veri DERLEME-SABİTİ + `SystemStatusCard`
  canlılık-bilgisi. Yeni uç GEREKMEZ (ilk sürüm).
- Öncelik: DÜŞÜK. Bağımsız, risksiz, vitrin-değeri. AA.2–AA.4'ten sonra.

## AA.9 (=`sec-ai`): Bot AI · Copilot

### [Nesne Envanteri] (14: satır 688–727 + JS 2494–2597)
Başlık + 2 DÜRÜSTLÜK rozeti ("🔧 GELİŞTİRME AŞAMASI: KURGUSAL" /
"🚀 DEPLOY'DA: GERÇEK LLM + VEKTÖR HAFIZA") + 2-sütun: (A) sohbet paneli
(yeşil `pingr` nabız + "Bot AI" + "model: kurgusal-hg-1" + `#aiChat`
[min 380/max 440 kaydırmalı] + `#aiChips` 6 hazır-soru + input + Gönder;
`aiAsk`: "🤖 hafızadan okunuyor…" yazıyor-göstergesi 500–900ms → `aiAnswer`
REGEX-eşleşmeli hazır-yanıtlar [optimizasyon/walk-forward/backtest/xmr/api/
mimari/durum(CANLI sayılar!)/hafıza] + "— hafızadan okundu · sorgu #N" imzası
+ stats artışı [reads+1, tokens+=rastgele!]) ; (B) hafıza-bankası (`memCount`
+ 2 kutu [HAFIZADAN OKUNAN, TAHMİNİ TASARRUF ~tok] + snapshot-butonu
[`memSnap` → `addAiMemory` DURUM-kaydı] + JSON-dışa-aktar [`memExport` →
panoya] + `#memList` [40-kayıt-sınırlı kartlar: kategori/başlık/metin/
oluşturma/doğrulama] — localStorage `hg_ai_v1`, 4 tohum-kayıt `aiInit`).

### [DCABOT Karşılığı]
Sohbet + hafıza-bankası: **YOK**. En yakın: `ExplanationSection` (açıklama
metinleri) + `EventPanel` (olay akışı) + sihirbaz AI-önerici (B.2 — GERÇEK
sweep-tabanlı, LLM değil). Dış-LLM: açık-soru (DEFERRED).

### [Backend-Gerçeklik]
- Kurgusal-sohbet ASLA taşınmaz (regex-yanıt + rastgele-token-sayacı =
  halüsinasyon-teşhirı; qwen kendisi "KURGUSAL" diye etiketlemiş).
- GERÇEK karşılığı iki katmanlı: (1) "durum-özeti" soruları (`aiAnswer`'ın
  CANLI-dalı: bot/deal/depo sayıları) → MEVCUT uçlardan (`/api/dashboard`,
  `/api/events`) beslenen KURAL-TABANLI yanıtlayıcı (LLM'siz, deterministik,
  alıntılı) — yapılabilir, sıfır yeni backend; (2) açık-uçlu sorular → DIŞ-
  LLM (DEFERRED, ürün+maliyet+gizlilik kararı — API-anahtarı asla istemcide/
  sohbette olmaz, qwen'in kendi kuralı da bu).
- Hafıza-bankası: DCABOT karşılığı `docs/KARARLAR.md` + `evidence/**` +
  run-kayıtları (GERÇEK kalıcı-hafıza, dosyada) → UI "karar/kanıt-gezgini"
  olabilir (salt-okunur, mevcut dosyalar — yeni backend yok).
- Snapshot-butonu: "durum-snapshot" = `/api/dashboard` + canary + dataset-
  sayacı tek-görünümde dondurma (istemci-derlemesi, hesap yok) — yapılabilir.

### [Sektör-Karşılaştırma + İyileştirme]
- 3Commas AI: "kapalı-kutu" bot-ayar-sihirbazı; Pionex: sinyal-takip;
  Bitsgap: asistan-YOK. Hiçbiri alıntılı/deterministik-değil. DCABOT
  iyileştirmesi: LLM'siz-önce — "her yanıtın altında kaynak-uç + saat"
  disiplinli kural-yanıtlayıcı (rakiplerde yok) + LLM gelirse "kurgusal
  rozeti" standardı (qwen'in rozet-dürüstlüğü korunur).
- Öneri: AA.9 ilk-sürüm = "Durum Asistanı" (5 hazır-soru: durum/canary/
  son-koşu/veri-hazırlık/kapılar — hepsi mevcut-uç) + kanıt-gezgini.

### [Teknik Not + Öncelik]
- Yanıtlayıcı: istemci-şablon + `fetch` (mevcut `apiFetch` disiplini);
  streaming YOK (kural-yanıtı anlık). Sohbet-girdi a11y (label + Enter).
- Dış-LLM bağlanırsa: sunucu-vekil ZORUNLU (anahtar sızmaz) + hız-limiti +
  maliyet-göstergesi.
- Öncelik: DÜŞÜK-ORTA. Sıra: Durum-Asistanı (sıfır-backend) → kanıt-gezgini
  → dış-LLM (ürün kararı sonrası).

## AA.10 (=`sec-risk`): Risk Paneli & Tarayıcılar

### [Nesne Envanteri] (14: satır 730–760 + JS 2600–2673)
1. Circuit-Breaker paneli: başlık + "Korumayı Aktifleştir" switch'i
   (`armSw` → `appData.armed` + toast) + DD-satırı (SABİT "-%1,8" / eşik
   "-%5,0") + `ddBar` (%36 gradient, eşik-slider'ı 2–15 adım-.5 ile
   `1.8/eşik` SABİT-pay yeniden-hesaplar!) + "⛔ GLOBAL KILL-SWITCH"
   (`killBig`: kurulu-değilse "Önce korumayı aktifleştirin" engeli).
2. Liquidation-Engine paneli: 3 statik çip (Cross/Isolated MM, Tiered MMR,
   Auto-Deleverage) + `#liqList` (`renderLiq`: deal-başına SAHTE-formül liq +
   mesafe + <%8 danger-vurgusu).
3. Korelasyon-Matrisi: açıklama ("yüksek korelasyonda marjin kısıtlanır") +
   `#corrGrid` (`buildCorr`: SABİT 5×5 matris, eşik-renkli).
4. Funding-Tarayıcı: açıklama + 6-sütun tablo (`renderFunding`: SABİT
   `fundRows` oran/ofset × fiyat → spot/futures/baz + negatifte "★ fırsat").
5. Global-kill (başlık-çubuğu): `#ksBtn` (iki-aşamalı-onay: "⚠️ Emin
   misiniz?" + 3sn zaman-aşımı) + `#ksBanner` + `#ksResume` (normale-dön).

### [DCABOT Karşılığı]
- Circuit-Breaker + DD-bar + eşik-slider: **KISMİ** (`RiskPanel`: "Neden
  işlem açılmıyor" + canary + kill-switch-sebepli VAR; DD-göstergesi + eşik-
  ayarı YOK).
- Kill-switch (büyük-buton + kurma-engeli + banner + resume): **KISMİ**
  (backend `/api/risk/kill-switch` + panel VAR; iki-aşamalı-onay + banner +
  resume-akışı KISMİ — `ConfirmDialog` VAR, global-banner YOK).
- Liquidation-Engine: **KISMİ** (`LiquidationStatusSection` + venue-ucu VAR;
  liste-düzeni + 3-çip YOK — çiplerdeki "Auto-Deleverage" KAVRAMI YASAK).
- Korelasyon-matrisi: **YOK** (F.2 backend VAR, UI YOK).
- Funding-tarayıcı: **YOK** (uç YOK).
- Başlık kill-butonu: **YOK** (`AppShell` başlığında kill YOK).

### [Backend-Gerçeklik]
- Kill-switch: TAMAMEN VAR (`POST /api/risk/kill-switch` + canary `GET`) —
  kurma-önkoşulu + iki-aşamalı-onay + banner + resume DOĞRUDAN bağlanır
  (sıfır yeni backend). DD-değeri: backend YOK (günlük-DD izleyici yok) →
  bar ya "uç-yok" boş ya DD-ucu (Claude); qwen'in SABİT-%1.8'i asla örnek
  alınmaz. Eşik-slider: eşik-KAYDI backend'i YOK → slider ya salt-görsel-
  filtre ya uç-sonrası (dürüst-etiketle).
- Liq-listesi: venue-ucu VAR (`/api/risk/liquidation-status/{symbol}`) —
  SEMBOL-BAZINDA gerçek-değer; liste = kayıtlı-semboller × uç (N+1 çağrı —
  toplu-uç daha iyi, Claude'a not). SAHTE-formül + Auto-Deleverage ASLA.
- Korelasyon: F.2 `correlation_risk` + `correlation_scores` VAR ama UÇ YOK
  → matris için uç ŞART (Claude); gelene-kadar dürüst-boş ("matris-ucu yok").
  qwen'in SABİT-matrisi örnek alınmaz.
- Funding: uç YOK (venue funding-saati/oranı) → tablo dürüst-boş ya da
  iskelet. Spot-futures-baz HESABI sunucuda olmalı (UI hesap YASAK).
- Başlık-kill: `AppShell`'e kill-durum rozeti + diyaloglu-buton (mevcut
  bileşenler, sıfır yeni backend).

### [Sektör-Karşılaştırma + İyileştirme]
- 3Commas: portföy-stop-loss + bildirimler (kill-benzeri YOK — qwen'in
  "acil durdurma yok" satırı doğru); Pionex: manuel-kapatma; Bitsgap:
  stop-loss-şablonları. DCABOT kill-switch + canary ile ZATEN önde —
  AA.10 bunu GÖRÜNÜR kılar (başlık-banner + risk-sekmesi).
- İyileştirme: (1) DD-bar'a "ölçüm-penceresi + kaynak-uç" notu (rakipler
  DD-tanımını gizler), (2) korelasyon-matrise "eylem-bağı" (yüksek-hücre →
  ilgili botlar — F.2 `correlation_breach` kararıyla), (3) funding-tabloya
  "sonraki-funding geri-sayımı" (AA.2 fundCount ile aynı uç).
- "Kurma-önkoşulu" (arm-önce-kill): 3Commas'ta yok; DCABOT güvenlik-farkı
  olarak korunur + resume-akışı denetim-izli (sebep-zorunlu, mevcut).

### [Teknik Not + Öncelik]
- Risk-sekmesi = mevcut `RiskPanel` + `LiquidationStatusSection` + YENİ
  korelasyon/funding/DD-kutuları (iskelet+dürüst-boş). Banner: `AppShell`
  üst-şerit (rol=alert).
- N+1 liq-çağrısı ilk-sürümde kabul (sembol-sayısı küçük) + toplu-uç notu.
- Öncelik: YÜKSEK (kill/canary görünürlüğü güvenlik-kritik). Sıra: banner +
  kurma-akışı (hazır) → liq-listesi (hazır uç) → DD-eşik (uç/karar) →
  korelasyon + funding (uç-sonrası).

## AA.11 (=`sec-core`): Çekirdek & Modül Mimarisi

### [Nesne Envanteri] (14: satır 763–821 + JS 2691–2811)
1. Başlık + "ÇEKİRDEK DONMUŞ v2" rozeti.
2. Mimari-topoloji paneli (2/3): `#coreTop` (INFRA+MOTOR çipleri) +
   EVENT-BUS şeridi (gradient + 3 `busdot` animasyon-noktası + "EVENT BUS ·
   PROTOKOL v2") + `#coreBottom` (STRATEJİ+ÖZEL çipleri) — `renderCoreDiagram`
   (`allModules` üstünden; çip: durum-noktası + id + FAM·ver).
3. Event-Bus-Trafiği paneli (1/3): "simüle" etiketli başlık + `#busRate`
   ("— olay/dk") + `#busFeed` (14-satır-sınırlı log; içerik RASTGELE havuzdan
   `pool[rnd]` — örn. "order.request → mod.exec"; hız SAHTE `busCount*4`).
4. Modül-Kayıt-Defteri: `#coreCount` ("N modül · M aktif") + `#coreRegistry`
   (`renderCoreRegistry`): 9 yerleşik modül (`CORE_MODULES`: core.bus,
   mod.data, mod.exec, mod.risk, strat.dca, strat.grid, strat.arb [pasif],
   engine.backtest, engine.optimize — her biri: fam-çipi + id + ver + AKTİF/
   PASİF + 🔒 donmuş ya da toggle + özelse 🗑 + "Sözleşme ▾" genişletici
   [ABONE çipleri + YAYINLAR çipleri + PARAMETRELER]) + localStorage özel-
   modüller (`hg_core_custom_v1`, ekle/kapama/silme).
5. Plugin-ekleme formu: Modül-Adı + Strateji-Ailesi (5 seçenek) + Açıklama +
   2 parametre (ad+varsayılan) + "🔌 Plugin'i Kaydet (pasif başlar)"
   (`csSave` → `addCustomStrategy` → localStorage + feed + re-render).

### [DCABOT Karşılığı]
- Topoloji + bus-şeridi + trafik + kayıt-defteri + plugin-formu: **YOK**.
  En yakınlar: `strategies/custom/CONTRACT.md` (B.7 — `decision(State,
  Config)` imza, BLOCKED), `data_adapters/README.md` (B.6 port-desen),
  `indicator_registry` (G.4 — GERÇEK kayıt-defteri!), `/api/events` +
  `EventPanel` (GERÇEK olay akışı), `SweepPanel`-yokluğundaki optimizasyon
  kayıtları.

### [Backend-Gerçeklik]
- DCABOT'ta event-bus YOK (mimari farklı: doğrudan modül-çağrıları +
  FastAPI) → bus-şeridi/trafiği KAVRAM OLARAK taşınmaz; karşılığı `/api/
  events` akışı (GERÇEK, EventPanel VAR) — "trafik" kutusu events-özetine
  bağlanabilir (sayaç + son-N — mevcut uç).
- Kayıt-defteri: G.4 `indicator_registry` GERÇEK kayıt-defteri örneği;
  STRATEJİ-kaydı YOK (B.7 BLOCKED) → defter ya gösterge-kayıt + veri-
  adaptör-katalogu (GERÇEK içerik) ya dürüst-boş.
- Plugin-formu: B.7 BLOCKED (kod-bağlama yok) → FORM KONULMAZ (ölü-form
  yasağı); karşılığı "strateji-sözleşmesi belgesi" salt-okunur-görünüm
  (CONTRACT.md render — yeni backend yok).
- Sürüm/durum çipleri: derleme-sabiti + uç-yoklaması (AA.8 ile aynı desen).

### [Sektör-Karşılaştırma + İyileştirme]
- Rakiplerde mimari-topoloji ekranı YOK (kapalı-kutu); Freqtrade'de strateji
  listesi + hyperopt-durumu var (en yakın). DCABOT iyileştirmesi:
  "denetlenebilir-mimari" — kayıt-defteri + sözleşme-genişleticiler +
  kanıt-bağları
  (AA.8 kartlarıyla birleşir; tek "Sistem" sekmesi).
- Öneri: bus-trafiği yerine GERÇEK events-özeti (son-14 + tür-sayaçları) —
  qwen'in simüle-akışından dürüst.

### [Teknik Not + Öncelik]
- Salt-okunur topoloji (CSS-grid, animasyonlu-nokta CSS) + events-özeti
  (mevcut uç, anketli). Plugin-formu YOK (BLOCKED kalkmadan).
- Öncelik: DÜŞÜK. Vitrin + geliştirici-güveni. AA.8 ile birleştirilebilir.

## AA.12 (=`sec-grid`): Infinity Grid + Hybrid Engine

### [Nesne Envanteri] (14: satır 824–851 + JS 2814–2849, 3040)
Başlık ("Geometrik grid · dinamik taban · 3 fazlı hibrit akış (kavramsal)")
+ 2/3: lejant-çipleri (Dinamik-Alt-Taban / Grid-Adımları / Dinamik-Üst-Tavan)
+ `gridCanvas` (`drawGrid`: 9 geometrik-seviye + kesikli-TABAN + kesikli-TAVAN
+ fiyat-yolu — YOL RASTGELE `gridSim.path`, taban/adım parametreli) + 1/3:
"Hybrid Engine Fazları" (3 statik faz-kartı `ph-0/1/2`, `cyclePhase` 6sn'de
bir DÖNÜŞÜMLÜ-aktif + feed + `phaseLog` — dekoratif) + kontroller (Grid-Adımı
slider .2–3 adım-.1 + canlı-etiket; 2 görsel-toggle [Dynamic-Floor, Futures-
Rebalancing — SADECE sınıf-değiştirir]; `phaseLog`).

### [DCABOT Karşılığı]
Grid-canvas + faz-kartları + kontroller: **YOK**. En yakın: `FuturesPanel`/
`FuturesDcaForm` + `FuturesGridMarginView` (marjin-PROJEKSİYONU, grid-motoru
değil) + botdetail'deki GRID-tipi `_settings`-satırı (qwen tarafı).

### [Backend-Gerçeklik]
- Grid MOTORU YOK (DCABOT DCA-öncelikli; grid P1-kapsam-dışı) → canvas +
  faz-döngüsü + rebalancing-toggle KONULMAZ (uysal-olmayan kavramın UI'ı
  olmaz). `POST /api/futures/grid/margin` (marjin-projeksiyonu) VAR —
  grid-bağlamlı TEK gerçek: mevcut `FuturesGridMarginView` korunur.
- Grid-Adımı-slider: motorsuz-anlamsız → YOK. Dynamic-floor: kavram YOK → YOK.
- Dürüst-alternatif: "Grid (yol-haritası)" iskelet-kartı — "motor yok,
  marjin-projeksiyonu mevcut" + forma-bağlantı (mevcut görünüme derin-bağ).

### [Sektör-Karşılaştırma + İyileştirme]
- Pionex = grid-amirali (Infinity-Grid ürünü VAR); 3Commas grid-bot VAR;
  Bitsgap grid VAR. DCABOT grid'de YOK — bu BİLİNÇLİ kapsam (DCA-önce).
  qwen grid'i kavramsal-süs; Pionex-ölçüsünde grid-motoru AYRI-FAZ işi
  (ürün kararı + motor + testnet).
- İyileştirme (motor-gelirse): Pionex'ten farklı — grid-seviyeleri exact-
  backend + "taban-gerekçesi" (neden-bu-taban: ATR/son-N — alıntılı).

### [Teknik Not + Öncelik]
- EN-DÜŞÜK (motorsuz-UI yasak). İskelet-kart tek hamle; motor-fazı açılırsa
  bu araştırma güncellenir.

## AA.13 (=`sec-deploy`): Deployment — Hedef Senaryo

### [Nesne Envanteri] (14: satır 854–885 + JS 2874–2935)
1. Başlık + SARI DÜRÜSTLÜK bandı ("hedef senaryoyu canlandırır; metrikler
   demo amaçlıdır").
2. `#svcGrid` (`renderServices`): 6 servis-kartı (`svcData`: postgres/
   redis/backend/frontend/backtest_worker[Celery]/bot_ai — her biri: nabız-
   noktası + ad + RUNNING-çipi + imaj·port + rol + CPU/RAM barları
   [`jitterServices` RASTGELE sallar]).
3. `docker-compose.yml` `pre` bloğu ("hedef yapı" çipi; 6 servis + `.env`
   TESTNET-anahtar-notu [sohbette-paylaşılmaz!] + celery-worker + AI-copilot
   komutları).
4. Yayın-terminali: "↻ tekrar" + `#deployTerm` (daktilo-animasyonlu
   `deployScript`: ssh→git-pull→compose-up→health-curl→"TAMAMLANDI
   (canlandırma) 🚀").

### [DCABOT Karşılığı]
Servis-ızgarası + compose + terminal: **YOK**. En yakın: `SystemStatusCard`
(canlılık) + `BackupPanel` (yedekler) + footer rozetleri (Local-only) +
`/api/health` + Cloudflare-Tunnels offline-first ilkesi (belgede).

### [Backend-Gerçeklik]
- DCABOT mimarisi FARKLI (yerel-önce: tek-backend + dosyalar + SQLite-yok/
  postgres-yok + redis-yok + celery-yok) → qwen compose'u KOPYALANMAZ.
  Gerçek-karşılık: "yerel-kurulum sağlığı" (backend-UP + veri-dizini yazılabilir
  + disk + yedek-durumu) — KISMEN uç VAR (`/api/health`, `/api/backups`? —
  BackupPanel'in ucu) + eksikler dürüst-boş.
- Servis-kartları → "bileşen-durumu" (backend/dataset deposu/run-store/
  testnet-bağlantısı — GERÇEK yoklamalar). CPU/RAM barları: İSTEMCİ-ölçümü
  YOK (yanıltıcı olur) → konulmaz ya da sunucu-`health`-genişletmesi (Claude,
  düşük-öncelik).
- Terminal-animasyonu: canlandırma ASLA taşınmaz; karşılığı "kurulum-
  kılavuzu" (Cloudflare-Tunnels adımları — statik-belge, mevcut-ilke).
- `.env`-anahtar-notu: DCABOT ilkesiyle BİREBİR (credential-asla-dosya/
  prompt) — kılavuza taşınır.

### [Sektör-Karşılaştırma + İyileştirme]
- Rakipler SaaS (deploy-kavramı YOK); Freqtrade/Docker-kullananlar: compose-
  dosyası + dokümantasyon. DCABOT iyileştirmesi: "tek-tık-yerel-sağlık" —
  kurulum-doğrulayıcı (dizinler+yazma+uç-yoklaması, YEŞİL/KIRMIZI liste) +
  yedek-geri-yükleme (mevcut `BackupPanel` genişler). Rakiplerde yok.
- Öneri: AA.13 = "Sistem & Yedekler" sekmesi (status + backup + kılavuz) —
  qwen-süsleri yok, operasyon-gerçeği var.

### [Teknik Not + Öncelik]
- Mevcut paneller birleşir + sağlık-yoklaması (zaten periyodik-disiplin VAR
  mı — `apiStatus` anketli; genişletilir). Yeni bağımlılık YOK.
- Öncelik: DÜŞÜK-ORTA. Sıra: sağlık-listesi (hazır) → yedek-UX (mevcut) →
  kılavuz (statik).

## AA.14 (=#17 + #21/#22 `sec-lab`): Strateji Laboratuvarı

### [Nesne Envanteri] (#17: satır 92–177 + JS 258–409; #21/#22 özet-varyant)
1. `sec-portfolio`: tahsis-halkası (`drawDonut` canvas + `#allocLegend` +
   ortada toplam-$) + `#portSummary` (Toplam-PnL/Aktif/Kazançlı/Zararlı) +
   `#botRows` (bot-başına PnL-barları) + başlık-çipleri (`#hBots/#hPnl`).
   VERİ: SABİT `bots[5]` dizisi (alloc% + pnl$).
2. `sec-compare`: sembol-select + "▶ Karşılaştır" (`runCompare`: DCA/Grid/
   Hybrid İSTEMCİ-float simleri `runDCA/runGrid/runHybrid` [canlı-veya-sim
   mumlar] + `cmpChart` 3-seri equity + lejant) + 7-sütun metrik-tablosu
   (`cmpTable`: Net/ROI/Win/MaxDD/Sharpe/İşlem; boş-durum "Karşılaştır ile
   çalıştırın") + en-iyi-Sharpe toast'ı.
3. `sec-config`: tip/parite/yön + 6 sayı (BO/SO/MaxSO/dev/TP/SL) + "🚀
   Fırlat (Paper)" (`cfgLaunch` → `launchedList` PAPER-çipli-satırlar) +
   "🔬 Önce Parite Testi" (`cfgParity` → yönlendirme-toast'ı).
4. `sec-ai`: `#aiRecs` 3 SABİT öneri-kartı (ağırlık-artır/SL-sıkılaştır/
   parite-eşiği).
5. #21/#22 `sec-lab`: yalnız `cmpChart` (DCA/Grid[/Hybrid]) + lejant —
   özet-varyant, yeni-nesne YOK.

### [DCABOT Karşılığı]
- Portföy-halkası + özet + bot-satırları: **YOK** (`DashboardPanel` sayaç-
  tablosu VAR; dağılım-görseli YOK).
- Karşılaştırma (grafik + 7-sütun): **YOK-UI** ama **BACKEND-VAR** (B.4
  `preset_comparison`: aynı-dataset yan-yana materialize+simulate!) —
  en-değerli eşleşme.
- Konfigüratör + Paper-fırlat + liste: **KISMİ** (sihirbaz + `/api/bots`
  kayıt + paper-session POST'ları VAR; "fırlat-listesi" YOK).
- AI-öneri-kartları: **KISMİ** (B.2 GERÇEK sweep-önerici VAR; kart-dizimi
  YOK — qwen-kartları sabit-metin).

### [Backend-Gerçeklik]
- Karşılaştırma: B.4-motor DOĞRUDAN bağlanır (aynı-dataset, exact) —
  qwen'in istemci-float 3-motoru ASLA taşınmaz. Grid/Hybrid SÜTUNLARI
  konulmaz (motor YOK) — tablo DCA-varyantları-karşılaştırır (B.4'ün
  gerçek-kapsamı) + "Grid/Hybrid motor-yok" notu.
- Portföy: tahsis = bot-bütçeleri (`virtual_quote_budget` VAR, `/api/bots`
  profilinde) + PnL = deal-kâr-uçları (YOK — AA.3 ile aynı bağımlılık) →
  halka ilk-sürümde BÜTÇE-dağılımı (gerçek) + PnL dürüst-boş.
- Fırlat: `/api/bots` + paper-session POST'ları VAR → "paper-fırlat"
  GERÇEK akış olur (CANLI-fırlat YOK; PAPER-çipi ZORUNLU — qwen'de VAR).
- Parite-testi-butonu: backtest-koşusuna derin-bağ (AA.7 hazır-olunca).
- AI-kartları: B.2-önerici SONUCU kartlaşır (gerçek-sweep-alıntılı) —
  sabit-metin ASLA.

### [Sektör-Karşılaştırma + İyileştirme]
- 3Commas: bot-karşılaştırma YOK (tek-tek backtest-yok); Pionex: strateji-
  kopyalama (karşılaştırmasız); Bitsgap: demo-karşılaştırma-yok. TradingView:
  çoklu-strateji-overlay YOK. DCABOT B.4-UI ile KATEGORİ-İLKİ olur:
  "aynı-veri + alıntılı-metrik + tek-tık-sihirbaza" (qwen'in "→ DCA formuna"
  akışıyla birleşir).
- Portföy-halkası: borsalarda standart (Binance pie); bot-platformlarında
  nadir. DCABOT farkı: dilim-altı "hangi-bot + bütçe-kaynağı" (denetlenebilir
  tahsis).
- İyileştirme: karşılaştırma-tablosuna "fark-sütunu" (ΔNet vs seçili-baz —
  SUNUCU-hesabı, B.4-motor-genişletmesi, Claude).

### [Teknik Not + Öncelik]
- B.4-sonucu → tablo+grafik (mevcut çizim-yığını); halka-canvas bağımsız
  (`drawDonut` deseni taşınabilir — VERİ gerçeğe bağlanır).
- Öncelik: YÜKSEK (B.4-motor hazır, UI-sıfır — AA.7 ile aynı değer-açığı).
  Sıra: karşılaştırma-UI (hazır backend) → portföy-halka (bütçe-gerçeği) →
  fırlat-listesi → AI-kartları (B.2-bağlı).

## AA.15 (=#18 + #21/#22 `sec-exec`/`sec-tests`): Execution Console

### [Nesne Envanteri] (#18: satır 92–171 + JS 189–293; #21/#22 özet)
1. `sec-conn`: API-Key/Secret password-alanları + "Kaydet (.env)" (`saveKeys`
   → SİMÜLE-yazım + DRY→TESTNET mod-değişimi) + "Bağlantıyı Test Et"
   (`testConn` → SAHTE-ping toast+log) + `connStatus` ("Anahtar girilmedi →
   DRY-RUN, emir gönderilmez") + Faz-8-geçiş-koşulları (3 madde: paper✓/
   anahtar-bekleniyor/mod-notu) + mod-kutusu (DRY-RUN/TESTNET + "Gerçek
   emir: KAPALI").
2. `sec-orders`: orderbook (`renderOrderBook`: ortadan ±%0.04/katman ÜRETME
   6+6 satır + rastgele-miktar + derinlik-barları, 1.2sn-yenileme; fiyat
   canlı-veya-sim) + emir-formu (sembol/yön/LIMIT-MARKET/miktar/fiyat[oto])
   + "📨 Emir Ver (DRY-RUN)" (`placeOrder`: NEW→WORKING→FILLED zamanlayıcılı
   + RASTGELE-PnL + toast) + aktif-emirler (`renderOrders`: durum-çipleri +
   İptal-butonu + başlık-sayaçları `hOrders/hFills/hMode`) + geçmiş-tablosu
   (`renderHistory`: 8-sütun Zaman/Sembol/Yön/Tip/Miktar/Fiyat/Durum/PnL +
   "Henüz emir yok" boş-durumu).
3. `sec-execlog`: `#execLog` (öne-eklemeli 80-satır-sınırlı + Temizle) —
   emir-döngüsü + mod-değişimi + ping-satırları.
4. #21/#22 `sec-exec`: özet-varyant (anahtar-alanları + mod-kutusu + "EMİR
   YAŞAM DÖNGÜSÜ" log) + `sec-tests`: "MOTOR BİRİM TESTLERİ" (`runTests`:
   14 tarayıcı-içi test [DCA/Grid/Engine + CostEngine-fee/liq/arb + ATR +
   rejim] → PASS/FAIL-listesi + sayaç-toast; sekme-açılışında otomatik-koşar).

### [DCABOT Karşılığı]
- Anahtar-formu + test + mod-kutusu: **YOK + KISMEN-YASAK** (anahtar-giriş-
  UI'si credential-kuralına AYKIRI — ASLA yapılmaz; mod-göstergesi + testnet-
  durumu VAR-olabilir: `testnet/account` yoklaması).
- Orderbook: **YOK-UI** ama **BACKEND-VAR** (`binance_public_depth` E.3!) —
  gerçek-derinlik bağlanabilir.
- Emir-formu + yaşam-döngüsü + iptal + geçmiş: **KISMİ** (paper `orders`/
  `fills` POST'ları + `open-orders` testnet-GET VAR; emir-UI YOK).
- Execution-log: **KISMİ** (`EventPanel` + `/api/events` VAR; emir-odaklı
  filtre YOK).
- Birim-test-koşucu: **YOK** (karşılığı: `run_checks.py` geliştirici-aracı;
  ÜRÜN-UI'si değil).

### [Backend-Gerçeklik]
- Emir-formu: CANLI/TESTNET-emir YOK (gate-dışı) → form YALNIZ paper-kapsamlı
  (`/api/paper/sessions/.../orders|fills` GERÇEK akış: emir-aç + dolum-kaydet
  + iptal=durum) + "PAPER" çipi ZORUNLU. LIMIT/MARKET + qty/price: paper-
  model-alanlarıyla BİREBİR (sözleşme-dışı-alan YOK).
- Orderbook: `binance_public_depth` + E.3-whale VAR → GERÇEK bid/ask +
  derinlik + (E.3-gelince) duvar-işaretleri. qwen-üretme ASLA.
- Aktif-emirler: paper-oturum-açık-emirleri (VAR) + testnet `open-orders`
  GET (VAR, salt-okunur!) — İKİ-AYRI-BLOK (karışmaz; testnet-satırı "salt-
  okunur" rozetli).
- Geçmiş: fills-kayıtları (paper) + events (sistem) → tablo yapılabilir;
  PnL-sütunu sunucu-hesabı (yoksa dürüst-boş).
- Anahtar-UI: YASAK (AGENTS.md kural-1). Testnet-hazırlık: "credential-
  durumu" GÖSTERGESİ (dosya-dışı-bellek-yoklaması — NASIL gösterileceği
  Claude+Arda kararı; varsayılan: metin-kılavuz).
- Test-koşucu: ÜRÜN-UI OLAMAZ (test-sonuçları geliştirici-artefaktı) →
  karşılığı "sistem-durumu" (AA.13) + `review=NOT_RUN` şeffaflığı.

### [Sektör-Karşılaştırma + İyileştirme]
- 3Commas SmartTrade-terminali: qwen-birebir (orderbook YOK-3Commas'ta;
  TradingView-grafik VAR). Binance-emir-paneli: orderbook+form+geçmiş
  (qwen-birebir). DCABOT iyileştirmesi: (1) orderbook + whale-duvarları
  (E.3 — borsalarda-bile-yok), (2) DRY-PAPER-TESTNET üç-kipli mod-çipi
  (qwen-iki-kipliden net), (3) her-dolumda "neden-bu-fiyat" (paper-fill-
  politikası alıntısı — F27 explicit-fill ilkesi, rakiplerde-yok).
- Test-koşucu: rakiplerde YOK; profesyonel-açık-kaynakta CI-rozeti VAR.
  DCABOT karşılığı: footer'a "checker: PASS 1893 · <tarih>" DERLEME-
  damgası (denetlenebilirlik, sıfır-yeni-backend).

### [Teknik Not + Öncelik]
- Paper-emir-UI = form + liste + geçmiş (hazır-uçlar); testnet-satırlar
  salt-okunur-ayrı-blok. Orderbook: anketli-derinlik (hız-limiti-saygılı
  + "X-sn-önce" damgası).
- Anahtar-alanı KODDA-YASAK (metin-incelemesi + PR-kuralı).
- Öncelik: ORTA-YÜKSEK (paper-emir-UI hazır-backendli; testnet-satırlar
  salt-okunur). Sıra: paper-emir (hazır) → orderbook (hazır-adaptör) →
  testnet-salt-okunur → mod-göstergesi (karar-sonrası).

---

## AA.0 Kapanış Notu (muse)

1. **Kapsam**: #14'ün 15 bölümü + #17/#18/#21/#22 tarandı; HER bölümde HER
   nesne envantere alındı (yukarıda satır-referanslı). Okunmayan qwen dosyası
   kalmadı (bu turun brief-kapsamında).
2. **Kritik dürüstlük-hattı** (AA-uygulamasında ASLA çiğnenmeyecek):
   Lightweight-Charts-CDN taşınmaz (offline-first); istemci-float-hesap
   taşınmaz (exactness); `0.95/lev` likidasyon-formülü + `entry*0.88…`
   fon-formülü + `Math.random`-veriler + sabit-matris/kartlar taşınmaz;
   "canlı/testnet"-etiketi yalnız gerçek-bağlantıda; ölü-buton/ölü-form/
   anahtar-alanı konulmaz; "CANLI-bota-kopyala" dili paper-yönlü-yazılır.
3. **En büyük 3 değer-açığı** (motor-hazır/UI-yok): AA.7-backtest/OPT
   (sweep-uç-hazır), AA.14-karşılaştırma (B.4-hazır), AA.4-deal-tablosu
   (liste-ucu-gerekli — TEK kritik-yeni-backend).
4. **Claude'a backend-bağı listesi** (öncelikli): deal-listesi-ucu,
   portföy-toplam-ucu, indikatör-seri-uçları, kâr-serisi-ucu, ticker-24s-ucu,
   korelasyon-matris-ucu, sayısal-önizleme(avg/TP/SL)-ucu, WF/MC-uçları,
   plan-seviye-overlay-ucu, DD-ucu, toplu-liq-ucu. Tümü AA-bölümlerinde
   işaretli; hiçbiri bu-turda istenmedi (yalnız araştırma).
5. **Bağımsızlık beyanı**: `docs/ARASTIRMA_AA0_UX_CLAUDE.md`
   açılmadı/okunmadı; yukarıdaki VAR/KISMİ/YOK hükümleri yalnız bu-turda
   okunan kaynaklara dayanır. Sektör-kıyasları genel-ürün-bilgisidir.
