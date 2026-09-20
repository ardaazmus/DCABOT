# Yol haritası

Sıra bağlayıcıdır: P1 yerel demo → P2 Binance testnet → P3 gerçek Binance (sınırlı canary) → P4 diğer borsalar. Bir sonraki faza geçmek için önceki fazın kapanış ölçütü sağlanır. Eski dilim günlükleri: `docs/archive/history/`.

## Şimdi
- **Faz 2.1 — demo akışı denetimi:** Faz 1 tamamlandı; aktif iş TASK.md'dedir.

## Sonra
Faz 2 (P1 kapanışı) → Faz 3 (gerçek testnet) → Faz 4 (canary).

## Dondurulmuş (P1'i bekletmez; kod var, arayüze bağlanmadan yeni sözleşme yazılmaz)
Futures Grid, Reverse/Infinity Grid, two-leg/hedge, rebalancing, signal bot, çoklu bot/pair, LLM açıklayıcı asistan.

## Faz 0 — Temizlik (tamam)
Kural reformu, belge/kanıt arşivi, boyut kapısı. Yeni oturum yalnız AGENTS + STATE + TASK okuyarak doğru işi seçebilmeli.

## Faz 1 — Kod borcu
Açık hata raporu maddelerini doğrula ve kapat (TASK.md). Çıkış: rapor boş, tam checker + frontend testleri yeşil. `engine.py:292` tek-deal sınırı docs/KARARLAR.md'de belgelidir.

## Faz 2 — P1'i gerçekten kapat
Ürün akışı: veri seç → kalite raporu → bot kur → parasal etkiyi önizle → geçmişi çalıştır → grafikten olayları incele → kaydet → kapat/aç → aynı sonucu yeniden üret.
1. **2.1 Demo akışı denetimi:** 9 adımı arayüzden elle yürüt; her adım için `çalışıyor / kısmen / yok` tablosu çıkar. Bu tablo Faz 2'nin gerçek iş listesidir.
2. **2.1b Sıralı deal:** Tek-deal çekirdek değişmezini koruyarak, tamamlanan deal sonrasında yeni `State`/`deal_id` ile üst katman döngüsünü tasarla; implementasyon ve iki-deal oracle onay sonrasına bağlıdır.
3. **2.2 Ekonomik metrik seti v1:** net PnL, max drawdown, işlem sayısı, ortalama giriş, toplam ücret, pozisyonda kalma süresi. Hesap çekirdekte, UI göstermekle yetinir.
4. **2.3 Reproduce + compare:** kayıtlı run'ı aynı config ve veriyle yeniden çalıştır, sonuç hash'i eşit çıksın; iki run yan yana karşılaştırılsın.
5. **2.4 Etkileşimli marker:** grafikte olay → hesap kaydı bağlantısı.
6. **2.5 Stress modeli:** yalnız 2.1–2.4 bittikten sonra, sınırlı tek dilim.

Kapanış: temiz klonda README komutlarıyla 9 adımlık akış hatasız çalışır → bağımsız review APPROVED → `git tag p1-demo-complete`.

## Faz 3 — P2: gerçek Binance testnet
Her dilim `evidence_scope=REAL_TESTNET` üretmiyorsa iş sayılmaz.
1. **3.1 Reconnect worker** (user data stream): bağlan, düş, yeniden bağlan; gap tespiti. Kanıt: ağı kes/aç, `GAP → RECONCILIATION_REQUIRED → SYNCED` gerçek olay akışıyla görülür.
2. **3.2 REST catch-up:** gap sonrası açık emir/işlem sorgusuyla snapshot.
3. **3.3 Salt-okunur hesap ekranı:** bakiye ve açık emirler, "TESTNET" rozetiyle.
4. **3.4 Mutation gate kararı** (belge, kod değil): hangi koşulda emir gider? Onay ekranı, tutar limiti, kill-switch, idempotent clientOrderId. Arda onaylar.
5. **3.5 Tek testnet emri:** limit emir gönder → gör → iptal et; journal kaydı.
6. **3.6 Dolum + restart kurtarma:** süreç ortada öldürülür, yeniden başlayınca tek ekonomik kayıt.
7. **3.7 DCA botu testnet'te uçtan uca:** base + 1–2 safety + TP.

Arda'nın yapacakları: testnet API anahtarı üretip yerelde kaydetmek (`tools/configure_testnet_credential.py`; repoya girmez), 3.4 kararı, 3.5+ için yerelde çalıştırmak. Kapanış: 3.7 PASS + bağımsız review → `git tag p2-testnet-complete`.

## Faz 4 — P3: gerçek Binance, sınırlı canary (taslak; P2 bitince ayrıntılanır)
Arda'nın açık onayı olmadan mainnet emri yok. Küçük sabit tutar üst sınırı, kill-switch, günlük kayıp limiti. Canary süresi ve başarı ölçütü (işlem sayısı, sıfır duplicate, çözülmemiş UNKNOWN yok) baştan yazılır. Paketleme ve tek-worker sınırı bu fazda ele alınır. P4 (diğer borsalar) P3 sonrası planlanır.
