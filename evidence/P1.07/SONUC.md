# P1.07 rapor değerlendirmesi

## Durum

`RESEARCH_RECEIVED / P1.07.a.1_CORE_ORDER_STATE_COMPLETE / P1.07.a.2_APPLICATION_COMPLETE / P1.07.a.3_PUBLIC_CONTRACT_COMPLETE`

Kullanıcının sağladığı P1.07 raporu proje talimatı olarak değil, doğrulanacak araştırma kanıtı olarak değerlendirildi. Raporun “fixed-quantity partial fill + explicit cancel remainder” önerisi, mevcut kodla karşılaştırıldı; doğrudan kod değişikliği yapılmadı.

## Bağımsız doğrulamalar

1. `tests.test_engine_store` ve `tests.api.test_historical_simulation` odak kontrolü, doğru `PYTHONPATH` ile `29/29 PASS` verdi.
2. Mevcut reducer üzerinde salt-okunur probe ile şu davranış doğrulandı: `INTENT qty=1` → `FILL qty=0.4` → `ORDER_FINAL CANCELED filled_qty=0.4` sonucu `CANCELED`, filled `0.4`, position `0.4`, leaves türetimi `0.6`, unsettled boş.
3. Aynı probe, tarihsel simülatörün iki düz barlı örnekte tek `BASE` action ile quantity `1` ürettiğini gösterdi; mevcut historical path partial slice üretmiyor.
4. Kod incelemesinde mevcut tarihsel action sözleşmesinin yalnız `bar_index` başına tek action kabul ettiği, action’da order lifecycle/status/provenance/canceled remainder alanlarının bulunmadığı doğrulandı.
5. Store katmanında `execution_id` duplicate payload dedup ve conflicting payload conflict davranışı mevcut; saf reducer’da bu persistence dedup katmanı yok.
6. Config schema 1 strict olduğu ve `slice_qty`/fill model alanı içermediği doğrulandı.

## Uygulanan en küçük mikro dilim: P1.07.a.1

Raporun `SIMPLIFIED` kararından yalnızca çekirdek order görünümü uygulandı:

- Partial `FILL` sonrası order status artık açıkça `PARTIALLY_FILLED` olur.
- `Order.leaves`, açık order için `original_qty - filled_qty` değerini exact döndürür.
- Explicit terminal `CANCELED` sonrası `Order.canceled`, `original_qty - filled_qty` değerini exact döndürür.
- Late fill sonrası mevcut `UNKNOWN` güvenlik durumu korunur; partial status ile üzerine yazılmaz.
- Historical simulator, public API, config schema, persistence action schema, reserve/collateral ve UI değiştirilmedi.

TDD kanıtı:

- Yeni RED testi önce `Order.leaves` alanı bulunamadığı için başarısız oldu.
- Minimum reducer değişikliği sonrası aynı test GREEN oldu.
- İlk tam regresyon late-fill `UNKNOWN` durumunun yanlışlıkla `PARTIALLY_FILLED` olduğunu yakaladı.
- Koşul daraltıldı; odak düzeltme testleri `2/2 PASS` verdi.
- Son tam regresyon `114/114 PASS`, `compileall PASS`, workspace kontrolü `PASS`.

## Kabul edilen tespit

Raporun ilk dilim önerisi kavramsal olarak mevcut planla uyumlu olsa da implementation-ready değildir. En az şu sözleşme kararları kapanmadan tarihsel finansal kod değiştirilmeyecek:

- partial order’ın barlar arası lifecycle’ı ve dataset sonu davranışı,
- `canceled_qty`’nin state’te tutulması veya güvenli türetimi,
- action response/persistence’in aynı order için birden fazla fill’i taşıması,
- explicit opt-in config/profile/model version ayrımı,
- mevcut reserve ledger olmadığı için reserve’in kapsam dışı olduğunun açık sözleşmesi,
- reducer/store idempotency sınırı.

## Sonraki tek iş

Anonim ve kanıtlı contract audit promptu hazırlandı:

