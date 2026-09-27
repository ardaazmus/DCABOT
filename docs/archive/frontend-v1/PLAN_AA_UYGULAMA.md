# BÜYÜK FAZ AA — Nihai Uygulama Planı

Bu belge, `docs/ARASTIRMA_AA0_UX_CLAUDE.md` (Claude, bağımsız) ve `docs/ARASTIRMA_AA0_UX_MUSE.md` (muse, bağımsız) raporlarının Claude tarafından çapraz değerlendirilmesiyle üretilmiştir (§8.6.0 metodolojisi). İki rapor da aynı 5 qwen HTML dosyasını (14/17/18/21/22) ve aynı DCABOT kod tabanını bağımsız okudu; bulguların büyük çoğunluğu **birbirini doğruluyor** — bu, planın güvenilirliğini artırıyor. Çelişkili noktalarda hangi rapor izlendi ve neden, aşağıda her AA.N altında **[Sentez]** başlığıyla belirtildi.

**Numaralandırma notu:** Roadmap'in özgün AA.1-AA.15 numaralandırması (`docs/ARASTIRMA_FAZ16_QWEN_VIZYON_HARITASI.md` §8.6) burada kanonik kabul edildi. Muse'un raporu AA.8/AA.11'i (modules/core) ayırıp grid/deploy'u kaydırarak farklı numaralandırdı — bu yalnız bir defter-tutma farkı, içerik burada roadmap numaralarına geri eşlendi.

## Değişmez kurallar (her iki rapor da bağımsız aynı sonuca vardı — MUTLAK)

1. **Qwen'in sahte-veri üretim mantığı ASLA taşınmaz**: `Math.random()` fiyat/PnL/order-book/ping, hardcoded bot/deal dizileri, `0.95/lev` ve `entry*0.88+price*0.12` gibi uydurma formüller, sabit korelasyon matrisi/funding tablosu, "RUNNING" servis kartları, tarayıcı-içi unit-test koşucusu. Qwen'in nesne DİZİLİMİ taban, SAHTE VERİ ÜRETİMİ hiçbir zaman taban değil.
2. **LCR-12 mutlak**: Hiçbir ekranda motor kendi likidasyon tahminini çizmez/göstermez. Yalnız venue'den gelen gerçek değer (`/api/risk/liquidation-status/{symbol}`) gösterilir, yoksa hücre boş.
3. **Credential-giriş UI'sı KESİN YASAK** (AGENTS.md kural 1): API Key/Secret giriş formu hiçbir ekrana konulmaz (qwen'in sec-conn'u dahil). Yalnız MEVCUT (zaten ayarlanmış) credential'ların DURUMU gösterilir.
4. **"Canlı emir" yasağı**: Panic Sell/Fon Ekle/Smart-Trade-Aç gibi aksiyonlar YALNIZ paper-trading akışına (`/api/paper/sessions/*`) bağlanabilir, gerçek emir asla. Her yerde "PAPER" rozeti zorunlu.
5. **İstemci-tarafı finansal hesap YASAK**: Tüm PnL/ortalama/TP/SL/marjin/ROI hesapları sunucudan gelir (exact-Fraction), tarayıcıda yeniden hesaplanmaz.
6. **Offline-first**: Lightweight-Charts CDN'i veya başka bir yeni harici bağımlılık YOK — mevcut grafik bileşenleri (`TradingChart`/`CandleChart`) genişletilir.
7. **Ölü buton/form yasağı**: Backend'i olmayan bir aksiyon (switch, buton, form alanı) hiçbir zaman "yakında" olarak bile UI'a konmaz — ya gerçek bir uca bağlanır ya da hiç yer almaz.

---

## AA.-1 (yeni, plandan önce gelir): API-kablolama dilimi — **yalnız Claude**

