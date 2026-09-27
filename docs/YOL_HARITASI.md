# Yol haritası

İki bağımsız eksen var. (1) **Venue ekseni** (bağlayıcı sıra): P1 yerel demo → P2 Binance testnet → P3 gerçek Binance (sınırlı canary) → P4 diğer borsalar. (2) **Özellik ailesi ekseni** (Faz 5-8, 2026-09-21'de dondurmadan çıkarıldı): her aile kendi sözleşme olgunluğuna göre venue eksenine PARALEL ilerler — mainnet'i (P3/P4) beklemez, ama kendi kanıt kapısını (aşağıda) geçmeden implementasyona geçmez. Bir sonraki faza geçmek için önceki fazın kapanış ölçütü sağlanır. Eski dilim günlükleri: `docs/archive/history/`.

## Şimdi
- **P4 hariç TÜM FAZLAR kapalı** (Faz 1+3-15, F11.1+F27+F20) + Faz 17 BÜYÜK FAZ A-F kapalı. **2026-09-24 Arda kararı: qwen ve eski frontend terk edildi, arşivlendi (`docs/archive/frontend-v1/`); Faz AA/AB geçersiz.** **Aktif: Faz W — arayüz backend'e ve 3Commas/Bitsgap/Pionex terminolojisine göre sıfırdan (`docs/PLAN_WEB.md`).** Önce backend önkoşulları (Claude): kalıcı bot, otomatik bot çalıştırıcı, istatistik serileri, USDT emir büyüklüğü, v2 sözleşme. W-F9a + W-F5b kapalı (2026-09-26, 3×62/62 e2e). Tek yapay zeka (2026-09-26, bağlayıcı): brief/devret kalktı. W-B4 + W-F6 + Faz G1 + W-B5 + W-F7 + W-B6 + W-B8 + N1 + Faz G2 + G3-a + G3-b + G3-c + N2-impl + G3-d + G4 + A + B + F10a + F20a (bot-copy) + F09a (DCA trailing TP) + Q1 (backtest fiyat+islem+PF) kapalı (2026-09-27, checker 2516/2516, vitest 265/265, e2e 79/79); sırada: Q2 (korelasyon-matrisi UI) → en son P4+N2-canlı+Qwen (Arda kararı). Faz G (parite) açıldı, aşağıda.

## Sonra
Faz 4 (canary, venue ekseni) · Faz 5-8 (dondurulmuş aileler, açık) · Faz 9 (P1 kapanış borcu) · Faz 10 (yeni aileler) — hepsi birbirinden bağımsız, paralel yürüyebilir; hiçbiri mainnet'i (P3/P4) beklemez.

## Faz G — Sektör paritesi: 3Commas/Bitsgap DCA+grid (2026-09-26 açıldı)
Bağlayıcı hedef (Arda): minimum 3Commas/Bitsgap spot/futures DCA ve grid bot özellikleri + görünümü. G1 DCA parity kapalı (SHORT + kapılar + futures paper; max-deals DEFERRED) → G2 spot grid (motor+backtest+paper+UI) → G3 futures parity (futures grid kapalı, multi-pair DCA kapalı, likidasyon canlı bekliyor) → G4 COMBO-lite kapalı. Bildirim N1 (uygulama-içi) paralel, N2 (Telegram) sonra. Kararlar: docs/KARARLAR.md 2026-09-26.

## Faz 0 — Temizlik (tamam)
Kural reformu, belge/kanıt arşivi, boyut kapısı. Yeni oturum yalnız AGENTS + STATE + TASK okuyarak doğru işi seçebilmeli.

## Faz 1 — Kod borcu
Açık hata raporu maddelerini doğrula ve kapat (TASK.md). Çıkış: rapor boş, tam checker + frontend testleri yeşil. `engine.py:292` tek-deal sınırı docs/KARARLAR.md'de belgelidir.

## Faz 2 — P1'i gerçekten kapat (tamam, `p1-demo-complete`)
Ürün akışı: veri seç → kalite raporu → bot kur → önizle → çalıştır → grafikten incele → kaydet → kapat/aç → yeniden üret. 2.1 demo denetimi, 2.1b sıralı deal (`deal_id`/`event_sequence` dedup), 2.2 ekonomik metrik seti, 2.3 reproduce+compare (`POST /api/historical-runs/{run_id}/reproduce`, hash karşılaştırmalı fail-closed), 2.4 grafik↔tablo etkileşimli marker, 2.5 stress modeli (dar kapsam — P1.16.i.b araştırması bağımsız kontrolde çelişkili çıktı verdi, yeni stress ekonomik kod `NO-GO`; mevcut `config.slippage` ile ikinci etiketli profil eklendi). Temiz klonda 9 adım hatasız çalıştı → bağımsız review `APPROVED_WITH_FINDINGS` (1 bulgu aynı gün düzeltildi) → tag. Ayrıntı: docs/KARARLAR.md.

## Faz 3 — P2: gerçek Binance testnet (tamam, `p2-testnet-complete`)
Ana dosyalar: `application/user_stream_reconnect_worker.py`, `rest_catch_up.py`, `testnet_order_execution.py` (mutation gate, 7 kural), `data_adapters/binance_testnet_order_execution.py` (mutation yapabilen TEK dosya), `application/testnet_dca_session.py` (DCA orkestrasyonu). 3.1/3.5/3.6 tam REAL_TESTNET, 3.2/3.7 kısmi. Bağımsız review `APPROVED_WITH_FINDINGS` — 2 bulgu (cancel'in AttemptStore disiplininden geçmemesi, UNKNOWN attempt'in yeni mutation'ı bloklamaması) aynı gün düzeltildi, 9 yeni test. Tüm bulgular/bug'lar/kanıtlar: docs/KARARLAR.md (tarih sırasıyla, 2026-09-20/21).

## Faz 4 — P3: gerçek Binance, sınırlı canary (altyapı tamam, kapı kapalı)
Arda'nın açık onayı olmadan mainnet emri yok. Teslim: tek-worker OS kilidi, saf canary politikası (cap/kayıp/pencere/sıfır-duplicate/sıfır-UNKNOWN), dosya kill-switch, test-only canlı kapı (hiçbir kod yolundan çağrılmıyor), `tools/run_api.py` paketleme, DRAFT `config/canary.json`. Emir gönderilmedi. Açık: canary sayısal değerleri + onay formatı (Arda). P4 (diğer borsalar) P3 sonrası planlanır.

## Faz 5-10 — dondurulmuş + yeni aileler (2026-09-21; KAPALI — claim ID eşlemesi: docs/KARARLAR.md 2026-09-21)
F5 futures-grid (liquidation `BLOCKED` LCR-12) · F6 two-leg (persistence/recovery LCR-09 AÇIK) · F7 rebalancing+signal (`VERIFIED`) · F8 çoklu-bot+LLM (`CONDITIONAL`) · F9 (F27 `VERIFIED`; F31/F09 kısmen AÇIK; F30 NVDA/JAWS yerel iş) · F10 (F20 blocker yok; F36/F40/F35 tasarım kararı gerekir; F16/F28/F29/F33/F39 `PLAN`).

## Belge düzeltmeleri (2026-09-21)
F22 (kayıtlı koşu/kıyas/log-chart) matriste stale `PLAN` kaydediliydi; gerçekte Faz 2.3/2.4 ile teslim edilmiş — `docs/OZELLIK_MATRISI.md` düzeltildi, yalnız CSV/JSON export `PLAN` kaldı.

## Faz 11 — Birleşik UI/UX tasarımı (2026-09-21, kapanış fazı; TAMAMLANDI)
2 bağımsız araştırma raporu → 5-bölüm IA + form ailesi + bot sihirbazı + bot tablosu/context + 5-kanal bildirim + render/lazy/transition (gate F11 PASS). Tam sentez (9 madde): docs/KARARLAR.md 2026-09-21 "Faz 11 tasarım kararı". **Not (2026-09-22): Faz 17'nin qwen görsel dili kararı bu fazın IA/bileşen iskeletini korur, yalnız token/renk/animasyon katmanını değiştirir.**

## Faz 12 — Birleşik bot deneyimi + terminoloji/i18n (KAPALI, LOCAL, gate F12 PASS)
6/6 dilim kapalı: 12.1 mum+hacim+canlı grafik (saf SVG, harici lib yok) → 12.5 tek-XML i18n (TR/EN takma-ad) → 12.2 birleşik sihirbaz → 12.3 küme B bağlantısı (salt okunur) → 12.4 webhook görünümü → 12.6 temizlik. Kanıt: `evidence/F12/SONUC.md`.

## Faz 13 — TradingView sinyal entegrasyonu (KAPALI, LOCAL, gate F13 PASS)
13.1–13.5 kapalı: static-token webhook + durable dedup + fast-ACK/bind + HMAC internal hat + native indikatörler. Kanıt: `evidence/F13/SONUC.md`.

## Faz 14 — İleri backtest: overfitting direnci + ölçekleme (KAPALI, LOCAL, gate F14 PASS)
14.1–14.6 kapalı: embargo + CPCV + PBO/DSR (izole `analytics/`) + sweep orkestratörü + sampler. Kanıt: `evidence/F14/SONUC.md`.

## Ölü/bağlanmamış kod envanteri (2026-09-21 tarama + 12.3/12.6 güncellemesi)
Küme B (9) 12.3'te bağlandı. `bootstrap`/`domain.math`/`store` ERİŞİLİYOR (üretim+tools) → silinmedi. `canary_policy`/`live_gate` test-only netleşti. Geri kalan bilinçli araştırma kodu (Faz 5/9 DEFERRED). Liste: `docs/ARASTIRMA_UI_TERMINOLOJI_I18N_FAZ12.md` §1.

## Faz 15 — Görsel düzeltme + terminoloji (2026-09-21; KAPALI + 15.10)
12 dilim + 15.10 (Claude: eski paneller "Klasik Görünüm"e taşındı, öksüz süreçler temizlendi). Liste+sözlük: `docs/ARASTIRMA_FAZ15_GORSEL_DUZELTME.md`. Kanıt: `evidence/F15.*/SONUC.md`.

## Faz 16 — Qwen vizyon haritası: gerçek TradingView chart + tam sayfa bot/deal detay (2026-09-21 açıldı; BÜYÜK FAZ A 2026-09-22'de kapandı, onaylı)
Arda'nın önceki Qwen denemesinden (yalnız arayüz simülasyonu) çıkan kesin talimatlar: `lightweight-charts` (Arda'nın kararı) + grafik üzerinde botun SO/TP/likidasyon seviyeleri canlı çizili + bot/deal tıklamasında popup DEĞİL tam sayfa detay + tüm-borsa sembol arama. DCABOT'un backtest/dataset/exact-math'ı qwen'den zaten daha olgun (o simüle ediyordu, DCABOT gerçek yapıyor) — kalan iş görsel taşıma. Kritik yol: 16.1 chart kütüphanesi → 16.5 canlı parametre-overlay → 16.3/16.4 tam sayfa detay. Tam harita+alıntılar+renk paleti: `docs/ARASTIRMA_FAZ16_QWEN_VIZYON_HARITASI.md`, kaynak: `docs/qwen_referans/`. **Implementasyona geçilmedi.**

## Faz 17 — 3Commas'ın ötesi: qwen modülleri + DCA-spec genişletme (2026-09-22, AÇIK, muse'a devredilecek)
12 konu için 3'er bağımsız anonim araştırma raporu toplandı, M/F/B (Matematik/Finansal/Borsa) doğrulaması yapıldı; konu 1 (Short/Bidirectional) `domain/math.py`'ye teslim edildi (bkz. `evidence/F17.7/SONUC.md`). Kalan 11 konunun kararları: `docs/KARARLAR.md` (2026-09-21/22 tarihli, konu başına ayrı kayıt). Detaylı, kapılı (test+QC+kabul), muse-icin-PowerShell-prompt haritası: `docs/ARASTIRMA_FAZ16_QWEN_VIZYON_HARITASI.md` §6-8. **Implementasyona geçilmedi — yalnız Faz 17.7 (yön matematiği) teslim edildi.**
