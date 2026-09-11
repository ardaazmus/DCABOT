# DCABOT Task History

# Current task status — 2026-09-11

Verified commit: `8bcf7fc`, equal to `origin/main` on the private repository. The review hardening changed only six scoped files and passed `414/414` full backend tests, Python `-O` focused tests, compileall, workspace checks, and frontend production build.

The P2.03 lifecycle-to-core binding already exists in `a60ef1f` and is locally verified as an offline/fake Spot LIMIT binding. It does not activate live Binance REST/WS, signed account, mutation, persistence atomicity, or mainnet.

Current gate: Full P2.03 `IN_PROGRESS`; trading activation `NO-GO`.

Next safe action: consolidate P2.03/P2.04 offline acceptance evidence and evaluate remaining live-integration prerequisites in a separate decision gate. Testnet mutation requires explicit authorization.

---

## P1.02.a — Yerel CSV/ZIP kalite raporunun ilk dikey dilimi

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. P1.02.a tamamlandı; bağımsız faz incelemesi açık bırakıldı. Sıradaki en küçük davranış P1.02.b'dir.

## Tek davranış

Kullanıcı local CSV veya ZIP dosyasını veri merkezine verir; backend dosyayı güvenli biçimde okur ve sessiz kabul yerine sembol, kolon, timestamp, duplicate, gap ve satır kalite raporu üretir. Bu alt dilim alan eşleme ekranından önce yalnız güvenli okuma + deterministik kalite sonucunu kapsar; credential, public downloader ve gerçek emir yolu yoktur.

## Sınırlı okuma ve değişim

AGENTS/STATE; docs/VERI_VE_SIMULASYON veri sözleşmesi; docs/MIMARI data_adapters sınırı; docs/OZELLIK_MATRISI F25. Kod: `tools/check_workspace.py`, mevcut `src/dcabot` sınırları ve test fixture yaklaşımı. Önce yedek kapsam dışı; `YEDEK_ESKI_PROJE` okunmaz.

Gerçekleşen yollar: `src/dcabot/data_adapters/quality.py`, `src/dcabot/server/api.py` altında `POST /api/data-quality`, `tests/data/test_quality.py` ve `tests/api/test_data_quality.py`. Dosya yalnız proje dışına taşmadan okunur; ZIP içindeki yol traversal, boyut, uzantı, encoding ve malformed CSV reddedilir. Kalıcı dataset kaydı bu alt dilimin dışındadır.

## Kabul

1. Güvenli local CSV okunur; dosya adı/satır sayısı/byte sınırı raporlanır.
2. CSV/ZIP içeriğinde izinli tek veri dosyası seçilir; path traversal, çoklu belirsiz aday ve bozuk dosya reddedilir.
3. Header, required alanlar, timestamp birimi/UTC, duplicate ve sıralı gap bulguları deterministik raporlanır.
4. Malformed veya unsupported input sessizce başarıya çevrilmez; alan/kategori bazlı hata döner.
5. Python odak test + API contract testi gerçek parser sonucunu doğrular; fixture dışı yedek taranmaz.

Kapanış: P1.02.a parser/API kanıtı `evidence/P1.02.a/SONUC.md` altında tutulur. P1.02.b alan eşleme + kalite ekranı başlamadan P2 testnet’e atlanmaz. UI/UX yönünde kapsam genişletme veya dış görsel araştırma ihtiyacı doğarsa önce kullanıcıya danışılır.

## P1.02.b — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.02.b/SONUC.md`.

Gerçekleşen küçük davranış: local CSV/ZIP seçimi, kalite raporunun ekranda gösterimi, exact canonical mapping, ham şema için Bar/Trade seçimi, manuel mapping ve eksik/çakışan mapping reddi. P1.02.a parser sonucu yeniden hesaplanmadı; kalıcı import yapılmadı.

## P1.03.a — Public kaynak sözleşmesi ve indirme doğrulama hazırlığı

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.03.a/SONUC.md`.

Gerçekleşen küçük davranış: registry’ye açıkça kayıtlı public source için HTTPS/host/path/filename allowlist kontrolü, immutable download planı, SHA-256/byte metadata’sı ve diske yazmadan payload doğrulaması. Güncel Binance URL/checksum kayıtları doğrulanmadan aktif kaynak eklenmedi.

## P1.03.b — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.03.b/SONUC.md`.

Gerçekleşen küçük davranış: Kullanıcı tarafından doğrulanan Binance Spot `BTCUSDT/1h` 2025-01-01 ZIP’i registry’ye sabit hash/byte/iç CSV metadata’sıyla eklendi. HTTPS indirme response’u bounded streaming ile alınır; Content-Length/Content-Encoding, byte sayısı, SHA-256, ZIP CRC, üye yolu, symlink, üye/açılım sınırı ve beklenen CSV adı doğrulanmadan final cache yayınlanmaz. Başarılı payload content-addressed ZIP + metadata olarak atomik biçimde cache’e alınır; aynı doğrulanmış plan ağ çağrısı olmadan cache hit döner. Checksum/redirect/network retry orkestrasyonu ve katalog/UI bu dilimin dışındadır.

## P1.03.c — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.03.c/SONUC.md`.

Gerçekleşen küçük davranış: Explicit dataset definition’lar yerel cache durumuyla birleştirilerek dataset ID, source, sembol, interval, `[başlangıç,bitiş)` dönemi, beklenen SHA-256, byte, artifact adı ve `MISSING/CORRUPT/VERIFIED` bütünlük durumu listelenir. `select(dataset_id)` yalnız expected hash ve güvenli ZIP doğrulaması geçmiş artifact’ın path’ini parser/application portuna aktarır; bilinmeyen, eksik veya bozuk dataset seçilemez. UI, HTTP endpoint, download job orchestration ve credential kapsam dışıdır.

## P1.03.d — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.03.d/SONUC.md`.

Gerçekleşen küçük davranış: `GET /api/datasets` explicit katalog tanımlarını deterministic sırayla ve `MISSING/CORRUPT/VERIFIED` durumlarıyla döndürür. `PUT /api/dataset-selection` strict dataset ID alır; bilinmeyen ID’yi 404, bilinen fakat seçilemeyen cache’i 409 döndürür ve yalnız fresh VERIFIED artifact için path içermeyen selection DTO üretir. Yeni endpoint’ler `Cache-Control: no-store` kullanır, download/network başlatmaz ve mevcut endpoint’lerin hata sözleşmesini değiştirmez. Loopback çalıştırma README’deki `127.0.0.1` komutuyla korunur; yeni runtime dependency eklenmedi.

## P1.03.e — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.03.e/SONUC.md`.

Gerçekleşen küçük davranış: Katalog API’si mevcut P1.02 ekranına bağlandı. UI explicit dataset listesini okur; `ALL/VERIFIED/MISSING/CORRUPT` filtreleri, semantik tablo ve sağ detay paneliyle dataset type, enstrüman, interval, dönem, artifact boyutu ve kısaltılmış hash’i gösterir. `MISSING` ve `CORRUPT` seçim eylemleri kapalıdır; yalnız `VERIFIED` için `PUT /api/dataset-selection` çağrısı yapılır. Parser/application durumu, mevcut API’nin aktarımı başlatmadığı açıkça belirtilerek gösterilir. İndirme, URL/path, credential, progress/cancel/retry job ve testnet eklenmedi. Görsel karar, kullanıcı tarafından sağlanan anonim rapordaki tablo + sağ detay paneli önerisiyle sınırlı tutuldu.

## P1.03.f — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.03.f/SONUC.md`.

Gerçekleşen küçük davranış: Mevcut bounded downloader’a iptal/progress hook’ları eklendi; in-memory job yöneticisi `QUEUED/RUNNING/RETRYING/SUCCEEDED/FAILED/CANCELLED` durumlarını, sınırlı retry’ı ve dataset başına tek aktif job sahipliğini yönetiyor. `POST /api/dataset-downloads`, `GET /api/dataset-downloads/{job_id}` ve `POST /api/dataset-downloads/{job_id}/cancel` yalnız explicit katalog `dataset_id` ile çalışıyor. Job response’ları progress ve güvenli hata kodu taşır; URL/path/credential içermez. Verified cache yayımlama mevcut atomik/hash/ZIP doğrulama akışından geçer.

## P1.03.g — Katalog download job UI

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.03.g/SONUC.md`.

Gerçekleşen küçük davranış: Sağ detay panelindeki tek `LOCAL COPY` kartı, yalnız explicit registry dataset’i için indirme başlatır; `MISSING` ve `CORRUPT` durumlarında başlatma, `QUEUED/RUNNING/RETRYING` durumlarında bounded progress + deneme bilgisi + iptal, `FAILED/CANCELLED` durumlarında güvenli hata ve tekrar deneme eylemi gösterilir. Başarılı job sonrası katalog yeniden okunur ve `VERIFIED` selection akışı korunur. Polling hatası terminal başarısızlık sayılmaz; backend faz/ETA üretmediği için UI bunları uydurmaz. Serbest URL, credential, testnet/live emir eklenmedi.

## P1.04.a — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.04.a/SONUC.md`.

Gerçekleşen küçük davranış: Verified katalog selection capability’si salt-okunur application use case üzerinden header’sız Binance kline satırlarını immutable canonical bar tuple’ına dönüştürüyor. OHLCV değerleri exact decimal string, zamanlar integer microseconds/UTC, source kimliği ve artifact hash/byte metadata’sı input’a bağlı; path, URL, credential ve ekonomik hesap yok. Bar sırası, dönem sınırı, kapanış aralığı, OHLC sınırı, ham kolon sayısı ve bounded row sayısı doğrulanıyor.

## P1.04.b — Verified dataset preflight özeti

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.04.b/SONUC.md`.

Gerçekleşen küçük davranış: Verified canonical input için mevcut katalog detayında salt-okunur koşu öncesi özet gösteriliyor. Backend parser/application sınırından enstrüman, interval, `[başlangıç,bitiş)` dönemi, UTC microseconds standardı, gerçek bar sayısı ve artifact bütünlüğü alınarak path/URL/credential dışı bir preflight DTO’suna bağlanıyor. UI `READY`, yükleniyor ve güvenli hata durumlarını; `UNKNOWN` veri kalitesi durumunu; klavye ile açılabilen bütünlük ayrıntılarını ve 390px taşmasız görünümü gösteriyor. Koşu başlatma, ekonomik hesap tekrarı, import ve emir yolu eklenmedi.

## P1.04.c — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.04.c/SONUC.md`.

Gerçekleşen küçük davranış: Verified dataset preflight’i aktif `config/paper.json` ile salt-okunur tarihsel koşu planına bağlandı. Application katmanı offline config’i tekrar doğruluyor, dataset sembol uyumunu kontrol ediyor ve exact finansal string alanlarıyla deterministik config hash’i üretiyor. API `SIMULATED`, `NOT_STARTED`, `read_only` ve dataset preflight’ini aynı response’ta döndürüyor. UI mevcut preflight kartında aktif config snapshot’ını ve koşunun henüz başlatılmadığını gösteriyor. Simülasyon çalıştırma, sonuç kaydı ve yeni UI aksiyonu eklenmedi.

## P1.04.d — Bounded tarihsel koşu doğrulaması

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.04.d/SONUC.md`.

Gerçekleşen küçük davranış: `POST /api/historical-runs/validate` yalnız explicit dataset ID, current artifact SHA-256, current config hash ve `SIMULATED` kabul eder. Server kendi güncel VERIFIED preflight ve offline config bağlamını karşılaştırır; stale artifact/config, dataset-config çatışması, offline gate ve bar sınırı fail-closed reddedilir. Strict request/response DTO, 4 KiB body sınırı, güvenli Problem Details, `no-store` ve path/URL/credential/arbitrary config dışlama korunur. Endpoint run oluşturmaz, job başlatmaz, simülasyon çalıştırmaz, persistence/cache write yapmaz ve UI aksiyonu eklemez.

## P1.04.e — Offline tarihsel simülasyon başlatma

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.04.e/SONUC.md`.

Gerçekleşen küçük davranış: Güncel VERIFIED dataset preflight ve aktif offline config hazır olduğunda UI, `OFFLINE / TARİHSEL / SIMULATED` kapsamını görünür kılar; erişilebilir onay adımından sonra strict `POST /api/historical-runs/simulate` çağrılır. Application katmanı en fazla 1.000 kapalı barı `historical_ohlcv_v1` modeliyle, mevcut core reducer’a delegasyon ve deterministik fee/slippage sınırıyla işler. Safety/TP aynı OHLC barında birlikte erişilebiliyorsa o bar commit edilmeden `INDETERMINATE / AMBIGUOUS_OHLC_PATH` döner. UI yalnız completed/indeterminate/error durumunu bildirir; sonuç grafiği, işlem tablosu, persistence, network emir veya credential eklenmedi. Gerçek artifact + mevcut `config/paper.json` smoke’unda reducer’ın `max_entry_notional` politikası nedeniyle 422 güvenli hata görüldü; config sessizce değiştirilmedi.

## P1.05.a — Minimal güvenli tarihsel sonuç özeti

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.05.a/SONUC.md`.

Gerçekleşen küçük davranış: Mevcut `historical_ohlcv_v1` response’u UI’da yeni finansal hesap yapılmadan gösteriliyor. `COMPLETED` sonuçta backend’den gelen realized net after all costs, fee, position status, işlenen bar, dataset dönemi, model ve kısaltılmış config/artifact hash görünür. `OPEN_AT_END`, funding `NOT_MODELED`, mark `NOT_AVAILABLE`, forced close yokluğu ve `persisted=false` açıkça belirtiliyor. `INDETERMINATE` durumda ekonomik özet başarı gibi gösterilmiyor; ambiguity açıklaması korunuyor. Grafik, action/trade table, equity curve, ROI/risk metrikleri, persistence, credential ve network emir eklenmedi.

## P1.05.b — Read-only action/trade table

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.05.b/SONUC.md`.

Gerçekleşen küçük davranış: Mevcut `actions` alanından read-only aksiyon geçmişi eklendi. Masaüstünde semantik tablo; dar ekranda yatay taşma üretmeyen kart/liste düzeni kullanılıyor. `bar_index`, backend’in ham `role` değeri, `open_time_us`, `fill_price`, `quantity` ve `fee` aynen gösteriliyor; frontend finansal hesap yapmıyor. `INDETERMINATE` durumda tablo gösterilmiyor; `OPEN_AT_END` için sahte kapanış aksiyonu eklenmiyor. Grafik, marker, OHLCV response genişletmesi, yeni endpoint, chart dependency, ekonomik detay genişletmesi ve persistence eklenmedi.

