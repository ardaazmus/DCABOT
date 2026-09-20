# Karar defteri — DEMO_FIRST_1

Kullanıcının son ürün sırası önceki N serisi önerilerini değiştirir. Bu karar kaynak kodu veya eski yedeği değersiz kılmaz.

| ID | Karar | Önceki karara etkisi |
|---|---|---|
| ADR01 | Yeni kök + sabit yedek + kontrollü parça aktarımı | Korunur |
| ADR02 | P1 tam UI/demo; P2 Binance testnet; P3 Binance gerçek; P4 diğerleri | UI=N12 ve backtest=N13 sırası yürürlükten kalkar |
| ADR03 | Çekirdek ortak katman; demo/live/arayüz ekonomik motoru kopyalamaz | Korunur; ayrı microservice zorunlu değil |
| ADR04 | Tek long/tek deal sınırı CORE01 implementation sınırıdır | Nihai ürünü daraltan kapsam kararı kaldırılır; P1 özellik matrisi belirleyici |
| ADR05 | Gerçek geçmiş veri ilk üründe zorunlu; public ağ veri erişimi erken olabilir | Testnet bekleme koşulu kaldırılır |
| ADR06 | UI basit/uzman, tam kontrol ve analiz; salt read-only ekranla sınırlı değil | İlk ürün fonksiyonel çalışma alanıdır |
| ADR07 | Python çekirdek + FastAPI API + React/TypeScript UI hedefi | Minimal dependency/sürüm kilidi ilgili görevde eklenir |
| ADR08 | Mevcut exact hesap/Decimal sınır, dedup, UNKNOWN ve atomik journal | Korunur; yeni ürün modelleri ayrı testlerle genişler |
| ADR09 | SQLite tek makine başlangıcı; job/projection/schema planlı büyüme | Büyük tarihsel veri için ölçülen performans kapısı gerekir |
| ADR10 | Büyük faz bağımsız Codex review; odak review dikey UI işlerine eşlik eder | REVIEW_CORE01 geniş backend işi için UI'ı bekleten sıra kapısı değildir |
| ADR11 | Aktif kural AGENTS/STATE/TASK; tek özellik matrisi ve kanonik docs | Korunur; eski N/D görevleri aktif talimat sayılmaz |
| ADR12 | Veri modu ile execution modu ayrıdır; riskli mod yalnız açık yetki | Public veri bağlantısı canlı emir yetkisi açmaz |

Tam rakip eşdeğerliği, kâr üstünlüğü veya tamamlanmış UI bu belgeyle ilan edilmez. Kullanıcı hedefi kabul edilen bir ürün kapsamıdır; her gereksinim implementation/test kanıtıyla kapanır. Dış platforma bağımlı özellikler ayrıca görünürdür.

## 2026-09-20 — CORE01 tek-deal sınırı
- Karar: `State` tek-deal değişmezi ve “One base order per deal” kuralı çekirdekte kalır; nihai ürün kapsamını tek deal ile sınırlamaz.
- Gerekçe: `engine.py:292` BASE kolu yalnız taze, emirsiz `State` için geçerlidir; terminal emirler temizlenmez.
- Sonuç: deal bitince `global_new_risk_gate_open` kapanır; çekirdek aynı state içinde ikinci deal başlatmaz.
- Sınır: Çoklu deal üst katmanda sıralı deal olarak, yeni `State` ve yeni `deal_id` ile ele alınacaktır.
- Karar notu: Bu oturumda yalnız belgeleme yapıldı; `engine.py` değiştirilmedi.

