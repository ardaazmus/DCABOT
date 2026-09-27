# Faz 16 — Qwen Vizyon Haritası: DCABOT'un Ulaşması Gereken Nihai Görünüm

**Tarih:** 2026-09-21 · Arda'nın daha önce Qwen ile denediği (ve **yalnızca arayüz simülasyonu** olduğunu sonradan fark ettiği) bir tasarım çalışmasının 11 HTML iterasyonu + tam sohbet dökümü incelendi. Bu belge, o çalışmadaki **görsel dili ve etkileşim modelini** (`docs/qwen_referans/qwen-arayuz-final.html`) DCABOT'un **gerçek** backend'iyle birleştiren kesin bir uygulama planıdır. Önceki Faz 15 SVG wireframe'lerinden çok daha ayrıntılı ve doğru bir referans — bundan sonra **birincil görsel hedef budur**, 3Commas/Pionex/Bitsgap ekranları (docs/referans_ekranlar/) yalnız spesifik kontrol desenleri için ikincil kaynak kalır.

**Kritik çerçeve:** Qwen çalışması sahte veriyle **arayüz simülasyonu** yaptı (Arda: "aslında sadece arayüz simülasyonu yaptığını çok sonradan anladığım"). DCABOT'un farkı: aynı görsel dili **gerçek** backend'e (exact Fraction, fail-closed, gerçek dataset/backtest) bağlamak. Aşağıdaki her madde bunun için "qwen'de ne var → DCABOT'ta gerçek karşılığı ne → eylem" formatında.

---

## 0. Kaynak dosyalar
- `docs/qwen_referans/qwen-arayuz-final.html` — 11. (son, en olgun) iterasyon, tam çalışan HTML/Tailwind/vanilla-JS mockup.
- `docs/qwen_referans/kullanici_istekleri.txt` — Arda'nın o oturumda verdiği 52 isteğin ham kronolojik dökümü. Aşağıdaki gereksinimler doğrudan buradan alıntılanmıştır.

---

## 1. Arda'nın doğrudan, tekrar etmeyen talimatları (sohbetten alıntı, tartışmasız)

