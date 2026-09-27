# muse — Görev W-F2.1 + W-F8: Piyasa düzeltmeleri + Ayarlar ekranı

Plan: `docs/PLAN_WEB.md` §6.7. İşbölümü aynı: yalnız bu görev, bana rapor. `STATE.md`, `TASK.md`, `docs/KARARLAR.md`, `src/` ve `web/src/lib/decimal.ts` değiştirilmez.

## W-F2 geri bildirimi
W-F2 kabul edildi. e2e 21/21'i kendim çalıştırdım; grafik, indikatörler, emir defteri ve mobil kill switch doğru. Sorularına cevaplar:
1. **Rejim 300 mum:** backend düzeltildi. ADX artık sabit 10^-30 ızgarasında; 300 mum 0,25 sn, 1.000 mum 0,29 sn. Karta 300 mum gönder ve notu "Son 300 1h mumuyla hesaplanır" yap.
2. **tickers-24h toplu hata:** davranış bilinçli, katı kalıyor. İşlemde olmayan parite (BREAK) için gerçek fiyat yoktur; listeyi TRADING ile sınırlaman doğru. Favorilerdeki TRADING dışı pariteyi gizleme: satırda "İşlem dışı" rozetiyle, fiyat hücreleri "—" olarak göster. Bu satırlar `tickers-24h` isteğine girmez.
3. **MACD/StochRSI scale 8:** uygun, kalsın.

## A. W-F2.1 düzeltmeleri
1. **"Bu paritede bot kur" düğmesi 17 MB'lık sembol listesini bekliyordu** (~14 sn boyunca "…" görünüyordu). Yeni uç `GET /api/public/symbol-rules?symbol=` ~1,5 sn'de döner.
   - Düğme `data.bot_supported` ve `data.bot_unsupported_reason` alanlarını kullanır.
   - `QUOTE_UNSUPPORTED` → "Şimdilik yalnız USDT pariteleriyle bot kurulabilir."
   - `NOT_TRADING` → "Bu parite şu an işlemde değil."
   - İstemci USDT kontrolünü kendisi yapmaz. Backend'in kuralı tektir (`sector_dca.bot_unsupported_reason`).
2. **Sembol listesi artık backend'de 10 dk önbellekte** ve açılışta önceden yükleniyor (ilk istek ~0,2 sn). e2e'deki 30 sn beklemeleri makul bir değere indir.
3. **Hacim okunaklı değil:** "1.820.881.137,7509705 USDT". Tabloda ve başlıkta hacmi `maxFractionDigits: 0` ile göster. Kısaltma (Mn/Mr) istersen yalnız görüntüde ve `decimal.ts`'ye dokunmadan, metin üzerinde yap; ayrı bir yardımcı ve birim testi yaz.
4. **Grafik fiyat ekseni** "92000.00" biçiminde. Lightweight Charts `localization.priceFormatter` ile TR biçimine çevir (binlik ayırıcı, `,` ondalık). Bu çevirme `src/lib/chart/` içinde yapılır; ekran gösterimi olduğu için `Number` orada serbest.
5. `record:fixtures`'a `symbol-rules` (BTCUSDT ve BTCUSDC) ekle.

## B. W-F8 — Ayarlar (`/settings`)
Sol tarafta alt menü, her bölüm ayrı alt rota (`/settings/<bölüm>`):

| Bölüm | İçerik | Uçlar |
|---|---|---|
| **Borsa bağlantısı** | Testnet hesabı: bağlı / yapılandırılmamış, bakiyeler, açık emirler (salt okunur). Yapılandırılmamışsa dürüst açıklama + ne yapılacağı. Arayüzden anahtar girişi YOK. | `GET /api/testnet/account`, `GET /api/testnet/open-orders` |
| **Risk** | Kill switch: durum + aç/kapat. Açarken gerekçe zorunlu, ConfirmDialog ile. Canary durumu düz dille. "Neden işlem açılmıyor?" formu (isteğe bağlı bot/sembol) ve sonucu. | `GET /api/risk/canary`, `POST /api/risk/kill-switch`, `POST /api/risk/explain` |
| **Veri** | Dataset kataloğu (durum rozetleri), dataset indirme başlat/iptal ve iş durumu. Seçim, backtest stüdyosu için hazırlık. | `GET /api/datasets`, `POST /api/dataset-downloads`, `GET /api/dataset-downloads/{id}`, `POST …/cancel` |
| **Sistem** | W-F0 bağlantı kartı, sistem sağlığı (disk, veri dizini), yedek al / doğrula (ConfirmDialog), olay kaydı (sayfalı). | `GET /api/system/status`, `POST /api/admin/backup`, `POST /api/admin/backup/verify`, `GET /api/admin/backups`, `GET /api/events` |
| **Tercihler** | Tema, dil. | — |

Kurallar:
- **Kill switch ve yedek eylemleri gerçek yazma işlemidir.**
  - e2e'de kill switch açılırsa test sonunda mutlaka kapatılır.
  - Yedek testinde oluşan dosya raporda belirtilir.
- **Enum ve kod değerleri** (`CANARY_NOGO`, `NOT_CONFIGURED`, `VERIFIED` …) sözlükle Türkçe/İngilizce etikete çevrilir. Ham kod yalnız ipucunda (tooltip) görünür.
- **Her uç için** önce gerçek yanıtı fixture olarak kaydet, zod şemasını ondan yaz.
  - Eski uçların bazıları Problem Details değil `{"error":{"message","fields"}}` biçiminde hata döner. İstemci iki biçimi de ayrıştırmalı; birim testlerini gerçek kayıtlarla yaz.
  - Kayıt için bilerek hatalı bir istek gönder (ör. gerekçesiz kill switch).

## Sınırlar
- İstemcide finansal hesap yok. Bakiyeler ve tutarlar `formatDecimal` ile gösterilir.
- Kimlik bilgisi, API anahtarı ve secret giriş alanı YOK. Testnet anahtarı backend'de yapılandırılır; arayüz yalnız durumu gösterir.
- Backend'e dokunma.

## Rapor
Her zamanki biçimde: `git status` aynen, komut son satırları, ekran görüntüleri (yollarıyla) ve sapmalar.

Ekran görüntüleri: `/market/BTCUSDT` (düzeltilmiş eksen ve hacim), Ayarlar'ın 5 bölümü, kill switch onay diyaloğu.