## 2026-09-20 — Sıralı deal orkestrasyon düzeltmesi
- Karar: `historical_simulation.simulate_historical_ohlcv` deal kapanınca (`orders` dolu, `position.qty=0`, `unsettled` yok, `halted`/`blockers` yok) bir sonraki bar'da yeni `State` açıp yeni BASE başlatır; `realized/fees/funding/peak/max_dd/halted` taşınır, `orders/anchor/safety_stopped/blockers` sıfırlanır.
- Gerekçe: CORE01'in belirttiği üst-katman çözümü; taze `State.orders={}` "one base order per deal" değişmezini `engine.py`'ye dokunmadan doğal korur.
- Sınır: `deal_id`/`event_sequence` dedup anahtarı ve persistence çoklu-deal aggregate şeması bu kararın kapsamı dışıdır; mevcut bar-index tabanlı `order_id`/`execution_id` deal'ler arası çakışmadığı için orkestrasyon doğruluğu bu olmadan da sağlanır, ama kayıt katmanı hâlâ tek-deal varsayar (STATE.md/TASK.md).
- Kanıt: `tests/data/test_historical_simulation.py::test_bot_restarts_a_new_deal_after_the_prior_deal_closes_flat`; tam checker 872/872 PASS.

## 2026-09-20 — Proje temizliği kararları
- Karar: `.cluster/` (544MB, git dışı, eski ajan QA/araştırma çıktısı) tamamen silindi. Gerekçe: hiçbir kod veya aktif dokümana işlevsel bağımlılığı yok; yalnız 6 `evidence/*/SONUC.md` dosyası ekran görüntülerine referans veriyordu, bunlara "kaynak artık mevcut değil, tarihsel kayıt" notu eklendi.
- Karar: `evidence/` klasörünün AGENTS.md'nin "faz başına tek SONUC.md" kuralını 222 alt klasörle ihlal etmesi (P1.01'den beri, yeni bir bozulma değil) şimdi ele alınmayacak; ayrı, kasıtlı bir dilim olarak TASK.md/YOL_HARİTASI'nda planlanacak. Gerekçe: konsolidasyon `docs/OZELLIK_MATRISI.md`'nin onlarca satırdaki referansını değiştirecek büyüklükte, riskli bir refactor.
- Karar: `templates/GOREV_VE_DEVIR.md` ve `templates/OTURUM_MESAJI.md` (programatik referansı yok, muhtemelen elle kullanılan devir şablonu) olduğu gibi bırakıldı.
- Karar: `docs/` kökündeki 29 tamamlanmış-P1 araştırma promptu/raporu `docs/archive/arastirma-promptlari/` altına taşındı (bkz. STATE.md); içerik/hash değişmedi.

## 2026-09-20 — Çalışma kuralı: Claude karar alır, sormaz
- Karar: Arda bu tarihte iki kez, açıkça: ürün/teknik kararları Claude'a bırakıyor ("asıl uzman sensin", "en doğru kararı her zaman işaretle açıkla"). Bundan sonra AGENTS.md'nin "Durma ve sorma" listesindeki ürün/ekonomi kararı gerektiren durumlar dahil, Claude seçimi yapıp gerekçesiyle kaydeder; açık soru olarak Arda'ya geri atmaz.
- Sınır: Credential/secret, gerçek emir/mainnet ve parayı hareket ettiren geri dönüşsüz onaylar bu devrin dışındadır — bunlar için tek satır açık onay istenmeye devam eder (AGENTS.md güvenlik çizgileri değişmez).
- Aşağıdaki üç madde bu kuralla ilk kez karara bağlandı.

## 2026-09-20 — Sıralı deal persistence/API tasarımı ONAYLANDI
- Karar: TASK.md'de yazılı tasarım (`deal_id = execution_id:deal:<sequence>`, dedup anahtarı `(execution_id, deal_id, event_sequence)`, `source_execution_id` korunur, tek immutable run aggregate + sıralı deal özetleri) onaylandı; implementasyona geçilir.
- Gerekçe: Mevcut kod tabanında execution_id tabanlı dedup zaten birden çok yerde kullanılan bir kalıp (`spot_order_lifecycle.py` `seen_executions`, `futures_dca_journal_schema.py` `seen_execution`); yeni tasarım bu kalıbı genişletiyor, icat etmiyor. `engine.py`/çekirdek `State`'e dokunmuyor. Bar-index tabanlı `order_id`/`execution_id` zaten deal'ler arası çakışmıyor, yani orkestrasyon güvenliği zaten kanıtlı; eksik olan yalnız kayıt katmanının bunu ayrı kimlikle yansıtması. Bu olmadan `historical_ohlcv_v1` üzerinde birden fazla deal içeren HERHANGİ bir gerçekçi backtest (F21, en ileri özelliğimiz) kaydı yanıltıcı kalır — tek satır, son deal'in kümülatif özetini taşır, ara deal'leri gizler. Ertelemek F21'i yarım bırakır.
- Sonraki adım: `historical_run_contract.py` ve `historical_runs.py` şema değişikliği, TASK.md adım 7.

