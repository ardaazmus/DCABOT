# Faz G2 (spot grid) — SONUÇ (Muse, 2026-09-26)

## G2-a — motor çekirdeği (2026-09-26, Muse)
Saf fiyat-serisi motoru `application/spot_grid_engine.py` (rev G2a.1):
aralık-bazlı emir modeli (aralık başına tek bekleyen), giriş fiyatı
dışındaysa WAIT, eşit kotasyon/grid tahsisi (fail-closed), seviyeden
limit dolgu (düşüşte yukarıdan-aşağı, yükselişte aşağıdan-yukarı),
fiyat-tabanlı SL + özsermaye-tabanlı TP (terminal likidasyon),
trailing up/down (aritmetikte toplamsal, geometrikte çarpımsal
kaydırma + mevcut bakiyeyle yeniden planlama), JSON snapshot +
config parmak izi (G2-c hazır). Kotasyon değişmezi her senaryoda
testli: rezerv+kilit = yatırım − alış + satış.
Kanıt (LOCAL): checker 2305/2305 (29 yeni test) · e2e 69/69 korundu.

## G2-b — grid backtest + API (2026-09-26, Muse)
`application/grid_backtest.py`: kapalı mumlar O,H,L,C intrabar yoluyla
motora beslenir; venue tick/qty_step/min-notional güncel kurallardan
alınır (varsayımlarda kayıtlı). Durumlar: COMPLETED/STOPPED_SL/
STOPPED_TP/NEVER_ENTERED (sermaye nakit sayılır). `POST
/api/v2/grid-backtests`: tarih/cache/venue akışı DCA ucuyla aynı,
typed sözleşme + body limiti + route listesi güncel.
Kanıt (LOCAL): checker 2318/2318 (13 yeni) · canlı: BTCUSDT 1h
20-26 Eyl (VENUE, 168 mum) +%4.27, 13 cycle, 31 dolgu.

## G2-c — grid paper + UI (2026-09-26, Muse)
`grid_runtime` tablosu + `grid_runner` (1m mumlar O,H,L,C) + runner
dallanması (terminalde STOPPED + GRID_STOPPED landmark). Uçlar: POST
`/api/v2/grid-bots` + `/preview` (hata→alan eşlemeli), GET
`/bots/{id}/grid`. UI: sihirbazda DCA/Grid seçimi + grid akışı,
detayda seviye merdiveni + dolgular, listede Tür sütunu. Portföy
grid botunu bütçeden sayar (canlı grid P&L portföyde yok — sınır).
Kanıt (LOCAL): checker 2333/2333 · vitest 237/237 · tsc+lint · e2e 71/71.
G2 KAPALI. Sıradaki: G3 futures parity.