## P1.05.c — Grafik veri sözleşmesi araştırma kapısı

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.05.c.1/SONUC.md`.

Gerçekleşen küçük davranış: Ayrı ve salt-okunur `GET /api/datasets/{dataset_id}/chart-data` endpoint’i ile bounded canonical chart data sözleşmesi eklendi. DTO yalnız verified dataset metadata’sını, `bar_index`, `open_time_us`, `close_time_us` ve exact OHLC stringlerini taşır. `volume`, `is_closed`, marker, grafik UI’si, persistence/run_id ve yeni chart dependency eklenmedi. Endpoint `no-store`, strict/frozen Pydantic model, dataset preflight ve 1.000 bar sınırını korur. P1.05.b action table mevcut sözleşmesiyle korunuyor.

## P1.05.c.2 — Minimal grafik render araştırma kapısı

Durum: COMPLETE / LOCAL_PASS_WITH_LIMITATION; review: NOT_RUN. Kanıt: `evidence/P1.05.c.2/SONUC.md`.

Gerçekleşen küçük davranış: P1.05.c.1 chart contract değişmeden, yalnız `COMPLETED` simülasyon sonrası mevcut `/api/datasets/{dataset_id}/chart-data` endpoint’inden veri alan native inline SVG nötr OHLC overview eklendi. Renderer backend sırasını koruyor; bounded 1.000 bar guard’ı, exact decimal string kaynağı, fixed-point display coordinate mapping, flat-domain/invalid payload fail-closed davranışı, accessible figure/image açıklaması ve 320px taşmasız görünüm var. Marker, tooltip, crosshair, zoom/pan, aggregation/downsampling, yeni endpoint/dependency, frontend finansal hesap ve persistence eklenmedi. `INDETERMINATE`/`AMBIGUOUS_OHLC_PATH` grafik göstermiyor; action table korunuyor.

## P1.05.c.3 — Action marker araştırma kapısı

Durum: COMPLETE / LOCAL_PASS_WITH_LIMITATION; review: NOT_RUN. Kanıt: `evidence/P1.05.c.3/SONUC.md`.

Gerçekleşen küçük davranış: Kullanıcı tarafından sağlanan anonim action marker araştırmasına göre mevcut `simulation.actions` ile `HistoricalChartData.bars` aynı dataset/artifact/bar kapsamı kimliği altında doğrulanıyor. `bar_index` aynı canonical equal-slot x yardımcısıyla marker merkezine bağlanıyor; `open_time_us` yalnız exact consistency check olarak kullanılıyor. Marker statik ve nötr bir circle glyph; sabit annotation lane’de çiziliyor, `pointer-events:none`, focus/tabindex/tooltip/hover/crosshair/zoom/pan yok. Duplicate, out-of-range, timestamp mismatch veya kimlik uyuşmazlığında yalnız marker katmanı fail-closed kapanıyor ve action table ayrıntı/fallback olarak kalıyor. `INDETERMINATE` sonuçta mevcut davranış korunuyor; `OPEN_AT_END` için sahte exit eklenmiyor. Backend, yeni endpoint, persistence, dependency ve frontend finansal hesap eklenmedi.

P1.05.c.2 chart contract ve static OHLC renderer korunur. Aktif gerçek config ile başarı sonucu üretilemediği için marker’ın canlı `COMPLETED` örneği browser’da sentetik veri olmadan doğrulanmadı; build ve güvenli hata/responsive QA PASS olarak kaydedildi. Sıradaki alt faz için marker etkileşimi veya kapsamlı finansal görünüm otomatik başlatılmayacak; ayrıca karar/araştırma kapısı gerekir.

## P1.05.d — Minimal ekonomik sonuç özeti araştırma kapısı

Durum: COMPLETE / LOCAL_PASS_WITH_LIMITATION; review: NOT_RUN. Araştırma girdisi: `P1.05.d_Minimal_Ekonomik_Sonuc_Detayli_Arastirma_Raporu.md`. Kanıt: `evidence/P1.05.d/SONUC.md`.

P1.05.a mevcut sonuç özeti, P1.05.b action table ve P1.05.c chart/marker katmanı korunuyor. Mevcut kod/contract clarification ile yalnız backend’den gelen `realized_gross`, `fees`, `realized_net_after_all_costs` ve `position_status` değerleri, explicit `quote_asset` etiketiyle gösteriliyor. `unrealized`, `equity`, numeric funding, ROI, drawdown, Sharpe/Sortino/CAGR, equity curve, benchmark, export ve frontend finansal hesaplama bu faza alınmadı. `OPEN_AT_END`, mark/funding ve `persisted=false` sınırlamaları metinsel olarak görünür; `INDETERMINATE` özeti gizli kalır.

## P1.06 — Kalıcı tarihsel koşu ve tekrar üretme araştırma kapısı

Durum: IN_PROGRESS; araştırma raporu değerlendirildi. Kanıt: `evidence/P1.06.a/SONUC.md`. Anonim araştırma girdisi: `P1.06_Persistent_Run_Detayli_Arastirma_Raporu_2026-09-08.md`.

Raporun kararları proje talimatı değil, doğrulanacak kanıt/öneri kaynağı olarak işlendi. P1.06.a’da persistence yazmadan önce bounded canonical input/config/result snapshot, explicit `USDT` monetary unit, action `raw_reference` güvenlik doğrulaması ve execution identity hash’leri hazırlandı. Yeni modül `src/dcabot/application/historical_run_contract.py` yalnız canonical capture üretir; SQLite, HTTP save/list/detail/reproduce, frontend persistence ve `run_id` henüz yoktur. P1.06 genel kabulü için dedicated store ownership, atomicity/corruption/migration, runtime benchmark ve API/UI mikro dilimleri sırayla kanıtlanacaktır.

### P1.06.b — Dedicated SQLite run-store ve backend save/reopen

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.06.b/SONUC.md`.

P1.06.a capture bileşenleri ayrı versioned SQLite run store’a bağlandı. Store path ownership, foreign DB reddi, rollback journal/FULL synchronous ayarı, immutable transaction insert, UUIDv4 run ID, source execution idempotency/conflict, record checksum, corruption isolation ve bounded deterministic list sınıf seviyesinde doğrulandı. HTTP endpoint, frontend, reproduction, compare, delete ve backup eklenmedi.

### P1.06.c — Explicit application/API save

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.06.c/SONUC.md`.

`POST /api/historical-runs/simulate` artık server-side bounded ephemeral execution registry’ye bir capture bağlayıp güvenli `execution_id` döndürüyor. `POST /api/historical-runs` istemciden result/config kabul etmeden yalnız bu mevcut execution capture’ını dedicated store’a kaydediyor. İlk save `201`, aynı execution retry’ı `200` ve aynı `run_id` döndürüyor; bilinmeyen execution store oluşturmadan `404 EXECUTION_NOT_FOUND` veriyor. `COMPLETED`/`INDETERMINATE`, `persisted=false`, secret/path/url dışı payload ve 4 KiB request sınırı RED→GREEN test edildi. UI, list/detail, reproduction, compare, delete ve backup eklenmedi.

### P1.06.d — Bounded list/detail read API

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.06.d/SONUC.md`.

Dedicated store’daki immutable kayıtlar için bounded deterministic `GET /api/historical-runs` list ve `GET /api/historical-runs/{run_id}` read-only detail/reopen API’si eklendi. Eksik store listede boş sonuç döndürürken dosya oluşturmaz; list limit’i 1..100 bounded; corrupt kayıt health’i korunur; invalid/not found/corrupt durumları Problem Details sözleşmesindedir; detail allowlist dışı path/url/secret anahtarlarında fail-closed olur ve 256 KiB response bütçesini aşamaz. Store tarafında valid checksum’e rağmen eksik nested alanlar da exception yerine `CORRUPT` olarak ayrıştırılır. UI, reproduction, compare, delete ve backup eklenmedi.

### P1.06.e — Saved Run UI

Durum: COMPLETE / LOCAL_PASS_WITH_LIMITATION; review: NOT_RUN. Kanıt: `evidence/P1.06.e/SONUC.md`. Araştırma girdisi: `P1.06.e_Saved_Run_UI_UX_Detayli_Arastirma_Raporu_2026-09-08.md`.

Mevcut React uygulamasına en küçük dikey dilimde `POST /api/historical-runs` save, `GET /api/historical-runs` bounded liste ve `GET /api/historical-runs/{run_id}` salt-okunur detay bağlandı. Ayrı Saved Runs navigasyonu, boş/yükleniyor/hata durumları, masaüstü semantik tablo, 320px stacked görünüm, `INDETERMINATE` uyarısı ve `CORRUPT` fail-closed ayrımı uygulandı. Detay snapshot’ları native disclosure içinde gösterilir; client-side finansal hesap, round/normalize, edit, delete, re-run, export, compare ve grafik eklenmedi. `COMPLETED` nötr durum olarak gösterilir; save feedback’i `201`/`200` idempotent ayrımını korur. Frontend build, 109/109 backend regresyonu, compile, workspace ve Browser/IAB desktop+320px QA PASS. Gerçek local cache/store boş olduğu için canlı save-success zinciri sentetik veriyle doğrulanmadı; bu sınırlama kanıtta açık bırakıldı.

### P1.06.f — Uyumlu historical profile ve gerçek backend save kanıtı

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.06.f/SONUC.md`. Araştırma girdisi: `P1.06.f_Uyumlu_Historical_Config_Detayli_Arastirma_Raporu_2026-09-08.md`.

Raporun `paper` config’i koruma ve ayrı explicit profile önerisi kabul edildi; rapordaki demo miktarları gerçek artifact üzerinde bağımsız test edildi. `config/historical_demo_btcusdt_1h_v1.json` ve kayıtlı profile registry eklendi. API run-plan, validation ve simulation request’leri explicit `profile_id` taşır; response ve immutable execution identity profile/provenance alanlarını echo eder. Gerçek artifact ile `historical_demo_btcusdt_1h_v1` backend zinciri `COMPLETED → temporary save → detail` olarak geçti. `paper.json` değişmedi; cap formülü ve anchor davranışı değiştirilmedi. Tam Python regresyonu `113/113 PASS`, frontend build, compile ve workspace PASS. Profile selector UI’sı anonim araştırma raporu sonrasında uygulandı; kanıt: `evidence/P1.06.f.2/SONUC.md`. Re-run, compare, delete, export ve kapsamlı ekonomik görünüm hâlâ kapsam dışıdır.

### P1.06.f.2 — Explicit profile selector UI

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.06.f.2/SONUC.md`. Araştırma girdisi: `P1.06.f.2_Historical_Profile_Secimi_UI_UX_Detayli_Arastirma_Raporu_2026-09-08.md`.

Preflight kartına native `Historical profile` select eklendi. İlk durum boş ve fail-closed; seçim backend `profile_id` ile run-plan’a bağlanıyor. Backend’den gelen insan-okunur label ve `expected_dataset_id` frontend’de yeniden türetilmiyor. Profil değişiminde eski plan/simülasyon/chart/save state’i temizleniyor; `project_fixture` uyarısı kalıcı inline note olarak gösteriliyor. 320px taşma ve browser console kontrolü PASS. Sonraki tek iş plan sırasındaki P1.06.f.2 bağımsız review kapısıdır; review `NOT_RUN` olarak açık bırakıldı.

### P1.07 — Sıradaki tek iş / kısmi fill ve order-event araştırma kapısı

Durum: IN_PROGRESS; P1.07.a, P1.07.b, P1.07.c.1, guarded P1.07.c.2/c.3 ve P1.07.d.1 complete-with-limitation; d.2 ve d.3 DEFERRED. Kanıt: `evidence/P1.07/SONUC.md`.

Kısmi fill, cancel/fill yarışı, limit/stop tetikleme, gecikme, OHLC belirsizliği ve exact ekonomik invariant’lar aynı state-machine’i etkiliyor. P1.07.a.1–a.4 ve P1.07.b fixed-slice dikey dilimleri tamamlandı. P1.07.c.1 ile fixed public response’ta `INDETERMINATE` fail-closed authority, c.2 ile capability-aware prefix action kanıtı, c.3 ile yalnız boundary-only annotation, d.1 ile bağımsız strict fixed-limit application policy uygulandı; incomplete persistence, volume/latency/queue/stop ve aynı-bar cancel-fill yarışı değiştirilmedi. Public limit contract d.2, mevcut DCA strategy binding kanıtlanmadığı için ertelendi. Sıradaki tek kapı `P1.07.d.3` DCA strategy binding araştırmasıdır.

### P1.07.a — Mevcut Core partial-fill uyumluluk audit kapısı

Durum: COMPLETE / LOCAL_PASS; araştırma kararı `SIMPLIFIED`. Kanıt: `evidence/P1.07/SONUC.md`. Prompt: `docs/P1.07.a_Mevcut_Core_Partial_Fill_Uyumluluk_Arastirma_Promptu.md`.

P1.07 raporu mevcut reducer ile karşılaştırıldı. Reducer manuel partial `FILL` ve `ORDER_FINAL(CANCELED)` gözlemini taşıyor; historical simulator aynı bar içinde full fill yapıyor, config schema’da explicit slice modeli yok ve persisted action contract’ı lifecycle için yetersiz. Bu audit sonrasında yalnız `Order` üzerinde `PARTIALLY_FILLED`, exact `leaves` ve explicit cancel `canceled` görünümü eklendi; late-fill `UNKNOWN` korundu. Historical model/API/config değişikliği sonraki mikro faza bırakıldı.

### P1.07.a.1 — Core order partial-state görünümü

Durum: COMPLETE / LOCAL_PASS. Kanıt: `evidence/P1.07/SONUC.md`.

`FILL` ile order quantity conservation görünümü açıklaştırıldı: partial fill `PARTIALLY_FILLED`, açık remainder `leaves`, explicit cancel remainder `canceled`. Legacy historical path, reserve, latency, stop ve same-bar race değiştirilmedi. TDD RED→GREEN, late-fill kontrolü, tam `114/114` regresyonu, compile ve workspace PASS. Sonraki tek iş P1.07.a.2’dir.

### P1.07.a.2 — Opt-in historical fixed-slice runner

Durum: COMPLETE / LOCAL_PASS. Kanıt: `evidence/P1.07/SONUC.md`.

Raporun önerdiği `historical_ohlcv_partial_fixed_v1` application runner olarak eklendi. Yalnız explicit `slice_qty`, aynı order’ın çok barlı lifecycle’ı, bar başına tek fill, exact remainder ve EOF’de sentetik cancel yerine `OPEN_AT_END` davranışı var. RED→GREEN, farklı ambiguity/determinism kontrolü, tam `119/119` regresyon, compile ve workspace PASS. Public API/action v2 ve UI henüz bağlanmadı.

### P1.07.a.3 — Fixed-slice public profile/config/response contract

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.07/SONUC.md`.

Yeni application runner strict opt-in `historical_demo_btcusdt_1h_partial_fixed_v1` profile/config ve versioned public response/action contract’ına bağlandı. Fixed model config hash’i execution policy’yi kapsıyor; run-plan/validation için ayrı strict DTO’lar ve lifecycle action alanları var. Legacy `historical_ohlcv_v1`, `paper` profile, legacy run-plan/validation/simulation response’ları ve frontend davranışı korunuyor. Fixed response `execution_id=null`, `persisted=false` ile P1.06 persistence’ından ayrılıyor. TDD RED→GREEN, `121/121` tam regresyon, OpenAPI, compile ve workspace PASS. UI görsel değişikliği yapılmadı.

### P1.07.a.4 — Fixed-slice gerçek ASGI HTTP smoke

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.07/SONUC.md`.

Opt-in fixed profile için gerçek ASGI request/response serileştirmesi ve strict response union smoke kontrol edildi. `1/1 PASS`; `execution_id=null`, `persisted=false` ve lifecycle action alanları doğrulandı. Fixed profile mevcut UI selector’a veya P1.06 save akışına açılmadı.

### P1.07.b — Fixed-slice UI/UX araştırma kapısı

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.07/SONUC.md`. Araştırma girdisi: `P1.07.b_Fixed_Slice_UI_UX_Detayli_Arastirma_Raporu_2026-09-08.md`.

Fixed profile mevcut selector’a explicit opt-in olarak açıldı; model farkı yardımcı metinle anlatılıyor. Onay checkbox’ı işaretlenmeden başlatma engelleniyor ve hata checkbox’a odaklanıyor. Determinate fixed sonuçta backend action lifecycle alanları Original → Cumulative filled → Leaves ana sırasıyla gösteriliyor; teknik kimlik/provenance alanları native disclosure içinde ve kopyalama düğmeleriyle sunuluyor. `INDETERMINATE` durumda ekonomik özet, grafik ve action history gizli kalıyor; frontend belirsizlik üretmiyor. Fixed sonuçta `persisted=false` nedeniyle save CTA kaldırıldı ve kaydedilemez notu gösteriliyor. 320px/390px responsive ölçümleri, keyboard/focus akışı, copy disclosure, frontend build, tam backend `122/122` regresyon, compile, workspace ve Browser/IAB console QA PASS.

### P1.07.c — INDETERMINATE action authority araştırma kapısı

Durum: RESEARCH_RECEIVED; P1.07.c.1 COMPLETE / LOCAL_PASS; P1.07.c.2 COMPLETE_WITH_LIMITATION / LOCAL_PASS. Prompt: `docs/P1.07.c_Indeterminate_Action_Authority_Arastirma_Promptu.md`; c.2 raporu: `P1.07.c.2_Committed_Prefix_Marker_Ayrintili_Arastirma_Raporu.md`.

Kullanıcı araştırması talimat değil, doğrulanacak kanıt olarak değerlendirildi. Raporun `INDETERMINATE` için authority, cutoff, no-final-summary ve marker fail-closed kararları mevcut fixed runner/API ile kontrol edildi. P1.07.c.1’de legacy client’ın yanlış yorumlayabileceği çıplak prefix public response’tan çıkarıldı; c.2’de explicit fixed capability ile prefix kanıtı kontrollü biçimde açıldı. Marker için doğrudan trading-domain kanıtı ve incomplete persistence semantiği bulunmadığından marker/persistence uygulanmadı; `marker_authority=NONE` korunuyor.

### P1.07.c.1 — Fixed indeterminate fail-closed public contract

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.07/SONUC.md`.

