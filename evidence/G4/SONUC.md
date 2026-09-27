# Faz G4 (COMBO-lite) — SONUÇ (Muse, 2026-09-27)

## G4-a — birleşik take-profit backend (2026-09-27, Muse)
Opsiyonel `combined_take_profit` (%): set ise motor deal-TP'si
kapanır (Config.take_profit=None), runner her adımda birleşik
uPnL% ≥ hedefse TÜM açık deal'leri marketten kapatır (TAKE_PROFIT,
yeni neden yok). Tetik bölmesiz exact (u*100 ≥ hedef*maliyet),
SHORT aynalı; boş/yassı/marksız defter asla tetiklemez.
Per-deal SL çalışmaya devam eder; pause'da kapanış olur, açılış
olmaz. Yan bulgu: multi next_seq off-by-one düzeltildi (max+1 →
max; kapanış-sonrası tekrar açılışta seq atlıyordu).
Kanıt (LOCAL): checker 2476/2476 (25 yeni); canlı paper
BTCUSDT+ETHUSDT hedef %0.05'te aynı tick'te kapandı (seq 1-2).

## G4-b — API + UI + e2e (2026-09-27, Muse)
DcaStrategy alanı + preview (combo'da TP fiyatı null) + sihirbaz
alanı + detay satırı + önizleme notu + backtest köprüsü; e2e
multi testi combo ile genişletildi. Kanıt (LOCAL): vitest
254/254, tsc+lint temiz, e2e 75/75; 3 görsel taban yenilendi
(bots-detail, backtest-desktop/mobile).
Sınırlar: tetik fiyat-hareketidir (maliyet hariç, ekrandaki uPnL
ile aynı tanım); backtest combo-kapanışı modellemez (ilk sembol,
TP'siz koşar). Faz G4 kapandı.