İki rapor da bağımsız olarak aynı sonuca vardı: motor katmanının büyük kısmı (F.2 korelasyon, F.1 rejim, G.4 MACD/StochRSI/Bollinger/Kleene-AST, reinvest havuzu, active-deals registry, margin-mode preflight/registry) test edilmiş ve doğru ama **hiçbir HTTP endpoint'i yok**. AA.2 ve AA.10 gibi kilit ekranlar bunlarsız "dürüst-boş" kalır. Aşağıdaki ince FastAPI route'ları (yeni matematik değil, var olan fonksiyonları çağıran kablolama) AA.1'den önce eklenmeli:

| Yeni endpoint (öneri) | Çağırdığı mevcut modül | Hangi AA ekranını açar |
|---|---|---|
| `GET /api/deals` (liste) | mevcut deal state'lerinden agregasyon | AA.2 (miniDeals), AA.4 (tablo) — **EN KRİTİK, tek gerçek yeni backend** |
| `GET /api/indicators/macd`, `/stoch-rsi`, `/bollinger` | `momentum_oscillators.py`, `bollinger_bands.py` | AA.2 indikatör çubuğu |
| `GET /api/indicators/sma-series`, `/ema-series` | `signal_native_indicators.py` (zaten var, yalnız kesişim ucu bağlı) | AA.2 indikatör çubuğu |
| `GET /api/risk/correlation` | `correlation_risk.py`/`correlation_scores.py` | AA.10 korelasyon matrisi |
| `GET /api/risk/regime` (opsiyonel) | `regime_detection.py` | AA.10 ek bağlam |
| `GET /api/dashboard/portfolio-summary` | mevcut bot/deal state + `virtual_quote_budget` | AA.2 4-stat-kartı, AA.13 portföy halkası |
| `GET /api/dashboard/profit-series?period=` | deal geçmişi realized PnL toplamı | AA.2 Kâr Grafiği |
| `GET /api/public/ticker-24h` | Binance public 24s-değişim/hacim | AA.2 market paneli sütunları |
| `GET /api/bots/{id}/performance` | deal geçmişinden agregasyon | AA.3 6-kutu istatistik + sparkline |
| `GET /api/bots/{id}/deal-count` | mevcut bot/deal ilişkisi | AA.3 kart "N aktif deal" |
| `POST /api/preview/full` (avg/TP/SL/margin sayısal önizleme) | mevcut `plan()`/`target()` matematiği | AA.5 5-mini-stat |

**Kabul:** Her endpoint TDD'li (Claude), `run_checks.py` regresyon-sıfır, hiçbiri yeni ekonomik formül İCAT ETMİYOR (yalnız var olan `Config`/`engine.py`/`application/*` fonksiyonlarını HTTP'ye açıyor). Bu dilim AA.1 başlamadan biter.

---

## AA.1 (sec-status) — "Sistem Sağlığı"

**[Sentez]** İki rapor da aynı sonuca vardı: qwen'in "geliştirme fazı" içeriği taşınmaz, GÖRSEL FORMAT (halka+sayaç) gerçek DCABOT sayılarıyla doldurulur. Muse'un önerisi daha somut: bağlantı-modu, dataset-hazırlığı, bot/deal sayaçları, canary durumu.
**Hedef:** `SystemStatusCard` genişler + qwen'in dairesel-gauge/sayaç görsel dili eklenir; içerik `/api/dashboard`, `/api/risk/canary`, `/api/capabilities`'ten.
**Kapsam DIŞI:** Qwen'in "Faz 1/4/4.5" içeriği; `phaseGrid`'in roadmap-kartları (DCABOT'un kendi roadmap'i iç belge, kullanıcıya gösterilmez).
**Kabul:** Sayaçlar `prefers-reduced-motion` saygılı, tüm sayılar gerçek uçlardan; test.
**Öncelik:** DÜŞÜK-ORTA, AA.2'den sonra.

## AA.2 (sec-overview) — EN YÜKSEK ÖNCELİK