Fixed response’a `complete_execution`, machine-readable `action_authority`, `marker_authority` ve nullable `final_economic_summary` alanları eklendi. `INDETERMINATE / AMBIGUOUS_OHLC_PATH` durumunda application’ın iç prefix’i public DTO’ya sızmaz; ambiguity barı ve sonrası için action/marker/final ekonomik özet yayınlanmaz. Completed fixed result’ta action lifecycle ve ekonomik özet `FULL_RUN` authority ile aynı içerikte kalır. Legacy `historical_ohlcv_v1` response/persistence sözleşmesine bu dilimde alan sızdırılmadı.

RED→GREEN: yeni ambiguity fixture’ı önce dört prefix action’ının çıplak biçimde döndüğünü göstererek başarısız oldu; minimum public DTO filtresi ve authority alanları sonrası odak API `10/10 PASS` verdi. Bağımsız gerçek ASGI response kontrolü aynı fixture’da `actions=[]`, `NONE`, nullable final summary ve eski `summary` alanının yokluğunu doğruladı. Tam regresyon `123/123 PASS`, compile, workspace ve frontend build PASS.

### P1.07.c.2 — Capability-aware committed prefix ve marker

Durum: COMPLETE_WITH_LIMITATION / LOCAL_PASS; bağımsız review: NOT_RUN. Araştırma girdisi: `P1.07.c.2_Committed_Prefix_Marker_Ayrintili_Arastirma_Raporu.md`. Kanıt: `evidence/P1.07/SONUC.md`.

Raporun yalnız doğrulanabilir ve güvenli kısmı uygulandı. Fixed `historical_ohlcv_partial_fixed_v1` için request’e açık `action_authority` capability’si eklendi; varsayılan `NONE` kaldı ve `COMMITTED_PREFIX` legacy `historical_ohlcv_v1` yolunda sessizce yok sayılmak yerine `422 UNSUPPORTED_ACTION_AUTHORITY` ile reddedildi. Explicit prefix isteğinde yalnız ambiguity öncesi backend action snapshot’ları döner; `event_sequence`, cutoff bar/zaman/event ve `PREFIX_ONLY` kapsamı görünürdür. `complete_execution=false`, `complete_history=false`, `final_economic_summary=null`, `marker_authority=NONE` ve ambiguity/post-ambiguity action guard’ları korunur. UI’da prefix eylemleri ayrı, salt-okunur “PREFIX KANITI” tablosunda gösterilir; normal action marker çizilmez.

Raporun doğrudan finansal marker kanıtı olmadığından prefix marker, persistence ve incomplete run save/reopen bu mikro dilime alınmadı. Legacy default response, fixed completed `FULL_RUN` sonucu ve P1.06 persistence akışı korunuyor.

Doğrulama: odak API `11/11 PASS`; tam Python regresyonu `124/124 PASS`; frontend `npm run build PASS`. c.2’nin sonraki marker authority kapısı c.3’te boundary-only kararıyla kapanmıştır; limit/stop/gecikme gibi ekonomik davranışlar için ayrı araştırma gereklidir.

### P1.07.c.3 — Marker authority araştırması ve boundary-only uygulaması

Durum: COMPLETE_WITH_LIMITATION / LOCAL_PASS; bağımsız review: NOT_RUN. Araştırma girdisi: `P1.07.c.3_Marker_Authority_Ayrintili_Arastirma_Raporu.md`. Kanıt: `evidence/P1.07/SONUC.md`.

Raporun `SIMPLIFY` kararı uygulandı: `INDETERMINATE + COMMITTED_PREFIX` için normal trade/action marker eklenmedi. Bunun yerine API’de `marker_authority=PREFIX_BOUNDARY_ONLY` ve `marker_kind=INCOMPLETE_BOUNDARY` ayrımıyla yalnız ambiguity barı başlangıcında nötr, çizgili ve metin etiketli boundary annotation gösteriliyor. Boundary; dataset/artifact, ambiguity bar/zamanı, committed cutoff, action count, event sequence, bar index ve action timestamp invariant’larını geçmeden çizilmiyor. Geçemezse yalnız annotation layer kapanıyor; OHLC chart, warning ve geçerli prefix tablosu korunuyor.

UI’da boundary interaktif değil, tooltip/crosshair/hover/focus/animasyon yok; görünür `INCOMPLETE · BAR n` etiketi, caption ve screen-reader açıklamasıyla destekleniyor. Grafik yalnız explicit prefix authority’de indeterminate sonuca açılıyor; `OPEN_AT_END`, legacy response, persistence ve ekonomik hesap değişmedi. Prefix action’ları price chart üzerinde marker olarak çizilmedi.

Doğrulama: ilk TypeScript build kontrolü event sequence type guard hatasını yakaladı; düzeltme sonrası frontend `npm run build PASS`. Odak API `11/11 PASS`; tam Python regresyonu `124/124 PASS`; `compileall PASS`; `tools/check_workspace.py PASS`. Sonraki tek iş P1.07 içindeki limit/stop/gecikme gibi yeni ekonomik davranışlar için ayrı kanıt kapısıdır.

### P1.07.d — Tarihsel limit trigger/fill araştırma kapısı

Durum: RESEARCH_RECEIVED; d.1 application mikro dilimi COMPLETE / LOCAL_PASS. Anonim araştırma promptu: `docs/P1.07.d_Limit_Order_Trigger_Fill_Arastirma_Promptu.md`; rapor: `P1.07.d_Limit_Order_Trigger_Fill_Ayrintili_Arastirma_Raporu.md`.

Bu kapı yalnız OHLCV üzerinde limit order placement zamanı, touch/equality trigger kuralı, gap/open dolum fiyatı, exact fixed-slice/remainder uyumu ve EOF davranışını inceler. Stop, cancellation yarışı, latency, queue, volume participation, persistence, UI ve kapsamlı ekonomik metrikler bu kapının dışındadır. Raporun `SIMPLIFY` kararıyla yalnız explicit, bağımsız application policy dilimi açıldı; legacy veya mevcut public fixed profile’a bağlanmadı.

### P1.07.d.1 — Explicit fixed-limit application policy

Durum: COMPLETE / LOCAL_PASS; bağımsız review: NOT_RUN. Kanıt: `evidence/P1.07/SONUC.md`.

Yeni `src/dcabot/application/historical_fixed_limit.py` modülü yalnız explicit `FIXED_LIMIT_STRICT_V1` policy’sini uygular: placement barı eligible değildir; sonraki canonical barlar değerlendirilir; BUY için `low < limit`, SELL için `high > limit` strict penetration sentetik fill gözlemi verir; equality yalnız `EQUALITY_TOUCH` observation olarak kalır; fill exact `limit_price` ile bir fixed slice’tır; bar başına tek fill, exact remainder ve EOF’de `OPEN_AT_END` korunur. Same-bar ekonomik sıra belirsizliği application seam üzerinden `INDETERMINATE / AMBIGUOUS_OHLC_PATH` olarak fail-closed’dur. Fee, slippage, tick uydurma, open price improvement ve gerçek exchange execution iddiası eklenmedi.

RED → GREEN odak testleri ve production kodundan bağımsız Decimal tablo oracle kontrolü `7/7 PASS`; tam regresyon `131/131 PASS`; `compileall PASS`. Public profile/API, legacy historical model, persistence, UI ve marker authority değiştirilmedi. P1.07.d.2 public contract değerlendirmesi `DEFER` edildi; sonraki tek iş, public entegrasyondan önce DCA strategy binding araştırma kapısı olan P1.07.d.3’tür.

### P1.07.d.2 — Public contract araştırma kapısı

Durum: DEFERRED; karar `DEFER`; implementation başlamadı. Rapor: `P1.07.d.2_Limit_Order_Public_Contract_Ayrintili_Arastirma_Raporu.md`. Prompt: `docs/P1.07.d.2_Limit_Order_Public_Contract_Arastirma_Promptu.md`.

D.1 application policy’sini public profile/run-plan/HTTP response’a bağlama adımı bilinçli olarak durduruldu. Yerel kontrol mevcut public contract’ı gösterse de d.1 generic single-limit policy’sinin DCA strategy state, role, anchor, reserve ve economic posting’e bağlandığı kanıtlanmadı. Public endpoint/profile açmak yerine bu eksik binding için d.3 araştırması gerekiyor. Persistence, UI, marker ve canlı exchange kapsam dışıdır.

### P1.07.d.3 — DCA strategy binding araştırma kapısı

Durum: RESEARCH_RECEIVED / DEFERRED; implementation başlamadı. Araştırma raporu: `P1.07.d.3_DCA_Limit_Strategy_Binding_Ayrintili_Arastirma_Raporu(1).md`. Prompt: `docs/P1.07.d.3_DCA_Limit_Strategy_Binding_Arastirma_Promptu.md`.

Raporun BASE-only aday önerisi production’a alınmadı. Yerel kontrolde çekirdeğin INTENT/FILL/ORDER_FINAL, partial leaves, BASE anchor, safety blocker ve late-fill invalidation davranışları mevcut testlerle kanıtlandı; ancak d.1 fixed-limit observation’ının DCA order state’e güvenli adapter olarak bağlandığı, reserve lifecycle’ının ve BASE-only end-to-end ekonomik posting zincirinin kanıtı yok. SAFETY ve EXIT DEFER olarak kaldı. Public API, persistence, UI ve marker kapsam dışıdır.

P1.07.d.3.a tamamlandı: internal BASE-only probe, d.1 observation’dan existing core INTENT/FILL/ORDER_FINAL zincirine geçişi kanıtlıyor; `reserve_model=NONE` ve `production_ready=false` sınırı korunuyor. Odak testleri `6/6 PASS`; kanıt: `evidence/P1.07.d.3.a/SONUC.md`. Bu probe production DCA reserve kanıtı değildir.

P1.07.d.3.b araştırması alındı ve yerel kontrollerle değerlendirildi. Mevcut BASE-only v1 için karar `SIMPLIFY_WITH_LIMITATION`: `reserve_model=NONE`, numeric reserve iddiası yok, pending blocker lifecycle gate, accepted core FILL tek ekonomik authority, equality/candidate no-op ve EOF `OPEN_AT_END`. Yeni explicit reserve ledger için karar `DEFER`; raporun asset/unit/owner/fee/partial/EOF/ambiguity/duplicate/atomicity kapıları local code/test ile kapanmadı. Kanıt: `evidence/P1.07.d.3.b/SONUC.md`.

P1.07.d.3.c tamamlandı: `reserve_model=NONE` için `NOT_MODELED`/`NOT_APPLICABLE` metadata sınırı eklendi; pending BASE → SAFETY blokajı ve full-fill/final-coverage ayrımı acceptance testleriyle kapatıldı. Odak `9/9 PASS`, tam regresyon `140/140 PASS`, compile ve workspace PASS; internal probe `production_ready=false` olarak kaldı. Kanıt: `evidence/P1.07.d.3.c/SONUC.md`.

### P1.07.d.2.b — BASE-bound public limit contract readiness

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.07.d.2.b/SONUC.md`.

Yalnız explicit `historical_demo_btcusdt_1h_v1` fixture’a bağlı `POST /api/historical-runs/simulate-base-limit` public contract’ı eklendi. Strict exact-decimal request, dataset/artifact/config doğrulaması, sunucu kontrollü BASE quantity, observation/fill ayrımı, deterministic `binding_identity_sha256`, fail-closed `INDETERMINATE`, `reserve_model=NONE` metadata’sı, `no-store` ve bounded response sınırı uygulandı. Legacy route/fixed-slice route, persistence, UI ve profile katalog akışı değiştirilmedi. Review’de validation-error path’inin generic JSON/no-cache davranışı RED ile doğrulandı ve Problem Details + `no-store` olarak düzeltildi. Tam regresyon `151/151 PASS`; compile, workspace ve OpenAPI route kontrolleri PASS.

Bu bir genel DCA/production execution adapter’ı değildir. Explicit numeric reserve ledger, SAFETY/EXIT, cancellation race, latency/queue/volume/stop, persistence, marker/UI ve canlı venue kapsam dışıdır.

Bağımsız review `NOT_RUN` kalır: scoped security scan reportable bulgu üretmedi, ancak delegated bağımsız worker yoktu ve scan snapshot’ı son düzeltmeden önceydi. Bu nedenle bağımsız acceptance yerine geçmez.

### P1.08.a — Lifecycle authority local inventory

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.a/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/05_P1.08_DEAL_LIFECYCLE.md`, LCR-02.

Mevcut reducer’ın economic `INTENT/FILL/ORDER_FINAL/UNKNOWN/MARK` authority’siyle saf deal lifecycle authority’si ayrıldı. Araştırmadaki çelişkili `STARTED/RUNNING` ve `STARTING/ACTIVE` adları yeni ekonomik durumlar olarak kabul edilmedi: kalıcı projection `DRAFT -> RUNNING <-> PAUSED -> COMPLETED | ABORTED | FAILED`; `START` bir olaydır. Deal ve config-revision kimliği immutable kalır; geçiş sayacı yalnız geçerli transition ile artar. Declarative transition table ve negatif geçiş testi RED -> GREEN çalıştırıldı; tam regresyon `153/153 PASS`, compile ve workspace PASS.

Bu, production lifecycle değildir: persistence/reopen/replay, event identity/dedupe, gerçek immutable config revision kaydı ve COPY, cooldown, pause altındaki order policy, UI, shared account/reserve ve tüm ekonomik mutation kapsam dışıdır.

### P1.08.b — Lifecycle config-revision binding contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.b/SONUC.md`.

`COPY`, aktif lifecycle projection’ı değiştirmeden caller’ın sağladığı yeni deal kimliği ve yeni config-revision kimliğiyle `DRAFT` projection üretir. Kaynak deal veya config revision kimliğinin tekrar kullanımı reddedilir. RED import failure -> GREEN copy/negative testleri, tam regresyon `155/155 PASS`, compile ve workspace PASS.

Bu, config revision snapshot/store veya persisted COPY değildir: yeni revision’ın içerik hash’i, persistence/replay, event identity/dedupe, cooldown, pause-order policy, UI, shared-account/reserve ve ekonomik mutation kapsam dışıdır.

### P1.08.c — Lifecycle persistence/replay authority inventory

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.c/SONUC.md`.

Mevcut `Store` ekonomik event journal’ında batch-idempotency ve FILL execution-id dedupe/conflict; `HistoricalRunStore` ise source-execution idempotency/conflict ve immutable sonuç kaydı taşıyor. Bunlar lifecycle event’inin deal/config-revision/status/cursor authority’si değildir. Lifecycle persistence/replay için ayrı schema veya adapter mevcut olmadığı yerel kodla doğrulandı; yeni production davranışı eklenmedi.

### P1.08.d — Lifecycle event identity contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.d/SONUC.md`.

Lifecycle event contract’ı caller-supplied immutable event ID, deal/config-revision scope ve ardışık event sequence taşır. Aynı tam kayıt ikinci kez gelirse `DUPLICATE`, aynı ID farklı immutable alanla gelirse `LIFECYCLE_EVENT_CONFLICT`, farklı scope veya sequence gap ise fail-closed rejection döner. RED import failure -> GREEN odak testleri; tam regresyon `158/158 PASS`, compile ve workspace PASS.

Bu contract ekonomik journal’a veya persistence’a bağlı değildir; hash/canonical serialization, terminal transition enforcement, API/UI, cooldown, pause-order policy ve ekonomik posting kapsam dışıdır.

### P1.08.e — Lifecycle event-to-transition adapter

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.e/SONUC.md`.

Accepted lifecycle event önce event identity/scope/sequence contract’ından, sonra saf `DealLifecycle` transition tablosundan geçirilir. Geçerli event projection ve history’yi birlikte ilerletir; exact duplicate ikisini de değiştirmez; invalid transition history’ye eklenmez. RED import failure -> GREEN adapter testleri; tam regresyon `161/161 PASS`, compile ve workspace PASS.

Persistence/replay, API/UI, config snapshot/hash, cooldown, pause-order policy, shared account/reserve veya ekonomik mutation bu dilimde açılmadı.

### P1.08.f — Persistent lifecycle record boundary

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.f/SONUC.md`.

