# muse — Görev W-F3: Backtest stüdyosu (W-F4'ten sonra)

Plan: `docs/PLAN_WEB.md` §6.5. İşbölümü aynı: yalnız bu görev, bana rapor. `STATE.md`, `TASK.md`, `docs/KARARLAR.md`, `src/` ve `web/src/lib/decimal.ts` değiştirilmez.

## W-F4 geri bildirimi — önce bunları düzelt (W-F4.1)
W-F4 + W-F5a kabul edildi. e2e 37/37'yi yeniden başlatılmış backend'e karşı kendim çalıştırdım; geride test botu kalmadı. Ekran görüntülerindeki sorunlar:
1. **Mobil taşma:** `/bots/new` 390 px'te form ve önizleme kartları ekranın sağından taşıyor.
   - Düzelt.
   - Bütün rotalar için e2e'ye genel bir kontrol ekle: 390 px'te `document.documentElement.scrollWidth <= window.innerWidth`.
2. **Sapma ve fiyat kapsamı kâr/zarar değildir:** emir tablosundaki "Sapma" ve önizlemedeki "Fiyat kapsamı" yeşil ve "+" işaretli gösteriliyor. Bunları nötr renkte, işaretsiz göster ("%1,5", "%14,89"). PnL rengi yalnız kâr/zarar alanlarında kullanılır.
3. **Ondalık okunaklılığı (yalnız gösterim, `formatDecimal` ile):**
   - Fiyatlar paritenin `symbol-rules.tick` ondalık sayısıyla gösterilir. Örnek: ortalama "75.069,08". Şu an "75.069,075131761442" görünüyor.
   - USDT tutarları 2 ondalıkla gösterilir ("24,23").
   - Miktarlar `qty_step` ondalığıyla gösterilir.
   - Tam değer `title` ipucunda kalır.
   - Ondalık sayısını tick metninden çıkaran yardımcı + birim testi.
4. **Türkçe biçim:** Detay sayfasındaki Strateji kartında hacim ve adım ölçeği "1.5" / "1.2" görünüyor; `formatDecimal` ile "1,5" / "1,2" olmalı.
5. **Ham kod gösterimi:** USDC engel mesajında ham kod ("QUOTE_UNSUPPORTED") görünüyor. Yalnız etiket göster; kod ipucuna.
6. **Detay grafiği:** `bots-detail.png`'de "Seviyeler" grafiği boş (iskelet). Ekran görüntüsünden önce grafik tuvalinin çizildiğini bekle.
7. **Yeniden deneme davranışı onaylı:** önizlemede yalnız ağ/5xx için 2 yeniden deneme kabul (sapma 1). 422/409 asla yeniden denenmez; bu kural kalsın.

## Backend sözleşmesi (hazır, tipli — `npm run gen:api`)
`POST /api/v2/backtests`

İstek: `{budget, strategy, interval, start_date, end_date}`
- `strategy`: bot sihirbazıyla aynı `DcaStrategy`.
- `interval`: `15m` | `30m` | `1h` | `4h` | `1d`.
- Tarihler `YYYY-MM-DD` (UTC), bitiş günü dahil.

Yanıt `data`:
- **Kimlik ve durum:**
  - `symbol`, `interval`, `period_start_us`, `period_end_us`, `bar_count`, `processed_bar_count`
  - `status`: `COMPLETED` | `INDETERMINATE`; `indeterminate_at_us`
  - `budget`
  - `data_source`: `VENUE` | `CACHE`
- **`summary`:**
  - `net_profit`, `roi_percent`, `annualized_roi_percent`, `final_equity`
  - `deals_completed`, `winning_deals`, `win_rate_percent` (null = kapanmış deal yok)
  - `average_deal_profit`, `average_deal_duration_us`, `max_safety_orders_used`
  - `max_drawdown_percent`, `total_fees`
  - `sharpe_ratio_annualized` (null = tanımsız)
- **`open_deal`:** `{unrealized, cost, qty}` | null
- **`deals[]`:** `{deal, started_at_us, closed_at_us, safety_orders_filled, profit}`. Açık deal'da `closed_at_us` ve `profit` null.
- **`safety_order_usage[]`:** `{safety_orders_filled, deals}`
- **`equity_curve[]`:** `{time_us, equity}`
- **`drawdown_curve[]`:** `{time_us, drawdown_percent}`
- **`monthly_returns[]`:** `{month: "YYYY-MM", return_percent, complete}`. `complete:false` = kısmi ay (dönemin ilk ve son ayı).
- **`assumptions[]`:** `CURRENT_VENUE_RULES`, `CLOSED_BAR_FILLS`, `FEES_FROM_PAPER_CONFIG`, `FUNDING_NOT_MODELED`.

Hatalar (422 Problem Details, `errors[{field, code}]`):
- Tarih ve aralık: `BACKTEST_DATE_INVALID`, `BACKTEST_RANGE_INVALID`, `BACKTEST_RANGE_TOO_LARGE` (en fazla 20.000 mum).
- Strateji: `SECTOR_*` kodları (sihirbazla aynı).
- 502: borsa verisi alınamadı.

