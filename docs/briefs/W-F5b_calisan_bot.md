# muse — Görev W-F5b: çalışan bot (Başlat, istatistik, deal'ler, olay kaydı)

İşbölümü aynı: yalnız bu görevi yap ve bana raporla. Şunları değiştirme:
- `STATE.md`, `TASK.md`, `docs/KARARLAR.md`
- `src/`
- `web/src/lib/decimal.ts`

**Ön koşul:** W-F9a (portlar 3770/8770, 3771/8771; e2e `next build` + `next start`) kabul edilmiş olmalı. Önce W-F9a'yı bitir; bu brief ondan sonra başlar.

## Backend değişikliği (hazır, Claude — W-B2)
Paper botlar artık gerçekten çalışıyor.
- Arka planda bir çalıştırıcı her 15 sn'de bir kapanmış 1 dakikalık Binance mumlarını okuyor.
- Base order, safety order, TP ve SL kuralları backtest ile birebir aynı işliyor.
- Gerçek emir yok.

**Senin API'ni yeniden başlatman gerekiyor:** 8770'e taşırken zaten yeniden başlayacak. Çalıştırıcı API açılışında kendiliğinden başlar.

### Değişen davranış
- `POST /api/v2/bots/{id}/start` → 200, durum `RUNNING`. İlk başlatmada o anki fiyat ve borsa kurallarıyla botun motor ayarı kurulur. Yeniden başlatma açık deal'i korur.
- TESTNET bot başlatılamaz → 409 `TESTNET_RUNNER_NOT_ENABLED`. UI'da Testnet botlarında **Başlat** devre dışı olsun; üzerine gelince açıklama: "Testnet otomatik çalışma ayrı onay gerektirir".
- Çalıştırıcı kapalıysa → 409 `BOT_RUNNER_UNAVAILABLE`. Problem Details `title`/`detail` metnini göster.
- **Duraklatıldı:** açık deal bitene kadar devam eder, yeni deal açılmaz. Bunu durum rozetinin yanında kısa bir ipucuyla belirt.
- `status_reason` (Bot nesnesinde zaten var) artık dolabilir:
  - `KILL_SWITCH_ACTIVE`: "Acil durdurma açık — bot donduruldu".
  - `MARKET_DATA_UNAVAILABLE`: "Piyasa verisi alınamıyor, yeniden deneniyor".
  - `RUNTIME_MISSING` veya `RUNNER_ERROR: …`: durum `ERROR` olur; metni olduğu gibi göster.
  - `null` ise hiçbir şey gösterme.
- `DealPlan` (preview) iki yeni alan döner:
  - `orders_total`: emirlerin toplamı.
  - `estimated_fees`: tahmini ücret.
  - `required_funds` = `orders_total` + `estimated_fees`. Önizleme panelinde üçü ayrı satırda görünsün.

### Yeni uçlar (hepsi GET; zod şemasıyla doğrula)
**`/api/v2/bots/{id}/stats`** → `{data: BotStats}`

```
total_profit: str            roi_percent: str (yüzde, "0.1234" = %0,1234)
deals_completed: int         winning_deals: int
win_rate_percent: str|null   average_deal_profit: str|null
average_deal_duration_us: int|null
stop_loss_deals: int         last_bar_open_us: int|null   (son işlenen mumun açılışı)
active_deal: null | {
  deal: int, started_at_us: int, safety_orders_filled: int, max_safety_orders: int,
  qty: str, cost: str, average_price: str, mark_price: str|null,
  unrealized_profit: str|null, take_profit_price: str|null, next_safety_order_price: str|null }
```

**`/api/v2/bots/{id}/deals`** → `{data: BotDeal[]}`. Sıra eskiden yeniye; en fazla bir açık deal olur.

```
deal: int, started_at_us: int, closed_at_us: int|null, safety_orders_filled: int,
profit: str|null, close_reason: "TAKE_PROFIT"|"STOP_LOSS"|null,
cumulative_profit: str|null   (kapanan deal'e kadar kümülatif gerçekleşen kâr; açık deal'de null)
```

**`/api/v2/bots/{id}/events?limit=1..500`** (varsayılan 50) → `{data: BotEvent[]}`. Sıra yeniden eskiye.

```
time_us: int
kind: "DEAL_STARTED" | "SAFETY_ORDER_FILLED" | "DEAL_CLOSED" | "AMBIGUOUS_BAR_SAFETY_FIRST"
detail: { [k]: str|int|null }
```

