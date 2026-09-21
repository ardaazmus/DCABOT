# F15.10 kanıt — eski kitchen-sink panelinin gizlenmesi (Claude, doğrudan düzeltme)

## Bulgu
Arda, temiz sunucu yeniden başlatma sonrası canlı ekranı gönderdi: "Bot Oluştur"
(15.3) unified akışı doğru çalışıyordu ama "Botlar & Stratejiler" ana sayfasının
**altında eski Bot stüdyosu/Ladder planı/Ekonomik özet/BotPanel/DealPanel/ExitPanel
panelleri hâlâ koşulsuz render ediliyordu** — 15.3'ün planı ("11 araştırma aracı
varsayılan kapalı") yalnız RebalancePanel/TemplatePanel/SignalPanel/FuturesPanel/
TwoLegPanel/RecurringPanel/RiskPanel'e uygulanmış, çekirdek eski builder trio'su
ve BotPanel/DealPanel/ExitPanel'e hiç uygulanmamıştı. Sonuç: yeni akış + eski akış
aynı sayfada üst üste, "ana sayfa tümüyle eski" izlenimi.

## Düzeltme
`App.tsx`'te "bots" bölümü yeniden sıralandı: varsayılan görünüm artık yalnız
HeroChartPanel + "+ Yeni Bot" + BotContextHeader + BotTable (Fleet Ops). Eski
builder-panel/ladder-panel/summary-panel + BotPanel + DealPanel + ExitPanel
yeni bir `AdvancedTools` grubuna ("Klasik Görünüm (eski panel + deal/exit
detayı)", yeni i18n anahtarı `tools.classic.label`) taşındı — davranış/veri akışı
değişmedi, yalnız varsayılan görünürlük.

## Doğrulama
- checker 1432/1432 PASS (1 skip), tsc temiz, vitest 234/234 (değişmedi —
  testler role/label ile sorguluyor, DOM konumuna bağlı değildi).
- Canlı ekran: temiz sunucu yeniden başlatma + tarayıcı doğrulaması yapıldı.
  Varsayılan sayfa artık yalnız 3 blok gösteriyor (Hero Chart, + Yeni Bot,
  Bot Fleet tablosu boş-durum deseniyle) + 3 katlı grup (Klasik Görünüm,
  Strateji Araştırma Araçları, Planlama ve Risk Araçları).

## Açık kalan (bu dilimde çözülmedi, dürüst not)
- Grafik kalitesi: demo veri seti yalnız 24 düz bar içeriyor, görsel olarak
  "heyecansız" — bu veri sınırlaması, render hatası değil. Gerçek TradingView-
  tarzı etkileşim (crosshair, zoom/pan, fiyat ekseni, indikatör overlay)
  `CandleChart.tsx`'in şu anki salt-SVG kapsamının dışında — ayrı bir dilim
  (Faz 16 adayı: `lightweight-charts` entegrasyonu, docs/ARASTIRMA_UI_
  TERMINOLOJI_I18N_FAZ12.md §4'te önerilmişti, henüz uygulanmadı).