**[Sentez]** Tam mutabakat: en büyük ve en kritik dilim. Muse'un endpoint-eksikliği envanteri (portföy-toplam, indikatör-serileri, kâr-serisi, deal-listesi, ticker-24s) AA.-1 tablosuna alındı.
**Hedef:** 4 stat kartı + sembol-seçici+market-paneli (mevcut `SymbolSelector` taşınır) + indikatör çip çubuğu (SMA/EMA hazır uçtan, MACD/Bollinger/StochRSI AA.-1 sonrası) + Kâr Grafiği (dönem-chip'li, gerçek seri) + Canlı Sistem Akışı (`/api/events` doğrudan) + Açık İşlemler mini-kart grid'i (`data-goto` bölüm-geçişi zaten var).
**Kapsam DIŞI:** `engineTick` simülasyonu; Lightweight-Charts CDN'i (mevcut grafik bileşeni genişler).
**Kabul:** Her hücre ya gerçek veri ya dürüst-boş; hiçbir hücre placeholder-sayı taşımaz.
**Öncelik:** EN YÜKSEK. Sıra: (1) yerleşim + hazır-uçlu kartlar, (2) AA.-1 uçları gelince indikatör/kâr-grafiği/deal-özet bağlanır.

## AA.3 (sec-bots + sec-botdetail)

**[Sentez]** Güçlü mutabakat üzerine muse'un netleştirmesi eklendi: **switch (aç/kapa) ve Panic Sell backend'siz — YER TUTUCU OLARAK BİLE KONULMAZ** (ölü-buton yasağı, ürün+testnet-gate kararı bekliyor). Kill-switch kart-kilidi istisna: mevcut `/api/risk/kill-switch`'e bağlanabilir.
**Hedef:** `BotTable`'a kart-görünümü seçeneği eklenir (tablo korunur) + `BotDetailView`'e 6-kutu performans istatistiği (AA.-1 `bots/{id}/performance`) + hızlı-bot-geçiş chipbar + overlay genişletmesi (SO/TP/SL çizgileri, `build_plan` matematiğinden — Claude) + "Aktif Ayarlar" grid'i TÜM Config alanlarını gösterecek şekilde genişler (margin_mode, order_type×4, ladder, SL-onay, max-duration, profit_asset dahil).
**Kapsam DIŞI:** Bot aç/kapa switch'i, Panic Sell (backend-gate'siz — konulmaz).
**Kabul:** Kill-switch kilidi hariç hiçbir yeni buton/switch backend'siz eklenmez.
**Öncelik:** YÜKSEK (ikinci büyük dilim).

## AA.4 (sec-deals + sec-dealdetail)

**[Sentez]** Muse'un çözümü benimsendi (kendi ilk taslağımdaki "Smart Trade'i düşür" fikrinden daha iyi): **Smart Trade Terminal PAPER modda gerçeklenir** (`/api/paper/sessions/*` zaten var), "PAPER" rozeti zorunlu, canlı emir değil. Deal-liste ucu (AA.-1) bu dilimin ÖN KOŞULU.
**Hedef:** Deal tablosu (9 sütun, AA.-1'in deal-liste ucundan) + SO-doluluk (G.3 state machine'den gerçek) + TP-mesafe (`target()`'tan) + Deal Detay (8-bilgi-kutusu, grafik+overlay, "Seviyeler" paneli) + Fon-Ekle/Panic-Sell **yalnız paper-session'a bağlı, gerçek formülle** (`entry*0.88+...` UYDURMA formülü asla, gerçek `Position.buy()` matematiği kullanılır).
**Kapsam DIŞI:** Likidasyon mesafesi (LCR-12 — yalnız venue değeri varsa gösterilir); bağlı-bot ilişkisi (deal↔bot bağı modelde yok, dürüst-boş).
**Öncelik:** EN YÜKSEK (liste-ucuyla birlikte). Sıra: liste-ucu (AA.-1) → salt-okunur tablo+detay → hücre-gerçekleri → paper-aksiyonlar.

## AA.5 (sec-dca) — düşük risk, yüksek vitrin değeri

**[Sentez]** Tam mutabakat: backend zaten G-I fazlarıyla 3Commas+Pionex+Bitsgap toplamını aşıyor, yalnız TEK-SAYFA qwen yerleşimi eksik. Muse'un önerisi benimsendi: **sihirbaz adımları korunur (yeni-başlayan dostu) + qwen'in tek-sayfa formu "uzman görünümü" olarak İKİNCİ, aynı-state'li bir görünüm eklenir** (Pionex'in basit/pro ayrımına benzer).
**Hedef:** 5 mini-stat (AA.-1 `preview/full` ucundan) + tek-sayfa yerleşim + Deal-Start-Conditions çipleri (G.4 Kleene-AST'e bağlı, "HERHANGİ-BİRİ" mantığı 3Commas'tan farklı olarak AÇIK gösterilir).
**Kapsam DIŞI:** Trailing-TP, breakeven, 24h-filtreleri, cooldown (backend yok — motorsuz alan konulmaz).
**Öncelik:** YÜKSEK, düşük risk.

