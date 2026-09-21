# Yol haritası

İki bağımsız eksen var. (1) **Venue ekseni** (bağlayıcı sıra): P1 yerel demo → P2 Binance testnet → P3 gerçek Binance (sınırlı canary) → P4 diğer borsalar. (2) **Özellik ailesi ekseni** (Faz 5-8, 2026-09-21'de dondurmadan çıkarıldı): her aile kendi sözleşme olgunluğuna göre venue eksenine PARALEL ilerler — mainnet'i (P3/P4) beklemez, ama kendi kanıt kapısını (aşağıda) geçmeden implementasyona geçmez. Bir sonraki faza geçmek için önceki fazın kapanış ölçütü sağlanır. Eski dilim günlükleri: `docs/archive/history/`.

## Şimdi
- **Faz 3 (P2 testnet) tamamen kapandı — `p2-testnet-complete` etiketlendi.** Sıradaki iş TASK.md'dedir (Faz 4, 5, 9 ve 10 kapsam/sıra kararları Arda'yı bekliyor).
- **En az sürtünmeli başlangıç noktaları** (dış araştırma kutusu zaten kapalı, doğrudan yerel implementasyon+test ile başlanabilir): **Faz 7** (rebalancing+signal bot), **Faz 9/F27** (paper trading), **Faz 10/F20** (strateji şablonu).

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

## Faz 4 — P3: gerçek Binance, sınırlı canary (taslak; P2 bitince ayrıntılanır)
Arda'nın açık onayı olmadan mainnet emri yok. Küçük sabit tutar üst sınırı, kill-switch, günlük kayıp limiti. Canary süresi ve başarı ölçütü (işlem sayısı, sıfır duplicate, çözülmemiş UNKNOWN yok) baştan yazılır. Paketleme ve tek-worker sınırı bu fazda ele alınır. P4 (diğer borsalar) P3 sonrası planlanır.

## Faz 5-10 — dondurulmuş + yeni istenen aileler (2026-09-21, Arda: "tüm kapalı olanları aç" → gap-analizi → "tüm kodu tara")
Sıra: derin kod incelemesine (bağımsız ajan, salt-okunur) dayalı olgunluk. Her madde implementasyona geçmeden önce kendi `DEFERRED/NO-GO`/`PLAN`/`BLOCKED` sözleşme boşluğunu kapatan bir araştırma kutusu gerektirir (AGENTS.md, ≤1 oturum) — **kanıtsız implementasyona geçilmez**. Dış kaynak: `docs/P1_KRITIK_ARASTIRMA_FINAL/` (GPT-5.6 Sol, 2026-09-09, 48 kaynak/74 iddia, VERIFIED/CONDITIONAL/BLOCKED/LOCAL_CODE_REQUIRED sınıflı) taranıp her maddeye eşlendi — bazı maddelerde dış araştırma kutusu artık **kapalı** (yalnız yerel implementasyon+test kaldı), bazılarında hâlâ **açık** (venue-profili seçimi, concurrency/transaction boundary gibi yerel mimari kararlar dış kaynaktan çözülemez). Tam eşleme + claim ID'leri: docs/KARARLAR.md 2026-09-21 "Faz 5-8 açılış" + "Faz 9-10 açılış" + "Dış araştırma paketi eşlemesi".

