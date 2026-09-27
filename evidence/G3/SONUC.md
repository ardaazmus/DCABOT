# Faz G3 (futures parity) — SONUÇ (Muse, 2026-09-26)

## G3-a — futures grid motor çekirdeği (2026-09-26, Muse)
Saf motor `application/futures_grid_engine.py` (rev G3a.1): one-way
LONG/SHORT, isolated 1-10x, aralık-bazlı emir (açılış marjin kilitli),
aralık-etiketli lotlar + FIFO eşleşme (ortalama-giriş exact'a sığmaz,
bu yüzden lot takibi; toplam-form likidasyon kökü doğrulanmış formülle
diferansiyel testli), funding oran+mark'tan motor içinde türetilir
(|oran| ≤ %2), SL/TP/trailing spot ile aynı, snapshot+parmak izi.
Likidasyon yalnız ESTIMATE_ONLY etiketiyle (LCR-12 sürüyor);
tiers yoksa tahmin üretilmez. Marjin değişmezi (cüzdan+kilit+lot =
yatırım+gerçekleşen−komisyon+funding) tüm senaryolarda testli.
Kanıt (LOCAL): checker 2355/2355 (22 yeni).
Sıradaki: G3-b futures grid backtest + API.

## G3-b — futures grid backtest + API (2026-09-27, Muse)
POST /api/v2/futures-grid-backtests: venue fapi kline + funding + kurallar,
ayrı kline/funding cache'leri, typed sözleşme. Funding bar kapanışına
atfedilir; liq tiersiz modellenmez (varsayımda yazar). Motor marjin-exact
düzeltmesi + fapi tam-liste kuralları dahil. Kanıt (LOCAL): checker
2400/2400 (45 yeni); canlı 120 mum COMPLETED +31.52 (15 funding).
Sıradaki: G3-c paper + UI.

## G3-c — futures grid paper + UI (2026-09-27, Muse)
Paper runner + API + UI: futures grid botlar 1m venue mumlariyla
canli kosar (funding dahil), sihirbaz/detay/liste futures-destekli.
Kanıt (LOCAL): checker 2413/2413 (13 yeni), vitest 244/244, e2e
grid.spec 5/5, tam e2e 73/73; canlı paper ACTIVE 5 lot/fill.
Faz G3 futures-grid ayagi kapandi; multi-pair + canli likidasyon acik.

## G3-d — multi-pair DCA (2026-09-27, Muse)
Tek bot N parite: pair başına runtime (cap-as-equity izolasyon),
paylaşımlı deal sırası + max_active_deals kapağı; fiyat-bağımsız
bütçe kapısı (cap × deals ≤ bütçe). Sihirbaz ek-sembol + kapak,
detay Sembol(ler), deals Parite sütunu, önizleme toplam kartı.
Kanıt (LOCAL): checker 2451/2451, vitest 253/253, e2e 75/75;
canlı paper BTCUSDT+ETHUSDT 2 deal (seq 1-2, aynı bar).
Faz G3 multi-pair ayağı kapandı; canlı likidasyon açık.
