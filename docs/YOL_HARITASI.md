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
Her dilim `evidence_scope=REAL_TESTNET` üretmiyorsa iş sayılmaz.
1. **3.1 Reconnect worker** (user data stream): bağlan, düş, yeniden bağlan; gap tespiti. **Kod tamam, offline doğrulandı; REAL_TESTNET kanıtı Arda'yı bekliyor** (bkz. TASK.md). `src/dcabot/application/user_stream_reconnect_worker.py` mevcut `BinanceTestnetUserDataStream` (tek bağlantı, kasıtlı reconnect'siz) ile mevcut `ReconciliationCoordinator`'ı (offline state machine) sınırlı, deterministic backoff'la (varsayılan 1/2/4/8/16 sn, en fazla 5 deneme) birbirine bağlar; hem `connect()` hem `recv()` hatası aynı sayaç+backoff yoluna girer (backoff'suz sıkı döngü riski yok). SYNCED'e ulaşmak 3.2'nin (REST catch-up) authoritative snapshot'ını gerektirdiği için 3.1'in kanıtladığı gerçek yay `CONNECTED_READ_ONLY → (düş) → STALE → (backoff+reconnect) → RECONCILIATION_REQUIRED → (gerçek gap varsa) → GAP` — roadmap'in "bağlan, düş, yeniden bağlan; gap tespiti" cümlesiyle birebir. Test: `tests/test_user_stream_reconnect_worker.py` (6 test — happy path, disconnect+reconnect, gerçek out-of-order/gap, bounded retry tükenmesi, constructor doğrulaması). Canlı çalıştırma aracı: `tools/run_user_stream_reconnect_worker.py <credential_id>` — Claude bunu hiç çalıştırmaz/çalıştıramaz (gerçek ağ + Arda'nın yerel credential'ı gerekir); Arda `tools/configure_testnet_credential.py` ile credential'ı kaydettikten sonra bu scripti çalıştırıp ağı kesip/açarak transition log'unu (`DISCONNECTED`/`RECONNECTING`/`RECONNECTED`, varsa `GAP`) gözlemler.
2. **3.2 REST catch-up:** gap sonrası açık emir/işlem sorgusuyla snapshot. **Kod tamam, offline doğrulandı; REAL_TESTNET kanıtı kısmi** — sorgu mekaniği gerçek venue'ya karşı doğrulanabilir (`tools/run_order_status_lookup_diagnostic.py`), ama gerçek bir "kesintiye uğramış emir" senaryosu için 3.5 (emir gönderme) gerekiyor; tam uçtan uca REAL_TESTNET kanıtı 3.5 sonrası tamamlanacak. `src/dcabot/application/rest_catch_up.py`: blocking attempt'leri (`AttemptStore.list_resolvable_attempts` — yeni, yalnız UNKNOWN/RECONCILING; UNRESOLVED kasıtlı hariç çünkü `can_transition` ona çıkış kenarı vermiyor) mevcut `reconcile_attempt`'e signed WS-API sorgusuyla besler, hepsi çözülünce `apply_authoritative_snapshot`'ı gerçek bir cursor'la (`ReconciliationCoordinator.last_accepted_event` — yeni salt-okunur property) çağırır. Yeni: `query_binance_testnet_order_status_by_client_id` (venue_order_id hiç gelmemiş SENDING→UNKNOWN attempt'ler için — asıl kritik durum bu, mevcut `orderId`-tabanlı sorgu bunu çözemiyordu) ve her iki sorguda `-2013` (order not found) artık exception değil `OrderLookup.not_found()` döndürüyor.
3. **3.3 Salt-okunur hesap ekranı:** bakiye ve açık emirler, "TESTNET" rozetiyle. **Backend tamam, offline+kısmi canlı doğrulandı; frontend paneli sırada** (bkz. TASK.md). `binance_testnet_account.py` genişletildi: `fetch_binance_testnet_account` artık sıfır olmayan gerçek testnet bakiyelerini (`asset/free/locked`, exact decimal, mainnet değil) döndürüyor (önceki P2.05 kapısı yalnız public exchangeInfo'yu kapsıyordu, signed account hiç kabul kapısından geçmemişti); yeni `fetch_binance_testnet_open_orders` (`GET /api/v3/openOrders`, signed, bounded, redakte). Yeni API uç noktaları: `GET /api/testnet/account`, `GET /api/testnet/open-orders` — ikisi de `DCABOT_TESTNET_CREDENTIAL_ID` env değişkeni ayarlı değilse `409 TESTNET_CREDENTIAL_NOT_CONFIGURED` ile fail-closed. Canlıda `/api/health` ve OpenAPI şeması üzerinden doğrulandı (credential ayarlanmadan, gerçek credential'a Claude dokunmadı).
4. **3.4 Mutation gate kararı** (belge, kod değil): hangi koşulda emir gider? Onay ekranı, tutar limiti, kill-switch, idempotent clientOrderId. Arda onaylar.
5. **3.5 Tek testnet emri:** limit emir gönder → gör → iptal et; journal kaydı.
6. **3.6 Dolum + restart kurtarma:** süreç ortada öldürülür, yeniden başlayınca tek ekonomik kayıt.
7. **3.7 DCA botu testnet'te uçtan uca:** base + 1–2 safety + TP.

Arda'nın yapacakları: testnet API anahtarı üretip yerelde kaydetmek (`tools/configure_testnet_credential.py`; repoya girmez), 3.4 kararı, 3.5+ için yerelde çalıştırmak. Kapanış: 3.7 PASS + bağımsız review → `git tag p2-testnet-complete`.

## Faz 4 — P3: gerçek Binance, sınırlı canary (taslak; P2 bitince ayrıntılanır)
Arda'nın açık onayı olmadan mainnet emri yok. Küçük sabit tutar üst sınırı, kill-switch, günlük kayıp limiti. Canary süresi ve başarı ölçütü (işlem sayısı, sıfır duplicate, çözülmemiş UNKNOWN yok) baştan yazılır. Paketleme ve tek-worker sınırı bu fazda ele alınır. P4 (diğer borsalar) P3 sonrası planlanır.