Ekonomik `Store`’dan ayrı versioned lifecycle SQLite store eklendi. Store yalnız lifecycle event kayıtlarını transaction içinde yazar; event kimliği, deal/config-revision scope ve sequence replay ile doğrulanır. Yeniden açma aynı projection/history üretir; exact duplicate idempotent kalır; conflict, invalid transition ve satır/payload uyumsuzluğu fail-closed reddedilir. RED import failure -> GREEN store testleri; tam regresyon `164/164 PASS`, compile ve workspace PASS.

Store API/UI’ya açılmadı; config snapshot/hash, cooldown, pause-order policy, shared account/reserve ve ekonomik posting kapsam dışıdır.

### P1.08.g — Config revision snapshot binding

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.g/SONUC.md`.

Lifecycle store artık event’in `config_revision_id` değerini ayrı immutable canonical config snapshot + SHA-256 kaydıyla zorunlu olarak bağlıyor. Aynı revision ID farklı snapshot ile kullanılamaz; row/payload ve revision snapshot/hash uyumsuzlukları fail-closed reddedilir. Eşdeğer JSON field order tek revision kimliği üretir, config değişince hash değişir. RED import failure -> GREEN binding/conflict testleri; tam regresyon `167/167 PASS`, compile ve workspace PASS.

Bu yalnız local snapshot binding’dir; API/UI, config editing, COPY persistence, cooldown, pause-order policy, shared account/reserve ve ekonomik posting kapsam dışıdır.

### P1.08.h — Lifecycle terminal/cooldown policy contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.h/SONUC.md`.

Terminal `COMPLETED`, `ABORTED` ve `FAILED` projection’ları için sonraki lifecycle event reddi mevcut transition adapter üzerinden korundu; reddedilen event history/projection’ı değiştirmiyor. Yeni saf `cooldown_allows_new_deal` politikası yalnız integer historical `effective_time_us` farkını kullanıyor, eşit sınırı kabul ediyor ve geriye giden zaman/negatif süreyi fail-closed reddediyor. Wall-clock, processing-time, persistence, API/UI ve ekonomik state mutation eklenmedi. RED import failure -> GREEN odak policy testleri; tam regresyon `170/170 PASS`, compile ve workspace PASS.

Sonraki tek iş: `P1.08.i` pause altındaki order policy contract’ını araştırma kanıtı ve saf test sınırıyla değerlendirmek.

### P1.08.i — Pause altında order policy contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.i/SONUC.md`.

PAUSED lifecycle için saf `evaluate_paused_orders` contract’ı eklendi. Üç explicit policy (`KEEP_OPEN`, `CANCEL_REQUESTED`, `BLOCKED`) mevcut pending order davranışını tanımlar; üçünde de yeni economic intent `BLOCKED` kalır. `CANCEL_REQUESTED` yalnız `REQUESTED_NOT_CONFIRMED` bildirir; otomatik cancellation, fill, reserve release, persistence, API/UI veya ekonomik mutation iddiası taşımaz. Bilinmeyen policy fail-closed reddedilir. RED import failure -> GREEN odak policy testleri; tam regresyon `173/173 PASS`, compile ve workspace PASS.

Sonraki tek iş: P1 plan sırasındaki sonraki READY mikro-fazı, mevcut kanıt ve bağımlılıklar yeniden kontrol edilerek seçilecektir.

### P1.09.a — Exact BASE/QUOTE sizing candidate contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.a/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

`build_sizing_candidate` ile explicit `BASE_QTY` ve `QUOTE_NOTIONAL` farklı birimlerde parse ediliyor; QUOTE notional yalnız explicit positive reference price ile aday BASE quantity’ye çevriliyor. Aday quantity/notional exact decimal string olarak üretiliyor ve eşdeğer BASE/QUOTE girdileri bağımsız testle aynı sonucu veriyor. `BALANCE_PERCENT`, venue quantity/tick quantization, min-notional/risk kabulü, ladder, reinvestment, API/UI, persistence ve economic posting bu mikro dilime alınmadı. Unknown/malformed/zero input fail-closed. RED import failure -> GREEN odak testleri; tam regresyon `176/176 PASS`, bağımsız odak unittest, compile ve workspace PASS.

Sonraki tek iş: P1.09.b exact ladder allocation/conservation contract’ı; venue rounding owner netleşmeden public/API/UI bağlantısı yapılmayacak.

### P1.09.b — Exact ladder allocation/conservation contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.b/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

`validate_ladder_allocations` explicit `BASE_QTY` veya `QUOTE_NOTIONAL` birimindeki allocation tuple’ını exact toplar, explicit budget ile karşılaştırır ve kalan bütçeyi aynı birimde döndürür. Bütçe aşımı, bilinmeyen birim ve geçersiz/zero allocation fail-closed reddedilir. Venue quantization, instrument metadata, risk kabulü, reserve/economic posting, ladder price generation, balance-percent, reinvestment, API/UI ve persistence bu mikro dilime alınmadı. RED import failure -> GREEN odak testleri; tam regresyon `179/179 PASS`, bağımsız odak unittest, compile ve workspace PASS.

Sonraki tek iş: `P1.09.c` venue quantization/filter owner contract’ı; profile kanıtı olmadan rounding veya public order davranışı eklenmeyecek.

### P1.09.c — Profile-bound instrument filter contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.c/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

`InstrumentFilterProfile` explicit `profile_id`, quantity step, price tick, minimum quantity ve minimum notional metadata’sını sahipleniyor. `validate_order_candidate` yalnız profile grid’inde olan, minimumları ve exact notional filtresini geçen adayları doğruluyor; off-grid veya minimum altı aday fail-closed reddediliyor. Rounding yönü seçilmedi ve aday otomatik quantize edilmedi. Venue, live/testnet, risk acceptance, reserve, API/UI, persistence ve economic posting bu mikro dilime alınmadı. RED import failure -> GREEN odak testleri; tam regresyon `182/182 PASS`, bağımsız odak unittest, compile ve workspace PASS.

Sonraki tek iş: `P1.09.d` balance-percent sizing için eligible balance kaynağı ve exact budget contract’ı; kaynak belirsizse numeric sıfır varsayılmayacak.

### P1.09.d — Tagged eligible-balance percent budget contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.d/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

`build_balance_percent_budget`, caller’ın sağladığı açık `balance_source`, asset, positive `eligible_balance` ve `0 < percent <= 1` değerleriyle exact `budget = eligible_balance * percent` projection’ı üretir. Total wallet, available/reserved ayrımı, balance discovery, reserve creation, risk acceptance veya order posting yapılmaz; kaynak/asset/percent/zero input fail-closed reddedilir. RED import failure -> GREEN odak testleri; tam regresyon `185/185 PASS`, bağımsız odak unittest, compile ve workspace PASS.

Sonraki tek iş: `P1.09.e` exact ladder generation’ın sizing candidate ve conservation contract’larına bağlanması; venue quantization tamamlanmadan public/API/UI yolu açılmayacak.

### P1.09.e — Exact ladder generation binding

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.e/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

Mevcut domain `build_plan` çıktısı exact application binding’e alındı: generated price/quantity seviyeleri açık allocation unit’e (`BASE_QTY` veya `QUOTE_NOTIONAL`) dönüştürülüyor ve P1.09.b conservation contract’ı ile budget’a karşı doğrulanıyor. BASE ve QUOTE allocation’ları bağımsız exact fixture ile kontrol edildi; budget aşımı ve collapsed/invalid ladder fail-closed. Venue rounding/filter, balance authority, risk acceptance, reserve, economic posting, API/UI ve persistence bağlanmadı. RED import failure -> GREEN odak testleri; tam regresyon `188/188 PASS`, bağımsız odak unittest, compile ve workspace PASS.

Sonraki tek iş: P1.09.f reinvestment eligibility contract’ı; yalnız realized eligible pool için araştırma ve local ledger kanıtı varsa ilerlenir.

### P1.09.f — Realized-profit eligible reinvestment contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.f/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

`build_reinvestment_budget`, yalnız asset etiketli `realized_profit_eligible` pool ve `0..1` percent ile exact budget projection’ı üretir. Negative pool, invalid asset/percent fail-closed; zero pool/zero percent `0` budget verir. Unrealized PnL, fee/funding, account ledger, reserve, API/UI, persistence ve economic posting bu dilimde kullanılmadı. RED import failure -> GREEN odak testleri; tam regresyon `191/191 PASS`, bağımsız odak unittest, compile ve workspace PASS.

Sonraki tek iş: `P1.09.g` sizing candidate + ladder + instrument filter + eligible budget birleşimi için saf pre-acceptance gate; mevcut kanıt yetersizse public/UI bağlantısı açılmayacak.

### P1.09.g — Sizing pre-acceptance gate

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.g/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

P1.09.a–f sözleşmeleri saf bir pre-acceptance gate’te birleştirildi. İlk güvenli kapsam yalnız ortak `QUOTE_NOTIONAL` unit, aynı quote asset, profile-bound instrument filters ve eligible balance budget’tır. Candidate notional + ladder notional toplamı eligible budget’ı aşamaz; candidate/ladder snapshot uyuşmazlığı ve cross-unit/cross-asset durumları fail-closed reddedilir. Sonuç `order_authority=NONE` taşır; accepted intent, reserve, risk, API/UI, persistence veya economic posting açılmadı. RED import failure -> GREEN odak testleri; tam regresyon `194/194 PASS`, bağımsız odak unittest, compile ve workspace PASS.

Sonraki tek iş: `P1.09.h` pre-acceptance gate için bağımsız metamorphic/exact oracle kontrolleri; kanıt geçmeden public/API/UI sizing akışı açılmayacak.

### P1.09.h — Independent exact/metamorphic sizing oracle

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.h/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

Production kodu değiştirilmeden bağımsız Decimal oracle ve metamorphic testler eklendi. QUOTE candidate division, eşdeğer decimal yazımları, allocation sırası değişmezliği ve ladder price/notional formülü production output’tan bağımsız kontrol edildi. Test-only olduğu için import-failure RED uygulanmadı; tam regresyon `197/197 PASS`, bağımsız odak unittest `3/3 PASS`, Python 3.13 compile ve workspace `PASS`.

P1.09.a–h sizing zinciri public/API/UI akışına açılmadı; BASE/balance conversion, quantization owner, hacim/indikatör koşulları, risk, reserve, persistence ve economic posting hâlâ kapsam dışıdır.

Sonraki tek iş: `P1.09.i` için plan bağımlılıklarını kontrol edip yalnız güvenli ve kanıtlanabilir bir sonraki sizing mikro-fazını seçmek.

### P1.09.i — BASE candidate quote commitment binding

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.i/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

P1.09.a exact `BASE_QTY` candidate, explicit referans fiyatla hesaplanmış quote notional’ı üzerinden P1.09.g pre-acceptance gate’e bağlandı. Candidate quantity/notional tutarlılığı, profile filter, quote asset, quote-unit ladder ve eligible budget kontrolleri korundu; cross-unit ladder reddediliyor. RED testi mevcut `PRE_ACCEPTANCE_UNIT_CONFLICT` davranışını gösterdi; GREEN sonrası gate `4/4`, tam regresyon `198/198`, bağımsız ilgili suite `9/9`, Python 3.13 compile/workspace `PASS`. `order_authority=NONE` korunuyor; reserve, risk, API/UI, persistence ve economic posting açılmadı.

Sonraki tek iş: P1.09 kapsamındaki kalan koşulları ve P1.10’a geçiş bağımlılığını yeniden kontrol ederek bir sonraki en küçük READY mikro-fazı seçmek.

### P1.10.a — Exit trigger/execution boundary

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.10.a/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Mevcut core reducer bağımsız testlerle doğrulandı: TP eşiği yalnız `EXIT` kararı üretir, `EXIT` intent pozisyon/PnL değiştirmez, yalnız ayrı `SELL` fill ekonomik geçiş yapar. Test-only olduğu için import-failure RED uygulanmadı; boundary suite `3/3 PASS`, farklı engine kontrolü `1/1 PASS`, tam regresyon `201/201 PASS`, Python 3.13 compile/workspace `PASS`. Multi-TP, trailing, breakeven, cancel-replace ve late-fill recovery bu dilime alınmadı.

Sonraki tek iş: `P1.10.b` multi-TP quantity conservation için mevcut core local contract ve bağımsız oracle kontrolü.

### P1.10.b — Multi-TP exact quantity conservation

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.10.b/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Saf application validation contract’ı eklendi: `free_exit_capacity = open_qty - accepted_exit_fills - committed_exit_qty`. Over-close fail-closed reddediliyor; split-fill ve exact remainder korunuyor; contract order/position mutation yapmıyor. RED import failure -> GREEN `4/4`, bağımsız Python 3.13 suite `7/7`, tam regresyon `205/205`, compile/workspace `PASS`. Multi-TP registry/OCO, cancel-replace, late fill, stop, trailing, breakeven, API/UI, persistence, reserve ve economic posting açılmadı.

Sonraki tek iş: `P1.10.c` stop trigger/execution ayrımının local contract kontrolü.

### P1.10.c — Stop trigger/execution boundary

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.10.c/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Mevcut core reducer bağımsız testlerle doğrulandı: halted state `STOP` kararı üretir, stop intent position/PnL değiştirmez, yalnız ayrı `SELL` fill ekonomik geçiş yapar. Test-only olduğu için import-failure RED uygulanmadı; stop boundary `3/3`, bağımsız TP+stop suite `6/6`, tam regresyon `208/208`, Python 3.13 compile/workspace `PASS`. Stop-market/stop-limit, gap/slippage, competing exit, cancel-replace, late fill, trailing ve breakeven açılmadı.

Sonraki tek iş: `P1.10.d` trailing ratchet contract kontrolü.

### P1.10.d — Long trailing ratchet

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.10.d/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Sabit mesafeli long trailing trigger projection’ı eklendi: `INACTIVE → ACTIVE(high_water, stop_price) → TRIGGERED`. Aktivasyon altı pasiflik, exact `high_water - distance`, favorable ratchet, retracement monotonicity ve trigger sınırı fail-closed testlerle doğrulandı. RED import failure -> GREEN trailing `5/5`, bağımsız Python 3.13 TP/STOP/trailing/multi-TP suite `15/15`, tam regresyon `213/213`, compile/workspace `PASS`. Yalnız trigger state’i vardır; execution, fill, position/PnL, API/UI, persistence, reserve, OCO/cancel-replace, late fill ve breakeven açılmadı.

Sonraki tek iş: `P1.10.e` trailing state’in exit capacity/trigger boundary ile birlikte kontrolü.

### P1.10.e — Trailing exit capacity binding

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.10.e/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

`TRIGGERED` long trailing state, multi-TP exit capacity contract’ına bağlandı. Accepted fill + mevcut commitment + yeni aday exact açık pozisyon kapasitesini aşarsa fail-closed; geçerli adayda trigger fiyatı ve kalan kapasite dönüyor, `order_authority=NONE` korunuyor. RED import failure -> GREEN binding `3/3`, bağımsız Python 3.13 ilgili suite `12/12`, tam regresyon `216/216`, compile/workspace `PASS`. Order/position mutation, reserve, OCO/cancel-replace, late fill, gap/slippage ve breakeven açılmadı.

Sonraki tek iş: `P1.10.f` breakeven için fee/asset conversion koşul ve karar kapısı.

### P1.10.f — Breakeven fee/asset conversion karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; kanıt: `evidence/P1.10.f/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Fee-aware breakeven için gerekli fee asset dönüşümü, beklenen çıkış maliyeti ve funding tahsisi yerel sözleşmede tanımlı olmadığı için kod değişikliği yapılmadı. Mevcut `NET_QUOTE` hesabı breakeven olarak yeniden adlandırılmadı; mevcut math testi yalnız generic NET_QUOTE davranışını doğruluyor. Bu mikro fazda production readiness `NO` olarak korunuyor.

Sonraki tek iş: `P1.10.g` short sabit-mesafeli trailing ratchet için bağımsız local contract kontrolü.

