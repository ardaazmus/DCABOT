# muse — Görev W-F2: Piyasa ekranı

Plan: `docs/PLAN_WEB.md` §6.6. Terminoloji: §4.
İşbölümü: yalnız bu görevi yap ve bana raporla. `STATE.md`, `TASK.md`, `docs/KARARLAR.md`, `src/` (backend) ve `web/src/lib/decimal.ts` değiştirilmez.

## W-F1 geri bildirimi
W-F1 kabul edildi. Rapor dosyalarla birebir uyuşuyordu, teşekkürler; aynı rapor düzenini sürdür.
Tek düzeltme (bu dilimde yap): mobil üst çubukta kill switch durumu gizlenmiş. Mod rozeti gibi hiçbir genişlikte gizlenmemeli; dar ekranda yalnız ikon + renk olabilir, `aria-label` ile.

## Kullanılacak backend uçları (hepsi hazır)
| Uç | Kullanım |
|---|---|
| `GET /api/public/exchange-symbols` | Parite listesi (sembol, durum, base/quote) |
| `GET /api/public/tickers-24h?symbols=A,B,…` | **Yeni.** En fazla 50 sembol; son fiyat, 24s %, 24s quote hacmi; istenen sırada |
| `GET /api/public/ticker-24h?symbol=` | Parite sayfası başlığı |
| `GET /api/public/klines?symbol=&interval=&limit=` | Mum grafiği; `bars[]` + `last_bar_closed` |
| `GET /api/public/depth?symbol=&limit=20` | Emir defteri |
| `POST /api/indicators/{sma,ema,bollinger,macd,stoch-rsi}` | İndikatörler. Gövdede `closes` = klines'tan gelen `close` metinleri **olduğu gibi**; istemci hesap yapmaz |
| `POST /api/risk/regime` | Piyasa rejimi kartı (aşağıda) |

Yanıt biçimlerini tahmin etme: her uç için `record:fixtures`'a gerçek yanıt ekle ve zod şemasını o yanıttan yaz.

## Yapılacaklar

### 1. `/market` — parite listesi
- **Sekmeler:** USDT · USDC · BTC · Favoriler. Varsayılan USDT.
  - Favoriler zustand + localStorage'da, izleyici başına.
  - localStorage erişimi try/catch içinde olmalı.
- **Arama kutusu** (sembol içerir).
- **Tablo:** Parite · Son fiyat · 24s değişim (PnL renkli) · 24s hacim (quote) · favori yıldızı.
- **Sayfalama:** sayfa başına 25 satır. Görünen sayfanın sembolleri tek `tickers-24h` isteğiyle alınır; 3.700 sembolü tek tek sorgulamak yasak. 15 sn'de bir yenilenir.
- **Satıra tıklayınca** `/market/<SYMBOL>` açılır.
- **Sıralama:** yalnız sayfa içinde. Tüm borsayı hacme göre sıralamak için backend ucu yok; bunu arayüzde "sayfa içinde sıralı" diye açıkça belirt.

### 2. `/market/[symbol]` — parite sayfası
- **Başlık:** sembol, son fiyat, 24s değişim, 24s hacim, favori yıldızı.
- **Mum grafiği:** TradingView Lightweight Charts, `klines`'tan.
  - Aralık çipleri: 15m · 1h · 4h · 1d. Varsayılan 1h, limit 300. 30 sn'de bir yenilenir.
  - `last_bar_closed:false` ise son mumun yanında "oluşuyor" ibaresi görünür.
  - Dönüşüm (metin → grafik sayısı, `open_time_us` → saniye) yalnız `src/lib/chart/` altında yapılır ve birim testi yazılır.
- **İndikatör katmanları** (aç/kapa çipleri, varsayılan kapalı):
  - Ana grafikte: SMA 20, EMA 50, Bollinger 20 / 2.
  - Alt panellerde: MACD 12/26/9 ve StochRSI 14/14.
  - `scale` ve diğer alanlar backend doğrulayıcısının istediği biçimde. Gövdeyi göndermeden önce doğrulayıcıyı `src/dcabot/server/api.py`'de oku (yalnız okuma).
  - Sonuçtaki `null` / eksik noktalar boşluk olarak çizilir; 0 uydurulmaz.
- **Emir defteri:** alış/satış 20 seviye, fiyat ve miktar metni aynen. 5 sn yenileme, "Duraklat" düğmesiyle durdurulabilir.
- **Piyasa rejimi kartı:**
  - `POST /api/risk/regime`, son 300 1h mumun `{high, low, close}` metinleri ile.
  - Parametreler: `adx_window 14`, `bb_window 20`, `bb_num_std "2"`, `trend_threshold "25"`, `range_threshold "20"`, `squeeze_threshold "0.05"`, `min_di_separation "0"`.
  - Sonuç düz dille gösterilir (Trend / Yatay / Sıkışma + yön).
  - Kartın altında şu not bulunur: "Eşikler sektör varsayılanlarıdır, bu parite için kalibre edilmedi."
  - `confidence` bir olasılık DEĞİLDİR; yüzde olarak gösterme.
- **"Bu paritede bot kur" düğmesi:**
  - USDT paritelerinde `/bots/new?symbol=<SYMBOL>` bağlantısı. Bu sayfa W-F4'te gelecek; şimdilik kabuğun EmptyState'ine düşmesi kabul.
  - USDT dışı paritelerde devre dışı + ipucu: "Şimdilik yalnız USDT pariteleriyle bot kurulabilir."
- **Bozuk ya da bilinmeyen sembol:** dürüst hata + "Piyasaya dön".

### 3. Ctrl+K
Parite seçimi zaten `/market/<SYMBOL>`'e gidiyor; değişiklik yok.

## Sınırlar
- İstemcide finansal hesap yok. Yüzde, fiyat ve hacim yalnız `formatDecimal` ile gösterilir.
- `Number()` yalnız `src/lib/chart/**` altında.
- Grafik, backend'in gönderdiğinden başka nokta çizmez: ara değer ya da tahmin yok.
- Backend'e dokunma. Eksik ya da yanlış bir uç varsa bana yaz.

## Testler
- **Vitest:**
  - klines → grafik dönüşümü (gerçek fixture).
  - `null` indikatör noktası → boşluk.
  - Favori deposu, localStorage hata verdiğinde de çalışmalı.
  - USDT dışı parite için bot kur düğmesi devre dışı.
- **Playwright** (canlı backend):
  - `/market` açılır, arama `ETH` → satır → parite sayfası.
  - Grafik tuvali görünür, aralık değişimi yeni istek atar.
  - İndikatör çipi açılınca `/api/indicators/sma` isteği gider.
  - Emir defterinde 20 + 20 satır.
  - axe kritik ihlal 0.
  - Görsel taban: `/market` ve `/market/BTCUSDT`, masaüstü + mobil.

## Rapor (bana)
1. `git status --short -- web .claude .github` aynen + yeni/değişen dosyaların gerçek listesi.
2. `typecheck`, `lint`, `test`, `build`, `test:e2e` son satırları.
3. Ekran görüntüleri ve yolları:
   - `/market` masaüstü + mobil
   - `/market/BTCUSDT` indikatörler kapalı ve açık
   - USDC paritesinde devre dışı bot kur düğmesi
   - mobil üst çubukta kill switch
4. Plandan sapmalar, gerekçesiyle.