`docs/archive/arastirma-promptlari/P1.07.a_Mevcut_Core_Partial_Fill_Uyumluluk_Arastirma_Promptu.md` (2026-09-20'de arşivlendi; içerik/hash değişmedi)

Rapor artık alındığı için yeni araştırma bekleme kapısı kapandı; ancak tarihsel partial modelin kalan implementation işi ayrı mikro fazdır. Sonraki tek iş `historical_ohlcv_partial_fixed_v1` için opt-in parser/runner RED testlerini kurmaktır. Stop, queue, volume participation, random latency ve same-bar cancel/fill race hâlâ uygulanmayacaktır.

## Uygulanan mikro dilim: P1.07.a.2

Opt-in application runner `simulate_historical_fixed_slice` eklendi:

- Explicit pozitif ve mevcut quantity grid’ine hizalı `slice_qty` zorunlu.
- Legacy `simulate_historical_ohlcv` çağrısı ve `historical_ohlcv_v1` davranışı değişmedi.
- `historical_ohlcv_partial_fixed_v1` model etiketiyle aynı order birden fazla bar boyunca izleniyor.
- Her eligible bar en fazla bir exact fixed slice `FILL` üretiyor.
- Son remainder `min(slice_qty, leaves)` ile yalnız conservation için tamamlanıyor; round/upsize yapılmıyor.
- Action projection’da order ID, execution ID, cumulative fill, leaves, canceled, provenance ve post-status bulunuyor.
- Dataset sonunda açık order için sentetik cancel üretilmiyor; `OPEN_AT_END` ve `synthetic_cancel_applied=false` dönüyor.
- Ambiguous OHLC barında önceki ekonomik state korunuyor ve `INDETERMINATE/AMBIGUOUS_OHLC_PATH` devam ediyor.
- Reserve/collateral, latency, queue, volume participation, stop ve same-bar cancel/fill race eklenmedi.
- Runner ayrı `historical_fixed_slice.py` modülünde tutuldu; `historical_simulation.py` 461 LoC, helper modülü 155 LoC.

TDD/farklı kontrol kanıtı:

- Fixed slice invalid/off-grid, multi-bar `0.4 + 0.4 + 0.2`, EOF `OPEN_AT_END`, ambiguity ve determinism testleri: `5/5 PASS`.
- Tam Python regresyonu: `119/119 PASS`.
- `compileall`: PASS.
- Workspace kontrolü: PASS.

## Sınır ve sonraki kapı

P1.07.a.2 tamamlandığı anda runner henüz public API/profile/config schema veya persistence action v2’ye bağlanmamıştı; mevcut frontend ve legacy response sözleşmesine partial alan sızmıyordu. Bu kapı P1.07.a.3’te strict opt-in profile/config ve public response contract’ı ile tamamlandı.

## Uygulanan mikro dilim: P1.07.a.3

Fixed-slice runner strict public contract’a bağlandı:

- `historical_demo_btcusdt_1h_partial_fixed_v1` ayrı ve explicit opt-in profile olarak tanımlandı; mevcut `GET /api/historical-profiles` listesi ve UI yalnız legacy profilleri göstermeye devam ediyor.
- Opt-in profile, mevcut `historical_demo_btcusdt_1h_v1.json` schema 1 config’ine güvenli biçimde bağlanır ve `slice_qty="0.001"` politikasını profile metadata’sında taşır. `paper.json` ve legacy demo config değiştirilmedi.
- Fixed model için config hash, ham config ile birlikte `simulation_model` ve `slice_qty` politikasını kapsar; legacy config hash hesaplaması korunur.
- Run-plan ve validation, fixed profile seçildiğinde ayrı strict config/profile DTO’su döndürür. Legacy run-plan/validation JSON’u ek alan almadan korunur.
- `/api/historical-runs/simulate` yalnız request’te fixed model ve fixed profile birlikte eşleşirse runner’a dispatch eder; response versioned lifecycle action alanlarını (`order_id`, `execution_id`, `action_type`, cumulative fill, leaves, canceled, post-status, provenance) taşır.
- Fixed response `execution_id=null`, `persisted=false` ve `persistence=NOT_SUPPORTED_IN_THIS_PHASE` ile kalıcı save akışından ayrılır. Partial capture mevcut P1.06 store’a yanlış tipte yazılmaz.
- Ambiguous bar indeksi application result’a açıkça taşındı; `INDETERMINATE/AMBIGUOUS_OHLC_PATH` response’unda ekonomik commit iddiası yapılmaz.
- Legacy response/action/profile contract’ına yeni alan sızması tam regresyonda yakalandı ve ayrı DTO union’larıyla düzeltildi.

TDD ve bağımsız kontrol kanıtı:

- RED: opt-in profile bulunamadı ve fixed run-plan alanları yoktu; test beklenen eksik-contract hatalarıyla başarısız oldu.
- GREEN: opt-in run-plan ve fixed lifecycle response testleri `2/2 PASS`.
- Bağımsız tam regresyon: `121/121 PASS`.
- OpenAPI üretimi: `17 paths / 39 schemas` PASS.
- `compileall`: PASS.
- `tools/check_workspace.py`: PASS.

## Sınır ve sonraki tek iş

Bu dilimde fixed model için frontend görseli, profile selector görünümü, action tablosu genişletmesi, grafik marker değişikliği ve P1.06 persistence action v2 eklenmedi. Fixed response mevcut save endpoint’ine bilerek bağlanmadı; `execution_id=null` bu sınırı makinece görünür kılar.

Gerçek ASGI HTTP request/response smoke ve strict serialization doğrulaması da tamamlandı:

- Ham ASGI `scope/receive/send` üzerinden gerçek `POST /api/historical-runs/simulate` çağrısı: `1/1 PASS`.
- FastAPI response-model union serileştirmesi, `execution_id=null`, `persisted=false`, fixed model ve dört lifecycle action doğrulandı.
- `compileall`, workspace ve tam regresyon kontrolleri önceki sonuçlarla birlikte PASS.

P1.07.a public contract tamamlandı. Fixed profile’ı mevcut UI’a açmak yeni UI/UX davranışı olduğu için anonim araştırma kapısı açıldı:

`docs/archive/arastirma-promptlari/P1.07.b_Fixed_Slice_UI_UX_Arastirma_Promptu.md` (2026-09-20'de arşivlendi; içerik/hash değişmedi)

Bu rapor alınana kadar profile selector, partial action tablosu, save düğmesi davranışı veya grafik görünümü genişletilmedi; aşağıdaki P1.07.b bölümünde yalnız doğrulanmış ve sınırlı uygulama kaydedilmiştir.

## P1.07.b — Fixed-slice UI/UX uygulaması

Durum: `COMPLETE / LOCAL_PASS`; bağımsız review: `NOT_RUN`.

Kullanıcı tarafından sağlanan `P1.07.b_Fixed_Slice_UI_UX_Detayli_Arastirma_Raporu_2026-09-08.md` talimat değil, araştırma kanıtı olarak değerlendirildi. Rapor kararları mevcut API ve önceki güvenlik sınırlarıyla karşılaştırıldı. `INDETERMINATE` altında action authority tanımlı olmadığı için action history/grafik/marker gösterimi fail-closed bırakıldı; bu rapordaki B01 araştırma gereksinimi olarak korunuyor.

Uygulanan en küçük dikey dilim:

- Fixed profile güvenli katalog listesine explicit opt-in olarak eklendi; legacy profile response alanları korunuyor.
- Selector’da model farkı yardımcı metinle görünür. Fixed model seçildiğinde varsayılanı unchecked olan tek onay checkbox’ı gösterilir.
- Onay olmadan başlatma reddedilir; hata doğrudan checkbox’a bağlanır ve focus checkbox’a taşınır. Fixed model için ayrıca confirmation modal açılmaz; legacy modal akışı korunur.
- Profil değişiminde mevcut plan/simülasyon/chart/save state temizleme akışına polite reset duyurusu eklendi.
- Determinate fixed sonuçta action tablosu backend alanlarını yeniden hesaplamadan `Aksiyon → Rol → Order → Original → Cumulative filled → Leaves → Durum` sırasıyla gösterir. Full ID, raw reference, fiyat/miktar, fee, fee asset, provenance ve lifecycle ayrıntıları native disclosure’da tutulur; kimlik kopyalama kontrolü eklenir.
- `PARTIAL_FILL`, `FULL_FILL`, `PARTIALLY_FILLED`, `FILLED`, `OPEN_AT_END` metinle görünür; `canceled_qty` ile `leaves_qty` birleştirilmez. Dataset sonunda sentetik cancel/exit üretilmez.
- Fixed `persisted=false` sonucu için save CTA kaldırıldı ve “Bu profilin sonucu bu aşamada kalıcı koşuya bağlı değildir ve kaydedilemez.” notu gösterildi. Legacy save akışı ve guard korundu.
- `INDETERMINATE / AMBIGUOUS_OHLC_PATH` altında kesin ekonomik özet, action history ve marker gösterimi değiştirilmedi; frontend yeni ekonomik veri üretmiyor.
- 320px ladder tablo taşması da aynı responsive kabulü sağlamak için düzeltildi; fixed action görünümünde yatay taşma oluşmadı.

Doğrulama zinciri:

1. RED: profile registry/API testleri fixed profil katalogda yokken beklenen üç profili istedi ve `2` test başarısız oldu.
2. GREEN: registry + strict profile union response düzeltmesi sonrası odak testleri `12/12 PASS`.
3. Backend tam regresyonu `122/122 PASS`; `compileall PASS`; `tools/check_workspace.py PASS`.
4. Frontend `npm run build PASS`.
5. Browser/IAB: fixed profil görünür; unchecked onayla başlatma checkbox’a focuslanan hata veriyor; checked akışta 4 lifecycle action görünüyor; Original/Cumulative/Leaves doğrulandı; fixed save butonu `0`; disclosure ve copy kontrolü çalışıyor; console warning/error `0`.
6. Responsive ikinci kontrol: 320px `scrollWidth=305`, 390px `scrollWidth=375`; action row sayısı `4`; görünür kayıt CTA’sı `0`. Geçici viewport sıfırlandı.

## Sınır ve sonraki tek iş

`INDETERMINATE` yanıtında belirsizlik öncesi action prefix’inin yetkili biçimde gösterilip gösterilemeyeceği bu aşamada kanıtlanmadı. Bu sınır, `P1.07.c` araştırma kapısı ile yeniden değerlendirildi; araştırma ve yeni contract kanıtı olmadan belirsiz sonuçta action history, marker, sentetik çıkış veya persistence genişletilmeyecekti.

## P1.07.c — Araştırma değerlendirmesi ve güvenli ilk uygulama

Durum: `RESEARCH_RECEIVED / P1.07.c.1_COMPLETE / P1.07.c.2_COMPLETE_WITH_LIMITATION`; bağımsız review: `NOT_RUN`.

Kullanıcının sağladığı `P1.07.c_Indeterminate_Action_Authority_Ayrintili_Arastirma_Raporu.md` proje talimatı değildir; contract ve risk iddiaları için kanıt kaynağıdır. Raporun ana iddiası mevcut kodla doğrulandı: fixed runner ambiguity barında duruyor, fakat application result içinde ambiguity öncesi dört action prefix’i kalıyordu ve fixed public response bunları authority etiketi olmadan yayınlıyordu. UI bu durumu gizlese de ham API tüketicisi listeyi tam execution history olarak yorumlayabilirdi.

### Doğrulama sırası

1. `historical_ohlcv_partial_fixed_v1` için dört tamamlanmış base slice ve beşinci barında hem safety hem take-profit erişilebilirliği olan anonim fixture kuruldu.
2. RED testi, mevcut public response’ta dört prefix action’ının döndüğünü gösterdi.
3. Minimum contract değişikliği uygulandı: fixed response’a `complete_execution`, `action_authority`, `marker_authority` ve nullable `final_economic_summary` eklendi. `INDETERMINATE` durumunda public `actions=[]`; authority `NONE`; marker `NONE`; final ekonomik özet `null`; eski fixed `summary` alanı artık yayınlanmıyor. Completed fixed sonucu `FULL_RUN` authority altında aynı backend değerlerini taşımaya devam ediyor.
4. Odak API suite’i `10/10 PASS` verdi.
5. İkinci kontrol olarak gerçek ASGI request/response yolu çalıştırıldı; JSON body’de `actions=[]`, `action_authority.mode=NONE`, `marker_authority=NONE`, `final_economic_summary=null` ve `summary` alanının yokluğu doğrulandı.
6. Tam Python regresyonu `123/123 PASS`; `compileall PASS`; `tools/check_workspace.py PASS`; frontend `npm run build PASS`.

### Uygulanan karar

P1.07.c.1 `COMPLETE / LOCAL_PASS`: fixed public contract fail-closed hale getirildi. Bu dilimde application’ın iç prefix’i silinmedi; yalnız authority sözleşmesi olmayan public fixed response’tan çıkarıldı. Böylece gelecekte capability-aware prefix contract’ı için iç engine gözlemi korunurken mevcut client yanlış yetki varsayımına zorlanmıyor. Legacy `historical_ohlcv_v1` response ve P1.06 persistence akışı değiştirilmedi.

### Uygulanmayan kararlar

`COMMITTED_PREFIX` ile prefix action yayınlama; exact economic commit timing, bar/action cutoff, incomplete persistence ve legacy migration kararları kapanmadan açılmadı. Prefix marker görselleştirmesi için raporun kendisi de doğrudan kanıt bulunmadığını belirtiyor; v1 `marker_authority=NONE` olarak kaldı. Ambiguity sonrası action/fill/cancel/exit, sentetik kapatma, final P&L veya yeni persistence eklenmedi.

### Sonraki tek iş

P1.07.c.2 raporu sonrası prefix capability küçük guarded dilimi tamamlandı. Marker authority ve incomplete persistence için ayrı anonim kanıt/araştırma kapısı açılmadan yeni marker veya kayıt davranışı eklenmeyecek.

## P1.07.c.2 — Rapor sonrası guarded committed-prefix uygulaması

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`.

Kullanıcının sağladığı `P1.07.c.2_Committed_Prefix_Marker_Ayrintili_Arastirma_Raporu.md` talimat değildir; kanıt ve öneri kaynağı olarak değerlendirildi. Raporun `COMMITTED_PREFIX` için implementation-ready dediği bölüm mevcut c.1 fixed contract ile karşılaştırıldı. Marker için doğrudan trading-domain kanıtı bulunmadığı ve persistence semantiği açık olmadığı için bu iki alan uygulanmadı.

### İddia → kontrol → sonuç

1. Capability’nin yalnız explicit fixed profile’de açılması gerektiği kontrol edildi. Request’e `action_authority: NONE | COMMITTED_PREFIX` eklendi; default `NONE` ile mevcut fail-closed davranış korundu. Legacy `historical_ohlcv_v1` + `COMMITTED_PREFIX` kombinasyonu sessizce yok sayılmıyor, `422 UNSUPPORTED_ACTION_AUTHORITY` dönüyor.
2. Prefix’in ambiguity barı ve sonrası içermemesi kontrol edildi. Fixed runner’ın anonim ambiguity fixture’ında dört pre-ambiguity action’ı vardı; explicit capability olmadan `actions=[]`, explicit capability ile `[event_sequence 1..4]` döndü. Response cutoff bar `4`, ambiguity bar `5`, scope `PREFIX_ONLY`, `action_count=4`; `complete_history=false`, final ekonomik özet `null`, marker `NONE` kaldı.
3. UI yanlış final yorum üretmemeli iddiası kontrol edildi. Prefix actions normal history yerine ayrı `PREFIX KANITI · TAMAMLANMAMIŞ KOŞU` salt-okunur tablosunda; cutoff ve ambiguity zamanı metinsel olarak; normal marker/grafik olmadan gösteriliyor. Frontend finansal hesap ve persistence eklenmedi.

### Doğrulama

- RED/ikinci kontrol: legacy capability guard testi önce problem type sözleşmesiyle hizalandı; düzeltilmiş guard ve fixed explicit-prefix ASGI testi GREEN oldu.
- Odak API suite: `11/11 PASS`.
- Tam Python kalite kapısı: `124/124 PASS`.
- Frontend: `npm run build PASS`.
- `compileall` ve `tools/check_workspace.py`: PASS.

### Uygulama sınırı

Marker authority/prefix marker, incomplete persistence/save/reopen ve `OPEN_AT_END` için yeni contract uygulanmadı. `marker_authority=NONE`, normal marker yokluğu ve fixed `persisted=false` korunuyor. Sonraki tek iş marker authority için ayrı kanıt/araştırma kapısıdır; yeni marker davranışı rapor ve test olmadan eklenmeyecek.

## Sonraki tek iş: P1.07.c.3 marker authority araştırma kapısı

Prompt hazırlandı: `docs/archive/arastirma-promptlari/P1.07.c.3_Marker_Authority_Arastirma_Promptu.md` (2026-09-20'de arşivlendi; içerik/hash değişmedi).

Bu araştırma, `INDETERMINATE` prefix için normal action marker ile nötr incomplete boundary marker’ı ayıracak; doğrudan trading-domain kanıtını genel erişilebilirlik çıkarımından ayıracak; SVG/ARIA, keyboard, screen reader, grayscale, reduced-motion ve 320px kabul testlerini tanımlayacak. Rapor gelmeden marker authority `NONE` kalacak.

## P1.07.c.3 — Marker authority ve boundary-only uygulaması

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`.

Kullanıcının sağladığı `P1.07.c.3_Marker_Authority_Ayrintili_Arastirma_Raporu.md` talimat değildir; kaynaklı karar ve risk kanıtı olarak değerlendirildi. Rapor `SIMPLIFY` kararını verdi: normal trade/action marker yerine yalnız ambiguity başlangıcını gösteren nötr boundary annotation; görünür warning, cutoff ve ayrı prefix evidence tablosu korunmalı. Trading-domain kaynaklarında nötr boundary için doğrudan standart bulunmadığı `KANIT YOK` olarak bırakıldı; bu nedenle boundary ekonomik olay veya execution marker olarak tanımlanmadı.

### İddia → kontrol → sonuç

1. Normal marker’ın fill/entry/exit anlamına çekilebileceği iddiası kaynak rapordaki TradingView execution/strategy semantics bulgularıyla uyumlu bulundu. Prefix action’ları price chart üzerinde normal marker olarak çizilmedi.
2. Boundary’nin yalnız explicit prefix authority’de açılması kararı mevcut API ile kontrol edildi. Fixed completed response `FULL / TRADE_EXECUTION`, default indeterminate response `NONE`, explicit prefix indeterminate response `PREFIX_BOUNDARY_ONLY / INCOMPLETE_BOUNDARY` taşıyor.
3. Boundary yanlış dataset veya yanlış bara bağlanmamalı iddiası frontend guard’larıyla uygulandı: dataset/artifact eşleşmesi, ambiguity bar/time, committed cutoff, action count, event sequence, bar range, duplicate ve action timestamp kontrolleri geçmeden boundary çizilmiyor.
4. Boundary annotation hatası OHLC grafiğini gereksiz yere kapatmamalı iddiası uygulandı. Annotation layer fail-closed olduğunda canonical OHLC overview, visible warning ve kendi binding’i geçerli prefix tablosu kalıyor.
5. Erişilebilirlik iddiası uygulandı: SVG içinde non-interactive dashed boundary + `INCOMPLETE · BAR n` text label; accessible description/caption içinde ambiguity ve commit edilmemiş bar açıklaması; tooltip/hover/focus/animasyon yok. 320px için mevcut responsive chart/table sınırları korunuyor.

### Uygulanan değişiklikler

- Fixed response contract’ına `marker_authority` için `PREFIX_BOUNDARY_ONLY`, ayrıca `marker_kind` için `INCOMPLETE_BOUNDARY` eklendi.
- Explicit `COMMITTED_PREFIX` indeterminate response’unda ambiguity başlangıç barı ve zamanı chart dataset’iyle exact doğrulanarak boundary üretiliyor.
- İndeterminate fixed sonuç için chart data fetch’i tam canonical dataset kapsamına izin verecek şekilde ayrıştırıldı; simulation’ın işlediği prefix sayısı ile chart’ın tüm verified bar sayısı karıştırılmıyor.
- Prefix action’ları grafikte normal marker olarak gösterilmiyor; ayrı `PREFIX KANITI` tablosu source of truth olarak kalıyor.
- `OPEN_AT_END` için sentetik close/exit, incomplete persistence/save/reopen, frontend ekonomik hesap, tooltip/crosshair/zoom/pan ve yeni endpoint eklenmedi.

### Doğrulama

- İlk build kontrolü event sequence optional type guard hatasını yakaladı; düzeltme sonrası frontend `npm run build PASS`.
- Fixed/API odak suite: `11/11 PASS`.
- Tam Python regresyonu: `124/124 PASS`.
- `compileall`: `PASS`.
- `tools/check_workspace.py`: `PASS`.

### Sınır ve sonraki faz

Prefix action marker’ı, farklı renk/şekille trade lane kullanımı ve usability kanıtı olmadan evidence lane eklenmedi. `marker_authority=PREFIX_BOUNDARY_ONLY` yalnız boundary annotation yetkisidir; execution marker yetkisi değildir. P1.07.c.3 complete-with-limitation olarak kapandı. Sıradaki planlı ekonomik davranışlar limit/stop/gecikme/queue/volume participation için ayrı araştırma ve test kapılarıdır.

## P1.07.d — Limit trigger/fill araştırması ve d.1 application mikro dilimi

Durum: `RESEARCH_RECEIVED / d.1_COMPLETE / LOCAL_PASS`; bağımsız review: `NOT_RUN`.

Kullanıcının sağladığı `P1.07.d_Limit_Order_Trigger_Fill_Ayrintili_Arastirma_Raporu.md` talimat değildir; kaynaklı iddia ve model önerisi olarak kontrol edildi. Raporun `SIMPLIFY` kararı mevcut planla sınırlandı: gerçek exchange execution reconstruction yapılmadı; stop, queue, latency, volume participation, cancel/fill race, persistence, UI ve yeni P&L eklenmedi.

### İddia → kontrol → sonuç

1. Placement barında görülen OHLC’nin aynı bar için kullanılmaması iddiası yeni test fixture’ı ile kontrol edildi. Order yalnız `placement_bar_index` sonrasındaki canonical barlarda gözlemlendi; placement barı strict penetration içerse bile fill üretilmedi.
2. Equality touch’ın fill authority vermemesi rapor kuralı olarak uygulandı ve BUY/SELL mirror testleriyle kontrol edildi. `low == limit` veya `high == limit` yalnız `EQUALITY_TOUCH` observation üretiyor; action ve ekonomik fill yok.
3. Strict penetration’ın sentetik policy olduğu ve fill fiyatının exact limit olması kontrol edildi. Advantageous open fixture’ında sonuç `FILLED`, `fill_price == limit_price`; open price improvement oluşmadı.
4. Fixed slice/remainder ve bar başına tek fill mevcut quantity sınırıyla kontrol edildi. Original `0.005`, slice `0.003` için ardışık barlarda `0.003 + 0.002`, tek action/bar ve final leaves `0` üretildi.
5. Same-bar ordering belirsizliği için application seam kontrol edildi. Ambiguous bar’da sonuç `INDETERMINATE / AMBIGUOUS_OHLC_PATH`, yeni action yok ve leaves korunuyor.
6. Bağımsız ikinci kontrol olarak production helper çağırmayan Decimal tablo oracle’ı kullanıldı; BUY/SELL strict/equality/no-touch senaryoları application sonucu ile eşleşti.

### Uygulanan en küçük değişiklik

`src/dcabot/application/historical_fixed_limit.py` içinde versioned `FIXED_LIMIT_STRICT_V1` policy’si ve exact result/action/observation dataclass’ları eklendi. `FixedLimitOrder` immutable placement identity taşır. Config grid/order policy doğrulanmadan çalışma başlamaz. Ekonomik kararlar `Fraction`/exact decimal boundary üzerinden yürür; float, fee, slippage, tick uydurma veya frontend hesabı yoktur. EOF’de pending leaves için `OPEN_AT_END` verilir; sentetik cancel/exit/fill üretilmez.

### Doğrulama

- İlk RED: eksik application modülü nedeniyle test import’u başarısız oldu.
- Düzeltme sonrası odak policy testleri ve bağımsız Decimal oracle: `7/7 PASS`.
- Tam `tools/run_checks.py`: `131/131 PASS`.
- `compileall src tests`: `PASS`.
- Legacy API/profile/persistence/UI testleri tam regresyonda korundu.

### Sınır ve sonraki tek iş

Bu modül henüz public profile, `/api/historical-runs/simulate`, action v2, persistence veya UI’ya bağlanmadı. Bu bilinçli bir sınırdır; public contract’ın limit observation/fill/provenance alanları için ayrı d.2 değerlendirmesi gerekir. `OPEN_AT_END`, equality observation ve synthetic fill’in UI/marker anlamı bu fazda değiştirilmedi. P1.07.d.2 public contract değerlendirmesi `DEFER` edildi; sonraki tek iş DCA strategy binding araştırma kapısıdır.

## P1.07.d.2 — Public contract araştırma kapısı

### Rapor değerlendirmesi: DEFER

Kullanıcının sağladığı P1.07.d.2 public contract raporu talimat değildir; public boundary iddiaları için kanıt kaynağı olarak değerlendirildi. Repository’de mevcut public model ve route sözleşmeleri incelendi. D.1 historical_fixed_limit.py ise generic tek limit order sonucudur; DCA BASE/SAFETY/EXIT, anchor, pending strategy state, reserve ve core economic posting’e bağlı değildir.

Bu nedenle yeni public profile/model, response union, run-plan alanı veya HTTP route eklenmedi. D.1 generic policy’yi public’e bağlamak, DCA sonucu olmayan bir synthetic demo fill’i gerçek strategy sonucu gibi yorumlatabilir. Public OpenAPI/ASGI union, legacy golden diff ve independent public reference oracle kanıtı da henüz yoktur.

Raporun “observation ve fill ayrılmalı” iddiası d.1 testleriyle doğrulandı: equality observation action üretmiyor; strict fill action’ı ayrı taşınıyor. Bu ayrım korunacak, ancak public response’a taşınmayacak.

### Sonraki tek iş

D.1 policy’sinin DCA strategy state’e bağlanması için anonim araştırma promptu açıldı: docs/archive/arastirma-promptlari/P1.07.d.3_DCA_Limit_Strategy_Binding_Arastirma_Promptu.md (2026-09-20'de arşivlendi; içerik/hash değişmedi). D.3 raporu gelmeden public limit contract’ı veya DCA limit behavior’ı uygulanmayacak.

### P1.07.d.3 — DCA strategy binding araştırma kapısı

Durum: `RESEARCH_RECEIVED / DEFERRED`; implementation yok. Araştırma raporu: `P1.07.d.3_DCA_Limit_Strategy_Binding_Ayrintili_Arastirma_Raporu(1).md`. Prompt: `docs/archive/arastirma-promptlari/P1.07.d.3_DCA_Limit_Strategy_Binding_Arastirma_Promptu.md` (2026-09-20'de arşivlendi; içerik/hash değişmedi).

Raporun BASE-only aday önerisi production’a alınmadı. Yerel kontrolde çekirdeğin INTENT/FILL/ORDER_FINAL, partial leaves, BASE anchor, safety blocker ve late-fill invalidation davranışları mevcut testlerle kanıtlandı; ancak d.1 fixed-limit observation’ının DCA order state’e güvenli adapter olarak bağlandığı, reserve lifecycle’ının ve BASE-only end-to-end ekonomik posting zincirinin kanıtı yok. SAFETY ve EXIT DEFER olarak kaldı. Public API, persistence, UI ve marker kapsam dışıdır.

External paket ayrıca 15 kaynak kartı, 30 önerilen test ve 14 local gate satırı sağlıyor; paket kendi sınırına göre local test çalıştırmamış, oracle yalnız araştırma fixture’ı üzerinde 48 kontrol yapmış ve production gate’i `DEFER_LOCAL_CODE_REQUIRED` bırakmış. Bu oracle bağımsız aritmetik kontrol olarak çalıştırıldı ve `PASS_RESEARCH_EXAMPLES_ONLY` verdi. Ayrı local doğrulamada reducer + fixed-limit odak suite `31/31 PASS`, tam regresyon `131/131 PASS`, compile ve workspace kontrolleri PASS oldu. Bu sonuçlar d.1 policy’sinin DCA binding’e bağlandığını kanıtlamaz.

Sonraki tek iş: production binding yazmadan local reducer claim inventory ve yalnız BASE için RED→GREEN integration test paketi. Bu paket reserve, anchor timing, pending blocker, duplicate/late fill, ORDER_FINAL ve placement/look-ahead kanıtlarını kapatmadan public/API/UI değişikliği yapılmayacaktır.

## P1.07.d.3.b — Reserve lifecycle ve BASE commitment araştırması

Durum: `RESEARCH_RECEIVED / SIMPLIFY_WITH_LIMITATION`; bağımsız review: `NOT_RUN`.

Kullanıcının sağladığı `P1.07.d.3.b_Reserve_Lifecycle_Ayrintili_Arastirma_Raporu.md` talimat değildir; reserve/commitment iddiaları için kanıt kaynağı olarak değerlendirildi. Raporun mevcut BASE-only v1 kararı `SIMPLIFY`: `reserve_model=NONE`, initial-margin estimate ≠ reserve, pending blocker lifecycle gate, accepted core FILL tek ekonomik authority, equality/candidate no-op ve EOF `OPEN_AT_END`. Explicit numeric reserve ledger kararı `DEFER` kaldı; reserve asset/unit, acquisition/reduction/release owner, fee/rounding, partial/EOF/ambiguity, duplicate/late ve atomicity sözleşmeleri local code/test ile kapanmadı.

Yerel kontrol d.3.a binding, fixed-limit policy ve core/store lifecycle yollarında `37/37 PASS`; tam `tools/run_checks.py` `137/137 PASS`; `compileall` ve `tools/check_workspace.py` PASS verdi. Kontrol, store katmanında duplicate execution dedupe ve late-fill blocker bulunduğunu; fakat saf reducer seviyesinde `execution_id` idempotency’sinin ayrı bir özellik olmadığını gösterdi. Bu nedenle reserve ledger, public DCA limit contract, persistence, UI ve SAFETY/EXIT binding açılmadı. Ayrıntılı kanıt: `evidence/P1.07.d.3.b/SONUC.md`.

Sonraki tek iş: `P1.07.d.3.c` — yalnız `reserve_model=NONE` için eksik BASE acceptance testlerini RED → GREEN ile kapatmak.

## P1.07.d.3.c — BASE-only `reserve_model=NONE` kabul testleri

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`.

P1.07.d.3.b araştırmasının `SIMPLIFY` kararı local testlerle dar kapsamda kapatıldı. Internal BASE binding sonucu `reserve_model=NONE`, `reserve_amount=NOT_MODELED` ve `reserve_asset=NOT_APPLICABLE` taşıyor; numeric reserve hesabı eklenmedi. Pending BASE → SAFETY blokajı ve full quantity FILL’in `ORDER_FINAL` coverage olmadan anchor üretmemesi test edildi. Odak suite `9/9 PASS`, tam `tools/run_checks.py` `140/140 PASS`, compile ve workspace PASS oldu. Saf reducer `execution_id` idempotency’si ayrı özellik olarak eklenmedi; store dedupe ve late-fill blocker ayrı katmandadır. Internal probe `production_ready=false` olarak kaldı.

## P1.07.d.2.b — BASE-bound public limit contract readiness

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.07.d.2.b/SONUC.md`.

Yalnız explicit `historical_demo_btcusdt_1h_v1` fixture’a bağlı `POST /api/historical-runs/simulate-base-limit` eklendi. Public adapter strict exact-decimal request, current dataset/artifact/config doğrulaması, server-owned BASE quantity, observation/fill ayrımı, deterministic binding identity, fail-closed `INDETERMINATE`, `NONE` reserve metadata’sı, `no-store` ve bounded response davranışını taşıyor. `150/150 PASS`, compile, workspace ve OpenAPI route kontrolleri PASS.

Bu dar contract genel DCA veya production execution değildir. Numeric reserve ledger, SAFETY/EXIT, cancellation race, latency/queue/volume/stop, persistence, marker/UI ve canlı venue kapsam dışıdır.

Sonraki tek kapı: bağımsız review. Review tamamlanmadan public contract genişletilmeyecek.
