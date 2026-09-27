# BÜYÜK FAZ A kanıt — Görsel taşıma çekirdeği (qwen görsel dili + gerçek grafik)

## Kapsam (FAZ16 harita §8.6, 5/5 dilim kapalı)
- A.1 (=16.1): `lightweight-charts` + Binance public WS sembol seçici.
  Önceki oturumda teslim + bağımsız doğrulama (3707 sembol canlı).
- A.2 (§2 token geçişi): 186 koyu-tema tokenı qwen paletine; fontlar
  npm-fontsource ile yerel bundle; açık tema dondurulmuş haliyle korundu.
- A.3 (=16.5): Bot Oluştur canlı parametre-overlay (form → /api/preview →
  GİRİŞ + SO çizgileri). TP/SL/avg/liq çizgisi YOK (backend alanı yok).
- A.4 (=16.3/16.4): tam sayfa bot/deal detay, popup yok (grep kanıtlı).
  Bot detayında A.3 overlay'i taslaktan besleniyor.
- A.5 (=16.2): bot listesi tablo → tıklanabilir kart görünümü.

## Doğrulama (muse, 2026-09-22)
- `uv run --frozen python tools/run_checks.py` → **1464/1464 PASS**
  (skip=1 optuna-yok).
- `npx tsc -b` temiz; `npx vitest run` → **283/283 PASS** (A.2-A.5'te
  +35 yeni test: qwenTokens 6, previewOverlay 5, HeroOverlay 3,
  BotWizard 6, BotCreateView 1, BotDetail 7, DealDetail 5, DealPanel 2,
  BotTable net +1; themeContrast AA + açık-tema dondurma yeşil).
- `npm run build` temiz; `vite preview` smoke: index 200 + başlık +
  root div, CSS'de Space Grotesk/.chipbar/.botcard-grid mevcut,
  `/api/bots` canlı yanıt verdi. Önizleme sunucusu kapatıldı.
- A.3 sözleşmesi ayrıca çalışan API'ye gerçek POST ile doğrulandı
  (anchor + 3 seviye + revision echo).

## Bilinçli kapsam-dışı (backend karşılığı yok, uydurulmadı)
- TP/SL/ortalama/lik overlay çizgileri (preview alanı ister, Claude işi).
- Bot açma/kapama, sparkline, PnL, bot↔deal bağları, deal listesi ve
  hızlı geçişi, deal fiyat grafiği, Fon Ekle/Panic Sell.
- Güvenlik onayları (toplu-deal/backtest confirm) detay akışı değil,
  aynen duruyor.

## Kapı
Build + gözlem tamam; Arda'ya "devam edeyim mi yoksa eklenecek bir
not var mı?" soruldu — yanıt bekleniyor. Onaysız BÜYÜK FAZ B'ye
geçilmez. review=NOT_RUN (bağımsız inceleme yapılmadı).
