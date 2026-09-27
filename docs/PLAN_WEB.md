# DCABOT Web — sıfırdan arayüz yol haritası

Tarih: 2026-09-24 · Karar ve tasarım: Claude · Arayüz uygulaması: muse · Backend, finans ve test: Claude
Girdi: yalnız backend (`src/dcabot/`, 120 HTTP ucu) ve sektör tabanı (3Commas, Bitsgap, Pionex; gerçek ekran görüntüleri `docs/referans_ekranlar/`).
Eski frontend ve qwen referansı arşivde (`docs/archive/frontend-v1/`); bu planın hiçbir kararı onlara dayanmaz.

---

## 1. Hedef

Bir DCA/sinyal botu kullanıcısının 3Commas, Bitsgap ya da Pionex'ten geldiğinde öğrenmeden kullanabileceği,
her şeyin istatistiğini grafikle gösteren, sade ve şık bir web arayüzü. Üç ilke:

1. **Tanıdık dil.** Menü, alan adları, butonlar üç platformun ortak terimleriyle (§4).
2. **Her ekran tek iş.** Az menü öğesi, her ekranda tek ana eylem, gelişmiş ayarlar kapalı gelir.
3. **Her sayı backend'den, her şey grafikle.** İstemci finansal hesap yapmaz; istatistikler backend'de exact hesaplanır.

## 2. Backend envanteri — ne hazır, ne eksik