### P1.10.g — Short sabit-mesafeli trailing ratchet

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.10.g/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Short trigger-only projection eklendi: aktivasyon `price <= activation_price`, exact `stop = low_water + distance`, favorable düşüşte low-water ratchet ve `price >= stop` ile `TRIGGERED`. RED import failure -> GREEN long+short suite `10/10`, bağımsız Python 3.13 Decimal oracle `PASS`, tam regresyon `221/221 PASS`. Execution/fill, position/PnL, reserve, OCO/cancel-replace, gap/slippage, API/UI, persistence ve breakeven açılmadı; production readiness `NO`.

Sonraki tek iş: `P1.10.h` yüzde-mesafeli trailing ratchet için karar/uygulama kapısı.

### P1.10.h — Percentage trailing ratchet

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.10.h/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Long ve short percentage trigger-only projection eklendi: long `high_water × (1-rate)`, short `low_water × (1+rate)`; `0 < rate < 1`, exact Fraction hesabı, yönsel monotonic ratchet ve sınır trigger’ı doğrulandı. RED import failure -> GREEN suite `15/15`, bağımsız Python 3.13 Decimal oracle `PASS`, tam regresyon `226/226`, workspace/compile `PASS`. Execution/fill, position/PnL, reserve, OCO/cancel-replace, gap/slippage, API/UI, persistence ve breakeven açılmadı; production readiness `NO`.

Sonraki tek iş: `P1.10.i` trailing trigger’ın stop/exit execution boundary’sine bağlanması için karar kapısı.

### P1.10.i — Trailing trigger–exit boundary

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.10.i/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Trailing exit adapter’ı long/short fixed-distance ve percentage state’lerini ortak exact exit-capacity kontrolüne bağlıyor. Yalnız `TRIGGERED` state aday üretebiliyor; accepted fill, `ORDER_FINAL`, reserve, position/PnL mutasyonu yok; `order_authority=NONE` korunuyor. RED type-boundary failure -> GREEN binding `5/5`, dört variant bağımsız immutability control `PASS`, tam regresyon `228/228`, workspace/compile `PASS`. OCO/cancel-replace, late fill, gap/slippage, execution, API/UI, persistence, reserve ve breakeven açılmadı; production readiness `NO`.

Sonraki tek iş: `P1.10.j` OCO/cancel-replace ve late-fill kapasite karar kapısı.

### P1.10.j — OCO/cancel-replace ve late-fill kapasite karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; kanıt: `evidence/P1.10.j/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md` ve `docs/External_Claim_Verification/01_rapor/Ayrintili_Arastirma_Raporu.md`.

Mevcut reducer late fill’i `UNKNOWN` + `LATE_FILL_AFTER_FINAL` blocker’ına alıyor; partial/cancel, duplicate/conflict ve pending-order kontrolleri çalışıyor. Buna rağmen trailing’e özgü OCO üyeliği, cancellation confirmation, replacement identity, late-fill authority ve reserve/commitment owner sözleşmesi yok. Kod veya numeric reserve davranışı eklenmedi. Odak suite `27/27 PASS`, tam regresyon `228/228 PASS`, workspace/compile `PASS`; production readiness `NO`.

Sonraki tek iş: `P1.10.k` trailing public/API/UI readiness karar kapısı.

### P1.10.k — Trailing public/API/UI readiness karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; kanıt: `evidence/P1.10.k/SONUC.md`; ilgili araştırma: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Mevcut public historical response chart/action/authority sözleşmesini taşıyor ancak trailing state, trigger-candidate identity ve execution lifecycle alanlarını taşımıyor. UI’da yeni trailing görünümü veya marker semantiği eklenmedi; görsel araştırma ve OCO/cancel-replace/reserve önkoşulları kapanmadı. Güncel tam regresyon `228/228 PASS`, workspace/compile `PASS`; kod değişikliği yok, production readiness `NO`.

Sonraki tek iş: `P1.11.a` ortak sanal hesap için account/position ownership ve isolation karar kapısı.

### P1.11.a — Ortak sanal hesap ownership/isolation karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; kanıt: `evidence/P1.11.a/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md`.

P1.11 araştırması concurrent reservation ve replay’i `LOCAL_CODE_REQUIRED` olarak işaretliyor. Yerel model deal lifecycle/config-revision scope’u taşıyor ancak shared account balance/reservation ledger, pair/deal position owner ve account version conflict boundary taşımıyor. Multi-bot/account mutation eklenmedi. Güncel tam regresyon `228/228 PASS`, workspace/compile `PASS`; production readiness `NO`.

Sonraki tek iş: `P1.11.b` shared-account immutable identity ve account/deal/position ownership contract karar kapısı.

### P1.11.b — Shared-account immutable identity contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.11.b/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md`.

Ekonomik davranışa dokunmadan immutable `SharedAccountIdentity(account_id, product_id, position_mode, deal_id, allocation_id)` contract’ı eklendi. Her kimlik bileşeni scope-significant; `position_mode` bu mikro fazda opaque bırakıldı ve account balance/reservation/position allocation anlamı uydurulmadı. RED import failure -> GREEN identity suite `3/3`, bağımsız frozen/hash control `PASS`, tam regresyon `231/231`, workspace/compile `PASS`; production readiness `NO`.

 Sonraki tek iş: `P1.11.c` account reservation ledger ve account-version concurrency karar kapısı.

 ### P1.11.c — Account reservation capacity/version projection

 Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.11.c/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md`.

 Pure `AccountCapacity` + `AccountReservation` projection’ı eklendi: `available = capacity - Σactive_reservations`, same-account/same-asset scope, duplicate ID ve stale account version fail-closed; `ReservationProjection` version+1 döndürüyor. RED import failure → GREEN `5/5`, bağımsız Fraction oracle `PASS`, tam regresyon `236/236`, workspace/compile `PASS` (`100` aktif Python dosyası). Persistence, atomic multi-writer locking, fill/release, replay, API/UI ve production reservation ledger açılmadı; production readiness `NO`.

 Sonraki tek iş: `P1.11.d` atomic reservation persistence/replay ve fill/release karar kapısı.

### P1.11.d — Atomic reservation persistence ve account-version boundary

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.11.d/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md`.

Dedicated `ReservationLedger` SQLite modülü eklendi. `BEGIN IMMEDIATE` transaction içinde capacity, active reservation toplamı, reservation commit metadata’sı ve account version artışı tek atomik yerel geçişte tutuluyor. Reopen, exact duplicate idempotency, conflicting duplicate, stale-version, capacity-overrun, unrelated SQLite file protection ve ikinci ledger instance kontrolleri var. RED import failure → GREEN ledger testleri ile tam regresyon `241/241 PASS`; bağımsız Fraction oracle `PASS`; workspace/compile `PASS` (`102` aktif Python dosyası). Mevcut economic `Store`/core reducer binding’i, fill/release, position commitment transferi, dedup/replay birleşimi, API/UI ve production readiness açılmadı.

 Sonraki tek iş: `P1.11.e` reservation fill/release, position commitment transferi ve mevcut economic Store binding karar kapısı.

### P1.11.e — Reservation fill/release ve economic Store binding karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; kanıt: `evidence/P1.11.e/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md`.

Mevcut core `FILL` event’i account/reservation owner taşımıyor; fill quantity base asset, reservation quote asset. `ORDER_FINAL` release miktarı ve reservation kimliği taşımıyor. Reservation ledger ile economic `Store` ayrı SQLite dosyalarında olduğundan atomic reserve + fill/release + posting transaction’ı kanıtlanamadı. Fee/slippage/rounding, partial/late/unknown/conflict authority ve commitment transferi eksik olduğu için kod veya adapter eklenmedi. Son doğrulanmış baseline `241/241 PASS`, workspace/compile `PASS` (`102` aktif Python dosyası), production readiness `NO`.

Sonraki tek iş: `P1.12.a` spot ve lineer futures ürün/settlement/fee/funding/teminat modelinin karar kapısı. P1.11.e yeniden açma koşulları kanıt dosyasında listelidir.

### P1.12.a — Linear futures PnL ve funding temel sınırı

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.12.a/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/09_P1.12_FUTURES_MODEL.md`.

Spot state’inden ayrı saf `LinearFuturesPosition`/`FundingProjection` eklendi. Explicit contract size ile effective quantity, settlement-asset position value, long/short signed unrealized PnL ve timestamped funding projection exact hesaplanıyor. RED import failure → GREEN suite ile tam regresyon `245/245 PASS`; bağımsız Decimal oracle `PASS`; workspace/compile `PASS` (`104` aktif Python dosyası). Leverage, margin, liquidation, mark/index adapter, venue profile, persistence, event replay, API/UI, fee ledger ve account binding açılmadı; production readiness `NO`.

Sonraki tek iş: `P1.12.b` linear futures partial-close, trading fee/funding ledger ve event/replay contract karar kapısı.

### P1.12.b — Linear futures partial-close quantity ve gross PnL

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.12.b/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/09_P1.12_FUTURES_MODEL.md`.

`project_partial_close` ile explicit contract-size partial/full close, kalan quantity conservation, long/short gross realized PnL ve over-close fail-closed sınırı eklendi. RED import failure → GREEN ile tam regresyon `248/248 PASS`; bağımsız Decimal oracle `PASS`; workspace/compile `PASS` (`105` aktif Python dosyası). Fee/funding net binding, event identity/replay, persistence, margin, liquidation, API/UI ve account binding açılmadı; production readiness `NO`.

Sonraki tek iş: `P1.12.c` timestamped funding/trading-fee ledger event identity, duplicate/replay ve net-result binding karar kapısı.

### P1.12.c — Linear futures fee/funding event projection

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.12.c/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/09_P1.12_FUTURES_MODEL.md`.

Immutable `LinearLedgerEvent`/`LinearLedgerState` eklendi. Trading fee pozitif expense, funding işaretli cashflow olarak ayrı tutuluyor; event identity, effective time ordering, exact duplicate idempotency/conflict, asset scope ve `gross - fee + funding` net binding projection’ı doğrulandı. RED import failure → GREEN ile tam regresyon `251/251 PASS`; bağımsız Decimal oracle `PASS`; workspace/compile `PASS` (`106` aktif Python dosyası). Persistence, existing economic Store binding, restart replay, fee tier/maker-taker, funding dataset, per-fill rounding, API/UI ve venue profile açılmadı; production readiness `NO`.

Sonraki tek iş: `P1.12.d` timestamped fee/funding event’lerinin mevcut economic Store içinde kalıcı replay/idempotency binding karar kapısı.

### P1.12.d — Futures fee/funding persistence ve core Store binding karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; kanıt: `evidence/P1.12.d/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/09_P1.12_FUTURES_MODEL.md`.

Mevcut Store generic `FILL` fee ve `FUNDING` posting’ini aynı SQLite transaction’ında, batch dedup/replay ile taşıyor; fakat `effective_time_us`, futures product/profile/position owner ve linear short/margin state’i taşımıyor. Strict event schema’yı migration/replay planı olmadan genişletmek güvenli değil; iki ayrı ledger’ı sonradan birleştiren adapter da atomicity kanıtı üretmez. Kod değişikliği yapılmadı. Son kod baseline `251/251 PASS`, bağımsız Decimal oracle `PASS`, workspace/compile `PASS` (`106` aktif Python dosyası), production readiness `NO`.

Sonraki tek iş: `P1.12.e` isolated margin terminolojisi ve seçilmiş venue-profile kapsamı için karar kapısı.

### P1.12.e — Isolated margin ve venue profile karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; kanıt: `evidence/P1.12.e/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/09_P1.12_FUTURES_MODEL.md`.

Mevcut `leverage`/`initial_equity` yalnız CORE01 local teaching IM estimate ve sentetik başlangıç varsayımıdır; venue margin balance, available margin, collateral, MMR veya liquidation authority değildir. Araştırma isolated/cross kapsamını venue/profile/risk-tier bağımlı, liquidation’ı generic formüle kapalı sınıflandırıyor. Numeric margin/liquidation, collateral conversion, margin API/UI ve profile adapter eklenmedi. Son kod baseline `251/251 PASS`, workspace/compile `PASS` (`106` aktif Python dosyası), production readiness `NO`.

Sonraki tek iş: `P1.13.a` spot grid ailesi için ayrı state-machine, inventory/fee ve level-generation karar kapısı.

### P1.13.a — Spot grid aritmetik seviye üretimi

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.13.a/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/10_P1.13_GRID_FAMILIES.md`.

`build_arithmetic_grid_levels` ile exact `(upper-lower)/N` step ve `N+1` decimal-string seviye üretimi eklendi. Pozitif/bounds/interval doğrulaması, 1–1000 sınırı ve exact decimal sözleşmesine sığmayan sonucu sessiz yuvarlamadan reddetme davranışı var. Geometric precision/quantization sahibi, inventory/fee, accepted FILL, order/replacement, trailing/reverse/infinity/leveraged grid ve UI bu mikro-faza alınmadı. Odak `4/4 PASS`, bağımsız Decimal oracle `PASS`, tam regresyon `255/255 PASS`, compile ve workspace `PASS` (`108` aktif Python dosyası).

Sonraki tek iş: `P1.13.b` spot grid inventory/fee ve accepted-fill cycle/replacement karar kapısı.

### P1.13.b — Spot grid accepted-fill inventory projection

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.13.b/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/10_P1.13_GRID_FAMILIES.md`.

`SpotInventoryState` ve `apply_accepted_spot_fill` ile accepted BUY/SELL fill’in exact base inventory ve signed quote cashflow etkisi eklendi. Sell yalnız sahip olunan base kapasitesi kadar geçerli; aynı canonical `fill_id` duplicate’i idempotent, farklı payload conflict olarak reddediliyor. Fee asset/rounding/posting, order/reserve/replacement, matched grid profit-total equity, geometric/trailing/reverse/infinity/leveraged grid ve UI açılmadı. Odak `4/4 PASS`, bağımsız Decimal inventory oracle `PASS`, tam regresyon `259/259 PASS`, compile ve workspace `PASS` (`110` aktif Python dosyası).

Sonraki tek iş: `P1.13.c` spot grid fee asset/rounding ve matched cycle profit ile total equity ayrımının karar kapısı.

### P1.13.c — Spot grid fee ve cycle/equity karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.13.c/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/10_P1.13_GRID_FAMILIES.md`.

Local core `FILL` yalnız `quote_asset` fee kabul ediyor ve `State.fees` tek scalar toplam taşıyor; spot base-fee/third-asset inventory ve multi-asset mark authority yok. Fee asset/sign/rounding owner ile matched cycle profit-total equity köprüsü seçilmeden numeric grid net sonucu eklenmedi. Fee posting, geometric quantization, accepted fill Store binding, replacement, reserve, API/UI ve public grid sonucu açılmadı. Önceki kod baseline `259/259 PASS`, compile/workspace `PASS` (`110` aktif Python dosyası); production readiness `NO`.

Sonraki tek iş: `P1.13.d` geometric seviye precision/quantization karar kapısı; kanıt yetersizse güvenli DEFER.

### P1.13.d — Geometric grid precision ve quantization karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.13.d/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/10_P1.13_GRID_FAMILIES.md`.

Geometric `r=(upper/lower)^(1/N)` sonucu genel olarak exact Fraction değildir. Precision, N semantiği, endpoint/level sayısı, tick origin, rounding direction/mode ve quantization owner profile’e bağlanmadan ekonomik level üretilmedi. Mevcut `exact_text` exact dış decimal ister; `align` yalnız off-grid’i reddeder. Otomatik rounding, order/fill, inventory, fee, replacement, trailing/reverse/infinity/leveraged grid ve UI açılmadı. Önceki kod baseline `259/259 PASS`, compile/workspace `PASS` (`110` aktif Python dosyası); production readiness `NO`.

Sonraki tek iş: `P1.13.e` trailing-up/down ve reverse/infinity grid ailelerinin ayrı profile karar kapısı.

### P1.13.e — Grid trailing-up/down ve reverse/infinity karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.13.e/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/10_P1.13_GRID_FAMILIES.md`.

Trailing-up/down için araştırma yalnız ürün davranışını destekliyor; exact range/version transition, pending order/reserve lifecycle, cancel-replace identity, late fill, precision/rounding ve persistence/replay sözleşmesi yok. Reverse/infinity exact semantics `NOT_VERIFIED`. Mevcut `trailing_ratchet.py` exit-trigger projection’ıdır ve grid range authority değildir; aritmetik seviye üreticisine de range kaydırma eklenmedi. Leveraged grid P1.12/P1.11 bağımlılıkları nedeniyle kapsam dışı kaldı. Kod/API/UI/order/reserve değişikliği yapılmadı.