## 2026-09-20 — Faz 2 dondurma listesi ONAYLANDI (P1 kapanışına kadar)
- Karar: Futures Grid (F14), Reverse/Infinity Grid (F12/F13), two-leg/hedge (F18/F34), rebalancing (F17), signal bot (F19), çoklu bot/pair (F05) ve LLM açıklayıcı asistan (F32'nin dış-LLM parçası) P1 kapanışına kadar dondurulmuş kalır. Yeniden değerlendirme noktası: `git tag p1-demo-complete`.
- Gerekçe: (1) Rakip emsali — kendi C1-C4/P1-P5 araştırma kaynaklarımıza göre 3Commas ve Pionex de önce DCA/Spot Grid çekirdeğini oturttu, Futures/Reverse/sinyal/copy ailelerini yıllar içinde ekledi; aynı sıralama riski azaltır. (2) Kanıt durumu — bu 7 ailenin her biri zaten `DEFERRED/NO-GO` işaretli çünkü resmî kaynaklar exact ekonomik oracle sağlamıyor; şimdi açmak "kanıt yetersizse riskli ekonomik davranış açılmaz" ilkesini ihlal eder. (3) Odak — P1'in kapanış ölçütü (9 adımlık akış, bağımsız review, `p1-demo-complete` tag'i) zaten dar bir çekirdek (DCA + Spot Grid + backtest) üzerinden tanımlı; dondurulmuş ailelerin hiçbiri bu ölçütün parçası değil.
- Sınır: Bu dondurma nihai ürün kapsamını daraltmaz (bkz. ADR04), yalnız sırayı belirler; docs/URUN_KAPSAMI.md'deki "Hedef aileler" listesi değişmedi.

## 2026-09-20 — Testnet mutation kapısı ERTELENDİ (henüz olgun değil)
- Karar: Faz 3.4'ün mutation gate koşulları (onay ekranı, tutar limiti, kill-switch, idempotent clientOrderId) şimdi karara bağlanmaz.
- Gerekçe: Bu erken karar değil, kanıtsız karar olur — P2 (Binance testnet) henüz açılmadı; reconnect worker, REST catch-up ve salt-okunur hesap ekranı (Faz 3.1-3.3) olmadan mutation koşullarını tanımlamak gerçek testnet davranışı gözlemlenmeden yapılan bir tahmin olurdu. AGENTS.md'nin araştırma kutusu ilkesiyle çelişir.
- Yeniden değerlendirme noktası: Faz 3.4'e gelindiğinde, 3.1-3.3 kanıtı elde edildikten sonra.

