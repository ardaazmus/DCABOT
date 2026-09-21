# Yol haritası

İki bağımsız eksen var. (1) **Venue ekseni** (bağlayıcı sıra): P1 yerel demo → P2 Binance testnet → P3 gerçek Binance (sınırlı canary) → P4 diğer borsalar. (2) **Özellik ailesi ekseni** (Faz 5-8, 2026-09-21'de dondurmadan çıkarıldı): her aile kendi sözleşme olgunluğuna göre venue eksenine PARALEL ilerler — mainnet'i (P3/P4) beklemez, ama kendi kanıt kapısını (aşağıda) geçmeden implementasyona geçmez. Bir sonraki faza geçmek için önceki fazın kapanış ölçütü sağlanır. Eski dilim günlükleri: `docs/archive/history/`.

## Şimdi
- **P4 hariç TÜM FAZLAR kapalı** (Faz 1+3+4+5+6+7+8+9+10+11+12+13+14, F11.1+F27+F20). Kalan: Arda kararları (canary değerleri, dış LLM, NVDA/JAWS/HCM, P4 kapsamı).

## Sonra
Faz 4 (canary, venue ekseni) · Faz 5-8 (dondurulmuş aileler, açık) · Faz 9 (P1 kapanış borcu) · Faz 10 (yeni aileler) — hepsi birbirinden bağımsız, paralel yürüyebilir; hiçbiri mainnet'i (P3/P4) beklemez.

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
Kaynak: iki bağımsız anonim araştırma raporu (docs/UIUX_ARASTIRMA_FINAL/01_RAPOR_A.md, 02_RAPOR_B.md — NN/g, Material Design 3, Atlassian/Carbon/Fluent, W3C, React/web.dev resmi kaynaklı, CONFIRMED/CONDITIONAL/JUDGMENT sınıflı). İki rapor aynı ana sonuca yakınsıyor; tek ayrışma madde (2)'de. Tam sentez: docs/KARARLAR.md 2026-09-21 "Faz 11 tasarım kararı".

1. **3 katmanlı IA:** workspace kabuğu (üst bar: arama/Cmd-K, bildirim, hesap, workspace/tema) → **5 bölümlük** kalıcı sol nav (Genel Bakış · Botlar & Stratejiler · Piyasa & Veri · Olaylar & Denetim · Ayarlar; M3'ün "5'ten fazla nav hedefi koyma" sınırı `CONFIRMED`) → nesne workspace'i (breadcrumb + sabit bot-context header [ad·tür·parite·durum·PnL·Başlat/Durdur] + ≤7 in-page tab). **Strateji aileleri (DCA/grid/futures-grid/hedge/rebalance/sinyal) nav öğesi DEĞİL, "Botlar & Stratejiler" içinde tür/filtre** — mevcut `App.tsx`'teki tek "Bot stüdyosu" + disabled "Ayarlar"/"Planlar" sidebar'ı bu 5 bölüme genişletilecek.
2. **Tek ayrışma noktası:** Rapor A 8 üst bölüm önerdi (Automation/Portfolio/Monitor/Simulation/Alerts/Audit ayrı), Rapor B M3'ün sert 3-5 sınırını kaynak göstererek 5'e indirdi. **Karar: Rapor B'nin 5-bölüm modeli esas alındı** (daha güçlü kaynaklı); Rapor A'nın "Monitor" fikri ayrı nav öğesi değil, Genel Bakış özeti + Botlar tablosunun filtreli görünümü olarak korunuyor.
3. **Progressive disclosure:** global "Basit/Uzman mod" anahtarı YOK (`CONFIRMED` red — iki paralel ilerleme mekanizması kaynak kriterine aykırı); bunun yerine alan/bölüm seviyesinde "Gelişmiş: ..." (içerik-adı verilmiş, en fazla 2 seviye) katlanır. Risk-kritik alanlar (bütçe, kaldıraç, stop-loss, gerçek/paper, kill-switch durumu) **hiçbir zaman** katlanmaz.
4. **Formlar:** yeni bot = 4-6 adımlı sihirbaz + sağda canlı önizleme (`CONFIRMED`, NN/g Wizards); mevcut bot düzenleme = tek-sayfa bölümlü form + sticky önizleme paneli, sihirbaz YOK. Tüm strateji tipleri ortak `Section/FieldGroup/NumericParameter/ConditionalField/CalculatedPreview` bileşen ailesini paylaşır (tutarlılık, `CONFIRMED`).
5. **Çoklu bot izleme:** kart-özet (Genel Bakış) → virtualized/filtrelenebilir tablo (operasyonel çalışma yüzeyi, `CONFIRMED` Carbon data-table) → drawer/detay → tam bot workspace'i. 10+ bot'ta table-first.
6. **Bildirim mimarisi (5 kanal, hepsi `CONFIRMED`):** toast (geçici/otomatik-kapanan) · banner (kritik sistem-geneli, kalıcı) · section/status mesajı (bot-içi bağlamsal) · bildirim merkezi+rozet (geçmiş) · özetleyen-seçenekli onay diyaloğu (yıkıcı işlem).
7. **Gerçek-zamanlı render:** merkezi abone-store + `useSyncExternalStore`, tick throttle/batch, `useDeferredValue`/`useTransition`, uzun liste/tablolarda virtualization, `React.lazy`+`Suspense` code-splitting, ölçülmüş memoization (Profiler'sız otomatik memo YOK). Hedef: INP ≤200ms (p75).
8. **Tema:** 3 katmanlı semantic design token mimarisi (primitive→semantic-role→component), `data-theme` + `prefers-color-scheme`; component asla ham hex kullanmaz. **Mevcut `styles.css` şu an bunu karşılamıyor** — yalnız 6 düz `--ui-*` token var, açık tema/`[data-theme]` bağlamı hiç yok; bu Faz 11'in somut ilk kod adımı.
9. **Bilinçli dışarıda bırakılan:** yüksek-kontrast/ekran-okuyucu erişilebilirliği (Faz 9/F30'da ayrı izleniyor; rapor yalnız yapısal ARIA desenlerini kullandı, kontrast/NVDA/JAWS puanlamasını değil).
Teslim: 5-bölüm dağıtım + form ailesi/disclosure + bot sihirbazı + bot tablosu/context + 5-kanal bildirim + pencere-render/lazy/transition (F11.2–F11.7, gate F11 PASS).

## Faz 12 — Birleşik bot deneyimi + terminoloji/i18n (KAPALI, LOCAL, gate F12 PASS)
6/6 dilim kapalı: 12.1 mum+hacim+canlı grafik (saf SVG, harici lib yok) → 12.5 tek-XML i18n (TR/EN takma-ad) → 12.2 birleşik sihirbaz → 12.3 küme B bağlantısı (salt okunur) → 12.4 webhook görünümü → 12.6 temizlik. Kanıt: `evidence/F12/SONUC.md`.

## Faz 13 — TradingView sinyal entegrasyonu (KAPALI, LOCAL, gate F13 PASS)
13.1–13.5 kapalı: static-token webhook + durable dedup + fast-ACK/bind + HMAC internal hat + native indikatörler. Kanıt: `evidence/F13/SONUC.md`.

## Faz 14 — İleri backtest: overfitting direnci + ölçekleme (KAPALI, LOCAL, gate F14 PASS)
14.1–14.6 kapalı: embargo + CPCV + PBO/DSR (izole `analytics/`) + sweep orkestratörü + sampler. Kanıt: `evidence/F14/SONUC.md`.

## Ölü/bağlanmamış kod envanteri (2026-09-21 tarama + 12.3/12.6 güncellemesi)
Küme B (9) 12.3'te bağlandı. `bootstrap`/`domain.math`/`store` ERİŞİLİYOR (üretim+tools) → silinmedi. `canary_policy`/`live_gate` test-only netleşti. Geri kalan bilinçli araştırma kodu (Faz 5/9 DEFERRED). Liste: `docs/ARASTIRMA_UI_TERMINOLOJI_I18N_FAZ12.md` §1.

## Faz 15 — Görsel düzeltme + terminoloji + 8-referans minimum özellik listesi (2026-09-21, AÇIK, onay bekliyor)
Faz 12 checker/vitest/gate PASS oldu ama canlı ekranda görsel/akış benzerliği yoktu; ayrıca ExitPanel.tsx/TwoLegPanel.tsx (Futures TP/SL/Trailing + Hedge Bot ekranları) Faz 12.5'in i18n taramasını hiç görmemiş (0 `t()` çağrısı). 8 referans görselin tamamı tek tek çıkarılıp 30 maddelik minimum özellik listesi çıkarıldı — DCABOT'un olup referanslarda olmayan özellikleri (exact-math, PBO/DSR, replay) aynı görsel dilde rozet olarak gömülüyor, referansların olup DCABOT'ta olmayanları (segmented/slider/stepper kontroller, indikatör formu, Optimize→sweep bağlantısı, risk toggle'ları) dilimlere bölündü. Motor sözleşmesini etkileyen maddeler (DCA Mode, Order type, Stop Trigger vb.) Faz 15 dışı bırakıldı, ayrı karar gerekir. Zorunlu yeni kural: her dilim gerçek ekran-görüntüsü kanıtı olmadan kapanamaz. Tam liste+terminoloji sözlüğü+dilim planı: `docs/ARASTIRMA_FAZ15_GORSEL_DUZELTME.md`. **Implementasyona geçilmedi.**