Kanonik `uv run --frozen python tools/run_checks.py`: `259/259 PASS`; workspace: `PASS` (`110` aktif Python dosyası). Sonraki tek iş: `P1.14.a` rebalancing/signal/template çekirdek sınırı ve karar kapısı.

### P1.14.a — Rebalancing exact target/delta projection

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.14.a/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md`.

`target_value_i = total_equity * target_weight_i` ve `trade_delta_i = target_value_i - current_value_i` aynı açık valuation asset içinde exact projection olarak eklendi. Weight toplamı exact 1, duplicate asset, negatif current, geçersiz giriş ve exact decimal dışı sonuç fail-closed; çıktı asset adına göre canonical. Order/reserve/fill, fee/rounding, price conversion, balance, trigger, persistence, signal/template ve UI authority’si yoktur. RED import → GREEN kanonik regresyon `265/265 PASS`; bağımsız Decimal oracle `PASS`; workspace `PASS` (`110` aktif Python dosyası).

Sonraki tek iş: `P1.14.b` signal identity/dedupe ve event-time karar kapısı.

### P1.14.b — Signal identity, event-time ve dedupe

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.14.b/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md`.

Immutable `signal_id`, source, integer `event_time_us`, `schema_version=signal-v1` ve lowercase SHA-256 payload hash sözleşmesi eklendi. Exact duplicate no-op, aynı ID ile farklı metadata/payload conflict, eski yeni signal stale ve geçmiş zaman sırası ihlali fail-closed. Signal candidate/order/fill, payload hash üretimi, auth/replay window, warmup/closed-bar, persistence, API ve UI açılmadı. RED import → GREEN kanonik regresyon `270/270 PASS`; bağımsız signal control `PASS`; compile/workspace `PASS` (`114` aktif Python dosyası).

Sonraki tek iş: `P1.14.c` signal warmup/closed-bar ve stale-policy karar kapısı.

### P1.14.c — Signal warmup, closed-bar ve stale readiness gate

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.14.c/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md`.

Explicit `WAITING_FOR_CLOSED_BAR`, `STALE`, `WARMING_UP` ve `READY` readiness projection’ı eklendi. Signal event time ile son kapalı bar zamanı integer microseconds; warmup/stale pencereleri açık caller input’u; wall-clock/processing time kullanılmıyor. Signal candidate/order/fill, indikatör, adapter, trigger, persistence, API ve UI açılmadı. RED import → GREEN kanonik regresyon `275/275 PASS`; bağımsız readiness control `PASS`; compile/workspace `PASS` (`116` aktif Python dosyası).

Sonraki tek iş: `P1.14.d` threshold/time rebalancing trigger karar kapısı.

### P1.14.d — Rebalancing threshold/time trigger projection

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.14.d/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md`.

Threshold `abs(current-target)>=threshold` ve time interval `observation-last>=interval` ayrı exact projection’lar olarak eklendi. Inclusive boundary, decimal weight/threshold, integer microsecond time ve geriye giden observation zamanı fail-closed. Trigger yalnız readiness/candidate kapısıdır; order/reserve/fill, conversion, fee/rounding, balance, sizing, persistence, API ve UI authority’si yoktur. RED import → GREEN kanonik regresyon `281/281 PASS`; bağımsız Decimal/time oracle `PASS`; compile/workspace `PASS` (`118` aktif Python dosyası).

Sonraki tek iş: `P1.14.e` template integrity ve non-authority karar kapısı.

### P1.14.e — Strategy template integrity ve non-authority

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.14.e/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md`.

`strategy-template-v1` canonical JSON snapshot, SHA-256 identity, 64 KiB/bounded payload, forbidden executable/secret/credential field, declared capability integrity ve inert/non-authority sınırı ile eklendi. Activation approval, profile capability binding, webhook auth, order/reserve/fill, persistence, API ve UI açılmadı. RED → GREEN kanonik regresyon `286/286 PASS`; bağımsız canonical/hash control `PASS`; compile/workspace `PASS` (`120` aktif Python dosyası).

P1.14.f tamamlandı; ayrıntılı kapanış ve sonraki görev aşağıdaki bölümde kayıtlıdır.

### P1.14.f — Template activation ve capability gate

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.14.f/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md`.

Template declared capability’leri explicit allowlist ve `PENDING`/`APPROVED` approval durumu ile değerlendiren gate eklendi. Supported pending `AWAITING_APPROVAL`, supported approved `READY_FOR_ACTIVATION`, eksik capability `CAPABILITY_UNSUPPORTED` döner. Gate activation, candidate, order, reserve veya fill üretmez; gerçek activation transition, profile binding, parameter validation, persistence, API ve UI dışarıdadır. RED import → GREEN kanonik regresyon `290/290 PASS`; bağımsız activation/capability control, compile ve workspace `PASS` (`122` aktif Python dosyası).

Sonraki tek iş: `P1.15.a` hedge/cross/two-leg kapsam karar kapısı.

### P1.15.a — Hedge identity ve two-leg state sınırı

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.15.a/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/12_P1.15_HEDGE_CROSS_TWO_LEG.md`.

`ONE_WAY` ve `HEDGE` position identity’leri explicit venue profile, product, symbol ve gerekiyorsa LONG/SHORT hedge side ile ayrıldı. Two-leg state machine yalnız güvenli ilk sınırı uygular: `NONE → LEG_A_PENDING → ONE_LEG_FILLED/PARTIAL_HEDGE → BOTH_ESTABLISHED`; recovery ve timeout geçişleri explicit’tir. First-leg ara state’i geri alınmaz; fake atomicity yoktur. Accepted-fill quantity posting, duplicate/replay persistence, recovery ledger, cross ownership, reduce-only, liquidation, API ve UI bu dilimin dışındadır. RED → GREEN `294/294 PASS`; bağımsız identity/state control, compile ve workspace `PASS` (`124` aktif Python dosyası).

P1.15.a tamamlandı; ayrıntılı kapanış `evidence/P1.15.a/SONUC.md` altında kayıtlıdır.

### P1.15.b — Accepted two-leg fill projection

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.15.b/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/12_P1.15_HEDGE_CROSS_TWO_LEG.md`.

`LegFill` ve immutable `TwoLegFillProjection` ile aynı account/venue-profile/product/symbol kapsamındaki HEDGE LONG/SHORT iki ayağın accepted fill’leri exact decimal miktarlarla ayrı izleniyor. İlk leg partial/full sonrası `PARTIAL_HEDGE`/`ONE_LEG_FILLED` ara state’i korunuyor; iki leg FULL olduğunda `BOTH_ESTABLISHED` oluşuyor. Duplicate aynı payload’da idempotent, conflicting ID, aynı side, scope değişimi, geriye giden event time ve tamamlanmış leg’e yeni fill fail-closed reddediliyor. İstenen toplam quantity bu mikro-fazda bulunmadığından quantity conservation iddia edilmiyor.

Projection yalnız in-memory read modelidir; persistence/reopen/replay/recovery, late-fill policy, cross ownership, reduce-only, margin/liquidation, order/reserve binding, API/UI ve ekonomik posting açılmadı. `test_matrices/P1.15_TESTS.md` checkout’ta bulunmadığı için kanıt kapsamı araştırma belgesi ve yerel testlerle sınırlıdır. RED import → GREEN `298/298 PASS`; bağımsız accepted-fill control, compile ve workspace `PASS` (`126` aktif Python dosyası).

P1.15.b tamamlandı; ayrıntılı kapanış `evidence/P1.15.b/SONUC.md` altında kayıtlıdır.

### P1.15.c — Two-leg persistence/replay/recovery karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.15.c/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/12_P1.15_HEDGE_CROSS_TWO_LEG.md`.

Mevcut `LifecycleStore` açıkça `NON_ECONOMIC_LIFECYCLE_ONLY` kapsamındadır ve two-leg economic identity/leg/effective-time alanlarını taşımaz. Generic economic `Store` execution dedup ve posting içerir, ancak hedge side/leg scope, effective ordering, recovery state ve P1.15 model lineage sözleşmesini taşımaz. P1.15.b in-memory projection’ını iki ayrı store arasında bağlayan adapter atomic accepted-fill + state transition kanıtı üretmez. Bu nedenle migration, yeni economic schema, recovery numeric modeli veya adapter yazılmadı.

P1.15.c’nin yeniden açılması için canonical event schema, tek persistence sahibi/transaction planı, event/effective/persistence time ayrımı, two-leg duplicate/conflict/late-fill recovery politikası, deterministic reopen/replay ve independent field-level oracle/test matrisi gerekir. `test_matrices/P1.15_TESTS.md` checkout’ta mevcut değil. Kanonik regresyon `298/298 PASS`, bağımsız storage schema control, compile ve workspace `PASS` (`126` aktif Python dosyası).

Sonraki güvenli tek iş: `P1.16.a` chronological split ve leakage-free evaluation karar kapısı.

### P1.16.a — Chronological train/gap/test split sınırı

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.16.a/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

`ChronologicalPoint`, `ChronologicalSplit` ve `split_chronological` ile strict artan integer `event_time_us` kullanan immutable train/gap/test sınırı eklendi. `max(train_time) < min(test_time)` korunuyor; sıralama otomatik yapılmıyor. Explicit `gap_count` yalnız yapısal dışlama alanıdır, purge/embargo horizon’u değildir. Duplicate identity, duplicate/geriye giden zaman, geçersiz sınır ve boş bölüm fail-closed reddediliyor. OOS freeze/touched lineage, feature/label horizon, exact purge/embargo, multiple-testing/stress registry, persistence, API/UI ve economic result bu mikro-fazda yok. RED import → GREEN `303/303 PASS`; bağımsız chronology oracle, compile ve workspace `PASS` (`128` aktif Python dosyası).

Sonraki tek iş: `P1.16.b` OOS freeze ve evaluation lineage karar kapısı.

### P1.16.b — OOS freeze ve evaluation lineage

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.16.b/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

`EvaluationLineage` OOS sonucu görülmeden `OOS_UNTOUCHED`, inspection sonrası `OOS_INSPECTED` durumunu taşır. Inspection sonrası tuning talebi eski lineage’ı `TOUCHED` yaparak `NEW_EXPERIMENT_REQUIRED` döndürür; eski OOS tekrar untouched gösterilemez. OOS görülmeden tuning değişmeden izinlidir. New experiment/trial üretimi, dataset/config/model/kernel/seed binding, persistence, OOS KPI, purge/embargo, stress, API/UI ve economic result bu mikro-fazda yok. RED import → GREEN `307/307 PASS`; bağımsız OOS freeze control, compile ve workspace `PASS` (`130` aktif Python dosyası).

Sonraki tek iş: `P1.16.c` feature/label horizon ve purge/embargo karar kapısı.

### P1.16.c — Feature/label horizon overlap ve purge kararı

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.16.c/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

`TimeInterval` ve `assess_purge_requirement` ile half-open `[start_time_us,end_time_us)` train-label/test-feature aralıkları karşılaştırılıyor. Adjacent sınır `NO_OVERLAP`, kesişen aralık `PURGE_REQUIRED`; duplicate identity ve unsorted interval listesi fail-closed. Bu yalnız overlap/gate sonucudur; exact purge/embargo süresi feature lookback, label future horizon ve settlement bilgisi olmadan seçilmedi. Dataset binding, OOS/trial/stress lineage, persistence, API/UI ve economic result yok. RED import → fixture sıralama düzeltmeli GREEN `311/311 PASS`; bağımsız horizon oracle, compile ve workspace `PASS` (`132` aktif Python dosyası).

Sonraki tek iş: `P1.16.d` multiple-testing trial registry karar kapısı.

### P1.16.d — Multiple-testing trial registry

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.16.d/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

`TrialStudy` explicit parameter-space/objective/selection-rule identity ve en fazla 1.000 trial sınırı taşır. `TrialRecord` status’ları `SUCCEEDED`, `FAILED`, `INVALID` olarak ayrıdır ve tümü trial_count’a dahil edilir. Exact duplicate no-op, conflicting ID fail-closed; winner selection yoktur. Parameter snapshot/score, optimizer, persistence, dataset lineage, OOS/stress result, purge/embargo, API/UI ve economic result bu mikro-fazda açılmadı. RED import → GREEN `315/315 PASS`; bağımsız trial registry control, compile ve workspace `PASS` (`134` aktif Python dosyası).

Sonraki tek iş: `P1.16.e` stress lineage ve ayrı sonuç kimliği karar kapısı.

### P1.16.e — Stress lineage ve ayrı sonuç kimliği

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.16.e/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

`StressLineage` base result identity, stress profile identity ve profile hash’ini immutable biçimde taşır. Aynı girdiler deterministik ayrı `stress_result_id` üretir; sabit `STRESS` etiketi ve base result overwrite koruması vardır. Spread/slippage/latency/volume/partial-fill/OHLC ekonomik modeli, seed/RNG, persistence, dataset/config/model/kernel binding, API/UI ve exact purge/embargo bu mikro-fazda yok. RED import → GREEN `318/318 PASS`; bağımsız stress lineage control, compile ve workspace `PASS` (`136` aktif Python dosyası).

Sonraki tek iş: `P1.16.f` warmup leakage ve readiness binding karar kapısı.

### P1.16.f — Warmup leakage ve readiness binding

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.16.f/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

Mevcut `signal_readiness.py` saf readiness sınıflandırması yapıyor; ancak gerçek feature/indicator lookback, warmup başlangıcı ve historical economic runner’a binding yok. Bu nedenle yeni numeric warmup, indicator/signal authority veya warmup event’lerinden fill oluşmadığına dair end-to-end ekonomik kod açılmadı. Mevcut `318/318 PASS`, compile ve workspace `PASS` (`136` aktif Python dosyası).

Sonraki tek iş: `P1.16.g` local feature/label horizon ve gerçek run binding karar kapısı.

### P1.16.g — Local feature/label horizon ve gerçek run binding

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.16.g/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

Local code/test ağacında feature/indicator/label pipeline, lookback/future horizon veya historical runner binding bulunmadı. Bu nedenle numeric purge/embargo, warmup policy, OOS KPI veya gerçek run identity binding uydurulmadı; mevcut `TimeInterval` overlap gate’i yalnız structural karar olarak kaldı. Mevcut `318/318 PASS`, compile ve workspace `PASS` (`136` aktif Python dosyası).

Sonraki tek iş: `P1.16.h` bounded real-run lineage binding karar kapısı.

### P1.16.h — Bounded real-run lineage binding

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.16.h/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

P1.06 capture/store dataset/config/model/kernel/seed/result identity’sini kendi kapsamı içinde taşıyor. P1.16.h ile optional `EvaluationRunBinding` bu mevcut kimlikleri kayıtlı trial, OOS ve isteğe bağlı stress lineage’ına canonical biçimde bağlıyor. Store binding’i checksum’lı immutable kayda alıyor; close/reopen sonrası geri veriyor; aynı source execution’da aynı binding idempotent, farklı binding conflict; sözleşme dışı binding alanları fail-closed reddediliyor. Mevcut `325/325 PASS`, bağımsız canonical kontrol, compile ve workspace `PASS` (`138` aktif Python dosyası).

Economic stress modeli, exact purge/embargo, feature/label/warmup pipeline, score/KPI ve production readiness bu dilimde açılmadı. Sonraki tek iş: `P1.16.i` stress ekonomik modeli ve gerçek senaryo runner karar kapısı.

### P1.16.i — Stress ekonomik modeli ve gerçek senaryo runner karar kapısı

