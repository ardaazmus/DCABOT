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