## 2026-09-20 — Ajanlar arası işbölümü (Claude kritik/matematik, Codex sınırlı UI dilimi)
- Karar: Arda birden fazla ajan kullanıyor (Codex/Luna, yüksek effort). İşbölümü kriterine göre yapılır: exact Decimal/Fraction/hash hesabı, `engine.py`, `historical_simulation.py`, `historical_run_contract.py`, `persistence/` — yalnız Claude değiştirir. Backend'e dokunmayan, salt UI dilimleri (ör. Faz 2.4 etkileşimli marker) dosya allowlist'li bir brief ile Codex'e TASK.md üzerinden devredilebilir.
- Gerekçe: Arda "hangisi verimli sen seç" dedi; kritik yerlerde "mükemmel matematik ve doğruluk" istedi. Proje zaten Codex'in "anlamsız döngüye" girmesinden kirlenmişti (bkz. proje temizliği kararı) — büyük/gevşek görev yerine dar, dosya sınırlı, durma koşullu tek dilim vermek riski azaltır. TASK.md zaten her oturumun okuduğu tek kaynak; brief'i ayrı bir chat promptu yerine oraya yazmak devri "kırılmaz" yapar.
- Sınır: Devralan ajan STATE.md/TASK.md/docs/KARARLAR.md'yi değiştirmez; yalnız kod+test yazar. Claude her devirden sonra diff'i, tam checker'ı ve frontend tsc/vitest'i kontrol eder, belgeleri kendisi günceller. Kural AGENTS.md'ye "Ajanlar arası işbölümü" olarak eklendi.
- İlk uygulama: Faz 2.4 (etkileşimli marker) — TASK.md'de Codex brief'i olarak yazıldı.