Durum: `IN_PROGRESS / EVIDENCE_AUDIT`; production readiness: `NO`. Ana kanıt dayanağı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`. Alt faz kanıtı: `evidence/P1.16.i/SONUC.md`.

Stress profile metadata’sı P1.16.h ile persisted run’a bağlandı; ancak spread/slippage/latency/volume/partial-fill/OHLC stress modelinin ekonomik authority’si yok. Bu ana faz kanıt sırasına göre mikro fazlara ayrılmıştır; aynı anda yalnız bir alt faz aktiftir:

- `P1.16.i.a` — Core/store authority ve mevcut scenario evidence inventory: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**. Mevcut fill, fee, precision, late-fill, OHLC ambiguity, result identity ve persistence sahipleri kod/fixture üzerinden çıkarıldı; eksik ekonomik davranışlar varsayımla açılmadı. Kanıt: `evidence/P1.16.i/SONUC.md`.
- `P1.16.i.b` — Exact stress economic contract: **COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED**; ekonomik implementation **DEFERRED / NO-GO**. Rapor `evidence/P1.16.i.b/SONUC.md` altında yerel ve bağımsız kontrollerle denetlendi. T-07’de sayısal çelişki, T-12’de seed/identity çelişkisi ve reserve oracle’ında negatif available karşı örneği bulundu. Spread/slippage/latency/volume/partial-fill/OHLC ekonomik kodu, reserve adapter ve yeni public yüzey açılmadı.
- `P1.16.i.c` — Deterministic scenario/result identity: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; ekonomik scenario identity **DEFERRED / NO-GO**. Mevcut stress profile hash, base-result ilişkisi, canonical serialization ve overwrite/dedup/conflict sınırı bağımsız oracle ile doğrulandı; seed/scenario/kapsam genişletmesi yapılmadı. Kanıt: `evidence/P1.16.i.c/SONUC.md`.
- `P1.16.i.d` — Persistence/replay/recovery: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**. Base Store’un kendi transaction/replay/rollback ve HistoricalRunStore’un snapshot checksum/idempotency sınırı doğrulandı; stress event, branch isolation, cross-store atomicity, economic recovery ve field-level result comparison **DEFERRED / NO-GO** kaldı. Kanıt: `evidence/P1.16.i.d/SONUC.md`. Economic runner, reserve adapter veya yeni public yüzey yazılmadı.
- `P1.16.i.e` — Minimum dikey uygulama ve dış yüzey kararı: **COMPLETE_WITH_LIMITATION / NO-GO**. P1.16.i.a–d kanıt zinciri birleştirildi; economic runner, yeni persistence schema/adapter, API ve UI açılmadı. Ekonomik stress persistence, branch isolation, cross-store atomicity, reserve lifecycle ve scenario identity `DEFERRED / NO-GO`. Kanıt: `evidence/P1.16.i.e/SONUC.md`.

Her alt fazda değişiklik sırası zorunludur: iddia → mevcut kontrol → RED/karşı örnek → farklı bağımsız kontrol → sonuç → yalnız doğrulanmış iddia için değişiklik. Ekonomik model, optimizer, numeric purge/embargo, yeni UI veya public endpoint kanıt yokken açılamaz.

### P1.17.a — Public read-only data authority inventory

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`.

P1.16.i ekonomik stress kapısı kanıt yetersizliği nedeniyle no-go olarak kapatıldı. Sıradaki bağlayıcı P1 işi, public canlı fiyat/veri için mevcut kod, veri adapter’ı, stale/gap/reconnect, offline fallback ve `SIMULATED` emir sınırlarının yerel envanteridir. Bu mikro fazda private credential, gerçek emir, yeni ekonomik hesap, stress runner veya UI eklenmeyecek. Public kaynağın güncel davranışı yerel kodla cevaplanamıyorsa ancak uygulama kararını değiştirecek iddia için anonim/kanıtlı araştırma istenecektir.

Çıkış kanıtı: `evidence/P1.17.a/SONUC.md` içinde mevcut authority, RED/karşı örnek, bağımsız kontrol ve public-read-only sınırı kaydedildi. Canlı feed bulunmadığı için kod açılmadı.

### P1.17.b — Public read-only feed contract research gate

Durum: **COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED**; production readiness: `NO`. Kanıt: `evidence/P1.17.b/SONUC.md`. Araştırma: `docs/P1_KRITIK_ARASTIRMA_FINAL/14_P1.17_SIMULATED_RUNTIME.md`.

Güncel resmi kaynak araştırması public read-only market-data WebSocket, source/system zaman ayrımı ve sequence gap/out-of-order riskini destekledi. Rapor yerel kodu ve testleri incelemediği için RED→GREEN yerel kontrolü ayrıca yapıldı. REST payload/rate-limit/catch-up ayrıntıları ve belirli venue reconnect algoritması tamamlanmış sayılmadı. Canlı REST/WS adapter, live route, credential, gerçek emir veya ekonomik live fill kodu hâlâ açılmadı.

### P1.17.c — Offline observation replay adapter

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.17.c/SONUC.md`.

P1.17.b ile doğrulanan salt-okunur `PublicObservation` ve fail-closed feed cursor’ı yalnız local fixture/replay girdileriyle ilerletildi. `replay_observations` bounded ve deterministic zamanlıdır; gap sonrası explicit resync olmadan devam etmez. Ağ bağlantısı, venue SDK’sı, yeni API/UI, persistence, candidate/order/fill, fee/spread/slippage ve gerçek paper-trading davranışı yoktur.

### P1.17.d — Venue-specific transport mapping and reconnect/catch-up research gate

Durum: **COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED**; production readiness: `NO`. Kanıt: `evidence/P1.17.d/SONUC.md`.

Binance Spot `binance-spot-public-v3` tek public profile olarak seçilebilir sınırlı araştırma yönü verdi. Güncel resmi belgelerle heartbeat/limit/timestamp iddiaları düzeltildi: ping 20 saniye, pong penceresi 60 saniye, 1024 stream/connection ve 300 connection attempt/5 dakika/IP ayrıdır; millisecond varsayılan olsa da explicit microsecond seçenekleri vardır. `t/a` yalnız trade/aggregate-trade identity’sidir; source sequence olarak bağlanmaz. Resubscribe kabul edildi, automatic snapshot ve tam REST gap repair garanti edilmedi. Canlı adapter, live route, credential, simulated economic fill veya persistence açılmadı.

### P1.17.e — Binance public payload normalization (network-free)

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.17.e/SONUC.md`.

Binance Spot `@trade` ve `@aggTrade` fixture payload’ları ağsız biçimde generic `PublicObservation` sınırına aktarıldı. Numeric/timestamp unit guard’ları, transport/profile scope, stream ayrımı, `t/a` event identity ve `source_sequence=None` doğrulandı. WebSocket client, reconnect worker, REST catch-up, persistence, API/UI, candidate/order/fill ve ekonomik hesap açılmadı.

### P1.17.f — Binance normalized observation → local replay binding (network-free)

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.17.f/SONUC.md`.

Normalize edilmiş Binance trade/aggTrade observation kayıtları mevcut bounded replay cursor’ına doğru stream scope, duplicate/conflict ve event-time davranışıyla bağlandı. `t/a` source sequence olarak bağlanmadı; forged sequence fail-closed reddedildi. Ağ, reconnect, REST catch-up, persistence, API/UI, candidate/order/fill ve ekonomik hesap açılmadı.

### P1.17.g — Binance public profile acceptance matrix (network-free)

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.17.g/SONUC.md`.

Trade/aggTrade mapping, unit mismatch, malformed payload, wrong scope, duplicate/conflict, event-time order, replay ve economic-boundary no-op davranışları tek bounded acceptance matrix içinde birlikte kanıtlandı. İlk RED’de görülen timestamp unit mismatch kabulü explicit plausibility/unit guard ile düzeltildi; bağımsız oracle ve `346/346` regresyon geçti. Canlı transport, reconnect worker, REST catch-up, persistence, API/UI ve economic fill açılmadı.

### P1.17.h — Binance REST public payload normalization (network-free)

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.17.h/SONUC.md`.

Yalnız fixture/decoded payload ile `/api/v3/trades` ve `/api/v3/aggTrades` REST mapping’i uygulandı. `transport=REST`, REST’e özgü zaman alanları, event identity, exact numeric parse, symbol/product scope ve WS observation’dan ayrık identity davranışı RED→GREEN ve bağımsız kontrolle kanıtlandı. `7/7` odak testi ve `353/353` regresyon geçti. Ağ, REST catch-up, reconnect worker, persistence, API/UI, candidate/order/fill ve ekonomik hesap açılmadı.

### P1.17.i — Binance public observation capability boundary (network-free)

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.17.i/SONUC.md`.

REST ve WS normalize edilmiş observation’ların hiçbir candidate/order/fill/economic authority portuna ulaşmadığı mevcut local import/call graph ve bounded negatif testlerle kanıtlandı. Observation yalnız read-only public data ve replay sınırında kaldı; untrusted economic alanlar taşınmadı. `2/2` odak testi ve `355/355` regresyon geçti. Canlı network, reconnect/catch-up, persistence ve API/UI açılmadı.

### P1.17.j — Binance public transport activation readiness gate (network-free)

Durum: **DEFERRED / NO-GO / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.17.j/SONUC.md`.

Mevcut resmi venue kanıtı ile local persistence/catch-up ve reconnect önkoşulları karşılaştırıldı. Bağımsız gate `NO-GO` verdi: canlı entrypoint, reconnect worker, tam REST catch-up ve live observation persistence yok; venue automatic snapshot/full gap repair/contiguous sequence garantisi vermiyor. `355/355` regresyon geçti. Network client, reconnect worker, REST catch-up, credential, candidate/order/fill ve economic/paper execution açılmadı.

### P1.18.a — Offline rule-based read-only event explanation projection

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.18.a/SONUC.md`.

Mevcut tarihsel/public observation ve sonuç sınırlarından yalnız açıklama/projection üretildi. `ReadOnlyExplanation` bounded ve salt-okunur; bilinmeyen durumlar fail-closed. `4/4` odak test, bağımsız oracle, `359/359` tam regresyon, compile ve workspace geçti. Parametre, emir, fill, reserve, PnL veya canlı transport authority’si eklenmedi.

### P1.18.b — Read-only explanation response binding karar kapısı

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.18.b/SONUC.md`.

P1.18.a projection’ı mevcut iki historical API response’una bounded `explanations` alanı olarak bağlandı. Strict/forbid/frozen response modeli, fixed-slice summary status fallback’i ve frontend type-only tüketim sınırı doğrulandı. İlk RED’deki üç response/projection hatası minimum düzeltmeyle kapatıldı; `359/359` regresyon, compile/workspace ve frontend build geçti. Persistence response DTO’sunu değil mevcut capture/result snapshot’ını kullandığı için persisted schema değişmedi. UI görünümü, LLM, network, candidate/order/fill, reserve veya PnL authority açılmadı.

### P1.18.c — Read-only explanation UI/UX research gate

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.18.c/SONUC.md`.

Kullanıcı tarafından teslim edilen UI/UX araştırma raporu gerçek sonuç ekranı ve response contract ile karşılaştırıldı. `ExplanationSection` completed ve indeterminate result akışlarına bağlandı; severity sunumu, backend grup-içi sıra korunumu, native teknik ayrıntı disclosure’ı ve 320px taşma önlemleri eklendi. Frontend hesaplama, LLM, network, persistence ve backend contract değişmedi. `frontend npm run build`, `359/359` regresyon, compile ve workspace geçti. Browser kernel-assets hatası nedeniyle görsel screenshot/viewport QA çalıştırılamadı; bu açık P1.18.d görsel erişilebilirlik QA kapısına bırakıldı.

### P1.18.d — Read-only explanation visual/accessibility QA

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.18.d/SONUC.md`.

Browser eklentisinin kernel-assets hatası sürmesine rağmen doğrudan kurulu Chrome CDP fallback’i ile gerçek yerel frontend/backend sonucu doğrulandı. 1280, 390 ve 320px görünümleri; 8 açıklama/8 kart, mobil yatay taşmama ve native disclosure’ın Space klavye etkileşimi geçti. Frontend build, `359/359` regresyon, compile, workspace ve statik UI contract kontrolleri geçti. NVDA/JAWS çalıştırılmadı; bu nedenle kabul local visual/accessibility smoke QA ile sınırlıdır. Yeni ekonomik alan, backend contract, LLM, network, persistence veya sticky notification eklenmedi.

### P1.19.a — Result shell responsive state acceptance

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.19.a/SONUC.md`.

Gerçek local UI akışında idle/empty, loading, error ve completed durumları doğrulandı. İlk RED, legacy response’un `summary` alanının UI tarafından okunmamasıydı; `final_economic_summary ?? summary` ile minimum frontend düzeltmesi yapıldı. Fixed-slice akışı korundu; indeterminate branch mevcut backend/API testleri ve kod sınırıyla doğrulandı ancak bu dilimde ayrı UI screenshot’ı alınmadı. Frontend build ve `359/359` regresyon geçti. Backend economic authority, response contract, network, persistence veya LLM değişmedi.

### P1.19.b — Existing result-shell responsive/theme inventory

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.19.b/SONUC.md`.

Mevcut result shell’in responsive breakpoint, renk tokenı, açık/koyu tema, focus ve empty/error görsel durumu envanterlendi. 1080/720/380px responsive kırılımları ve önceki 320/390px taşmama kanıtı doğrulandı; açık tema/token yok, focus desteği kısmi. Yeni tema sistemi veya focus davranışı eklenmedi. NVDA/JAWS etkileşimli QA ortam sınırı nedeniyle NOT_RUN kaldı.

### P1.19.c — Theme/focus implementation decision gate

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.19.c/SONUC.md`.

Teslim edilen raporun `SIMPLIFY` kararı bağımsız local kontrolle denetlendi. Raporun yanlış palette/satır referansları kullanılmadı; mevcut dark palette’den sınırlı CSS tokenları ve button/input/select/summary/a için ortak `:focus-visible` standardı eklendi. 768px gerçek yatay taşma RED’i 900px altında tek workspace kolonu ile kapatıldı. Light theme, ARIA redesign, backend/economic/network/persistence/LLM açılmadı. Frontend build, `359/359` regresyon, compile, workspace ve Chrome CDP responsive/focus smoke PASS; NVDA/JAWS etkileşimli QA ortam sınırı nedeniyle NOT_RUN.

### P1.19.d — Screen-reader/high-contrast accessibility QA gate

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.19.d/SONUC.md`.

Chrome CDP fallback’i ile gerçek local DOM/AX tree, 320/390/768/1024/1280px taşmama, 18 focus durağı, native disclosure, forced-colors emülasyonu ve temiz uygulama konsolu doğrulandı. Eksik favicon isteği kapatıldı; frontend build, `359/359` regresyon, compile ve workspace PASS. NVDA/JAWS ve gerçek Windows High Contrast Mode çalıştırılmadı; bu nedenle production readiness `NO` ve tam erişilebilirlik iddiası kapalıdır. Light theme veya yeni persistence mekanizması bu mikro fazda açılmadı.

### P1.19.e — Light theme / uzman görünüm karar kapısı

Durum: **COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED**; production readiness: `NO`. Kanıt: `evidence/P1.19.e/SONUC.md`.

Kullanıcı tarafından sağlanan rapor gerçek checkout ile denetlendi; okunmamış dosya/palette iddiaları local evidence olarak reddedildi. Gerçek React/Vite sürümleri, `ReadOnlyExplanation` type’ı, backend strict response modelleri, mevcut CSS token/focus kuralları ve P1.19.d responsive/focus kanıtı doğrulandı. Bağımsız contrast oracle seçilmiş gerçek çiftlerde 11 PASS, border/body için 1.44:1 FAIL verdi; alpha/gradient dahil tam matrix tamamlanmadı. Light theme ve uzman görünüm DEFER; app kodu bu mikro fazda değiştirilmedi. NVDA/JAWS ve gerçek Windows High Contrast Mode NOT_RUN olduğundan production readiness `NO` kaldı.

Araştırma promptu: `docs/P1.19.e_Light_Theme_Uzman_Gorunum_Arastirma_Promptu.md`. Ayrıntılı sonuç: `evidence/P1.19.e/SONUC.md`.

### P1.19.f — Exact token/palette ve safe detailed-view implementation gate

Durum: **DEFERRED / NO-GO / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.19.f/SONUC.md`.

Mevcut gerçek token kapsamı ve seçilmiş kontrast oracle ölçüldü; 11 kritik çift PASS, border/body `1.44:1` FAIL. Tam semantic token/alpha/gradient matrisi ve exact light palette yok. Yeni light theme/toggle/persistence veya expert mode eklenmedi. Mevcut native `details/summary` teknik disclosure’ı güvenli minimum detailed-view olarak kabul edildi; raw context’ten ekonomik türetme ve frontend ekonomik hesaplaması kalıcı `NO-GO`.

F30’un light theme kısmı için exact palette/default/persistence kararı gerekir; bu karar gelmeden yeni UI kodu açılmayacak. Kanıt: `evidence/P1.19.f/SONUC.md`.

