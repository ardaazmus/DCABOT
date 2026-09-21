# Yol haritası

İki bağımsız eksen var. (1) **Venue ekseni** (bağlayıcı sıra): P1 yerel demo → P2 Binance testnet → P3 gerçek Binance (sınırlı canary) → P4 diğer borsalar. (2) **Özellik ailesi ekseni** (Faz 5-8, 2026-09-21'de dondurmadan çıkarıldı): her aile kendi sözleşme olgunluğuna göre venue eksenine PARALEL ilerler — mainnet'i (P3/P4) beklemez, ama kendi kanıt kapısını (aşağıda) geçmeden implementasyona geçmez. Bir sonraki faza geçmek için önceki fazın kapanış ölçütü sağlanır. Eski dilim günlükleri: `docs/archive/history/`.

## Şimdi
- **Faz 3 (P2 testnet) tamamen kapandı — `p2-testnet-complete` etiketlendi.** Sıradaki iş TASK.md'dedir (Faz 4, 5, 9 ve 10 kapsam/sıra kararları Arda'yı bekliyor).

## Sonra
Faz 4 (canary, venue ekseni) · Faz 5-8 (dondurulmuş aileler, açık) · Faz 9 (P1 kapanış borcu) · Faz 10 (yeni aileler) — hepsi birbirinden bağımsız, paralel yürüyebilir; hiçbiri mainnet'i (P3/P4) beklemez.

## Faz 0 — Temizlik (tamam)
Kural reformu, belge/kanıt arşivi, boyut kapısı. Yeni oturum yalnız AGENTS + STATE + TASK okuyarak doğru işi seçebilmeli.

## Faz 1 — Kod borcu
Açık hata raporu maddelerini doğrula ve kapat (TASK.md). Çıkış: rapor boş, tam checker + frontend testleri yeşil. `engine.py:292` tek-deal sınırı docs/KARARLAR.md'de belgelidir.

## Faz 2 — P1'i gerçekten kapat
Ürün akışı: veri seç → kalite raporu → bot kur → parasal etkiyi önizle → geçmişi çalıştır → grafikten olayları incele → kaydet → kapat/aç → aynı sonucu yeniden üret.
1. **2.1 Demo akışı denetimi (tamam):** 9 adım arayüzden uçtan uca doğrulandı (TASK.md, STATE.md).
2. **2.1b Sıralı deal (tamam):** Orkestrasyon düzeltmesi + `deal_id`/`event_sequence` dedup kimliği + persistence çoklu-deal şeması uygulandı, çekirdek/engine.py değişmedi (bkz. STATE.md/docs/KARARLAR.md).
3. **2.2 Ekonomik metrik seti v1 (tamam):** net PnL, max drawdown, işlem sayısı, ortalama giriş, toplam ücret, pozisyonda kalma süresi — çekirdekte (`report()`) ve `historical_simulation.py`'de hesaplanıp hem canlı hem kayıtlı API yanıtında gösteriliyor (bkz. STATE.md).
4. **2.3 Reproduce + compare (tamam):** `POST /api/historical-runs/{run_id}/reproduce` kayıtlı run'ı stored config/dataset snapshot'ıyla yeniden çalıştırıp result/canonical-input/execution-identity hash'lerini karşılaştırır; yerel artifact değiştiyse fail-closed reddeder. Saved Runs ekranında iki koşu seçilip yan yana karşılaştırılabiliyor (bkz. STATE.md).
5. **2.4 Etkileşimli marker (tamam):** grafikte olay ↔ tablo satırı çift yönlü bağlantı, mouse + klavye (bkz. STATE.md).
6. **2.5 Stress modeli (tamam — dar kapsam):** P1.16.i.b araştırması bağımsız kontrolde iki yerde çelişkili çıktı verdi (T-07 sayısal, T-12 identity) ve reserve örneği kendi invariant'ını ihlal etti; bu yüzden yeni spread/latency/queue/reserve stress modeli `NO-GO` kaldı. Bunun yerine yalnız mevcut exact `config.slippage` mekanizmasıyla ikinci, açık şekilde etiketlenmiş bir "stress slippage" profili eklendi (`historical_demo_btcusdt_1h_stress_slippage_v1`, slippage=0.002); yeni ekonomik kod yok, mevcut profil seçici + mevcut compare ekranı üzerinden kullanılıyor (bkz. STATE.md, docs/KARARLAR.md).

Kapanış (tamam, 2026-09-20): temiz klonda (gerçek `git clone`, kalıcı config değişikliği yok) README komutlarıyla 9 adımlık akış hatasız çalıştı (indir/doğrula → kalite → bot kur → önizle → koş → grafikten incele → kaydet → kapat/aç → reproduce ile aynı hash) → bağımsız review `APPROVED_WITH_FINDINGS` (Codex/muse, `evidence/P1_CLOSURE_INDEPENDENT_REVIEW_2026_09_20/SONUC.md`; tek eyleme dönüşen bulgu — click-bubbling kozmetik hata — Claude tarafından aynı gün düzeltildi ve doğrulandı) → `git tag p1-demo-complete` atıldı.

