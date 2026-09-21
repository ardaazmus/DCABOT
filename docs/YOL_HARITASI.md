# Yol haritası

İki bağımsız eksen var. (1) **Venue ekseni** (bağlayıcı sıra): P1 yerel demo → P2 Binance testnet → P3 gerçek Binance (sınırlı canary) → P4 diğer borsalar. (2) **Özellik ailesi ekseni** (Faz 5-8, 2026-09-21'de dondurmadan çıkarıldı): her aile kendi sözleşme olgunluğuna göre venue eksenine PARALEL ilerler — mainnet'i (P3/P4) beklemez, ama kendi kanıt kapısını (aşağıda) geçmeden implementasyona geçmez. Bir sonraki faza geçmek için önceki fazın kapanış ölçütü sağlanır. Eski dilim günlükleri: `docs/archive/history/`.

## Şimdi
- **P4 hariç TÜM FAZLAR kapalı** (Faz 1+3+4+5+6+7+8+9+10+11, F11.1+F27+F20). Kalan: bağımsız inceleme + Arda kararları (canary değerleri, dış LLM, NVDA/JAWS/HCM).
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

## Faz 5-10 — dondurulmuş + yeni istenen aileler (2026-09-21, Arda: "tüm kapalı olanları aç" → gap-analizi → "tüm kodu tara")
Sıra: derin kod incelemesine dayalı olgunluk. Her madde implementasyona geçmeden önce kendi `DEFERRED/NO-GO`/`PLAN`/`BLOCKED` sözleşme boşluğunu kapatan bir araştırma kutusu gerektirir (AGENTS.md, ≤1 oturum) — **kanıtsız implementasyona geçilmez**. Dış kaynak: `docs/P1_KRITIK_ARASTIRMA_FINAL/` (2026-09-09, 48 kaynak) her maddeye eşlendi. Tam eşleme + claim ID'leri: docs/KARARLAR.md 2026-09-21.

1. **Faz 5 — Futures Grid + Reverse/Infinity (F14, F12/F13):** en olgun kod (1257+17+7 dosya, 57+ test). PnL/funding/mark formülleri `VERIFIED`; **liquidation `BLOCKED`** (CLM-112-06, venue-profili donmadan kapanmaz), Reverse/Infinity `NOT_VERIFIED`. Araştırma kutusu AÇIK (LCR-12); ayrı Futures mutation katmanı gerekir.
2. **Faz 6 — two-leg/hedge (F18/F34):** identity+fill-projection tamam, hedge/netting `VERIFIED`. **Persistence/recovery `LOCAL_CODE_REQUIRED`** (CLM-115-05, LCR-09) — araştırma kutusu AÇIK.
3. **Faz 7 — rebalancing (F17) + signal bot (F19):** tüm claim'ler `VERIFIED/CONDITIONAL+ACCEPT`, sıfır blocker. **Araştırma kutusu KAPALI** — doğrudan yerel implementasyon+test.
4. **Faz 8 — çoklu bot/pair (F05) + LLM dış-parça (F32):** F05 dış kaynakta yok, en ham. F32'nin "LLM read-only" ilkesi `CONDITIONAL+ACCEPT`.

## Faz 9 — P1 kapanış borcu (2026-09-21)
1. **F27 paper trading:** en olgun, CLM-G05 `VERIFIED`, sıfır blocker. **Araştırma kutusu KAPALI** — kalan iş yalnız gerçek REST/WS transport.
2. **F31 shared-account bulk actions:** concurrency/transaction boundary `LOCAL_CODE_REQUIRED+DEFER` (CLM-111-02) — AÇIK.
3. **F09 trailing breakeven:** trigger/execution+ratchet `VERIFIED`; cancel-replace geç-fill `LOCAL_CODE_REQUIRED` (CLM-110-04) — KISMEN AÇIK.
4. **F30 erişilebilirlik:** WCAG kriterleri `VERIFIED`. NVDA/JAWS/HCM ve light theme tamamen yeni yerel iş; Windows offline install `LOCAL_CODE_REQUIRED`.

## Faz 10 — yeni istenen aileler (2026-09-21)
1. **F20 strateji şablonu:** Faz 7 ile aynı kaynak/sonuç — blocker yok, **araştırma kutusu KAPALI**.
2. **F36 audit/backup**, **F40 timeline replay** (domain-replay altyapısı var, kullanıcı timeline'ı yok), **F35 çoklu settlement** (USDT'ye kilitli tasarım kararı) — yerel tasarım kararı gerekiyor.
3. **F16, F28, F29, F33, F39:** sıfır kod, en ham, hepsi `PLAN`.

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