### P1.16.g — Local feature/label horizon ve gerçek run binding

Gerçek feature/indicator/label pipeline ve historical runner bağı mevcut kod/fixture ile görülmeden purge/embargo veya warmup için numeric policy seçilmeyecek. Yalnız kanıtlı, bounded ve fail-closed bir sınır uygulanabilir.

### P1.16.f — Warmup leakage ve readiness binding

Warmup döneminin gerçek trade window’dan ayrılması ve warmup event’lerinin emir üretmemesi için local feature/indicator binding kanıtı gereklidir. Kanıt olmadan indicator, signal veya ekonomik sonuç kodu açılmayacak.

### P1.06.e — Kapanan UI araştırma kapısı

Kaydetme ve saved-run list/detail deneyimini mevcut React ekranına bağlamadan önce anonim görsel/UX araştırma raporu alınacak. Prompt: `docs/P1.06.e_Saved_Run_UI_UX_Arastirma_Promptu.md`. Rapor gelmeden UI özelliği, yeni görsel sistem, grafik genişletmesi veya mobil davranış kararı uygulanmayacak.

## 2026-09-07 — Kapsamlı/matematiksel analiz audit kapısı

Durum: AUDIT_COMPLETE_WITH_ONE_SMALL_FIX; kanıt: `evidence/AUDIT_2026-09-07/SONUC.md`.

Kullanıcı raporlarındaki iddialar kaynak kod, mevcut sözleşme, gerçek local artifact, kontrollü matematik ve bağımsız kontrollerle denetlendi. Timestamp mikro-saniye sözleşmesi ve config TOCTOU iddiası doğrulanmadı; TP/slippage, gap politikası, demo sizing ve ortak request-body/quality response sınırları karar araştırması bekliyor. Kanıtlanan tek küçük hata, simulate validation hatasının Problem Details yerine genel JSON dönmesiydi; `/api/historical-runs/simulate` mevcut Problem Details path kümesine alındı ve 83/83 regresyon geçti.

Yeni araştırma kapısı: `docs/2026-09-07_Kanitli_Audit_Dis_Arastirma_Promptu.md`. Bu kapı kapanmadan finansal formül, `paper.json`, gap status veya ortak body-limit sözleşmesi değiştirilmeyecek.

## 2026-09-07 — Yeni offline simülasyon audit raporu değerlendirmesi

Durum: B UYGULANDI / A BELGELENDİ / C DEFERRED / D1 UYGULANDI / D2 UYGULANDI / D3A UYGULANDI / D3B UYGULANDI. Son doğrulama: `92/92 PASS`; kanıt: `evidence/AUDIT_2026-09-07/SONUC.md`.

Kullanıcının sağladığı kapsamlı rapor talimat değil, kanıtlanması gereken araştırma çıktısı olarak ele alındı. Raporun TP/slippage kararı mevcut sözleşmeyle uyumlu bulundu: formül değiştirilmedi, trigger referansı ile fill fiyatı ayrımı `docs/VERI_VE_SIMULASYON.md` içinde belgelendi. Gap kararı için önce RED→GREEN test uygulandı; yalnız desteklenen `1h` interval’inde exact open-time grid preflight’i ekonomik state kurulmadan çalışıyor ve gap/bilinmeyen interval fail-closed reddediliyor. Demo sizing değiştirilmedi.

Gövde sınırının D1 parçası uygulandı: küçük JSON route’ları native Starlette katmanında 4 KiB ile sınırlı, `data-quality` 20 MiB upload bütçesini koruyor. D2 olarak quality issue örnekleri üretim anında en fazla 200 kayıtla bounded hale getirildi; tam issue/error/warning sayaçları ve `issues_truncated` korunuyor. Native 413 yanıtları küçük JSON route’larında ortak Problem Details sözleşmesine alındı (D3A). Quality report response toplam byte bütçesi D3B olarak 256 KiB fallback ile sınırlandı. Bu audit güvenlik dilimleri tamamlandı; P1.06 kalıcı koşu fazı sırası atlanmadı.

## 2026-09-11 — P2.01 Binance Spot Testnet bağlantı/capability araştırması

Durum: `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`; implementasyon kapısı `DEFERRED`; trading activation `NO-GO`. Kanıt: `evidence/P2.01/SONUC.md`.

P1.20 sonrası P2.01 için resmi Binance Spot Testnet endpoint ve izin/filter snapshot yüzeyi mevcut local kodla karşılaştırıldı. Testnet REST’in `https://testnet.binance.vision/api` tabanı, market WebSocket’in `wss://stream.testnet.binance.vision/ws` tabanı, WebSocket API’nin ayrı tabanı ve yalnız `/api/*` desteği doğrulandı. Mevcut projede venue adapter, signed client ve güvenli credential injection bulunmadığı için credential, order, account mutation veya yeni testnet kodu açılmadı. Sıradaki tek küçük iş `P2.01.a`: credential/emir içermeyen public connectivity + exchangeInfo snapshot sözleşmesi.

## 2026-09-11 — P2.01.a public connectivity + exchangeInfo snapshot

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; trading activation `NO-GO`. Kanıt: `evidence/P2.01.a/SONUC.md`.

Kimliksiz gerçek Binance Spot Testnet `GET /api/v3/exchangeInfo?symbol=BTCUSDT` çağrısı bounded adaptöre bağlandı ve yeni read-only local endpoint’ten sunuldu: `GET /api/venue-snapshots/binance-spot-testnet?symbol=BTCUSDT`. Sözleşme sabit testnet tabanı, boşluksuz/kontrol-karaktersiz 1–32 karakter UTF-8 symbol girdisi, UTF-8 percent-encoding, 5 saniye default/30 saniye max timeout, 256 KiB response sınırı, identity encoding, response hash, symbol/filter/rate-limit metadata’sı ve fail-closed upstream hatalarını içeriyor. Gerçek public yanıt `TRADING`, 11 filter, 4 rate-limit kaydı, boş `permissions` ve `permissionSets=[['SPOT']]` verdi; `SPOT` account/key capability’si uydurulmadı.

Odak `7/7 PASS`, tam Python regresyon `366/366 PASS`, Python 3.13 compile/workspace, ASGI smoke, frontend build ve gerçek public GET PASS. API key/secret, signed account capability, `/sapi`, WebSocket, order/order-test/cancel, persistence, UI wizard ve ekonomik hesaplama açılmadı. Sıradaki tek iş: P2.01.b public snapshot’ın UI’da salt-okunur gösterimi için karar/uygulama kapısı.

## 2026-09-11 — P2.01.b public snapshot salt-okunur UI

Durum: `IMPLEMENTED_WITH_LIMITATION / READY_WITH_LIMITATION`; kanıt: `evidence/P2.01.b/SONUC.md`.

Public Testnet snapshot kartı mevcut React stüdyo ekranına bağlandı. Kart yalnız
`CONNECTED_READ_ONLY`/yükleniyor/`FAILED` durumlarını, venue status’ünü,
`permissionSets`, `order_types`, rate limits, filters ve hash ayrıntılarını
gösterir. Hesap/API-key trade yetkisi, bakiye, order, fill veya frontend
ekonomik hesaplama yoktur. Frontend build ve backend test/compile/workspace
kontrolleri PASS; güncel kaynakla yeniden başlatılan local API route smoke HTTP
200 verdi. Doğrudan Chrome CDP ile 320/768/1280px taşmama, snapshot/boundary
DOM, screenshot ve 23 klavye odağında görünür focus ring doğrulandı. Yerleşik
browser runtime yolu, NVDA/JAWS ve gerçek Windows HCM NOT_RUN. Sıradaki tek iş:
P2.02/P2.04 offline güvenlik kapıları.

## 2026-09-11 — P1.20 tam demo kabulü

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.20/SONUC.md`.

Gerçek local frontend/backend ile verified sabit BTCUSDT 1h artifact kullanılarak dataset seçimi, historical profile/run plan, kullanıcı onayı, simülasyon, grafik/ekonomi/açıklama incelemesi, kaydetme, Saved Runs listesi ve salt-okunur ayrıntıyı yeniden açma akışı tamamlandı. `359/359` Python regresyonu, Python 3.13 compile, workspace kontrolü, frontend build ve Chrome CDP görsel/etkileşim smoke PASS. İlk 768px Saved Runs yatay taşması `900px` responsive eşik düzeltmesiyle kapatıldı. NVDA/JAWS ve gerçek Windows High Contrast Mode çalıştırılmadı; production readiness `NO`. P1.20 demo kapısı kapanmıştır; özellik matrisindeki PLAN maddeleri P1 tamamlanmış anlamına gelmez.

## 2026-09-11 — P2.02.a offline signer ve request-time sınırı

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; full P2.02: `IN_PROGRESS`; trading activation: `NO-GO`. Kanıt: `evidence/P2.02/SONUC.md`.

P2.02.a’da gerçek ağ çağrısı olmadan `HmacSha256Signer`, `RequestSigner`/`Clock` sınırları, exact UTF-8 percent-encoded imza payload’ı, unsafe/duplicate/credential parametre reddi, unknown key type fail-closed ve integer millisecond `timestamp/recvWindow` predicate’i eklendi. RED import failure → GREEN `6/6` odak testi geçti. Gerçek secret/API key, Ed25519/RSA signer, Windows provider, signed account, HTTP, clock sync, reconciliation, Testnet mutation ve mainnet açılmadı.

Sıradaki tek iş: P2.02’nin Windows secret provider ve signed-account sınırını offline/fake oracle ile değerlendirmek. Bu iş tamamlanmadan P2.03 order lifecycle veya gerçek Testnet mutation başlatılmaz.

## 2026-09-11 — P2.02.b Windows secret-provider ve signed-account sınırı

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; sahiplik: backend application security boundary; kanıt: `evidence/P2.02/SONUC.md`.

Kapsam: Windows Credential Locker/DPAPI’ye gerçek yazma yapmadan, secret’ın frontend/URL/log/persistence dışı kaldığını garanti eden provider portu ve public venue metadata’nın signed account/key capability sayılamadığı fail-closed sözleşme. Ön kontrol: mevcut source’ta credential provider veya signed-account implementation bulunmadı; bu yüzden yalnız yeni offline/fake oracle açılacak. RED→GREEN, dummy material, import-graph ve serialization boundary testleriyle kanıtlanacak. Gerçek secret, API key, OS vault, HTTP, signed account çağrısı, order veya mainnet yok.

RED→GREEN odak testi `6/6 PASS`; tam regresyon `387/387 PASS`, Python 3.13 compile/workspace ve frontend build PASS. Gerçek Windows provider runtime ve signed account `DEFERRED/NO-GO` kalır; ekonomik/API/persistence davranışı varsayımla açılmaz.

Sıradaki tek iş: `P2.04.a` — Fake WebSocket/Fake REST ile reconnect, stale/gap, restart ve UNKNOWN attempt reconciliation state machine.

## 2026-09-11 — P2.04.a offline reconciliation state machine

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; full P2.04: `IN_PROGRESS`;
trading activation: `NO-GO`; kanıt: `evidence/P2.02/SONUC.md`.

Yalnız [OFFLINE_ORACLE] fake WebSocket/Fake REST sınırı eklendi. Restart sonrası
`SENDING` attempt `UNKNOWN` olarak karantinaya alınıyor; reconnect doğrudan
`SYNCED` olmuyor; authoritative REST sonucu olmadan ekonomik senkronizasyon
verilmiyor. Duplicate event idempotent, aynı ID ile farklı fingerprint conflict,
out-of-order event `GAP`; ham event payload’ı saklanmıyor. Fake REST `FOUND`
yalnız `ACKNOWLEDGED`, diğer sonuçlar `UNRESOLVED` üretiyor; fill veya emir
yaşam döngüsü hesabı yok.

RED→GREEN odak `6/6 PASS`; tam regresyon `393/393 PASS`; Python 3.13
compileall, workspace (`160` aktif Python dosyası) ve frontend build PASS.
Gerçek WebSocket API, signed REST, Testnet mutation, P2.03 order lifecycle,
NVDA/JAWS ve Windows HCM açılmadı.

Sıradaki tek iş: P2.04.b — Fake REST/stream disagreement, stale/reset ve
non-terminal attempt recovery matrisini genişletmek.

## 2026-09-11 — P2.04.b disagreement/freshness/reset quarantine

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; full P2.04: `IN_PROGRESS`;
trading activation: `NO-GO`; kanıt: `evidence/P2.02/SONUC.md`.

P2.04.a state machine’i Fake REST/stream disagreement, freshness ve Testnet
reset karşı-örnekleriyle genişletildi. REST ve stream order identity farkı
`GAP` açıyor; freshness sınırı `STALE`; reset sonrası yeni authoritative snapshot
olmadan `SYNCED` yasak; GAP sonrası event’ler karantinada tutuluyor. Ham event,
ekonomik değer veya order lifecycle hesabı eklenmedi.

RED→GREEN odak `10/10 PASS`; tam regresyon `397/397 PASS`; Python 3.13
compileall, workspace (`160` aktif Python dosyası) ve frontend build PASS.
Gerçek WebSocket API, signed REST, canlı reset recovery, P2.03 lifecycle,
NVDA/JAWS ve Windows HCM açılmadı.

Sıradaki tek iş: `P2.04.c` — mevcut signed transport/WS adapter contract
denetimi; local kod yeterli değilse gerçek entegrasyon açılmayacak.

## 2026-09-11 — P2.02 offline attempt/outbox ilk dikey dilimi

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; full P2.02: `IN_PROGRESS`; trading activation: `NO-GO`. Kanıt: `evidence/P2.02/SONUC.md`.

P2.02’nin ilk güvenli diliminde ayrı SQLite attempt store, `PREPARED -> PERSISTED -> SENDING` kalıcılık sırası, canonical request fingerprint, credential-bearing payload reddi, ambiguous transport -> `UNKNOWN`, restart sırasında `SENDING -> UNKNOWN`, kör retry engeli ve `UNKNOWN -> RECONCILING` geçişi uygulandı. Odak `9/9 PASS`, tam regresyon `375/375 PASS`, Python 3.13 compile/workspace PASS (`154` aktif Python dosyası). Gerçek transport, API key/secret, signer, clock/recvWindow, signed account, reconciliation, API/UI, Testnet mutation ve mainnet açılmadı.

Bu ilk dilimin sonraki alt fazı P2.02.a olarak tamamlandı; signer/time kanıtı ve kalan sınırlar `evidence/P2.02/SONUC.md` içinde tutulur.
# P2.04.c — Signed transport ve WebSocket adapter contract denetimi

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; full P2.04: `IN_PROGRESS`;
trading activation: `NO-GO`; kanıt: `evidence/P2.04.c/SONUC.md`.

Mevcut public Testnet snapshot, offline signed-request/credential sınırı,
fake order transport ve reconciliation coordinator denetlendi. Gerçek signed
REST, API-key header binding, Binance User Data Stream subscription, reconnect
worker ve order query adapter'ı bulunmadı. Bu nedenle canlı entegrasyon,
secret, order ve mainnet açılmadı.

Standart suite `397/397 PASS`, Python 3.13 compileall/workspace ve frontend
production build PASS. Bir sonraki tek iş: P2.03 fake venue ile Spot
`LIMIT`/`MARKET` order lifecycle, partial fill ve cancel/fill race sözleşmesi.
# P2.03 — Fake venue Spot LIMIT/MARKET order lifecycle ilk dilimi

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; full P2.03: `IN_PROGRESS`;
trading activation: `NO-GO`; kanıt: `evidence/P2.03/SONUC.md`.

Offline/fake lifecycle modülüyle LIMIT/MARKET, exact filter validation,
partial fill/leaves, quoteOrderQty sınırı, duplicate/conflict, out-of-order,
terminal late fill, cancel/fill race ve order-scoped event sözleşmesi eklendi.
Gerçek Binance REST/WS, signed account/order, mutation, frontend binding ve
ekonomik posting açılmadı. Tam regresyon `404/404 PASS`, compileall/workspace
PASS.

Sıradaki tek iş: venue lifecycle facts’larının mevcut `domain.engine`
`INTENT/FILL/ORDER_FINAL` ekonomik event’lerine bağlanma sözleşmesini ve
offline dedup/reconciliation kanıtını incelemek.
