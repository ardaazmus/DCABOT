# Durum — 2026-09-21 (Faz 15 kapalı + 15.10 düzeltme, P4 hariç)

Aktif iş: **yok — Faz 15 + 15.10 bitti.** 15/15 kapı PASS + F15 görsel kabul.
Doğrulanan: checker 1432/1432 PASS (1 skip=optuna-yok), tsc temiz,
vitest 234/234. Kanıt: `evidence/F15.*/SONUC.md` + ekran görüntüleri.
Eksenler: implementation=COMPLETE · verification=PASS ·
evidence_scope=LOCAL_INTEGRATION · review=NOT_RUN ·
deployment=NOT_DEPLOYED

## Kapanış (bu oturum)
F15 (15.1–15.9, muse): hero grafik, sektör form kontrolleri, Exit/TwoLeg
i18n, Bot Oluştur, Futures Pionex sırası, Hedge kartları, native
rozetler, başlatma-koşulu akışı, Optimize→sweep. **15.10 (Claude, doğrudan
düzeltme):** Arda canlı ekranda "ana sayfa tümüyle eski" bulgusunu
bildirdi — eski Bot stüdyosu/Ladder/Ekonomik özet/BotPanel/DealPanel/
ExitPanel panelleri 15.3'ün "varsayılan kapalı" kuralına dahil edilmemiş,
yeni akışla üst üste kalmıştı. Ayrıca iki `:8000/:8001` öksüz sunucu
süreci eski kodu çalıştırıyordu (öldürüldü). Düzeltme: bu paneller
`AdvancedTools` "Klasik Görünüm" grubuna taşındı; varsayılan sayfa artık
yalnız Hero Chart + Yeni Bot + Bot Fleet. Kanıt: `evidence/F15.10/SONUC.md`.

## Bilinen sınırlar
- DCA/paper/bot session RAM'de; şablon/two-leg/deal/webhook dosyada.
- Mainnet kesin NO-GO. NVDA/JAWS/HCM NOT_RUN. Dış LLM DEFERRED.
- Pine-parity DEFERRED. Hedge/Sonsuz kapıda kapalı.
- DEFERRED: PBO satırı, Canary rozeti, 15.9 risk toggle'ları, 15.8 pair
  keşfi → Faz 16 adayı.
- **Grafik kalitesi (yeni, dürüst not):** `CandleChart.tsx` salt-SVG,
  TradingView-tarzı crosshair/zoom/indikatör yok; demo veri seti 24 düz
  bar. Gerçek kütüphane entegrasyonu (`lightweight-charts`) Faz 16 adayı.
- Motor `average_entry_price` exactness tuzağı sürüyor.
- review=NOT_RUN (F12–F15 bağımsız incelemesi yapılmadı).

## Arda kararları (açık)
Canary değerleri + onay formatı; dış LLM; P4 kapsamı; Pine indikatörü;
NVDA/JAWS/HCM; 15.8 keşif metriği; Faz 16 kapsamı (grafik kütüphanesi +
motor esnekliği).