## Faz 3 — P2: gerçek Binance testnet (tamam, `p2-testnet-complete`)
Ana dosyalar: `application/user_stream_reconnect_worker.py`, `rest_catch_up.py`, `testnet_order_execution.py` (mutation gate, 7 kural), `data_adapters/binance_testnet_order_execution.py` (mutation yapabilen TEK dosya), `application/testnet_dca_session.py` (DCA orkestrasyonu). 3.1/3.5/3.6 tam REAL_TESTNET, 3.2/3.7 kısmi. Bağımsız review `APPROVED_WITH_FINDINGS` — 2 bulgu (cancel'in AttemptStore disiplininden geçmemesi, UNKNOWN attempt'in yeni mutation'ı bloklamaması) aynı gün düzeltildi, 9 yeni test. Tüm bulgular/bug'lar/kanıtlar: docs/KARARLAR.md (tarih sırasıyla, 2026-09-20/21).

## Faz 4 — P3: gerçek Binance, sınırlı canary (taslak; P2 bitince ayrıntılanır)
Arda'nın açık onayı olmadan mainnet emri yok. Küçük sabit tutar üst sınırı, kill-switch, günlük kayıp limiti. Canary süresi ve başarı ölçütü (işlem sayısı, sıfır duplicate, çözülmemiş UNKNOWN yok) baştan yazılır. Paketleme ve tek-worker sınırı bu fazda ele alınır. P4 (diğer borsalar) P3 sonrası planlanır.

## Faz 5-8 — Dondurulmuş özellik aileleri açıldı (2026-09-21, Arda: "tüm kapalı olanları aç")
Sıra: derin kod incelemesine (bağımsız ajan, salt-okunur) dayalı olgunluk — en kanıtlı/en az eksik önce. Her fazın ilk adımı kendi `DEFERRED/NO-GO`/`PLAN` sözleşme boşluğunu kapatan bir araştırma kutusu (AGENTS.md, ≤1 oturum) — kanıtsız implementasyona geçilmez. Tam dosya/satır envanteri ve engel detayı: docs/KARARLAR.md 2026-09-21 "Faz 5-8 açılış".

1. **Faz 5 — Futures Grid + Reverse/Infinity varyantı (F14, F12/F13):** en olgun — `futures_grid_*.py`(10 dosya/1257 satır) + `futures_dca_*.py`(17+7 dosya), 57+ test; implementation `DEFERRED/NO-GO`, API/UI yok. Engel: venue liquidation/funding exact oracle yok. Ayrı Futures venue/mutation katmanı gerekir (P2'nin Spot gate'i doğrudan taşınmaz).
2. **Faz 6 — two-leg/hedge (F18/F34):** identity+fill-projection tamam, persistence/replay/recovery hiç yazılmamış (`P1.15.c DEFERRED/NO-GO`) — net sonraki adım.
3. **Faz 7 — rebalancing (F17) + signal bot (F19):** küçük/temiz matematik-kimlik katmanları var, asset-conversion/fee/order-binding (rebalancing) ve auth/replay/webhook (signal bot) `PLAN`.
4. **Faz 8 — çoklu bot/pair (F05) + LLM açıklayıcı asistan dış-LLM kısmı (F32):** sıfır kod/test, yalnız `PLAN` — en ham. (F32'nin rule-based kısmı zaten P1'de bağlı; bu yalnız dış-LLM önerisini kapsar.)

## Faz 9 — P1 kapanış borcu (2026-09-21, tam envanter docs/KARARLAR.md'de)
P1'in kendi kapsamında olup kapanışta unutulmuş, kısmen bitmiş 4 madde. Olgunluk sırası:
1. **F27 — Canlı fiyatla paper trading:** en olgun — normalization/replay/capability-research katmanı `COMPLETE_WITH_LIMITATION/RESEARCH_AUDITED`; yalnız transport activation gate (`P1.17.j`) kasıtlı kapalı, gerçek REST/WS adapter + simulated emir/fill `PLAN`.
2. **F31 — Bot lifecycle/shared-account bulk actions:** tekli lifecycle tamam; paylaşılan hesapta ownership/isolation (`P1.11.a/e`) `DEFERRED/NO-GO`, cross-deal isolation + toplu işlemler `PLAN`.
3. **F09 — Trailing TP/SL breakeven kuyruğu:** çekirdek ratchet/exit-binding tamam (API/UI yok); breakeven, OCO/cancel-replace/late-fill, public sözleşmeler `DEFERRED/NO-GO`.
4. **F30 — Erişilebilirlik kuyruğu:** light theme exact palette kararı bekliyor; NVDA/JAWS/HCM `NOT_RUN` — hiç koşulmamış.

## Faz 10 — Yeni istenen aileler (2026-09-21, hiçbir fazda hiç yer almamıştı)
9 madde, olgunluk sırasıyla; tam envanter docs/KARARLAR.md'de:
1. **F20 — Strateji şablonu/kopyalama/paylaşma:** canonical snapshot/hash + onay kapısı `COMPLETE_WITH_LIMITATION`, aktivasyon/profile-binding/import-export/paylaşım/UI `PLAN`.
2. **F36 — Audit/export/backup/restore:** append-only journal audit alt kümesi var, gerçek backup/restore hiç yok.
3. **F40 — Zaman çizgisinde replay step/seek/speed:** domain-seviye event replay altyapısı var (`futures_dca_core_replay_*.py`), kullanıcıya dönük timeline/scrubber hiç yok.
4. **F35 — Çoklu settlement/fee varlığı:** mimari olarak tek-varlığa (USDT) kilitli tasarım kararı — genişletme ayrı bir tasarım gerektirir.
5. **F16, F28, F29, F33, F39 — eşit derecede ham:** dönemsel alım, dashboard/risk bütçesi, grafik-üstü plan düzenleme, uyarı/bildirim merkezi, hesaplanabilir risk açıklaması — hiçbirinde kod yok, hepsi `PLAN`.

## Belge düzeltmesi (2026-09-21)
F22 (kayıtlı koşu/kıyas/log-chart) matriste stale `PLAN` kaydediliydi; gerçekte Faz 2.3/2.4 ile teslim edilmiş. `docs/OZELLIK_MATRISI.md` güncellendi — yalnız CSV/JSON export hâlâ `PLAN`.
