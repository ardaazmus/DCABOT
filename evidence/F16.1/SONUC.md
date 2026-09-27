# F16.1 kanıt — gerçek TradingView Lightweight Charts entegrasyonu

## Referans
Arda'nın Qwen sohbetinden kesin talimatı: "veri kaynağı olarak Binance Public
WebSocket, görselleştirme motoru olarak ise TradingView Lightweight Charts
kütüphanesini kullanmanız en optimum çözüm" (`docs/qwen_referans/
kullanici_istekleri.txt` [32]). Matematik doğrulaması: qwen'in SO/ortalama-
maliyet/TP ladder formülü standart ve DCABOT'un motoruyla aynı yöntem
(martingale step/volume scale); **likidasyon formülü** (`avg*(1-0.95/kaldıraç)`)
kaba bir sabit-oranlı yaklaşıklama — DCABOT'un mevcut `isolated_liquidation`
ESTIMATE_ONLY / LCR-12 BLOCKED kararı (gerçek venue marj-kademesi verisi
olmadan likidasyon fiyatı hesaplanmaz) korunuyor, qwen'in formülü kopyalanmadı.

## Yapılan
- `lightweight-charts@5.2.1` gerçek bağımlılık olarak eklendi.
- `TradingChart.tsx`: gerçek mum+hacim serisi (`addSeries(CandlestickSeries/
  HistogramSeries)`), fiyat-çizgisi overlay API'si (`createPriceLine`,
  ileride SO/TP/ortalama-maliyet seviyeleri için — 16.5), marker desteği.
  Girdi hâlâ backend'in exact Decimal string'leri; `Number()` dönüşümü
  yalnız piksel-render sınırında (ekonomik hesap değil, Faz 14'ün analytics-
  sınırı ilkesiyle aynı mantık).
- Aynı-saniyeye düşen ardışık bar zaman damgalarına karşı savunma (dedup)
  eklendi — ileride 1m veri geldiğinde kütüphanenin "strictly ascending"
  kuralı yüzünden tüm grafiğin çökmesini engeller.
- `HeroChartPanel.tsx` eski `CandleChart`'ı bırakıp `TradingChart`'ı
  kullanacak şekilde güncellendi; canlı fiyat artık gerçek bir price-line.
- Bundle şişmesini önlemek için `TradingChart` `React.lazy` ile ayrı chunk
  (177.85 kB gzip 57.44 kB) — ana bundle 604→426 kB'a düştü.
- Test ortamına `vitest-canvas-mock` + minimal `ResizeObserver` polyfill
  eklendi (jsdom canvas/ResizeObserver desteklemiyor).

## Doğrulama
- Backend checker 1432/1432 PASS (dokunulmadı, sadece hijyen kontrolü).
- tsc temiz, vitest 238/238 (4 yeni `TradingChart.test.tsx`).
- `vite build` PASS, ayrı `TradingChart` chunk doğrulandı.
- **Canlı ekran** (temiz sunucu yeniden başlatma sonrası): gerçek mum
  gövdeleri, sağ fiyat ekseni (95800.00 vb. gerçek etiketler), zaman ekseni,
  canlı fiyat kutusu, hacim histogramı, TradingView logosu — referans
  ekranlardaki (3Commas/Pionex/Bitsgap/qwen) gerçek chart deneyimiyle
  birebir aynı görsel dil.

## Açık kalan (16.5/16.3/16.4'e devrediyor)
- Grafik üzerinde SO/TP/ortalama-maliyet price-line overlay'i henüz Bot
  Oluştur formuna bağlanmadı (API hazır, `priceLines` prop'u var).
- Tam sayfa bot/deal detay görünümü (popup değil) henüz yok.
- Tüm-borsa sembol arama seçici henüz yok.