| Alan | Hazır uçlar | Durum |
|---|---|---|
| Piyasa | `public/klines` `ticker-24h` `last-price` `depth` `exchange-symbols`, `indicators/*` (SMA, EMA, MACD, BB, StochRSI), `risk/regime` | **Hazır** |
| Backtest | `historical-runs` (simulate, kaydet, listele, dışa aktar, yeniden üret), `datasets` + `dataset-downloads`, `sweeps/optimize`, `sweeps/overfitting` (PBO/DSR), equity eğrisi + Sharpe | **Hazır** (ek istatistik: §7 W-B5) |
| Bot önizleme | `preview`, `preview/full` (seviyeler, ortalama, TP, SL, marjin) | **Hazır** |
| Şablonlar | `templates` (listele, içe/dışa aktar, fark, profile bağla), `presets/compare` | **Hazır** |
| Sinyal botu | `signals/webhook/tradingview`, `status`, `intakes`, `bind`, `signals/*` | **Hazır** |
| Risk | `risk/kill-switch`, `risk/canary`, `risk/explain` ("neden işlem açılmıyor"), `risk/correlation`, `risk/liquidation-status` | **Hazır** |
| Sistem | `health`, `system/status`, `capabilities`, `events`, `admin/backup*` | **Hazır** (olay kaydı RAM'de) |
| Botlar | `bots` (yalnız kimlik + pariteler + sanal bütçe, **RAM'de**), `testnet/dca-sessions` (SQLite, strateji config burada) | **Parçalı** |
| Bot çalışması | `place`, `sync`, `mark`, `paper-fill`, `decision` — **yalnız dışarıdan çağrılınca bir adım ilerler** | **Eksik: otomatik çalıştırıcı yok** |
| Deal'ler | `deals` (dosya tabanlı yaşam döngüsü), `deals/{id}/timeline`, `testnet/dca-sessions/{id}` | **Parçalı** |
| İstatistik | `dashboard` (sayaçlar), `portfolio/dca-performance`, `bots/{id}/dca-sessions/performance` (toplam gerçekleşmiş net) | **Eksik: zaman serisi yok** |
| Araçlar | `rebalance/*` (plan, emir yok), `recurring/schedule` (projeksiyon), `futures/*` (projeksiyon), `two-leg/*` | Hazır, ama **bot değil** |
| Grid botu | yalnız seviye/marjin projeksiyonu; `INFINITY_GRID` kapalı | **Motor yok** (Arda kararı: AA Q2) |

**Sonuç:** Arayüz yazılmadan önce backend'de üç temel eksik kapanmalı. Bunlar kapanmazsa hiçbir arayüz sektör ürünü gibi davranamaz:
- Kalıcı bot kaynağı yok.
- Botları kendi kendine çalıştıran bir döngü yok.
- İstatistik zaman serileri yok.

## 3. Mimari ve teknoloji

| Karar | Seçim | Gerekçe |
|---|---|---|
| Uygulama | **Next.js 16 (App Router) + React 19 + TypeScript strict**, yeni klasör `web/` | Varsayılan yığın; rota bazlı sayfalar (`/bots/[id]`, `/deals/[id]`) doğal. |
| Stil | **Tailwind CSS v4 + shadcn/ui (Radix)** | Erişilebilir hazır bileşenler; token'larla tek tema. |
| Sunucu durumu | **TanStack Query** (polling, önbellek, yeniden deneme) | Canlı veriler (fiyat, bot durumu) için standart. |
| İstemci durumu | **Zustand** (tema, seçili sembol, tablo tercihleri) | Varsayılan yığın, hafif. |
| Fiyat grafiği | **TradingView Lightweight Charts** | Sektörün kullandığı kütüphane; mum, seviye çizgisi ve işaretleyiciler. |
| İstatistik grafikleri | **Recharts** (shadcn Charts) | Çizgi, alan, çubuk, halka, ısı haritası. |
| Sayılar | Backend exact metin → **`DecimalString` tipi**; biçimlendirme BigInt tabanlı (`formatDecimal`); `Number()` yalnız grafik pikseli | Float yok; mevcut finans disiplini. |
| API sözleşmesi | Backend v2 uçlarına Pydantic `response_model` → OpenAPI → **`openapi-typescript`** ile üretilen tipler + sınırda **zod** doğrulama | Eski arayüzdeki `FullPreviewPanel` tipi uyuşmazlığının tekrarını yapısal olarak önler. |
| Gerçek zaman | Önce polling (2–10 sn), sonra **SSE** `/api/stream` | Basit başla, ölçeklenince akışa geç. |
| Çalışma | Yerel: `next dev` → `/api` FastAPI'ye proxy (127.0.0.1:8000). Dış erişim gerekirse Cloudflare Tunnel. | Offline-first. |
| Dil | Türkçe arayüz + İngilizce; sektör terimleri standart İngilizce biçiminde, Türkçe açıklama ipucuyla (§4) | Kullanıcı 3Commas/Pionex'ten bu terimleri tanıyor. |
| Test | Vitest + Testing Library, **fast-check** (sayı biçimlendirme özellik testleri), **Playwright** (uçtan uca + ekran görüntüsü karşılaştırma), axe (erişilebilirlik), gerçek backend'e karşı sözleşme testleri | Görsel kabul ekran görüntüsüyle; sözleşme gerçek backend'le. |

## 4. Ortak terminoloji (3Commas · Bitsgap · Pionex → DCABOT)

| DCABOT arayüzü | 3Commas | Bitsgap | Pionex | Backend alanı |
|---|---|---|---|---|
| Bot | Bot | Bot | Bot | `bots` + session |
| DCA Bot / Futures DCA Bot / Signal Bot | DCA Bot / Signal Bot | DCA bot | DCA Bot / Signal Bot | `direction`, `leverage`, sinyal bağlama |
| Deal (aktif / geçmiş) | Deal | Deal / Trade | Order cycle | deal, session |
| Base order | Base order size | Base order | First order | `base_qty` (+W-B3: USDT cinsinden) |
| Safety order (SO) | Safety order | Averaging order | Additional order | `safety_qty`, `safety_count` |
| Max safety orders | Max safety trades count | — | Max orders | `safety_count` |
| Max active safety orders | Max active safety trades | — | — | `max_active_safety_orders` |
| Price deviation | Price deviation to open SO | Step | Price drop | `deviation` |
| Safety order volume scale | SO volume scale | Order size multiplier | Multiplier | `volume_multiplier` |
| Safety order step scale | SO step scale | Step multiplier | — | `step_multiplier` |
| Take profit (TP) | Target profit | Take profit | Take profit | `take_profit`, `target_mode` |
| Multiple TP targets | Multiple targets | — | — | `take_profit_ladder` |
| Trailing take profit | Trailing | Trailing TP | Trailing | `exits/trailing*` |
| Stop loss (SL) / SL timeout | Stop loss / SL timeout | Stop loss | Stop loss | `stop_loss_rate`, `stop_loss_confirmation_bars` |
| Max deal duration | — | — | — | `max_deal_duration_*` |
| Required funds | Max amount for bot usage | Investment | Investment | `preview/full.planned_gross_notional` |
| Price coverage | Max price deviation | — | Price range | seviyelerden (backend) |
| Average price / Break-even | Average price | Avg. price | Avg. price | `average_cost` |
| Total profit / Realized / Unrealized PnL | Profit / Unrealized | Current P&L / Realized | Total profit / Floating PnL | performance uçları + W-B5 |
| ROI / APR | ROI | — | APR | W-B5 |
| Add funds / Close at market / Cancel | Add funds / Close at market / Cancel | — | Close | W-B4 |
| Paper trading / Testnet | Paper trading | Demo | — | `mode: PAPER/TESTNET` |
| Backtest | Backtest | Backtest | AI params (backtest) | `historical-runs`, `sweeps/*` |
| Overfitting risk (PBO) | — | — | — | `sweeps/overfitting` — **fark yaratan özellik** |
| Kill switch | Panic sell all | — | — | `risk/kill-switch` |
| Templates / Presets | Bot presets | Presets | AI / Custom params | `templates`, `presets/compare` |

Kural: teknik kod değerleri (`CANARY_NOGO`, `APPROVED`, `µs`, `session_id`, JSON girdileri) arayüzde görünmez. Enum'lar etiket sözlüğüyle çevrilir, zaman alanları tarih seçicidir, kimlikler otomatik üretilir.

## 5. Bilgi mimarisi — 6 menü öğesi

| # | Menü | Rotalar | İçerik |
|---|---|---|---|
| 1 | **Kontrol merkezi** | `/` | KPI'lar, portföy değeri, günlük kâr, kâr dağılımı, aktif deal'ler, olay akışı |
| 2 | **Botlar** | `/bots`, `/bots/new`, `/bots/[id]` | Bot listesi (kart/tablo), bot oluşturma sihirbazı, bot detayı. Alt menü "Araçlar": Şablonlar, Rebalance planlayıcı, Düzenli alım planı |
| 3 | **Deal'ler** | `/deals`, `/deals/[id]` | Aktif / Geçmiş tablo, deal detayı (grafik, seviyeler, dolumlar, zaman çizgisi, eylemler) |
| 4 | **Backtest** | `/backtest`, `/backtest/[runId]`, `/backtest/compare`, `/backtest/optimize` | Yeni backtest, sonuçlar, karşılaştırma, optimizasyon + aşırı uyum riski |
| 5 | **Piyasa** | `/market`, `/market/[symbol]` | Parite listesi (arama, favori, 24s), parite sayfası (mum, indikatör, derinlik, rejim) |
| 6 | **Ayarlar** | `/settings/*` | Borsa bağlantısı (testnet durumu), Risk (kill switch, canary, "neden işlem açılmıyor"), Veri (dataset/indirme), Sistem (sağlık, yedek, olay kaydı), Tercihler (tema, dil) |

**Üst çubuk:** mod rozeti (Paper / Testnet, hiçbir zaman gizlenmez), kill switch butonu (onaylı), bağlantı durumu, bildirimler (olaylar), Ctrl+K komut paleti (parite, bot ve deal arama).
**Kapsam dışı / gizli:** Two-leg hedge ve futures lifecycle JSON hesaplayıcıları kullanıcı arayüzünde yok (Ayarlar > Sistem > Gelişmiş'te, katlanmış). Grid bot sihirbazda "Yakında" olarak görünür ve seçilemez; motor gelene kadar sahte ekran yok.

## 6. Ekran tasarımları ve istatistik kataloğu

Her grafik backend verisidir; "Kaynak" sütunu hazır uç ya da §7'deki yeni iştir.

### 6.1 Kontrol merkezi
| Öğe | Görsel | Kaynak |
|---|---|---|
| Toplam değer, bugünkü kâr, aktif bot, bağlı sermaye | 4 KPI kartı | W-B5 `stats/portfolio/summary` |
| Portföy değeri (7G/30G/Tümü) | Alan grafiği | W-B5 `stats/portfolio/equity` |
| Günlük gerçekleşmiş kâr | Çubuk grafik (yeşil/kırmızı) | W-B5 `stats/portfolio/daily-profit` |
| Bot/parite bazında kâr | Halka + sıralı liste | W-B5 `stats/portfolio/by-bot`, `by-pair` |
| Aktif deal'ler | Satır başına TP'ye ilerleme çubuğu, SO x/y | W-B4 `v2/deals?status=active` |
| Olay akışı | Zaman sıralı liste | `events` (W-B8 kalıcı) |
| Boş durum | "İlk botunu kur" daveti + "Önce backtest et" | — |

### 6.2 Botlar listesi ve bot detayı
- **Liste:** kart/tablo geçişi. Filtreler: tür, durum (Çalışıyor/Duraklatıldı/Durdu/Hata), mod. Her kartta mini kâr eğrisi, toplam kâr, aktif deal, çalışma süresi. Toplu duraklatma.
- **Detay sekmeleri:**
  - Genel: KPI'lar, kümülatif kâr grafiği, aktif deal kartı
  - Deal'ler
  - İstatistik: kazanma oranı, ortalama deal süresi dağılımı, **SO kullanım histogramı** (deal başına kaç SO doldu), aylık kâr, maks. düşüş
  - Backtest: son koşu + yeniden çalıştır
  - Ayarlar: düzenle
  - Olay kaydı
- Üstte diğer botlara hızlı geçiş şeridi.
- Kaynak: W-B1, W-B5 `stats/bots/{id}/*`.

### 6.3 Bot oluşturma sihirbazı
- **Adımlar:**
  1. Tür: DCA / Futures DCA / Signal / Grid (yakında)
  2. Parite ve mod: Paper / Testnet
  3. Giriş: base order (USDT), başlangıç koşulu (hemen / TradingView sinyali)
  4. Safety orders
  5. Take profit: tek hedef, çoklu hedef ya da trailing
  6. Stop loss ve limitler
  7. Özet
- **Sağ panel:** canlı mum grafiği (`public/klines`) üzerinde base order, SO seviyeleri, ortalama ve TP çizgileri, form değiştikçe `preview/full` ile anında güncellenir.
- **Özet kartı:** gerekli sermaye, fiyat kapsamı, bütçe limiti kontrolü.
- **Hazır ayarlar:** Muhafazakar / Dengeli / Agresif, ayrıca "şablondan başla".
- **Ana eylem:** "Paper'da başlat". İkincil eylem: "Önce backtest et" (aynı parametrelerle hızlı koşu, sonuç kartı sihirbazın içinde görünür).
- Kaynak: `preview/full`, `templates`, `historical-runs/simulate`, W-B1, W-B3.

### 6.4 Deal'ler
- **Tablo sütunları:** parite, bot, yön, ortalama fiyat, güncel fiyat, TP, uPnL (% ve USDT), SO x/y, süre.
- **Deal detayı:** fiyat grafiği + seviye çizgileri + dolum işaretleri, seviye tablosu, zaman çizgisi.
- **Eylemler:** Add funds, Close at market, Cancel (onaylı). Kaynak: W-B4, `deals/{id}/timeline`.

### 6.5 Backtest stüdyosu
- **Form:** sihirbazla aynı strateji bileşenleri + veri seçimi (parite, zaman dilimi, tarih aralığı, dataset durumu).
- **Sonuç ekranı:**
  - KPI'lar: net kâr, ROI, kazanma oranı, deal sayısı, maks. düşüş, Sharpe, ortalama süre
  - Equity eğrisi + **sualtı (drawdown) grafiği**
  - İşlem işaretli fiyat grafiği
  - **Aylık getiri ısı haritası**
  - Deal listesi
- **Karşılaştırma:** 2–4 koşu üst üste bindirilmiş equity eğrisi + metrik tablosu.
- **Optimizasyon:** parametre aralıkları, sonuç tablosu, 2 parametreli ısı haritası, **"Aşırı uyum riski" kartı** (PBO/DSR, düz dille: düşük/orta/yüksek + açıklama).
- Kaynak: hazır uçlar + W-B5 backtest ekleri.

### 6.6 Piyasa
- **Liste:** sembol, fiyat, 24s değişim, hacim, favori.
- **Parite sayfası:** mum grafiği (aralık seçici), indikatör katmanları, emir defteri derinliği, piyasa rejimi kartı (trend/yatay, ADX), "Bu paritede bot kur" butonu.

### 6.7 Ayarlar
- **Bağlantı:** testnet hesabı, bakiye, açık emirler (salt okunur).
- **Risk:** kill switch (neden alanı zorunlu), canary durumu, "Neden işlem açılmıyor" sorgusu.
- **Veri:** datasetler ve indirme işleri.
- **Sistem:** sağlık, disk, yedek al/doğrula, olay kaydı.
- **Tercihler.**

### 6.8 Tasarım sistemi
- **Tema:** koyu varsayılan + açık tema. Nötr zemin, tek vurgu rengi.
- **Anlamsal renkler:** kâr yeşili, zarar kırmızısı, SO/uyarı amberi, giriş mavisi. Gradyan ve parıltı yok.
- **Tipografi:** Inter; sayılar `tabular-nums` + JetBrains Mono.
- **Bileşen kiti:** StatCard, PnL metni (işaret + renk), Badge (live/paper/testnet/warn/danger), TP ilerleme çubuğu, ChartCard, DataTable (sıralama, sayfalama, sütun seçimi), EmptyState, ConfirmDialog, Skeleton.
- Bileşen galerisi `/design` rotasında; Playwright ekran görüntüsü tabanı buradan alınır.
- Mobil: tüm listeler kart görünümüne düşer; grafikler tam genişlik.

## 7. Backend işleri (Claude) — arayüzün önkoşulları

| Kod | İş | Neden |
|---|---|---|
| **W-B1** | **Kalıcı bot kaynağı** (SQLite `bots`): tür, mod, parite, doğrulanmış config, durum (Taslak/Çalışıyor/Duraklatıldı/Durdu/Hata), zaman damgaları. Uçlar `v2/bots`: oluştur, listele (özet istatistikle), detay, başlat/duraklat/devam/durdur, config güncelle, arşivle | Bugün bot RAM'de ve config ayrı yerde |
| **W-B2** | **Bot çalıştırıcı:** tek worker içinde asenkron döngü. Her çalışan bot için adımlar: fiyat → mark → karar → Paper'da simüle dolum, Testnet'te mevcut place/sync yolu (testnet kapısı ve kill switch saygılı). Çökmeden SQLite'tan devam. Idempotent. Her adım olay üretir. | Sektör ürününde bot kendi kendine çalışır; tarayıcı kapanınca durmamalı |
| **W-B3** | **USDT cinsinden emir büyüklüğü:** base/safety order'ı quote tutarıyla alıp `qty_step`/`min_notional` kurallarıyla exact `base_qty`'ye çevirme (backend'de) | Sektör standardı: "Base order: 100 USDT" |
| **W-B4** | **Deal v2:** botlar arası birleşik deal listesi/detayı (ortalama, güncel, TP, uPnL, SO x/y, süre). Eylemler: close at market, cancel, add funds (manuel SO) — motor desteği yoksa `engine.py`'ye eklenir | Deal ekranı ve aksiyonlar |
| **W-B5** | **İstatistik uçları (exact):** portföy özet/equity/günlük kâr/bot-parite dağılımı (çalıştırıcının yazdığı periyodik anlık görüntü tablosundan); bot istatistikleri (kazanma oranı, süre dağılımı, SO kullanım histogramı, maks. düşüş, ROI, APR); backtest ekleri (drawdown serisi, aylık getiri, deal listesi, profit factor) | "Her şeyin istatistiği grafikle" |
| **W-B6** | **SSE** `/api/stream`: olay, fiyat, bot durumu | Polling'den canlı akışa |
| **W-B7** | **Sözleşme:** tüm v2 uçlarında Pydantic `response_model`, OpenAPI dışa aktarımı, sözleşme kilit testleri | Tip uyuşmazlığını imkânsız kılmak |
| **W-B8** | Paper oturumları ve olay kaydını kalıcı yapma (SQLite) | Yeniden başlatmada veri kaybı olmasın |

Mevcut kurallar sürer: mainnet kesin NO-GO; testnet emirleri yalnız mevcut onay kapılarıyla; kill switch her şeyi durdurur; istemciye finansal hesap düşmez.

## 8. Arayüz dilimleri (muse uygular, Claude brief yazar ve doğrular)

| Kod | Dilim | Backend bağımlılığı |
|---|---|---|
| **W-F0** | İskelet: `web/` (Next 16, TS strict, Tailwind v4, shadcn, TanStack Query, Zustand, next-intl TR/EN, Lightweight Charts, Recharts), `DecimalString` + `formatDecimal` (fast-check özellik testleri), OpenAPI tip üretimi, Vitest, Playwright, CI işi, `.claude/launch.json` | — |
| **W-F1** | Tasarım sistemi + uygulama kabuğu: token'lar, bileşen kiti, `/design` galerisi, kenar menü (6 öğe), üst çubuk (mod, kill switch, bildirim, Ctrl+K), boş/yükleniyor/hata durumları | — |
| **W-F2** | Piyasa (liste + parite sayfası) | hazır |
| **W-F3** | Backtest stüdyosu (form, sonuç, karşılaştırma, optimizasyon, aşırı uyum riski) | hazır + W-B5 (backtest ekleri) |
| **W-F4** | Bot oluşturma sihirbazı (canlı seviye önizlemesi, hazır ayarlar, hızlı backtest, Paper'da başlat) | W-B1, W-B3 |
| **W-F5** | Botlar listesi + bot detayı (sekmeler, istatistik grafikleri) | W-B1, W-B2, W-B5 |
| **W-F6** | Deal'ler + deal detayı + eylemler | W-B4 |
| **W-F7** | Kontrol merkezi | W-B5 |
| **W-F8** | Ayarlar (bağlantı, risk, veri, sistem, tercihler) | hazır |
| **W-F9** | Kalite turu: mobil, erişilebilirlik (axe sıfır kritik), performans, ekran görüntüsü tabanları, onboarding | tümü |
| **W-F10** | Geçiş: eski frontend referanslarının temizliği (CI, `phase_gate`), README, kullanım kılavuzu | tümü |

## 9. Sıralama

```
Adım 0  Eski frontend kodunu arşive taşı (muse durduktan sonra) ─┐
Sprint 1  W-F0 + W-F1                     ║  W-B7 + W-B1              │ paralel
Sprint 2  W-F2 Piyasa + W-F3 Backtest     ║  W-B5 (backtest ekleri) + W-B3 + W-B2
Sprint 3  W-F4 Sihirbaz + W-F5 Botlar     ║  W-B4 + W-B5 (bot/portföy) + W-B8
Sprint 4  W-F6 Deal'ler + W-F7 Kontrol m. ║  W-B6 SSE
Sprint 5  W-F8 Ayarlar + W-F9 Kalite + W-F10 Geçiş
```

Backtest ve Piyasa önce gelir: backend'leri hazır, kullanıcı ilk sprintten sonra gerçek değer görür. Bot tarafı, çalıştırıcı (W-B2) doğrulanmadan açılmaz.

## 10. Kabul kriterleri (her dilim)

1. **Görsel:** taze sunucuda Playwright ekran görüntüleri (koyu + açık, masaüstü + mobil). Claude kendi görüntüsüyle doğrular; metin karşılaştırması kabul değildir.
2. **Sözleşme:** ekran yalnız OpenAPI'den üretilmiş tiplerle konuşur. En az bir uçtan uca test gerçek backend'e karşı koşar. Uydurma fixture yasak; fixture'lar gerçek yanıttan kaydedilir.
3. **Finans disiplini:** diff'te para değeri üzerinde `+ - * /` ya da `parseFloat` yok. Grafiklerde `Number()` yalnız piksel dönüşümünde.
4. **Dil:** §4 sözlüğü dışında teknik terim yok. Her boş durum bir davet cümlesi ve eylem içerir.
5. **Testler:** `tsc` temiz, Vitest ve Playwright geçer, axe'de kritik ihlal yok, backend `run_checks` geçer.
6. **Kayıt:** kapanış `docs/KARARLAR.md`'ye Claude yazar.

## 11. Arda'nın kararları gereken noktalar

- **Grid bot motoru** yapılacak mı (sektör tabanı için gerekli, ayrı faz)? Karar yoksa sihirbazda "Yakında" kalır.
- **Bildirim kanalı** isteniyor mu (Telegram / e-posta)? 3Commas ve Pionex'te var.
- **Testnet'te gerçek otomatik çalışma:** W-B2 çalıştırıcısının Testnet modunda emir göndermesi, mevcut onay kapısına ek olarak bot başına açık onay ister mi? Önerim: evet.
- **Mobil öncelik:** masaüstü öncelikli ve mobil uyumlu mu olsun, yoksa mobil öncelikli mi? Önerim: masaüstü öncelikli.