## 2026-09-20 — Faz 2.5 kapsamı: tam stress modeli NO-GO, dar slippage-profili ACCEPT
- Karar: `docs/OZELLIK_MATRISI.md` F24 ve `P1.16.i.b` araştırma kaydı yeniden okundu. Rapor kendi bağımsız matematik kontrolünde iki yerde çelişkili çıktı verdi (T-07: rapor formülüyle yeniden hesaplanan fill/net rapordakiyle uyuşmuyor; T-12: seed hem hash'e dahil hem deterministic model için null deniyor — çelişkili) ve rapordaki `ReserveState` örneği kendi `available >= 0` invariant'ını ihlal ediyordu (`evidence/P1.16.i.b/SONUC.md`). Bu nedenle yeni spread/latency/queue-participation/reserve stress ekonomik modeli **açılmadı, `DEFERRED/NO-GO` olarak kaldı** — kaynağın kendisi güvenilmez, "biraz daha araştırıp uygularız" değil.
- Bunun yerine uygulanan dar dilim: mevcut, zaten exact `config.slippage` mekanizmasını (Fraction, `historical_simulation.py:196,320`) kullanan ikinci bir açık isimli profil eklendi — `historical_demo_btcusdt_1h_stress_slippage_v1` (config: mevcut demo config ile birebir aynı, yalnız `slippage=0.002`). Yeni ekonomik kod, yeni RNG/seed, yeni reserve/latency/volume mantığı yok; `engine.py` çekirdeği değişmedi.
- Bu dilim beklenenden küçük çıktı: mevcut UI zaten profil seçiciyle bu yeni profili otomatik listeler (`/api/historical-profiles`), mevcut Saved Runs karşılaştırma ekranı (Faz 2.3) iki farklı slippage koşusunu yan yana göstermeye zaten yeterli — bu yüzden **frontend'e hiç dokunulmadı, Codex'e devredilecek bağımsız bir UI dilimi oluşmadı**. Gerekçe: `application/historical_profiles.py` ve `config/*.json`, işbölümü kuralının "exact/critical" tarafına giriyor (profil = ekonomik parametre seti); UI tarafında zaten var olan bileşenleri yeniden kullanmak, sıfırdan bir "ikinci koşu + otomatik karşılaştır" akışı icat etmekten daha az riskli ve daha az kod.
- Doğrulama: yeni bağımsız oracle testi (`tests/data/test_historical_simulation.py::test_stress_slippage_profile_shifts_the_base_fill_price_deterministically`, bar open=100 → base fill=100, stress fill=100.2, elle hesaplanmış), profil registry testi genişletildi, tam checker `880/880 PASS`, canlı tarayıcıda `/api/historical-profiles` ve `/api/datasets/{id}/run-plan?profile_id=...` her iki profil için ayrı `config_hash`/doğru `slippage` ile doğrulandı, yeni profil UI dropdown'ında göründü.
- Sonraki geçiş: `P1.16.i.c` (deterministic scenario/result identity) hâlâ açılmadı — bu karar onu tetiklemiyor; yalnız mevcut mekanizmanın ikinci parametre setiyle kullanımıdır.

## 2026-09-20 — P1 kapanış ölçütü tamamlandı, `p1-demo-complete` etiketlendi
- Karar: docs/YOL_HARITASI.md'nin Faz 2 kapanış ölçütünün üç şartı da sağlandı: (1) temiz klonda 9 adımlık akış, (2) bağımsız review, (3) tag. P1 (yerel demo) resmen kapandı.
- (1) Temiz klon: gerçek `git clone` (kalıcı git config değişikliği yapılmadan, yalnız `GIT_CONFIG_*` env override ile — "asla git config değiştirme" kuralına uyuldu), README komutlarıyla backend+frontend ayağa kaldırıldı, 9 adım (veri indir/doğrula → kalite raporu → bot kur → parasal etki önizle → geçmişi çalıştır → grafikten olayları incele → kaydet → kapat/aç [reload sonrası SQLite'tan geldi] → reproduce ile aynı sonuç [`reproduced=true`, 3 hash eşleşti]) tarayıcıda canlı doğrulandı; tam checker 880/880, manifest PASS, workspace PASS.
- (2) Bağımsız review: Codex/muse'e (farklı ajan, salt-okunur, tek çıktı dosyası izniyle) `git diff main...HEAD` (187 dosya, kritik→API→frontend üç katmanlı öncelik) incelettirildi. Sonuç `APPROVED_WITH_FINDINGS` (`evidence/P1_CLOSURE_INDEPENDENT_REVIEW_2026_09_20/SONUC.md`): Katman 1-2'de (ekonomik/API) davranışsal kusur yok; 1 LOW + 4 INFO bulgu, hepsi kanıtla (kod alıntısı/gerçek komut çıktısı) desteklenmiş, okunmayan alanlar açıkça `NOT_VERIFIED` bırakılmış.
- Tek eyleme dönüşen bulgu (F1): `DatasetCatalogPanel.tsx`'te aksiyon tablosu satırının `onClick`'i, klavye yolundaki (`onKeyDown`) hedef-koruma (`event.target !== event.currentTarget`) deseninin aynısını taşımıyordu — fixed-slice satırındaki Kopyala butonuna tıklamak hem butonu çalıştırıyor hem satırı seçiyordu (kozmetik, ekonomik etkisi yok). Claude aynı gün düzeltti (`onRowClick` fonksiyonu, aynı hedef-koruma deseni), yeni bir test eklendi (iç öğeye tıklama/Enter satırı seçmemeli), canlı tarayıcıda DOM üzerinden doğrulandı (`aria-pressed` Copy butonunda `false` kalıyor, satırın kendisinde `true` oluyor). F2-F5 (formül tekrarı, dependency üst sınırı, test kapsam notu, henüz API'ye bağlanmamış yeni store'lar) INFO seviyesinde, kapanışı engellemiyor; ileride ele alınabilir.
- Gerekçe: proje boyunca kurulan "Claude her devrilen işi bağımsız doğrular" disiplini burada tersine de uygulandı — Claude'un kendi kapanış iddiasını (P1 tamam) yalnız kendi self-review'üyle değil, gerçekten farklı bir ajana (Codex/muse) okutup kanıt istedi. Bu, projenin "kanıtsız karar yok" ilkesiyle tutarlı: "muhtemelen tamam" değil, "APPROVED_WITH_FINDINGS + kanıt dosyası + düzeltilmiş tek gerçek bulgu."
- Sonraki adım: Faz 3 (P2 gerçek Binance testnet) kapsam kararı Arda'yı bekliyor — TASK.md'de açık soru.

## 2026-09-20 — Faz 3.1 kapsam netleştirmesi: SYNCED bu dilimde hedef değil
- Karar: docs/YOL_HARITASI.md'nin 3.1 kanıt cümlesi ("GAP → RECONCILIATION_REQUIRED → SYNCED") ile 3.1'in kendi tanımı ("bağlan, düş, yeniden bağlan; gap tespiti") arasında küçük bir tutarsızlık vardı. `ReconciliationCoordinator.apply_authoritative_snapshot`/`mark_synced` kodunu okudum: SYNCED'e geçiş yalnız bir authoritative REST snapshot ile mümkün (`AUTHORITATIVE_SNAPSHOT_REQUIRED` fail-closed kontrolü) — bu snapshot 3.2'nin (REST catch-up) işi, henüz yok. Bu yüzden 3.1'i SYNCED'i de kapsayacak şekilde uygulamaya çalışmak ya sahte bir snapshot icat etmeyi (yasak) ya da 3.2'yi erken açmayı gerektirirdi.
- Karar: 3.1'in kapsamı kendi kısa tanımıyla sınırlı tutuldu: connect → disconnect → bounded backoff → reconnect → gerçek event continuity üzerinden gap tespiti. SYNCED, 3.2 REST catch-up'ı ile birlikte doğal olarak tamamlanacak.
- Gerekçe: Mevcut `ReconciliationCoordinator`/`BinanceTestnetUserDataStream` kodunu değiştirmeden (ikisi de önceki oturumlarda kurulmuş, iyi test edilmiş, kritik dosyalar) yeniden kullanmak, sıfırdan yeni bir snapshot/senkron mekanizması icat etmekten daha güvenli ve daha az kod.
- Uygulama: `src/dcabot/application/user_stream_reconnect_worker.py` (yeni, offline test edilebilir — `websocket_factory`/`sleep` enjekte edilebilir), `tools/run_user_stream_reconnect_worker.py` (Arda'nın yerelde çalıştıracağı, Claude'un hiç çalıştırmadığı canlı araç).

## 2026-09-21 — Faz 3.1 REAL_TESTNET kanıtı alındı; gerçek testnet'in yakaladığı bug düzeltildi
- Karar: Arda `tools/run_user_stream_reconnect_worker.py`'yi gerçek Binance Spot Testnet'e karşı yerelde çalıştırdı, ağı birden çok kez kesip açtı. İlk denemede program **çöktü**: `websockets.exceptions.ConnectionClosedError` (bir `Exception` alt sınıfı, `OSError` değil) `recv_execution_report`/`recv_order_list_event`'in `except (TimeoutError, OSError, ValueError, TypeError)` bloğu tarafından yakalanmıyordu, `asyncio.run()`'a kadar çıplak çıktı. Bu, offline sahte-socket testlerinin (yalnız `OSError` fırlatan) yapısal olarak kaçırdığı gerçek bir bug'dı.
- Fix: `binance_testnet_user_stream.py`'de her iki `recv_*` metoduna, `connect()`'in zaten sahip olduğu desenle aynı bir `except Exception` catch-all eklendi (aynı hata kodu/mesajıyla fail-closed). İki yeni test (`test_library_specific_close_exception_still_fails_closed`, `test_order_list_library_specific_close_exception_still_fails_closed`) gerçek `ConnectionClosedError` sınıfını kullanarak bunu kanıtlıyor.
- İkinci çalıştırmada: worker birden fazla gerçek disconnect/reconnect döngüsünü (biri `attempt=5`'e kadar, backoff sınırında tam zamanında toparlanarak) çökmeden atlattı. Gerçek bir `GAP` gözlenmedi (testnet hesabında o sırada işlem olmadığı için event kaçırılmadı) — roadmap'in kendisi bunu garanti etmiyordu.
- Gerekçe: Bu, "Claude her devrilen işi bağımsız doğrular" disiplininin bir başka yüzü — offline testler ne kadar iyi olursa olsun, gerçek ağ/gerçek kütüphane davranışı ayrı bir kanıt sınıfı. `evidence_scope=REAL_TESTNET` şartı bu yüzden roadmap'te var; bu olay onu somut olarak doğruladı.
- Sonuç: Faz 3.1 tamamen kapandı (`evidence_scope=REAL_TESTNET`). Sıradaki iş 3.2 (REST catch-up).