## AA.6 (sec-datastore)

**[Sentez]** Tam mutabakat. Muse'un netleştirmesi: script-üretimi (manifest/py/sh) DCABOT'un kendi artifact+hash formatına yeniden yazılır (qwen'in Parquet-yolu kopyalanmaz); "İndirdim→Kaydet" qwen'de sahte-kayıt riski taşıyordu — DCABOT'ta gerçek indirme-işi (`/api/dataset-downloads/{job_id}`) zaten var, o kullanılır.
**Öncelik:** ORTA.

## AA.7 (sec-backtest) — büyük değer açığı

**[Sentez]** Tam mutabakat, muse'un ek katkısı benimsendi: **her metriğe "kesinlik rozeti" (EXACT backend / FLOAT-analitik-sınırı) eklenir** — F.1/F.2/G.4'ün boundary disiplinini kullanıcıya gösteren, hiçbir rakipte olmayan bir şeffaflık katmanı.
**Hedef:** 9 metrik + equity eğrisi + trade tablosu (mevcut run-sonuç sözleşmesinden) + OPT sekmesi (`/api/sweeps/optimize` doğrudan bağlanır, sıfır yeni backend) + WF/MC sekmeleri (Faz 14 CPCV/PBO/DSR — AA.-1 benzeri küçük bir uç gerekebilir, ayrıca değerlendirilir).
**Kapsam DIŞI:** `btDeploy`'un "canlı bota kopyala" dili — yalnız "sihirbaza doldur" (paper-yönlü).
**Öncelik:** EN YÜKSEK (motor hazır, UI yok — en büyük değer açıklarından biri).

## AA.8 (sec-modules) — muse'un daha isabetli çözümü benimsendi

**[Sentez]** Kendi ilk taslağımda AA.8'i (modules+core birlikte) geniş ölçüde "kapsam dışı" eğilimindeydim. Muse'un modül-modül eşlemesi (11 karttan 6'sı VAR, 2'si KISMEN, 1'i YASAK/asla, 2'si UI'da "yakında") çok daha isabetli ve AKSİYON ALINABİLİR. Bu benimsendi.
**Hedef:** Modül-kart ızgarası SALT-OKUNUR KEŞİF ekranı olarak (yönetim/toggle değil) — her kart gerçek durumunu gösterir: Volatility-Adaptive-DCA (VAR, B.1), Regime-Detection (VAR, F.1 — AA.-1 sonrası canlı), Correlation-Risk (VAR, F.2 — AA.-1 sonrası canlı), Whale-Wall (VAR motor E.3, UI "yakında"), AI-Önerici (VAR, B.2), Circuit-Breaker (VAR, B.3), Marketplace (KISMEN, preset-galerisi VAR).
**Kapsam DIŞI:** Anti-Liquidation-Cascade kartı **hiç konulmaz** (LCR-12 — yasak kavramın reklamı bile yapılmaz); toggle/switch'ler (DCABOT'ta çalışma-zamanı modül-kapama yok); Custom-Strategy-Scripting kartı BLOCKED etiketiyle salt-bilgi.
**Öncelik:** DÜŞÜK, risksiz, vitrin değeri yüksek.

## AA.8b (sec-core, roadmap'te AA.8'e dahildi, ayrı ele alınması önerilir)

**[Sentez]** Muse'un ayrımı benimsendi: mimari-topoloji + event-bus şeridi DCABOT'ta KAVRAM OLARAK yok (event-bus mimarisi değil, doğrudan modül-çağrısı+FastAPI) — taşınmaz. Plugin-ekleme formu B.7 BLOCKED olduğu için **hiç konulmaz** (ölü-form yasağı).
**Hedef:** "Trafik" kutusu yerine GERÇEK `/api/events` özeti (son-N + tür-sayaçları); Modül-Kayıt-Defteri yerine `indicator_registry.py`'nin (G.4, GERÇEK bir kayıt defteri) salt-okunur görünümü + veri-adaptör kataloğu.
**Kapsam DIŞI:** Event-bus animasyonu, plugin-formu.
**Öncelik:** DÜŞÜK, AA.8 ile birleştirilebilir.

## AA.9 (sec-ai) — iki rapor da AYNI YENİ FİKRE bağımsız vardı

**[Sentez]** Güçlü, bağımsız yakınsama: ikisi de "kurgusal LLM sohbeti" yerine **dış-LLM kararından ÖNCE, sıfır-yeni-backend'li bir "Durum Asistanı"** öneriyor — mevcut uçlardan (`/api/dashboard`, `/api/events`, `/api/risk/canary`) beslenen, kural-tabanlı/deterministik, LLM'siz bir soru-cevap paneli (5-6 hazır soru: "durum ne", "canary durumu", "son koşu", "veri hazırlığı"). Bu, dış-LLM sorusu beklerken bile gerçek bir değer sunan, iki bağımsız araştırmacının aynı çözüme vardığı güçlü bir sinyal.
**Hedef:** "Durum Asistanı" ilk sürüm (yukarıdaki gibi) + `docs/KARARLAR.md`/`evidence/**`'e bağlı salt-okunur bir "karar/kanıt gezgini".
**Kapsam DIŞI:** Gerçek LLM entegrasyonu (açık soru, ayrı ürün kararı bekliyor); bağlanırsa bile sunucu-vekil zorunlu, anahtar istemciye asla.
**Öncelik:** DÜŞÜK-ORTA ama ucuz — sıfır yeni backend, hemen yapılabilir.

## AA.10 (sec-risk) — güvenlik-kritik

**[Sentez]** Tam mutabakat, muse'un netleştirmesi eklendi: kill-switch akışı (iki-aşamalı-onay + banner + resume) TAMAMEN hazır uçla (`/api/risk/kill-switch`) sıfır-yeni-backend'le yapılabilir — bu, güvenlik görünürlüğü açısından EN YÜKSEK öncelikli, en ucuz kazanım.
**Hedef:** `AppShell` başlığına kill-durum rozeti + iki-aşamalı-onay büyük buton + global banner + resume-akışı (mevcut `ConfirmDialog`) — sıfır yeni backend. Likidasyon listesi (`/api/risk/liquidation-status/{symbol}`, gerçek). Korelasyon matrisi + Funding tarayıcısı (AA.-1 sonrası).
**Kapsam DIŞI:** DD-eşik-slider'ın KAYDI (backend yok — salt-görsel filtre kalır ya da ayrı karar); "Auto-Deleverage" kavramı (yasak); sahte `0.95/lev` formülü (asla).
**Öncelik:** YÜKSEK. Sıra: banner+kill-akışı (hazır, hemen) → liq-listesi (hazır uç) → korelasyon/funding (AA.-1 sonrası).

## AA.11 (sec-grid) — muse'un daha sıkı sonucu benimsendi

**[Sentez]** Kendi ilk taslağım "grid görselleştirmesi taşınabilir" diyordu; muse'un daha dikkatli okuması doğru: DCABOT'ta qwen'in "geometrik grid + dinamik taban/tavan + 3-fazlı hibrit" kavramının GERÇEK bir motor karşılığı yok (`futures/grid/margin` bir MARJİN PROJEKSİYONU, canlı geometrik grid state'i değil). **Muse'un sonucu benimsendi: canvas+faz-döngüsü+kontroller KONULMAZ.**
**Hedef:** Yalnız "Grid (yol haritası)" iskelet-kartı — "motor yok, marjin projeksiyonu mevcut" dürüst notu + mevcut `FuturesGridMarginView`'e derin-bağlantı.
**Kapsam DIŞI:** Grid canvas'ı, Hybrid Engine 3-faz otomasyonu, grid-adımı slider'ı (motorsuz — hiçbiri konulmaz). Gerçek bir grid motoru istenirse bu AYRI, büyük bir BÜYÜK FAZ konusu (ürün kararı).
**Öncelik:** EN DÜŞÜK.