1. **"Bu botta temel eksiklik gerçek zamanlı tradingview benzeri... bir grafik. Bu Grafik Genel Bakışta, Bot oluştururken de botun parametrelerini kâr noktasını safety order'ların yerini, varsa liq seviyesini... online göstersin."** → Grafik yalnız fiyat göstermez; **botun kendi parametreleri (TP, her SO seviyesi, likidasyon varsa) grafiğin üzerine çizgi/marker olarak** işlenir. Bu, Genel Bakış + Bot Oluştur + Bot Detay + Deal Detay + Backtest sonucu — **hepsinde** geçerli.
2. **"bot kartları da tıklanabilir olmalı... tıklandığında botun durumunu gösteren bir istatistik sayfası ve yine tradingview benzeri... grafik olmalı."**
3. **"botlar ve aktif işlemlerde grafik ekranı popup açılmasın, ayrıntılı botun durumunu gösteren... ayrıntılı bir sayfa olsun."** → **Popup/modal YASAK**, tam sayfa detay görünümü şart (qwen'in `sec-botdetail`/`sec-dealdetail` deseni).
4. **"temel İndikatörlerin de seçimli olarak görünebilmesi gerekiyor tüm grafiklerde."** → İndikatör seçimi (SMA/EMA vb.) her grafikte tekrar eden bir bileşen.
5. **"veri kaynağı olarak Binance Public WebSocket, görselleştirme motoru olarak ise TradingView Lightweight Charts kütüphanesini kullanmanız en optimum çözüm... kullanalım."** → **Kesin teknoloji kararı, Arda tarafından verilmiş:** `lightweight-charts` (TradingView'ın kendi MIT lisanslı kütüphanesi) + Binance public WS. Bu artık öneri değil, talimat.
6. **"Canlı Piyasa verisi grafiği... farklı işlem çiftlerini görebilmek için... borsanın işlem çiftlerinin hepsini görebilmeliyim."** → Aranabilir, borsanın tüm paritelerini listeleyen sembol seçici (qwen'deki `marketPanel`/`mktSearch` deseni).
7. **"backtest motorunda eğer bir halüsinasyon oluşacaksa hesaplamalarında onları önleyecek kurallar eklersin."** → DCABOT bunu **zaten** çözmüş durumda (exact Fraction, fail-closed, `historical_run_contract.py`) — kalan iş bunu qwen'in "ANTİ-HALÜSİNASYON KURALLARI" kutusu gibi **kullanıcıya açıkça göstermek**.
8. **Veri kaynağı mimarisi sorusu** ("veriyi kendi bilgisayarımdan mı okutmak mantıklı") → DCABOT'un mevcut dataset-catalog + download-job + local-cache sistemi bu sorunun **zaten uygulanmış cevabı**.
9. **Modülerlik**: "backtest motoru, DCA stratejileri, Grid Stratejileri, Arbitraj stratejileri birbiri ile konuşur ama modüler kalması önemli, yeni stratejiler eklemek istediğimde bot sisteminin geneli değişmemeli." → DCABOT'un 158 application-modülü zaten bu felsefeyle yazılmış (bkz. `docs/ARASTIRMA_UI_TERMINOLOJI_I18N_FAZ12.md` §1 ölü-kod envanteri — çoğu "bilinçli, izole, henüz bağlanmamış modül") — kalan iş qwen'in "Çekirdek & Modül Mimarisi" ekranı gibi bunu **görünür kılmak**.

---

## 2. Görsel tasarım sistemi — qwen'den birebir alınacak tokenlar

DCABOT'un şu anki mavi-ağırlıklı paleti **değiştirilecek**. Qwen'in kullandığı, tutarlı ve olgun Tailwind semantik paleti:

| Rol | Renk | Kullanım |
|---|---|---|
| Zemin | `#06080d` (ink-950), `#0a0f18` (ink-900), `#0e1522` (ink-800) | body bg, sidebar, panel |
| **Marka/accent (YENİ — mavi yerine)** | amber `#fbbf24`/`#fcd34d` | aktif nav, birincil vurgular, slider thumb, progress bar |
| Pozitif/canlı | emerald `#34d399` | live-badge, kâr, "GERÇEK" rozetleri, başarı |
| Bilgi/ikincil aksiyon | cyan `#22d3ee`/`#67e8f9` | ikincil butonlar, indikatör vurguları, event bus |
| Negatif/tehlike | rose `#fb7185`/`#f43f5e` | kill-switch, zarar, likidasyon |
| Metin | slate ölçeği (`slate-100`→`slate-500`) | başlık→ikincil metin kademesi |
| Simülasyon/dikkat rozetleri | amber ton (`simbadge`) vs gerçek-veri rozetleri (`livebadge` emerald) | qwen'in kendi dürüstlük deseni — DCABOT için de gerekli (bkz. §5) |

**Fontlar (YENİ):** `Space Grotesk` (başlık/gövde) + `JetBrains Mono` (rakamlar/kod/kimlikler) — şu anki sistem fontu yerine. Her ikisi de Google Fonts/jsdelivr üzerinden ücretsiz, MIT/OFL lisanslı.

**Bileşen desenleri (qwen CSS'inden doğrudan taşınacak):** `.panel` (yarı-saydam koyu kart + blur + ince kenarlık), `.chip`/`.chipBtn` (pill), `.switch` (toggle, emerald "on" hali), `.fin` (koyu input, amber focus ring), grid-arka-plan dokusu (`bg-grid`, çok hafif amber çizgi deseni, radyal maske).

---

## 3. Bölüm haritası — qwen ekranı → DCABOT gerçek karşılığı → eylem

| Qwen bölümü | DCABOT'ta gerçek karşılığı | Eylem |
|---|---|---|
| **Durum & Veri Kaynağı** (sistem özeti, faz ilerleme halkası) | Yok (DCABOT'ta böyle bir "sistem durumu" dashboard'u yok) | YENİ: Genel Bakış'a sistem-durumu kartı (checker/gate durumu değil, kullanıcı-görünür "veri kaynağı: public WS bağlı" göstergesi) |
| **Genel Bakış** — 4 stat kart + canlı piyasa grafiği + sembol seçici + kâr grafiği + canlı akış + mini deals | Kısmen: `DashboardPanel`/`EventPanel` var ama ayrık; canlı grafik yok | **16.1**: gerçek `lightweight-charts` entegrasyonu + sembol seçici (tüm Binance public semboller) + mevcut dashboard verisini bu düzene taşı |
| **Botlarım** — tıklanabilir kartlar, şablon çipleri | `BotTable` (satır tabanlı, kart değil) | **16.2**: kart görünümüne çevir, tıklama → tam sayfa (popup değil) |
| **Bot Detay (tam sayfa)** — stats grid, sparkline, büyük grafik + parametre overlay, ayarlar grid, aktif deal listesi | `BotContextHeader`+`BotPanel` (küçük, "Klasik Görünüm"e taşınmış) | **16.3**: gerçek tam-sayfa route/görünüm; grafik üzerinde bot'un SO/TP seviyeleri çizgi olarak (`lightweight-charts` price-line API) |
| **Aktif İşlemler (Deals)** — tablo + Smart Trade Terminal | `DealPanel` (ham form, "Klasik Görünüm"de) | **16.4**: satır tıklama → tam sayfa deal detay (aynı grafik+overlay deseni) |
| **İşlem Detay (tam sayfa)** — chip-bar hızlı geçiş, seviyeler grid, Panic Sell/Fon Ekle | Yok | 16.4 kapsamında |
| **Bot Kur (DCA)** — canlı önizleme grafiği (form değiştikçe SO/TP/SL/likidasyon anında güncellenir), şablon çipleri | Faz 15'in Bot Oluştur akışı (form var, canlı grafik overlay yok) | **16.5**: mevcut Bot Oluştur formuna canlı parametre-overlay grafiği ekle (form `onChange` → chart price-line güncelleme, **hesap zaten backend'den geliyor, yalnız çizim eksik**) |
| **Faz 1 · Veri Pipeline** (parite panosu, doğrulama lab, indirme planı, kayıtlı depo) | **DCABOT'ta zaten gerçek ve daha olgun**: `DatasetCatalogPanel` + `download_jobs.py` + manifest/checksum doğrulama | Eylem yok — DCABOT burada qwen'den **ileride**; yalnız görsel dile taşınması yeterli (16.6, düşük öncelik) |
| **Faz 4 · Backtest Studio** (parametre formu, anti-halüsinasyon kutusu, equity eğrisi, fiyat+işlem noktaları, optimizasyon heatmap/walk-forward/Monte Carlo) | **DCABOT'ta zaten gerçek ve daha olgun**: `historical_simulation.py` + Faz 14'ün CPCV/PBO/DSR/sweep — qwen'de bunlar **kavramsal önizleme**, DCABOT'ta **gerçek** | **16.7**: backtest sonuç ekranını qwen'in equity-eğrisi + fiyat-üzerinde-işlem-noktaları düzenine taşı; "ANTİ-HALÜSİNASYON KURALLARI" kutusunu DCABOT'un gerçek kurallarıyla doldur (§5); heatmap'i Faz 14 sweep sonuçlarına bağla |
| **Gelişmiş Modüller / Çekirdek & Modül Mimarisi** (event bus görselleştirme, modül kayıt defteri) | Kısmen gerçek: 158 application modülü var ama görünmez | **16.8** (düşük öncelik): "hangi modüller bağlı/bağlanmamış" görünümü — §1 madde 9'daki ölü-kod envanterinin kullanıcı-dostu hali |
| **Bot AI / Copilot** | Yok, bilinçli DEFERRED (dış LLM kararı Arda'da) | Kapsam dışı — Arda'nın açık kararını bekliyor |
| **Risk Paneli** (circuit breaker slider, likidasyon motoru, korelasyon matrisi, funding tarayıcı) | Kısmen: `RiskPanel`/canary_policy var ama form'a bağlı değil (Faz 15.9 DEFERRED) | **16.9**: circuit-breaker slider'ı gerçek canary_policy'ye bağla (bu aynı zamanda canary_policy'nin "test-only" durumunu düzeltir, bkz. Faz 15 KARARLAR notu) |
| **Grid + Hybrid Engine** (fazlı akış görselleştirme) | Kısmen: `futures_grid_levels`+Küme B var, hibrit-faz konsepti yok | 16.10, düşük öncelik — ürün kararı gerektirir (DCA→Grid otomatik geçiş DCABOT'un şu anki kapsamında yok) |
| **Deployment** | Yok, DCABOT zaten offline-first/local çalışıyor (AGENTS.md P1-P3 sırası) | Kapsam dışı — qwen'in Docker/VPS senaryosu DCABOT'un mevcut mimari kararlarıyla çelişiyor (bkz. CLAUDE.md "offline-first tasarla") |

---

## 4. Öncelik sırası (somut dilimler)

**Kritik yol (Arda'nın en çok vurguladığı 3 madde, §1 madde 1-6):**
1. **16.1** — `lightweight-charts` entegrasyonu (mevcut `CandleChart.tsx`'in yerini alır, aynı `chart-data` sözleşmesini tüketir) + tüm-borsa sembol seçici.
2. **16.5** — Bot Oluştur formuna canlı parametre-overlay (SO seviyeleri + TP çizgisi backend'den zaten geliyor — `preview.levels`, yalnız grafiğe price-line olarak çizilmesi eksik).
3. **16.3/16.4** — Bot ve Deal için **tam sayfa** (popup değil) detay görünümü + aynı overlay deseni.

**İkinci dalga:**
4. **16.2** — Bot listesini kart görünümüne çevir.
5. **16.7** — Backtest sonuç ekranını qwen düzenine taşı + anti-halüsinasyon kutusu.
6. **16.9** — Risk paneli/circuit-breaker'ı gerçek canary_policy'ye bağla.

**Düşük öncelik / ürün kararı gerektiren:**
7. 16.6, 16.8, 16.10 — görsel taşıma, yeni karar gerektirmez ama acil değil.

**Kapsam dışı (bilinçli):** Bot AI/Copilot (dış LLM kararı bekliyor), Deployment/Docker senaryosu (offline-first mimariyle çelişiyor).

## 5. Anti-halüsinasyon kutusu — DCABOT'un gerçek karşılığı (16.7 için hazır metin)

Qwen'in kurgusal listesi yerine DCABOT'un **gerçek, test edilmiş** kuralları:
- ✓ Sonlu Decimal girdi + exact Fraction iç hesap (`numbers.py`) — hiçbir yerde float
- ✓ Fail-closed: UNKNOWN/eksik veri asla "başarı" sayılmaz
- ✓ Aynı ekonomik olay yalnız bir kez kaydedilir (idempotent attempt ledger)
- ✓ Look-ahead yok: `historical_simulation.py` yalnız kapalı bar kullanır
- ✓ Komisyon/slipaj modelde (`config.slippage`, fee_rate/fee_quantum)
- ✓ Nakit yetersizse güvenlik emri atlanır, bütçe aşımı yok (`account_reservation` ailesi)

Bu liste zaten `docs/ARASTIRMA_ILERI_BACKTEST_SINYAL_KALITE.md`'de dağınık halde var — 16.7'de tek bir görsel kutuya toplanacak.

---

## 6. Faz 17 — "3Commas'ın Ötesine Geçen Modüller" (qwen §2.4) + tam DCA parametre spesifikasyonu

**Hedef netliği (Arda, 2026-09-21):** Bu faz 3Commas/Bitsgap/Pionex'e *yetişmek* değil, hem borsa-doğruluğu (gerçek marj/likidasyon/emir semantiği) hem matematik/finans kurgusu (exact Fraction, fail-closed, kanıtlı istatistik) açısından onlardan **açıkça üstün** bir mimari kurmaktır. Aşağıdaki öncelik sırası bir **kapsam kısıtlaması değil, bağımlılık sırasıdır** — "kolay/hazır" olanlar önce çünkü araştırma raporu beklemiyor, "araştırma bekleyen"ler ise rapor geldikçe aynı derinlikte işlenecek; hiçbiri sadeleştirilerek/MVP'ye indirgenerek kapatılmayacak.

**Kural (Arda, tekrarlanan talimat):** qwen'deki bu liste bir **hedef/kontrol listesidir, matematiği değil**. Her satır için gerçek, sektörde kanıtlı yöntem DCABOT'un kendi mimarisiyle (exact Fraction, fail-closed, `data_adapters/` port-deseni) tasarlanır — qwen'in kodu kopyalanmaz. "Asla blocked etme" ilkesi gereği her modülün bir **güvenli/uygun yöntemi** var; yalnız 2 tanesi kendi isteğiyle (bkz. Arda'nın 2026-09-21 onayı) "şimdilik BLOCKED" statüsünde, ikisi de açık bir unblock-koşuluyla.

### 6.A — DCA parametre spesifikasyonu (qwen §2.1, 8 grup) — eksik alanlar

| Grup | Qwen alanı | DCABOT'ta durum | Güvenli/uygun yöntem |
|---|---|---|---|
| Sipariş Boyutları | Order Type (Market/Limit) | ❌ Yok — motor emri hep limit varsayıyor | `Config`'e `order_type` alanı; market emri mevcut `slippage` alanına uyarlanır, yeni kavram değil |
| Güvenlik Emirleri | Max ACTIVE Safety Orders (aynı anda açık SO sayısı, toplamdan ayrı) | ❌ Yok, yalnız toplam `safety_count` var | Yeni `max_active_safety_orders` alanı, varsayılan = `safety_count` (geriye uyumlu, davranış değişmez) |
| Ölçekleme | SO Deviation Reference (son SO'ya göre / ortalama girişe göre) | ⚠️ DCABOT 3. bir yöntem kullanıyor: anchor'dan kümülatif % (`math.py:75-81`) — 3Commas'ın gerçek varsayılanına qwen'in ikisinden daha yakın | Değiştirilmez; yalnız arayüzde "referans: giriş fiyatından kümülatif" diye açıkça etiketlenir |
| Giriş Sinyalleri | Conditional Start Price, Cool-down, Min/Max 24h Change Filter, çoklu koşul (VE/VEYA) | ❌ Faz 13.5 yalnız tek indikatör (SMA/EMA) destekliyor | `signal_native_indicators.py`'ye MACD/Bollinger/StochRSI (standart, kanıtlı formüller) + basit AND/OR koşul şeması |
| Kar Al | Partial TP, Reinvest Profit %, Trailing TP toggle | ⚠️ `take_profit` all-or-nothing; Trailing `ExitPanel`'de ayrı; Partial/Reinvest yok | Partial TP = `target_mode`'a kısmi-kapama %; Reinvest = sonraki deal'ın `initial_equity`'sini otomatik güncelleme |
| Zarar Kes | SL Timeout/Confirmation, Max Deal Duration | ❌ Yok | SL Timeout = Faz 13 replay-window desenine benzer bekleme penceresi; Max Deal Duration = basit zaman-aşımı alanı |
| Yön & Marjin | Margin Mode (Isolated/Cross), Direction (Long/Short/Bidirectional) | ❌ `Config` docstring'i "long-only" — çekirdek motorda Short yok | **En büyük gerçek boşluk.** Short = PnL işaretinin + SO tetikleyici yönünün tersine çevrilmesi; `engine.py`/`math.py`'ye dokunan gerçek çekirdek işi (yalnız Claude) — **17.7'de anonim araştırma raporu istenecek** |
| Bot Yönetimi | Max Active Deals, Profit Currency (çoklu para birimi) | ❌ `quote_asset` sabit `"USDT"` | Çoklu profit-currency = yeni doğrulama dalı; Max Deals = `bot_registry`'ye sayaç |

### 6.B — 11 modül (qwen §2.4) — durum ve DCABOT karşılığı

| # | Modül (qwen) | Qwen'in vaadi | Kanıtlı gerçek yöntem | Durum |
|---|---|---|---|---|
| 1 | Volatility-Adaptive DCA | SO sapması/TP, ATR'ye göre dinamik | ATR(14)/realized-vol ile `dev_dinamik = dev_baz × (ATR_şimdi/ATR_ref)` — exact Fraction'la yazılabilir | **17.1 — kolay, hazır** |
| 2 | Regime Detection & Auto-Switch | ADX/BB Width ile trend-range tespiti, Grid↔DCA otomatik geçiş | ADX + BB-Width eşiği ile rejim etiketle; **otomatik geçiş değil, öneri** (motor sözleşmesi sabit kalır) | **17.2 — orta, öneri-only sürüm** |
| 3 | Correlation-Aware Risk Manager | Yüksek korelasyonda toplam marjin otomatik kısıtlanır | Rolling Pearson korelasyon matrisi (float64, analytics-sınırı ilkesiyle — Faz 14 ile aynı), `account_reservation` ailesine bağlanan marjin tavanı | **17.3 — orta** |
| 4 | Anti-Liquidation Cascade | Kademeli kaldıraç düşürme, partial deleverage | Likidasyon fiyatı **kendimiz tahmin etmeyiz** (LCR-12 kararı korunur); **gerçek hesapta borsanın kendi bildirdiği `liquidationPrice`/`marginRatio`'sunu** (Binance position-risk endpoint) okuyup buna bağlı kademeli deleverage | **BLOCKED (Arda onaylı) — unblock koşulu: gerçek/testnet hesap bağlantısı + position-risk polling; testnet/paper'da dürüstçe boş kalır** |
| 5 | Whale Wall Detection | Orderbook duvarlarına göre SO/TP kaydırma | Binance depth-stream (`@depth`) ile ortalamanın N-katı emir kümesi eşik tespiti — **yeni veri kaynağı** (şu an yalnız trade/kline public stream var) | **17.5 — orta-büyük, yeni WS aboneliği gerektirir** |
| 6 | AI Parametre Önerici | Backtest + geçmişten öğrenen auto-tune | **Zaten var**: Faz 14 Optuna/sampler + sweep-orchestrator + Faz 15.7 "Optimize" düğmesi | **Zaten yapıldı — yalnız görünürlük/isimlendirme (17.6)** |
| 7 | Custom Strategy Scripting | Python DSL ile kendi giriş/çıkış mantığı | Tek-kullanıcılı yerel araç (çok-kullanıcılı SaaS tehdidi yok); kullanıcı modülü `engine.py`'nin `decision(State, Config)` imzasını uygulayarak `strategies/custom/`'a eklenir, aynı `historical_simulation`'dan geçer, sandbox gerekmez | **BLOCKED (Arda onaylı) — unblock koşulu: Arda'nın ayrı bir "yerel plugin API" ürün kararı** |
| 8 | Circuit Breaker / Kill-Switch | DD eşiğinde tüm botlar güvenli moda | **Zaten var**: `canary_policy.py`/`live_gate.py` (test-only) — kalan iş gerçek tetikleyiciye bağlamak | **Zaten yapıldı — 16.9'da bağlanacak** |
| 9 | Multi-Exchange Abstraction | Bybit/OKX plug-in | **Mimari zaten hazır**: `data_adapters/` port-deseni (`binance_testnet_*`, `binance_public_*`) | **P4'ün kendisi — yol haritasında zaten var, Arda'nın P4 kararını bekliyor** |
| 10 | Strategy Marketplace | Preset versiyonlama + A/B | **Kolay**: `TemplatePanel`'in `template_materialization`/config-hash'i zaten versiyonlu; A/B = iki config'i aynı dataset'te backtest edip yan yana koyma | **17.10 — kolay** |
| 11 | What-If Simülatörü | Parametre değişince 30/90 günlük anlık "ne olurdu" | `historical_simulation` zaten bunu yapıyor (~5sn bütçe) — eksik olan yalnız "form değişince debounce'lu otomatik tetikle" arayüz katmanı | **17.11 — kolay, 16.5 ile aynı temel** |

**Özet:** 7 modül (1,3,6,8,9,10,11) doğrudan/neredeyse doğrudan inşa edilebilir (3'ü zaten var, görünürlük meselesi). 2 modül (2,5) orta-büyük yeni iş (yeni veri akışı veya öneri-only ürün kararı). 2 modül (4,7) **Arda'nın kendi onayıyla** şimdilik BLOCKED — geçmişteki "asla blocked etme" ilkesine istisna, çünkü gerçek risk (yanlış likidasyon güveni / güvenlik yüzeyi) somut ve unblock-koşulu net.

### 6.C — Tam araştırma-talebi rosteri (Arda, 2026-09-21 talimatı — GÜNCEL, kapsayıcı)

**Arda'nın kesin talimatı:** *"Blocked olanları da yol haritasına al. Bizde olmayan HER özellik için anonim ama bizim sistemi hedefleyecek araştırma iste. Matematiğini, finansal doğruluğunu, borsa kurallarını ihlal edip etmediğini mutlaka test et."* Bu, önceki 6-konuluk listeyi genişletir: **BLOCKED durumundaki 2 modül de roadmap'tan çıkarılmaz**, kendi dilim numarasıyla haritada kalır ve unblock'u da bir araştırma raporuna bağlanır. Aşağıdaki roster, DCA-spec'in 7 gerçek boşluğu + modüllerin 5 araştırma-gerektiren kalemi olmak üzere **12 ayrı araştırma isteği**dir — her biri **ayrı, tek bir mesajda, sırayla** istenecek (toplu değil).

Her rapor için zorunlu **kabul kriterleri** (üçü de karşılanmadan hiçbir rapor uygulamaya alınmaz):
- **(M) Matematik uyumu:** önerilen formül/algoritma `Fraction`/exact-Decimal ile ifade edilebilir mi (float gerekiyorsa yalnızca izole `analytics/`-sınırı kuralına uyuyor mu — bkz. §5); köşe durumları (sıfıra bölme, negatif/aşırı değer) tanımlı mı.
- **(F) Finansal doğruluk:** önerilen mekanik gerçek piyasa/margin/PnL matematiğiyle tutarlı mı (bağımsız 2. kaynakla çapraz doğrulanabilir mi), DCABOT'un fail-closed ilkesini (UNKNOWN asla başarı sayılmaz) bozmuyor mu.
- **(B) Borsa kural uyumu:** Binance API rate-limit/ToS/izin (public vs. signed endpoint) kurallarını ihlal etmiyor mu; gerçek/testnet hesap gerektiren kısımlar açıkça ayrılmış mı (paper/backtest'te dürüst boş kalıyor mu).

| # | Dilim | Konu | Kaynak | Araştırma sorusu (özet) | Roadmap durumu |
|---|---|---|---|---|---|
| 1 | 17.7 | **Short/Bidirectional yön desteği** | 6.A, en büyük çekirdek boşluk | PnL işareti + SO tetikleyici yön mantığının tersine çevrilmesi, sektör-standart (3Commas/Pionex) uygulama detayları | **Faz 1 (matematik çekirdeği) TESLİM EDİLDİ, M/F/B PASS** — `Direction`/`signed_pnl`/`directional_take_profit`/`directional_stop_loss`/`directional_safety_price`/`is_safety_triggered` (`domain/math.py`), 14 test. Kalan: Config alanı, Position/build_plan SHORT desteği, engine.py bağlama, adapter capability, bidirectional concurrency — bkz. `evidence/F17.7/SONUC.md` |
| 2 | 17.4 | **Anti-Liquidation Cascade unblock** (modül 4) | 6.B #4 | Binance USDS-M `positionRisk`/`marginRatio` gerçek semantiği, kademeli deleverage eşik pratikleri | **BLOCKED ama haritada** — rapor unblock koşulunu karşılarsa 17.4 açılır |
| 3 | 17.5 | **Whale Wall Detection** (modül 5) | 6.B #5 | Depth-stream (`@depth`) işleme, gürültü/anomali eşiği belirleme yöntemleri | Araştırma bekliyor |
| 4 | 17.2 | **Regime Detection & Auto-Switch** (modül 2) | 6.B #2 | ADX/BB-Width eşik kalibrasyonu, yanlış-pozitif oranı sektör verisi | Araştırma bekliyor |
| 5 | 17.3 | **Correlation-Aware Risk Manager** (modül 3) | 6.B #3 | Rolling korelasyon penceresi seçimi, marjin-tavanı formülü örnekleri | Araştırma bekliyor |
| 6 | 17.12 | **Margin Mode (Isolated/Cross)** | 6.A | Mevcut `isolated_liquidation`/LCR-12 kararıyla motor+UI bütünleşmesi | Araştırma bekliyor |
| 7 | 17.13 | **Order Type (Market/Limit)** | 6.A | Market emrinin exact-Fraction slipaj modeline (mevcut `slippage` alanı) doğru uyarlanması, gerçek Binance emir-tipi kısıtları | Araştırma bekliyor |
| 8 | 17.14 | **Max Active Safety Orders** | 6.A | Toplam vs. eşzamanlı-açık SO ayrımının motor sözleşmesine geriye-uyumlu eklenmesi | Araştırma bekliyor |
| 9 | 17.15 | **Çoklu giriş-sinyali koşulu (VE/VEYA) + MACD/Bollinger/StochRSI** | 6.A | Standart indikatör formüllerinin exact/float-analytics sınırında doğru yazımı, koşul-kombinasyon şemasının motor sözleşmesine etkisi | Araştırma bekliyor |
| 10 | 17.16 | **Partial TP + Reinvest Profit %** | 6.A | Kısmi kapama muhasebesi (kalan pozisyon/ortalama maliyet exact yeniden hesabı), reinvest'in `initial_equity` zincirine etkisi | Araştırma bekliyor |
| 11 | 17.17 | **SL Timeout/Confirmation + Max Deal Duration** | 6.A | Yanlış-tetikleme önleme penceresinin (Faz 13 replay-window benzeri) doğru parametrelenmesi | Araştırma bekliyor |
| 12 | 17.18 | **Profit Currency (çoklu para birimi) + Max Active Deals** | 6.A | `quote_asset` sabitinin kaldırılmasının doğrulama/muhasebe zincirine etkisi, borsa-bazlı desteklenen quote listesi | Araştırma bekliyor |

**Araştırma gerektirmeyen, doğrudan uygulanabilir kalemler** (zaten net/kanıtlı veya zaten var — 17.1 Volatility-DCA, 17.6 AI Önerici görünürlüğü, 17.8 Circuit-Breaker bağlama, 17.9 P4/Multi-Exchange, 17.10 Marketplace, 17.11 What-If, 17.19 modül 7 Custom Scripting'in yerel-plugin iskeleti) — bunlar da roadmap'ta, ama araştırma sırasını beklemeden başlanabilir. **Modül 7 (Custom Scripting) BLOCKED kalır** ama iskelet/arayüz tasarımı Arda'nın ayrı "yerel plugin API" onayına kadar haritada bekler — kaldırılmadı.

### 6.D — Öncelik sırası (bağımlılık sırası, kapsam kısıtlaması DEĞİL)

**Hemen başlanabilir (araştırma raporu gerektirmez):** 17.1, 17.6, 17.8, 17.9 (P4 kararını beklerken iskelet), 17.10, 17.11, 17.19 (iskelet) + tüm görsel/animasyon paritesi (§2, §7).
**Araştırma raporu sırayla istenecek (12 rapor, §6.C tablosundaki sırayla, her biri M/F/B kriterleriyle test edilip onaylandıktan sonra uygulamaya alınır):** 17.7 → 17.4 → 17.5 → 17.2 → 17.3 → 17.12 → 17.13 → 17.14 → 17.15 → 17.16 → 17.17 → 17.18.
**Ürün kararı bekleyen (Arda, ayrı):** 17.7'nin canlı motora ne zaman alınacağı (yalnız backtest mi, gerçek emir de mi), modül 7'nin (17.19) nihai onayı, P4 borsa kapsamı.

**Hiçbir kalem bu listeden çıkarılmaz veya sadeleştirilmez** — BLOCKED (17.4, 17.19) dahil hepsi haritada kalıcı, yalnız sırası bağımlılığa göre değişir.

---

## 7. Kalıcı karar — eski arayüze asla dönülmez

**2026-09-21, Arda onayı:** Faz 16/17'nin qwen görsel dili (§2 renk/font/bileşen tokenları, animasyonlar dahil) DCABOT'un **nihai ve tek** hedef arayüzüdür. Faz 15 ve öncesi mavi-ağırlıklı/eski panel görünümüne **bir daha dönülmeyecek** — bu bir öneri değil, kalıcı mimari karardır. Yeni bir oturum/ajan bu dosyayı okuduğunda: (1) §2'deki renk paletini uygula, (2) eski `.builder-panel`/mavi-accent kalıntılarını qwen tokenlarıyla değiştir, (3) hiçbir gerekçeyle Faz 15-öncesi görsel düzene geri dönme. Ayrıntı: `docs/KARARLAR.md` (2026-09-21 kaydı).

---

## 8. Nihai uygulama yol haritası — muse'a devir (12/12 araştırma turu tamamlandı, 2026-09-22)

Bu bölüm, 12 anonim araştırma raporunun (§6.C) tamamı toplanıp M/F/B doğrulaması bitirildikten sonra yazılan **tek, nihai** hiyerarşidir (Arda: "sıralamalar değişecektir ana planı hemen yazma en son tüm raporları analiz et" — bu talimata uyulmuştur, sıralama önceki ayrı-ayrı taslaklardan burada revize edildi). **Bu yol haritasını Claude değil, muse (dış ajan) yürütecektir.** Bu yüzden yapı bilinçli olarak "en küçük anlamlı dilim → test → kalite kontrolü → kabul kapısı" granülaritesindedir; her **büyük faz** kapanışında **duraksız ilerleme YASAK** — build + ~5 dakika çalıştırıp gözlemleme + Arda'ya "devam edeyim mi yoksa eklenecek bir not var mı?" sorusu **zorunlu insan kapısıdır**.

### 8.0 — Araştırma kapıları (research gates) — kaynak envanteri

Her büyük fazın altında, o fazın dayandığı kaynaklar "Araştırma kapısı:" satırıyla adlandırılır. Tam envanter:

| Kod | Kaynak | Konum |
|---|---|---|
| RG-01..12 | 12 anonim araştırma raporu (3'er bağımsız ajan × 12 konu = 36 dosya) + M/F/B sentezleri | `docs/KARARLAR.md` — her biri "Faz 17 konu N/12 ... raporları değerlendirildi" başlıklı, tarihli (2026-09-21/22) kayıt |
| RG-QWEN-CHAT | Arda'nın qwen ile tam sohbet dökümü (55 mesaj, 22 HTML artifact) — `kullanici_istekleri.txt` bunun ÖZETİdir, birebir değil | `docs/qwen_referans/qwen-sohbet-export.json` (ham export) + `docs/qwen_referans/kullanici_istekleri.txt` (özet) |
| RG-QWEN-HTML | **DÜZELTME (2026-09-22):** Qwen'in 22 HTML iterasyonu (önceden yalnız "final" adlı #13 kullanılıyordu — en olgun/en büyük değildi). Birincil referans artık **#14** (#13 ile aynı 15 `sec-*` bölüm ama daha zengin optimizasyon ekranı); #17/#18/#21-22 ise 15'in DIŞINDA yeni ekranlar (Strateji Lab, Testnet Console, Mission Control) tanıtıyor. Tam indeks + hangi dilimde hangi iterasyona bakılacağı: | `docs/qwen_referans/ITERASYONLAR_INDEKSI.md`, dosyalar `docs/qwen_referans/iterasyonlar/` |
| RG-F17.7 | Direction/signed-math çekirdeği — teslim edilen kod + kanıt | `evidence/F17.7/SONUC.md`, `src/dcabot/domain/math.py`, `tests/test_directional_math.py` |

**Kural (muse için bağlayıcı):** Her küçük dilime başlamadan önce ilgili RG kodunun kaynağı **gerçekten açılıp okunur** — tahmin edilmez. Bir dilimin kabul kriteri, o dilimin RG kaynağındaki M/F/B sonucuyla çelişmemesidir.

### 8.1 — Qwen-kökenli özelliklerin finansal risk tablosu (Arda'nın görmek istediği, kalıcı görünür artefakt)

| Modül | Risk sınıfı | Somut risk | Yerleşim | Kullanım-anı uyarısı (UI'da zorunlu) |
|---|---|---|---|---|
| Anti-Liquidation Cascade (#4) | **Yüksek (yanlış güven)** | Tahmini likidasyon yanlışsa kullanıcı gerçek likidasyona güvenip kaybeder | **Ana motor**, ama yalnız gerçek/testnet hesap bağlıyken aktif; veri **daima borsadan** (`positionRisk`), asla yerel tahmin değil | "Bu değer borsanın anlık raporudur, hızlı çöküş/pump anlarında güncellik garantisi düşer" — bot kartında sabit, silinemez not |
| Whale Wall Detection (#5) | **Orta (borsa yorma/ban)** | Yüksek frekanslı `@depth` polling rate-limit/ban riski taşır | **Lab** | "Bu özellik ek borsa isteği yapar, hesabınızın rate-limit'ini kullanır" — Lab girişinde tek seferlik onay |
| Regime Detection & Auto-Switch (#2) | **Düşük-Orta (yanlış sinyal)** | ADX/BB-Width yanlış-pozitif → yanlış zamanlı strateji önerisi | **Ana motor**, ama **öneri-only** (otomatik geçiş yok) | "Öneridir, otomatik uygulanmaz" |
| Correlation-Aware Risk Manager (#3) | **Orta (kısıtlama yanlışlığı)** | Yanlış korelasyon penceresi → marjin tavanı ya fazla gevşek ya fazla sıkı | **Ana motor**, `analytics/` float-sınırı içinde | Marjin-tavanı önerisi "tahmini" etiketiyle gösterilir |
| Custom Strategy Scripting (#7) | **Orta (güvenlik yüzeyi)** | Kullanıcı kodu motora bağlanırsa hatalı/kötü niyetli kod riski | **BLOCKED**, ayrı ürün kararına kadar hiçbir yere yerleşmez | — |
| Partial TP + Reinvest % | **Düşük-Orta (bileşik risk)** | Reinvest zinciri yanlış kurulursa `initial_equity` sürüklenir | Ana motor | Reinvest aktifken "bir sonraki deal'ın sermayesi bu kârdan büyür/küçülür" açık gösterim |
| Profit Currency = Base | **Yüksek (belgelenmiş, gerçek kullanıcı kaybı — 2021-22 ayı piyasası)** | Kâr düşük hacimli altcoin'de birikip değer kaybeder | Ana motor (özellik kalır) | "Base kâr seçtiniz: bu coin'e uzun vadeli güveniyor olmalısınız" — zorunlu tek-seferlik onay checkbox'ı |
| Margin Mode = Cross | **Orta (kapsam genişlemesi)** | Cross modda bir pozisyonun zararı diğerlerinin marjinini yer — LCR-12 ile birlikte okunmalı | Ana motor, UI'da Isolated varsayılan | "Cross modda bu botun zararı hesabınızdaki diğer pozisyonları etkileyebilir" |

**İlke (Arda, 2026-09-22):** Qwen'den gelen ek özellikler **kaldırılmaz**, ama (a) finansal riski somut olanlar için kullanım-anında sade/doğru uyarı zorunlu, (b) borsayı yoracak/ban riski taşıyanlar **Lab**'a taşınır ve tasarım gereği borsa limitlerinin altında hız sınırlanır.

### 8.2 — "Lab" bölümü — tasarım ilkesi

- **Tanım:** Ana motorun (canlı emir/risk kararı zinciri) dışında, ekstra veri/insight üreten ama borsayı normalden fazla yoran (yüksek frekans polling, geniş depth-stream aboneliği vb.) özelliklerin yaşadığı ayrı ürün alanı.
- **Rate-limit-aware throttling, baştan tasarım gereği:** Lab'daki her veri kaynağı, Binance'in ilan edilmiş ağırlık limitlerinin (`X-MBX-USED-WEIGHT-1M` header'ı okunarak, sabit sayı varsayılmadan) **altında** sabit bir tavan ile çalışır; tavan kod-seviyesinde merkezi bir `lab_rate_budget.py` (yeni, izole modül) üzerinden paylaşılır — Lab'daki hiçbir özellik bu bütçeyi tek başına aşamaz.
- **Kullanım disiplini:** Lab özelliği açıldığında kullanıcıya tek satırlık, doğru risk notu gösterilir (8.1 tablosundaki "Kullanım-anı uyarısı"); teknik jargon yok.
- **İlk sakini:** Whale Wall Detection (17.5). Gelecekte borsa-yoran her yeni özellik varsayılan olarak önce Lab'a girer, yalnız Arda'nın açık kararıyla ana motora taşınır.

### 8.3 — Anti-Liquidation Cascade — UI gereksinimi (Arda, 2026-09-22, bağlayıcı)

Likidasyon fiyatını DCABOT **asla kendi hesaplamaz** (LCR-12, değişmez). Ama gerçek/testnet hesap bağlandığında borsanın **kendi raporladığı** `positionRisk.liquidationPrice`/`marginRatio` verisi **zaten mevcuttur** — bu veri artık pasif değil, **aktif botun kartında canlı gösterilir**:
1. Bot kartı (Genel Bakış + Bot Detay tam sayfa) üzerinde likidasyon mesafesi/oranı alanı — kaynağı her zaman `GET /fapi/v2/positionRisk` (veya eşdeğer), asla yerel türetme.
2. **Değişkenlik açıkça iletilir:** sabit bir küçük not/ikon — "Bu değer borsanın anlık raporudur, sabit değildir."
3. **Hızlı çöküş/pump uyarısı, özellikle vurgulanır:** fiyat hareketi son N saniyede eşik üstü hızlıysa (basit bir `|Δprice/Δt|` eşiği, exact Fraction) kart üzerinde "hızlı hareket sırasında bu veri daha az güvenilir olabilir" notu **belirgin** hale gelir (renk/ikon değişimi, emerald→amber gibi — sabit kırmızı alarm değil, çünkü veri hâlâ borsadan geliyor, yalnız güncellik riski artıyor).
4. Paper/testnet'te gerçek position-risk yoksa alan **dürüstçe boş/"veri yok"** kalır — asla tahmini sayı üretilmez (fail-closed, LCR-12 ile tutarlı).

### 8.4 — Local-first backtest mimarisi (kalıcı sistem ilkesi)

Arda'nın vurgusu: qwen'in "indirilebilir geçmiş veriyi sunucuyu yormadan yerel makinede çalıştırma" fikri doğru yön. DCABOT'ta bu **zaten** kısmen var (dataset-catalog + local-cache, §1 madde 8) — Faz 17 kapsamında pekiştirilecek ilkeler:
- Backtest/sweep/CPCV-PBO-DSR (Faz 14) çalıştırmaları **varsayılan olarak kullanıcının kendi makinesinde** yürütülür; sunucu yalnız veri kataloğu/manifest sağlar, hesaplama yapmaz.
- Sunucu tarafı backtest yalnız gelecekte ihtiyaç doğarsa (ör. paylaşımlı/uzaktan erişim senaryosu) eklenir; o zaman bile **iş kuyruğu + kullanıcı başına kota** ile sunucu maliyeti sınırlanır — bu, şimdiden `docs/KARARLAR.md`'ye ileriye-dönük not olarak düşülür, kod yazılmaz (YAGNI, henüz talep yok).
- Bu ilke yeni bir dilim numarası almaz; 16.1/16.7 ve Faz 14 kalıntılarının üzerine "yerelde çalıştır" varsayılanının korunduğunu doğrulayan bir kabul-kriteri satırı olarak her ilgili dilime eklenir (bkz. 8.6, BÜYÜK FAZ J).

### 8.5 — TradingView ücretsiz API'nin ileri kullanımı

Qwen'in önerisinin ötesinde, DCABOT'un kendi teknik değerlendirmesi: TradingView'ın ücretsiz `lightweight-charts` kütüphanesi zaten Arda'nın kesin kararı (§1 madde 5). Ek olarak (araştırma gerektirmez, mühendislik kararı):
- Sembol/parite arama ve temel OHLCV için TradingView'ın herkese açık, kimlik doğrulamasız `symbol_search`/`history` uçları **yalnız görüntüleme amaçlı** (asla emir/hesap kararı) ikincil kaynak olarak değerlendirilebilir — birincil kaynak yine Binance public WS/REST kalır (borsa-doğruluğu ilkesi).
- Bu, BÜYÜK FAZ J'de 16.1'in bir alt-notu olarak ele alınır; ayrı araştırma raporu gerektirmez çünkü yalnız görsel/keşif katmanına dokunur, ekonomik karara dokunmaz.

### 8.6 — Büyük fazlar (muse'un yürüteceği sıra, her biri kapılı küçük dilimlerden oluşur)

**Ortak kabul şablonu (her küçük dilim için, muse zorunlu uygular):**
`[Dilim adı] → Kaynak (RG kodu) → Uygulama → Test (unit + ilgiliyse checker/gate) → Kalite kontrolü (M/F/B ilgiliyse, değilse "kod inceleme + regresyon-sıfır" kanıtı) → Kabul kriteri (somut, ölçülebilir) → docs/KARARLAR.md'ye tek satır kayıt.`

---

**BÜYÜK FAZ A — Görsel taşıma çekirdeği (qwen görsel dili + gerçek grafik)**
Araştırma kapısı: RG-QWEN-CHAT, RG-QWEN-HTML.
- A.1 (=16.1) `lightweight-charts` entegrasyonu + Binance public WS sembol seçici — kabul: mevcut `chart-data` sözleşmesi bozulmadan grafik gerçek veriyle çiziliyor, checker+vitest yeşil.
- A.2 (=2, §2 token geçişi) Renk/font/bileşen tokenlarının (`styles.css`) qwen paletine taşınması — kabul: hiçbir ham hex kalmıyor, `data-theme` çalışıyor.
- A.3 (=16.5) Bot Oluştur formuna canlı parametre-overlay — kabul: form `onChange` → price-line güncelleme, backend hesabı değişmiyor (yalnız çizim).
- A.4 (=16.3/16.4) Bot ve Deal tam sayfa detay (popup YASAK) + overlay deseni — kabul: popup/modal hiçbir yerde kullanılmıyor (grep ile doğrulanır).
- A.5 (=16.2) Bot listesi kart görünümü.
**Kapanış kapısı A:** `tools/run_checks.py` + frontend testleri tam yeşil, build alınır, uygulama ~5 dakika elle gezilir (Genel Bakış→Bot Oluştur→Bot Detay→Deal Detay). **Ardından Arda'ya sor: "devam edeyim mi yoksa eklenecek bir not var mı?" — onay gelmeden BÜYÜK FAZ B'ye geçilmez.**

---

**BÜYÜK FAZ B — Araştırma gerektirmeyen Faz 17 kalemleri**
Araştırma kapısı: yok (zaten var/kanıtlı, §6.D "hemen başlanabilir" listesi).
- B.1 (=17.1) Volatility-Adaptive DCA (ATR-bazlı dinamik sapma).
- B.2 (=17.6) AI Önerici görünürlüğü (Faz 14 sweep/Optuna'yı kullanıcıya adlandırıp göster).
- B.3 (=17.8) Circuit-Breaker/`canary_policy`'yi gerçek tetikleyiciye bağlama (=16.9 ile aynı iş).
- B.4 (=17.10) Strategy Marketplace/preset A-B karşılaştırma.
- B.5 (=17.11) What-If simülatörü (debounce'lu otomatik backtest tetikleme, =16.5 ile aynı temel).
- B.6 (=17.9 iskelet) Multi-Exchange: mevcut `data_adapters/` port-deseninin dokümante edilmesi, yeni borsa eklenmeden (P4 Arda kararını bekler).
- B.7 (=17.19 iskelet) Custom Strategy Scripting **arayüz/iskelet tasarımı** — kod bağlanmaz, yalnız `strategies/custom/` dizin sözleşmesi ve `decision(State, Config)` imza dokümantasyonu (BLOCKED kalır, yalnız hazırlık).
**Kapanış kapısı B:** build + 5 dk gözlem + Arda'ya sor.

---

**BÜYÜK FAZ C — Direction/Short-Bidirectional'ın tamamlanması**
Araştırma kapısı: RG-01 (17.7), RG-F17.7 (zaten teslim edilen matematik çekirdeği).
- C.1 `Config`'e `direction` alanı (varsayılan `LONG`, geriye uyumlu).
- C.2 `Position`/`build_plan`'e SHORT desteği (Direction enum ile, `math.py`'deki `signed_pnl`/`directional_*` fonksiyonlarını kullanarak).
- C.3 `engine.py` bağlama — sinyal/karar akışının yön-farkında hale gelmesi.
- C.4 Exchange adapter capability matrisi (hangi borsa/mod SHORT destekliyor, `data_adapters/` içinde açık bayrak).
- C.5 Bidirectional concurrency kararı (aynı paritede eşzamanlı LONG+SHORT deal — yalnız RG-01'in izin verdiği kapsamda).
**Kapanış kapısı C:** `tests/test_directional_math.py` + yeni entegrasyon testleri yeşil, checker regresyon-sıfır, build + 5 dk gözlem + Arda'ya sor.

---

**BÜYÜK FAZ D — Anti-Liquidation Cascade (gerçek/testnet hesap bağımlı)**
Araştırma kapısı: RG-02 (17.4, BLOCKED→unblock).
**Ön koşul (dilim değil, kapı):** Gerçek veya testnet hesap bağlantısı zaten kurulu olmalı (Faz 3 `p2-testnet-complete` kapsamında). Bu sağlanmadan D.1'e başlanmaz.
- D.1 `positionRisk`/`marginRatio` polling — rate-limit-aware (8.2 ilkesiyle, ama bu ana motorda olduğu için Lab bütçesine değil kendi ayrı, düşük-frekans bütçesine tabi).
- D.2 Bot kartı UI — 8.3'teki 4 gereksinim birebir (canlı gösterim, değişkenlik notu, hızlı-hareket uyarısı, paper'da dürüst boş).
- D.3 Kademeli deleverage eşiği (RG-02'nin unblock koşulunu karşılayan kısmı; koşulu karşılamıyorsa bu dilim BLOCKED kalır, D.1/D.2 yine de teslim edilir).
**Kapanış kapısı D:** testnet hesapla gerçek `positionRisk` verisi UI'da görünüyor mu (manuel doğrulama), fail-closed davranış (paper'da boş) test edildi mi, build + 5 dk gözlem + Arda'ya sor.

---

**BÜYÜK FAZ E — Lab altyapısı + Whale Wall Detection**
Araştırma kapısı: RG-03 (17.5).
- E.1 `lab_rate_budget.py` — merkezi, izole rate-limit bütçe modülü (8.2).
- E.2 Lab bölümü UI iskeleti (ana nav'dan ayrı, risk-uyarı deseni ile).
- E.3 Whale Wall Detection — `@depth` stream + eşik tespiti, E.1 bütçesine bağlı.
**Kapanış kapısı E:** Lab açıkken gerçek/testnet ortamda rate-limit header'ları izlenip bütçenin aşılmadığı kanıtlanır (log/ekran görüntüsü), build + 5 dk gözlem + Arda'ya sor.

---

**BÜYÜK FAZ F — Regime Detection + Correlation-Aware Risk Manager**
Araştırma kapısı: RG-04 (17.2), RG-05 (17.3).
- F.1 ADX/BB-Width rejim etiketleme — öneri-only (otomatik geçiş yok).
- F.2 Rolling korelasyon matrisi (`analytics/` float-sınırı içinde, Faz 14 ile aynı izolasyon deseni) + `account_reservation` marjin-tavanı önerisi.
**Kapanış kapısı F:** M/F/B ilgili raporla çelişmiyor, float hiçbir yerde exact ledger'a sızmıyor (kod inceleme kanıtı), build + 5 dk gözlem + Arda'ya sor.

---

**BÜYÜK FAZ G — DCA-spec parametre genişletmesi I**
Araştırma kapısı: RG-06 (Margin Mode), RG-07 (Order Type), RG-08 (Max Active SO), RG-09 (çoklu-sinyal).
- G.1 Margin Mode (Isolated/Cross) — UI+motor, LCR-12 ile tutarlı, Cross seçilince 8.1'deki uyarı.
- G.2 Order Type (Market/Limit) — mevcut `slippage` alanına uyarlama.
- G.3 Max Active Safety Orders — yeni alan, varsayılan = mevcut `safety_count` (geriye uyumlu).
- G.4 Çoklu giriş-sinyali (VE/VEYA) + MACD/Bollinger/StochRSI — **Fraction digit-growth bulgusu uygulanır**: bu indikatörler ham `Fraction` değil, sabit-nokta tamsayı veya adım-başı `Decimal` ile yazılır (RG-09'un kritik bulgusu).
**Kapanış kapısı G:** her alt-dilim kendi M/F/B'siyle PASS, checker regresyon-sıfır, build + 5 dk gözlem + Arda'ya sor.

---

**BÜYÜK FAZ H — DCA-spec parametre genişletmesi II**
Araştırma kapısı: RG-10 (Partial TP+Reinvest), RG-11 (SL Timeout+Max Deal Duration).
- H.1 Partial TP — `Position.sell()`'in zaten desteklediği qty-parametreli kısmi kapama (bkz. F17.7 doğrulaması) UI/Config'e bağlanır.
- H.2 Reinvest Profit % — sonraki deal'ın `initial_equity`'sini otomatik güncelleme, 8.1'deki şeffaflık gereksinimiyle.
- H.3 SL Timeout/Confirmation — Faz 13 replay-window desenine benzer bekleme penceresi.
- H.4 Max Deal Duration — basit zaman-aşımı alanı.
**Kapanış kapısı H:** build + 5 dk gözlem + Arda'ya sor.

---

**BÜYÜK FAZ I — Profit Currency (çoklu kur) + Max Active Deals**
Araştırma kapısı: RG-12 (17.18) — **en büyük, çok-dosyalı dilim, KARARLAR.md 2026-09-22 kaydında "ayrı onayla başlanacak" olarak işaretli.**
**Ön koşul (kapı):** Bu büyük faza başlamadan önce Arda'nın ayrı, açık "başla" onayı — çünkü `Config.parse`'ın statik→dinamik borsa-metadata doğrulamasına geçmesi ve muhasebe defterinin `Dict[asset, Fraction]`'a genişlemesi mimari bir kırılma noktasıdır.
- I.1 Üç-katmanlı model: `quote_asset` (fon) / `profit_asset` (realize kâr, quote veya base) / raporlama-kuru (yalnız gösterim) — asla üçüncü rastgele bir coin'e dönüşüm yok.
- I.2 Dinamik quote-listesi doğrulama (`exchangeInfo` tabanlı, Freqtrade'in statik-whitelist hatasından kaçınarak).
- I.3 Base-kâr yuvarlama yönü düzeltmesi (yukarı yuvarlama, RG-12'nin inceliği) + 8.1'deki "Base kâr" zorunlu onay checkbox'ı.
- I.4 Max Active Deals — bot-bazlı + hesap-bazlı (global) limit, **kuyruk yok, reddet/logla** (`Ignored: max_active_deals_reached`).
**Kapanış kapısı I:** M/F/B PASS (RG-12 ile birebir), fee-asset-farklı (BNB dust) senaryosu test edilir, build + 5 dk gözlem + Arda'ya sor.

---

**BÜYÜK FAZ J — Sistem ilkelerinin pekiştirilmesi (backtest yerellik + TradingView ileri kullanım + sunucu maliyet notu)**
Araştırma kapısı: yok (mühendislik kararı, §8.4/8.5).
- J.1 Backtest/sweep'in varsayılan yerel-çalışma davranışının doğrulanması (mevcut mimari zaten böyle — bu dilim yalnız açık bir kabul testi ekler: sunucu backtest sırasında ağır hesap yapmıyor).
- J.2 TradingView public sembol-arama/OHLCV'nin yalnız görüntüleme katmanında, ikincil kaynak olarak değerlendirilmesi (opsiyonel, düşük öncelik).
- J.3 Sunucu maliyet-optimizasyon notunun `docs/KARARLAR.md`'ye ileriye-dönük madde olarak düşülmesi (kod yazılmaz, YAGNI).
**Kapanış kapısı J:** build + 5 dk gözlem + Arda'ya sor.

---

**BÜYÜK FAZ AA — Qwen ekran-birebir uyum denetimi + düzeltme (2026-09-22 eklendi, 2026-09-22'de J'nin sonrasına taşındı; Faz 17'nin gerçek son büyük fazı)**

**Sıralama kararı (Arda, 2026-09-22, bağlayıcı):** Önce backend (B'nin kalanı + C-J, qwen'den kabul edilen tüm motor/arka-uç özellikleri), sonra UI/UX. Gerekçe: AA, ekranları qwen'in nesne dizilimine göre yeniden kurarken o ekranların bazıları (Risk Paneli'nin korelasyon/funding alanları, Bot Kur'un Margin Mode/Order Type/çoklu-sinyal alanları, Genel Bakış'ın bazı kartları vb.) F/G/H/I fazlarının backend'ine bağımlı. Backend önce bitmezse UI o alanları "yakında" ile doldurup sonra tekrar açılıp gerçek veriye bağlanmak zorunda kalır — çifte iş. **Bu yüzden AA, J'den SONRAYA taşındı: A (kapalı) → B (devam) → C → D → E → F → G → H → I → J → AA.** BÜYÜK FAZ B, B.3'te durdurulmuştu (bu kararla) — **şimdi devam ediyor**: B.4-motor + B.5 (HELD, kapatılacak) + B.6 + B.7.

**Arda'nın nesne-birebir netleştirmesi (değişmedi, 2026-09-22, bağlayıcı):** Faz 16/17'nin "qwen görsel dili" kararı yalnız renk/font/animasyon değildi — **qwen HTML'indeki (`docs/qwen_referans/qwen-arayuz-final.html`) her ekranın her nesnesi (kart, grid, buton, panel yerleşimi, sıralama) birebir yansıtılacak**, tıpkı 3Commas/Pionex/Bitsgap referans ekranları gibi bağlayıcı bir ürün tasarımı olarak. Yalnız matematik/finans/backend DCABOT'un kendisi kalır; qwen'de olup DCABOT backend'inde karşılığı olmayan bir öğe **uydurulmaz**, dürüstçe boş/"veri yok"/devre-dışı gösterilir. BÜYÜK FAZ A bu ölçüde denetlenmeden kapatılmıştı — AA o boşluğu, **artık tüm backend hazırken**, tek seferde kapatır.

**Kaynak notu (düzeltildi, 2026-09-22):** Downloads'taki diğer `Qwen_html_*`/`Qwen LumaForge`/`qwen_lumaforge_*` dosyaları kontrol edildi — bunlar **DCABOT'la ilgisiz, farklı bir projeye ait** ("VitrinAI" + "LumaForge", yalnız "Qwen" aracı ortak). Ama tam sohbet dökümü (`qwen-sohbet-export.json`) taranınca DCABOT'un kendi qwen oturumunda **22 HTML iterasyonu** bulundu — `qwen-arayuz-final.html` bunların yalnız 13.'sü, en olgunu değil. Gerçek en-zengin sürüm #14 + 3 yeni ekran (AA.13-15). Tam indeks: `docs/qwen_referans/ITERASYONLAR_INDEKSI.md`.

Araştırma kapısı: RG-QWEN-HTML — birincil kaynak `docs/qwen_referans/iterasyonlar/14_1787388842.html` (#13/`qwen-arayuz-final.html` değil; #14 aynı 15 `sec-*` bölümün daha zengin/daha gelişmiş sürümü — optimizasyon ilerleme çubuğu+ısı haritası+mission-control istatistikleri ekli).

**AA başlamadan hemen önceki ek adım (Arda, 2026-09-22, bağlayıcı):** qwen'in nesne dizilimi/HTML'i AA için **taban/minimum** şarttır, tavan değil — DCABOT bunun üstüne çıkabilir. BÜYÜK FAZ J kapanıp AA sırası gelmeden hemen önce, Faz 17'nin geri kalanıyla aynı disiplinle (tek tek, sırayla, 3 bağımsız anonim ajandan) **"daha akıcı/gelişmiş trading-bot dashboard UX"** konusunda araştırma istenecek — kriter M/F/B değil, **kullanılabilirlik/performans (jank yok)/tutarlılık**. Bu, o anki güncel kütüphane/desenlerle yapılacağı için şimdiden istenmiyor (bayatlama riski) — AA.0 olarak roadmap'e eklenecek bir ön-dilim.

**Ortak kural (her AA dilimi için zorunlu):** muse (1) ilgili qwen `<section>` bloğunu HTML kaynağından **gerçekten okur**, (2) DCABOT'un karşılık gelen ekranındaki her nesneyi (kart/grid/buton/panel/chip/tablo sütunu) qwen'inkiyle **birebir eşler** — React bileşen/DOM iç yapısı birebir olmak zorunda değil, ama kullanıcı aynı nesneleri aynı yerde/sırada/biçimde görmeli, (3) eksik/farklı nesneleri qwen'e göre düzeltir, (4) DCABOT'a özgü gerçek veri/işlevi korur, uydurma veri eklemez. **AA, J'den sonra başladığı için artık C-J'nin backend'i hazır — "yakında/backend yok" istisnası yalnız kasıtlı kapsam-dışı kalemler (ör. Deploy ekranı) için geçerli, F/G/H/I alanları için değil.**

### 8.6.0 — AA.0: Bağımsız çapraz-araştırma turu (Arda, 2026-09-23, açıldı)

**Karar:** AA.1-AA.15'in yukarıdaki listesi yalnız BAŞLIK seviyesinde bir eşleme (hangi qwen bölümü hangi DCABOT ekranına karşılık geliyor). AA'nın kendisi başlamadan önce, HEM Claude HEM muse **birbirinin sonucunu görmeden, bağımsız olarak** aynı metodolojiyle derinlemesine bir araştırma yapar; sonuçlar çapraz değerlendirilip (Claude tarafından) TEK, nesne-seviyesinde eksiksiz, gerekçeli ve test edilebilir bir AA uygulama planına dönüştürülür. Amaç: AA'nın kendisi sırasında hiçbir "bunu nasıl yapacağız" belirsizliği kalmaması — plan yürütme sırasında hiç şaşmamalı.

**Metodoloji (ikisi de aynı adımları izler):**
1. **Envanter:** Birincil kaynak `docs/qwen_referans/iterasyonlar/14_1787388842.html` (15 `sec-*` bölümü) + ek ekranlar `17_1787399213.html`, `18_1787401208.html`, `21_1787405549.html`, `22_1787406517.html`. Her bölümdeki HER nesneyi (kart, grid, buton, form alanı, tablo sütunu, chip, grafik, animasyon/geçiş, boş/yükleniyor durumu) HTML/CSS/JS kaynağından okuyarak satır satır listele — ekran görüntüsüne/izlenime güvenme.
2. **DCABOT karşılığı:** `frontend/src/*.tsx` (güncel envanter) + `src/dcabot/server/api.py` gerçek endpoint'leri tara. Her qwen nesnesi için: VAR (birebir) / KISMİ (var ama eksik-farklı) / YOK.
3. **Backend-gerçeklik kontrolü (dürüstlük ilkesi, KRİTİK):** Karşılığı YOK/KISMİ olan her nesne için sor — bu artık tamamlanmış C-J fazlarında (margin_mode, order_type×4, max_active_safety_orders, take_profit_ladder, reinvest_pool, stop_loss_confirmation, max_deal_duration, profit_asset, active_deals_registry, çoklu-sinyal Kleene AST, MACD/StochRSI/Bollinger, whale-wall, korelasyon/likidasyon D-F) gerçek bir karşılığı var mı? Varsa hangi alan/endpoint. Yoksa **uydurulmaz** — "veri yok/devre dışı" olarak dürüstçe işaretlenecek şekilde not edilir (Arda'nın bağlayıcı ilkesi).
4. **Sektör-karşılaştırması:** qwen'in her ekranı için 3Commas/Pionex/Bitsgap'te gerçek bir eşdeğer var mı, varsa DCABOT nasıl daha iyi yapabilir (qwen taban, tavan değil — Arda'nın ilkesi).
5. **Teknik uygulanabilirlik:** Önerilen React yaklaşımı, mevcut bileşen/form kütüphanesiyle (`forms.tsx`, `formControls.tsx`) tutarlılık, yeni harici bağımlılık gerekiyorsa sıkı gerekçe (offline-first ilkesi), performans/jank riski.
6. **Bağımlılık/öncelik:** Hangi ekran hangi backend alanına bağlı (zaten hazır mı), hangi sırayla yapılmalı.

**Çıktı:** Her araştırmacı KENDİ dosyasına yazar, birbirininkini önceden okumaz:
- Claude → `docs/ARASTIRMA_AA0_UX_CLAUDE.md`
- muse → `docs/ARASTIRMA_AA0_UX_MUSE.md`

Format: ekran-bazlı (AA.1-AA.15 sırasıyla), her ekran için beş başlık: **[Nesne Envanteri]** → **[DCABOT Karşılığı: VAR/KISMİ/YOK]** → **[Backend-Gerçeklik: bağlı-alan veya dürüst-boş]** → **[Sektör-Karşılaştırma + İyileştirme]** → **[Teknik Not + Öncelik]**.

**Kapanış:** İkisi de bitince (Arda "bitti" der) Claude iki raporu çapraz okur, çelişki/atlanan nokta bulur, TEK kapsamlı AA uygulama planını (her AA.N için Hedef/Kapsam DIŞI/Allowlist/Kabul formatında, muse'a devredilebilir) yazar ve `docs/KARARLAR.md`'ye tek girdi olarak işler. Bu plan hazır olmadan AA.1'e başlanmaz.

- AA.1 (=`sec-status`): "Durum & Veri Kaynağı" kartı — Genel Bakış'a sistem/faz durumu göstergesi.
- AA.2 (=`sec-overview`, **en büyük dilim**): Genel Bakış TAM yeniden kurulur — 4 istatistik kartı + canlı piyasa grafiği + sembol seçici buton (mevcut `SymbolSelector` taşınır) + İndikatör çubuğu + Kâr Grafiği (Günlük/Haftalık/Aylık chip) + Canlı Sistem Akışı paneli (feed) + Açık İşlemler mini-kart grid'i.
- AA.3 (=`sec-bots`+`sec-botdetail`): Botlarım kart grid + Bot Detay tam sayfa — A.4/A.5'in qwen'in gerçek nesne dizilimine göre elemanı-elemanına denetimi.
- AA.4 (=`sec-deals`+`sec-dealdetail`): Aktif İşlemler tablosu (Smart Trade Terminal) + İşlem Detay tam sayfa.
- AA.5 (=`sec-dca`): Bot Kur (DCA) formu — canlı önizleme grafiği yerleşimi, şablon çipleri; artık G fazının Margin Mode/Order Type/çoklu-sinyal alanları da forma gerçek veriyle bağlanabilir.
- AA.6 (=`sec-datastore`): Veri Pipeline ekranı (eski 16.6).
- AA.7 (=`sec-backtest`): Backtest Studio — ANTİ-HALÜSİNASYON KURALLARI kutusu (§5), heatmap → Faz 14 sweep sonuçlarına bağlı (eski 16.7).
- AA.8 (=`sec-modules`+`sec-core`): Gelişmiş Modüller/Çekirdek & Modül Mimarisi (eski 16.8).
- AA.9 (=`sec-ai`): AI Önerici ekranı — B.2 rozetinin qwen düzenine taşınması.
- AA.10 (=`sec-risk`): Risk Paneli — B.3'ün canary/kill-switch bölümü + **artık gerçek** F fazının korelasyon matrisi/likidasyon (D) verisi qwen risk paneli yerleşimine taşınır.
- AA.11 (=`sec-grid`): Grid + Hybrid Engine (eski 16.10).
- AA.12 (=`sec-deploy`): Deploy ekranı — DCABOT offline-first kararıyla çelişiyor; bu dilim **kod yazmaz**, yalnız "bilinçli kapsam dışı" notu düşer.
- AA.13 (=`sec-compare`+`sec-config`+`sec-portfolio` iterasyon #17 "Strateji Laboratuvarı"): mevcut 15 bölümün DIŞINDA, daha önce hiç değerlendirilmemiş bir ekran — çoklu strateji/preset karşılaştırma + config + portföy görünümü. B.4'ün (Marketplace/A-B) gerçek karşılığı burada; qwen düzenine taşınır.
- AA.14 (=`sec-conn`+`sec-execlog`+`sec-history`+`sec-orders` iterasyon #18 "Testnet Execution Console"): testnet bağlantı durumu + emir logu + geçmiş + açık emirler — DCABOT'un Faz 3 testnet altyapısının (`testnet_order_execution.py`, `BinanceAccountPanel`) qwen görsel diline taşınmamış kısmı.
- AA.15 (=`sec-exec`+`sec-lab`+`sec-tests` iterasyon #21/#22 "Mission Control"): üretim/yürütme özeti + strateji lab + test durumu — DCABOT'un "Klasik Görünüm"deki dağınık araçların (Strateji Araştırma Araçları, Planlama ve Risk Araçları) toplandığı tek ekran karşılığı.

**Kapanış kapısı AA:** `tools/run_checks.py` + frontend testleri tam yeşil, build alınır, **15 qwen ekranı (AA.1-AA.12) + 3 ek ekran (AA.13-AA.15) tek tek yan yana gezilir**, fark kalmadığı doğrulanır. Arda'ya sor: "devam edeyim mi yoksa eklenecek bir not var mı?" **Bu, Faz 17'nin gerçek son büyük fazıdır.**

### 8.7 — Muse için sınırlar (değişmeyen, "tam yetkili" yetkiyi geçersiz kılan)

Muse'un bu roadmap'teki her büyük fazda geniş dosya-değiştirme yetkisi olsa da, aşağıdakiler **her koşulda** geçerli kalır (AGENTS.md'nin güvenlik çizgileri, bu belge tarafından gevşetilmez):
- Kimlik bilgisi/secret girme veya değiştirme yok.
- Gerçek mainnet emri yok (P3/canary kapısı Arda'nın açık onayı olmadan asla açılmaz).
- `src/dcabot/domain/math.py`'ye yazan her dilim (C, kısmen G, H, I) **yalnız Claude'un** doğrulayacağı şekilde küçük, test edilebilir commit'ler halinde bırakılır — muse büyük/tek-commit matematik değişikliği yapmaz.
- Her büyük faz kapanışında Arda onayı gelmeden bir sonrakine geçilmez (8.6'daki duraklar gerçek, atlanabilir değil).
- `tools/run_checks.py` kırmızıyken hiçbir büyük faz "kapandı" sayılmaz.

### 8.8 — Teslim: muse'a verilecek PowerShell prompt

Aşağıdaki blok, bu belgenin (§8) tamamını muse'a devretmek için hazırlanmış, kopyala-yapıştır PowerShell prompt'udur — proje genelinde daha önce kullanılan aynı delegasyon biçiminde.