Süre: aralık ilk kez istendiğinde veri Binance'ten indirilir (180 gün 1h ≈ 20 sn); sonra yerel önbellekten gelir (≈ 3 sn). Yanıt 180 gün 1h için ~500 KB.

## Yapılacaklar — `/backtest`
1. **Form (sol):**
   - Parite, hazır ayar ve strateji alanları: W-F4 sihirbazının bileşenleri **yeniden kullanılır**, kopyalanmaz.
   - Bütçe.
   - Zaman dilimi çipleri: 15m / 30m / 1h / 4h / 1d. Varsayılan 1h.
   - Tarih aralığı. Varsayılan: son 90 gün, bitiş dün. Hızlı çipler: 30G / 90G / 180G / 1Y.
   - Seçilen dilim ve aralığın tahmini mum sayısını göster. 20.000'i aşıyorsa "Çalıştır" yerine uyarı: "Daha büyük zaman dilimi seçin ya da aralığı kısaltın." Bu, gösterim amaçlı tam sayı bölmesidir; finansal hesap değildir. Asıl sınırı backend uygular.
2. **Çalıştırma:**
   - "Backtest'i çalıştır" düğmesi.
   - İstek sürerken ilerleme metni: "Geçmiş veri hazırlanıyor… (ilk seferde 20 sn'ye kadar sürebilir)".
   - İptal düğmesi: isteği `AbortController` ile keser.
3. **Sonuç (sağ, üstten alta):**
   - **Durum bandı:** `INDETERMINATE` ise amber: "<tarih> tarihinde aynı mumda hem safety order hem take profit seviyesine dokunuldu; sıra bilinemediği için simülasyon burada durdu. Sonuçlar o ana kadardır." Veri kaynağı rozeti: "Binance'ten indirildi" / "Yerel önbellekten".
   - **KPI kartları:** Net kâr (PnL rengi) · ROI % · Yıllık ROI % · Kapanan deal · Kazanma oranı · Maks. düşüş % · Sharpe (yıllık; null → "—") · Ort. deal süresi (µs → "7s 56dk"; biçimlendirme yardımcısı + birim testi) · Maks. kullanılan SO · Toplam ücret.
   - **Equity eğrisi** (alan grafiği) + başlangıç bütçesi yatay çizgisi.
   - **Drawdown grafiği** (sualtı, negatif yönde alan).
   - **Aylık getiri:** çubuk grafik ya da ısı haritası. Kısmi aylar soluk + "kısmi" etiketi.
   - **SO kullanım dağılımı:** çubuk grafik; x = dolan SO sayısı, y = deal sayısı.
   - **Deal tablosu:** #, başlangıç, bitiş, dolan SO, kâr. Açık deal "açık" rozetiyle.
   - **Açık deal kartı** (varsa): gerçekleşmemiş PnL, maliyet, miktar.
   - **Varsayımlar dipnotu:** kodlar sözlükle düz dile çevrilir, örneğin "Güncel borsa kuralları kullanıldı; geçmişteki filtreler farklı olabilir", "Dolumlar kapanmış mum verisiyle simüle edildi", "Ücretler paper config'ten (%0,1)", "Funding modellenmedi".
4. **Köprüler:**
   - Sonuç ekranında "Bu ayarlarla bot kur" → `/bots/new`, form önceden dolu gelir. Aktarma zustand ya da URL parametresiyle; yöntemi sen seç, raporda yaz.
   - W-F4 sihirbazına "Önce backtest et" düğmesi → `/backtest`, aynı ön doldurma.

## Sınırlar
- İstemcide finansal hesap yok. Tüm metrikler yanıttan gelir; tabloda ve kartta yeniden hesaplama, toplama ya da ortalama yok.
- Grafik dönüşümleri yalnız `src/lib/chart/` içinde (`Number` yalnız orada).
- Uzun seriler (4.000+ nokta): grafikte göstermek için seyreltme yalnız görüntüde, `src/lib/chart/` içinde yapılır ve birim testi yazılır. Kartlar ve tablolar hiçbir zaman seyreltilmiş veriden beslenmez.

## Testler
- **Vitest:**
  - Süre biçimi.
  - Seyreltme (ilk ve son nokta korunur, min/maks kaybolmaz).
  - INDETERMINATE bandı.
  - Kısmi ay görünümü.
  - Problem Details alan eşlemesi (gerçek kayıtlarla).
- **Playwright** (canlı backend):
  - BTCUSDT Dengeli, 1h, 14 gün → sonuç kartları ve grafikler görünür.
  - İkinci koşuda "Yerel önbellekten" rozeti.
  - 15m + 1 yıl → aralık uyarısı.
  - "Bu ayarlarla bot kur" → sihirbaz dolu.
  - axe kritik ihlal 0.
  - Görsel taban: sonuç ekranı masaüstü ve mobil; sayılar maskeli.
- Her uç için önce gerçek yanıtı kaydet: başarılı yanıt (kısa aralık) ve her hata kodu için bir örnek.

## Rapor
Her zamanki biçimde.