1. **Faz 5 — Futures Grid + Reverse/Infinity (F14, F12/F13):** en olgun kod (1257+17+7 dosya, 57+ test). Kaynak: `09_P1.12_FUTURES_MODEL.md`+`10_P1.13_GRID_FAMILIES.md` (S15-S22 Bybit/Binance resmi P&L/funding/margin/grid dokümantasyonu). PnL/funding/mark ayrımı formülleri `VERIFIED` — doğrudan kullanılabilir. **Liquidation formülü hâlâ `BLOCKED`** (CLM-112-06: "venue/product/mode/version profili seçilip donmadan ACCEPT edilemez"), Reverse/Infinity semantics `NOT_VERIFIED` (CLM-113-04). **Araştırma kutusu hâlâ açık** (LCR-12: venue-profili seçimi + local Position/Margin owner kanıtı); ayrıca ayrı Futures mutation katmanı gerekir.
2. **Faz 6 — two-leg/hedge (F18/F34):** identity+fill-projection tamam. Kaynak: `12_P1.15_HEDGE_CROSS_TWO_LEG.md` (S23/S24 Bybit hedge-mode/reduce-only). Hedge/netting kavramı `VERIFIED`. **Persistence/recovery hâlâ `LOCAL_CODE_REQUIRED`** (CLM-115-05, LCR-09: timeout/recovery/partial-hedge ownership) — roadmap'in "hiç yazılmamış" tespitiyle örtüşüyor, araştırma kutusu açık.
3. **Faz 7 — rebalancing (F17) + signal bot (F19):** Kaynak: `11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md` (S30 Binance Rebalancing Bot FAQ, S33 warmup, S38 dedupe). Tüm claim'ler `VERIFIED/CONDITIONAL+ACCEPT`, **sıfır blocker**. **Dış araştırma kutusu KAPALI** — sıradaki adım doğrudan yerel implementasyon+test, yeni araştırma gerekmiyor.
4. **Faz 8 — çoklu bot/pair (F05) + LLM dış-parça (F32):** F05 için dış kaynakta hiçbir kart yok — tamamen araştırılmamış, en ham. F32'nin "LLM read-only, ekonomik olay üretemez" ilkesi `15_P1.18_EXPLANATION_NOTIFICATIONS.md`'de `CONDITIONAL+ACCEPT`.

## Faz 9 — P1 kapanış borcu (2026-09-21)
1. **F27 paper trading:** en olgun. Kaynak: `14_P1.17_SIMULATED_RUNTIME.md` (S38-40 Coinbase/Bybit WS feed-ordering). CLM-G05 `VERIFIED`, sıfır blocker. **Dış araştırma kutusu KAPALI** — kalan iş yalnız gerçek REST/WS transport + activation gate.
2. **F31 shared-account bulk actions:** Kaynak: `05_P1.08`+`08_P1.11` (S08-09 SQLite WAL, S19-20 Bybit UTA). **Concurrency/transaction boundary hâlâ `LOCAL_CODE_REQUIRED+DEFER`** (CLM-111-02) — araştırma kutusu açık.
3. **F09 trailing breakeven:** Kaynak: `07_P1.10_TP_SL_TRAILING.md` (S25-26 Bybit TP/SL+trailing ratchet). Trigger/execution ayrımı+ratchet `VERIFIED`. **Cancel-replace geç-fill hâlâ `LOCAL_CODE_REQUIRED`** (CLM-110-04, LCR-07) — araştırma kutusu kısmen açık.
4. **F30 erişilebilirlik:** Kaynak: `16_P1.19_UX_ACCESSIBILITY_INSTALL.md` (S41-42 WCAG 2.2/reflow). WCAG kriterleri `VERIFIED`. NVDA/JAWS/HCM ve light theme paket kapsamında hiç yok — tamamen yeni yerel iş; Windows offline install ayrıca `LOCAL_CODE_REQUIRED` (LCR-10/11).

## Faz 10 — yeni istenen aileler (2026-09-21)
1. **F20 strateji şablonu:** Faz 7 ile aynı kaynak (`11_P1.14`), aynı sonuç — template authority/integrity `CONDITIONAL+ACCEPT`, blocker yok, **araştırma kutusu kapalı**.
2. **F36 audit/export/backup/restore**, **F40 zaman çizgisinde replay** (domain-seviye replay altyapısı var, kullanıcı timeline'ı yok), **F35 çoklu settlement** (mimari olarak USDT'ye kilitli tasarım kararı) — dış kaynakta doğrudan kart yok, yerel tasarım kararı gerekiyor.
3. **F16, F28, F29, F33, F39:** sıfır kod, dış kaynakta da kart yok — en ham, hepsi `PLAN`.

## Belge düzeltmeleri (2026-09-21)
F22 (kayıtlı koşu/kıyas/log-chart) matriste stale `PLAN` kaydediliydi; gerçekte Faz 2.3/2.4 ile teslim edilmiş — `docs/OZELLIK_MATRISI.md` düzeltildi, yalnız CSV/JSON export `PLAN` kaldı.
