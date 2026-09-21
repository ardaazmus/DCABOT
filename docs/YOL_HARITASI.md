# Yol haritası

Sıra bağlayıcıdır: P1 yerel demo → P2 Binance testnet → P3 gerçek Binance (sınırlı canary) → P4 diğer borsalar. Bir sonraki faza geçmek için önceki fazın kapanış ölçütü sağlanır. Eski dilim günlükleri: `docs/archive/history/`.

## Şimdi
- **Faz 2 (P1 kapanışı) tamamen kapandı — `p1-demo-complete` etiketlendi.** Sıradaki iş TASK.md'dedir (Faz 3 kapsam kararı Arda'yı bekliyor).

## Sonra
Faz 3 (gerçek testnet) → Faz 4 (canary).

## Dondurulmuş (P1'i bekletmez; kod var, arayüze bağlanmadan yeni sözleşme yazılmaz)
Futures Grid, Reverse/Infinity Grid, two-leg/hedge, rebalancing, signal bot, çoklu bot/pair, LLM açıklayıcı asistan.

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

## Faz 3 — P2: gerçek Binance testnet
Her dilim `evidence_scope=REAL_TESTNET` üretmiyorsa iş sayılmaz. Ayrıntılı uygulama notları docs/KARARLAR.md'de (tarih sırasıyla); burada yalnız durum ve ana dosyalar.
1. **3.1 Reconnect worker (tamam, REAL_TESTNET):** `application/user_stream_reconnect_worker.py`. Canlı testte gerçek bir bug (`ConnectionClosedError` yakalanmıyordu) bulundu, düzeltildi. Araç: `tools/run_user_stream_reconnect_worker.py`.
2. **3.2 REST catch-up (kod tamam, kısmi REAL_TESTNET):** `application/rest_catch_up.py`. Tam uçtan uca kanıt gerçek kesintiye uğramış bir attempt gerektiriyor — 3.5 başarıyla geçtiği için henüz oluşmadı. Araç: `tools/run_order_status_lookup_diagnostic.py`.
3. **3.3 Salt-okunur hesap ekranı (tamam):** backend `binance_testnet_account.py`, frontend `BinanceAccountPanel.tsx` (Codex/muse, dosya-sınırlı brief, Claude doğruladı). Uç noktalar: `GET /api/testnet/account`, `GET /api/testnet/open-orders`.
4. **3.4 Mutation gate kararı (tamam):** 7 kural onaylandı (kill-switch, `max_entry_notional`, execution-anında onay, idempotent clientOrderId + durable-before-send, tek eşzamanlı mutation, cancel aynı disiplin, testnet hard-code).
5. **3.5 Tek testnet emri (tamam, REAL_TESTNET):** `data_adapters/binance_testnet_order_execution.py` (mutation yapabilen TEK dosya), `application/testnet_order_execution.py` (7 kuralın kapısı). Gerçek döngü kanıtlandı (`venue_order_id=4423471`: NEW→FOUND→CANCELED). İki gerçek bug bulundu/düzeltildi (UNKNOWN/REJECTED ayrımı, `venue_error_code` işareti). Araç: `tools/run_single_testnet_order.py`.
6. **3.6 Dolum + restart kurtarma (tamam, REAL_TESTNET):** `AttemptStore.recover_after_restart` artık `PREPARED`/`PERSISTED`/`SENDING` hepsini kurtarıyor (bulundu: `can_transition` ilk ikisine çıkış vermiyordu — sonsuz kilitlenme riski, düzeltildi). `application/testnet_order_execution.py::recover_stuck_attempts` her oturum başında kalan attempt'leri gerçek sorguyla çözer. Elle Ctrl+C zamanlaması pratik olmadığı için `tools/run_single_testnet_order.py --simulate-crash-at {prepared,persisted,sending}` eklendi (gerçek `AttemptStore` geçişleri + `os._exit`). Kanıt: `PERSISTED`'de bırakılan attempt bir sonraki çalıştırmada `UNRESOLVED`'e çözüldü, yeni emir bloke olmadan geçti. Ayrıntı: docs/KARARLAR.md.
7. **3.7 DCA botu testnet'te uçtan uca (tamam, kısmi REAL_TESTNET — BASE bacağı canlı, SAFETY/EXIT offline):** base + safety + TP. Yeni icat değil — çekirdek `engine.py`'nin `State/apply/decision`'ı (Faz 2'nin de kullandığı aynı mekanizma) gerçek testnet mutation'larına bağlandı. `application/testnet_dca_session.py`: `place_next_action` (INTENT + gated gönder), `sync_order_fills` (yeni `fetch_binance_testnet_my_trades` ile exact dolum verisi, execution_id dedup, tam dolunca `ORDER_FINAL`). Bulundu: `engine.py` fee'nin her zaman quote-asset olmasını istiyor ama gerçek BUY dolumları (BNB indirimsiz) genelde base-asset ücret keser — aynı fill'in kendi fiyatıyla exact dönüştürülüyor, desteklenmeyen asset'te fail-closed. Offline test: tam BASE→SAFETY:1→EXIT döngüsü. Araç: `tools/run_testnet_dca_deal.py`. Bilinen sınır: deal state yalnız process belleğinde, restart'ta devam ettirilemez (attempt-seviyesi kurtarma hâlâ çalışır, ayrıntı docs/KARARLAR.md).

Arda'nın yapacakları: testnet API anahtarı üretip yerelde kaydetmek (`tools/configure_testnet_credential.py`; repoya girmez), 3.4 kararı, 3.5+ için yerelde çalıştırmak. Kapanış: 3.7 PASS + bağımsız review → `git tag p2-testnet-complete`.

## Faz 4 — P3: gerçek Binance, sınırlı canary (taslak; P2 bitince ayrıntılanır)
Arda'nın açık onayı olmadan mainnet emri yok. Küçük sabit tutar üst sınırı, kill-switch, günlük kayıp limiti. Canary süresi ve başarı ölçütü (işlem sayısı, sıfır duplicate, çözülmemiş UNKNOWN yok) baştan yazılır. Paketleme ve tek-worker sınırı bu fazda ele alınır. P4 (diğer borsalar) P3 sonrası planlanır.