`detail` alanları türe göre:

| Tür | Alanlar |
|---|---|
| `DEAL_STARTED` | deal, price, qty, fee |
| `SAFETY_ORDER_FILLED` | deal, index (kaçıncı SO, 1'den), price, qty, fee |
| `DEAL_CLOSED` | deal, reason (`TAKE_PROFIT`/`STOP_LOSS`), price, qty, fee, profit |
| `AMBIGUOUS_BAR_SAFETY_FIRST` | high, low (mumun zamanı `time_us`) |

Bilinmeyen `detail` anahtarlarını düz göster; hata verme.

## Yapılacaklar (`/bots/[id]`)
PLAN_WEB §6.2'deki sekmeler. Bu görevde şunlar var:

1. **Genel:**
   - **KPI şeridi:** Toplam kâr, ROI, Tamamlanan deal, Kazanma oranı, Ortalama deal kârı, Ortalama deal süresi, SL ile kapanan.
   - **Kümülatif kâr grafiği:** x = `closed_at_us`, y = `cumulative_profit`. Toplama yapma; değer backend'den hazır gelir. `textToNumber` yalnız `lib/chart` içinde kullanılır.
   - **Aktif deal kartı:** ortalama fiyat, güncel fiyat, uPnL (renkli), TP fiyatı, sonraki SO fiyatı, "SO x/y" ilerleme çubuğu, süre.
2. **Deal'ler sekmesi:** tablo.
   - Sütunlar: #, başlangıç, kapanış, süre, SO dolumu x/y, kâr, kapanış nedeni rozeti (TP yeşil / SL kırmızı / Açık).
   - En yeni üstte.
3. **İstatistik sekmesi:**
   - **SO kullanım histogramı:** kapanmış deal'lerde `safety_orders_filled` değerine göre sayım (0..max). Sayım para hesabı değildir, UI'da yapılabilir.
   - Kazanma/kaybetme halkası.
4. **Olay kaydı sekmesi:**
   - Zaman çizgisi; türe göre ikon, TR/EN metin.
   - Sayfa başı 50; "Daha fazla" ile `limit` artar (en fazla 500).
5. **Veri tazeleme:**
   - Bot `RUNNING` veya `PAUSED` iken stats, deals ve events 15 sn'de bir yeniden çekilir (TanStack Query `refetchInterval`).
   - Diğer durumlarda periyodik çekme kapalı.
   - Başlat, duraklat, devam ve durdur sonrası bu üç sorgu geçersiz kılınır.
6. **Boş durum:** henüz deal yoksa "İlk deal bir sonraki kapanan 1 dakikalık mumda açılır" metni ve `last_bar_open_us` saati.
7. **Botlar listesi (`/bots`):** her satıra toplam kâr ve aktif deal SO x/y eklenir; `/stats` bot başına çekilir. Mini kâr eğrisi bu görevde yok.
8. **Temizlik:** `web/src/app/market/[symbol/]` adlı boş, bozuk klasörü sil. Yanlışlıkla oluşmuş; gerçek rota `market/[symbol]`.

## Kurallar
- Tüm para ve fiyat değerleri `formatDecimal` ile gösterilir.
- UI'da toplama, çarpma ya da yüzde hesabı yapılmaz; `Number()` yalnız `lib/chart`'ta kullanılır.
- Süreler `*_us` mikro saniyedir. Süre biçimlendirme (`3 sa 12 dk`) takvim aritmetiğidir, serbest.

## Testler
- **vitest:**
  - Şema testleri: gerçek yanıt örnekleri + null alanlar.
  - Histogram sayımı.
  - Olay metin eşlemesi.
  - Testnet Başlat'ın devre dışı olması.
- **e2e** (izole API 8771, gerçek Binance verisi — kapanan mum beklemek gerekir):
  - Paper bot oluştur → Başlat → durum RUNNING.
  - En fazla 150 sn içinde Genel'de aktif deal kartı ve olay kaydında `DEAL_STARTED` görünür.
  - Sonra durdur.
  - Bu test `@slow` etiketli olsun, ayrı çalıştırılabilsin.

## Rapor
Her zamanki biçimde (tam `git status`, gerçek dosyalar, komut çıktıları).

Ek olarak:
- Masaüstü ve mobil ekran görüntüleri: çalışan bir paper botun Genel, Deal'ler, İstatistik ve Olay kaydı sekmeleri.
- Duraklatılmış ve kill switch'li bot ekranları.
