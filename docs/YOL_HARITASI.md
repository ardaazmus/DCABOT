# Yol haritası

İki bağımsız eksen var. (1) **Venue ekseni** (bağlayıcı sıra): P1 yerel demo → P2 Binance testnet → P3 gerçek Binance (sınırlı canary) → P4 diğer borsalar. (2) **Özellik ailesi ekseni** (Faz 5-8, 2026-09-21'de dondurmadan çıkarıldı): her aile kendi sözleşme olgunluğuna göre venue eksenine PARALEL ilerler — mainnet'i (P3/P4) beklemez, ama kendi kanıt kapısını (aşağıda) geçmeden implementasyona geçmez. Bir sonraki faza geçmek için önceki fazın kapanış ölçütü sağlanır. Eski dilim günlükleri: `docs/archive/history/`.

## Şimdi
- **P4 hariç TÜM FAZLAR kapalı** (Faz 1+3+4+5+6+7+8+9+10+11, F11.1+F27+F20). Kalan: Arda kararları (canary değerleri, dış LLM, NVDA/JAWS/HCM).
- **Yeni açılan, onay bekleyen (2026-09-21):** Faz 12 (UX/terminoloji/i18n), Faz 13 (TradingView sinyal), Faz 14 (ileri backtest) — detay aşağıda.
- **En az sürtünmeli** (dış kutu kapalı): **Faz 7**, **Faz 9/F27**, **Faz 10/F20**.

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
Arda'nın açık onayı olmadan mainnet emri yok. Teslim: tek-worker OS kilidi, saf canary politikası (cap/kayıp/pencere/sıfır-duplicate/sıfır-UNKNOWN), dosya kill-switch, kilitli canlı kapı, `tools/run_api.py` paketleme, DRAFT `config/canary.json`. Emir gönderilmedi. Açık: canary sayısal değerleri + onay formatı (Arda). P4 (diğer borsalar) P3 sonrası planlanır.

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

## Faz 12 — Birleşik bot deneyimi + terminoloji/i18n (2026-09-21, ayrıntılı plan hazır, onay bekliyor)
"Botlar & Stratejiler" 16 aracı tek sayfada diziyor + gerçek grafik yok + terminoloji sektörden (3Commas/Pionex/Bitsgap) kopuk. 6 alt-dilim: 12.1 chart altyapısı (lightweight-charts) → 12.5 tek-XML i18n (TR/EN, kod adları değişmeden takma-ad) → 12.2 BotWizard+Bot stüdyosu birleşimi (sektör terminolojisiyle) → 12.3 Grid Bot gerçek akışı (küme B'yi bağlar) → 12.4 sinyal/webhook görünümü (Faz 13 ile) → 12.6 küme C/F temizliği. Kapsam+terminoloji tablosu+i18n mimarisi: `docs/ARASTIRMA_UI_TERMINOLOJI_I18N_FAZ12.md`. **Implementasyona geçilmedi.**

## Faz 13 — TradingView sinyal entegrasyonu (2026-09-21, araştırma tamam, onay bekliyor)
`signal_intake.py`'de HMAC doğrulama + replay-window zaten yazılı/test edilmiş ama hiçbir endpoint'e bağlı değil. Kapsam ve kaynaklar: `docs/ARASTIRMA_ILERI_BACKTEST_SINYAL_KALITE.md` §1, §6.

## Faz 14 — İleri backtest: overfitting direnci + ölçekleme (2026-09-21, araştırma tamam, onay bekliyor)
`chronological_split.py`/`horizon_overlap.py`/`trial_registry.py`/`oos_lineage.py` CPCV/PBO/DSR'nin temel taşları ama embargo/kombinatoryal-path/skor katmanı yok; backtest tek-thread. Float/Fraction kararı KAPALI (float64, izole `analytics/` modülünde — §4). Kapsam ve kaynaklar: `docs/ARASTIRMA_ILERI_BACKTEST_SINYAL_KALITE.md` §2-4, §6.

## Ölü/bağlanmamış kod envanteri (2026-09-21, tek seferlik tarama)
158 modülden 70'i `api.py`/`tools/*.py`'den hiç import edilmiyor. Çoğu (62) bilinçli/belgeli araştırma kodu (Futures DCA 24, Futures Grid yürütme 9, venue mutabakat 26, overfitting-lineage 2 — Faz 5/9/14 DEFERRED'leriyle örtüşüyor). **Kritik:** `canary_policy.py`/`live_gate.py` hiç çağrılmıyor — "kilitli canlı kapı" ifadesi test-only netleştirilmeli. `bootstrap.py`/`domain/math.py`/`persistence/store.py` temizlik adayı. Tam liste: `docs/ARASTIRMA_UI_TERMINOLOJI_I18N_FAZ12.md` §1.