## AA.12 (sec-deploy)

**[Sentez]** Tam mutabakat: qwen'in docker-compose/postgres/redis/celery mimarisi DCABOT'un gerçek (yerel-önce, tek-backend) mimarisiyle temelden uyuşmuyor — kopyalanmaz. Muse'un somut önerisi benimsendi.
**Hedef:** "Sistem & Yedekler" sekmesi — gerçek sağlık-yoklaması (backend-up, veri-dizini, disk, yedek-durumu) + mevcut `BackupPanel` + Cloudflare-Tunnels kurulum-kılavuzu (statik belge).
**Kapsam DIŞI:** Servis-kartları (sahte "RUNNING"), docker-compose bloğu, CPU/RAM barları (istemci-ölçümü yanıltıcı), terminal-animasyonu.
**Öncelik:** DÜŞÜK-ORTA.

## AA.13 (sec-compare + sec-config + sec-portfolio, iterasyon #17) — büyük değer açığı

**[Sentez]** Muse'un buluşu kritik ve benimsendi: **`preset_comparison.py` (B.4) ZATEN aynı-dataset üzerinde yan-yana karşılaştırma yapıyor** — bu ekranın TAM karşılığı, sıfır yeni backend. Kendi taslağımda bunu bu kadar kesin tespit etmemiştim.
**Hedef:** Karşılaştırma tablosu+grafiği doğrudan `preset_comparison`'a bağlanır (Grid/Hybrid sütunları motor yok gerekçesiyle çıkarılır, yalnız DCA-varyantları). Portföy halkası — bot-bütçe dağılımı (`virtual_quote_budget`, gerçek) ilk sürümde, PnL AA.-1 sonrası. Konfigüratör "Paper Fırlat" gerçek paper-session akışına bağlanır.
**Kapsam DIŞI:** AI-öneri-kartları (B.2'nin gerçek sweep-önericisine bağlanmadan sabit metin asla).
**Öncelik:** YÜKSEK (motor hazır, UI yok).

## AA.14 (sec-conn + sec-execlog + sec-history + sec-orders, iterasyon #18)

**[Sentez]** Tam mutabakat + muse'un keskinleştirmesi: API-Key-giriş formu KESİN YASAK (madde 3, mutlak kural). Muse'un buluşu: **order book, `binance_public_depth`/E.3 whale-detection'a GERÇEKTEN bağlanabilir** — qwen'in sahte order book'unun yerine gerçek derinlik verisi konur; bu rakiplerin bile sunmadığı bir özellik (whale-duvar işaretleriyle).
**Hedef:** Emir formu YALNIZ paper-session'a bağlı ("PAPER" rozetli); order book gerçek derinlik (`binance_public_depth`); testnet açık-emirleri SALT-OKUNUR ayrı blok (`/api/testnet/open-orders`); execution log (`/api/events`, emir-filtreli).
**Kapsam DIŞI:** Anahtar-giriş formu (asla), sahte ping testi (asla — "Bağlantıyı Test Et" gerçek bir health-check'e bağlanır ya da konulmaz).
**Öncelik:** ORTA-YÜKSEK.

## AA.15 (sec-exec + sec-lab + sec-tests, iterasyon #21/#22)

**[Sentez]** Tam mutabakat: sec-exec/sec-lab AA.14/AA.13'ün küçültülmüş tekrarları (aynı analiz geçerli). **sec-tests (tarayıcıda motor testi) ÜRÜN'E KONULMAZ** — iki rapor da bağımsız aynı sonuca vardı (benim: "gereksiz+tutarsızlık riski"; muse: "test-sonuçları geliştirici-artefaktı"). Muse'un somut alternatifi benimsendi.
**Hedef:** sec-exec/sec-lab → AA.14/AA.13'e yönlendirilir (ayrı ekran gerekmez). sec-tests'in karşılığı: AA.1'in "Sistem Sağlığı" kartına gerçek `run_checks.py` sonucu + tarih damgası eklenir ("checker: PASS 1893 · <tarih>").
**Kapsam DIŞI:** Tarayıcıda motor-testi çalıştırma.
**Öncelik:** DÜŞÜK (AA.1'e gömülür).

---

## Öncelik sırası (nihai, muse'un uygulayacağı sıra)

1. **AA.-1** (API-kablolama, yalnız Claude) — her şeyin ön koşulu.
2. **AA.2** (Genel Bakış) — en büyük, en görünür.
3. **AA.4** (deal listesi+tablo) — kritik backend bağımlılığıyla birlikte.
4. **AA.5** (Bot Kur tek-sayfa) — düşük risk, yüksek vitrin.
5. **AA.7** (Backtest/OPT) — motor hazır, en büyük değer açığı.
6. **AA.13** (Strateji Lab, `preset_comparison`) — motor hazır, sıfır yeni backend.
7. **AA.3** (Bot kartları+detay).
8. **AA.10** (Risk — kill-switch banner önce, korelasyon AA.-1 sonrası).
9. **AA.9** (Durum Asistanı — ucuz, sıfır backend).
10. **AA.1** (Sistem Sağlığı, sec-tests'in yerini de alır).
11. **AA.6, AA.14** (orta öncelik).
12. **AA.8/AA.8b, AA.12** (düşük öncelik, vitrin).
13. **AA.11** (en düşük — iskelet kart).
14. **AA.15** — ayrı ekran değil, yukarıdakilere gömülür.

## Kapanış kapısı AA (değişmedi, roadmap §8.6'dan)

`tools/run_checks.py` + frontend testleri tam yeşil, build alınır, 15 qwen ekranı (+3 ek) tek tek yan yana gezilir, fark kalmadığı doğrulanır — ama artık "fark" ölçütü qwen'in SAHTE-VERİ desenine değil, bu planın "gerçek veri ya dürüst-boş" ilkesine göre değerlendirilir.

## Açık ürün soruları (iki rapor birleştikten sonra kalan, gerçekten teknik-olmayan)

1. AA.9'un dış-LLM'e geçiş zamanı (hâlâ açık, ayrı karar).
2. AA.11'in gerçek bir grid motoru olarak genişletilmesi istenip istenmediği (ayrı BÜYÜK FAZ).
3. AA.2'nin Kâr Grafiği hangi kapsamda (tek-bot/çoklu-bot/hesap-toplamı) hesaplanacak.
4. AA.8b'nin "modül kayıt defteri"nin veri-adaptör kataloğunun ötesine (gerçek bir strateji-plugin sistemi) genişletilip genişletilmeyeceği (B.7'nin BLOCKED durumunu kaldırma kararı, ayrı).
